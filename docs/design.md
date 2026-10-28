# Design — IRIS

Rancangan dasar (langkah 1). Penanggung jawab hardware/firmware: Christian; integrasi: Naufal.
Nilai yang ditandai *(tuning)* adalah nilai awal dan difinalkan saat pengujian.

## 1. Alur sistem

```mermaid
flowchart LR
    subgraph Input
        CAM[Kamera gerbang / zona]
        BTN[Push button<br/>reset supervisor + simulasi deteksi]
        SW[Slide switch<br/>peran & sumber data]
    end
    subgraph Server["Server vision (laptop RTX 4050)"]
        YOLO[YOLO26 + tracking<br/>+ aturan kepatuhan]
    end
    BROKER[(HiveMQ public broker<br/>broker.hivemq.com:8883 TLS)]
    subgraph Node["ESP32 node (Wokwi)"]
        LOGIC[State machine<br/>gerbang / zona]
    end
    subgraph Output
        SERVO[Servo palang]
        LED[LED hijau/kuning/merah]
        BUZ[Buzzer]
        OLED[OLED SSD1306]
        SER[Serial Monitor]
    end
    DASH[Dashboard Python<br/>paho-mqtt + Plotly]

    CAM --> YOLO -->|detection, heartbeat| BROKER --> LOGIC
    BTN --> LOGIC
    SW --> LOGIC
    LOGIC --> SERVO & LED & BUZ & OLED & SER
    LOGIC -->|status, event| BROKER --> DASH
    DASH -->|override| BROKER
```

Hasil deteksi YOLO diperlakukan sebagai **sensor virtual** yang masuk lewat MQTT. Wokwi tidak bisa menjalankan
kamera/YOLO, jadi pada mode uji (TEST) hasil deteksi disimulasikan dengan push button.

## 2. Komponen dan alasan pemilihan

| Komponen (part Wokwi) | Jumlah | Fungsi | Alasan teknis |
|---|---|---|---|
| ESP32 DevKit C v4 (`board-esp32-devkit-c-v4`) | 1 | Controller, logic, WiFi/MQTT | Wajib dari tugas; WiFi bawaan untuk MQTT; GPIO cukup untuk semua I/O |
| Servo SG90 (`wokwi-servo`) | 1 | Palang gerbang (0° tutup, 90° buka) | Aktuasi mekanis yang terlihat jelas di demo; dikendalikan PWM 50 Hz |
| LED hijau, kuning, merah (`wokwi-led`) + resistor 220 Ω | 3 + 3 | Status patuh / peringatan & gangguan / pelanggaran | Indikator murah, terbaca dari jauh; resistor membatasi arus ±(3,3−2)/220 ≈ 6 mA |
| Buzzer piezo (`wokwi-buzzer`) | 1 | Alarm audio | Peringatan yang tetap terdengar walau pekerja tidak melihat lampu; nada diatur PWM (LEDC) |
| OLED SSD1306 128×64 I2C (`board-ssd1306`) | 1 | Menampilkan status dan APD yang kurang | Informasi spesifik untuk pekerja ("HELM TIDAK TERDETEKSI"); I2C hanya butuh 2 pin |
| Push button (`wokwi-pushbutton`) | 4 | `RESET` supervisor; `PERSON`, `HELMET`, `VEST` untuk simulasi deteksi | Input fisik; satu-satunya input yang bisa diotomatisasi oleh scenario `wokwi-cli` (`set-control pressed`) |
| Slide switch (`wokwi-slide-switch`) | 2 | `ROLE` (GATE/ZONE), `SOURCE` (LIVE/TEST) | Pilihan mode yang terlihat di rangkaian; satu rangkaian bisa mendemokan kedua mode |
| Kamera (di luar Wokwi) | 1/titik | Sumber citra server vision | Komponen utama deteksi APD |

Catatan implementasi nyata (stage 3): tombol `PERSON/HELMET/VEST` hanya ada untuk mode uji; node lapangan cukup
punya `RESET`. Satu ESP32 per titik (gerbang/zona) dengan `ROLE` tetap. Servo diberi catu 5 V terpisah, dan buzzer
memakai modul atau transistor driver.

## 3. Pemetaan GPIO

Status: draft, sudah lulus uji wokwi-cli; menunggu review Christian dan verifikasi visual rangkaian.

