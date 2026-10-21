CREATE TABLE IF NOT EXISTS sensor_telemetry (
    time         TIMESTAMP WITH TIME ZONE NOT NULL,
    node_id      VARCHAR(50) NOT NULL,
    pga          DOUBLE PRECISION,
    rms          DOUBLE PRECISION,
    accel_x      DOUBLE PRECISION,
    accel_y      DOUBLE PRECISION,
    accel_z      DOUBLE PRECISION,
    temperature  DOUBLE PRECISION,
    pressure     DOUBLE PRECISION,
    humidity     DOUBLE PRECISION,
    latency_ms   DOUBLE PRECISION,
    valve_status VARCHAR(20),
    gas_raw      INTEGER,
    gas_alert    BOOLEAN
);

-- init.sql hanya jalan sekali saat volume postgres pertama kali dibuat, jadi
-- kolom baru di atas ditambahkan lagi di sini untuk deployment yang sudah
-- ada sebelumnya (volume lama tanpa kolom gas).
ALTER TABLE sensor_telemetry ADD COLUMN IF NOT EXISTS gas_raw INTEGER;
ALTER TABLE sensor_telemetry ADD COLUMN IF NOT EXISTS gas_alert BOOLEAN;

-- Status solenoid door lock (LOCKED/UNLOCKED; UNAVAILABLE di node tanpa door lock).
ALTER TABLE sensor_telemetry ADD COLUMN IF NOT EXISTS door_status VARCHAR(20);

-- TinyML shadow mode: probabilitas gempa dari firmware (0.0-1.0) dan kesepakatan dengan algoritma klasik.
ALTER TABLE sensor_telemetry ADD COLUMN IF NOT EXISTS ml_prob DOUBLE PRECISION DEFAULT 0.0;
ALTER TABLE sensor_telemetry ADD COLUMN IF NOT EXISTS ml_agree BOOLEAN DEFAULT TRUE;

-- Log event aktuator: satu baris tiap aktuator berubah state (valve, door, buzzer, led).
-- reason diisi firmware secara inferensi dari kondisi saat perubahan terjadi.
CREATE TABLE IF NOT EXISTS actuator_log (
    time     TIMESTAMP WITH TIME ZONE NOT NULL,
    node_id  VARCHAR(50) NOT NULL,
    actuator VARCHAR(20) NOT NULL,
    state    VARCHAR(30) NOT NULL,
    reason   VARCHAR(40)
);
CREATE INDEX IF NOT EXISTS actuator_log_time_idx ON actuator_log (time DESC);

CREATE TABLE IF NOT EXISTS sensor_status (
    time            TIMESTAMP WITH TIME ZONE NOT NULL,
    node_id         VARCHAR(50) NOT NULL,
    status          VARCHAR(20),
    pose            VARCHAR(20),
    tilt_angle      DOUBLE PRECISION,
    latency_ms      DOUBLE PRECISION,
    sensor_ok       BOOLEAN,
    fw_version      VARCHAR(50),
    ota_status      VARCHAR(50),
    motion_detected BOOLEAN
);

-- Kolom PIR ditambahkan belakangan; ALTER di sini agar deployment lama (volume
-- postgres yang sudah ada) ikut dapat kolomnya juga, sama seperti pola gas_raw/gas_alert di atas.
ALTER TABLE sensor_status ADD COLUMN IF NOT EXISTS motion_detected BOOLEAN;

-- Lokasi node terakhir yang diketahui (dipakai panel peta "Live Seismic Map").
-- Di-upsert oleh ingester setiap kali menerima pesan status dari node.
CREATE TABLE IF NOT EXISTS tb_nodes (
    node_id    VARCHAR(50) PRIMARY KEY,
    lat        DOUBLE PRECISION,
    lon        DOUBLE PRECISION,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Telemetri streaming per detik (freq_hz, sta_lta, uptime). Dipakai panel "Frekuensi Dominan" dan gauge PGA.
CREATE TABLE IF NOT EXISTS tb_sensor_telemetry (
    ts           TIMESTAMP(3) WITH TIME ZONE NOT NULL DEFAULT NOW(),
    node_id      VARCHAR(32),
    pga          DOUBLE PRECISION,
    sta_lta      DOUBLE PRECISION,
    freq_hz      INTEGER,
    ax           DOUBLE PRECISION,
    ay           DOUBLE PRECISION,
    az           DOUBLE PRECISION,
    lat          DOUBLE PRECISION,
    lon          DOUBLE PRECISION,
    uptime_ms    BIGINT,
    gas_raw      INTEGER,
    gas_alert    BOOLEAN,
    door_status  VARCHAR(16),
    valve_status VARCHAR(16),
    ml_prob      DOUBLE PRECISION DEFAULT 0.0,
    ml_agree     BOOLEAN DEFAULT TRUE
);
CREATE INDEX IF NOT EXISTS idx_tb_sensor_telemetry_ts_node ON tb_sensor_telemetry (ts DESC, node_id);
