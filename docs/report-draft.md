# DRAF ISI LAPORAN — IRIS (untuk diubah ke .docx)

> Draf ini disusun agent dari pekerjaan yang sudah teruji di repo. Urutan bab mengikuti
> `docs/study-case-guideline-stage-2.pdf`. Bagian bertanda **[TODO]** menunggu hasil akhir (metrik model final,
> screenshot, link) atau penulisan oleh penanggung jawab bagiannya. Semua angka sudah diukur atau bersumber;
> jangan menambah angka yang belum diukur.

---

## Cover

**IRIS: Smart PPE Compliance Gate and Monitoring System Using Computer Vision**

Tugas Akhir *Selection Phase 2 – IoT: Device and Hardware Discovery*, Samsung Innovation Campus Batch 8

Tim **Montblanc** — Universitas Mulawarman

- Muhammad Naufal Fahrozi (Ketua · Project Lead & System Integrator)
- Christian Mahatma Bima Alpindo (Hardware & Embedded Engineer)
- Tua Delima Sitompul (AI & Backend Engineer)
- Kalingga Dwindra Putraka (Product & Visual Designer)

[TODO Kalingga: logo IRIS dan tata letak cover]

---

## 1. Latar Belakang Masalah

Kecelakaan kerja masih menjadi persoalan besar di Indonesia. Data Satu Data Ketenagakerjaan Kementerian
Ketenagakerjaan mencatat **462.241 klaim kecelakaan kerja** pada program Jaminan Kecelakaan Kerja BPJS
Ketenagakerjaan sepanjang 2024 dan **319.382 klaim** sepanjang 2025, atau rata-rata lebih dari 870 klaim per hari
pada 2025 (Kementerian Ketenagakerjaan, t.t.). Angka ini hanya mencakup klaim yang disetujui dan dibayarkan, sehingga kejadian
sebenarnya kemungkinan lebih besar.

Penggunaan Alat Pelindung Diri (APD) / *Personal Protective Equipment* (PPE) seperti helm pengaman dan rompi
reflektif merupakan kewajiban di tempat kerja berisiko. Permenakertrans No. PER.08/MEN/VII/2010 tentang Alat Pelindung
Diri mewajibkan pengusaha menyediakan APD dan pekerja memakainya sesuai potensi bahaya. [TODO: verifikasi bunyi
pasal dari JDIH Kemnaker sebelum dikutip langsung — lihat `docs/report-sources.md`]

Di lapangan, pengawasan kepatuhan APD umumnya dilakukan manual oleh petugas K3/HSE. Cara ini sulit dilakukan terus
menerus, tidak konsisten antar petugas, dan tidak terdokumentasi sehingga pelanggaran berulang sulit dianalisis.

## 2. Problem Statement dan Tujuan

**Problem statement:** Bagaimana memastikan setiap pekerja memakai helm dan rompi saat memasuki dan selama berada di
area kerja berisiko, secara otomatis, konsisten, dan terdokumentasi, tanpa bergantung sepenuhnya pada pengawasan
manual?

**Tujuan:**
1. Membangun gerbang masuk yang hanya membuka palang jika **semua** orang di area masuk memakai helm dan rompi.
2. Membangun monitoring zona kerja ala CCTV yang mengeskalasi pelanggaran berdasarkan durasi (diabaikan →
   peringatan → alarm) dan reset otomatis saat pekerja patuh kembali.
3. Mengirim status dan kejadian lewat MQTT ke dashboard agar petugas K3 bisa memantau compliance rate dan riwayat
   pelanggaran.
4. Menjamin keamanan saat sistem gagal (*fail-safe*): jika server vision mati, gerbang terkunci.

## 3. Target User / Use Case

| Pengguna | Kebutuhan | Cara IRIS membantu |
|---|---|---|
| Petugas K3/HSE, supervisor lapangan | Memantau kepatuhan APD, menerima alarm, punya data riwayat | Dashboard (status node, compliance rate, grafik pelanggaran, tabel event), tombol reset alarm |
| Pekerja | Tahu apakah APD-nya sudah lengkap sebelum masuk | Palang, LED, buzzer, dan OLED yang menampilkan APD yang kurang ("Kurang: ROMPI") |

