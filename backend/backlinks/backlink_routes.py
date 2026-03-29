"""
BACKLINK ROUTES - Routes API FastAPI
Version: 2.0
Date: 2026-03-29

Routes pour piloter le système de backlinks via API.
Utilise le nouvel orchestrateur clean.
"""

import asyncio
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime
import logging
import os

from .backlink_orchestrator import (
    run_backlink_cycle,
    retry_pending_verifications_only,
    load_records_from_snapshot,
    DEFAULT_OUTPUT_PATH,
)
from .citation_engine import SUBMITTERS
from .directory_registry import (
    get_active_directories,
    get_submission_queue,
    build_business_payload,
    get_directory,
)
from .email_verification import summarize_verification_results

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/backlinks", tags=["backlinks"])


# =====================================================
# MODÈLES DE REQUÊTE
# =====================================================

class RunCycleRequest(BaseModel):
    headless: bool = True
    max_directories: Optional[int] = None
    process_email_verification: bool = True
    verification_days_back: int = 7
    click_verification_links: bool = True
    save_snapshot: bool = True


class RetryVerificationRequest(BaseModel):
    verification_days_back: int = 7
    click_verification_links: bool = True
    save_snapshot: bool = False


# =====================================================
# ROUTES - STATUS & INFO
# =====================================================

@router.get("/status")
async def get_status():
    """
    Retourne le statut global du système de backlinks.
    """
    active_directories = get_active_directories()
    submission_queue = get_submission_queue()
    
    # Check if snapshot exists
    snapshot_exists = os.path.exists(DEFAULT_OUTPUT_PATH)
    last_run_info = None
    
    if snapshot_exists:
        try:
            import json
            with open(DEFAULT_OUTPUT_PATH, "r") as f:
                snapshot = json.load(f)
                last_run_info = {
                    "saved_at": snapshot.get("saved_at"),
                    "total_records": len(snapshot.get("records", [])),
                    "metadata": snapshot.get("metadata", {}),
                }
        except Exception:
            pass
    
    return {
        "system": "backlinks_v2",
        "active_directories_count": len(active_directories),
        "submission_queue_size": len(submission_queue),
        "available_submitters": list(SUBMITTERS.keys()),
        "snapshot_path": DEFAULT_OUTPUT_PATH,
        "snapshot_exists": snapshot_exists,
        "last_run": last_run_info,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/directories")
async def list_directories():
    """
    Liste tous les annuaires disponibles.
    """
    directories = get_active_directories()
    
    return {
        "directories": [
            {
                "key": d["key"],
                "name": d["name"],
                "domain": d["domain"],
                "category": d.get("category", "directory"),
                "priority": d.get("priority", 1),
                "requires_email_verification": d.get("requires_email_verification", False),
                "has_submitter": d["key"] in SUBMITTERS,
            }
            for d in directories
        ],
        "total": len(directories)
    }


@router.get("/queue")
async def get_queue():
    """
    Retourne la file d'attente de soumission triée par priorité.
    """
    queue = get_submission_queue()
    
    return {
        "queue": [
            {
                "key": d["key"],
                "name": d["name"],
                "priority": d.get("priority", 1),
                "requires_email_verification": d.get("requires_email_verification", False),
            }
            for d in queue
        ],
        "total": len(queue)
    }


@router.get("/business-info")
async def business_info():
    """
    Retourne les informations business utilisées pour les soumissions.
    """
    return build_business_payload()


# =====================================================
# ROUTES - CYCLE COMPLET
# =====================================================

@router.post("/run")
async def run_cycle(request: RunCycleRequest, background_tasks: BackgroundTasks):
    """
    Lance un cycle complet de backlinks en arrière-plan.
    
    1. Soumet aux annuaires actifs
    2. Vérifie les emails si demandé
    3. Consolide les résultats
    4. Sauvegarde un snapshot JSON
    """
    cycle_id = f"cycle_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    async def run_in_background():
        try:
            result = await run_backlink_cycle(
                headless=request.headless,
                max_directories=request.max_directories,
                process_email_verification=request.process_email_verification,
                verification_days_back=request.verification_days_back,
                click_verification_links=request.click_verification_links,
                save_snapshot=request.save_snapshot,
            )
            logger.info(f"✅ Cycle {cycle_id} terminé: {result.get('run_summary', {})}")
        except Exception as e:
            logger.error(f"❌ Erreur cycle {cycle_id}: {e}")
    
    background_tasks.add_task(asyncio.create_task, run_in_background())
    
    return {
        "message": "Cycle de backlinks lancé en arrière-plan",
        "cycle_id": cycle_id,
        "config": {
            "headless": request.headless,
            "max_directories": request.max_directories,
            "process_email_verification": request.process_email_verification,
            "verification_days_back": request.verification_days_back,
            "save_snapshot": request.save_snapshot,
        }
    }


@router.post("/retry-pending")
async def retry_pending(request: RetryVerificationRequest, background_tasks: BackgroundTasks):
    """
    Relance la vérification email pour les records en attente.
    Charge les records depuis le dernier snapshot.
    """
    if not os.path.exists(DEFAULT_OUTPUT_PATH):
        raise HTTPException(
            status_code=404,
            detail="Aucun snapshot trouvé. Lancez d'abord un cycle complet avec /run."
        )
    
    try:
        records = load_records_from_snapshot(DEFAULT_OUTPUT_PATH)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur chargement snapshot: {str(e)}"
        )
    
    async def run_in_background():
        try:
            result = await retry_pending_verifications_only(
                records=records,
                verification_days_back=request.verification_days_back,
                click_verification_links=request.click_verification_links,
                save_snapshot=request.save_snapshot,
            )
            logger.info(f"✅ Retry terminé: {result.get('verification_summary', {})}")
        except Exception as e:
            logger.error(f"❌ Erreur retry: {e}")
    
    background_tasks.add_task(asyncio.create_task, run_in_background())
    
    return {
        "message": "Relance des vérifications en arrière-plan",
        "records_loaded": len(records),
        "config": {
            "verification_days_back": request.verification_days_back,
            "click_verification_links": request.click_verification_links,
            "save_snapshot": request.save_snapshot,
        }
    }


