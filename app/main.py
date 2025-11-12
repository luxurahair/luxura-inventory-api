# app/main.py
from fastapi import FastAPI
from app.db import init_db
from sqlmodel import Session, select
from app import models  # assure-toi que tes modèles sont importés pour être enregistrés

app = FastAPI(title="Luxura Inventory API")

@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/healthz")
def healthz():
    return {"ok": True}

# Exemple simple si tu as un modèle Salon
# from app.models import Salon
# @app.get("/salons")
# def list_salons():
#     with Session(models.engine) as s:  # ou importe engine depuis app.db si tu l’exportes
#         return s.exec(select(Salon)).all()
