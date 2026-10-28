# Training — IRIS

Dataset tidak disimpan di repo. Semua perintah dijalankan dari root repo.

## 1. Siapkan dataset SH17-IRIS

Butuh `KAGGLE_API_TOKEN` (atau `KAGGLE_USERNAME` + `KAGGLE_KEY`) di `.env`.

```
.venv\Scripts\python training/prepare_sh17.py --download --delete-zip
```

Skrip mengunduh zip SH17 (~13 GB), membaca gambar langsung dari zip, me-resize sisi terpanjang ke 1024 px,
dan me-remap kelas ke skema IRIS. Hasil: `datasets/sh17-iris/` (~1,15 GB) + `data.yaml`.

| ID IRIS | Kelas | ID SH17 |
|---|---|---|
| 0 | person | 0 |
| 1 | head | 12 |
| 2 | helmet | 10 |
| 3 | safety-vest | 16 |

Split resmi SH17 (`train_files.txt`, `val_files.txt`). Statistik hasil remap (instance / gambar):

| Split | Gambar | person | head | helmet | safety-vest |
|---|---|---|---|---|---|
| train | 6.479 | 11.068 / 6.102 | 9.558 / 5.181 | 773 / 373 | 433 / 168 |
| val | 1.620 | 2.734 / 1.515 | 2.427 / 1.314 | 154 / 93 | 97 / 45 |

Catatan: `helmet` dan `safety-vest` jauh lebih sedikit dibanding `person`/`head`.

## 2. Training

```
.venv\Scripts\python training/train.py --model yolo26m.pt --epochs 1 --name probe-yolo26m
.venv\Scripts\python training/train.py --model yolo26m.pt --epochs 100 --time <jam> --patience 20 --name sh17-yolo26m
```

Hasil di `runs/train/<name>/` (tidak di-commit). Metrik untuk laporan disalin ke `docs/assets/`.

## Atribusi

SH17 Dataset, CC BY-NC-SA 4.0 — H. M. Ahmad and A. Rahimi, arXiv:2407.04590, 2024.