# =====================================================
# ROUTES - SNAPSHOT & RÉSULTATS
# =====================================================

@router.get("/latest-run")
async def get_latest_run():
    """
    Retourne les résultats du dernier cycle (depuis le snapshot JSON).
    """
    if not os.path.exists(DEFAULT_OUTPUT_PATH):
        raise HTTPException(
            status_code=404,
            detail="Aucun snapshot trouvé. Lancez d'abord un cycle complet avec /run."
        )
    
    try:
        import json
        with open(DEFAULT_OUTPUT_PATH, "r") as f:
            snapshot = json.load(f)
        
        return {
            "saved_at": snapshot.get("saved_at"),
            "metadata": snapshot.get("metadata", {}),
            "run_summary": snapshot.get("run_summary", {}),
            "records_count": len(snapshot.get("records", [])),
            "records": snapshot.get("records", [])[:20],  # Limite à 20 pour l'API
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lecture snapshot: {str(e)}"
        )


@router.get("/latest-run/summary")
async def get_latest_run_summary():
    """
    Retourne un résumé condensé du dernier cycle.
    """
    if not os.path.exists(DEFAULT_OUTPUT_PATH):
        raise HTTPException(
            status_code=404,
            detail="Aucun snapshot trouvé."
        )
    
    try:
        import json
        with open(DEFAULT_OUTPUT_PATH, "r") as f:
            snapshot = json.load(f)
        
        records = snapshot.get("records", [])
        
        # Calculer les comptages
        counts = {
            "total": len(records),
            "submitted": 0,
            "email_pending": 0,
            "email_found": 0,
            "verification_clicked": 0,
            "verified": 0,
            "live": 0,
            "failed": 0,
            "skipped": 0,
        }
        
        for r in records:
            status = r.get("status", "unknown")
            if status in counts:
                counts[status] += 1
        
        return {
            "saved_at": snapshot.get("saved_at"),
            "counts": counts,
            "success_rate": round((counts["verified"] + counts["live"]) / max(counts["total"], 1) * 100, 1),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lecture snapshot: {str(e)}"
        )


@router.delete("/snapshot")
async def delete_snapshot():
    """
    Supprime le snapshot actuel.
    """
    if not os.path.exists(DEFAULT_OUTPUT_PATH):
        raise HTTPException(
            status_code=404,
            detail="Aucun snapshot à supprimer."
        )
    
    try:
        os.remove(DEFAULT_OUTPUT_PATH)
        return {"message": "Snapshot supprimé", "path": DEFAULT_OUTPUT_PATH}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur suppression: {str(e)}"
        )
