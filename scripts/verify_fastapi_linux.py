"""Test Linux réel de FastAPI sans modèle, sans modifier le dépôt backend.

Exécuter avec le Python Linux contenant les requirements-dev du backend.
Le serveur temporaire est arrêté à la fin, y compris en cas d'échec.
"""

import argparse
from datetime import datetime, timezone
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import socket
import subprocess
import sys
import tempfile
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def request(base, path, method="GET", headers=None):
    try:
        response = urlopen(Request(base + path, method=method, headers=headers or {}), timeout=3)
    except HTTPError as error:
        response = error
    with response:
        return response.status, dict(response.headers), response.read()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend", type=Path,
                        default=Path(__file__).resolve().parents[2] / "CardioScope-BACKEND")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    if platform.system() != "Linux":
        raise RuntimeError("Ce contrôle doit être exécuté dans Linux, par exemple Ubuntu/WSL.")
    if sys.version_info[:3] != (3, 13, 7):
        raise RuntimeError("Utiliser Python 3.13.7 pour correspondre aux versions du projet.")
    backend = args.backend.resolve()
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    base = f"http://127.0.0.1:{port}"
    with tempfile.TemporaryDirectory(prefix="cardioscope-linux-") as directory:
        env = dict(os.environ, MODEL_PATH=str(Path(directory) / "absent.joblib"),
                   CORS_ORIGINS="http://localhost:5173,http://127.0.0.1:5173")
        tests = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
            cwd=backend, env=env, capture_output=True, text=True,
        )
        print(tests.stdout + tests.stderr)
        tests.check_returncode()
        with tempfile.TemporaryFile(mode="w+b") as log:
            process = subprocess.Popen(
                [sys.executable, "-m", "uvicorn", "app.main:app", "--app-dir", str(backend),
                 "--host", "127.0.0.1", "--port", str(port)],
                cwd=directory, env=env, stdout=log, stderr=log,
            )
            try:
                deadline = time.monotonic() + 30
                while True:
                    try:
                        status, _, _ = request(base, "/docs")
                        if status == 200:
                            break
                    except (URLError, TimeoutError):
                        pass
                    if process.poll() is not None or time.monotonic() > deadline:
                        log.seek(0)
                        raise RuntimeError(log.read().decode(errors="replace"))
                    time.sleep(0.1)
                checks = {}
                status, _, data = request(base, "/health")
                assert status == 503
                assert json.loads(data) == {"status": "model_unavailable", "model_ready": False}
                checks["health_without_model"] = status
                for path in ["/docs", "/openapi.json"]:
                    status, _, _ = request(base, path)
                    assert status == 200
                    checks[path] = status
                status, _, data = request(base, "/route-inexistante")
                assert status == 404 and json.loads(data)["error"]["code"] == "not_found"
                checks["missing_route"] = status
                status, _, _ = request(base, "/health", method="POST")
                assert status == 405
                checks["wrong_method"] = status
                for origin, expected in [("http://localhost:5173", 200), ("https://other.example", 400)]:
                    status, headers, _ = request(base, "/predict", method="OPTIONS", headers={
                        "Origin": origin, "Access-Control-Request-Method": "POST",
                        "Access-Control-Request-Headers": "content-type",
                    })
                    assert status == expected
                    lower_headers = {key.lower(): value for key, value in headers.items()}
                    if expected == 200:
                        assert lower_headers["access-control-allow-origin"] == origin
                    else:
                        assert "access-control-allow-origin" not in lower_headers
                    checks[f"preflight_{'allowed' if expected == 200 else 'denied'}"] = status
            finally:
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
    commit = subprocess.check_output(
        ["git", "-c", f"safe.directory={backend}", "-C", str(backend), "rev-parse", "HEAD"],
        text=True,
    ).strip()
    dirty = subprocess.check_output(
        ["git", "-c", f"safe.directory={backend}", "-C", str(backend), "status", "--porcelain"],
        text=True,
    ).strip()
    report = {
        "verified_at_utc": datetime.now(timezone.utc).isoformat(),
        "system": platform.system(), "kernel": platform.release(),
        "python": platform.python_version(), "backend_commit": commit,
        "backend_has_local_changes": bool(dirty),
        "versions": {name: importlib.metadata.version(name)
                     for name in ["fastapi", "uvicorn", "scikit-learn", "joblib", "numpy", "scipy"]},
        "backend_tests": tests.stdout + tests.stderr,
        "http_checks": checks,
        "scope": "WSL/Linux, serveur local sans modèle ; ni Docker ni prédiction réelle validés.",
    }
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
