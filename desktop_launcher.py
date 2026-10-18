"""Desktop launcher running SimCorp engine and WebView on Windows."""
from __future__ import annotations
import os
import sys
import threading
import time
from pathlib import Path
import uvicorn
import webview

def start_backend_server():
    """Runs FastAPI backend on 127.0.0.1:8000."""
    # Ensure backend path is on sys.path
    project_root = Path(__file__).resolve().parent
    sys.path.insert(0, str(project_root / "backend"))
    from simcorp.api.server import app
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")

def main():
    project_root = Path(__file__).resolve().parent
    frontend_dist = project_root / "frontend" / "dist" / "index.html"

    # Start FastAPI server in background thread
    server_thread = threading.Thread(target=start_backend_server, daemon=True)
    server_thread.start()

    # Small pause to let uvicorn initialize
    time.sleep(1.2)

    target_url = "http://127.0.0.1:8000"

    # Create native Windows desktop application window
    window = webview.create_window(
        title="SimCorp - Enterprise Business Simulation",
        url=target_url,
        width=1280,
        height=850,
        min_size=(1024, 680),
        background_color="#0b0f19"
    )

    webview.start(debug=False)

if __name__ == "__main__":
    main()
