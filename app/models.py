from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field

class Salon(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    address: Optional[str] = None

class Product(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    sku: str
    name: str
    length_inch: Optional[int] = None
    color: Optional[str] = None
    price: Optional[float] = None

class Inventory(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    salon_id: int
    product_id: int
    quantity: int = 0

class Movement(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    type: str
    salon_id: int
    product_id: int
    qty: int
    note: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
