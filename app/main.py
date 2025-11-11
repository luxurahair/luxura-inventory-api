from fastapi import FastAPI, HTTPException
from sqlmodel import SQLModel, Session, select
from .db import engine
from .models import Salon, SalonCreate, Product, ProductCreate

app = FastAPI(title="Luxura Inventory API")

@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)

# -------- Salons
@app.get("/salons", response_model=list[Salon])
def list_salons():
    with Session(engine) as session:
        return session.exec(select(Salon)).all()

@app.post("/salons", response_model=Salon)
def create_salon(payload: SalonCreate):
    salon = Salon(**payload.dict())
    with Session(engine) as session:
        session.add(salon)
        session.commit()
        session.refresh(salon)
        return salon

# -------- Products
@app.get("/products", response_model=list[Product])
def list_products():
    with Session(engine) as session:
        return session.exec(select(Product)).all()

@app.post("/products", response_model=Product)
def create_product(payload: ProductCreate):
    prod = Product(**payload.dict())
    with Session(engine) as session:
        session.add(prod)
        session.commit()
        session.refresh(prod)
        return prod
