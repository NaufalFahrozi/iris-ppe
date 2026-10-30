# Kontribusi Anggota — IRIS

Sumber untuk bab "Pembagian Peran Anggota" di laporan.

## Cara kerja tim

- Tim bekerja bersama dalam sesi kerja di satu laptop (laptop ketua, GPU RTX 4050), sehingga sebagian besar pekerjaan
  dilakukan berdampingan, bukan terpisah per orang.
- Implementasi kode, training, dan draf dokumen dibantu **AI coding agent (Claude Code)** yang diorkestrasi oleh ketua.
  Tim menentukan konsep, aturan, dan keputusan teknis; agent menulis kode dan menjalankan pengujian; hasilnya ditinjau
  dan diuji bersama. Hal ini dinyatakan terbuka agar tidak ada klaim yang menyesatkan.
- Setiap anggota memegang satu bidang sebagai **penanggung jawab utama**: memahami dan menjelaskan bagian itu saat
  presentasi, meninjau hasilnya, dan memutuskan perubahan di bidang tersebut.
- Author commit di GitHub mengikuti bidang yang disentuh (kebijakan tim, lihat `CLAUDE.md` bagian 10), bukan jumlah jam
  kerja seseorang.

## Pembagian per anggota

### Muhammad Naufal Fahrozi — Project Lead & System Integrator

- Perencanaan proyek, jadwal, dan pembagian irisan kerja; orkestrasi AI agent; maintainer repo GitHub.
- Keputusan teknis utama: arsitektur server vision terpusat + ESP32 per titik, broker HiveMQ publik (TLS 8883),
  pemilihan dataset dan model YOLO26m, kebijakan fail-safe.
- Integrasi end-to-end vision → MQTT → ESP32 → dashboard dan koordinasi pengujian (irisan 2–5).
- Menjalankan benchmark training di Google Colab T4 sebagai pembanding laptop.
- Bagian laporan: latar belakang, problem statement & tujuan, target user, arsitektur, kesimpulan, pengembangan lanjutan.
- Bukti: `CLAUDE.md`, `README.md`, `docs/demo-runbook.md`, `docs/testing-log.md` (irisan 2–5).

### Christian Mahatma Bima Alpindo — Hardware & Embedded Engineer

- Pemilihan komponen dan alasannya (ESP32, servo SG90, LED, buzzer, OLED SSD1306, push button, switch).
- Rangkaian dan wiring Wokwi, pemetaan GPIO yang aman (tanpa strapping pin untuk output).
- Firmware ESP32: state machine gerbang (FAULT/IDLE/GRANTED/DENIED) dan zona (FAULT/NORMAL/WARNING/ALARM), aktuator,
  log Serial terstruktur, MQTT TLS, fail-safe heartbeat.
- Pengujian sisi perangkat di wokwi-cli dan wokwi.com; proyek wokwi.com untuk pengumpulan.
- Bagian laporan: daftar komponen, wiring diagram, Pin/GPIO, logika program ESP32.
- Bukti: `firmware/`, `docs/design.md` bagian 2–4, `docs/assets/irisan1/`, `docs/assets/irisan2/`.

### Tua Delima Sitompul — AI & Backend Engineer

- Dataset: SH17 sebagai utama, ditambah 4 dataset publik; remap kelas, pseudo-label person/head, total 17.313 gambar train.
- Training YOLO26m (3 run) dan evaluasi: AP per kelas, ambang keyakinan F1, FPS.
- Pipeline vision: tracking ByteTrack, aturan kepatuhan berbasis posisi kotak, voting 1 detik, timer pelanggaran per
  orang, ROI gerbang, publisher MQTT dan heartbeat.
- Sisi data dashboard: langganan MQTT, compliance rate, pencatatan event ke CSV.
- Merapikan isi, format, dan versi final laporan .docx.
- Bagian laporan: computer vision, komunikasi MQTT, dashboard (sisi data).
- Bukti: `training/`, `vision/`, `dashboard/app.py`, `docs/assets/model/`, `docs/assets/irisan3/`.

### Kalingga Dwindra Putraka — Product & Visual Designer

- Identitas visual IRIS (logo), block diagram dan diagram arsitektur.
- Desain tampilan dashboard dan tata letak screenshot pengujian.
- Cover dan tata letak laporan .docx; penyusunan draf laporan 16 bab.
- Storyboard dan editing video demo .mp4.
- Bagian laporan: cover, semua diagram/visual, screenshot & tata letak, video demo.
- Bukti: `docs/report-draft.md`, `docs/assets/`, video demo.

## Pengujian

Semua anggota ikut dalam pengujian skenario T1–T6 dan uji langsung di depan webcam dengan helm dan rompi
(`docs/testing-log.md`, `docs/demo-runbook.md`).

## Ringkasan untuk laporan (bab 13)

| Anggota | Peran | Tanggung jawab utama |
|---|---|---|
| Muhammad Naufal Fahrozi | Project Lead & System Integrator | Perencanaan, arsitektur, integrasi end-to-end, koordinasi uji, laporan final |
| Christian Mahatma Bima Alpindo | Hardware & Embedded Engineer | Komponen, wiring & GPIO Wokwi, firmware ESP32, uji perangkat |
| Tua Delima Sitompul | AI & Backend Engineer | Dataset, training & evaluasi YOLO, pipeline vision, MQTT, data dashboard |
| Kalingga Dwindra Putraka | Product & Visual Designer | Logo, diagram, desain dashboard, cover & tata letak laporan, video demo |

Implementasi dibantu AI coding agent (Claude Code) di bawah arahan ketua; seluruh anggota meninjau, menguji, dan mampu
menjelaskan bagiannya.
