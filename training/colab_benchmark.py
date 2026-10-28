"""Benchmark kecepatan training YOLO26m: Google Colab vs laptop tim.

Cara pakai di Colab (Runtime -> Change runtime type -> T4 GPU):
  Sel 1:  !pip install -q ultralytics
  Sel 2:  tempel seluruh isi file ini, jalankan (~10-15 menit).
Salin baris "RESULT ..." di akhir dan kirim ke tim.

Yang diukur: gambar/detik HANYA saat training (validasi & unduhan tidak dihitung),
model yolo26m, imgsz 640, dataset Ultralytics Construction-PPE (unduh otomatis, AGPL-3.0).
"""

import os
import subprocess
import time

from ultralytics import YOLO

print(subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
                     capture_output=True, text=True).stdout.strip(), "| CPU cores:", os.cpu_count())

results = []
for batch in (4, 16):  # 4 = setelan laptop; 16 = muat di VRAM T4 16 GB
    model = YOLO("yolo26m.pt")
    marks = {}
    model.add_callback("on_train_epoch_start", lambda tr: marks.update(start=time.time()))
    model.add_callback("on_train_epoch_end", lambda tr: marks.update(
        end=time.time(), n=len(tr.train_loader.dataset)))
    model.train(data="construction-ppe.yaml", epochs=1, imgsz=640, batch=batch,
                workers=os.cpu_count(), val=False, plots=False,
                project="/content/bench", name=f"b{batch}", exist_ok=True)
    ips = marks["n"] / (marks["end"] - marks["start"])
    results.append(f"batch{batch}={ips:.1f} img/s")

print("RESULT", " | ".join(results))