| GPIO | Arah | Terhubung ke | Catatan |
|---|---|---|---|
| 18 | Output (PWM) | Servo PWM | LEDC 50 Hz via ESP32Servo |
| 19 | Output (PWM) | Buzzer (+) | `ledcWriteTone` |
| 25 | Output | LED hijau → 220 Ω → GND | |
| 26 | Output | LED kuning → 220 Ω → GND | |
| 27 | Output | LED merah → 220 Ω → GND | |
| 21 | I2C SDA | OLED SDA | Pin I2C default ESP32 |
| 22 | I2C SCL | OLED SCL | Pin I2C default ESP32 |
| 32 | Input, pull-up internal | Tombol `PERSON` → GND | Aktif LOW, toggle (mode TEST) |
| 33 | Input, pull-up internal | Tombol `HELMET` → GND | Aktif LOW, toggle (mode TEST) |
| 14 | Input, pull-up internal | Tombol `VEST` → GND | Aktif LOW, toggle (mode TEST) |
| 13 | Input, pull-up internal | Tombol `RESET` → GND | Aktif LOW; reset/ack alarm |
| 34 | Input only | Slide switch `ROLE` (kiri GND = GATE, kanan 3V3 = ZONE) | Tanpa pull-up, switch memberi level pasti |
| 35 | Input only | Slide switch `SOURCE` (kiri GND = LIVE, kanan 3V3 = TEST) | Tanpa pull-up, switch memberi level pasti |

Pin yang **dihindari**: 0, 2, 5, 12, 15 (strapping), 6–11 (flash), 1/3 (UART Serial Monitor).
Pin input-only 34/35 dipakai untuk slide switch karena tidak butuh pull-up dan tidak pernah dipakai sebagai output.

**Power & ground:** semua komponen berbagi GND ESP32. OLED dan slide switch dari 3V3. Servo V+ dari pin 5V
(di Wokwi; pada hardware nyata dari catu 5 V terpisah dengan ground bersama).

## 4. State machine

Evaluasi dilakukan setiap loop dari **snapshot deteksi** terakhir: `person_count`, daftar pelanggar, APD yang kurang,
dan umur snapshot. Pada `SOURCE=LIVE` snapshot berasal dari MQTT; pada `SOURCE=TEST` dari tombol.

### 4.1 Mode gerbang

```mermaid
stateDiagram-v2
    [*] --> FAULT
    FAULT --> IDLE: data/heartbeat kembali
    IDLE --> GRANTED: ada orang & semua patuh
    IDLE --> DENIED: ada pelanggar
    GRANTED --> DENIED: pelanggar masuk ROI (T5)
    GRANTED --> IDLE: ROI kosong / jendela buka habis
    DENIED --> GRANTED: semua patuh
    DENIED --> IDLE: ROI kosong
    IDLE --> FAULT: timeout
    GRANTED --> FAULT: timeout
    DENIED --> FAULT: timeout
```

| State | Palang | LED | Buzzer | OLED |
|---|---|---|---|---|
| `FAULT` | tertutup (terkunci) | kuning berkedip | — | "VISION OFFLINE" |
| `IDLE` | tertutup | — | — | "SIAP" |
| `GRANTED` | **terbuka** maks `OPEN_WINDOW_MS` | hijau | 1 bip pendek | "SILAKAN MASUK" |
| `DENIED` | tertutup | merah | bip berulang (bisa di-ack `RESET`) | APD yang kurang |

- Palang terbuka hanya jika **semua** orang di ROI patuh. Satu pelanggar → `DENIED`.
- Setelah `OPEN_WINDOW_MS` palang menutup (`IDLE`); jika antrean masih patuh, dibuka lagi pada evaluasi berikutnya.

### 4.2 Mode zona (monitoring)

```mermaid
stateDiagram-v2
    [*] --> FAULT
    FAULT --> NORMAL: data/heartbeat kembali
    NORMAL --> WARNING: durasi pelanggaran ≥ WARN_S
    WARNING --> ALARM: durasi ≥ ALARM_S
    WARNING --> NORMAL: patuh kembali
    ALARM --> NORMAL: patuh kembali (reset otomatis)
```

| State | LED | Buzzer | OLED | Event MQTT |
|---|---|---|---|---|
| `NORMAL` | hijau | — | "ZONA AMAN" (atau hitung mundur bila pelanggaran < `WARN_S`, diabaikan) | — |
| `WARNING` | kuning | — | APD yang kurang + durasi | `warning` |
| `ALARM` | merah | bip berulang (bisa di-ack `RESET`) | APD yang kurang + durasi | `alarm` |
| `FAULT` | kuning berkedip | — | "VISION OFFLINE" | `fault` |

