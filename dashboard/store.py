"""Penampung data dashboard: subscribe MQTT IRIS, simpan di memori, dan catat event ke CSV.

Topic (docs/design.md bagian 5): <prefix>/+/status, <prefix>/+/event, <prefix>/+/detection, <prefix>/server/heartbeat
"""

import csv
import json
import sys
import threading
import time
from collections import deque
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "vision"))
import iris_mqtt  # noqa: E402

DATA_DIR = Path(__file__).resolve().parent / "data"
EVENT_CSV = DATA_DIR / "events.csv"
HISTORY_S = 30 * 60  # data yang disimpan di memori


class Store:
    def __init__(self):
        self.lock = threading.Lock()
        self.started = time.time()
        self.nodes: dict[str, dict] = {}         # node -> status terakhir (+ "_rx")
        self.heartbeat: dict | None = None       # heartbeat server terakhir (+ "_rx")
        self.detections: deque = deque()         # (t, node, person_count, compliant_count)
        self.events: deque = deque()             # event dict (+ "_rx")
        DATA_DIR.mkdir(exist_ok=True)
        self.client = iris_mqtt.connect("dashboard")
        self.client.on_message = self._on_message
        for leaf in ("status", "event", "detection"):
            self.client.subscribe(f"{iris_mqtt.PREFIX}/+/{leaf}")
        self.client.subscribe(iris_mqtt.HEARTBEAT_TOPIC)

    # ---- MQTT ----
    def _on_message(self, client, userdata, msg):
        try:
            data = json.loads(msg.payload)
        except json.JSONDecodeError:
            return
        now = time.time()
        parts = msg.topic.split("/")
        node, leaf = parts[-2], parts[-1]
        with self.lock:
            if leaf == "heartbeat":
                self.heartbeat = {**data, "_rx": now}
            elif leaf == "status":
                # status retained lama tetap ditampilkan, ditandai umurnya lewat "_rx" dari ts
                self.nodes[node] = {**data, "_rx": now if not msg.retain else now - 3600}
            elif leaf == "detection":
                persons = data.get("persons", [])
                compliant = sum(1 for p in persons if p.get("helmet") and p.get("vest"))
                self.detections.append((now, node, len(persons), compliant))
            elif leaf == "event" and not msg.retain:
                event = {**data, "node": data.get("node", node), "_rx": now}
                self.events.append(event)
                self._log_event(event)
            self._trim(now)

    def _trim(self, now):
        while self.detections and now - self.detections[0][0] > HISTORY_S:
            self.detections.popleft()
        while self.events and now - self.events[0]["_rx"] > HISTORY_S:
            self.events.popleft()

    def _log_event(self, e):
        new = not EVENT_CSV.exists()
        with EVENT_CSV.open("a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            if new:
                w.writerow(["time", "node", "type", "level", "missing", "person_count", "duration_s"])
            w.writerow([time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(e["_rx"])), e["node"], e.get("type"),
                        e.get("level"), "+".join(e.get("missing", [])), e.get("person_count"), e.get("duration_s")])

    # ---- Aksi ----
    def send_reset(self, node: str):
        iris_mqtt.publish_json(self.client, iris_mqtt.topic(node, "override"), {"cmd": "reset", "by": "dashboard"},
                               qos=1)

    # ---- Snapshot untuk UI ----
    def snapshot(self):
        with self.lock:
            return {
                "nodes": {k: dict(v) for k, v in self.nodes.items()},
                "heartbeat": dict(self.heartbeat) if self.heartbeat else None,
                "detections": list(self.detections),
                "events": list(self.events),
                "started": self.started,
                "connected": self.client.is_connected(),
            }