Use case: (a) titik masuk proyek konstruksi/pabrik (mode gerbang), (b) area kerja di dalam proyek (mode zona).

## 4. System Architecture / Block Diagram

[TODO Kalingga: gambar ulang diagram berikut secara visual; versi teks/Mermaid ada di `docs/design.md` bagian 1]

```
INPUT / SENSOR                PROCESSING / LOGIC          OUTPUT / ACTUATOR
Kamera  ─► Server vision (YOLO26 + tracking + aturan) ─┐
                                                      │ MQTT (TLS 8883)
Push button, slide switch ─────────────► ESP32 (state machine gerbang/zona) ─► Servo, LED, buzzer, OLED, Serial
                                                      │
                             broker.hivemq.com ◄──────┘──► Dashboard Python (paho-mqtt + Plotly Dash)
```

- **Input/Sensing:** kamera (diolah server vision menjadi "sensor virtual" hasil deteksi APD), push button (reset
  supervisor + simulasi deteksi pada mode uji), slide switch (peran gerbang/zona, sumber LIVE/TEST).
- **Processing/Logic:** server vision (YOLO26 + ByteTrack + aturan kepatuhan) dan ESP32 (state machine).
- **Output/Actuation:** servo palang, LED hijau/kuning/merah, buzzer, OLED, Serial Monitor.
- **Communication:** MQTT lewat HiveMQ public broker dengan TLS; Serial untuk debugging.
- **Visualization:** dashboard Plotly Dash.

Alasan arsitektur: komputasi berat (YOLO) dipusatkan di satu server GPU, sedangkan setiap titik cukup memakai ESP32
murah untuk aktuasi. Wokwi tidak bisa menjalankan kamera/YOLO, sehingga server vision berjalan di luar Wokwi dan
mengirim hasilnya lewat MQTT; pada mode uji, hasil deteksi disimulasikan dengan tombol.

## 5. Daftar Komponen dan Alasan Pemilihan

[TODO Christian: tinjau dan lengkapi] — sumber: `docs/design.md` bagian 2.

| Komponen | Jml | Fungsi | Alasan teknis |
|---|---|---|---|
| ESP32 DevKit C v4 | 1 | Controller, logic, WiFi/MQTT | Wajib; WiFi bawaan; GPIO cukup |
| Servo SG90 | 1 | Palang gerbang (0° tutup, 90° buka) | Aktuasi mekanis yang terlihat jelas; PWM 50 Hz |
| LED hijau/kuning/merah + resistor 220 Ω | 3+3 | Patuh / peringatan & gangguan / pelanggaran | Murah, terbaca dari jauh; arus ±6 mA |
| Buzzer piezo | 1 | Alarm audio | Terdengar walau pekerja tidak melihat lampu |
| OLED SSD1306 128×64 I2C | 1 | Status dan APD yang kurang | Informasi spesifik untuk pekerja; I2C hanya 2 pin |
| Push button | 4 | RESET supervisor; PERSON/HELMET/VEST untuk mode uji | Input fisik; bisa diotomatisasi oleh scenario wokwi-cli |
| Slide switch | 2 | ROLE (GATE/ZONE), SOURCE (LIVE/TEST) | Satu rangkaian dapat mendemokan dua mode |
| Kamera (di luar Wokwi) | 1/titik | Sumber citra server vision | Komponen utama deteksi APD |

## 6. Wokwi Circuit / Wiring Diagram

Link proyek Wokwi: https://wokwi.com/projects/479194485722835969

Proyek wokwi.com berisi sketch yang sama dengan firmware PlatformIO di repo (`sketch.ino`, `config.h`, `ca_cert.h`,
`diagram.json`, `libraries.txt`). Saat dijalankan di browser, ESP32 tersambung ke WiFi `Wokwi-GUEST` lalu ke broker
HiveMQ lewat TLS, sehingga dapat menerima hasil deteksi dari server vision di laptop secara langsung.

