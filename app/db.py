# app/db.py
import os
from sqlmodel import create_engine

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # Aide au debug si la variable n'est pas présente dans Render
    raise RuntimeError("DATABASE_URL is missing from environment variables")

engine = create_engine(DATABASE_URL, echo=False)

try:
    print("[BOOT] DB URL =", engine.url.render_as_string(hide_password=True), flush=True)
except Exception:
    print("[BOOT] DB URL (raw) =", DATABASE_URL, flush=True)
