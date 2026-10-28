# E2E MQTT — gate (2026-10-29 04:46)

Broker `broker.hivemq.com:8883`, node `gate1`, ESP32 di Wokwi mode LIVE.
Latency = waktu dari publish detection sampai status ESP32 diterima kembali (lewat broker dua arah).

| ID | Test Case | Input/Condition | Expected | Actual | Latency (s) | Status |
|---|---|---|---|---|---|---|
| E2-0 | ROI kosong | detection person_count=0 + heartbeat | IDLE, palang tertutup | state=IDLE gate=closed missing=[] persons=0 | 19.43 | Lulus |
| T1 | Satu orang APD lengkap | 1 orang helmet=true vest=true | GRANTED, palang terbuka | state=GRANTED gate=open missing=[] persons=1 | 1.0 | Lulus |
| T2 | Rompi tidak dipakai | 1 orang vest=false | DENIED, missing=[vest], palang tertutup | state=DENIED gate=closed missing=['vest'] persons=1 | 0.91 | Lulus |
| T4 | Dua orang, satu tidak patuh | orang 1 lengkap, orang 2 helmet=false | DENIED, palang tetap tertutup | state=DENIED gate=closed missing=['helmet'] persons=2 | 1.15 | Lulus |
| T5a | Gerbang terbuka untuk yang patuh | 1 orang lengkap | GRANTED | state=GRANTED gate=open missing=[] persons=1 | 1.39 | Lulus |
| T5 | Pelanggar masuk ROI saat palang terbuka | orang 2 tanpa rompi masuk | DENIED, palang menutup + alarm | state=DENIED gate=closed missing=['vest'] persons=2 | 1.01 | Lulus |
| T3 | Server vision mati | heartbeat & detection dihentikan | FAULT, gerbang terkunci | state=FAULT gate=closed missing=['vest'] persons=2 | 9.62 | Lulus |
| T3b | Server vision pulih | heartbeat & detection kembali (ROI kosong) | keluar dari FAULT ke IDLE | state=IDLE gate=closed missing=[] persons=0 | 1.31 | Lulus |
| OV | Override reset dari dashboard | publish override {"cmd":"reset"} saat DENIED | Buzzer dibungkam, palang tetap tertutup | log serial: 'reset (mqtt) -> alarm acknowledged' | None | Lulus |

Event yang diterima dashboard:

- `{"ts": 0, "node": "gate1", "type": "recovered", "level": 0, "missing": [], "person_count": 0, "duration_s": 0.0}`
- `{"ts": 0, "node": "gate1", "type": "granted", "level": 0, "missing": [], "person_count": 1, "duration_s": 0.0}`
- `{"ts": 0, "node": "gate1", "type": "denied", "level": 2, "missing": ["vest"], "person_count": 1, "duration_s": 0.0}`
- `{"ts": 1793220403, "node": "gate1", "type": "granted", "level": 0, "missing": [], "person_count": 1, "duration_s": 0.0}`
- `{"ts": 1793220404, "node": "gate1", "type": "denied", "level": 2, "missing": ["vest"], "person_count": 2, "duration_s": 2.5}`
- `{"ts": 1793220410, "node": "gate1", "type": "fault", "level": 3, "missing": ["vest"], "person_count": 2, "duration_s": 6.2}`
- `{"ts": 1793220411, "node": "gate1", "type": "recovered", "level": 0, "missing": [], "person_count": 0, "duration_s": 0.0}`

Log serial: `docs/assets/irisan2/e2e-gate-serial.log`
