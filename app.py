"""Start Tukang Copilot:   python app.py   then open http://localhost:8000"""
import os

import uvicorn

from api.main import app  # noqa: F401  (re-exported for `uvicorn app:app`)
from api.settings import settings

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    print(f"\n  Tukang Copilot is running in {'OFFLINE SAMPLE (pre-written answers, no API calls)' if settings.offline else 'LIVE'} mode.")
    print(f"  Open http://localhost:{port} in your browser.\n")
    uvicorn.run("api.main:app", host="0.0.0.0", port=port, server_header=False)
