# CLAUDE.md — IRIS · Tim Montblanc · Samsung Innovation Campus Batch 8

Konteks proyek untuk agent. **Baca seluruh file ini sebelum mengerjakan apa pun.** Setiap ada keputusan baru, perbarui bagian "Keputusan teknis", "Hal yang masih terbuka", dan "Status", lalu commit bersama perubahan terkait.

---

## 1. Identitas proyek

| | |
|---|---|
| Produk | **IRIS** (nama merek, bukan singkatan) |
| Judul | **IRIS: Smart PPE Compliance Gate and Monitoring System Using Computer Vision** |
| Program | Samsung Innovation Campus (SIC) Batch 8, jalur IoT |
| Tugas | Tugas akhir *Selection Phase 2 – IoT: Device and Hardware Discovery* |
| Tim | **Montblanc**, Universitas Mulawarman |
| Repo | `github.com/NaufalFahrozi/iris-ppe`, **publik**, owner ketua, anggota lain sebagai collaborator |
| Lisensi repo | **AGPL-3.0** (selaras dengan Ultralytics YOLO) |
| **Deadline stage 2** | **Jumat, 30 Oktober 2026, 24:00 WITA**. Target internal: kumpulkan paling lambat 22:00 WITA |

Anggota:

| Nama | Peran | GitHub |
|---|---|---|
| Muhammad Naufal Fahrozi | Ketua · Project Lead & System Integrator | [NaufalFahrozi](https://github.com/NaufalFahrozi) |
| Christian Mahatma Bima Alpindo | Hardware & Embedded Engineer | [ChristianMahatma](https://github.com/ChristianMahatma) |
| Tua Delima Sitompul | AI & Backend Engineer | [delima-sitompul](https://github.com/delima-sitompul) |
| Kalingga Dwindra Putraka | Product & Visual Designer | [Kal2501](https://github.com/Kal2501) |

Tim bekerja bersama di semua bagian; peran di bawah menunjukkan **penanggung jawab utama** tiap bidang.

| Peran | Tanggung jawab stage 2 | Bagian laporan yang dipegang |
|---|---|---|
| **Project Lead & System Integrator** (Naufal) | Perencanaan dan orkestrasi pekerjaan (termasuk agent), maintainer repo, integrasi end-to-end vision ↔ MQTT ↔ ESP32 ↔ dashboard, koordinasi pengujian, penyusunan laporan final | Latar belakang, problem statement & tujuan, target user, arsitektur sistem, kesimpulan, pengembangan lanjutan |
| **Hardware & Embedded Engineer** (Christian) | Pemilihan komponen dan alasannya, rangkaian & wiring di Wokwi, pemetaan GPIO, firmware ESP32 (state machine, aktuator, Serial log), pengujian sisi perangkat. Stage 3: perakitan hardware fisik | Daftar komponen, wiring diagram, Pin/GPIO, logika program ESP32 |
| **AI & Backend Engineer** (Delima) | Dataset, training & evaluasi YOLO, pipeline vision (tracking, aturan kepatuhan), publisher MQTT, backend data dashboard | Bagian computer vision, komunikasi MQTT, dashboard (sisi data) |
| **Product & Visual Designer** (Kalingga) | Identitas visual IRIS (logo), block diagram & diagram arsitektur, desain tampilan dashboard, cover & tata letak laporan, storyboard dan editing video demo | Cover, semua diagram/visual, screenshot & tata letak, video demo |

Semua anggota ikut pengujian dan harus bisa menjelaskan bagian yang dipegangnya saat presentasi. Catat pekerjaan yang benar-benar dilakukan tiap anggota di `docs/contributions.md`.

**Sumber kebenaran syarat tugas: `docs/study-case-guideline-stage-2.pdf`.** Kalau isi file ini bertentangan dengan PDF, ikuti PDF dan laporkan perbedaannya ke tim.

Repo ini tidak dipisah per stage. Kalau tim lolos ke stage 3, pekerjaan dilanjutkan di repo yang sama. Saat pengumpulan stage 2, buat tag `stage2-submission`.

---

## 2. Bahasa

- **Laporan .docx: Bahasa Indonesia.** Istilah teknis yang lazim boleh tetap bahasa Inggris (MQTT, GPIO, bounding box, payload). Pada penyebutan pertama tulis "Alat Pelindung Diri (APD) / *Personal Protective Equipment* (PPE)".
- **Judul proyek: bahasa Inggris** (seperti di atas), dipakai juga di cover laporan.
- Percakapan dengan tim: Bahasa Indonesia santai.
- Kode, nama variabel, nama file, dan commit message: bahasa Inggris.
- Komentar kode dan README: Bahasa Indonesia atau Inggris, konsisten per file.

---

## 3. Syarat tugas stage 2 (ringkasan PDF)

### 3.1 Tujuan peserta
Memilih komponen sesuai fungsi; merancang rangkaian ESP32 dengan input dan output; membuat logika program dasar; memahami alur **Input/Sensing → Processing/Logic → Output/Actuation → Communication → Visualization**; memakai Wokwi sebagai media utama simulasi dan pengujian; mendokumentasikan proyek secara sistematis dan bekerja sebagai tim.

### 3.2 Tahapan yang wajib diikuti
Ideasi → device discovery → hardware design → programming → communication → testing → documentation.

### 3.3 Detail proyek dan cara IRIS memenuhinya

| Bagian PDF | Syarat | IRIS |
|---|---|---|
| A. Tema / use case | Masalah, target user, input/proses/output/komunikasi/visualisasi, judul | Kepatuhan APD di area kerja berisiko; lihat bagian 4 |
| B. Device & hardware discovery | ESP32 controller utama; ≥1 input; ≥1 output; identifikasi GPIO; daftar komponen + alasan; dapat disimulasikan di Wokwi | Bagian 5 dan `docs/design.md` |
| C. Arsitektur & wiring | Block diagram Input → ESP32/Logic → Output, ditambah Communication → MQTT/Broker → Application/Dashboard; wiring di Wokwi; jelaskan power, GPIO, ground, koneksi antarperangkat | `docs/design.md`, `firmware/diagram.json` |
| D. Programming & logic | Program ESP32 (Arduino IDE/PlatformIO); baca input → hasilkan output; logic sesuai use case; Serial Monitor untuk debugging; testing & debugging | `firmware/` |
| E. Communication | Serial untuk memahami aliran data; MQTT via **HiveMQ Cloud**; topic & payload konsisten | Bagian 7 |
| F. Visualization | Python + paho-mqtt; Colab/IDE Python; **Plotly atau Matplotlib**; minimal tampilkan data/status/trend | `dashboard/` |
| G. Testing | ≥3 skenario; kondisi normal dan abnormal; catat Input, Expected, Actual, Status; bukti screenshot/video | `docs/testing-log.md` |

### 3.4 Minimum requirement (semua wajib)
- ESP32 sebagai controller utama
- Minimal 1 input device/sensor
- Minimal 1 output device/aktuator/indikator
- Wokwi sebagai media simulasi
- Program yang menunjukkan fungsi utama
- Serial Monitor sebagai media debugging/data output
- Dokumentasi wiring dan logic

Fitur rekomendasi yang **diambil semua** oleh IRIS: MQTT + HiveMQ Cloud, Python + paho-mqtt, dashboard Plotly, serta OLED/servo/buzzer.

### 3.5 Dokumentasi akhir (deliverable)
1. Laporan **.docx** (tanpa slide/presentasi)
2. Link proyek Wokwi
3. Source code/sketch
4. Video demo **.mp4**
5. Screenshot hasil pengujian

### 3.6 Isi laporan .docx (urutan mengikuti PDF)
1. Cover: judul, tim, anggota, universitas
2. Latar belakang masalah
3. Problem statement dan tujuan
4. Target user/use case
5. System architecture/block diagram
6. Daftar komponen dan alasan pemilihan
7. Wokwi circuit/wiring diagram
8. Pin/GPIO yang digunakan
9. Penjelasan logika program
10. Serial/MQTT communication
11. Dashboard/visualization
12. Test scenario dan hasil pengujian
13. Screenshot/output
14. Pembagian peran anggota
15. Kesimpulan
16. Pengembangan lanjutan (opsional, tetapi IRIS mengisinya)

### 3.7 Rubrik penilaian

| Kategori | Rincian | Bobot |
|---|---|---|
| Project Structure | Ide & relevansi 5%, Problem statement & tujuan 5% | 10% |
| Device & Hardware Discovery | Pemilihan komponen 5%, Fungsi/GPIO 5%, Wiring & architecture 10% | 20% |
| Programming & Functionality | Logic/program 15%, Input-output 10%, Debugging/stability 5% | 30% |
| Communication & Visualization | Serial 5%, MQTT/HiveMQ 5%, Dashboard/visualization 5% | 15% |
| Documentation, Testing & Teamwork | Laporan 5%, Testing 5%, Kontribusi 5%, **Video demo 10%** | 25% |

### 3.8 Catatan penting dari PDF
- Pemilihan komponen harus punya **alasan teknis yang jelas**.
- **Wokwi adalah media simulasi utama.**
- MQTT, HiveMQ, dan dashboard dipakai sesuai kebutuhan proyek.
- Kreativitas boleh selama proyek **realistis, dapat diuji, dan dapat didemonstrasikan**.

---

## 4. Konsep sistem

### 4.1 Masalah
Pengawasan kepatuhan APD di area kerja berisiko (konstruksi, pabrik, tambang) umumnya dilakukan manual, sehingga tidak konsisten dan tidak terdokumentasi. Data kecelakaan kerja untuk latar belakang **wajib diambil dari sumber resmi** (mis. Kemnaker, BPJS Ketenagakerjaan) dan dikutip. Jangan mengarang angka.

### 4.2 Target user
- Petugas K3/HSE dan supervisor lapangan (pengguna dashboard dan penerima alarm)
- Pekerja (pengguna langsung gerbang)

### 4.3 Dua mode wajib (MVP)
1. **Gerbang (preventif):** kamera di titik masuk → deteksi APD → ESP32 memutuskan → servo palang buka/tutup, LED, buzzer, OLED.
2. **Monitoring ala CCTV (detektif):** kamera di zona kerja → pantau terus → **eskalasi berdasarkan durasi pelanggaran**:
   - pelanggaran singkat: diabaikan (hindari false alarm)
   - berlanjut: peringatan (LED kuning, OLED)
   - lebih lama: alarm (buzzer, LED merah) dan event ke dashboard
   - patuh kembali: reset otomatis

   Nilai ambang durasi ditentukan saat pengujian, simpan sebagai konstanta konfigurasi.

Kedua mode memakai pipeline yang sama; bedanya hanya di logic.

### 4.4 Batas scope

| Tingkat | Isi |
|---|---|
| Wajib | APD **helm + rompi**, satu aturan (keduanya wajib), mode gerbang, mode monitoring dengan eskalasi, fail-safe, dashboard dasar, ≥3 skenario tes |
| Tambahan jika sempat | Profil aturan APD per zona, satu jenis APD ekstra (mis. kacamata) |
| Pengembangan lanjutan (cukup ditulis di laporan) | Banyak jenis APD, aturan adaptif berdasarkan sensor lingkungan, RFID identitas pekerja, multi-server untuk puluhan kamera |

Jangan menambah fitur di luar tingkat "Wajib" sebelum seluruh tingkat itu berjalan dan teruji.

### 4.5 Arsitektur

```
Kamera gerbang ─┐
Kamera zona ────┼─► Server vision terpusat (laptop, GPU RTX 4050)
                │     YOLO + tracking + aturan kepatuhan
                │              │
                │              ▼  publish
                │        HiveMQ Cloud (MQTT broker)
                │       │            │             │
                ▼       ▼            ▼             ▼
            ESP32 gerbang      ESP32 zona     Dashboard Python
         (servo, LED, buzzer,  (LED, buzzer,   (paho-mqtt + Plotly)
          OLED, tombol)         OLED)
```

- Hasil deteksi YOLO diperlakukan sebagai **sensor virtual** yang masuk ke ESP32 lewat MQTT. Tombol fisik di ESP32 adalah input fisik (override/reset supervisor dan mode uji).
- Wokwi tidak menjalankan YOLO atau feed kamera sungguhan, jadi server vision berjalan di luar Wokwi. Jelaskan ini apa adanya di laporan.
- **Tidak memakai Raspberry Pi per kamera.** Komputasi dipusatkan di server, ESP32 per titik hanya untuk aktuasi (murah, mudah diperbanyak).
- Untuk simulasi Wokwi, satu ESP32 boleh berperan sebagai controller untuk gerbang dan zona sekaligus. Di laporan, jelaskan bahwa implementasi nyata memakai satu node per titik.

---

## 5. Keputusan teknis

- **Deteksi per orang:** deteksi `person` dan item APD, lalu kaitkan APD ke orang berdasarkan posisi kotak (helm di area kepala, rompi di area badan). Jangan mengandalkan kelas "no-helmet".
- **Aturan gerbang:**
  - definisikan region of interest (ROI) area masuk, termasuk zona antre di belakangnya
  - palang terbuka hanya jika **semua** orang di ROI patuh
  - evaluasi tetap berjalan selama palang terbuka; pelanggar muncul → palang menutup + alarm
  - jendela terbuka dibatasi waktu
- **Monitoring:** tracking ID untuk timer per orang. Jika tracking bermasalah, fallback ke durasi di level frame dan catat sebagai keterbatasan.
- **Fail-safe:** server vision mengirim heartbeat. Kalau heartbeat atau pesan berhenti melewati batas waktu, ESP32 masuk mode aman (gerbang terkunci, indikator gangguan aktif).
- **Mode uji standalone:** tombol/switch di Wokwi mensimulasikan hasil deteksi, sehingga seluruh logic ESP32 bisa diuji tanpa YOLO.
- **Serial Monitor:** firmware mencetak log terstruktur (koneksi WiFi/MQTT, payload diterima, transisi state, aksi aktuator). Ini bukti untuk rubrik Serial dan Debugging.
- **Privasi:** tanpa face recognition, tanpa menyimpan video. Hanya event dan angka yang dikirim.
- **Keterbatasan yang diakui di laporan:** tailgating tidak 100% tertutup; akurasi bergantung pada cahaya, sudut, oklusi, dan kerumunan; kapasitas satu GPU terbatas; server terpusat adalah titik tunggal kegagalan. Sistem diposisikan sebagai alat bantu pengawasan, bukan pengganti prosedur K3.

### 5.1 Model
- **Ultralytics YOLO26**, generasi terbaru yang tersedia (YOLO27 belum dirilis). Mode tracking didukung untuk model deteksi. Fine-tune dari bobot pretrained COCO.
- **Kandidat utama `yolo26m`**, pembanding `yolo26s`. Pilih final berdasarkan mAP di validation set **dan** FPS inferensi live di laptop (ukur, jangan diasumsikan). Demo butuh inferensi + tracking + MQTT berjalan lancar bersamaan.
- `yolo26l`/`yolo26x` hanya dicoba kalau semua irisan wajib sudah selesai.
- Hardware: laptop tim dengan RTX 4050. Cek VRAM dengan `nvidia-smi`, pakai `batch=-1` (autobatch). Google Colab sebagai cadangan.

### 5.2 Dataset
- **Utama: SH17** (8.099 gambar, 17 kelas termasuk Person, Head, Helmet, Safety-vest; label format YOLO; tersedia di Kaggle).
  - Pakai subset kelas: `person`, `head`, `helmet`, `safety-vest` (tambah `glasses` hanya jika APD ekstra diambil). Remap ID kelas ke skema IRIS.
  - Gunakan split resmi SH17 (`train_files.txt`, `val_files.txt`).
  - Gambar beresolusi tinggi: pertimbangkan resize offline agar loading tidak jadi bottleneck.
  - **Lisensi CC BY-NC-SA 4.0** (non-komersial, share-alike). Cantumkan atribusi dan sitasi di README dan laporan. Jika IRIS kelak dikomersialkan, dataset harus diganti.
- **Pendamping (opsional): Ultralytics Construction-PPE** (1.416 gambar, 11 kelas, AGPL-3.0, unduh otomatis). Skemanya berbeda (punya kelas negatif seperti `no_helmet`, tidak ada `no_vest`), jadi tidak digabung di run pertama.
- **Data rekaman tim** (helm proyek dan rompi tersedia): rekam di lokasi demo, dipakai sebagai **test set lokal** untuk evaluasi kondisi nyata dan bahan video demo. Dilabel untuk training hanya jika waktu cukup.
- **Fallback:** bobot pretrained yang dirilis penulis SH17, jika training gagal atau terlambat. Cek format kelas dan lisensinya.

### 5.3 Prosedur training
1. Jalankan 1 epoch singkat untuk mengukur waktu per epoch dan pemakaian VRAM.
2. Tentukan budget training (gunakan argumen batas waktu dan `patience` dari Ultralytics; cek dokumentasi) supaya **training selesai paling lambat Jumat pagi**.
3. Training berjalan di background sementara irisan 0–2 dikerjakan. Sampai model siap, pipeline vision dikembangkan memakai bobot COCO (`person`) atau mode uji.
4. Simpan metrik (mAP50, mAP50-95 per kelas, confusion matrix, FPS) ke `docs/assets/` untuk laporan.

---

## 6. Komponen awal (stage 2, Wokwi)

| Komponen | Fungsi | Alasan |
|---|---|---|
| ESP32 DevKit | Controller utama, logic, WiFi/MQTT | Wajib dari tugas; WiFi bawaan |
| Servo (mis. SG90) | Palang gerbang | Aktuasi yang jelas dan terlihat di demo |
| LED merah, kuning, hijau + resistor | Status patuh / peringatan / pelanggaran | Indikator visual murah |
| Buzzer | Alarm | Peringatan audio |
| OLED SSD1306 (I2C) | Menampilkan status dan APD yang kurang | Informasi spesifik bagi pekerja |
| Push button (≥1) | Override/reset supervisor, input fisik | Memenuhi input fisik, mendukung mode uji |
| Kamera (di luar Wokwi) | Sumber citra untuk server vision | Komponen utama deteksi APD |

Pemetaan GPIO ditentukan di `docs/design.md`. Pilih pin yang aman untuk ESP32 (hindari strapping pin dan pin input-only untuk output). **Cek ketersediaan setiap komponen di Wokwi** sebelum dipakai.

---

## 7. Topic dan payload MQTT (draft, final di irisan 2)

| Topic | Arah | Contoh payload |
|---|---|---|
| `iris/<node>/detection` | server → ESP32, dashboard | `{"ts":..., "person_count":2, "persons":[{"id":1,"helmet":true,"vest":true},{"id":2,"helmet":false,"vest":true}], "violators":[2]}` |
| `iris/<node>/status` | ESP32 → dashboard | `{"ts":..., "mode":"gate", "state":"DENIED", "gate":"closed", "missing":["helmet"]}` |
| `iris/<node>/event` | ESP32 → dashboard | `{"ts":..., "type":"alarm", "level":2, "person_id":2, "duration_s":12}` |
| `iris/<node>/override` | dashboard/supervisor → ESP32 | `{"cmd":"reset"}` |
| `iris/server/heartbeat` | server → ESP32 | `{"ts":...}` |

`<node>` contoh: `gate1`, `zoneA`. Semua payload JSON, field konsisten, timestamp selalu ada.

---

## 8. Struktur repo (usulan)

```
iris-ppe/
├── CLAUDE.md
├── README.md                # ringkasan proyek, tim, cara menjalankan, link Wokwi
├── .gitignore
├── .env.example             # nama variabel tanpa nilai rahasia
├── docs/
│   ├── study-case-guideline-stage-2.pdf
│   ├── design.md            # komponen, GPIO, block diagram, state machine
│   ├── testing-log.md       # tabel pengujian
│   ├── contributions.md     # siapa mengerjakan apa (untuk laporan)
│   └── assets/              # diagram, screenshot pengujian
├── firmware/                # PlatformIO: platformio.ini, src/, diagram.json, wokwi.toml
├── vision/                  # inferensi YOLO, tracking, aturan kepatuhan, publisher MQTT
├── training/                # konfigurasi & notebook training/evaluasi (tanpa dataset)
└── dashboard/               # paho-mqtt + Plotly
```

---

## 9. Wokwi

- Simulasi lokal memakai `wokwi-cli` dengan token dari dashboard Wokwi CI di environment variable `WOKWI_CLI_TOKEN`. `wokwi-cli` punya mode MCP (eksperimental) untuk integrasi agent. Cek dokumentasi resmi untuk detail dan kuota sebelum mengandalkannya.
- `firmware/wokwi.toml` menunjuk ke firmware hasil build PlatformIO (`.bin`/`.elf`).
- Manfaatkan `--serial-log-file`, `--screenshot-*`, dan scenario file untuk pengujian otomatis dan bukti laporan.
- ESP32 di Wokwi terhubung internet lewat WiFi virtual `Wokwi-GUEST` (tanpa password). **Uji koneksi TLS ke HiveMQ Cloud (port 8883) sedini mungkin.**
- **Link proyek Wokwi untuk pengumpulan harus berupa proyek di wokwi.com.** Jaga agar sketch bisa dikompilasi di sana: siapkan versi `sketch.ino`, `diagram.json`, dan `libraries.txt`, lalu uji di wokwi.com sebelum pengumpulan. Kredensial di proyek publik wokwi.com harus berupa kredensial khusus demo yang bisa dicabut.
- Rangkaian buatan agent **wajib diverifikasi visual** di Wokwi sebelum dianggap benar.

---

## 10. Git dan GitHub

- **Commit setiap unit kerja yang sudah berjalan dan teruji, lalu langsung push ke GitHub.** Jangan menumpuk banyak perubahan dalam satu commit.
- Format commit: Conventional Commits berbahasa Inggris, mis. `feat(firmware): add gate state machine`, `fix(vision): correct helmet-to-person matching`, `docs: update testing log`.
- `main` harus selalu dalam kondisi berjalan. Pekerjaan besar atau eksperimen di branch `feat/<topik>`, di-merge setelah teruji.
- Dilarang: force push ke `main`, menulis ulang history yang sudah di-push, commit file rahasia.
- **Jangan commit:** `.env`, token/kredensial, dataset, bobot model besar (`*.pt`, `*.onnx`), video mentah, folder build (`.pio/`, `runs/`, `__pycache__/`). Bobot model final dibagikan lewat GitHub Releases atau tautan Drive yang dicatat di README.
- **Kontribusi (rubrik 5%):** commit dibuat oleh anggota yang benar-benar mengerjakan. Agent tidak memalsukan author atau co-author. Catat pembagian kerja yang sebenarnya di `docs/contributions.md`.
- Tag `stage2-submission` pada commit yang dikumpulkan.

---

## 11. Hal yang masih terbuka

- Ukuran model final (`yolo26m` vs `yolo26s`), diputuskan dari hasil training dan FPS
- Nilai ambang eskalasi dan timeout fail-safe
- Pemetaan GPIO final

---

## 12. Urutan kerja

Kerjakan dalam irisan tipis. Setiap irisan: kerjakan → uji → catat di `docs/testing-log.md` → commit → push.

0. **Setup & uji kelayakan:** struktur repo, `.gitignore`, `.env.example`, README awal. Jalankan sketch ESP32 + LED + tombol lewat `wokwi-cli` dan pastikan log serial terbaca.
1. **Rancangan dasar:** komponen + alasan, GPIO, block diagram, state machine, format MQTT di `docs/design.md`.
2. **Irisan 1 – Gerbang tanpa YOLO:** ESP32 di Wokwi, tombol sebagai hasil deteksi, servo, LED, buzzer, OLED, log Serial.
3. **Irisan 2 – MQTT:** koneksi ESP32 ↔ HiveMQ Cloud, topic/payload final, uji dengan publisher Python sederhana.
4. **Irisan 3 – Vision:** inferensi YOLO + aturan kepatuhan, publish ke MQTT.
5. **Irisan 4 – Dashboard:** paho-mqtt + Plotly (status terkini, pelanggaran per waktu, compliance rate).
6. **Irisan 5 – Monitoring:** tracking, eskalasi durasi, fail-safe heartbeat.
7. **Finalisasi:** proyek wokwi.com, laporan .docx (Bahasa Indonesia), video demo .mp4, screenshot, tag `stage2-submission`.

Training model berjalan paralel sejak langkah 0 (lihat 5.3).

### 12.1 Jadwal (deadline Jumat 30 Okt 2026, 24:00 WITA)

| Waktu (WITA) | Target |
|---|---|
| Kamis pagi | Langkah 0: setup repo, uji Wokwi CLI. Unduh SH17, ukur 1 epoch, **mulai training di background** |
| Kamis siang–malam | Langkah 1–3: rancangan dasar, irisan 1 (gerbang tanpa YOLO), irisan 2 (MQTT). Pipeline vision dirintis dengan bobot COCO. Logo dan diagram mulai dibuat |
| Jumat pagi | Model final dipilih. Irisan 3 (vision) dan irisan 4 (dashboard) |
| Jumat siang | Irisan 5 (monitoring, fail-safe). Pengujian T1–T6. Proyek wokwi.com dipublikasikan |
| **Jumat 16:00** | **Code freeze.** Rekam video demo, ambil screenshot |
| Jumat malam | Laporan .docx final, README, tag `stage2-submission`, **kumpulkan paling lambat 22:00** |

### 12.2 Urutan pemangkasan bila tertinggal
Pangkas dari atas ke bawah, jangan sebaliknya:
1. Eksperimen `yolo26l`/`yolo26x`
2. Penggabungan dataset Construction-PPE dan pelabelan data tim
3. Timer per orang → fallback durasi per frame
4. Skenario T5 dan T6

**Tidak boleh dipangkas:** gerbang end-to-end (vision → MQTT → ESP32 → aktuator), Serial log, MQTT/HiveMQ, dashboard dasar, minimal 3 skenario tes terdokumentasi, link Wokwi, video demo, laporan .docx.

---

## 13. Skenario pengujian minimum

| ID | Kondisi | Hasil yang diharapkan |
|---|---|---|
| T1 | Satu orang, APD lengkap, di gerbang | Palang terbuka, LED hijau, status `GRANTED` terkirim |
| T2 | Satu orang, rompi tidak dipakai | Palang tertutup, buzzer, OLED menampilkan item yang kurang |
| T3 | Server vision mati / heartbeat berhenti | Fail-safe: gerbang terkunci, indikator gangguan |
| T4 | Dua orang, satu tidak patuh | Palang tetap tertutup |
| T5 | Pelanggar masuk ROI saat palang terbuka | Palang menutup, alarm |
| T6 | Zona kerja: pekerja melepas helm makin lama | Abaikan → peringatan → alarm + event dashboard, lalu reset saat patuh |

Catat untuk setiap tes: Test Case, Input/Condition, Expected Result, Actual Result, Status, bukti (screenshot/log/video).

---

## 14. Aturan kerja agent

- Jelaskan keputusan desain secara singkat. Tim harus bisa menjelaskan seluruh kode saat presentasi, jadi hindari solusi yang tidak perlu rumit.
- Rahasia hanya di `.env` (masuk `.gitignore`). Akun Wokwi dan HiveMQ dibuat oleh tim sendiri. Jangan menulis rahasia di kode, commit, log, atau chat.
- Jangan mengklaim angka (FPS, akurasi, jumlah kamera, statistik kecelakaan) yang belum diukur atau tidak bersumber.
- Jangan menambah komponen atau fitur tanpa alasan teknis dan tanpa cek ketersediaan di Wokwi.
- Tanyakan ke tim sebelum mengubah keputusan di bagian 4–7.

---

## 15. Status

- [ ] 0. Setup & uji kelayakan Wokwi CLI
- [ ] 1. Rancangan dasar
- [ ] 2. Irisan 1 – Gerbang tanpa YOLO
- [ ] 3. Irisan 2 – MQTT
- [ ] 4. Irisan 3 – Vision
- [ ] 5. Irisan 4 – Dashboard
- [ ] 6. Irisan 5 – Monitoring
- [ ] 7. Finalisasi & pengumpulan
