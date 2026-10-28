// IRIS — firmware node ESP32 (gerbang & zona).
// Irisan 1: logic + aktuator + mode uji tombol. Sumber LIVE (MQTT) ditambahkan di irisan 2.
// Rancangan: docs/design.md
#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <ESP32Servo.h>

#include "config.h"

// ---------- Tipe ----------
enum class Role { GATE, ZONE };
enum class Source { LIVE, TEST };
enum class State { FAULT, IDLE, GRANTED, DENIED, NORMAL, WARNING, ALARM };

// Hasil deteksi terakhir (dari MQTT atau dari tombol uji)
struct Snapshot {
  int personCount = 0;
  int violatorCount = 0;
  bool missingHelmet = false;
  bool missingVest = false;
  float maxViolationS = -1;       // durasi dari server; -1 = tidak ada, pakai timer lokal
  unsigned long receivedMs = 0;   // 0 = belum pernah menerima data
};

// Tombol aktif-LOW dengan debounce; pressed() true sekali per tekanan
struct Button {
  int pin;
  bool stable = false;
  bool lastRead = false;
  unsigned long changedAt = 0;

  void begin() { pinMode(pin, INPUT_PULLUP); }

  bool pressed() {
    bool reading = digitalRead(pin) == LOW;
    unsigned long now = millis();
    if (reading != lastRead) {
      lastRead = reading;
      changedAt = now;
    }
    if (now - changedAt > DEBOUNCE_MS && reading != stable) {
      stable = reading;
      return stable;
    }
    return false;
  }
};

// ---------- Objek global ----------
Adafruit_SSD1306 oled(128, 64, &Wire, -1);
bool oledOk = false;
Servo gateServo;

Button btnPerson{PIN_BTN_PERSON}, btnHelmet{PIN_BTN_HELMET}, btnVest{PIN_BTN_VEST}, btnReset{PIN_BTN_RESET};

Role role;
Source source;
State state = State::FAULT;
unsigned long stateSince = 0;
Snapshot snap;

bool testPerson = false, testHelmet = false, testVest = false;  // nilai simulasi (mode TEST)
unsigned long violationStartMs = 0;  // timer lokal pelanggaran zona
unsigned long gateRearmUntil = 0;    // palang tidak boleh buka lagi sebelum waktu ini
bool alarmAcked = false;             // buzzer dibungkam supervisor
bool gateOpen = false;
unsigned long lastStatusMs = 0, lastDisplayMs = 0;
uint8_t lastMissingMask = 0;

// ---------- Utilitas ----------
const char* stateName(State s) {
  switch (s) {
    case State::FAULT: return "FAULT";
    case State::IDLE: return "IDLE";
    case State::GRANTED: return "GRANTED";
    case State::DENIED: return "DENIED";
    case State::NORMAL: return "NORMAL";
    case State::WARNING: return "WARNING";
    case State::ALARM: return "ALARM";
  }
  return "?";
}

const char* nodeName() { return role == Role::GATE ? NODE_GATE : NODE_ZONE; }

uint8_t missingMask() { return (snap.missingHelmet ? 1 : 0) | (snap.missingVest ? 2 : 0); }

String missingList() {
  String s;
  if (snap.missingHelmet) s += "helmet";
  if (snap.missingVest) s += s.length() ? ",vest" : "vest";
  return s.length() ? s : "-";
}

String missingText() {  // untuk OLED (Bahasa Indonesia)
  if (snap.missingHelmet && snap.missingVest) return "HELM + ROMPI";
  if (snap.missingHelmet) return "HELM";
  if (snap.missingVest) return "ROMPI";
  return "-";
}

bool dataStale() {
  return snap.receivedMs == 0 || millis() - snap.receivedMs > FAILSAFE_TIMEOUT_MS;
}

// Durasi pelanggaran zona: utamakan nilai server (tracking per orang), fallback timer lokal
float violationSeconds() {
  if (snap.violatorCount == 0) return 0;
  if (snap.maxViolationS >= 0) return snap.maxViolationS;
  return violationStartMs ? (millis() - violationStartMs) / 1000.0f : 0;
}

// ---------- Aktuator ----------
void setLeds(bool green, bool yellow, bool red) {
  digitalWrite(PIN_LED_GREEN, green);
  digitalWrite(PIN_LED_YELLOW, yellow);
  digitalWrite(PIN_LED_RED, red);
}

void setGate(bool open) {
  if (open == gateOpen) return;
  gateOpen = open;
  gateServo.write(open ? SERVO_OPEN_DEG : SERVO_CLOSED_DEG);
  Serial.printf("[ACT] servo=%d gate=%s\n", open ? SERVO_OPEN_DEG : SERVO_CLOSED_DEG, open ? "open" : "closed");
}

void buzzerTone(bool on) { ledcWriteTone(PIN_BUZZER, on ? BUZZER_FREQ_HZ : 0); }

