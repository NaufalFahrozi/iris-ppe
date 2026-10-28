"""Susun data.yaml gabungan untuk run 3 dari semua dataset *-iris.

Gambar dataset tambahan (pseudo-label person) yang kemungkinan besar punya banyak orang TIDAK berlabel dibuang dari
train: jika (helm + kepala) > 1.5 x person + 2. Tanpa filter ini model belajar bahwa orang kecil = latar belakang.

Pemakaian (dari root repo): .venv\\Scripts\\python training/build_merged.py
"""

from pathlib import Path

ROOT = Path("datasets").resolve()
FULL = ["sh17-iris", "cppe-iris", "css-iris"]   # label person lengkap (asli)
FILTERED = ["shrj-iris", "hhv-iris"]            # label person dari pseudo-label


def keep(label: Path) -> bool:
    ids = [l.split()[0] for l in label.read_text().splitlines() if l.strip()]
    persons = ids.count("0")
    return ids.count("1") + ids.count("2") <= 1.5 * persons + 2


def main() -> None:
    lists = {"train": [], "val": []}
    for split in lists:
        for ds in FULL + FILTERED:
            img_dir = ROOT / ds / "images" / split
            if not img_dir.exists():
                continue
            imgs = sorted(p for p in img_dir.iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".png"})
            if ds in FILTERED and split == "train":
                kept = [p for p in imgs if keep(ROOT / ds / "labels" / split / f"{p.stem}.txt")]
                print(f"{ds}/{split}: {len(kept)}/{len(imgs)} dipakai (filter orang tak berlabel)")
                imgs = kept
            else:
                print(f"{ds}/{split}: {len(imgs)}")
            lists[split] += [p.as_posix() for p in imgs]
        (ROOT / f"iris-all-{split}.txt").write_text("\n".join(lists[split]) + "\n")
    (ROOT / "iris-all.yaml").write_text(
        f"# Gabungan semua dataset IRIS (dibuat oleh training/build_merged.py)\npath: {ROOT.as_posix()}\n"
        "train: iris-all-train.txt\nval: iris-all-val.txt\n\n"
        "names:\n  0: person\n  1: head\n  2: helmet\n  3: safety-vest\n")
    print(f"train {len(lists['train'])} gambar, val {len(lists['val'])} gambar -> {ROOT / 'iris-all.yaml'}")


if __name__ == "__main__":
    main()
