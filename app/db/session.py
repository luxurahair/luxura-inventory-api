import os
from sqlmodel import create_engine, Session
from sqlalchemy.engine import make_url

# On récupère l'URL brute (Render ou local)
RAW_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./luxura.db")

# Corrige "postgres://" -> "postgresql://"
if RAW_DATABASE_URL.startswith("postgres://"):
    RAW_DATABASE_URL = RAW_DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Parse pour inspecter / modifier le driver
url = make_url(RAW_DATABASE_URL)

# Force l'utilisation de psycopg3 si le driver est juste "postgresql"
if url.drivername == "postgresql":
    url = url.set(drivername="postgresql+psycopg")

DATABASE_URL = str(url)

print(f"[DB] Using DATABASE_URL = {DATABASE_URL}")  # tu le vois dans les logs Render

engine = create_engine(DATABASE_URL, echo=False)

def get_session():
    with Session(engine) as session:
        yield session
