// IRIS — uji kelayakan Wokwi (langkah 0): ESP32 + LED + tombol + log Serial.
// Akan diganti firmware gerbang pada irisan 1.
#include <Arduino.h>

const int LED_PIN = 26;
const int BUTTON_PIN = 27;           // tombol ke GND, pakai pull-up internal
const unsigned long DEBOUNCE_MS = 30;

bool stablePressed = false;
bool lastReading = false;
unsigned long lastChangeMs = 0;

void setup() {
  Serial.begin(115200);
  pinMode(LED_PIN, OUTPUT);
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  digitalWrite(LED_PIN, LOW);
  Serial.println("[BOOT] IRIS feasibility ready");
}

void loop() {
  bool reading = digitalRead(BUTTON_PIN) == LOW;
  if (reading != lastReading) {
    lastChangeMs = millis();
    lastReading = reading;
  }
  if (millis() - lastChangeMs > DEBOUNCE_MS && reading != stablePressed) {
    stablePressed = reading;
    digitalWrite(LED_PIN, stablePressed ? HIGH : LOW);
    Serial.printf("[IO] button=%s led=%s t=%lu\n",
                  stablePressed ? "PRESSED" : "RELEASED",
                  stablePressed ? "ON" : "OFF", millis());
  }
}
