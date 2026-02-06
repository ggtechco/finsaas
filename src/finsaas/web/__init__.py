"""FinSaaS Web Dashboard - FastAPI backend with static frontend."""

import os
from pathlib import Path

UPLOAD_DIR = Path(os.environ.get("UPLOAD_DIR", "uploads"))
STATIC_DIR = Path(__file__).parent / "static"
