# app/db.py
import os
from typing import Generator
from sqlmodel import SQLModel, Session, create_engine


def _normalize_database_url(url: str) -> str:
    if not url:
        return "sqlite:///./data.db"

    url = url.strip()

    if url.startswith("sqlite:"):
        return url

    if url.startswith("postgresql+psycopg://"):
        return url

    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)

    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)

    return url


def _build_engine(url: str):
    if url.startswith("sqlite:"):
        return create_engine(
            url,
            echo=False,
            connect_args={"check_same_thread": False},
        )

    return create_engine(
        url,
        echo=False,
        pool_pre_ping=True,
        pool_size=int(os.getenv("DB_POOL_SIZE", "5")),
        max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "10")),
        pool_recycle=1800,
    )


RAW_DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
DATABASE_URL = _normalize_database_url(RAW_DATABASE_URL)
engine = _build_engine(DATABASE_URL)

try:
    safe_url = engine.url._replace(password="***")
    print(f"[BOOT] DB URL = {safe_url}", flush=True)
except Exception:
    print(f"[BOOT] DB URL (raw) = {DATABASE_URL}", flush=True)


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
