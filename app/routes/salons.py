from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db import get_session
from app.models import Salon, SalonCreate, SalonRead, SalonUpdate

router = APIRouter(
    prefix="/salons",
    tags=["salons"],
)

SessionDep = Depends(get_session)


@router.get(
    "",
    response_model=List[SalonRead],
    summary="Lister tous les salons",
)
def list_salons(
    session: Session = SessionDep,
) -> List[SalonRead]:
    """
    Retourne la liste complète des salons.
    Aucun paramètre requis -> ne peut PAS renvoyer 422.
    """
    salons = session.exec(select(Salon)).all()
    return salons


@router.get(
    "/{salon_id}",
    response_model=SalonRead,
    summary="Récupérer un salon",
)
def get_salon(
    salon_id: int,
    session: Session = SessionDep,
) -> SalonRead:
    """Récupérer un salon par son ID."""
    salon = session.get(Salon, salon_id)
    if not salon:
        raise HTTPException(status_code=404, detail="Salon introuvable")
    return salon


@router.post(
    "",
    response_model=SalonRead,
    status_code=201,
    summary="Créer un salon",
)
def create_salon(
    payload: SalonCreate,
    session: Session = SessionDep,
) -> SalonRead:
    """Créer un nouveau salon."""
    salon = Salon.from_orm(payload)
    session.add(salon)
    session.commit()
    session.refresh(salon)
    return salon


@router.put(
    "/{salon_id}",
    response_model=SalonRead,
    summary="Mettre à jour un salon",
)
def update_salon(
    salon_id: int,
    payload: SalonUpdate,
    session: Session = SessionDep,
) -> SalonRead:
    """Mettre à jour un salon existant."""
    salon = session.get(Salon, salon_id)
    if not salon:
        raise HTTPException(status_code=404, detail="Salon introuvable")

    data = payload.dict(exclude_unset=True)
    for key, value in data.items():
        setattr(salon, key, value)

    session.add(salon)
    session.commit()
    session.refresh(salon)
    return salon


@router.delete(
    "/{salon_id}",
    status_code=204,
    summary="Supprimer un salon",
)
def delete_salon(
    salon_id: int,
    session: Session = SessionDep,
) -> None:
    """Supprimer un salon."""
    salon = session.get(Salon, salon_id)
    if not salon:
        raise HTTPException(status_code=404, detail="Salon introuvable")
    session.delete(salon)
    session.commit()
