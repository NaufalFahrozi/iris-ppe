"""Jalankan semua scenario Wokwi untuk firmware IRIS dan simpan log sebagai bukti.

Pemakaian (dari root repo, setelah `pio run` di folder firmware):
    .venv\\Scripts\\python firmware/test/run_tests.py            # semua
    .venv\\Scripts\\python firmware/test/run_tests.py gate       # satu scenario

Butuh WOKWI_CLI_TOKEN di .env. Log serial disimpan ke docs/assets/irisan1/.
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
FW = ROOT / "firmware"
TEST = FW / "test"
OUT = ROOT / "docs" / "assets" / "irisan1"
WOKWI = shutil.which("wokwi-cli") or str(Path.home() / ".wokwi" / "bin" / "wokwi-cli.exe")

# scenario -> posisi slide switch (value "" = kiri, "1" = kanan)
SCENARIOS = {
    "gate": {"sw_role": "", "sw_source": "1"},
    "zone": {"sw_role": "1", "sw_source": "1"},
    "failsafe": {"sw_role": "", "sw_source": ""},
}


def make_diagram(switches: dict) -> Path:
    """Salin diagram.json dengan posisi slide switch untuk scenario ini."""
    diagram = json.loads((FW / "diagram.json").read_text(encoding="utf-8"))
    for part in diagram["parts"]:
        if part["id"] in switches:
            part["attrs"]["value"] = switches[part["id"]]
    path = TEST / ".diagram.generated.json"
    path.write_text(json.dumps(diagram, indent=2), encoding="utf-8")
    return path


def run(name: str) -> bool:
    diagram = make_diagram(SCENARIOS[name])
    log = OUT / f"{name}-serial.log"
    cmd = [WOKWI, str(FW), "--diagram-file", str(diagram), "--scenario", str(TEST / f"{name}.test.yaml"),
           "--timeout", "60000", "--serial-log-file", str(log)]
    print(f"\n=== {name} ===", flush=True)
    result = subprocess.run(cmd, cwd=TEST)
    ok = result.returncode == 0
    print(f"=== {name}: {'PASS' if ok else 'FAIL'} (exit {result.returncode}) ===", flush=True)
    return ok


def main() -> None:
    load_dotenv(ROOT / ".env")
    if not os.getenv("WOKWI_CLI_TOKEN"):
        sys.exit("WOKWI_CLI_TOKEN belum diisi di .env")
    OUT.mkdir(parents=True, exist_ok=True)
    names = sys.argv[1:] or list(SCENARIOS)
    results = {n: run(n) for n in names}
    (TEST / ".diagram.generated.json").unlink(missing_ok=True)
    print("\nRINGKASAN:", ", ".join(f"{n}={'PASS' if ok else 'FAIL'}" for n, ok in results.items()))
    sys.exit(0 if all(results.values()) else 1)


if __name__ == "__main__":
    main()
