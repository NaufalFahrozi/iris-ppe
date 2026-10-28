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

Verifikasi visual (2026-10-29): rangkaian dibuka di editor wokwi.com. Versi pertama terhubung benar tapi semrawut;
tata letak dirapikan (input kiri, output kanan, label `wokwi-text`, bus GND) dan pin dipetakan ulang (GPIO v2,
`docs/design.md` bagian 3). Bukti: `docs/assets/irisan1/wokwi-circuit-first-look.jpg` (sebelum) dan
`docs/assets/irisan1/wokwi-circuit.png` (sesudah). Setelah pemetaan ulang, I1-1..I1-8 diulang dan **lulus**
(LED dicek di GPIO 18/17/16). T3 penuh diuji di irisan 2.

## Irisan 2 — End-to-end MQTT (ESP32 LIVE ↔ broker.hivemq.com:8883 TLS ↔ Python)

Dijalankan dengan `.venv\Scripts\python firmware/test/mqtt_e2e.py gate|zone` (2026-10-29). Python berperan sebagai
server vision (heartbeat 1 Hz, detection 2 Hz) **tanpa kamera/YOLO**; ESP32 berjalan di Wokwi mode LIVE dan status
balasannya dibaca kembali dari broker. Latency = publish detection → status ESP32 diterima kembali (dua kali lewat broker).

| ID | Test Case | Input/Condition | Expected Result | Actual Result | Latency | Status |
|---|---|---|---|---|---|---|
| T1 | Satu orang, APD lengkap | detection 1 orang helmet+vest | GRANTED, palang terbuka, status terkirim | `state=GRANTED gate=open` | 0,78 s | Lulus |
| T2 | Rompi tidak dipakai | 1 orang `vest=false` | DENIED, missing `[vest]` | `state=DENIED missing=['vest']` | 0,86 s | Lulus |
| T3 | Server vision mati | heartbeat & detection dihentikan | FAULT, gerbang terkunci | `state=FAULT gate=closed` | 8,35 s* | Lulus |
| T3b | Server pulih | heartbeat & detection kembali | Keluar FAULT, event `recovered` | `state=IDLE` | 1,09 s | Lulus |
| T4 | Dua orang, satu tidak patuh | orang 2 `helmet=false` | Palang tetap tertutup | `state=DENIED persons=2` | 1,12 s | Lulus |
| T5 | Pelanggar masuk saat palang terbuka | GRANTED lalu orang 2 tanpa rompi | Palang menutup + alarm | `GRANTED -> DENIED gate=closed` | 0,84 s | Lulus |
| OV | Override reset dari dashboard | publish `{"cmd":"reset"}` saat DENIED | Buzzer dibungkam | log `reset (mqtt) -> alarm acknowledged` | – | Lulus |
| T6a | Zona: helm dilepas | `helmet=false`, `violation_s` dari server | WARNING setelah ≥ 3 s | `state=WARNING` | 4,39 s | Lulus |
| T6b | Zona: helm dilepas lama | `violation_s` terus naik | ALARM setelah ≥ 8 s + event `alarm` | `state=ALARM` | +5,13 s | Lulus |
| T6c | Zona: patuh kembali | `helmet=true` | NORMAL otomatis + event `cleared` | `state=NORMAL` | 1,23 s | Lulus |

\* Batas fail-safe 5 s diukur dalam waktu simulasi; Wokwi berjalan lebih lambat dari waktu nyata saat WiFi/TLS aktif,
sehingga dari sisi Python terukur 8–13 s. Pada hardware nyata belum diukur.

Bukti: `docs/assets/irisan2/e2e-gate.md`, `e2e-zone.md` (tabel + daftar event yang diterima), `e2e-*-serial.log`.

Catatan: satu kali run gate gagal 0/9 karena simulasi Wokwi tidak berjalan (log serial kosong); penyebab tidak terekam
karena output wokwi-cli saat itu tidak disimpan. Harness sekarang menyimpan output wokwi-cli dan berhenti jika simulasi
mati. Run ulang pada firmware yang sama: 9/9 lulus.

Diulang setelah GPIO v2 (rangkaian dirapikan): gate 9/9 dan zone 4/4 tetap lulus (latency 0,9–1,4 s; T3 9,6 s);
`e2e-gate.md`/`e2e-zone.md` berisi hasil run terakhir.

Regresi mode TEST (irisan 1) setelah kode jaringan ditambahkan: gate, zone, failsafe **lulus**. Ditemukan bahwa
handshake TLS menahan `loop()` beberapa detik; scenario kini menunggu `[MQTT] connected` sebelum menekan tombol, dan
handshake dibatasi 8 s (lihat `docs/design.md` bagian 5, keterbatasan).

## Irisan 4 — Dashboard (Plotly Dash)

Diuji 2026-10-29 dengan dua ESP32 di Wokwi (gate1 & zoneA, mode LIVE) + `vision/sim_publisher.py` sebagai server vision,
lewat broker.hivemq.com. Dashboard: `.venv\Scripts\python dashboard/app.py`.

