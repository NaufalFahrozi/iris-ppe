"""Siapkan berkas untuk proyek di wokwi.com (link pengumpulan) dari firmware PlatformIO.

Hasil: firmware/wokwi-web/ berisi sketch.ino, config.h, ca_cert.h, diagram.json, libraries.txt.
Isi tiap berkas ditempel ke tab dengan nama yang sama di editor wokwi.com.

Pemakaian (dari root repo): .venv\\Scripts\\python firmware/export_wokwi_web.py
"""

import re
import shutil
from pathlib import Path

FW = Path(__file__).resolve().parent
OUT = FW / "wokwi-web"


def main() -> None:
    OUT.mkdir(exist_ok=True)
    shutil.copy(FW / "src" / "main.cpp", OUT / "sketch.ino")
    shutil.copy(FW / "src" / "config.h", OUT / "config.h")
    shutil.copy(FW / "src" / "ca_cert.h", OUT / "ca_cert.h")
    shutil.copy(FW / "diagram.json", OUT / "diagram.json")

    # lib_deps di platformio.ini -> nama library Arduino untuk wokwi.com
    ini = (FW / "platformio.ini").read_text(encoding="utf-8")
    names = {"ESP32Servo": "ESP32Servo", "Adafruit SSD1306": "Adafruit SSD1306",
             "Adafruit GFX Library": "Adafruit GFX Library", "PubSubClient": "PubSubClient",
             "ArduinoJson": "ArduinoJson"}
    libs = [lib for key, lib in names.items() if re.search(rf"/{re.escape(key)}@", ini)]
    (OUT / "libraries.txt").write_text("# Wokwi Library List\n" + "\n".join(libs) + "\n", encoding="utf-8")
    print(f"siap di {OUT}: " + ", ".join(sorted(p.name for p in OUT.iterdir())))


if __name__ == "__main__":
    main()
