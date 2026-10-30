# Panduan Uji & Demo IRIS (untuk tim)

Ikuti urutan ini persis. Semua perintah dijalankan di **PowerShell** dari folder proyek `C:\Kuliah\iris-ppe`.
Kalau ada yang tidak sesuai "Yang harus terlihat", lihat bagian **Kalau ada masalah** di bawah.

## 0. Persiapan (sekali saja)

- Laptop dicolok charger, layar jangan ditutup. Di mode baterai GPU dibatasi dan FPS turun drastis.
- **Matikan sleep** (Settings → System → Power → saat dicolok: sleep = Never). Setelah sleep, GPU RTX 4050 bisa hilang
  dari sistem dan vision diam-diam jalan di CPU (±7 FPS). Cek sebelum mulai:
  `.venv\Scripts\python -c "import torch; print(torch.cuda.is_available())"` harus `True`; kalau `False`, restart laptop.
- Bobot model ada di `models\iris-best.pt` (disalin dari hasil training terbaik).
- Webcam terpasang. Posisi kamera: **2–4 meter** dari orang, **seluruh badan** (kepala sampai pinggang minimal)
  terlihat, cahaya terang dari depan (jangan membelakangi jendela).
- APD untuk uji: helm proyek + rompi. Siapkan juga kondisi "tanpa rompi" dan "tanpa helm".

## Cara cepat: `start-iris.bat`

Double-click `start-iris.bat`, pilih mode (1 gerbang, 2 zona, 3/4 latihan tanpa rompi, 5 simulator, 6 dashboard),
tekan Enter untuk kamera USB (indeks 1). Launcher menjalankan langkah 2 dan 3 di bawah secara otomatis; langkah 1
(wokwi.com) tetap manual sesuai petunjuk di layar. Langkah manual di bawah dipakai jika launcher bermasalah.

## 1. Jalankan ESP32 (Wokwi)

Pilih salah satu:

- **A. wokwi.com (untuk demo/video):** buka proyek IRIS di wokwi.com, tekan ▶, tunggu `[MQTT] connected`, lalu geser
  slide switch **SOURCE ke kiri (LIVE)** dan **ROLE** sesuai mode (kiri = GATE, kanan = ZONE). Setelah halaman dimuat
  ulang, SOURCE kembali ke TEST, jadi perlu digeser lagi. Jalankan hanya satu simulasi, dan jendelanya harus tetap
  terlihat di layar (lihat bagian 5).
- **B. wokwi-cli (tanpa browser):**
  ```
  cd firmware; pio run; cd ..
  .venv\Scripts\python firmware/test/run_tests.py failsafe
  ```
  (opsi B hanya untuk cek cepat; untuk demo pakai A agar rangkaian terlihat)

**Yang harus terlihat:** di Serial Monitor muncul `[NET] wifi connected`, lalu `[MQTT] connected`. OLED menampilkan
`OFFLINE` (kuning berkedip) karena vision belum jalan. Ini **benar** (fail-safe).

## 2. Jalankan dashboard (jendela PowerShell kedua)

```
.venv\Scripts\python dashboard/app.py
```

Buka http://127.0.0.1:8050 di browser. **Yang harus terlihat:** "Broker terhubung" hijau, kartu `gate1`/`zoneA`.

## 3. Jalankan vision dengan webcam (jendela PowerShell ketiga)

Di laptop tim, webcam USB = `--source 1` (kamera bawaan di indeks 0 rusak dan hanya memberi frame hitam).

Mode **gerbang** (webcam dekat, seluruh frame dihitung; ROI hanya dipakai jika kaki orang terlihat di frame):

```
.venv\Scripts\python vision/run_vision.py --source 1 --node gate1 --show
```

Mode **zona** (monitoring ala CCTV):

```
.venv\Scripts\python vision/run_vision.py --source 1 --node zoneA --show
```

Untuk kamera CCTV yang jauh (orang kecil di frame) tambahkan `--imgsz 1280`.

Latihan tanpa rompi: tambahkan `--ignore-vest` (rompi dianggap selalu dipakai). **Jangan dipakai saat rekam demo.**

Jendela "IRIS vision" muncul. Kotak **hijau** = patuh, **merah** = melanggar, abu-abu = di luar ROI.
Label `H:Y V:N` artinya helm terdeteksi, rompi tidak. Tekan `q` di jendela itu untuk berhenti.

**Yang harus terlihat:** OLED ESP32 berubah dari `OFFLINE` ke `SIAP` (gerbang) / `AMAN` (zona) dalam beberapa
detik; dashboard menulis "Server vision online".

## 4. Skenario uji (catat hasilnya di `docs/testing-log.md`, rekam layar sebagai bukti)