| ID | Test Case | Input/Condition | Expected Result | Actual Result | Status | Bukti |
|---|---|---|---|---|---|---|
| D1 | Status node live | 2 node ESP32 publish status | Kartu gate1/zoneA menampilkan state, palang, APD kurang, umur data | gate1 `GRANTED` (palang terbuka), zoneA `NORMAL`, sumber live | Lulus | `docs/assets/irisan4/dashboard-live-top.jpg` |
| D2 | Compliance rate | detection 2 Hz dari simulator | Garis % orang patuh per 30 s + stat tile sesi | Grafik terisi; tile 43–44 % (sesuai skenario demo) | Lulus | `dashboard-compliance-chart.jpg` |
| D3 | Pelanggaran per waktu | event `denied`/`alarm` dari ESP32 | Bar bertumpuk helm/rompi per 30 s | Bar muncul sesuai event | Lulus | `dashboard-live-top.jpg` |
| D4 | Reset alarm dari dashboard | klik **Reset alarm** gate1 | Override `{"cmd":"reset"}` terkirim | Notifikasi "Perintah reset dikirim ke gate1"; penerimaan di ESP32 dibuktikan uji OV irisan 2 | Lulus | screenshot sesi, `docs/assets/irisan2/e2e-gate.md` |
| D5 | Server vision berhenti | simulator dihentikan | Indikator "Server vision offline", node zona FAULT, event Gangguan | Sesuai | Lulus | `dashboard-fault-after-sim-stop.jpg` |

Temuan saat uji: (1) tombol di kartu node sempat hilang-muncul tiap refresh sehingga klik bisa terlewat; diperbaiki
dengan merender kerangka kartu sekali dan hanya memperbarui isinya. (2) Satu kali run demo kedua node Wokwi tidak
berjalan (penyebab tidak terekam); run ulang dengan log wokwi-cli disimpan berjalan normal.

## Irisan 3 — Pipeline vision (video → YOLO + tracking → aturan → MQTT → ESP32)

Diuji 2026-10-29 dengan bobot sementara (run 2, epoch 10) dan video stok Pexels (lisensi Pexels, tidak di-commit):
`pexels-5423610` (1 pekerja, helm hitam + rompi, tampak belakang) dan `pexels-8965561` (pekerja berhelm tanpa rompi).
ESP32 di Wokwi mode LIVE gate1, lewat broker.hivemq.com. Skrip: `firmware/test/vision_e2e.py`.

| ID | Test Case | Input/Condition | Expected Result | Actual Result | Status | Bukti |
|---|---|---|---|---|---|---|
| V1 | Aturan kepatuhan (unit) | Kotak buatan: APD lengkap, rompi hilang, helm di tangan, helm milik orang lain, ROI, kedip 35 FPS | Sesuai aturan; status tidak berkedip | 7/7 lulus | Lulus | `vision/test_compliance.py` |
| V2 | Pekerja patuh (T1 dengan video) | Video 5423610 | Akhirnya GRANTED dan stabil | Sebelum perbaikan: palang **buka-tutup 6×** (keyakinan helm hitam 0,16–0,36 berkedip di sekitar ambang). Setelah voting berbasis waktu 1 s: DENIED sekali di awal, lalu GRANTED stabil | Lulus setelah perbaikan | `docs/assets/irisan3/vision-e2e-serial.log` |
| V3 | Rompi tidak dipakai (T2 dengan video) | Video 8965561 | DENIED, missing=vest | DENIED stabil, missing=vest | Lulus | idem |
| V4 | Vision berhenti (T3) | Proses vision selesai | FAULT, gerbang terkunci | `DENIED -> FAULT` ±5 s setelah video habis | Lulus | idem |
| V5 | Kecepatan | 1080p, RTX 4050 berbagi GPU dengan training | Real-time | 33–40 FPS (diukur pipeline) | Lulus | `vision-e2e-vision.log` |

Temuan: deteksi helm hitam tampak belakang lemah pada bobot sementara (DENIED awal di V2). Ditindaklanjuti dengan run 3
(data helm ×19) dan ambang per kelas yang akan dihitung dari kurva F1 validasi.

## Skenario utama (T1–T6)

| ID | Test Case | Input/Condition | Expected Result | Actual Result | Status | Bukti |
|---|---|---|---|---|---|---|
| T1 | Satu orang, APD lengkap, di gerbang | | Palang terbuka, LED hijau, status `GRANTED` terkirim | | Belum diuji | |
| T2 | Satu orang, rompi tidak dipakai | | Palang tertutup, buzzer, OLED menampilkan item yang kurang | | Belum diuji | |
| T3 | Server vision mati / heartbeat berhenti | | Fail-safe: gerbang terkunci, indikator gangguan | | Belum diuji | |
| T4 | Dua orang, satu tidak patuh | | Palang tetap tertutup | | Belum diuji | |
| T5 | Pelanggar masuk ROI saat palang terbuka | | Palang menutup, alarm | | Belum diuji | |
| T6 | Zona kerja: pekerja melepas helm makin lama | | Abaikan → peringatan → alarm + event dashboard, reset saat patuh | | Belum diuji | |
