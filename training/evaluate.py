"""Evaluasi bobot IRIS untuk laporan: AP per kelas, ambang confidence F1-optimal, dan FPS.

Contoh (dari root repo):
    .venv\\Scripts\\python training/evaluate.py --weights runs/train/all-yolo26m/weights/best.pt
    # tambah ukur FPS inferensi + tracking di video
    .venv\\Scripts\\python training/evaluate.py --weights models/iris-best.pt --bench-video datasets/videos/x.mp4

Hasil: docs/assets/model/metrics.md, metrics.json, dan plot (confusion matrix, kurva PR/F1) per set.

Set evaluasi:
- sh17-val  : val resmi SH17 (label asli semua kelas, tanpa pseudo-label) -> angka utama
- all-val   : val gabungan 5 dataset (person/head sebagian pseudo-label)
- public-test: split test CSS + SHRJ + HHV (tidak dipakai training; helm & rompi berlabel asli)
"""

import argparse
import json
import shutil
import time
from pathlib import Path

import numpy as np
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parents[1]
DS = ROOT / "datasets"
NAMES = {0: "person", 1: "head", 2: "helmet", 3: "safety-vest"}
TEST_SOURCES = ["css-iris", "shrj-iris", "hhv-iris"]


def make_test_yaml() -> Path:
    """Gabungkan split test publik menjadi satu daftar gambar."""
    files = []
    for src in TEST_SOURCES:
        files += sorted(str(p).replace("\\", "/") for p in (DS / src / "images" / "test").glob("*") if p.is_file())
    lst = DS / "iris-public-test.txt"
    lst.write_text("\n".join(files) + "\n", encoding="utf-8")
    yml = DS / "iris-public-test.yaml"
    names = "\n".join(f"  {k}: {v}" for k, v in NAMES.items())
    yml.write_text(f"path: {DS.as_posix()}\ntrain: {lst.name}\nval: {lst.name}\ntest: {lst.name}\n\nnames:\n{names}\n",
                   encoding="utf-8")
    return yml


def best_f1_threshold(box, idx: int) -> tuple[float, float]:
    """Confidence dengan F1 tertinggi untuk satu kelas, dari kurva F1 hasil val."""
    f1 = getattr(box, "f1_curve", None)
    px = getattr(box, "px", None)
    if f1 is None or px is None or len(f1) <= idx:
        return float("nan"), float("nan")
    i = int(np.argmax(f1[idx]))
    return float(px[i]), float(f1[idx][i])


def evaluate(model: YOLO, name: str, data: Path, split: str, imgsz: int, out: Path) -> dict:
    print(f"\n=== {name} ({data.name}, split={split}, imgsz={imgsz}) ===", flush=True)
    m = model.val(data=str(data), split=split, imgsz=imgsz, batch=4, workers=0, plots=True,
                  project=str(ROOT / "runs" / "eval"), name=name, exist_ok=True, verbose=False)
    box = m.box
    classes = {}
    for pos, c in enumerate(box.ap_class_index):
        c = int(c)
        thr, f1 = best_f1_threshold(box, pos)
        classes[NAMES[c]] = {
            "precision": round(float(box.p[pos]), 4),
            "recall": round(float(box.r[pos]), 4),
            "ap50": round(float(box.ap50[pos]), 4),
            "ap50_95": round(float(box.ap[pos]), 4),
            "best_f1": round(f1, 4),
            "best_f1_conf": round(thr, 3),
        }
    res = {
        "data": data.name, "split": split, "imgsz": imgsz,
        "map50": round(float(box.map50), 4), "map50_95": round(float(box.map), 4),
        "speed_ms": {k: round(v, 2) for k, v in m.speed.items()},
        "classes": classes,
    }
    # salin plot penting untuk laporan
    dst = out / name
    dst.mkdir(parents=True, exist_ok=True)
    for f in Path(m.save_dir).glob("*.png"):
        if any(k in f.name for k in ("confusion_matrix", "PR_curve", "F1_curve")):
            shutil.copy2(f, dst / f.name)
    return res


