"""Server vision IRIS: kamera/video -> YOLO26 + tracking -> aturan kepatuhan -> MQTT (detection + heartbeat).

Contoh (dari root repo):
    # gerbang, webcam 0, ROI setengah bawah frame, tampilkan jendela
    .venv\\Scripts\\python vision/run_vision.py --source 0 --node gate1 --roi "0,0.4;1,0.4;1,1;0,1" --show
    # zona, file video
    .venv\\Scripts\\python vision/run_vision.py --source rekaman.mp4 --node zoneA --show

Privasi: tidak ada face recognition dan tidak ada video yang disimpan; hanya angka/status yang dikirim.
"""

import argparse
import time
from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO

import iris_mqtt
from compliance import HELMET, PERSON, VEST, Box, ComplianceTracker, assign_ppe, in_roi

DEFAULT_WEIGHTS = Path(__file__).resolve().parents[1] / "models" / "iris-best.pt"


def parse_roi(text: str | None):
    if not text:
        return None
    return [tuple(map(float, p.split(","))) for p in text.split(";")]


def draw(frame, persons, states, inside, roi, fps):
    h, w = frame.shape[:2]
    if roi:
        pts = [(int(x * w), int(y * h)) for x, y in roi]
        cv2.polylines(frame, [np.array(pts, dtype=np.int32)], True, (255, 200, 0), 2)
    for (tid, box), st, ok_roi in zip(persons, states, inside):
        if not ok_roi:
            color = (150, 150, 150)
        else:
            color = (0, 200, 0) if st["helmet"] and st["vest"] else (0, 0, 230)
        cv2.rectangle(frame, (int(box.x1), int(box.y1)), (int(box.x2), int(box.y2)), color, 2)
        label = f"#{tid} H:{'Y' if st['helmet'] else 'N'} V:{'Y' if st['vest'] else 'N'}"
        if st["violation_s"]:
            label += f" {st['violation_s']:.0f}s"
        cv2.putText(frame, label, (int(box.x1), int(box.y1) - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    cv2.putText(frame, f"IRIS {fps:.1f} FPS", (10, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    return frame


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--weights", type=Path, default=DEFAULT_WEIGHTS)
    ap.add_argument("--source", default="0", help="0 = webcam, path video/folder gambar, atau URL stream")
    ap.add_argument("--node", default="gate1", help="gate1 / zoneA (harus sama dengan firmware)")
    ap.add_argument("--roi", default=None, help='poligon ROI ternormalisasi, mis. "0,0.4;1,0.4;1,1;0,1" (gerbang)')
    ap.add_argument("--conf", type=float, default=0.4)
    ap.add_argument("--imgsz", type=int, default=640)
    ap.add_argument("--rate", type=float, default=5.0, help="maks. publish detection per detik")
    ap.add_argument("--show", action="store_true", help="tampilkan jendela anotasi (q = keluar)")
    ap.add_argument("--no-mqtt", action="store_true", help="uji lokal tanpa broker")
    args = ap.parse_args()

    model = YOLO(args.weights)
    roi = parse_roi(args.roi)
    client = None if args.no_mqtt else iris_mqtt.connect(f"vision-{args.node}")
    det_topic = iris_mqtt.topic(args.node, "detection")
    tracker = ComplianceTracker()
    source = int(args.source) if args.source.isdigit() else args.source
    print(f"[VISION] weights={args.weights.name} source={args.source} node={args.node} roi={roi} "
          f"mqtt={'off' if client is None else iris_mqtt.HOST}", flush=True)

    fps, last_pub, last_hb, last_log, frames = 0.0, 0.0, 0.0, time.time(), 0
    t_prev = time.time()
    for res in model.track(source, stream=True, persist=True, tracker="bytetrack.yaml", conf=args.conf,
                           imgsz=args.imgsz, verbose=False):
        now = time.time()
        fps = 0.9 * fps + 0.1 * (1 / max(now - t_prev, 1e-6)) if fps else 1 / max(now - t_prev, 1e-6)
        t_prev = now
        frames += 1
        h, w = res.orig_shape

        boxes = res.boxes
        cls = boxes.cls.int().tolist()
        xyxy = boxes.xyxy.tolist()
        confs = boxes.conf.tolist()
        ids = boxes.id.int().tolist() if boxes.id is not None else [None] * len(cls)

        persons = [(tid if tid is not None else -(i + 1), Box(*b, c))
                   for i, (k, b, c, tid) in enumerate(zip(cls, xyxy, confs, ids)) if k == PERSON]
        helmets = [Box(*b, c) for k, b, c in zip(cls, xyxy, confs) if k == HELMET]
        vests = [Box(*b, c) for k, b, c in zip(cls, xyxy, confs) if k == VEST]

        ppe = assign_ppe([p for _, p in persons], helmets, vests)
        inside = [in_roi(p, roi, w, h) for _, p in persons]
        states = [tracker.update(tid, a["helmet"], a["vest"], now) for (tid, _), a in zip(persons, ppe)]
        tracker.prune(now)

        people = [{"id": tid, **st} for (tid, _), st, ok in zip(persons, states, inside) if ok]
        payload = iris_mqtt.detection_payload(people)

        if client and now - last_pub >= 1 / args.rate:
            iris_mqtt.publish_json(client, det_topic, payload)
            last_pub = now
        if client and now - last_hb >= 1:
            iris_mqtt.publish_json(client, iris_mqtt.HEARTBEAT_TOPIC, {"fps": round(fps, 1), "source": "vision"})
            last_hb = now
        if now - last_log >= 2:
            print(f"[VISION] fps={fps:.1f} persons_roi={payload['person_count']} violators={payload['violators']}",
                  flush=True)
            last_log = now

        if args.show:
            cv2.imshow("IRIS vision", draw(res.orig_img.copy(), persons, states, inside, roi, fps))
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    if client:
        client.loop_stop()
        client.disconnect()
    cv2.destroyAllWindows()
    print(f"[VISION] selesai, {frames} frame", flush=True)


if __name__ == "__main__":
    main()