Gambar: `docs/assets/irisan1/wokwi-circuit.png`.

Penjelasan: input diletakkan di sisi kiri ESP32 dan output di sisi kanan, dengan urutan komponen mengikuti urutan pin
sehingga kabel tidak saling menyilang. Semua komponen berbagi ground ESP32 (bus GND di kiri, trunk bawah ke GND.1;
buzzer ke GND.2; OLED ke GND.3). OLED dicatu dari 3V3, servo dari pin 5V. Tombol dan slide switch hanya disambung ke
GND dan memakai pull-up internal ESP32 (aktif LOW), sehingga tidak perlu resistor eksternal.

## 7. Pin/GPIO yang Digunakan

| GPIO | Arah | Komponen |
|---|---|---|
| 32 | Input pull-up | Slide switch ROLE (kiri = GATE, kanan = ZONE) |
| 33 | Input pull-up | Slide switch SOURCE (kiri = LIVE/MQTT, kanan = TEST/tombol) |
| 25 / 26 / 27 | Input pull-up | Tombol PERSON / HELMET / VEST (mode uji) |
| 14 | Input pull-up | Tombol RESET supervisor |
| 23 | Output PWM | Buzzer |
| 22 / 21 | I2C SDA / SCL | OLED |
| 19 | Output PWM | Servo |
| 18 / 17 / 16 | Output | LED hijau / kuning / merah (via 220 Ω) |

Pin yang dihindari: strapping pin (0, 2, 5, 12, 15), pin flash (6–11), UART (1, 3), dan pin input-only tanpa pull-up
(34–39).

## 8. Penjelasan Logika Program

[TODO Christian (ESP32) + Delima (vision): tinjau]

### 8.1 Firmware ESP32 (state machine)

Setiap loop, ESP32 mengevaluasi "snapshot" deteksi terakhir (jumlah orang, pelanggar, APD yang kurang, umur data).

**Mode gerbang:** `FAULT` (data/heartbeat basi > 8 s → palang terkunci, LED kuning berkedip) · `IDLE` (tidak ada
orang) · `GRANTED` (semua orang patuh → palang terbuka maks 5 s, LED hijau) · `DENIED` (ada pelanggar → palang
tertutup, LED merah, buzzer, OLED menampilkan APD yang kurang). Satu pelanggar cukup untuk menutup palang, termasuk
saat palang sedang terbuka.

**Mode zona:** `NORMAL` (pelanggaran < 3 s diabaikan untuk menghindari alarm palsu) · `WARNING` (≥ 3 s, LED kuning)
· `ALARM` (≥ 8 s, LED merah + buzzer + event ke dashboard) · reset otomatis ke `NORMAL` saat patuh kembali.

Tombol RESET (atau perintah `override` dari dashboard) membungkam buzzer tanpa membuka palang.

### 8.2 Server vision

1. **Model:** Ultralytics YOLO26m, fine-tune dari bobot COCO pada 4 kelas: person, head, helmet, safety-vest.
   Data training gabungan 5 dataset publik (17.313 gambar; lihat bab 11 dan `docs/report-sources.md`).
   Hasil evaluasi model final (`docs/assets/model/metrics.md`, imgsz 640):

   | Kelas | AP50 val SH17 | AP50 test publik* | Precision / Recall test publik |
   |---|---|---|---|
   | person | 0,918 | 0,895 | 0,79 / 0,86 |
   | head | 0,922 | 0,712 | 0,92 / 0,52 |
   | helmet | 0,643 | 0,850 | 0,84 / 0,77 |
   | safety-vest | 0,510 | 0,927 | 0,85 / 0,89 |
   | **mAP50 / mAP50-95** | **0,748 / 0,555** | **0,846 / 0,588** | |

   \*Test publik = split test Construction Site Safety, Safety Helmet & Reflective Jacket, dan HardHat-Vest
   (1.682 gambar, tidak dipakai training). Label person/head di sebagian test berasal dari pseudo-label, sehingga
   angka helm dan rompi yang paling bisa dipegang. Val SH17 lebih sulit (gambar resolusi tinggi, objek kecil, banyak
   variasi). Kecepatan inferensi + tracking di RTX 4050 laptop: 77–80 FPS pada imgsz 640 dan 27–28 FPS pada 1280
   (diukur pada 300 frame video 1080p); pipeline lengkap dengan MQTT 78–85 FPS pada 640.
   Ambang keyakinan: person 0,4, rompi 0,4 (F1-optimal), helm 0,3 (lebih rendah dari F1-optimal 0,38–0,41 agar helm
   gelap tetap terdeteksi; diuji pada video patuh dan tanpa rompi).
   **Model:** YOLO26m dipertahankan (YOLO26s tidak perlu dilatih karena FPS 26m sudah jauh di atas kebutuhan real-time).
