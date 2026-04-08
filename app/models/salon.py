from datetime import datetime, timezone
from typing import Optional

from sqlmodel import SQLModel, Field


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


class Salon(SQLModel, table=True):
    __tablename__ = "salon"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    code: Optional[str] = Field(default=None, index=True)  # ex: ONLINE, CAROUSO
    is_active: bool = Field(default=True)

    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)


class SalonCreate(SQLModel):
    name: str
    code: Optional[str] = None
    is_active: bool = True


class SalonRead(SQLModel):
    id: int
    name: str
    code: Optional[str] = None
    is_active: bool


class SalonUpdate(SQLModel):
    name: Optional[str] = None
    code: Optional[str] = None
    is_active: Optional[bool] = None
