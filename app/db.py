# app/db.py
import os
from typing import Generator

from sqlmodel import SQLModel, Session, create_engine


def _normalize_database_url(url: str) -> str:
    """
    Normalise l'URL de DB pour qu'elle utilise psycopg (psycopg3) avec SQLAlchemy.

    - Si vide -> SQLite local (dev)
    - postgres:// -> postgresql+psycopg://
    - postgresql:// -> postgresql+psycopg://
    - Si ça commence déjà par postgresql+psycopg://, on touche à rien.
    """
    if not url:
        # fallback local pour le dev
        return "sqlite:///./data.db"

    url = url.strip()

    # SQLite -> on laisse tel quel
    if url.startswith("sqlite:"):
        return url

    # Déjà correct
    if url.startswith("postgresql+psycopg://"):
        return url

    # Render / Supabase donnent souvent "postgres://" ou "postgresql://"
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)

    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)

    # Sinon on laisse
    return url


def _build_engine(url: str):
    """
    Crée le moteur SQLAlchemy.

    - SQLite: check_same_thread=False
    - Postgres (psycopg3): pool_pre_ping, etc.
    """
    is_sqlite = url.startswith("sqlite:")

    if is_sqlite:
        return create_engine(
            url,
            echo=False,
            connect_args={"check_same_thread": False},
        )

    # Postgres via psycopg3
    return create_engine(
        url,
        echo=False,
        pool_pre_ping=True,
        pool_size=int(os.getenv("DB_POOL_SIZE", "5")),
        max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "10")),
        pool_recycle=1800,
    )


# ─────────────────────────────────────────────────────────────
# Config globale
# ─────────────────────────────────────────────────────────────
RAW_DATABASE_URL = os.getenv("DATABASE_URL", "")
DATABASE_URL = _normalize_database_url(RAW_DATABASE_URL)

engine = _build_engine(DATABASE_URL)

# Log au démarrage (sans mot de passe)
try:
    safe_url = engine.url._replace(password="***")
    print(f"[BOOT] DB URL = {safe_url}", flush=True)
except Exception:
    print(f"[BOOT] DB URL (raw) = {DATABASE_URL}", flush=True)


# ─────────────────────────────────────────────────────────────
# Init DB
# ─────────────────────────────────────────────────────────────
def init_db() -> None:
    SQLModel.metadata.create_all(engine)


# ─────────────────────────────────────────────────────────────
# Session par requête (FastAPI dependency)
# ─────────────────────────────────────────────────────────────
def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
