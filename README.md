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
6. Dashboard: `.venv\Scripts\python dashboard/app.py`, lalu buka http://127.0.0.1:8050
   (status node, compliance rate, pelanggaran per waktu, event terbaru, tombol reset alarm; event juga dicatat ke
   `dashboard/data/events.csv`).
7. Proyek wokwi.com: `.venv\Scripts\python firmware/export_wokwi_web.py` lalu tempel isi `firmware/wokwi-web/` ke editor wokwi.com.

8. Server vision (kamera → YOLO → MQTT): `.venv\Scripts\python vision/run_vision.py --source 0 --node gate1 --show`

**Panduan uji & demo langkah demi langkah: [docs/demo-runbook.md](docs/demo-runbook.md).**
Rancangan, GPIO, state machine, dan format MQTT: [docs/design.md](docs/design.md). Hasil uji: [docs/testing-log.md](docs/testing-log.md).

## Pasang di laptop lain (anggota tim)

Butuh: Windows 10/11, [Git](https://git-scm.com/), [uv](https://docs.astral.sh/uv/) (`winget install astral-sh.uv`),
webcam. GPU NVIDIA disarankan; tanpa GPU tetap jalan di CPU tetapi jauh lebih lambat.

```powershell
git clone https://github.com/NaufalFahrozi/iris-ppe.git
cd iris-ppe
uv venv --python 3.12 .venv
uv pip install --python .venv torch torchvision --torch-backend=auto
uv pip install --python .venv -r requirements.txt
copy .env.example .env
mkdir models
curl.exe -L -o models/iris-best.pt https://github.com/NaufalFahrozi/iris-ppe/releases/download/model-v1/iris-best.pt
```

Lalu jalankan (dua terminal):

```powershell
.venv\Scripts\python dashboard/app.py                                    # buka http://127.0.0.1:8050
.venv\Scripts\python vision/run_vision.py --source 0 --node gate1 --show  # webcam → MQTT
```

ESP32-nya dijalankan di proyek wokwi.com (link di bawah): klik ▶, tunggu "MQTT connected", geser switch SOURCE ke LIVE.

Catatan:
- **Satu node hanya boleh dilayani satu server vision.** Kalau dua laptop menjalankan `run_vision.py --node gate1`
  bersamaan, ESP32 menerima dua aliran deteksi yang saling bertentangan. Laptop lain cukup menjalankan dashboard
  (dashboard boleh dibuka di banyak laptop sekaligus) atau memakai node lain (`--node zoneA`).
- Semua laptop memakai broker publik dan prefix topic yang sama, jadi tidak perlu konfigurasi tambahan; `.env` hanya perlu
  `WOKWI_CLI_TOKEN` jika ingin memakai `wokwi-cli`.
- Ambang keyakinan bisa disesuaikan jika helm/rompi sulit terdeteksi: `--conf-helmet 0.2 --conf-vest 0.3`.

## Link

- Proyek Wokwi: https://wokwi.com/projects/479194485722835969
- Video demo: _menyusul_
- Bobot model final (YOLO26m, 4 kelas, 44 MB): GitHub Releases tag `model-v1` — metrik di
  [docs/assets/model/metrics.md](docs/assets/model/metrics.md)

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

Ditambah **Ultralytics Construction-PPE** (AGPL-3.0, https://docs.ultralytics.com/datasets/detect/construction-ppe/)
serta [Construction Site Safety Image Dataset (Roboflow)](https://www.kaggle.com/datasets/snehilsanyal/construction-site-safety-image-dataset-roboflow)
(CC BY 4.0), [Safety Helmet and Reflective Jacket](https://www.kaggle.com/datasets/niravnaik/safety-helmet-and-reflective-jacket)
(Apache 2.0), dan [HardHat-Vest Dataset v3](https://www.kaggle.com/datasets/muhammetzahitaydn/hardhat-vest-dataset-v3) (CC0)
untuk memperkuat deteksi helm dan rompi. Dataset tidak disertakan di repo ini. Karena dilatih dengan SH17, **bobot model
mengikuti CC BY-NC-SA 4.0 (non-komersial)**.

## Lisensi

Kode di repo ini dirilis di bawah [GNU AGPL-3.0](LICENSE), selaras dengan Ultralytics YOLO.
