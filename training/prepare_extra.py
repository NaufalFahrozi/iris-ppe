"""Gabungkan dataset PPE tambahan (format YOLO, dalam zip) ke skema IRIS.

Untuk tiap dataset: kelas dipetakan ke IRIS (0 person, 1 head, 2 helmet, 3 safety-vest), subset dipilih dengan
memprioritaskan gambar berisi rompi, lalu kelas yang TIDAK dilabeli lengkap oleh dataset itu diisi pseudo-label dari
model IRIS (conf >= --conf), tanpa menduplikasi kotak yang sudah ada (IoU >= 0.5).

Pemakaian (dari root repo):
    .venv\\Scripts\\python training/prepare_extra.py --model <bobot.pt>
"""

import argparse
import io
import random
import zipfile
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath

import yaml
from PIL import Image, ImageOps
from ultralytics import YOLO

IRIS_NAMES = ["person", "head", "helmet", "safety-vest"]

# name: (zip, {nama kelas sumber (lowercase): id IRIS}, kelas IRIS yang perlu pseudo-label, batas gambar per split)
DATASETS = {
    "css": ("construction-site-safety-image-dataset-roboflow.zip",
            {"person": 0, "no-hardhat": 1, "hardhat": 2, "safety vest": 3},
            [1], {"train": None, "val": None, "test": None}),
    "shrj": ("safety-helmet-and-reflective-jacket.zip",
             {"safety-helmet": 2, "helmet": 2, "reflective-jacket": 3, "jacket": 3},
             [0, 1], {"train": 4000, "val": 400, "test": 600}),
    "hhv": ("hardhat-vest-dataset-v3.zip",
            {"head": 1, "helmet": 2, "vest": 3},
            [0, 1], {"train": 6000, "val": 500, "test": 1000}),
}
# Zip tanpa file yaml: urutan nama kelas ditetapkan dari jumlah instance per id vs tabel deskripsi dataset
MANUAL_NAMES = {"hhv": ["helmet", "vest", "head"]}
SPLIT_ALIASES = {"train": "train", "valid": "val", "val": "val", "validation": "val", "test": "test"}
IMG_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def iou(a, b):
    ax1, ay1, ax2, ay2 = a[0] - a[2] / 2, a[1] - a[3] / 2, a[0] + a[2] / 2, a[1] + a[3] / 2
    bx1, by1, bx2, by2 = b[0] - b[2] / 2, b[1] - b[3] / 2, b[0] + b[2] / 2, b[1] + b[3] / 2
    inter = max(0, min(ax2, bx2) - max(ax1, bx1)) * max(0, min(ay2, by2) - max(ay1, by1))
    union = a[2] * a[3] + b[2] * b[3] - inter
    return inter / union if union > 0 else 0


def find_names(zf: zipfile.ZipFile) -> list[str]:
    """Ambil daftar nama kelas dari file yaml dataset di dalam zip (data.yaml, ppe_data.yaml, ...)."""
    for n in zf.namelist():
        if PurePosixPath(n).suffix.lower() in {".yaml", ".yml"} and PurePosixPath(n).name != "args.yaml":
            doc = yaml.safe_load(zf.read(n))
            if isinstance(doc, dict) and "names" in doc:
                names = doc["names"]
                return list(names.values()) if isinstance(names, dict) else list(names)
    raise SystemExit("yaml berisi 'names' tidak ditemukan di zip")


def index_pairs(zf: zipfile.ZipFile):
    """(split, stem) -> (gambar, label) berdasarkan folder .../<split>/images & .../<split>/labels."""
    imgs, lbls = {}, {}
    for n in zf.namelist():
        p = PurePosixPath(n)
        parts = [x.lower() for x in p.parts]
        split = next((SPLIT_ALIASES[x] for x in parts if x in SPLIT_ALIASES), None)
        if split is None:
            continue
        if p.suffix.lower() in IMG_EXT and "images" in parts:
            imgs[(split, p.stem)] = n
        elif p.suffix == ".txt" and "labels" in parts:
            lbls[(split, p.stem)] = n
    return {k: (v, lbls.get(k)) for k, v in imgs.items()}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", type=Path, default=Path("datasets/raw/extra"))
    ap.add_argument("--out", type=Path, default=Path("datasets"))
    ap.add_argument("--model", type=Path, required=True)
    ap.add_argument("--conf", type=float, default=0.5)
    ap.add_argument("--max-side", type=int, default=1024)
    ap.add_argument("--only", nargs="*", default=list(DATASETS))
    args = ap.parse_args()
    random.seed(0)
    model = YOLO(args.model)

    for key in args.only:
        zname, mapping, pseudo, limits = DATASETS[key]
        with zipfile.ZipFile(args.raw / zname) as zf:
            names = MANUAL_NAMES.get(key) or find_names(zf)
            src_to_iris = {i: mapping[n.lower()] for i, n in enumerate(names) if n.lower() in mapping}
            print(f"[{key}] kelas sumber {names} -> IRIS {src_to_iris}", flush=True)
            pairs = index_pairs(zf)

            by_split = defaultdict(list)
            for (split, stem), (img, lbl) in pairs.items():
                boxes = []
                if lbl:
                    for line in zf.read(lbl).decode("utf-8", "ignore").splitlines():
                        p = line.split()
                        if len(p) == 5 and int(p[0]) in src_to_iris:
                            boxes.append((src_to_iris[int(p[0])], *map(float, p[1:])))
                by_split[split].append((stem, img, boxes))

            for split, items in by_split.items():
                limit = limits.get(split)
                random.shuffle(items)
                if limit and len(items) > limit:  # prioritaskan gambar yang berisi rompi
                    with_vest = [it for it in items if any(b[0] == 3 for b in it[2])]
                    rest = [it for it in items if not any(b[0] == 3 for b in it[2])]
                    items = (with_vest + rest)[:limit]
                out_img = args.out / f"{key}-iris" / "images" / split
                out_lbl = args.out / f"{key}-iris" / "labels" / split
                out_img.mkdir(parents=True, exist_ok=True)
                out_lbl.mkdir(parents=True, exist_ok=True)
                counts = Counter()
                for i in range(0, len(items), 16):
                    batch = items[i:i + 16]
                    ims = []
                    for stem, img, _ in batch:
                        im = ImageOps.exif_transpose(Image.open(io.BytesIO(zf.read(img)))).convert("RGB")
                        im.thumbnail((args.max_side, args.max_side), Image.LANCZOS)
                        ims.append(im)
                    results = model.predict(ims, classes=pseudo, conf=args.conf, verbose=False)
                    for (stem, _, boxes), im, res in zip(batch, ims, results):
                        boxes = list(boxes)
                        for cls, xywh in zip(res.boxes.cls.tolist(), res.boxes.xywhn.tolist()):
                            same = [b[1:] for b in boxes if b[0] == int(cls)]
                            if all(iou(xywh, b) < 0.5 for b in same):
                                boxes.append((int(cls), *xywh))
                                counts[f"pseudo_{IRIS_NAMES[int(cls)]}"] += 1
                        safe = f"{key}_{stem}"[:120]
                        im.save(out_img / f"{safe}.jpg", quality=90)
                        (out_lbl / f"{safe}.txt").write_text(
                            "\n".join(f"{c} {x:.6f} {y:.6f} {w:.6f} {h:.6f}" for c, x, y, w, h in boxes))
                        counts["images"] += 1
                        counts.update(IRIS_NAMES[b[0]] for b in boxes)
                print(f"[{key}] {split}: {dict(counts)}", flush=True)


if __name__ == "__main__":
    main()