// Pola buzzer: bip singkat saat GRANTED, bip berulang saat DENIED/ALARM (kecuali di-ack)
void updateBuzzer() {
  unsigned long t = millis() - stateSince;
  bool on = false;
  if (state == State::GRANTED) on = t < 120;
  else if ((state == State::DENIED || state == State::ALARM) && !alarmAcked) on = (t % 500) < 250;
  buzzerTone(on);
}

// LED berdasarkan state; kuning berkedip saat FAULT
void updateLeds() {
  bool blink = (millis() / 400) % 2;
  switch (state) {
    case State::FAULT: setLeds(false, blink, false); break;
    case State::IDLE: setLeds(false, false, false); break;
    case State::GRANTED: case State::NORMAL: setLeds(true, false, false); break;
    case State::WARNING: setLeds(false, true, false); break;
    case State::DENIED: case State::ALARM: setLeds(false, false, true); break;
  }
}

// Gambar ulang OLED hanya jika isinya berubah (transfer I2C penuh cukup lama dan bisa membuat tombol terlewat)
void drawDisplay() {
  static String lastContent;
  if (!oledOk) return;

  const char* title = "";
  String line1, line2;
  switch (state) {
    case State::FAULT: title = "OFFLINE"; line1 = "Vision tidak aktif"; line2 = role == Role::GATE ? "Gerbang terkunci" : "Monitoring berhenti"; break;
    case State::IDLE: title = "SIAP"; line1 = "Silakan mendekat"; break;
    case State::GRANTED: title = "MASUK"; line1 = "APD lengkap"; line2 = "Palang terbuka"; break;
    case State::DENIED: title = "DITOLAK"; line1 = "Kurang: " + missingText(); line2 = "Pakai APD lengkap"; break;
    case State::NORMAL:
      title = "AMAN";
      if (snap.violatorCount > 0) line1 = "Pelanggaran " + String(violationSeconds(), 1) + "s";
      else line1 = "Orang: " + String(snap.personCount);
      break;
    case State::WARNING: title = "AWAS"; line1 = "Kurang: " + missingText(); line2 = "Durasi " + String(violationSeconds(), 1) + "s"; break;
    case State::ALARM: title = "ALARM!"; line1 = "Kurang: " + missingText(); line2 = "Durasi " + String(violationSeconds(), 1) + "s"; break;
  }
  String header = String("IRIS ") + nodeName() + (source == Source::TEST ? " [TEST]" : " [LIVE]");
  String content = header + title + line1 + line2;
  if (content == lastContent) return;
  lastContent = content;

  oled.clearDisplay();
  oled.setTextColor(SSD1306_WHITE);
  oled.setTextSize(1);
  oled.setCursor(0, 0);
  oled.print(header);
  oled.drawLine(0, 10, 127, 10, SSD1306_WHITE);
  oled.setTextSize(2);
  oled.setCursor(0, 16);
  oled.print(title);
  oled.setTextSize(1);
  oled.setCursor(0, 40);
  oled.print(line1);
  oled.setCursor(0, 52);
  oled.print(line2);
  oled.display();
}

// ---------- Event & status (irisan 2: dikirim juga via MQTT) ----------
void logEvent(const char* type) {
  Serial.printf("[EVENT] node=%s type=%s missing=%s persons=%d duration_s=%.1f\n",
                nodeName(), type, missingList().c_str(), snap.personCount, violationSeconds());
}

void logStatus() {
  Serial.printf("[STATUS] {\"node\":\"%s\",\"mode\":\"%s\",\"source\":\"%s\",\"state\":\"%s\",\"gate\":\"%s\","
                "\"missing\":\"%s\",\"person_count\":%d}\n",
                nodeName(), role == Role::GATE ? "gate" : "zone", source == Source::TEST ? "test" : "live",
                stateName(state), gateOpen ? "open" : "closed", missingList().c_str(), snap.personCount);
}

// ---------- State machine ----------
void enterState(State next) {
  State prev = state;
  state = next;
  stateSince = millis();
  alarmAcked = false;
  Serial.printf("[STATE] %s -> %s missing=%s persons=%d\n", stateName(prev), stateName(next),
                missingList().c_str(), snap.personCount);

  setGate(next == State::GRANTED);
  if (prev == State::GRANTED && next == State::IDLE) gateRearmUntil = millis() + GATE_REARM_MS;

  if (next == State::FAULT) logEvent("fault");
  else if (prev == State::FAULT) logEvent("recovered");
  if (next == State::GRANTED) logEvent("granted");
  if (next == State::DENIED) logEvent("denied");
  if (next == State::WARNING) logEvent("warning");
  if (next == State::ALARM) logEvent("alarm");
  if (next == State::NORMAL && (prev == State::WARNING || prev == State::ALARM)) logEvent("cleared");

  drawDisplay();
  logStatus();
}

State evaluateGate() {
  if (dataStale()) return State::FAULT;
  if (snap.personCount == 0) return State::IDLE;
  if (snap.violatorCount > 0) return State::DENIED;  // satu pelanggar cukup untuk menutup palang
  if (state == State::GRANTED) {
    return millis() - stateSince < OPEN_WINDOW_MS ? State::GRANTED : State::IDLE;  // jendela buka habis
  }
  return millis() < gateRearmUntil ? State::IDLE : State::GRANTED;
}

