# Metrik model IRIS

Bobot: `runs/train/all-yolo26m/weights/best.pt`  
Diukur: 2026-10-29 17:43


## sh17-val — mAP50 0.748, mAP50-95 0.555

Data `data.yaml` (split val, imgsz 640); inferensi 10.33 ms/gambar.


| Kelas | Precision | Recall | AP50 | AP50-95 | F1 terbaik | conf @F1 terbaik |
|---|---|---|---|---|---|---|
| person | 0.914 | 0.866 | 0.918 | 0.750 | 0.891 | 0.41 |
| head | 0.945 | 0.880 | 0.922 | 0.705 | 0.912 | 0.37 |
| helmet | 0.705 | 0.597 | 0.643 | 0.430 | 0.655 | 0.41 |
| safety-vest | 0.683 | 0.546 | 0.510 | 0.334 | 0.616 | 0.42 |

## all-val — mAP50 0.868, mAP50-95 0.614

Data `iris-all.yaml` (split val, imgsz 640); inferensi 12.76 ms/gambar.


| Kelas | Precision | Recall | AP50 | AP50-95 | F1 terbaik | conf @F1 terbaik |
|---|---|---|---|---|---|---|
| person | 0.874 | 0.861 | 0.911 | 0.725 | 0.870 | 0.44 |
| head | 0.934 | 0.725 | 0.846 | 0.646 | 0.828 | 0.22 |
| helmet | 0.818 | 0.746 | 0.814 | 0.480 | 0.782 | 0.41 |
| safety-vest | 0.878 | 0.849 | 0.900 | 0.605 | 0.867 | 0.42 |

## public-test — mAP50 0.846, mAP50-95 0.588

Data `iris-public-test.yaml` (split test, imgsz 640); inferensi 16.35 ms/gambar.


| Kelas | Precision | Recall | AP50 | AP50-95 | F1 terbaik | conf @F1 terbaik |
|---|---|---|---|---|---|---|
| person | 0.791 | 0.858 | 0.895 | 0.729 | 0.827 | 0.39 |
| head | 0.922 | 0.518 | 0.712 | 0.484 | 0.712 | 0.07 |
| helmet | 0.840 | 0.769 | 0.850 | 0.504 | 0.808 | 0.38 |
| safety-vest | 0.851 | 0.889 | 0.927 | 0.637 | 0.874 | 0.45 |

## FPS (model.track + ByteTrack, tanpa tampilan/MQTT)

| Video | imgsz | Frame | FPS |
|---|---|---|---|
| pexels-11798561.mp4 | 640 | 300 | 79.5 |
| pexels-11798561.mp4 | 1280 | 300 | 28.3 |
| pexels-5434223.mp4 | 640 | 300 | 77.1 |
| pexels-5434223.mp4 | 1280 | 300 | 27.5 |

Catatan: pada all-val dan public-test, kelas person/head sebagian berasal dari pseudo-label; angka helm dan rompi memakai label asli.