2. **Tracking:** ByteTrack memberi ID per orang antar frame.
3. **Aturan kepatuhan:** helm dihitung jika tepi atasnya berada di puncak kotak orang (20% teratas), sehingga helm yang
   dipegang di tangan atau di depan dada tidak dihitung; rompi jika pusatnya di area badan (15–75%); satu item APD hanya
   diberikan ke orang terdekat. Tidak memakai kelas "no-helmet". (Versi awal memakai pusat helm di 0–35% tinggi, tetapi
   gagal pada close-up karena kotak helm sebagian dataset membungkus seluruh kepala; uji V10.)
4. **Stabilisasi:** status APD tiap orang = mayoritas deteksi dalam 1 detik terakhir (mencegah palang buka-tutup
   akibat deteksi berkedip); timer pelanggaran per orang tetap berlanjut walau ID tracking berganti; orang baru dihitung
   setelah terlihat ≥ 1 detik agar deteksi palsu sesaat (mis. benda di tepi frame) tidak menutup palang (uji V11).
5. **ROI gerbang:** hanya orang yang titik kakinya di dalam poligon area masuk yang dihitung.
6. **Publikasi:** `detection` (maks 5 Hz) dan `heartbeat` (1 Hz, berisi FPS) ke MQTT. Tidak ada video yang disimpan.

## 9. Serial / MQTT Communication

**Serial Monitor** mencetak log terstruktur, misalnya:

```
[BOOT] IRIS node=gate1 role=GATE source=LIVE
[NET] wifi connected ip=10.13.37.2
[MQTT] connecting broker.hivemq.com:8883 (TLS) id=iris-gate1-c40a24
[MQTT] connected, subscribed sic8-montblanc/iris/{gate1,server}/...
[MQTT] rx detection persons=1 violators=1 missing=vest
[STATE] IDLE -> DENIED missing=vest persons=1
[ACT] servo=0 gate=closed
[EVENT] node=gate1 type=denied missing=vest persons=1 duration_s=0.0
```

**MQTT:** broker `broker.hivemq.com` port 8883 (TLS). ESP32 memverifikasi sertifikat server dengan Amazon Root CA 1.
Topic (prefix `sic8-montblanc/iris`): `<node>/detection` (server → ESP32), `<node>/status` (ESP32 → dashboard,
retained), `<node>/event`, `<node>/override` (dashboard → ESP32), `server/heartbeat`. Semua payload JSON dengan
timestamp. Rincian: `docs/design.md` bagian 5.

Catatan broker: paket gratis HiveMQ Cloud Serverless sudah tidak tersedia untuk pengguna baru (dipensiunkan
31 Desember 2026) dan paket Starter hanya trial 15 hari dengan kartu kredit, sehingga dipakai HiveMQ public broker
dengan TLS. Konsekuensinya broker tidak memakai autentikasi; dicatat sebagai keterbatasan, dan konfigurasi dibuat agar
bisa pindah ke broker ber-autentikasi tanpa mengubah logika.

## 10. Dashboard / Visualization

Dashboard Python (paho-mqtt + Plotly Dash), refresh tiap 1 detik: indikator koneksi broker dan status server vision,
stat tile (compliance rate sesi, jumlah pelanggaran, izin masuk, FPS vision), kartu status tiap node dengan tombol
Reset alarm, grafik compliance rate per 30 detik, grafik pelanggaran per waktu (helm vs rompi), dan tabel event
terbaru. Event juga dicatat ke CSV. Gambar: `docs/assets/irisan4/`.

