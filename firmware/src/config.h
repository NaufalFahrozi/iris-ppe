// IRIS — konfigurasi pin dan konstanta. Detail & alasan: docs/design.md
#pragma once

// ---- Pin (lihat docs/design.md bagian 3) ----
constexpr int PIN_SERVO = 18;
constexpr int PIN_BUZZER = 19;
constexpr int PIN_LED_GREEN = 25;
constexpr int PIN_LED_YELLOW = 26;
constexpr int PIN_LED_RED = 27;
constexpr int PIN_SDA = 21;
constexpr int PIN_SCL = 22;
constexpr int PIN_BTN_PERSON = 32;  // tombol ke GND, pull-up internal
constexpr int PIN_BTN_HELMET = 33;
constexpr int PIN_BTN_VEST = 14;
constexpr int PIN_BTN_RESET = 13;
constexpr int PIN_SW_ROLE = 34;     // LOW = GATE, HIGH = ZONE (input-only)
constexpr int PIN_SW_SOURCE = 35;   // LOW = LIVE (MQTT), HIGH = TEST (tombol)

// ---- Jaringan & MQTT (broker publik, tidak ada rahasia; lihat CLAUDE.md bagian 5) ----
constexpr const char* WIFI_SSID = "Wokwi-GUEST";
constexpr const char* WIFI_PASSWORD = "";
constexpr const char* MQTT_HOST = "broker.hivemq.com";
constexpr int MQTT_PORT = 8883;                      // TLS
constexpr const char* MQTT_USERNAME = "";            // kosong untuk broker publik
constexpr const char* MQTT_PASSWORD = "";
constexpr const char* MQTT_TOPIC_PREFIX = "sic8-montblanc/iris";
constexpr unsigned long NET_RETRY_MS = 5000;

// ---- Identitas node ----
constexpr const char* NODE_GATE = "gate1";
constexpr const char* NODE_ZONE = "zoneA";

// ---- Waktu (nilai awal, difinalkan saat pengujian) ----
constexpr unsigned long FAILSAFE_TIMEOUT_MS = 5000;  // tanpa data selama ini -> FAULT
constexpr unsigned long OPEN_WINDOW_MS = 5000;       // lama palang terbuka per izin
constexpr unsigned long GATE_REARM_MS = 2000;        // jeda tutup sebelum boleh buka lagi
constexpr float ZONE_WARN_S = 3.0;                   // pelanggaran < ini diabaikan
constexpr float ZONE_ALARM_S = 8.0;                  // batas eskalasi ke alarm
constexpr unsigned long STATUS_PERIOD_MS = 5000;     // status periodik
constexpr unsigned long DEBOUNCE_MS = 30;

// ---- Aktuator ----
constexpr int SERVO_CLOSED_DEG = 0;
constexpr int SERVO_OPEN_DEG = 90;
constexpr int BUZZER_FREQ_HZ = 2000;
constexpr int OLED_ADDR = 0x3C;
