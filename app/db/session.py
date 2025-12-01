import os
from sqlmodel import create_engine, Session
from sqlalchemy.engine import make_url

# On récupère l'URL brute (Render)
RAW_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./luxura.db")

# Supabase utilise parfois "postgres://" -> on corrige
if RAW_DATABASE_URL.startswith("postgres://"):
    RAW_DATABASE_URL = RAW_DATABASE_URL.replace("postgres://", "postgresql://", 1)

# On parse l'URL pour inspecter le driver
url = make_url(RAW_DATABASE_URL)

# Si le driver est "postgresql" (ce qui force psycopg2),
# on le remplace par "postgresql+psycopg" (psycopg3)
if url.drivername == "postgresql":
    url = url.set(drivername="postgresql+psycopg")

DATABASE_URL = str(url)

print(f"[DB] Using DATABASE_URL = {DATABASE_URL}")  # visible dans les logs Render

engine = create_engine(DATABASE_URL, echo=False)


def get_session():
    with Session(engine) as session:
        yield session
