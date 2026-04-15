import os
from typing import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool
from sqlmodel import Session


def mask_db_url(url: str) -> str:
    if not url or "://" not in url or "@" not in url:
        return url
    scheme, rest = url.split("://", 1)
    creds, tail = rest.split("@", 1)
    user = creds.split(":", 1)[0]
    return f"{scheme}://{user}:***@{tail}"


DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is missing in environment variables")

print("[DB] Using DATABASE_URL =", mask_db_url(DATABASE_URL))

# Configuration optimisée pour Supabase + Render
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_pre_ping=True,       # Vérifie la connexion avant utilisation
    pool_recycle=300,         # Recycle toutes les 5 minutes
    pool_size=2,              # Seulement 2 connexions permanentes
    max_overflow=3,           # Jusqu'à 5 total en pic
    pool_timeout=30,          # Attendre max 30s pour une connexion
    connect_args={
        "connect_timeout": 10,
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 5,
    }
)


def get_session() -> Generator[Session, None, None]:
    """
    Générateur de session avec gestion propre des connexions.
    """
    session = Session(engine)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@contextmanager
def get_db_session():
    """
    Context manager alternatif pour utilisation manuelle.
    """
    session = Session(engine)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