## 11. Test Scenario dan Hasil Pengujian

Ringkasan dari `docs/testing-log.md` (rincian dan bukti lengkap ada di sana).

| ID | Kondisi | Expected | Actual | Status |
|---|---|---|---|---|
| T1 | 1 orang APD lengkap di gerbang | Palang terbuka, LED hijau, `GRANTED` | Sesuai (simulator: latency 0,78–1,0 s; video: GRANTED stabil) | Lulus |
| T2 | 1 orang tanpa rompi | Palang tertutup, buzzer, OLED "Kurang: ROMPI" | Sesuai (simulator & video Pexels 8965561) | Lulus |
| T3 | Server vision mati | Gerbang terkunci, indikator gangguan | `FAULT`, palang tertutup | Lulus |
| T4 | 2 orang, 1 tidak patuh | Palang tetap tertutup | `DENIED`, persons=2 | Lulus |
| T5 | Pelanggar masuk saat palang terbuka | Palang menutup + alarm | `GRANTED -> DENIED`, servo 0° | Lulus |
| T6 | Zona: helm/rompi dilepas makin lama | Abaikan → WARNING → ALARM + event → reset | WARNING 3,0 s, ALARM 8,1 s, `cleared` (simulator & video) | Lulus |

Uji langsung dengan webcam USB, helm, dan rompi asli saat rekaman video demo: T1–T6 lulus (rincian di `docs/testing-log.md`).

Temuan penting selama pengujian dan perbaikannya:
1. Tombol uji tidak terbaca karena loop terlalu lama menggambar OLED → OLED hanya digambar ulang jika isinya berubah.
2. Handshake TLS menahan loop beberapa detik, dan di simulator browser wokwi.com batas 8 s selalu gagal (rc=-2) →
   batas handshake 30 s, dan gerbang dikunci (`FAULT`) selama menyambung ulang sehingga palang tidak pernah tertahan
   terbuka. Diverifikasi end-to-end di proyek wokwi.com (`docs/assets/irisan2/wokwi-web-e2e.log`).
3. Palang buka-tutup 6 kali untuk satu pekerja karena deteksi helm berkedip → voting berbasis waktu 1 detik.
4. Timer pelanggaran reset saat ID tracking berganti → state diwariskan ke ID baru di posisi yang sama.
5. FAULT palsu akibat jeda broker publik > 5 s → batas fail-safe 8 s.
6. Deteksi rompi lemah pada model awal (AP50 0,33) karena data rompi SH17 hanya 433 contoh → dataset diperluas
   (13.599 contoh rompi). AP50 rompi di val SH17 naik 0,33 → 0,51 dan helm 0,62 → 0,64; di test publik
   AP50 rompi 0,93 dan helm 0,85.

## 12. Screenshot / Output

[TODO Kalingga: susun gambar berikut dengan keterangan]
- Rangkaian Wokwi: `docs/assets/irisan1/wokwi-circuit.png`
- OLED: `docs/assets/irisan1/oled-*.png`
- Dashboard: `docs/assets/irisan4/*.jpg`
- Log Serial & laporan uji MQTT: `docs/assets/irisan2/`, `docs/assets/irisan3/`
- [TODO] Tangkapan layar vision dengan kotak deteksi (dari uji webcam tim)
- Grafik training & evaluasi model final: `docs/assets/model/results.png`, `docs/assets/model/*/confusion_matrix_normalized.png`, `BoxPR_curve.png`

## 13. Pembagian Peran Anggota

