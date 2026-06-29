import atexit
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

import requests

from config.firebase_config import API_BASE_URL

_process: subprocess.Popen | None = None
_we_started = False

_LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1"}


def _parse_target():
    parsed = urlparse(API_BASE_URL)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    if port in (80, 443) and not parsed.port:
        port = 8000
    return host, port


def _health_url() -> str:
    return f"{API_BASE_URL.rstrip('/')}/health"


def is_healthy() -> bool:
    try:
        requests.get(_health_url(), timeout=0.5).raise_for_status()
        return True
    except Exception:
        return False


def ensure_running(timeout: float = 20.0) -> None:
    """Start a local API process if needed and wait until /health responds."""
    global _process, _we_started

    if is_healthy():
        return

    host, port = _parse_target()
    if host not in _LOCAL_HOSTS:
        raise RuntimeError(
            f"API at {API_BASE_URL} is not reachable. "
            "Start the remote server or point API_BASE_URL to localhost."
        )

    root = Path(__file__).resolve().parent.parent
    _process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "backend.api.main:app",
            "--host",
            host,
            "--port",
            str(port),
        ],
        cwd=root,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    _we_started = True

    deadline = time.time() + timeout
    while time.time() < deadline:
        if _process.poll() is not None:
            err = _process.stderr.read().decode(errors="replace") if _process.stderr else ""
            _process = None
            _we_started = False
            raise RuntimeError(f"API server exited unexpectedly:\n{err}".strip())

        if is_healthy():
            return
        time.sleep(0.2)

    stop()
    raise RuntimeError("API server did not become ready in time.")


def stop() -> None:
    global _process, _we_started
    if not _we_started or _process is None:
        return

    _process.terminate()
    try:
        _process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        _process.kill()
        _process.wait()
    _process = None
    _we_started = False


atexit.register(stop)
