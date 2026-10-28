"""Fine-tune YOLO26 pada subset SH17-IRIS.

Contoh (dari root repo):
    # ukur waktu 1 epoch + VRAM
    .venv\\Scripts\\python training/train.py --model yolo26m.pt --epochs 1 --name probe-yolo26m
    # training penuh dengan batas waktu (jam) dan early stopping
    .venv\\Scripts\\python training/train.py --model yolo26m.pt --epochs 100 --time 20 --patience 20 --name sh17-yolo26m
"""

import argparse

from ultralytics import YOLO


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="yolo26m.pt", help="bobot pretrained COCO")
    ap.add_argument("--data", default="datasets/sh17-iris/data.yaml")
    ap.add_argument("--epochs", type=int, default=100)
    ap.add_argument("--time", type=float, default=None, help="batas waktu training (jam), menimpa epochs")
    ap.add_argument("--patience", type=int, default=20)
    ap.add_argument("--imgsz", type=int, default=640)
    ap.add_argument("--batch", type=float, default=-1, help="-1 = autobatch, 0.x = fraksi VRAM")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--name", default="sh17-yolo26m")
    args = ap.parse_args()

    model = YOLO(args.model)
    train_kwargs = dict(
        data=args.data,
        epochs=args.epochs,
        patience=args.patience,
        imgsz=args.imgsz,
        batch=int(args.batch) if args.batch.is_integer() else args.batch,
        workers=args.workers,
        project="runs/train",
        name=args.name,
        exist_ok=True,
        plots=True,
    )
    if args.time:
        train_kwargs["time"] = args.time
    model.train(**train_kwargs)


if __name__ == "__main__":
    main()
