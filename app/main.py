from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import select
from app.db import init_db, get_session
from app.models import Salon, Product, Inventory, Movement

app = FastAPI(title="Luxura Inventory")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    init_db()

@app.post("/salons")
def create_salon(salon: Salon):
    with get_session() as session:
        session.add(salon)
        session.commit()
        session.refresh(salon)
        return salon

@app.get("/salons")
def list_salons():
    with get_session() as session:
        return session.exec(select(Salon)).all()

@app.post("/products")
def create_product(product: Product):
    with get_session() as session:
        session.add(product)
        session.commit()
        session.refresh(product)
        return product

@app.get("/products")
def list_products():
    with get_session() as session:
        return session.exec(select(Product)).all()

@app.post("/movement")
def movement(type: str, salon_id: int, product_id: int, qty: int, note: str=""):
    with get_session() as session:
        inv = session.exec(select(Inventory).where(Inventory.salon_id==salon_id, Inventory.product_id==product_id)).first()
        if not inv:
            inv = Inventory(salon_id=salon_id, product_id=product_id, quantity=0)
        inv.quantity += qty
        if inv.quantity < 0:
            raise HTTPException(400, "Stock insuffisant")
        session.add(inv)
        mov = Movement(type=type, salon_id=salon_id, product_id=product_id, qty=qty, note=note)
        session.add(mov)
        session.commit()
        return {"ok": True}

@app.get("/inventory")
def inventory():
    with get_session() as session:
        return session.exec(select(Inventory)).all()