Durasi pelanggaran: utamakan `violation_s` per orang dari server (berbasis tracking ID); jika tidak ada, ESP32
menghitung sendiri sejak pelanggar pertama terlihat (fallback durasi level frame).

### 4.3 Konstanta konfigurasi (`firmware/src/config.h`)

| Nama | Nilai awal | Arti |
|---|---|---|
| `FAILSAFE_TIMEOUT_MS` | 5000 *(tuning)* | Tanpa heartbeat/deteksi selama ini → `FAULT` |
| `OPEN_WINDOW_MS` | 5000 *(tuning)* | Lama palang terbuka per izin |
| `GATE_REARM_MS` | 2000 *(tuning)* | Jeda palang tertutup sebelum boleh dibuka lagi |
| `ZONE_WARN_S` | 3 *(tuning)* | Pelanggaran lebih singkat dari ini diabaikan |
| `ZONE_ALARM_S` | 8 *(tuning)* | Batas eskalasi ke alarm |
| `STATUS_PERIOD_MS` | 5000 | Publikasi status periodik |

## 5. MQTT (final irisan 2)

Broker `broker.hivemq.com:8883` (TLS). ESP32 memverifikasi sertifikat server dengan **Amazon Root CA 1**
(`firmware/src/ca_cert.h`; rantai: `Amazon RSA 2048 M04` → `Amazon Root CA 1`), bukan `setInsecure()`.
Prefix `<prefix>` = `sic8-montblanc/iris`. Semua payload JSON dan punya `ts` (detik Unix; ESP32 memakai NTP dan
mengirim `0` sebelum jam tersinkron).

| Topic | Arah | QoS / retain | Payload |
|---|---|---|---|
| `<prefix>/<node>/detection` | server → ESP32, dashboard | 0 | `{"ts":1793210995.2,"person_count":2,"persons":[{"id":1,"helmet":true,"vest":true,"violation_s":0.0},{"id":2,"helmet":false,"vest":true,"violation_s":4.5}],"violators":[2]}` |
| `<prefix>/<node>/status` | ESP32 → dashboard | 0 / **retain** | `{"ts":...,"node":"gate1","mode":"gate","source":"live","state":"DENIED","gate":"closed","missing":["helmet"],"person_count":2,"violation_s":0.0}` |
| `<prefix>/<node>/event` | ESP32 → dashboard | 0 | `{"ts":...,"node":"gate1","type":"denied","level":2,"missing":["helmet"],"person_count":2,"duration_s":0.0}` |
| `<prefix>/<node>/override` | dashboard/supervisor → ESP32 | 1 | `{"cmd":"reset"}` |
| `<prefix>/server/heartbeat` | server → ESP32 | 0 | `{"ts":...,"fps":24.5,"source":"vision"}` |

- `<node>`: `gate1`, `zoneA`. `type` event: `granted`, `denied`, `warning`, `alarm`, `cleared`, `fault`, `recovered`;
  `level`: 0 info, 1 peringatan, 2 pelanggaran, 3 gangguan.
- Server mengirim `detection` ±2 Hz dan `heartbeat` 1 Hz. ESP32 masuk `FAULT` bila salah satunya berhenti
  > `FAILSAFE_TIMEOUT_MS`.
- ESP32 publish `status` saat state/APD berubah dan tiap `STATUS_PERIOD_MS`. *Last Will* broker:
  `{"node":"gate1","state":"OFFLINE"}` (retain) jika ESP32 putus tidak wajar.
- ESP32 memakai PubSubClient, yang hanya bisa publish QoS 0; karena itu `event` QoS 0.
- `vision/iris_mqtt.py` = modul koneksi Python bersama; `vision/sim_publisher.py` = simulator server vision.

**Keterbatasan diketahui:** saat (re)connect TLS, `loop()` tertahan beberapa detik (handshake dibatasi 8 s). Selama itu
aktuator mempertahankan state terakhir. Pada mode LIVE durasi pelanggaran dihitung server, jadi timer zona tidak
terpengaruh; pada mode TEST timer lokal ikut berjalan.

## 6. Format log Serial

Satu baris per kejadian, diawali tag:

```
[BOOT] IRIS node=gate1 role=GATE source=TEST
[INPUT] person=1 helmet=1 vest=0
[STATE] IDLE -> DENIED missing=vest
[ACT] servo=0 led=RED buzzer=ON
[NET] wifi connected ip=10.10.0.2          (irisan 2)
[MQTT] rx detection person_count=1 violators=1   (irisan 2)
```
