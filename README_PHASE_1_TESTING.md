# 🧪 Phase 1: Local Hardware Testing (Grafana Sandbox)

Dokumen ini adalah panduan cepat untuk menguji fisik ESP32 pertama Anda dan memastikan data telemetri (PGA, RMS, Sumbu X/Y/Z) mengalir dengan benar ke sistem *dashboard* sebelum dihubungkan ke *React Command Center* berskala besar.

## 🏗️ 1. Arsitektur Pengujian
```text
[ Sensor Fisik ]           [ Koneksi Lokal Wi-Fi ]                 [ Komputer Anda (Docker) ]
ESP32 + LSM6DS3  ────────► Wi-Fi Router Rumah ────────► Mosquitto Broker (Port 1883)
                                                                    │
                                                                    ▼
                                                            Ingester (Python)
                                                                    │
                                                                    ▼
                                                        PostgreSQL (Port 5432)
                                                                    │
                                                                    ▼
                                                            Grafana (Port 3000)
```

---

## 🔌 2. Tabel Pemasangan Kabel (GPIO Wiring)
Secara standar, kita menggunakan protokol I2C untuk menghubungkan sensor ke ESP32. Pasangkan kabel jumper *Female-to-Female* atau gunakan *Breadboard* dengan skema berikut:

| Pin LSM6DS3 (Sensor) | Pin ESP32 (Dev Board) | Fungsi | Keterangan |
| :--- | :--- | :--- | :--- |
| **VCC** (atau VIN) | **3.3V** | Power | ⚠️ **JANGAN** sambungkan ke 5V. Sensor bisa terbakar! |
| **GND** | **GND** | Ground | Titik referensi listrik. |
| **SCL** | **GPIO 22** | I2C Clock | Jalur detak sinkronisasi data. |
| **SDA** | **GPIO 21** | I2C Data | Jalur data dua arah (Telemetri). |

---

## 🛠️ 3. Penyesuaian Kode C++ (Wajib untuk Testing Lokal)

Kode C++ kita (`NetworkManager.cpp`) awalnya diset untuk level Produksi (Menggunakan Enkripsi TLS 1.2 dan mengarah ke `test.mosquitto.org:8883`). 
Untuk pengujian lokal di jaringan rumah Anda (Grafana Docker), kita harus **mematikan TLS** dan **mengarahkan IP-nya ke komputer Anda**.

### Langkah A: Buka `src/esp32_sensor_node/src/NetworkManager.cpp`
Ubah bagian paling atas dari:
```cpp
#include <WiFiClientSecure.h>
#include <PubSubClient.h>

WiFiClientSecure espClient;
PubSubClient mqtt(espClient);
```
**Menjadi (Tanpa TLS):**
```cpp
#include <WiFiClient.h>
#include <PubSubClient.h>

WiFiClient espClient;
PubSubClient mqtt(espClient);
```

### Langkah B: Ubah IP MQTT
Cari baris ini (sekitar baris ke-16):
```cpp
mqtt.setServer("test.mosquitto.org", 8883); 
```
**Ganti dengan IP Lokal Komputer Laptop Anda (Contoh: 192.168.1.5) dan Port 1883:**
```cpp
// Ganti 192.168.1.x dengan IP Address Laptop Anda saat ini (Cek via ipconfig/ifconfig)
mqtt.setServer("192.168.1.5", 1883); 
```
*Catatan: Pastikan ESP32 dan Laptop terhubung di WiFi yang sama.*

---

## 🚀 4. Langkah Eksekusi (Flashing & Monitoring)

1. Jalankan tumpukan (*stack*) Docker Grafana Anda di Terminal:
   ```bash
   cd prototype/grafana-stack
   docker-compose up -d --build
   ```
2. Hubungkan ESP32 ke Laptop menggunakan kabel USB Data.
3. Buka **PlatformIO** (di VSCode), lalu klik tombol **Upload (➔)** untuk melakukan *flashing* kode.
4. **Koneksi WiFi ESP32:** Karena kode kita menggunakan `WiFiManager`, saat pertama kali menyala ESP32 akan memancarkan WiFi mandiri. Buka HP Anda, sambungkan ke WiFi ESP32 tersebut, dan masukkan kata sandi WiFi rumah Anda.
5. Setelah ESP32 terhubung ke router, buka browser di Laptop Anda: **http://localhost:3000**
6. Di dashboard Grafana, goyangkan ESP32 Anda secara fisik. Anda seharusnya melihat grafik X/Y/Z, Metrik PGA/RMS, serta indikator kemiringan (Flat/Wall) merespons secara langsung (Real-Time)!
