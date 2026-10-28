// IRIS — firmware node ESP32 (gerbang & zona).
// Sumber deteksi: LIVE (MQTT dari server vision) atau TEST (tombol). Rancangan: docs/design.md
#include <Arduino.h>
#include <Wire.h>
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <time.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <ArduinoJson.h>
#include <ESP32Servo.h>
#include <PubSubClient.h>

#include "ca_cert.h"
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
WiFiClientSecure tlsClient;
PubSubClient mqtt(tlsClient);

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

bool wifiUp = false;
unsigned long lastWifiAttemptMs = 0, lastMqttAttemptMs = 0;
unsigned long lastHeartbeatMs = 0;   // 0 = belum pernah menerima heartbeat
String lastDetectionSummary;         // log MQTT hanya saat isi deteksi berubah

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

String topicFor(const char* leaf) { return String(MQTT_TOPIC_PREFIX) + "/" + nodeName() + "/" + leaf; }
String heartbeatTopic() { return String(MQTT_TOPIC_PREFIX) + "/server/heartbeat"; }

// Detik Unix dari NTP; 0 jika jam belum tersinkron
uint32_t nowTs() {
  time_t t = time(nullptr);
  return t > 1700000000 ? (uint32_t)t : 0;
}

uint8_t missingMask() { return (snap.missingHelmet ? 1 : 0) | (snap.missingVest ? 2 : 0); }

String missingList() {
  String s;
  if (snap.missingHelmet) s += "helmet";
  if (snap.missingVest) s += s.length() ? ",vest" : "vest";
  return s.length() ? s : "-";
}

void addMissingArray(JsonDocument& doc) {
  JsonArray arr = doc["missing"].to<JsonArray>();
  if (snap.missingHelmet) arr.add("helmet");
  if (snap.missingVest) arr.add("vest");
}

String missingText() {  // untuk OLED (Bahasa Indonesia)
  if (snap.missingHelmet && snap.missingVest) return "HELM + ROMPI";
  if (snap.missingHelmet) return "HELM";
  if (snap.missingVest) return "ROMPI";
  return "-";
}

