# IRIS: Smart PPE Compliance Gate and Monitoring System Using Computer Vision

Proyek tugas akhir *Selection Phase 2 – IoT: Device and Hardware Discovery*, **Samsung Innovation Campus Batch 8** (jalur IoT).
Tim **Montblanc**, Universitas Mulawarman.

IRIS memeriksa kepatuhan Alat Pelindung Diri (APD) / *Personal Protective Equipment* (PPE) — helm dan rompi — memakai computer vision (YOLO), lalu mengirim hasilnya lewat MQTT (HiveMQ public broker, TLS) ke ESP32 yang menggerakkan palang gerbang, LED, buzzer, dan OLED. Data kepatuhan ditampilkan di dashboard Python (paho-mqtt + Plotly).

Dua mode:

1. **Gerbang (preventif):** palang hanya terbuka jika semua orang di area masuk memakai helm dan rompi.
2. **Monitoring zona (detektif):** pelanggaran di zona kerja dieskalasi berdasarkan durasi (abaikan → peringatan → alarm), reset otomatis saat patuh kembali.

> Status: dalam pengembangan (stage 2). Lihat [CLAUDE.md](CLAUDE.md) bagian Status.

## Arsitektur singkat

```
Kamera ─► Server vision (YOLO + tracking + aturan) ─► broker.hivemq.com (MQTT, TLS 8883)
                                                      ├─► ESP32 gerbang (servo, LED, buzzer, OLED, tombol)
                                                      ├─► ESP32 zona (LED, buzzer, OLED)
                                                      └─► Dashboard Python (paho-mqtt + Plotly)
```

## Struktur repo

| Folder | Isi |
|---|---|
| `firmware/` | Firmware ESP32 (PlatformIO) + rangkaian Wokwi (`diagram.json`, `wokwi.toml`) |
| `vision/` | Inferensi YOLO, tracking, aturan kepatuhan, publisher MQTT |
| `training/` | Konfigurasi dan skrip training/evaluasi model (tanpa dataset) |
| `dashboard/` | Dashboard paho-mqtt + Plotly |
| `docs/` | Desain, log pengujian, kontribusi, aset laporan |

## Cara menjalankan

1. Salin `.env.example` menjadi `.env`, isi `WOKWI_CLI_TOKEN` (MQTT sudah terisi untuk broker publik). Jangan di-commit.
2. Python: `uv venv --python 3.12 .venv`, pasang PyTorch CUDA (`uv pip install --python .venv torch torchvision --torch-backend=auto`),
   lalu `uv pip install --python .venv -r requirements.txt`.
3. Firmware: `cd firmware && pio run`.
4. Uji otomatis di Wokwi (dari root repo):
   - Mode TEST (tombol): `.venv\Scripts\python firmware/test/run_tests.py`
   - End-to-end MQTT (ESP32 mode LIVE ↔ broker ↔ Python): `.venv\Scripts\python firmware/test/mqtt_e2e.py gate` / `zone`
5. Simulator server vision (tanpa kamera): `.venv\Scripts\python vision/sim_publisher.py --node gate1 --scenario demo`

Rancangan, GPIO, state machine, dan format MQTT: [docs/design.md](docs/design.md). Hasil uji: [docs/testing-log.md](docs/testing-log.md).

## Link

- Proyek Wokwi: _menyusul_
- Video demo: _menyusul_
- Bobot model final: _menyusul (GitHub Releases)_

## Tim

| Nama | Peran |
|---|---|
| Muhammad Naufal Fahrozi | Project Lead & System Integrator |
| Christian Mahatma Bima Alpindo | Hardware & Embedded Engineer |
| Tua Delima Sitompul | AI & Backend Engineer |
| Kalingga Dwindra Putraka | Product & Visual Designer |

## Atribusi dataset

Model dilatih memakai **SH17 Dataset** (lisensi CC BY-NC-SA 4.0, non-komersial):

> H. M. Ahmad and A. Rahimi, "SH17: A dataset for human safety and personal protective equipment detection in manufacturing industry," arXiv:2407.04590, 2024. Sumber: https://github.com/ahmadmughees/SH17dataset

Dataset tidak disertakan di repo ini.

## Lisensi

Kode di repo ini dirilis di bawah [GNU AGPL-3.0](LICENSE), selaras dengan Ultralytics YOLO.
