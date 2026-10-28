"""Ubah Ultralytics Construction-PPE ke skema IRIS dan isi label `head` yang hilang (pseudo-label).

Construction-PPE tidak memberi label kepala untuk orang yang memakai helm (hanya `no_helmet`). Label `head` untuk
kepala tersebut diisi dari prediksi model IRIS yang sudah dilatih di SH17 (conf >= --conf), agar tidak bertentangan
dengan SH17 yang melabeli semua kepala.

Pemakaian (dari root repo):
    curl -L -o datasets/raw/construction-ppe.zip https://github.com/ultralytics/assets/releases/download/v0.0.0/construction-ppe.zip
    (ekstrak ke datasets/raw/cppe)
    .venv\\Scripts\\python training/prepare_cppe.py --model runs/train/sh17-yolo26m/weights/last.pt
"""

import argparse
import shutil
from pathlib import Path

from ultralytics import YOLO

# ID Construction-PPE -> ID IRIS (0 person, 1 head, 2 helmet, 3 safety-vest)
CPPE_TO_IRIS = {6: 0, 7: 1, 0: 2, 2: 3}
HEAD = 1


def iou(a, b):
    """IoU dua kotak format YOLO ternormalisasi (cx, cy, w, h)."""
    ax1, ay1, ax2, ay2 = a[0] - a[2] / 2, a[1] - a[3] / 2, a[0] + a[2] / 2, a[1] + a[3] / 2
    bx1, by1, bx2, by2 = b[0] - b[2] / 2, b[1] - b[3] / 2, b[0] + b[2] / 2, b[1] + b[3] / 2
    inter = max(0, min(ax2, bx2) - max(ax1, bx1)) * max(0, min(ay2, by2) - max(ay1, by1))
    union = a[2] * a[3] + b[2] * b[3] - inter
    return inter / union if union > 0 else 0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", type=Path, default=Path("datasets/raw/cppe"))
    ap.add_argument("--out", type=Path, default=Path("datasets/cppe-iris"))
    ap.add_argument("--model", type=Path, required=True, help="model IRIS untuk pseudo-label head")
    ap.add_argument("--conf", type=float, default=0.5)
    args = ap.parse_args()

    model = YOLO(args.model)
    for split in ("train", "val"):
        img_dir, lbl_dir = args.src / "images" / split, args.src / "labels" / split
        out_img, out_lbl = args.out / "images" / split, args.out / "labels" / split
        out_img.mkdir(parents=True, exist_ok=True)
        out_lbl.mkdir(parents=True, exist_ok=True)
        images = sorted(p for p in img_dir.iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".png"})
        counts = {"images": 0, "kept": 0, "pseudo_head": 0}

        for i in range(0, len(images), 16):
            batch = images[i:i + 16]
            results = model.predict([str(p) for p in batch], classes=[HEAD], conf=args.conf, verbose=False)
            for img, res in zip(batch, results):
                boxes = []
                lbl = lbl_dir / f"{img.stem}.txt"
                if lbl.exists():
                    for line in lbl.read_text().splitlines():
                        parts = line.split()
                        if len(parts) == 5 and int(parts[0]) in CPPE_TO_IRIS:
                            boxes.append((CPPE_TO_IRIS[int(parts[0])], *map(float, parts[1:])))
                counts["kept"] += len(boxes)
                heads = [b[1:] for b in boxes if b[0] == HEAD]
                for xywh in res.boxes.xywhn.tolist():
                    if all(iou(xywh, h) < 0.5 for h in heads):  # jangan duplikasi kepala no_helmet
                        boxes.append((HEAD, *xywh))
                        heads.append(xywh)
                        counts["pseudo_head"] += 1
                shutil.copy(img, out_img / img.name)
                (out_lbl / f"{img.stem}.txt").write_text(
                    "\n".join(f"{c} {x:.6f} {y:.6f} {w:.6f} {h:.6f}" for c, x, y, w, h in boxes))
                counts["images"] += 1
        print(split, counts, flush=True)

    root = args.out.parent.resolve().as_posix()
    yaml = (f"# SH17-IRIS + Construction-PPE-IRIS (dibuat oleh training/prepare_cppe.py)\npath: {root}\n"
            "train:\n  - sh17-iris/images/train\n  - cppe-iris/images/train\n"
            "val:\n  - sh17-iris/images/val\n  - cppe-iris/images/val\n\n"
            "names:\n  0: person\n  1: head\n  2: helmet\n  3: safety-vest\n")
    (args.out.parent / "iris-merged.yaml").write_text(yaml)
    print(f"data yaml: {args.out.parent / 'iris-merged.yaml'}")


if __name__ == "__main__":
    main()
