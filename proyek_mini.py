import time
import random
import threading
import paho.mqtt.client as mqtt

# ================= KONFIGURASI =================
NIM = "2410020125"

MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_CLIENT_ID = f"PythonDevice-{NIM}"

TOPIC_SUHU = f"iot/{NIM}/sensor/suhu"
TOPIC_RELAY = f"iot/{NIM}/aktuator/relay"
TOPIC_PWM = f"iot/{NIM}/aktuator/pwm"

INTERVAL_PUBLISH = 3  # Mengirim data suhu setiap 3 detik

# ================= STATE GLOBAL =================
relay_state = "OFF"
pwm_value = 0

# ================= CALLBACK MQTT =================
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("[MQTT] Terhubung ke broker")
        client.subscribe(TOPIC_RELAY, qos=0)
        client.subscribe(TOPIC_PWM, qos=0)
        print(f"[MQTT] Subscribe ke topik: {TOPIC_RELAY}")
        print(f"[MQTT] Subscribe ke topik: {TOPIC_PWM}")
    else:
        print(f"[MQTT] Gagal terhubung, kode: {rc}")

def on_message(client, userdata, msg):
    global relay_state, pwm_value
    payload = msg.payload.decode("utf-8").strip()
    print(f"[MQTT] Pesan masuk [{msg.topic}]: {payload}")

    # 1. Kontrol Relay (GPIO 26)
    if msg.topic == TOPIC_RELAY:
        if payload in ("ON", "1"):
            relay_state = "ON"
            print("[AKTUATOR - GPIO 26] Relay ON")
        elif payload in ("OFF", "0"):
            relay_state = "OFF"
            print("[AKTUATOR - GPIO 26] Relay OFF")

    # 2. Kontrol PWM LED (GPIO 2)
    elif msg.topic == TOPIC_PWM:
        try:
            nilai = int(float(payload))
            if 0 <= nilai <= 255:
                pwm_value = nilai
                print(f"[AKTUATOR - GPIO 2] Kecerahan LED PWM: {pwm_value}/255")
        except ValueError:
            print(f"[AKTUATOR] Nilai tidak valid: {payload}")

def on_disconnect(client, userdata, rc):
    print(f"[MQTT] Terputus (kode: {rc}). Mencoba reconnect...")

# ================= PEMBACAAN SENSOR =================
def baca_suhu():
    base = 27.0
    noise = random.uniform(-1.5, 1.5)
    return round(base + noise, 2)

# ================= THREAD PUBLISH SENSOR =================
def publish_loop(client):
    while True:
        suhu = baca_suhu()
        client.publish(TOPIC_SUHU, str(suhu), qos=0)
        print(f"[SENSOR DHT22] Publish suhu: {TOPIC_SUHU} -> {suhu} °C")
        time.sleep(INTERVAL_PUBLISH)

# ================= MAIN =================
def main():
    client = mqtt.Client(client_id=MQTT_CLIENT_ID, protocol=mqtt.MQTTv311)
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect

    print(f"[MQTT] Menghubungkan ke {MQTT_BROKER}:{MQTT_PORT}...")
    client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
    client.loop_start()
    time.sleep(1)

    publisher = threading.Thread(target=publish_loop, args=(client,), daemon=True)
    publisher.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[MAIN] Menghentikan program...")
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    main()