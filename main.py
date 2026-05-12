"""Solar Panel Estimation Tool — Entry point.

Usage:
    python main.py
"""

import threading
import time
import requests
import sys

BACKEND_PORT = 8765


def _start_backend() -> None:
    import uvicorn
    from backend.api.server import app
    uvicorn.run(app, host="127.0.0.1", port=BACKEND_PORT, log_level="warning")


def _wait_for_backend(timeout: float = 10.0) -> None:
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


def main() -> None:
    # Start backend server in background
    t = threading.Thread(target=_start_backend, daemon=True)
    t.start()
    _wait_for_backend()

    import tkinter as tk
    from frontend.app import SolarPanelEstimationApp
    from frontend.api_client import ApiClient

    api = ApiClient(f"http://127.0.0.1:{BACKEND_PORT}")

    root = tk.Tk()
    app = SolarPanelEstimationApp(root, api)
    root.mainloop()


if __name__ == "__main__":
    main()
