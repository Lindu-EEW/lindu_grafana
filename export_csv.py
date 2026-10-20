"""Export the live PostgreSQL tables to CSV (UTF-8, header row, UTC timestamps).

Usage:  python export_csv.py [output_dir]
Default output_dir is ../../dataset. Reads through `docker exec` on the
grafana_postgres container, so no Python DB driver is needed.
"""
import os
import subprocess
import sys

CONTAINER = os.getenv("PG_CONTAINER", "grafana_postgres")
DB_USER = os.getenv("DB_USER", "postgres")
DB_NAME = os.getenv("DB_NAME", "lindu_db")

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "..", "dataset")

EXPORTS = {
    "node_heartbeat_pir_log.csv": "SELECT * FROM sensor_status ORDER BY time",
    "actuator_log.csv": "SELECT * FROM actuator_log ORDER BY time",
}


def export(name, query):
    path = os.path.join(OUT_DIR, name)
    sql = f"SET TIME ZONE 'UTC'; COPY ({query}) TO STDOUT WITH CSV HEADER"
    with open(path, "wb") as f:
        subprocess.run(
            ["docker", "exec", CONTAINER, "psql", "-U", DB_USER, "-d", DB_NAME, "-q", "-c", sql],
            stdout=f, check=True,
        )
    with open(path, "rb") as f:
        rows = sum(1 for _ in f) - 1
    print(f"{name}: {rows} rows")


if __name__ == "__main__":
    os.makedirs(OUT_DIR, exist_ok=True)
    for name, query in EXPORTS.items():
        export(name, query)
