# Testing Log — IRIS

Setiap irisan dicatat di sini: Test Case, Input/Condition, Expected Result, Actual Result, Status, Bukti.

## Uji kelayakan (langkah 0)

| ID | Test Case | Input/Condition | Expected Result | Actual Result | Status | Bukti |
|---|---|---|---|---|---|---|
| F0 | ESP32 + LED + tombol di Wokwi CLI (2026-10-29) | Scenario `firmware/test/feasibility.test.yaml`: tekan lalu lepas `btn1` (GPIO27, pull-up) | Log `[BOOT]`, lalu `button=PRESSED led=ON`, lalu `button=RELEASED led=OFF`; LED GPIO26 mengikuti tombol | Ketiga log cocok, wokwi-cli v0.29.1 "Scenario completed successfully", exit 0 | Lulus (verifikasi visual rangkaian di editor Wokwi belum) | `docs/assets/step0/feasibility-serial.log` |

F0 memakai sketch langkah 0 (commit `d5879cc`); sketch itu sudah digantikan firmware irisan 1.

## Irisan 1 — Gerbang & zona tanpa YOLO (mode TEST, wokwi-cli)

Dijalankan dengan `.venv\Scripts\python firmware/test/run_tests.py` (wokwi-cli v0.29.1, 2026-10-29). Hasil deteksi
disimulasikan tombol `PERSON/HELMET/VEST`. Ini menguji **logic ESP32**, belum pipeline vision/MQTT.

| ID | Test Case | Input/Condition | Expected Result | Actual Result | Status | Bukti |
|---|---|---|---|---|---|---|
| I1-1 | Gerbang: T2 (logic) | person=1, helmet=0, vest=0 | `IDLE -> DENIED`, missing helmet+vest, palang tertutup, OLED "DITOLAK" | Sesuai; event `denied`; OLED "Kurang: HELM + ROMPI" | Lulus | `docs/assets/irisan1/gate-serial.log`, `oled-gate-denied.png` |
| I1-2 | Gerbang: reset supervisor | `RESET` saat DENIED | Buzzer dibungkam, palang tetap tertutup | `reset -> alarm acknowledged`, state tetap DENIED | Lulus | `gate-serial.log` |
| I1-3 | Gerbang: T1 (logic) | helmet=1, vest=1 | `DENIED -> GRANTED`, servo 90°, LED hijau (GPIO25=1) | Sesuai; `expect-pin esp:25 == 1` lulus | Lulus | `gate-serial.log`, `oled-gate-granted.png` |
| I1-4 | Gerbang: T5 (logic) | Rompi dilepas saat palang terbuka | `GRANTED -> DENIED`, servo 0°, LED merah (GPIO27=1) | Sesuai | Lulus | `gate-serial.log` |
| I1-5 | Gerbang: jendela buka terbatas | Tetap patuh setelah izin | Palang menutup setelah `OPEN_WINDOW_MS` (5 s), buka lagi setelah `GATE_REARM_MS` (2 s) | `GRANTED -> IDLE -> GRANTED` | Lulus | `gate-serial.log` |
| I1-6 | Zona: pelanggaran singkat | Helm dilepas ±1,5 s lalu dipakai | Diabaikan, tetap NORMAL | Tidak ada WARNING | Lulus | `zone-serial.log` |
| I1-7 | Zona: T6 (logic) | Helm dilepas terus | NORMAL → WARNING (3 s, LED kuning) → ALARM (8 s, LED merah, event) → NORMAL saat patuh | Sesuai; event `warning` 3,0 s, `alarm` 8,0 s, `cleared` | Lulus | `zone-serial.log`, `oled-zone-warning.png`, `oled-zone-alarm.png` |
| I1-8 | Fail-safe tanpa data (bagian T3) | `SOURCE=LIVE`, belum ada data vision | Tetap FAULT, palang tertutup, OLED "OFFLINE" | Status periodik `"state":"FAULT","gate":"closed"` | Lulus | `failsafe-serial.log`, `oled-gate-fault.png` |

Belum: **verifikasi visual rangkaian** di editor Wokwi (wajib menurut CLAUDE.md), dan T3 penuh (heartbeat berhenti
setelah sempat aktif) yang menunggu irisan 2.

## Skenario utama (T1–T6)

| ID | Test Case | Input/Condition | Expected Result | Actual Result | Status | Bukti |
|---|---|---|---|---|---|---|
| T1 | Satu orang, APD lengkap, di gerbang | | Palang terbuka, LED hijau, status `GRANTED` terkirim | | Belum diuji | |
| T2 | Satu orang, rompi tidak dipakai | | Palang tertutup, buzzer, OLED menampilkan item yang kurang | | Belum diuji | |
| T3 | Server vision mati / heartbeat berhenti | | Fail-safe: gerbang terkunci, indikator gangguan | | Belum diuji | |
| T4 | Dua orang, satu tidak patuh | | Palang tetap tertutup | | Belum diuji | |
| T5 | Pelanggar masuk ROI saat palang terbuka | | Palang menutup, alarm | | Belum diuji | |
| T6 | Zona kerja: pekerja melepas helm makin lama | | Abaikan → peringatan → alarm + event dashboard, reset saat patuh | | Belum diuji | |
