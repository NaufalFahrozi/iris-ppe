# Testing Log — IRIS

Setiap irisan dicatat di sini: Test Case, Input/Condition, Expected Result, Actual Result, Status, Bukti.

## Uji kelayakan (langkah 0)

| ID | Test Case | Input/Condition | Expected Result | Actual Result | Status | Bukti |
|---|---|---|---|---|---|---|
| F0 | ESP32 + LED + tombol di Wokwi CLI (2026-10-29) | Scenario `firmware/test/feasibility.test.yaml`: tekan lalu lepas `btn1` (GPIO27, pull-up) | Log `[BOOT]`, lalu `button=PRESSED led=ON`, lalu `button=RELEASED led=OFF`; LED GPIO26 mengikuti tombol | Ketiga log cocok, wokwi-cli v0.29.1 "Scenario completed successfully", exit 0 | Lulus (verifikasi visual rangkaian di editor Wokwi belum) | `docs/assets/step0/feasibility-serial.log` |

## Skenario utama (T1–T6)

| ID | Test Case | Input/Condition | Expected Result | Actual Result | Status | Bukti |
|---|---|---|---|---|---|---|
| T1 | Satu orang, APD lengkap, di gerbang | | Palang terbuka, LED hijau, status `GRANTED` terkirim | | Belum diuji | |
| T2 | Satu orang, rompi tidak dipakai | | Palang tertutup, buzzer, OLED menampilkan item yang kurang | | Belum diuji | |
| T3 | Server vision mati / heartbeat berhenti | | Fail-safe: gerbang terkunci, indikator gangguan | | Belum diuji | |
| T4 | Dua orang, satu tidak patuh | | Palang tetap tertutup | | Belum diuji | |
| T5 | Pelanggar masuk ROI saat palang terbuka | | Palang menutup, alarm | | Belum diuji | |
| T6 | Zona kerja: pekerja melepas helm makin lama | | Abaikan → peringatan → alarm + event dashboard, reset saat patuh | | Belum diuji | |
