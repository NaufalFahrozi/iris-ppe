"""Uji end-to-end lewat MQTT: Python (pengganti server vision) <-> broker HiveMQ <-> ESP32 di Wokwi (mode LIVE).

Pemakaian (dari root repo, setelah `pio run` di folder firmware):
    .venv\\Scripts\\python firmware/test/mqtt_e2e.py gate
    .venv\\Scripts\\python firmware/test/mqtt_e2e.py zone

Hasil (tabel + log serial) disimpan ke docs/assets/irisan2/.
"""

import json
import queue
import subprocess
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "vision"))
import iris_mqtt  # noqa: E402
from run_tests import FW, ROOT, WOKWI, make_diagram  # noqa: E402

OUT = ROOT / "docs" / "assets" / "irisan2"
OK = {"helmet": True, "vest": True}
NO_VEST = {"helmet": True, "vest": False}
NO_HELMET = {"helmet": False, "vest": True}


class FakeVisionServer:
    """Kirim heartbeat (1 Hz) dan detection (2 Hz) seperti server vision; bisa dihentikan untuk uji fail-safe."""

    def __init__(self, client, node):
        self.client, self.node = client, node
        self.people: list[dict] = []
        self.running = True
        self.violation_since: dict[int, float] = {}
        threading.Thread(target=self._loop, daemon=True).start()

    def set(self, people):
        self.people = [{"id": i + 1, **p} for i, p in enumerate(people)]
        self.publish()

    def publish(self):
        now = time.time()
        for p in self.people:
            if p["helmet"] and p["vest"]:
                self.violation_since.pop(p["id"], None)
                p["violation_s"] = 0.0
            else:
                p["violation_s"] = round(now - self.violation_since.setdefault(p["id"], now), 1)
        iris_mqtt.publish_json(self.client, iris_mqtt.topic(self.node, "detection"),
                               iris_mqtt.detection_payload(self.people))

    def _loop(self):
        tick = 0
        while True:
            if self.running:
                self.publish()
                if tick % 2 == 0:
                    iris_mqtt.publish_json(self.client, iris_mqtt.HEARTBEAT_TOPIC, {"fps": 2.0, "source": "e2e"})
            tick += 1
            time.sleep(0.5)


class Harness:
    def __init__(self, node):
        self.node = node
        self.status: "queue.Queue[dict]" = queue.Queue()
        self.events: list[dict] = []
        self.results: list[dict] = []
        self.serial_checks: list[tuple] = []  # (id, nama, kondisi, teks yang harus ada di log, expected)
        self.client = iris_mqtt.connect("e2e")
        self.client.on_message = self._on_message
        self.client.subscribe(iris_mqtt.topic(node, "status"))
        self.client.subscribe(iris_mqtt.topic(node, "event"))

    def _on_message(self, client, userdata, msg):
        if msg.retain:  # abaikan status lama yang tersimpan di broker
            return
        data = json.loads(msg.payload)
        data["_rx"] = time.time()
        if msg.topic.endswith("/status"):
            self.status.put(data)
        else:
            self.events.append(data)

    def wait_status(self, pred, timeout):
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                s = self.status.get(timeout=max(0.1, deadline - time.time()))
            except queue.Empty:
                break
            if pred(s):
                return s
        return None

    def drain(self):
        while not self.status.empty():
            self.status.get_nowait()

    def check(self, test_id, name, condition, action, pred, expected, timeout=20):
        self.drain()
        t0 = time.time()
        action()
        s = self.wait_status(pred, timeout)
        ok = s is not None
        actual = (f"state={s['state']} gate={s['gate']} missing={s['missing']} persons={s['person_count']}"
                  if ok else f"timeout {timeout}s tanpa status yang cocok")
        latency = round(s["_rx"] - t0, 2) if ok else None
        self.results.append({"id": test_id, "name": name, "condition": condition, "expected": expected,
                             "actual": actual, "latency_s": latency, "status": "Lulus" if ok else "Gagal"})
        print(f"[{'PASS' if ok else 'FAIL'}] {test_id} {name}: {actual} (latency {latency}s)", flush=True)
        return ok


def gate_tests(h: Harness, vision: FakeVisionServer):
    h.check("E2-0", "ROI kosong", "detection person_count=0 + heartbeat", lambda: vision.set([]),
            lambda s: s["state"] == "IDLE", "IDLE, palang tertutup", timeout=90)
    h.check("T1", "Satu orang APD lengkap", "1 orang helmet=true vest=true", lambda: vision.set([OK]),
            lambda s: s["state"] == "GRANTED" and s["gate"] == "open", "GRANTED, palang terbuka")
    h.check("T2", "Rompi tidak dipakai", "1 orang vest=false", lambda: vision.set([NO_VEST]),
            lambda s: s["state"] == "DENIED" and s["missing"] == ["vest"], "DENIED, missing=[vest], palang tertutup")
    h.check("T4", "Dua orang, satu tidak patuh", "orang 1 lengkap, orang 2 helmet=false",
            lambda: vision.set([OK, NO_HELMET]),
            lambda s: s["state"] == "DENIED" and s["person_count"] == 2, "DENIED, palang tetap tertutup")
    h.check("T5a", "Gerbang terbuka untuk yang patuh", "1 orang lengkap", lambda: vision.set([OK]),
            lambda s: s["state"] == "GRANTED", "GRANTED")
    h.check("T5", "Pelanggar masuk ROI saat palang terbuka", "orang 2 tanpa rompi masuk",
            lambda: vision.set([OK, NO_VEST]),
            lambda s: s["state"] == "DENIED" and s["gate"] == "closed", "DENIED, palang menutup + alarm", timeout=10)
    # Override supervisor dari dashboard; diverifikasi dari log serial setelah simulasi selesai
    iris_mqtt.publish_json(h.client, iris_mqtt.topic(h.node, "override"), {"cmd": "reset"}, qos=1)
    h.serial_checks.append(("OV", "Override reset dari dashboard", "publish override {\"cmd\":\"reset\"} saat DENIED",
                            "reset (mqtt) -> alarm acknowledged", "Buzzer dibungkam, palang tetap tertutup"))
    time.sleep(3)
    h.check("T3", "Server vision mati", "heartbeat & detection dihentikan",
            lambda: setattr(vision, "running", False),
            lambda s: s["state"] == "FAULT" and s["gate"] == "closed", "FAULT, gerbang terkunci", timeout=30)
    h.check("T3b", "Server vision pulih", "heartbeat & detection kembali (ROI kosong)",
            lambda: (setattr(vision, "running", True), vision.set([])),
            lambda s: s["state"] == "IDLE", "keluar dari FAULT ke IDLE")