def bench_video(model: YOLO, video: Path, imgsz: int, frames: int) -> dict:
    """FPS end-to-end model.track (inferensi + ByteTrack) pada video, tanpa tampilan dan MQTT."""
    import cv2

    cap = cv2.VideoCapture(str(video))
    imgs = []
    while len(imgs) < frames:
        ok, f = cap.read()
        if not ok:
            break
        imgs.append(f)
    cap.release()
    for f in imgs[:10]:  # pemanasan GPU
        model.track(f, imgsz=imgsz, persist=True, verbose=False, tracker="bytetrack.yaml")
    t = time.perf_counter()
    for f in imgs:
        model.track(f, imgsz=imgsz, persist=True, verbose=False, tracker="bytetrack.yaml")
    dt = time.perf_counter() - t
    fps = len(imgs) / dt if dt else 0.0
    print(f"[BENCH] {video.name} imgsz={imgsz}: {len(imgs)} frame, {fps:.1f} FPS", flush=True)
    return {"video": video.name, "imgsz": imgsz, "frames": len(imgs), "fps": round(fps, 1)}


def write_markdown(report: dict, path: Path) -> None:
    lines = [f"# Metrik model IRIS\n", f"Bobot: `{report['weights']}`  \nDiukur: {report['date']}\n"]
    for name, r in report["sets"].items():
        lines += [f"\n## {name} — mAP50 {r['map50']:.3f}, mAP50-95 {r['map50_95']:.3f}\n",
                  f"Data `{r['data']}` (split {r['split']}, imgsz {r['imgsz']}); "
                  f"inferensi {r['speed_ms'].get('inference', 0)} ms/gambar.\n",
                  "\n| Kelas | Precision | Recall | AP50 | AP50-95 | F1 terbaik | conf @F1 terbaik |",
                  "|---|---|---|---|---|---|---|"]
        for c, v in r["classes"].items():
            lines.append(f"| {c} | {v['precision']:.3f} | {v['recall']:.3f} | {v['ap50']:.3f} | {v['ap50_95']:.3f} "
                         f"| {v['best_f1']:.3f} | {v['best_f1_conf']:.2f} |")
    if report.get("bench"):
        lines += ["\n## FPS (model.track + ByteTrack, tanpa tampilan/MQTT)\n", "| Video | imgsz | Frame | FPS |",
                  "|---|---|---|---|"]
        lines += [f"| {b['video']} | {b['imgsz']} | {b['frames']} | {b['fps']} |" for b in report["bench"]]
    lines.append("\nCatatan: pada all-val dan public-test, kelas person/head sebagian berasal dari pseudo-label; "
                 "angka helm dan rompi memakai label asli.\n")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--weights", default="runs/train/all-yolo26m/weights/best.pt")
    ap.add_argument("--imgsz", type=int, default=640)
    ap.add_argument("--sets", nargs="+", default=["sh17-val", "all-val", "public-test"])
    ap.add_argument("--bench-video", nargs="*", default=[], help="video untuk ukur FPS")
    ap.add_argument("--bench-imgsz", type=int, nargs="+", default=[640, 1280])
    ap.add_argument("--bench-frames", type=int, default=300)
    ap.add_argument("--out", default="docs/assets/model")
    args = ap.parse_args()

    out = ROOT / args.out
    out.mkdir(parents=True, exist_ok=True)
    model = YOLO(str(ROOT / args.weights))
    sets = {
        "sh17-val": (DS / "sh17-iris" / "data.yaml", "val"),
        "all-val": (DS / "iris-all.yaml", "val"),
        "public-test": (None, "test"),
    }
    report = {"weights": args.weights, "date": time.strftime("%Y-%m-%d %H:%M"), "sets": {}, "bench": []}
    for name in args.sets:
        data, split = sets[name]
        if data is None:
            data = make_test_yaml()
        report["sets"][name] = evaluate(model, name, data, split, args.imgsz, out)
    for v in args.bench_video:
        for sz in args.bench_imgsz:
            report["bench"].append(bench_video(YOLO(str(ROOT / args.weights)), ROOT / v, sz, args.bench_frames))

    (out / "metrics.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    write_markdown(report, out / "metrics.md")
    print(f"\nTersimpan: {out / 'metrics.md'}", flush=True)


if __name__ == "__main__":
    main()