// Data dianggap basi jika deteksi (atau heartbeat server, pada mode LIVE) berhenti melewati batas
bool dataStale() {
  unsigned long now = millis();
  if (snap.receivedMs == 0 || now - snap.receivedMs > FAILSAFE_TIMEOUT_MS) return true;
  if (source == Source::LIVE && (lastHeartbeatMs == 0 || now - lastHeartbeatMs > FAILSAFE_TIMEOUT_MS)) return true;
  return false;
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
  String header = String("IRIS ") + nodeName() + (source == Source::TEST ? " [TEST]" : " [LIVE]") +
                  (mqtt.connected() ? " *" : "");  // * = terhubung ke broker
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

// ---------- Status & event: Serial + MQTT ----------
void publishJson(const String& topic, JsonDocument& doc, bool retained) {
  if (!mqtt.connected()) return;
  String payload;
  serializeJson(doc, payload);
  if (!mqtt.publish(topic.c_str(), payload.c_str(), retained)) Serial.printf("[MQTT] publish failed topic=%s\n", topic.c_str());
}

void publishStatus() {
  JsonDocument doc;
  doc["ts"] = nowTs();
  doc["node"] = nodeName();
  doc["mode"] = role == Role::GATE ? "gate" : "zone";
  doc["source"] = source == Source::TEST ? "test" : "live";
  doc["state"] = stateName(state);
  doc["gate"] = gateOpen ? "open" : "closed";
  addMissingArray(doc);
  doc["person_count"] = snap.personCount;
  doc["violation_s"] = serialized(String(violationSeconds(), 1));
  String line;
  serializeJson(doc, line);
  Serial.printf("[STATUS] %s\n", line.c_str());
  publishJson(topicFor("status"), doc, true);  // retained: dashboard langsung tahu status terakhir
}

int eventLevel(const char* type) {
  if (!strcmp(type, "fault")) return 3;
  if (!strcmp(type, "denied") || !strcmp(type, "alarm")) return 2;
  if (!strcmp(type, "warning")) return 1;
  return 0;
}

void publishEvent(const char* type) {
  Serial.printf("[EVENT] node=%s type=%s missing=%s persons=%d duration_s=%.1f\n",
                nodeName(), type, missingList().c_str(), snap.personCount, violationSeconds());
  JsonDocument doc;
  doc["ts"] = nowTs();
  doc["node"] = nodeName();
  doc["type"] = type;
  doc["level"] = eventLevel(type);
  addMissingArray(doc);
  doc["person_count"] = snap.personCount;
  doc["duration_s"] = serialized(String(violationSeconds(), 1));
  publishJson(topicFor("event"), doc, false);
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

  if (next == State::FAULT) publishEvent("fault");
  else if (prev == State::FAULT) publishEvent("recovered");
  if (next == State::GRANTED) publishEvent("granted");
  if (next == State::DENIED) publishEvent("denied");
  if (next == State::WARNING) publishEvent("warning");
  if (next == State::ALARM) publishEvent("alarm");
  if (next == State::NORMAL && (prev == State::WARNING || prev == State::ALARM)) publishEvent("cleared");

  drawDisplay();
  publishStatus();
  lastStatusMs = millis();
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
void handleReset(const char* origin) {
  if ((state == State::DENIED || state == State::ALARM) && !alarmAcked) {
    alarmAcked = true;
    Serial.printf("[INPUT] reset (%s) -> alarm acknowledged (buzzer off)\n", origin);
  } else {
    Serial.printf("[INPUT] reset (%s) pressed (no active alarm)\n", origin);
  }
}

void readModeSwitches() {
  Role r = digitalRead(PIN_SW_ROLE) == HIGH ? Role::ZONE : Role::GATE;
  Source s = digitalRead(PIN_SW_SOURCE) == HIGH ? Source::TEST : Source::LIVE;
  if (r == role && s == source) return;
  bool roleChanged = r != role;
  role = r;
  source = s;
  Serial.printf("[MODE] role=%s source=%s node=%s\n", role == Role::GATE ? "GATE" : "ZONE",
                source == Source::TEST ? "TEST" : "LIVE", nodeName());
  snap = Snapshot();  // data mode lama tidak berlaku
  violationStartMs = 0;
  gateRearmUntil = 0;
  if (roleChanged && mqtt.connected()) mqtt.disconnect();  // sambung ulang dengan topic node yang baru
  enterState(State::FAULT);
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

// ---------- MQTT: pesan masuk ----------
// detection: {"ts":..,"person_count":2,"persons":[{"id":1,"helmet":true,"vest":true,"violation_s":0},...],"violators":[2]}
void handleDetection(JsonDocument& doc) {
  if (source != Source::LIVE) return;  // mode TEST memakai tombol
  Snapshot s;
  JsonArray persons = doc["persons"].as<JsonArray>();
  s.personCount = doc["person_count"] | (int)persons.size();
  for (JsonObject p : persons) {
    bool helmet = p["helmet"] | false;
    bool vest = p["vest"] | false;
    if (helmet && vest) continue;
    s.violatorCount++;
    s.missingHelmet |= !helmet;
    s.missingVest |= !vest;
    if (!p["violation_s"].isNull()) s.maxViolationS = max(s.maxViolationS, p["violation_s"].as<float>());
  }
  s.receivedMs = millis();
  snap = s;

  String summary = String(s.personCount) + "/" + s.violatorCount + "/" + missingList();
  if (summary != lastDetectionSummary) {
    lastDetectionSummary = summary;
    Serial.printf("[MQTT] rx detection persons=%d violators=%d missing=%s\n", s.personCount, s.violatorCount,
                  missingList().c_str());
  }
}

void onMqttMessage(char* topic, byte* payload, unsigned int length) {
  String t(topic);
  if (t == heartbeatTopic()) {
    if (lastHeartbeatMs == 0 || millis() - lastHeartbeatMs > FAILSAFE_TIMEOUT_MS) Serial.println("[MQTT] heartbeat ok");
    lastHeartbeatMs = millis();
    return;
  }
  JsonDocument doc;
  if (deserializeJson(doc, payload, length)) {
    Serial.printf("[MQTT] invalid JSON on %s\n", topic);
    return;
  }
  if (t == topicFor("detection")) handleDetection(doc);
  else if (t == topicFor("override")) {
    const char* cmd = doc["cmd"] | "";
    Serial.printf("[MQTT] rx override cmd=%s\n", cmd);
    if (!strcmp(cmd, "reset")) handleReset("mqtt");
  }
}

// ---------- Jaringan (coba ulang tiap NET_RETRY_MS, tidak menghentikan logic lokal) ----------
void networkLoop() {
  unsigned long now = millis();
  if (WiFi.status() != WL_CONNECTED) {
    if (wifiUp) {
      wifiUp = false;
      Serial.println("[NET] wifi lost");
    }
    if (lastWifiAttemptMs == 0 || now - lastWifiAttemptMs > 2 * NET_RETRY_MS) {
      lastWifiAttemptMs = now;
      Serial.printf("[NET] wifi connecting ssid=%s\n", WIFI_SSID);
      WiFi.begin(WIFI_SSID, WIFI_PASSWORD, 6);  // channel 6 mempercepat koneksi Wokwi-GUEST
    }
    return;
  }
  if (!wifiUp) {
    wifiUp = true;
    Serial.printf("[NET] wifi connected ip=%s\n", WiFi.localIP().toString().c_str());
    configTime(0, 0, "pool.ntp.org", "time.google.com");
  }

  if (!mqtt.connected()) {
    if (lastMqttAttemptMs != 0 && now - lastMqttAttemptMs < NET_RETRY_MS) return;
    lastMqttAttemptMs = now;
    String clientId = String("iris-") + nodeName() + "-" + String((uint32_t)ESP.getEfuseMac(), HEX);
    String willTopic = topicFor("status");
    String will = String("{\"node\":\"") + nodeName() + "\",\"state\":\"OFFLINE\"}";
    Serial.printf("[MQTT] connecting %s:%d (TLS) id=%s\n", MQTT_HOST, MQTT_PORT, clientId.c_str());
    bool useAuth = strlen(MQTT_USERNAME) > 0;
    bool ok = mqtt.connect(clientId.c_str(), useAuth ? MQTT_USERNAME : nullptr, useAuth ? MQTT_PASSWORD : nullptr,
                           willTopic.c_str(), 0, true, will.c_str());
    if (!ok) {
      Serial.printf("[MQTT] connect failed rc=%d\n", mqtt.state());
      return;
    }
    mqtt.subscribe(heartbeatTopic().c_str());
    mqtt.subscribe(topicFor("detection").c_str());
    mqtt.subscribe(topicFor("override").c_str());
    Serial.printf("[MQTT] connected, subscribed %s/{%s,server}/...\n", MQTT_TOPIC_PREFIX, nodeName());
    publishStatus();
  }
  mqtt.loop();
}

// ---------- Setup & loop ----------
void setup() {
  Serial.begin(115200);
  pinMode(PIN_LED_GREEN, OUTPUT);
  pinMode(PIN_LED_YELLOW, OUTPUT);
  pinMode(PIN_LED_RED, OUTPUT);
  pinMode(PIN_SW_ROLE, INPUT_PULLUP);   // switch hanya menyambung ke GND; posisi lepas = HIGH
  pinMode(PIN_SW_SOURCE, INPUT_PULLUP);
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

  WiFi.mode(WIFI_STA);
  tlsClient.setCACert(CA_CERT);  // verifikasi sertifikat broker (bukan setInsecure)
  tlsClient.setHandshakeTimeout(8);  // batasi lama loop tertahan saat (re)connect TLS (detik)
  mqtt.setServer(MQTT_HOST, MQTT_PORT);
  mqtt.setBufferSize(1024);      // payload detection bisa > 256 byte (default)
  mqtt.setCallback(onMqttMessage);

  stateSince = millis();
  drawDisplay();
}

void loop() {
  networkLoop();
  readModeSwitches();
  if (source == Source::TEST) readTestButtons();
  if (btnReset.pressed()) handleReset("button");

  State next = role == Role::GATE ? evaluateGate() : evaluateZone();
  if (next != state) {
    enterState(next);
  } else if (missingMask() != lastMissingMask) {
    Serial.printf("[STATE] %s missing=%s\n", stateName(state), missingList().c_str());
    drawDisplay();
    publishStatus();
  }
  lastMissingMask = missingMask();

  updateLeds();
  updateBuzzer();
  if (millis() - lastDisplayMs > 500) {  // perbarui durasi di OLED (hanya digambar jika berubah)
    lastDisplayMs = millis();
    drawDisplay();
  }
  if (millis() - lastStatusMs > STATUS_PERIOD_MS) {
    lastStatusMs = millis();
    publishStatus();
  }
  delay(10);
}
