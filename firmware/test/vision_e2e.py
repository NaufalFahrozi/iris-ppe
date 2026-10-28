"""Uji end-to-end lengkap: video -> vision/run_vision.py -> broker MQTT -> ESP32 Wokwi (mode LIVE gate1).

Pemakaian (dari root repo): .venv\\Scripts\\python firmware/test/vision_e2e.py video1.mp4 [video2.mp4 ...]
Log serial ESP32 dan output vision disimpan ke docs/assets/irisan3/.
"""

import subprocess
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

from run_tests import FW, ROOT, WOKWI, make_diagram

load_dotenv(ROOT / ".env")  # WOKWI_CLI_TOKEN untuk wokwi-cli

OUT = ROOT / "docs" / "assets" / "irisan3"
PY = sys.executable


def main() -> None:
    videos = sys.argv[1:]
    OUT.mkdir(parents=True, exist_ok=True)
    serial_log = OUT / "vision-e2e-serial.log"
    serial_log.unlink(missing_ok=True)
    diagram = make_diagram({"sw_role": "", "sw_source": ""})  # GATE + LIVE
    sim = subprocess.Popen([WOKWI, str(FW), "--diagram-file", str(diagram), "--timeout", "600000",
                            "--serial-log-file", str(serial_log), "-q"], cwd=FW / "test",
                           stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    try:
        deadline = time.time() + 120
        while time.time() < deadline:
            if serial_log.exists() and "[MQTT] connected" in serial_log.read_text(errors="replace"):
                break
            if sim.poll() is not None:
                sys.exit(f"wokwi-cli berhenti (exit {sim.returncode})")
            time.sleep(1)
        else:
            sys.exit("ESP32 tidak tersambung ke broker dalam 120 s")
        print("ESP32 tersambung; mulai vision", flush=True)

        with open(OUT / "vision-e2e-vision.log", "w", encoding="utf-8") as vlog:
            for v in videos:
                vlog.write(f"===== {v}\n")
                vlog.flush()
                subprocess.run([PY, str(ROOT / "vision" / "run_vision.py"), "--source", v, "--node", "gate1"],
                               cwd=ROOT, stdout=vlog, stderr=subprocess.STDOUT)
        print("vision selesai; tunggu fail-safe", flush=True)
        time.sleep(25)
    finally:
        sim.terminate()
        sim.wait(timeout=20)
        diagram.unlink(missing_ok=True)

    lines = serial_log.read_text(errors="replace").splitlines()
    for line in lines:
        if line.startswith(("[STATE]", "[EVENT]", "[MQTT] rx detection", "[MQTT] heartbeat")):
            print(line)


if __name__ == "__main__":
    main()
