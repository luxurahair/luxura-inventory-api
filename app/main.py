from fastapi import FastAPI
from sqlmodel import SQLModel
from app.db import engine  # importe ton moteur SQLAlchemy configuré dans app/db.py
from app import models  # importe tes modèles SQLModel (ex: Salon, Product, etc.)

app = FastAPI(
    title="Luxura Inventory API",
    description="API de gestion d’inventaire pour Luxura Distribution",
    version="1.0.0"
)

# --- Événement au démarrage ---
@app.on_event("startup")
def on_startup():
    print("[BOOT] Initialisation de la base de données...", flush=True)
    SQLModel.metadata.create_all(engine)
    print("[BOOT] Tables créées (si absentes).", flush=True)

# --- Route simple pour tester ---
@app.get("/healthz")
def healthz():
    return {"ok": True, "status": "Luxura API running"}

# --- Exemple de routes ---
@app.get("/salons")
def list_salons():
    """
    Exemple de route temporaire
    (remplace ou étends avec tes vraies routes de ton app)
    """
    return {"message": "Endpoint /salons fonctionnel"}

