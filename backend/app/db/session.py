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


DATABASE_URL = os.environ.get("DATABASE_URL", "")

# Fix URL format: postgresql+psycopg:// -> postgresql://
if DATABASE_URL.startswith("postgresql+psycopg://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql+psycopg://", "postgresql://", 1)

if DATABASE_URL:
    print("[DB] Using DATABASE_URL =", mask_db_url(DATABASE_URL))
else:
    print("[DB] WARNING: DATABASE_URL not set - database operations will fail")

# Lazy engine creation
_engine = None

def get_engine():
    global _engine
    if _engine is None:
        if not DATABASE_URL:
            raise RuntimeError("DATABASE_URL is missing in environment variables")
        _engine = create_engine(
            DATABASE_URL,
            poolclass=QueuePool,
            pool_pre_ping=True,
            pool_recycle=300,
            pool_size=2,
            max_overflow=3,
            pool_timeout=30,
            connect_args={
                "connect_timeout": 10,
                "keepalives": 1,
                "keepalives_idle": 30,
                "keepalives_interval": 10,
                "keepalives_count": 5,
            }
        )
    return _engine

# For backwards compatibility
@property
def engine():
    return get_engine()


def get_session() -> Generator[Session, None, None]:
    """
    Générateur de session avec gestion propre des connexions.
    """
    session = Session(get_engine())
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
    session = Session(get_engine())
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