State evaluateZone() {
  if (dataStale()) return State::FAULT;
  if (snap.violatorCount == 0) {
    violationStartMs = 0;
    return State::NORMAL;
  }
  if (violationStartMs == 0) violationStartMs = millis();
  float d = violationSeconds();
  if (d >= ZONE_ALARM_S) return State::ALARM;
  if (d >= ZONE_WARN_S) return State::WARNING;
  return State::NORMAL;  // pelanggaran singkat diabaikan
}

// ---------- Input ----------
void readModeSwitches() {
  Role r = digitalRead(PIN_SW_ROLE) == HIGH ? Role::ZONE : Role::GATE;
  Source s = digitalRead(PIN_SW_SOURCE) == HIGH ? Source::TEST : Source::LIVE;
  if (r == role && s == source) return;
  role = r;
  source = s;
  Serial.printf("[MODE] role=%s source=%s node=%s\n", role == Role::GATE ? "GATE" : "ZONE",
                source == Source::TEST ? "TEST" : "LIVE", nodeName());
  snap = Snapshot();  // data mode lama tidak berlaku
  violationStartMs = 0;
  gateRearmUntil = 0;
  enterState(State::FAULT);
}

void handleReset() {
  if ((state == State::DENIED || state == State::ALARM) && !alarmAcked) {
    alarmAcked = true;
    Serial.println("[INPUT] reset -> alarm acknowledged (buzzer off)");
  } else {
    Serial.println("[INPUT] reset pressed (no active alarm)");
  }
}

// Mode TEST: tombol toggle mensimulasikan hasil deteksi satu orang
void readTestButtons() {
  bool changed = false;
  if (btnPerson.pressed()) { testPerson = !testPerson; changed = true; }
  if (btnHelmet.pressed()) { testHelmet = !testHelmet; changed = true; }
  if (btnVest.pressed()) { testVest = !testVest; changed = true; }
  if (changed) Serial.printf("[INPUT] person=%d helmet=%d vest=%d\n", testPerson, testHelmet, testVest);

  snap.personCount = testPerson ? 1 : 0;
  snap.missingHelmet = testPerson && !testHelmet;
  snap.missingVest = testPerson && !testVest;
  snap.violatorCount = (snap.missingHelmet || snap.missingVest) ? 1 : 0;
  snap.maxViolationS = -1;
  snap.receivedMs = millis();  // tombol selalu "segar"
}

// ---------- Setup & loop ----------
void setup() {
  Serial.begin(115200);
  pinMode(PIN_LED_GREEN, OUTPUT);
  pinMode(PIN_LED_YELLOW, OUTPUT);
  pinMode(PIN_LED_RED, OUTPUT);
  pinMode(PIN_SW_ROLE, INPUT);
  pinMode(PIN_SW_SOURCE, INPUT);
  btnPerson.begin();
  btnHelmet.begin();
  btnVest.begin();
  btnReset.begin();

  gateServo.setPeriodHertz(50);
  gateServo.attach(PIN_SERVO, 500, 2400);
  gateServo.write(SERVO_CLOSED_DEG);
  ledcAttach(PIN_BUZZER, BUZZER_FREQ_HZ, 8);
  buzzerTone(false);

  Wire.begin(PIN_SDA, PIN_SCL);
  Wire.setClock(400000);  // I2C fast mode: gambar OLED lebih cepat
  oledOk = oled.begin(SSD1306_SWITCHCAPVCC, OLED_ADDR);
  if (!oledOk) Serial.println("[ERR] OLED not found");

  role = digitalRead(PIN_SW_ROLE) == HIGH ? Role::ZONE : Role::GATE;
  source = digitalRead(PIN_SW_SOURCE) == HIGH ? Source::TEST : Source::LIVE;
  Serial.printf("[BOOT] IRIS node=%s role=%s source=%s\n", nodeName(), role == Role::GATE ? "GATE" : "ZONE",
                source == Source::TEST ? "TEST" : "LIVE");
  stateSince = millis();
  drawDisplay();
}

void loop() {
  readModeSwitches();
  if (source == Source::TEST) readTestButtons();
  if (btnReset.pressed()) handleReset();

  State next = role == Role::GATE ? evaluateGate() : evaluateZone();
  if (next != state) {
    enterState(next);
  } else if (missingMask() != lastMissingMask) {
    Serial.printf("[STATE] %s missing=%s\n", stateName(state), missingList().c_str());
    drawDisplay();
  }
  lastMissingMask = missingMask();

  updateLeds();
  updateBuzzer();
  if (millis() - lastDisplayMs > 500) {  // perbarui durasi/kedipan di OLED
    lastDisplayMs = millis();
    drawDisplay();
  }
  if (millis() - lastStatusMs > STATUS_PERIOD_MS) {
    lastStatusMs = millis();
    logStatus();
  }
  delay(10);
}
