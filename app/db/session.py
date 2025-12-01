import os
from sqlmodel import create_engine, Session

# Exemple:
# DATABASE_URL=postgresql+psycopg://user:password@host:5432/dbname
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./luxura.db")

engine = create_engine(DATABASE_URL, echo=False)


def get_session():
    """Dépendance FastAPI pour obtenir une session DB."""
    with Session(engine) as session:
        yield session
