import threading
import paho.mqtt.client as mqtt
import psycopg2
import json
import time
import os
from datetime import datetime, timezone

# Konfigurasi
MQTT_HOST = os.getenv("MQTT_HOST", "mosquitto")
MQTT_PORT = 1883
DB_HOST = os.getenv("DB_HOST", "postgres")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "postgres")
DB_NAME = os.getenv("DB_NAME", "lindu_db")

time.sleep(5)
conn = psycopg2.connect(host=DB_HOST, user=DB_USER, password=DB_PASS, dbname=DB_NAME)
conn.autocommit = False
cursor = conn.cursor()

# Buffer antrean untuk Batch Insert (Sangat Efisien)
telemetry_buffer = []
status_buffer = []
buffer_lock = threading.Lock()

def db_writer_thread():
    global telemetry_buffer, status_buffer
    while True:
        time.sleep(0.5) # Flush ke database setiap 0.5 detik
        
        with buffer_lock:
            local_telemetry = telemetry_buffer[:]
            local_status = status_buffer[:]
            telemetry_buffer.clear()
            status_buffer.clear()
            
        if local_telemetry:
            try:
                cursor.executemany(
                    "INSERT INTO sensor_telemetry (time, node_id, pga, rms, accel_x, accel_y, accel_z, temperature, pressure, humidity, latency_ms) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    local_telemetry
                )
                conn.commit()
            except Exception as e:
                print(f"Error Batch Telemetry: {e}")
                conn.rollback()
                
        if local_status:
            try:
                cursor.executemany(
                    "INSERT INTO sensor_status (time, node_id, status, pose, tilt_angle, latency_ms, sensor_ok) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    local_status
                )
                conn.commit()
            except Exception as e:
                print(f"Error Batch Status: {e}")
                conn.rollback()

threading.Thread(target=db_writer_thread, daemon=True).start()


def on_connect(client, userdata, flags, rc):
    print(f"Ingester terhubung (rc={rc})")
    client.subscribe("lindu/sensor/#")

def on_message(client, userdata, msg):
    try:
        topic = msg.topic
        print(f'Received: {topic}')
        payload = json.loads(msg.payload.decode('utf-8'))
        now = datetime.now(timezone.utc)
        
        if topic.endswith("/data") or topic.endswith("/telemetry"):
            node_id = topic.split("/")[2]
            pga = payload.get("pga", 0.0)
            rms = payload.get("sta_lta", payload.get("rms", 0.0))
            ax = payload.get("ax", payload.get("dyn_x", 0.0))
            ay = payload.get("ay", payload.get("dyn_y", 0.0))
            az = payload.get("az", payload.get("dyn_z", 0.0))
            
            # Atmospheric Data (Opsional jika belum dikirim)
            temp = payload.get("temperature", None)
            press = payload.get("pressure", None)
            hum = payload.get("humidity", None)
            
            
            # Calculate Latency (if ESP32 sends its NTP synced epoch timestamp)
            sent_ts = payload.get("ts", payload.get("timestamp", None))
            latency = None
            if sent_ts:
                latency = (time.time() - sent_ts) * 1000.0 # Convert to milliseconds
                
            with buffer_lock:
                telemetry_buffer.append((now, node_id, pga, rms, ax, ay, az, temp, press, hum, latency))
            
        elif topic.endswith("/status"):
            node_id = payload.get("node_id", "unknown")
            status = payload.get("status", "unknown")
            pose = payload.get("pose", "unknown")
            tilt = payload.get("tilt_angle", 0.0)
            
            
            sent_ts = payload.get("ts", payload.get("timestamp", None))
            latency = None
            if sent_ts:
                latency = (time.time() - sent_ts) * 1000.0
                
            
            sensor_ok = payload.get("sensor_ok", False)
            with buffer_lock:
                status_buffer.append((now, node_id, status, pose, tilt, latency, sensor_ok))
    except Exception as e:
        print(f"Error: {e}")

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

while True:
    try:
        client.connect(MQTT_HOST, MQTT_PORT, 60)
        break
    except:
        time.sleep(2)

client.loop_forever()
