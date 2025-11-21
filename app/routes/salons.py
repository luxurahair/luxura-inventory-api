# app/routes/salons.py

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db import get_session
from app.models import Salon, SalonCreate, SalonRead, SalonUpdate

router = APIRouter()


# ─────────────────────────────────────────
# Routes CRUD Salons
# ─────────────────────────────────────────

@router.post(
    "/",
    response_model=SalonRead,
    summary="Créer un salon",
)
def create_salon(
    salon_in: SalonCreate,
    session: Session = Depends(get_session),
) -> SalonRead:
    """Créer un nouveau salon."""
    salon = Salon(**salon_in.model_dump())
    session.add(salon)
    session.commit()
    session.refresh(salon)
    return salon


@router.get(
    "/",
    response_model=List[SalonRead],
    summary="Lister tous les salons",
)
def list_salons(
    session: Session = Depends(get_session),
) -> List[SalonRead]:
    """Lister tous les salons."""
    salons = session.exec(select(Salon)).all()
    return salons


@router.get(
    "/{salon_id}",
    response_model=SalonRead,
    summary="Récupérer un salon",
)
def get_salon(
    salon_id: int,
    session: Session = Depends(get_session),
) -> SalonRead:
    """Récupérer un salon par son ID."""
    salon = session.get(Salon, salon_id)
    if not salon:
        raise HTTPException(status_code=404, detail="Salon introuvable")
    return salon


@router.put(
    "/{salon_id}",
    response_model=SalonRead,
    summary="Mettre à jour un salon",
)
def update_salon(
    salon_id: int,
    salon_in: SalonUpdate,
    session: Session = Depends(get_session),
) -> SalonRead:
    """Mettre à jour un salon existant."""
    salon = session.get(Salon, salon_id)
    if not salon:
        raise HTTPException(status_code=404, detail="Salon introuvable")

    data = salon_in.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(salon, key, value)

    session.add(salon)
    session.commit()
    session.refresh(salon)
    return salon


@router.delete(
    "/{salon_id}",
    summary="Supprimer un salon",
)
def delete_salon(
    salon_id: int,
    session: Session = Depends(get_session),
) -> dict:
    """Supprimer un salon par son ID."""
    salon = session.get(Salon, salon_id)
    if not salon:
        raise HTTPException(status_code=404, detail="Salon introuvable")

    session.delete(salon)
    session.commit()
    return {"ok": True}

