from typing import Optional
from sqlmodel import SQLModel, Field

# ---- Salon
class SalonBase(SQLModel):
    name: str
    address: Optional[str] = None

class Salon(SalonBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

class SalonCreate(SalonBase):
    pass

# ---- Product
class ProductBase(SQLModel):
    sku: str
    name: str
    length_inch: Optional[int] = None
    color: Optional[str] = None
    price: Optional[float] = None

class Product(ProductBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

class ProductCreate(ProductBase):
    pass
