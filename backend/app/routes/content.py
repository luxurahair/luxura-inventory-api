"""
Routes API pour le système de contenu automatisé
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel
from datetime import datetime

from app.services.content_pipeline import ContentPipeline
from app.services.content_discovery import ContentDiscoveryService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/content", tags=["Content Automation"])


# ============================================
# SCHEMAS
# ============================================

class ScanResponse(BaseModel):
    success: bool
    timestamp: str
    articles_found: int
    articles_relevant: int
    posts_generated: int
    images_generated: int = 0
    posts: List[dict]
    errors: List[str] = []


class PostStatusUpdate(BaseModel):
    status: str  # draft, approved, rejected, published


# ============================================
# ENDPOINTS
# ============================================

@router.post("/ingest/hair-canada", response_model=ScanResponse)
async def ingest_hair_canada_news(
    max_posts: int = Query(default=3, le=10, description="Nombre max de posts à générer"),
    generate_images: bool = Query(default=True, description="Générer les images DALL-E 3"),
    background_tasks: BackgroundTasks = None
):
    """
    🚀 Lance un scan des actualités extensions capillaires Canada
    
    Processus:
    1. Collecte Google News Canada
    2. Filtrage pertinence (extensions, rallonges, hair)
    3. Dédoublonnage
    4. Traduction FR
    5. Génération posts Facebook avec GPT-4o
    6. 🎨 Génération images DALL-E 3 (optionnel)
    7. Sauvegarde en brouillon
    
    Args:
        max_posts: Nombre max de posts (1-10)
        generate_images: Si True, génère des images DALL-E 3 pour chaque post
    
    Returns:
        Posts générés avec images
    """
    logger.info(f"🚀 Lancement scan contenu (max_posts={max_posts}, images={generate_images})")
    
    try:
        pipeline = ContentPipeline()
        results = await pipeline.run_daily_scan(
            max_posts=max_posts,
            generate_images=generate_images
        )
        
        return ScanResponse(
            success=True,
            timestamp=results["timestamp"],
            articles_found=results["articles_found"],
            articles_relevant=results["articles_relevant"],
            posts_generated=results["posts_generated"],
            images_generated=results.get("images_generated", 0),
            posts=results["posts"],
            errors=results["errors"]
        )
        
    except Exception as e:
        logger.error(f"Erreur scan: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sources")
async def list_content_sources():
    """
    📚 Liste les sources de contenu configurées
    """
    from app.services.content_sources import (
        SEARCH_QUERIES, TRUSTED_SOURCES, INCLUDE_KEYWORDS
    )
    
    return {
        "search_queries": SEARCH_QUERIES,
        "trusted_sources": TRUSTED_SOURCES[:20],
        "include_keywords_count": len(INCLUDE_KEYWORDS),
        "description": "Sources utilisées pour la collecte de contenu extensions capillaires"
    }


@router.get("/posts/facebook")
async def list_facebook_posts(
    status: Optional[str] = Query(default=None, description="Filtrer par status"),
    limit: int = Query(default=20, le=100)
):
    """
    📱 Liste les posts Facebook générés
    
    TODO: Implémenter avec base de données
    """
    return {
        "posts": [],
        "total": 0,
        "status_filter": status,
        "note": "Base de données non encore connectée"
    }


@router.patch("/posts/{post_id}/status")
async def update_post_status(
    post_id: str,
    update: PostStatusUpdate
):
    """
    ✏️ Met à jour le status d'un post
    
    Statuts possibles:
    - draft: Brouillon
    - approved: Approuvé pour publication
    - rejected: Rejeté
    - published: Publié
    
    TODO: Implémenter avec base de données
    """
    valid_statuses = ["draft", "approved", "rejected", "published"]
    
    if update.status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Status invalide. Valides: {valid_statuses}"
        )
    
    return {
        "post_id": post_id,
        "new_status": update.status,
        "updated_at": datetime.now().isoformat(),
        "note": "Base de données non encore connectée"
    }


@router.post("/posts/{post_id}/publish")
async def publish_post(post_id: str):
    """
    📤 Publie un post sur Facebook
    
    Prérequis:
    - Le post doit avoir le status "approved"
    - FB_PAGE_ACCESS_TOKEN configuré
    
    TODO: Implémenter avec facebook_publisher.py
    """
    return {
        "post_id": post_id,
        "status": "not_implemented",
        "message": "Publication Facebook à implémenter"
    }


@router.post("/jobs/daily-run")
async def trigger_daily_job(background_tasks: BackgroundTasks):
    """
    ⏰ Déclenche le job quotidien de contenu
    
    Même que POST /ingest/hair-canada mais en tâche de fond
    """
    async def run_job():
        pipeline = ContentPipeline()
        await pipeline.run_daily_scan(max_posts=3)
    
    background_tasks.add_task(run_job)
    
    return {
        "status": "started",
        "message": "Job quotidien démarré en arrière-plan"
    }
