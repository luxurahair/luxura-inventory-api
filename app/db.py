import os
from sqlmodel import create_engine

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///app.db"  # fallback local
)

# echo=False pour des logs propres
engine = create_engine(DATABASE_URL, echo=False)
