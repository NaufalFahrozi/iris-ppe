"""Koneksi MQTT bersama untuk komponen Python IRIS (vision, simulator, dashboard).

Konfigurasi dari .env: MQTT_HOST, MQTT_PORT, MQTT_TOPIC_PREFIX, MQTT_USERNAME, MQTT_PASSWORD.
Topic dan payload: docs/design.md bagian 5.
"""

import json
import os
import ssl
import time
import uuid
from pathlib import Path

import paho.mqtt.client as mqtt
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

HOST = os.getenv("MQTT_HOST", "broker.hivemq.com")
PORT = int(os.getenv("MQTT_PORT", "8883"))
PREFIX = os.getenv("MQTT_TOPIC_PREFIX", "sic8-montblanc/iris")


def topic(node: str, leaf: str) -> str:
    """Contoh: topic("gate1", "detection") -> sic8-montblanc/iris/gate1/detection"""
    return f"{PREFIX}/{node}/{leaf}"


HEARTBEAT_TOPIC = topic("server", "heartbeat")


def connect(name: str) -> mqtt.Client:
    """Buat client paho, sambung TLS ke broker, jalankan loop di thread latar."""
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"iris-{name}-{uuid.uuid4().hex[:6]}")
    if PORT == 8883:
        client.tls_set(cert_reqs=ssl.CERT_REQUIRED)
    if os.getenv("MQTT_USERNAME"):
        client.username_pw_set(os.getenv("MQTT_USERNAME"), os.getenv("MQTT_PASSWORD"))
    client.connect(HOST, PORT, keepalive=30)
    client.loop_start()
    deadline = time.time() + 15
    while not client.is_connected() and time.time() < deadline:
        time.sleep(0.05)
    if not client.is_connected():
        raise ConnectionError(f"Tidak bisa terhubung ke {HOST}:{PORT}")
    return client


def publish_json(client: mqtt.Client, topic_name: str, payload: dict, qos: int = 0, retain: bool = False) -> None:
    payload.setdefault("ts", round(time.time(), 3))
    client.publish(topic_name, json.dumps(payload), qos=qos, retain=retain)


def detection_payload(persons: list[dict]) -> dict:
    """persons: [{"id":1,"helmet":True,"vest":False,"violation_s":0.0}, ...] -> payload detection lengkap."""
    violators = [p["id"] for p in persons if not (p["helmet"] and p["vest"])]
    return {"person_count": len(persons), "persons": persons, "violators": violators}
