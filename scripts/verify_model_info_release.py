"""Run inside the backend Docker image; authenticate against a disposable database."""
import argparse
from datetime import datetime, timezone
from http.cookiejar import CookieJar
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import tempfile
import time
from urllib.error import HTTPError, URLError
from urllib.request import build_opener, HTTPCookieProcessor, Request
from uuid import uuid4

# This verifier is mounted outside the application directory inside its image.
sys.path.insert(0, "/app")

from alembic import command
from alembic.config import Config
import sqlalchemy as sa
from sqlalchemy.orm import Session

from app.database import database_url
from app.init_admin import initialize_admin


def verify():
    base = "http://127.0.0.1:18765"
    model = Path(os.environ["MODEL_PATH"])
    manifest = json.loads((model.parent / "release.json").read_text(encoding="utf-8"))
    name = "cardioscope_test_" + uuid4().hex
    original_host = os.environ["DB_HOST"]
    # Resolve Docker DNS once, outside the application's short connection timeout.
    os.environ["DB_HOST"] = socket.gethostbyname(original_host)
    control = sa.create_engine(database_url().set(database="postgres"),
                               isolation_level="AUTOCOMMIT", hide_parameters=True)
    process, engine, created = None, None, False
    original_name = os.environ["DB_NAME"]
    logs = tempfile.TemporaryFile()
    try:
        with control.connect() as connection:
            connection.exec_driver_sql(f'CREATE DATABASE "{name}"')
        created = True
        os.environ["DB_NAME"] = name
        for attempt in range(3):
            try:
                command.upgrade(Config("/app/alembic.ini"), "head")
                break
            except sa.exc.OperationalError:
                if attempt == 2:
                    raise
                time.sleep(1)
        engine = sa.create_engine(database_url(), hide_parameters=True)
        password = secrets.token_urlsafe(32)
        with Session(engine) as db:
            initialize_admin(db, "release-test-admin", password)
        env = dict(os.environ, AUTH_COOKIE_SECURE="false", CORS_ORIGINS=base)
        process = subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app",
                                    "--host", "127.0.0.1", "--port", "18765"],
                                   env=env, stdout=logs, stderr=logs)
        opener = build_opener(HTTPCookieProcessor(CookieJar()))

        def request(path, body=None, headers=None):
            req = Request(base + path, data=json.dumps(body).encode() if body is not None else None,
                          headers=headers or {})
            try:
                response = opener.open(req, timeout=10)
            except HTTPError as error:
                response = error
            with response:
                return response.status, json.load(response), response.headers

        deadline = time.monotonic() + 300
        while True:
            try:
                status, _, _ = request("/health")
                assert status == 200, "Release model did not load"
                break
            except (URLError, TimeoutError, ConnectionError):
                if process.poll() is not None or time.monotonic() >= deadline:
                    raise RuntimeError("Temporary backend did not start; no credentials logged") from None
                time.sleep(1)
        anonymous, error, _ = request("/model-info")
        assert anonymous == 401 and error["error"]["code"] == "unauthenticated"
        csrf_status, csrf, _ = request("/admin/csrf")
        assert csrf_status == 200
        login_status, _, _ = request("/admin/login",
            {"username": "release-test-admin", "password": password},
            {"Content-Type": "application/json", "Origin": base, "X-CSRF-Token": csrf["csrf_token"]})
        assert login_status == 200, "Temporary login failed"
        me_status, _, _ = request("/admin/me")
        assert me_status == 200
        info_status, info, headers = request("/model-info")
        assert info_status == 200
        assert info["model_version"] == manifest["model_version"]
        assert info["artifact_sha256"] == manifest["artifact_sha256"]
        assert headers["Cache-Control"] == "no-store"
        return {"verified_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "scope": "Docker/Linux; real release; temporary PostgreSQL database and admin; HTTP loopback",
                "http_checks": {"health": 200, "anonymous_model_info": anonymous,
                                "csrf": csrf_status, "login": login_status,
                                "me": me_status, "authenticated_model_info": info_status},
                "model_version": info["model_version"], "artifact_sha256": info["artifact_sha256"],
                "test_accuracy": info["evaluation"]["test_metrics"]["accuracy"],
                "cache_control": headers["Cache-Control"]}
    finally:
        if process:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        if engine:
            engine.dispose()
        os.environ["DB_NAME"] = original_name
        os.environ["DB_HOST"] = original_host
        if created:
            with control.connect() as connection:
                connection.exec_driver_sql(f'DROP DATABASE "{name}" WITH (FORCE)')
        control.dispose()
        logs.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    result = verify()
    # Only write a successful report after cleanup has completed.
    rendered = json.dumps(result, indent=2) + "\n"
    if args.report:
        args.report.write_text(rendered, encoding="utf-8")
    print(rendered)
