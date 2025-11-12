# app/db.py
import os
import re
from typing import Generator

from sqlmodel import SQLModel, create_engine, Session


def _normalize_database_url(url: str) -> str:
    """
    - Render fournit souvent un URL qui commence par 'postgres://'.
      SQLAlchemy préfère 'postgresql+psycopg://'.
    - Si tu as déjà 'postgresql+psycopg2://' ou 'postgresql+psycopg://', on touche à rien.
    - Supporte aussi SQLite pour le dev/local.
    """
    if not url:
        return "sqlite:///./data.db"

    url = url.strip()

    # SQLite: rien à faire
    if url.startswith("sqlite:"):
        return url

    # Déjà un dialecte explicite
    if url.startswith("postgresql+psycopg2://") or url.startswith("postgresql+psycopg://"):
        return url

    # 'postgres://' → 'postgresql+psycopg://'
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)

    # 'postgresql://' → 'postgresql+psycopg://'
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)

    # Par défaut, on laisse tel quel.
    return url


def _build_engine(url: str):
    """
    Crée le moteur SQLAlchemy avec des params safe pour Render.
    - Postgres (psycopg3) : pool pré-ping + sizing ok.
    - SQLite : check_same_thread=False pour l’async/Uvicorn.
    NE **PAS** passer ssl/sslmode dans connect_args ici (mets-le dans l’URL si besoin).
    """
    is_sqlite = url.startswith("sqlite:")
    if is_sqlite:
        return create_engine(
            url,
            echo=False,
            connect_args={"check_same_thread": False},
        )

    # Postgres (psycopg3)
    # Ajuste pool_size/max_overflow selon ta charge réelle.
    return create_engine(
        url,
        echo=False,
        pool_pre_ping=True,
        pool_size=int(os.getenv("DB_POOL_SIZE", "5")),
        max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "10")),
        pool_recycle=1800,  # recycle toutes les 30 min pour éviter les connexions zombies
    )


# ──────────────────────────────────────────────────────────────────────────────
# Configuration & Engine global
# ──────────────────────────────────────────────────────────────────────────────
RAW_DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
DATABASE_URL = _normalize_database_url(RAW_DATABASE_URL)
engine = _build_engine(DATABASE_URL)

# Petit log au boot (sans le mot de passe)
try:
    safe_url = engine.url._replace(password="***")
    print(f"[BOOT] DB URL = {safe_url}", flush=True)
except Exception:
    print(f"[BOOT] DB URL (raw) = {DATABASE_URL}", flush=True)


# ──────────────────────────────────────────────────────────────────────────────
# Init DB (appelée dans lifespan de FastAPI)
# ──────────────────────────────────────────────────────────────────────────────
def init_db() -> None:
    """
    Crée toutes les tables connues de SQLModel.
    Appelée une seule fois au démarrage de l’app (voir app/main.py).
    """
    SQLModel.metadata.create_all(engine)


# ──────────────────────────────────────────────────────────────────────────────
# Dépendance FastAPI pour obtenir une session par requête
# ──────────────────────────────────────────────────────────────────────────────
def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
