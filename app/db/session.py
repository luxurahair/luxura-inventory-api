import os
from sqlmodel import create_engine, Session
from sqlalchemy.engine import make_url

# On récupère l'URL brute (Render)
RAW_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./luxura.db")

# Render OU Supabase utilisent parfois "postgres://" -> corriger
if RAW_DATABASE_URL.startswith("postgres://"):
    RAW_DATABASE_URL = RAW_DATABASE_URL.replace("postgres://", "postgresql://", 1)

# On parse l'URL
url = make_url(RAW_DATABASE_URL)

# Exemple :
# url.drivername == "postgresql"
# On le remplace par psycopg (driver psycopg3 moderne)
if url.drivername == "postgresql":
    url = url.set(drivername="postgresql+psycopg")

DATABASE_URL = str(url)

print(f"[DB] Using DATABASE_URL = {DATABASE_URL}")

# Engine SQLAlchemy
engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,        # évite erreurs Render "connection lost"
    pool_recycle=1800          # recycle les connexions mortes après 30 min
)

def get_session():
    with Session(engine) as session:
        yield session
