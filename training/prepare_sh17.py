"""Unduh SH17 dari Kaggle lalu buat subset IRIS (person, head, helmet, safety-vest).

Gambar dibaca langsung dari zip, di-resize (sisi terpanjang <= --max-side), dan label
di-remap ke skema IRIS. Tidak ada ekstraksi penuh, karena SH17 ~14 GB.

Pemakaian (dari root repo):
    .venv\\Scripts\\python training/prepare_sh17.py --download
    .venv\\Scripts\\python training/prepare_sh17.py --zip datasets/raw/sh17.zip --delete-zip

Kredensial Kaggle dibaca dari .env: KAGGLE_API_TOKEN, atau KAGGLE_USERNAME + KAGGLE_KEY.
"""

import argparse
import io
import os
import zipfile
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path, PurePosixPath

from dotenv import load_dotenv
from PIL import Image, ImageOps

KAGGLE_DATASET = "mugheesahmad/sh17-dataset-for-ppe-detection"

# ID kelas SH17 (sh17.yaml resmi) -> ID kelas IRIS
SH17_TO_IRIS = {0: 0, 12: 1, 10: 2, 16: 3}
IRIS_NAMES = ["person", "head", "helmet", "safety-vest"]

IMG_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def download(dest: Path) -> None:
    """Unduh zip SH17 (tanpa ekstrak) memakai library resmi `kaggle`."""
    load_dotenv()
    if not (os.getenv("KAGGLE_API_TOKEN") or (os.getenv("KAGGLE_USERNAME") and os.getenv("KAGGLE_KEY"))):
        raise SystemExit("Isi KAGGLE_API_TOKEN atau KAGGLE_USERNAME + KAGGLE_KEY di .env")
    from kaggle import api  # import setelah load_dotenv karena kaggle langsung autentikasi

    dest.parent.mkdir(parents=True, exist_ok=True)
    api.dataset_download_files(KAGGLE_DATASET, path=str(dest.parent), unzip=False, quiet=False)
    (dest.parent / f"{KAGGLE_DATASET.split('/')[1]}.zip").replace(dest)


def read_split(zf: zipfile.ZipFile, names: list[str], split_file: str) -> set[str]:
    member = next((n for n in names if PurePosixPath(n).name == split_file), None)
    if member is None:
        raise SystemExit(f"{split_file} tidak ditemukan di zip")
    lines = zf.read(member).decode("utf-8").splitlines()
    return {PurePosixPath(line.strip().replace("\\", "/")).stem for line in lines if line.strip()}


def convert_one(args) -> tuple[int, int]:
    """Proses satu chunk gambar. Return (jumlah gambar, jumlah objek IRIS)."""
    zip_path, jobs, out_root, max_side = args
    n_img = n_obj = 0
    with zipfile.ZipFile(zip_path) as zf:
        for img_member, label_member, split in jobs:
            stem = PurePosixPath(img_member).stem
            img = Image.open(io.BytesIO(zf.read(img_member)))
            img = ImageOps.exif_transpose(img).convert("RGB")
            img.thumbnail((max_side, max_side), Image.LANCZOS)
            img.save(out_root / "images" / split / f"{stem}.jpg", quality=90)

            out_lines = []
            if label_member:
                for line in zf.read(label_member).decode("utf-8").splitlines():
                    parts = line.split()
                    if len(parts) == 5 and int(parts[0]) in SH17_TO_IRIS:
                        out_lines.append(" ".join([str(SH17_TO_IRIS[int(parts[0])]), *parts[1:]]))
            (out_root / "labels" / split / f"{stem}.txt").write_text("\n".join(out_lines))
            n_img += 1
            n_obj += len(out_lines)
    return n_img, n_obj


def prepare(zip_path: Path, out_root: Path, max_side: int, workers: int) -> None:
    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
        splits = {"train": read_split(zf, names, "train_files.txt"),
                  "val": read_split(zf, names, "val_files.txt")}

    labels = {PurePosixPath(n).stem: n for n in names
              if n.endswith(".txt") and "/labels/" in f"/{n}"}
    images = [n for n in names if PurePosixPath(n).suffix.lower() in IMG_EXT]

    jobs = []
    for img in images:
        stem = PurePosixPath(img).stem
        split = next((s for s, stems in splits.items() if stem in stems), None)
        if split:
            jobs.append((img, labels.get(stem), split))
    print(f"gambar di zip: {len(images)}, masuk split: {len(jobs)} "
          f"(train {sum(j[2] == 'train' for j in jobs)}, val {sum(j[2] == 'val' for j in jobs)})")

    for split in splits:
        (out_root / "images" / split).mkdir(parents=True, exist_ok=True)
        (out_root / "labels" / split).mkdir(parents=True, exist_ok=True)

    chunks = [jobs[i::workers * 4] for i in range(workers * 4)]
    total_img = total_obj = 0
    with ProcessPoolExecutor(workers) as ex:
        for n_img, n_obj in ex.map(convert_one, [(zip_path, c, out_root, max_side) for c in chunks]):
            total_img += n_img
            total_obj += n_obj
            print(f"\rdiproses {total_img}/{len(jobs)}", end="", flush=True)
    print(f"\nselesai: {total_img} gambar, {total_obj} objek IRIS")

    yaml = (f"path: {out_root.resolve().as_posix()}\n"
            "train: images/train\nval: images/val\n\nnames:\n"
            + "".join(f"  {i}: {n}\n" for i, n in enumerate(IRIS_NAMES)))
    (out_root / "data.yaml").write_text(yaml)
    print(f"data.yaml ditulis ke {out_root / 'data.yaml'}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--download", action="store_true", help="unduh zip dari Kaggle dulu")
    ap.add_argument("--zip", type=Path, default=Path("datasets/raw/sh17.zip"))
    ap.add_argument("--out", type=Path, default=Path("datasets/sh17-iris"))
    ap.add_argument("--max-side", type=int, default=1024)
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 2))
    ap.add_argument("--delete-zip", action="store_true", help="hapus zip setelah selesai")
    args = ap.parse_args()

    if args.download:
        download(args.zip)
    prepare(args.zip, args.out, args.max_side, args.workers)
    if args.delete_zip:
        args.zip.unlink()
        print(f"zip dihapus: {args.zip}")


if __name__ == "__main__":
    main()
