"""Simulator server vision: kirim heartbeat + detection palsu ke MQTT (tanpa kamera/YOLO).

Dipakai untuk menguji ESP32 (mode LIVE) dan dashboard sebelum pipeline vision siap.

Contoh (dari root repo):
    .venv\\Scripts\\python vision/sim_publisher.py --node gate1 --scenario compliant
    .venv\\Scripts\\python vision/sim_publisher.py --node gate1 --scenario demo
    .venv\\Scripts\\python vision/sim_publisher.py --node zoneA --scenario zone-escalation
"""

import argparse
import time

import iris_mqtt

OK = {"helmet": True, "vest": True}
NO_VEST = {"helmet": True, "vest": False}
NO_HELMET = {"helmet": False, "vest": True}

# Tiap scenario: daftar (durasi detik, daftar orang). Daftar kosong = ROI kosong.
SCENARIOS = {
    "empty": [(10, [])],
    "compliant": [(10, [OK])],                                   # T1
    "missing-vest": [(10, [NO_VEST])],                           # T2
    "two-one-violator": [(10, [OK, NO_HELMET])],                 # T4
    "violator-enters": [(6, [OK]), (6, [OK, NO_VEST])],          # T5
    "zone-escalation": [(3, [OK]), (12, [NO_HELMET]), (4, [OK])],  # T6 (violation_s dihitung di sini)
    "demo": [(4, []), (6, [OK]), (5, []), (6, [NO_VEST]), (6, [OK, NO_HELMET]), (4, [])],
}


def run(node: str, steps: list, rate_hz: float, stop_heartbeat: bool) -> None:
    client = iris_mqtt.connect("sim")
    det_topic = iris_mqtt.topic(node, "detection")
    print(f"terhubung {iris_mqtt.HOST}:{iris_mqtt.PORT}, publish ke {det_topic}")
    violation_since: dict[int, float] = {}
    last_hb = 0.0
    for duration, people in steps:
        persons = [{"id": i + 1, **p} for i, p in enumerate(people)]
        print(f"-> {duration}s: {persons or 'ROI kosong'}")
        end = time.time() + duration
        while time.time() < end:
            now = time.time()
            for p in persons:  # durasi pelanggaran per orang (meniru timer berbasis tracking ID)
                if p["helmet"] and p["vest"]:
                    violation_since.pop(p["id"], None)
                    p["violation_s"] = 0.0
                else:
                    p["violation_s"] = round(now - violation_since.setdefault(p["id"], now), 1)
            iris_mqtt.publish_json(client, det_topic, iris_mqtt.detection_payload(persons))
            if now - last_hb >= 1:
                iris_mqtt.publish_json(client, iris_mqtt.HEARTBEAT_TOPIC, {"fps": rate_hz, "source": "sim"})
                last_hb = now
            time.sleep(1 / rate_hz)
    if stop_heartbeat:
        print("selesai; heartbeat & detection DIHENTIKAN (uji fail-safe T3)")
    client.loop_stop()
    client.disconnect()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--node", default="gate1")
    ap.add_argument("--scenario", choices=SCENARIOS, default="demo")
    ap.add_argument("--rate", type=float, default=2.0, help="detection per detik")
    ap.add_argument("--loop", action="store_true", help="ulangi scenario terus")
    args = ap.parse_args()
    while True:
        run(args.node, SCENARIOS[args.scenario], args.rate, stop_heartbeat=not args.loop)
        if not args.loop:
            break


if __name__ == "__main__":
    main()