| ID | Lakukan | Yang harus terjadi |
|---|---|---|
| T1 | 1 orang, helm + rompi, berdiri di depan kamera (mode gerbang) | Palang (servo) terbuka, LED hijau, OLED "MASUK", dashboard `GRANTED`. Palang menutup sendiri setelah 5 s |
| T2 | 1 orang, helm saja (tanpa rompi) | Palang tetap tertutup, LED merah, buzzer bip, OLED "Kurang: ROMPI" |
| T3 | Tutup jendela vision (`q`) | ±8 s kemudian OLED "OFFLINE", LED kuning berkedip, palang terkunci; dashboard "Server vision offline" |
| T4 | 2 orang, satu lengkap, satu tanpa helm | Palang tetap tertutup, OLED "Kurang: HELM" |
| T5 | Orang lengkap masuk (palang terbuka) lalu orang tanpa APD ikut masuk frame | Palang langsung menutup + buzzer |
| T6 | Mode zona: pakai lengkap, lalu lepas helm dan tunggu | < 3 s: tetap AMAN; 3 s: LED kuning "AWAS"; 8 s: LED merah + buzzer "ALARM!" + event di dashboard; pakai helm lagi: kembali AMAN |
| OV | Saat alarm bunyi, klik **Reset alarm** di dashboard atau tombol RESET di Wokwi | Buzzer berhenti, palang tetap tertutup |

Tips agar deteksi stabil: menghadap kamera, jangan terlalu dekat (badan harus terlihat), helm warna terang lebih
mudah terdeteksi daripada helm hitam, rompi reflektif paling mudah.

## 5. Kalau ada masalah

| Gejala | Kemungkinan penyebab | Cara cek / perbaiki |
|---|---|---|
| OLED tetap `OFFLINE` padahal vision jalan | Node tidak cocok, atau SOURCE masih TEST | Pastikan `--node gate1` untuk ROLE=GATE dan `zoneA` untuk ROLE=ZONE; slide switch SOURCE di **kiri (LIVE)** |
| Serial tidak pernah `[MQTT] connected` | Internet putus / broker sibuk | Cek internet; tunggu (firmware mencoba ulang tiap 5 s) |
| Jendela vision tidak muncul / error kamera | Webcam dipakai aplikasi lain atau indeks salah | Tutup Zoom/Teams/kamera; coba `--source 1` |
| Orang terdeteksi tapi helm/rompi tidak (`H:N`) | Terlalu jauh, gelap, helm hitam, membelakangi | Mendekat ke 2–3 m, tambah cahaya, menghadap kamera; bisa turunkan ambang: `--conf-helmet 0.2 --conf-vest 0.2` |
| Palang buka-tutup terus | Deteksi tidak stabil | Perbaiki posisi/cahaya; status APD diputuskan dari mayoritas 1 detik terakhir, jadi tunggu ±1 s |
| FPS rendah (< 10) | GPU dipakai training, atau imgsz 1280 | Hentikan training; untuk gerbang pakai default (640) |
| Dashboard "Broker terputus" | Internet putus | Sambungkan internet, refresh halaman |
| `ModuleNotFoundError` | venv belum dipakai | Selalu jalankan dengan `.venv\Scripts\python` |
| `No Python at '...cpython-3.12.12...'` | Python dasar venv belum terpasang untuk user ini | `uv python install 3.12.12`, lalu ulangi |
| Kecepatan simulasi Wokwi turun ke ±3%, dashboard `gate1`/`zoneA` OFFLINE | Jendela Wokwi tersembunyi (diminimize atau tertutup jendela lain) sehingga browser menahannya | Tampilkan jendela Wokwi; jika koneksi sudah putus, tekan ⟳ lalu geser SOURCE ke LIVE lagi |
| Serial terus `wifi connecting`, ikon WiFi simulator dicoret | Gateway Wokwi belum tersambung, terutama setelah ganti jaringan (saat uji butuh ±1 menit) | Tunggu sebentar; jika masih gagal, muat ulang halaman dan tekan ▶ lagi |
| Dashboard tertulis "Broker terhubung" tetapi datanya berhenti | Dashboard tidak berlangganan ulang setelah koneksi internet putus | Jalankan ulang dashboard |
| Spam `can't grab frame` / layar hitam | Indeks kamera salah (kamera bawaan rusak) | Pakai `--source 1` (webcam USB) |

Kalau masih bingung: salin pesan error lengkap + jelaskan langkah yang dilakukan, kirim ke Naufal / agent.

## 6. Checklist rekam video demo (rubrik 10%)

Rekam layar (OBS / Xbox Game Bar `Win+G`) dengan **3 jendela terlihat bersamaan**: kamera vision, Wokwi
(rangkaian + Serial Monitor), dan dashboard. Urutan yang disarankan (±3–5 menit):

1. Pembukaan: judul IRIS, masalah (data klaim kecelakaan kerja Kemnaker), solusi singkat.
2. Arsitektur: diagram kamera → server vision → MQTT → ESP32 → dashboard.
3. Rangkaian Wokwi: tunjukkan komponen dan GPIO (input kiri, output kanan).
4. Demo T1, T2, T4/T5 (gerbang), T6 (zona), T3 (fail-safe), reset alarm dari dashboard.
5. Dashboard: compliance rate, grafik pelanggaran, tabel event.
6. Penutup: keterbatasan + pengembangan lanjutan.

Simpan sebagai `.mp4`. Jangan commit video ke repo (sudah di `.gitignore`); unggah ke Drive dan catat link-nya di README.