| Anggota | Peran | Tanggung jawab utama |
|---|---|---|
| Muhammad Naufal Fahrozi | Project Lead & System Integrator | Perencanaan, arsitektur, integrasi end-to-end, koordinasi uji, laporan final |
| Christian Mahatma Bima Alpindo | Hardware & Embedded Engineer | Komponen, wiring & GPIO Wokwi, firmware ESP32, uji perangkat |
| Tua Delima Sitompul | AI & Backend Engineer | Dataset, training & evaluasi YOLO, pipeline vision, MQTT, data dashboard |
| Kalingga Dwindra Putraka | Product & Visual Designer | Logo, diagram, desain dashboard, cover & tata letak laporan, video demo |

Tim bekerja bersama dalam sesi kerja di satu laptop; tiap anggota adalah penanggung jawab utama bidangnya. Implementasi
kode, training, dan draf dokumen dibantu AI coding agent (Claude Code) di bawah arahan ketua, sedangkan konsep, aturan,
dan keputusan teknis ditentukan tim. Seluruh anggota meninjau, menguji, dan mampu menjelaskan bagiannya. Rincian:
`docs/contributions.md`.

| Anggota | Peran | Kontribusi |
|---|---|---|
| Muhammad Naufal Fahrozi | Project Lead & System Integrator | |
| Christian Mahatma Bima Alpindo | Hardware & Embedded Engineer | |
| Tua Delima Sitompul | AI & Backend Engineer | |
| Kalingga Dwindra Putraka | Product & Visual Designer | |

## 14. Kesimpulan

[TODO Naufal: tulis setelah uji webcam] Kerangka: IRIS berhasil mengintegrasikan computer vision, ESP32, MQTT, dan
dashboard menjadi sistem pengawasan APD dua mode yang teruji pada skenario T1–T6; fail-safe bekerja; keterbatasan
utama (lihat bawah).

**Keterbatasan:** akurasi bergantung pada cahaya, sudut, jarak, dan oklusi (helm gelap tampak belakang dan objek kecil
di kejauhan lebih sulit terdeteksi); tailgating tidak tertutup 100%; satu server GPU adalah titik tunggal kegagalan;
broker publik tanpa autentikasi; data uji kondisi nyata terbatas (tidak ada rekaman lapangan, uji memakai dataset
publik, video stok, dan uji langsung tim). IRIS adalah alat bantu pengawasan, bukan pengganti prosedur K3.

## 15. Pengembangan Lanjutan

- Lebih banyak jenis APD (kacamata, sarung tangan, sepatu) dan profil aturan APD per zona.
- Aturan adaptif berdasarkan sensor lingkungan (mis. kebisingan → wajib pelindung telinga).
- Identitas pekerja dengan RFID untuk rekap kepatuhan per orang (tanpa face recognition).
- Broker ber-autentikasi (HiveMQ Cloud/self-hosted) dan multi-server untuk puluhan kamera.
- Perakitan hardware fisik (stage 3) dan pengumpulan data lapangan sendiri untuk evaluasi dan fine-tuning.

## Daftar Pustaka

- Kementerian Ketenagakerjaan. (t.t.). *Jumlah Klaim Kasus Kecelakaan Kerja, Januari–Desember Tahun 2024*. Satu Data
  Ketenagakerjaan. Diakses 29 Oktober 2026, dari https://satudata.kemnaker.go.id/data/kumpulan-data/2447
- Kementerian Ketenagakerjaan. (t.t.). *Jumlah Klaim Kasus Kecelakaan Kerja Tahun 2025*. Satu Data Ketenagakerjaan.
  Diakses 29 Oktober 2026, dari https://satudata.kemnaker.go.id/data/kumpulan-data/3246
- Peraturan Menteri Tenaga Kerja dan Transmigrasi No. PER.08/MEN/VII/2010 tentang Alat Pelindung Diri.
- Ahmad, H. M., & Rahimi, A. (2024). SH17: A Dataset for Human Safety and Personal Protective Equipment Detection in
  Manufacturing Industry. arXiv:2407.04590.
- Ultralytics. YOLO26 dan Construction-PPE Dataset. https://docs.ultralytics.com
- Dataset Kaggle: Construction Site Safety (CC BY 4.0), Safety Helmet and Reflective Jacket (Apache 2.0),
  HardHat-Vest v3 (CC0) — tautan di `docs/report-sources.md`.
