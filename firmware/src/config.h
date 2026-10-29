// IRIS — konfigurasi pin dan konstanta. Detail & alasan: docs/design.md
#pragma once

// ---- Pin (lihat docs/design.md bagian 3): input di sisi kiri board, output di sisi kanan ----
// Output (sisi kanan, urut dari atas)
constexpr int PIN_BUZZER = 23;
constexpr int PIN_SDA = 22;
constexpr int PIN_SCL = 21;
constexpr int PIN_SERVO = 19;
constexpr int PIN_LED_GREEN = 18;
constexpr int PIN_LED_YELLOW = 17;
constexpr int PIN_LED_RED = 16;
// Input (sisi kiri, urut dari atas); semua ke GND dengan pull-up internal (aktif LOW)
constexpr int PIN_SW_ROLE = 32;     // slide switch: kiri (ke GND) = GATE, kanan (lepas) = ZONE
constexpr int PIN_SW_SOURCE = 33;   // slide switch: kiri (ke GND) = LIVE (MQTT), kanan (lepas) = TEST (tombol)
constexpr int PIN_BTN_PERSON = 25;
constexpr int PIN_BTN_HELMET = 26;
constexpr int PIN_BTN_VEST = 27;
constexpr int PIN_BTN_RESET = 14;

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
constexpr unsigned long FAILSAFE_TIMEOUT_MS = 8000;  // tanpa data selama ini -> FAULT (5 s memicu FAULT palsu
                                                     // akibat jeda broker publik saat uji video, 2026-10-29)
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
