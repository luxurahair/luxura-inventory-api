import os
from typing import Generator

from sqlalchemy import create_engine
from sqlmodel import Session

def mask_db_url(url: str) -> str:
    if not url or "://" not in url or "@" not in url:
        return url
    scheme, rest = url.split("://", 1)
    creds, tail = rest.split("@", 1)
    user = creds.split(":", 1)[0]
    return f"{scheme}://{user}:***@{tail}"

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./luxura.db")
if "DATABASE_URL" not in os.environ:
    print("[DB] DATABASE_URL missing, fallback to sqlite:///./luxura.db")

print("[DB] Using DATABASE_URL =", mask_db_url(DATABASE_URL))

engine_options = {
    "pool_pre_ping": True,
}

if DATABASE_URL.startswith("sqlite"):
    engine_options["connect_args"] = {"check_same_thread": False}
else:
    engine_options["pool_size"] = 3
    engine_options["max_overflow"] = 2

engine = create_engine(DATABASE_URL, **engine_options)

def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
