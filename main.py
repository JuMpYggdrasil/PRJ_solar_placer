"""Solar Panel Estimation Tool — Entry point.

Usage:
    python main.py              # Tkinter frontend (default)
    python main.py --modern     # Next.js web frontend
"""

import threading
import time
import subprocess
import webbrowser
import os
import signal
import sys

BACKEND_PORT = 8765


def _start_backend() -> None:
    import uvicorn
    from backend.api.server import app
    uvicorn.run(app, host="127.0.0.1", port=BACKEND_PORT, log_level="warning")


def _wait_for_backend(timeout: float = 10.0) -> None:
    import requests
    url = f"http://127.0.0.1:{BACKEND_PORT}/api/health"
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = requests.get(url, timeout=2)
            if r.status_code == 200:
                return
        except requests.ConnectionError:
            pass
        time.sleep(0.25)
    print("ERROR: Backend failed to start.", file=sys.stderr)
    sys.exit(1)


def _start_web_frontend() -> None:
    """Start Next.js dev server and open browser."""
    frontend_dir = os.path.join(os.path.dirname(__file__), "frontend_modern")
    proc = subprocess.Popen(
        ["npx", "next", "dev"],
        cwd=frontend_dir,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        webbrowser.open("http://localhost:3000")
        print("Web frontend started at http://localhost:3000")
        print("Press Ctrl+C to stop.")
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()
        proc.wait()


def _start_tkinter() -> None:
    import tkinter as tk
    from frontend.app import SolarPanelEstimationApp
    from frontend.api_client import ApiClient

    api = ApiClient(f"http://127.0.0.1:{BACKEND_PORT}")

    root = tk.Tk()
    app = SolarPanelEstimationApp(root, api)
    root.mainloop()


def main() -> None:
    # Start backend server in background
    t = threading.Thread(target=_start_backend, daemon=True)
    t.start()
    _wait_for_backend()

    if "--modern" in sys.argv:
        _start_web_frontend()
    else:
        _start_tkinter()


if __name__ == "__main__":
    main()