def zone_tests(h: Harness, vision: FakeVisionServer):
    h.check("E2-0", "Zona aman", "1 orang lengkap + heartbeat", lambda: vision.set([OK]),
            lambda s: s["state"] == "NORMAL", "NORMAL", timeout=90)
    h.check("T6a", "Helm dilepas: peringatan", "helmet=false, violation_s naik dari server",
            lambda: vision.set([NO_HELMET]), lambda s: s["state"] == "WARNING", "WARNING setelah >= 3 s", timeout=30)
    h.check("T6b", "Helm dilepas lama: alarm", "violation_s terus naik", lambda: None,
            lambda s: s["state"] == "ALARM", "ALARM setelah >= 8 s + event alarm", timeout=30)
    h.check("T6c", "Patuh kembali", "helmet=true", lambda: vision.set([OK]),
            lambda s: s["state"] == "NORMAL", "NORMAL (reset otomatis) + event cleared")


def write_report(role, h: Harness, serial_log: Path):
    OUT.mkdir(parents=True, exist_ok=True)
    lines = [f"# E2E MQTT — {role} ({time.strftime('%Y-%m-%d %H:%M')})", "",
             f"Broker `{iris_mqtt.HOST}:{iris_mqtt.PORT}`, node `{h.node}`, ESP32 di Wokwi mode LIVE.",
             "Latency = waktu dari publish detection sampai status ESP32 diterima kembali (lewat broker dua arah).", "",
             "| ID | Test Case | Input/Condition | Expected | Actual | Latency (s) | Status |", "|---|---|---|---|---|---|---|"]
    for r in h.results:
        lines.append(f"| {r['id']} | {r['name']} | {r['condition']} | {r['expected']} | {r['actual']} | "
                     f"{r['latency_s']} | {r['status']} |")
    lines += ["", "Event yang diterima dashboard:", ""]
    lines += [f"- `{json.dumps({k: v for k, v in e.items() if k != '_rx'})}`" for e in h.events]
    lines += ["", f"Log serial: `{serial_log.relative_to(ROOT).as_posix()}`"]
    (OUT / f"e2e-{role}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    role = sys.argv[1] if len(sys.argv) > 1 else "gate"
    node = "gate1" if role == "gate" else "zoneA"
    OUT.mkdir(parents=True, exist_ok=True)
    diagram = make_diagram({"sw_role": "" if role == "gate" else "1", "sw_source": ""})
    serial_log = OUT / f"e2e-{role}-serial.log"

    h = Harness(node)
    vision = FakeVisionServer(h.client, node)
    cli_log = open(OUT / f"e2e-{role}-wokwi-cli.log", "w", encoding="utf-8")
    sim = subprocess.Popen([WOKWI, str(FW), "--diagram-file", str(diagram), "--timeout", "600000",
                            "--serial-log-file", str(serial_log), "-q"], cwd=FW / "test",
                           stdout=cli_log, stderr=subprocess.STDOUT)
    time.sleep(10)
    if sim.poll() is not None:
        cli_log.close()
        sys.exit(f"wokwi-cli berhenti (exit {sim.returncode}); lihat docs/assets/irisan2/e2e-{role}-wokwi-cli.log")
    try:
        (gate_tests if role == "gate" else zone_tests)(h, vision)
        time.sleep(1)
    finally:
        sim.terminate()
        sim.wait(timeout=20)
        cli_log.close()
        diagram.unlink(missing_ok=True)
    log_text = serial_log.read_text(encoding="utf-8", errors="replace") if serial_log.exists() else ""
    for test_id, name, condition, needle, expected in h.serial_checks:
        ok = needle in log_text
        h.results.append({"id": test_id, "name": name, "condition": condition, "expected": expected,
                          "actual": f"log serial: '{needle}'" if ok else "teks tidak ditemukan di log serial",
                          "latency_s": None, "status": "Lulus" if ok else "Gagal"})
        print(f"[{'PASS' if ok else 'FAIL'}] {test_id} {name}", flush=True)
    write_report(role, h, serial_log)
    passed = sum(r["status"] == "Lulus" for r in h.results)
    print(f"\nRINGKASAN {role}: {passed}/{len(h.results)} lulus -> docs/assets/irisan2/e2e-{role}.md")
    sys.exit(0 if passed == len(h.results) else 1)


if __name__ == "__main__":
    main()
