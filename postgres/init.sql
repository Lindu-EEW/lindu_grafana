CREATE TABLE IF NOT EXISTS sensor_telemetry (
    time        TIMESTAMP WITH TIME ZONE NOT NULL,
    node_id     VARCHAR(50) NOT NULL,
    pga         DOUBLE PRECISION,
    rms         DOUBLE PRECISION,
    accel_x     DOUBLE PRECISION,
    accel_y     DOUBLE PRECISION,
    accel_z     DOUBLE PRECISION,
    temperature DOUBLE PRECISION,
    pressure    DOUBLE PRECISION,
    humidity    DOUBLE PRECISION,
    latency_ms  DOUBLE PRECISION,
    sensor_ok   BOOLEAN
);

CREATE TABLE IF NOT EXISTS sensor_status (
    time        TIMESTAMP WITH TIME ZONE NOT NULL,
    node_id     VARCHAR(50) NOT NULL,
    status      VARCHAR(20),
    pose        VARCHAR(20),
    tilt_angle  DOUBLE PRECISION,
    latency_ms  DOUBLE PRECISION,
    sensor_ok   BOOLEAN
);
