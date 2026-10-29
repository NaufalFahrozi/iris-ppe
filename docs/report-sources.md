# Sumber Data untuk Laporan (latar belakang)

Hanya angka yang statusnya **terverifikasi** boleh dikutip apa adanya. Yang lain harus dicek ke sumber resmi dulu.

## Kecelakaan kerja di Indonesia (klaim JKK BPJS Ketenagakerjaan, diolah Kemnaker)

Dibaca langsung dari portal Satu Data Ketenagakerjaan (Kemnaker) pada 2026-10-29. Definisi resmi: jumlah klaim
kasus kecelakaan kerja = banyaknya peserta yang melakukan klaim kecelakaan kerja yang **telah disetujui dan dibayarkan**
oleh BPJS Ketenagakerjaan. Jadi angka ini adalah **klaim**, bukan seluruh kejadian (pekerja yang tidak terdaftar
BPJS tidak tercatat).

| Periode | Jumlah klaim | Penerima upah | Bukan penerima upah | Jasa konstruksi | Status | Sumber |
|---|---|---|---|---|---|---|
| Jan–Des 2024 | **462.241** | 91,65% | 7,43% | 0,92% | Terverifikasi | [satudata.kemnaker.go.id/data/kumpulan-data/2447](https://satudata.kemnaker.go.id/data/kumpulan-data/2447) |
| Jan–Des 2025 | **319.382** | 90,61% | 8,27% | 1,13% | Terverifikasi | [satudata.kemnaker.go.id/data/kumpulan-data/3246](https://satudata.kemnaker.go.id/data/kumpulan-data/3246) |
| Jan–Mei 2024 | 162.277 | 91,83% | 7,26% | 0,91% | Terverifikasi | [satudata.kemnaker.go.id/data/kumpulan-data/1881](https://satudata.kemnaker.go.id/data/kumpulan-data/1881) |

Catatan cara mengutip:
- Tulis "klaim kecelakaan kerja", bukan "kasus kecelakaan", dan sebut sumbernya (Kemnaker, Satu Data
  Ketenagakerjaan, diolah dari data BPJS Ketenagakerjaan).
- Persentase "jasa konstruksi" adalah **kategori kepesertaan BPJS**, bukan sektor tempat kejadian. Jangan ditulis
  "hanya ±1% kecelakaan terjadi di konstruksi".
- Contoh kalimat: "Sepanjang 2025 tercatat 319.382 klaim kecelakaan kerja pada program Jaminan Kecelakaan Kerja
  BPJS Ketenagakerjaan (Kemnaker, 2026), atau rata-rata lebih dari 870 klaim per hari." (319.382 / 365 ≈ 875)

Belum terverifikasi (dari media/blog, **jangan dikutip** sebelum dicek ke sumber resmi):
- "319.224 klaim dan 9.834 kematian pada 2025" ([harian.news](https://harian.news/319-224-klaim-kecelakaan-kerja-2025-menaker-bpjs-harus-jadi-motor-k3))
- Sebaran per provinsi 2025, Jawa Timur terbanyak ([Databoks](https://databoks.katadata.co.id/ketenagakerjaan/statistik/69dc599b93235/sebaran-kasus-kecelakaan-kerja-di-ri-2025-jatim-terbanyak), [GoodStats](https://data.goodstats.id/statistic/indonesia-catat-319-ribu-kasus-kecelakaan-kerja-pada-2025-jawa-timur-terbanyak-Fejk9))
- Klaim "29%/32% kecelakaan terjadi di konstruksi" ([CNBC Indonesia](https://www.cnbcindonesia.com/news/20250826131119-4-661455/angka-kecelakaan-kerja-di-ri-meningkat-biang-keroknya-terbongkar)) — definisi dan periodenya berbeda

## Dasar hukum APD

| Peraturan | Isi yang relevan | Status | Sumber |
|---|---|---|---|
| Permenakertrans No. PER.08/MEN/VII/2010 tentang Alat Pelindung Diri (ditetapkan 6 Juli 2010) | Pasal 2: pengusaha wajib menyediakan APD bagi pekerja/buruh di tempat kerja, sesuai SNI, tanpa biaya; Pasal 6: pekerja wajib memakai APD sesuai potensi bahaya; Pasal 9: sanksi mengacu UU No. 1 Tahun 1970 | Isi pasal dari ringkasan sekunder; **cek teks resmi di JDIH Kemnaker / peraturan.go.id** sebelum dikutip kata per kata | [pasal.id](https://pasal.id/peraturan/permen/permenakertrans-no-per-08-men-vii-2010-tahun-2010), [JDIH Kemnaker](https://jdih.kemnaker.go.id/peraturan?hal=47&page=1), [DDTC](https://perpajakan.ddtc.co.id/id/sumber-hukum/peraturan-pusat/peraturan-menteri-tenaga-kerja-dan-transmigrasi-per-08menvii2010) |
| UU No. 1 Tahun 1970 tentang Keselamatan Kerja | Dasar hukum K3 di Indonesia | Umum dikenal; cek teks resmi | peraturan.go.id |

## Dataset (atribusi wajib di laporan)

| Dataset | Lisensi | Sitasi / tautan |
|---|---|---|
| SH17 | CC BY-NC-SA 4.0 | H. M. Ahmad & A. Rahimi, "SH17: A Dataset for Human Safety and PPE Detection in Manufacturing Industry", arXiv:2407.04590, 2024 |
| Ultralytics Construction-PPE | AGPL-3.0 | https://docs.ultralytics.com/datasets/detect/construction-ppe/ |
| Construction Site Safety Image Dataset (Roboflow) | CC BY 4.0 | https://www.kaggle.com/datasets/snehilsanyal/construction-site-safety-image-dataset-roboflow |
| Safety Helmet and Reflective Jacket | Apache 2.0 | https://www.kaggle.com/datasets/niravnaik/safety-helmet-and-reflective-jacket |
| HardHat-Vest Dataset v3 | CC0 | https://www.kaggle.com/datasets/muhammetzahitaydn/hardhat-vest-dataset-v3 |
| Video uji (Pexels 5434223, 5423610, 11798561, 8965561) | Lisensi Pexels | https://www.pexels.com/license/ — hanya untuk pengujian, tidak didistribusikan ulang di repo |
