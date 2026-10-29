"""Uji end-to-end lengkap: video -> vision/run_vision.py -> broker MQTT -> ESP32 Wokwi (mode LIVE).

Pemakaian (dari root repo):
    .venv\\Scripts\\python firmware/test/vision_e2e.py gate video1.mp4 [video2.mp4 ...]
    .venv\\Scripts\\python firmware/test/vision_e2e.py zone video.mp4 -- --imgsz 1280
Argumen setelah "--" diteruskan ke run_vision.py. Log disimpan ke docs/assets/irisan3/vision-e2e-<role>-*.log.
"""

import subprocess
import sys
import time

from dotenv import load_dotenv

from run_tests import FW, ROOT, WOKWI, make_diagram

load_dotenv(ROOT / ".env")  # WOKWI_CLI_TOKEN untuk wokwi-cli
OUT = ROOT / "docs" / "assets" / "irisan3"
PY = sys.executable


def main() -> None:
    args = sys.argv[1:]
    extra = args[args.index("--") + 1:] if "--" in args else []
    args = args[:args.index("--")] if "--" in args else args
    role, videos = args[0], args[1:]
    node = "gate1" if role == "gate" else "zoneA"
    OUT.mkdir(parents=True, exist_ok=True)
    serial_log = OUT / f"vision-e2e-{role}-serial.log"
    serial_log.unlink(missing_ok=True)
    diagram = make_diagram({"sw_role": "" if role == "gate" else "1", "sw_source": ""})  # sumber LIVE
    sim = subprocess.Popen([WOKWI, str(FW), "--diagram-file", str(diagram), "--timeout", "900000",
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
        print(f"ESP32 {node} tersambung; mulai vision", flush=True)

        with open(OUT / f"vision-e2e-{role}-vision.log", "w", encoding="utf-8") as vlog:
            for v in videos:
                vlog.write(f"===== {v} {' '.join(extra)}\n")
                vlog.flush()
                subprocess.run([PY, str(ROOT / "vision" / "run_vision.py"), "--source", v, "--node", node, *extra],
                               cwd=ROOT, stdout=vlog, stderr=subprocess.STDOUT)
        print("vision selesai; tunggu fail-safe", flush=True)
        start = len(serial_log.read_text(errors="replace"))
        deadline = time.time() + 60  # FAILSAFE 8 s waktu simulasi; Wokwi lebih lambat dari waktu nyata
        while time.time() < deadline and "-> FAULT" not in serial_log.read_text(errors="replace")[start:]:
            time.sleep(2)
    finally:
        sim.terminate()
        sim.wait(timeout=20)
        diagram.unlink(missing_ok=True)

    for line in serial_log.read_text(errors="replace").splitlines():
        if line.startswith(("[STATE]", "[EVENT]")):
            print(line)


if __name__ == "__main__":
    main()
