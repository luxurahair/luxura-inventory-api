from typing import Optional, Dict, Any
from datetime import datetime

from sqlmodel import SQLModel, Field, Column
from sqlalchemy.dialects.postgresql import JSONB


class Product(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    # ID produit Wix (unique)
    wix_id: str = Field(index=True, unique=True)

    sku: Optional[str] = Field(default=None, index=True)
    name: str
    price: float = 0.0
    description: Optional[str] = None
    handle: Optional[str] = Field(default=None, index=True)

    is_in_stock: bool = True
    quantity: int = 0

    # options / variants (couleurs, longueurs etc.) stockés en JSON
    options: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSONB)
    )

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
