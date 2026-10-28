# E2E MQTT — zone (2026-10-29 03:48)

Broker `broker.hivemq.com:8883`, node `zoneA`, ESP32 di Wokwi mode LIVE.
Latency = waktu dari publish detection sampai status ESP32 diterima kembali (lewat broker dua arah).

| ID | Test Case | Input/Condition | Expected | Actual | Latency (s) | Status |
|---|---|---|---|---|---|---|
| E2-0 | Zona aman | 1 orang lengkap + heartbeat | NORMAL | state=NORMAL gate=closed missing=[] persons=1 | 30.1 | Lulus |
| T6a | Helm dilepas: peringatan | helmet=false, violation_s naik dari server | WARNING setelah >= 3 s | state=WARNING gate=closed missing=['helmet'] persons=1 | 4.39 | Lulus |
| T6b | Helm dilepas lama: alarm | violation_s terus naik | ALARM setelah >= 8 s + event alarm | state=ALARM gate=closed missing=['helmet'] persons=1 | 5.13 | Lulus |
| T6c | Patuh kembali | helmet=true | NORMAL (reset otomatis) + event cleared | state=NORMAL gate=closed missing=[] persons=1 | 1.23 | Lulus |

Event yang diterima dashboard:

- `{"ts": 1793216892, "node": "zoneA", "type": "recovered", "level": 0, "missing": [], "person_count": 1, "duration_s": 0.0}`
- `{"ts": 1793216893, "node": "zoneA", "type": "warning", "level": 1, "missing": ["helmet"], "person_count": 1, "duration_s": 3.4}`
- `{"ts": 1793216895, "node": "zoneA", "type": "alarm", "level": 2, "missing": ["helmet"], "person_count": 1, "duration_s": 8.4}`
- `{"ts": 1793216895, "node": "zoneA", "type": "cleared", "level": 0, "missing": [], "person_count": 1, "duration_s": 0.0}`

Log serial: `docs/assets/irisan2/e2e-zone-serial.log`
