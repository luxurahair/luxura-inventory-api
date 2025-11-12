import os
from sqlmodel import create_engine

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, echo=False)

try:
    print("[BOOT] DB URL =", engine.url.render_as_string(hide_password=True), flush=True)
except Exception:
    print("[BOOT] DB URL (raw) =", DATABASE_URL, flush=True)
