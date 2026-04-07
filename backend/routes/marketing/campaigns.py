"""
Luxura Marketing - Routes API pour gestion des campagnes publicitaires
"""

import os
import logging
import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from dotenv import load_dotenv

load_dotenv()

# Import models
import sys
sys.path.insert(0, '/app/backend')

from models.ad_campaign import (
    AdJobInput, AdJob, AdJobResponse, AdStatus, 
    GeneratedCopy, GeneratedVideo, OfferType
)
from services.copy_generator import generate_ad_copy, get_default_fal_prompt
from services.video_generator import (
    submit_video_job, check_video_status, generate_ad_videos
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/marketing", tags=["Marketing"])

# Stockage en mémoire (à remplacer par MongoDB en prod)
AD_JOBS_DB = {}


# ============ ENDPOINTS ============

@router.get("/health")
async def health_check():
    """Health check du module marketing"""
    return {
        "status": "ok",
        "module": "luxura_marketing",
        "jobs_count": len(AD_JOBS_DB)
    }


@router.post("/jobs", response_model=AdJobResponse)
async def create_ad_job(
    input_data: AdJobInput,
    background_tasks: BackgroundTasks
):
    """
    Crée un nouveau job de génération publicitaire
    
    Le système va:
    1. Générer les textes publicitaires via OpenAI
    2. Générer les vidéos Story (9:16) et Feed (4:5) via Fal.ai
    3. Préparer le brouillon Meta (si configuré)
    """
    
    # Créer le job
    job_id = f"lux_{uuid.uuid4().hex[:12]}"
    
    job = AdJob(
        job_id=job_id,
        status=AdStatus.DRAFT,
        input=input_data
    )
    
    AD_JOBS_DB[job_id] = job.dict()
    
    # Lancer la génération en background
    background_tasks.add_task(process_ad_job, job_id)
    
    logger.info(f"Job créé: {job_id} - {input_data.offer_type}")
    
    return AdJobResponse(
        success=True,
        job_id=job_id,
        status="generating",
        message="Job créé, génération en cours..."
    )


@router.get("/jobs", response_model=List[dict])
async def list_ad_jobs(
    status: Optional[str] = None,
    offer_type: Optional[str] = None,
    limit: int = 20
):
    """Liste tous les jobs publicitaires"""
    
    jobs = list(AD_JOBS_DB.values())
    
    # Filtrer par status
    if status:
        jobs = [j for j in jobs if j.get("status") == status]
    
    # Filtrer par type d'offre
    if offer_type:
        jobs = [j for j in jobs if j.get("input", {}).get("offer_type") == offer_type]
    
    # Trier par date (plus récent en premier)
    jobs.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    
    return jobs[:limit]


@router.get("/jobs/{job_id}")
async def get_ad_job(job_id: str):
    """Récupère les détails d'un job"""
    
    if job_id not in AD_JOBS_DB:
        raise HTTPException(status_code=404, detail="Job non trouvé")
    
    return AD_JOBS_DB[job_id]


@router.post("/jobs/{job_id}/refresh-status")
async def refresh_job_status(job_id: str):
    """Rafraîchit le status des vidéos Fal.ai pour un job"""
    
    if job_id not in AD_JOBS_DB:
        raise HTTPException(status_code=404, detail="Job non trouvé")
    
    job = AD_JOBS_DB[job_id]
    updates = {}
    
    # Vérifier la vidéo Story
    if job.get("story_video") and job["story_video"].get("request_id"):
        story = job["story_video"]
        if story.get("status") not in ["COMPLETED", "FAILED"]:
            result = await check_video_status(
                story["request_id"],
                story.get("model")
            )
            story["status"] = result["status"]
            if result.get("video_url"):
                story["video_url"] = result["video_url"]
                story["file_size"] = result.get("file_size")
            updates["story"] = story["status"]
    
    # Vérifier la vidéo Feed
    if job.get("feed_video") and job["feed_video"].get("request_id"):
        feed = job["feed_video"]
        if feed.get("status") not in ["COMPLETED", "FAILED"]:
            result = await check_video_status(
                feed["request_id"],
                feed.get("model")
            )
            feed["status"] = result["status"]
            if result.get("video_url"):
                feed["video_url"] = result["video_url"]
                feed["file_size"] = result.get("file_size")
            updates["feed"] = feed["status"]
    
    # Mettre à jour le status global
    story_done = job.get("story_video", {}).get("status") == "COMPLETED"
    feed_done = job.get("feed_video", {}).get("status") == "COMPLETED"
    
    if story_done and feed_done:
        job["status"] = "ready"
    elif job.get("story_video", {}).get("status") == "FAILED" or job.get("feed_video", {}).get("status") == "FAILED":
        job["status"] = "failed"
    
    job["updated_at"] = datetime.utcnow().isoformat()
    AD_JOBS_DB[job_id] = job
    
    return {
        "success": True,
        "job_id": job_id,
        "status": job["status"],
        "updates": updates,
        "story_video": job.get("story_video"),
        "feed_video": job.get("feed_video")
    }


@router.post("/jobs/{job_id}/approve")
async def approve_ad_job(job_id: str):
    """
    Approuve un job et le prépare pour publication Meta
    (Implémentation Meta à ajouter)
    """
    
    if job_id not in AD_JOBS_DB:
        raise HTTPException(status_code=404, detail="Job non trouvé")
    
    job = AD_JOBS_DB[job_id]
    
    if job.get("status") != "ready":
        raise HTTPException(
            status_code=400, 
            detail=f"Job pas prêt. Status actuel: {job.get('status')}"
        )
    
    # TODO: Créer le brouillon Meta via l'API Graph
    # Pour l'instant, on marque juste comme approuvé
    
    job["status"] = "published"
    job["updated_at"] = datetime.utcnow().isoformat()
    AD_JOBS_DB[job_id] = job
    
    return {
        "success": True,
        "job_id": job_id,
        "status": "published",
        "message": "Job approuvé! Brouillon Meta prêt."
    }


@router.delete("/jobs/{job_id}")
async def delete_ad_job(job_id: str):
    """Supprime un job"""
    
    if job_id not in AD_JOBS_DB:
        raise HTTPException(status_code=404, detail="Job non trouvé")
    
    del AD_JOBS_DB[job_id]
    
    return {"success": True, "message": "Job supprimé"}


# ============ BACKGROUND TASK ============

async def process_ad_job(job_id: str):
    """
    Traite un job de génération publicitaire en background
    
    1. Génère les textes via OpenAI
    2. Soumet les vidéos à Fal.ai
    """
    
    if job_id not in AD_JOBS_DB:
        logger.error(f"Job {job_id} non trouvé")
        return
    
    job = AD_JOBS_DB[job_id]
    job["status"] = "generating"
    
    try:
        input_data = job["input"]
        
        # ===== ÉTAPE 1: Générer les textes =====
        logger.info(f"[{job_id}] Génération des textes...")
        
        try:
            copy = await generate_ad_copy(
                offer_type=input_data["offer_type"],
                product_name=input_data["product_name"],
                hook=input_data["hook"],
                proof=input_data.get("proof", ""),
                cta=input_data.get("cta", "Commander"),
                landing_url=input_data.get("landing_url", ""),
                audience=input_data.get("target_audience", "")
            )
            
            job["copy"] = copy
            logger.info(f"[{job_id}] Textes générés: {copy.get('headline')}")
            
        except Exception as e:
            logger.warning(f"[{job_id}] Erreur génération texte, utilisation défauts: {e}")
            # Utiliser des prompts par défaut
            story_prompt, feed_prompt = get_default_fal_prompt(
                input_data["offer_type"],
                input_data["product_name"]
            )
            copy = {
                "primary_text": input_data["hook"],
                "headline": input_data["product_name"][:40],
                "fal_prompt_story": story_prompt,
                "fal_prompt_feed": feed_prompt
            }
            job["copy"] = copy
        
        # ===== ÉTAPE 2: Soumettre les vidéos =====
        logger.info(f"[{job_id}] Soumission des vidéos Fal.ai...")
        
        # Image source si fournie
        image_url = input_data.get("images", [None])[0] if input_data.get("images") else None
        
        # Soumettre Story
        story_job = await submit_video_job(
            prompt=copy.get("fal_prompt_story", ""),
            aspect_ratio="9:16",
            duration="5",
            image_url=image_url
        )
        
        job["story_video"] = {
            "request_id": story_job["request_id"],
            "model": story_job["model"],
            "status": "IN_QUEUE",
            "format": "9:16"
        }
        
        # Soumettre Feed
        feed_job = await submit_video_job(
            prompt=copy.get("fal_prompt_feed", ""),
            aspect_ratio="4:5",
            duration="5",
            image_url=image_url
        )
        
        job["feed_video"] = {
            "request_id": feed_job["request_id"],
            "model": feed_job["model"],
            "status": "IN_QUEUE",
            "format": "4:5"
        }
        
        logger.info(f"[{job_id}] Vidéos soumises - Story: {story_job['request_id']}, Feed: {feed_job['request_id']}")
        
        job["status"] = "generating"
        job["updated_at"] = datetime.utcnow().isoformat()
        
    except Exception as e:
        logger.error(f"[{job_id}] Erreur traitement: {e}")
        job["status"] = "failed"
        job["error"] = str(e)
    
    AD_JOBS_DB[job_id] = job
