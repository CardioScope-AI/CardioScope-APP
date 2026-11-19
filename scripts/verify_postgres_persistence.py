"""Verify the Compose database volume using an isolated, temporary SQL table."""

import json
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import uuid


ROOT = Path(__file__).resolve().parents[1]


def compose(*args):
    result = subprocess.run(
        ["docker", "compose", *args], cwd=ROOT,
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=300,
    )
    if result.returncode:
        raise RuntimeError(f"Docker Compose command failed: {args[0]}")
    return result.stdout.strip()


def sql(statement):
    return compose("exec", "-T", "db", "psql", "-X", "-t", "-A",
                   "-v", "ON_ERROR_STOP=1", "-U", "cardioscope",
                   "-d", "cardioscope", "-c", statement)


def main():
    table = "app18_probe_" + uuid.uuid4().hex
    compose("config", "--quiet")
    compose("up", "-d", "--wait", "--wait-timeout", "120", "db")
    before = compose("ps", "-q", "db")
    created = False
    try:
        sql(f"CREATE TABLE {table} (id integer PRIMARY KEY); "
            f"INSERT INTO {table} VALUES (1);")
        created = True
        compose("up", "-d", "--force-recreate", "--wait",
                "--wait-timeout", "120", "db")
        after = compose("ps", "-q", "db")
        count = sql(f"SELECT count(*) FROM {table} WHERE id = 1;")
        if not before or not after or before == after or count != "1":
            raise RuntimeError("Persistence check failed: container or row mismatch")
        postgres_version = sql("SHOW server_version;")
    finally:
        if created:
            sql(f"DROP TABLE IF EXISTS {table};")

    report = {
        "verified_at_utc": datetime.now(timezone.utc).isoformat(),
        "postgres_version": postgres_version,
        "container_before": before,
        "container_after": after,
        "container_recreated": True,
        "rows_after_recreation": 1,
        "temporary_table_removed": True,
        "scope": "Compose PostgreSQL volume only; no application tables or migrations validated",
    }
    target = ROOT / "docs" / "verification-postgresql.json"
    target.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
