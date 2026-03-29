"""
BACKLINK ROUTES - Routes API FastAPI
Version: 1.0
Date: 2026-03-29

Routes pour piloter le système de backlinks depuis l'API.
"""

import asyncio
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
import logging

from .backlink_orchestrator import (
    run_full_backlink_cycle,
    run_submission_only,
    run_verification_only,
    get_backlink_status,
    get_pending_directories,
    reset_directory_status,
    list_available_directories,
    get_business_info
)
from .citation_engine import submit_to_directory, SUBMISSION_FUNCTIONS
from .email_verification import get_verification_summary

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/backlinks", tags=["backlinks"])


# =====================================================
# MODÈLES DE REQUÊTE
# =====================================================

class RunCycleRequest(BaseModel):
    directories: Optional[List[str]] = None
    verify_emails: bool = True


class SubmitDirectoryRequest(BaseModel):
    directory_key: str


# =====================================================
# ROUTES
# =====================================================

@router.get("/status")
async def get_status():
    """
    Retourne le statut global du système de backlinks.
    """
    return get_backlink_status()


@router.get("/directories")
async def list_directories():
    """
    Liste tous les annuaires disponibles.
    """
    return {
        "directories": list_available_directories(),
        "total": len(list_available_directories())
    }


@router.get("/pending")
async def get_pending():
    """
    Retourne les annuaires en attente de vérification.
    """
    pending = get_pending_directories()
    return {
        "pending": pending,
        "count": len(pending)
    }


@router.get("/verification-summary")
async def verification_summary():
    """
    Retourne un résumé des vérifications.
    """
    return get_verification_summary()


@router.get("/business-info")
async def business_info():
    """
    Retourne les informations business utilisées.
    """
    return get_business_info()


@router.post("/run")
async def run_cycle(request: RunCycleRequest, background_tasks: BackgroundTasks):
    """
    Lance un cycle complet de backlinks en arrière-plan.
    
    - Soumet aux annuaires spécifiés (ou tous par défaut)
    - Vérifie les emails si demandé
    - Retourne immédiatement avec un ID de cycle
    """
    cycle_id = f"cycle_{__import__('datetime').datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    async def run_in_background():
        try:
            await run_full_backlink_cycle(
                directories=request.directories,
                verify_emails=request.verify_emails
            )
        except Exception as e:
            logger.error(f"Erreur cycle background: {e}")
    
    # Lancer en background
    background_tasks.add_task(asyncio.create_task, run_in_background())
    
    return {
        "message": "Cycle de backlinks lancé en arrière-plan",
        "cycle_id": cycle_id,
        "directories": request.directories or list(SUBMISSION_FUNCTIONS.keys()),
        "verify_emails": request.verify_emails
    }


@router.post("/submit")
async def submit_single(request: SubmitDirectoryRequest):
    """
    Soumet à un seul annuaire.
    """
    if request.directory_key not in SUBMISSION_FUNCTIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Annuaire inconnu: {request.directory_key}. Disponibles: {list(SUBMISSION_FUNCTIONS.keys())}"
        )
    
    try:
        result = await submit_to_directory(request.directory_key)
        return {
            "directory": result.directory_name,
            "status": result.status,
            "fields_filled": result.fields_filled,
            "requires_email": result.requires_email_verification,
            "submission_url": result.submission_url,
            "notes": result.notes
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/verify-emails")
async def verify_emails(background_tasks: BackgroundTasks):
    """
    Lance la vérification des emails en arrière-plan.
    """
    async def run_verification():
        try:
            await run_verification_only()
        except Exception as e:
            logger.error(f"Erreur vérification: {e}")
    
    background_tasks.add_task(asyncio.create_task, run_verification())
    
    return {
        "message": "Vérification emails lancée en arrière-plan"
    }


@router.post("/reset/{directory_key}")
async def reset_directory(directory_key: str):
    """
    Réinitialise le statut d'un annuaire.
    """
    success = reset_directory_status(directory_key)
    
    if success:
        return {"message": f"Statut réinitialisé pour {directory_key}"}
    else:
        raise HTTPException(
            status_code=404,
            detail=f"Annuaire non trouvé: {directory_key}"
        )


@router.post("/submissions-only")
async def submissions_only(request: RunCycleRequest, background_tasks: BackgroundTasks):
    """
    Lance seulement les soumissions (sans vérification email).
    """
    async def run_submissions():
        try:
            await run_submission_only(directories=request.directories)
        except Exception as e:
            logger.error(f"Erreur soumissions: {e}")
    
    background_tasks.add_task(asyncio.create_task, run_submissions())
    
    return {
        "message": "Soumissions lancées en arrière-plan",
        "directories": request.directories or list(SUBMISSION_FUNCTIONS.keys())
    }
