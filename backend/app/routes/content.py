"""
Routes API pour le système de contenu automatisé
Inclut le nouveau générateur de contenu Magazine Féminin
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel
from datetime import datetime

from app.services.content_pipeline import ContentPipeline
from app.services.content_discovery import ContentDiscoveryService
from app.services.magazine_content_generator import MagazineContentGenerator, get_jour_semaine_fr

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


class MagazinePostResponse(BaseModel):
    success: bool
    theme: str
    theme_name: str
    country_inspiration: str
    title: str
    full_text: str
    image_prompt: str
    fallback_image_url: str
    hashtags: List[str]
    day_fr: str
    generated_at: str


class PostStatusUpdate(BaseModel):
    status: str  # draft, approved, rejected, published


# ============================================
# ENDPOINTS - MAGAZINE CONTENT (NOUVEAU)
# ============================================

@router.post("/magazine/generate", response_model=MagazinePostResponse)
async def generate_magazine_post(
    theme: str = Query(default="auto", description="Thème du post: tendance_coupe, comparatif_extensions, conseils_erreurs, quiet_luxury, inspiration_internationale ou 'auto'"),
    country: str = Query(default="auto", description="Pays d'inspiration: france, italy, usa, uk ou 'auto'")
):
    """
    🎨 Génère un post Facebook style MAGAZINE FÉMININ
    
    Thèmes disponibles:
    - tendance_coupe: Décryptage bob, lob, frange
    - comparatif_extensions: Halo vs tape-in vs weft
    - conseils_erreurs: Erreurs à éviter, conseils pro
    - quiet_luxury: Tendance cheveux glossy/luxe
    - inspiration_internationale: Tendances Paris, Milan, NYC
    
    Inspirations:
    - france: Style parisien/français
    - italy: Style milanais/italien
    - usa: Style new-yorkais/américain
    - uk: Style londonien/britannique
    
    Retourne un post complet avec texte, prompt image, et hashtags.
    """
    logger.info(f"🎨 Génération post magazine: theme={theme}, country={country}")
    
    try:
        generator = MagazineContentGenerator()
        result = await generator.generate_magazine_post(theme=theme, country_inspiration=country)
        
        return MagazinePostResponse(
            success=True,
            theme=result["theme"],
            theme_name=result["theme_name"],
            country_inspiration=result["country_inspiration"],
            title=result["title"],
            full_text=result["full_text"],
            image_prompt=result["image_prompt"],
            fallback_image_url=result["fallback_image_url"],
            hashtags=result["hashtags"],
            day_fr=result["day_fr"],
            generated_at=result["generated_at"]
        )
        
    except Exception as e:
        logger.error(f"Erreur génération magazine: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/magazine/themes")
async def list_magazine_themes():
    """
    📚 Liste les thèmes magazine disponibles
    """
    from app.services.content_sources import MAGAZINE_THEMES
    
    themes = []
    for key, config in MAGAZINE_THEMES.items():
        themes.append({
            "id": key,
            "name": config["name"],
            "description": config["description"],
            "tone": config["tone"],
            "example_titles": config.get("example_titles", [])[:3]
        })
    
    return {
        "themes": themes,
        "countries": [
            {"id": "france", "name": "France (Paris)"},
            {"id": "italy", "name": "Italie (Milan)"},
            {"id": "usa", "name": "USA (New York)"},
            {"id": "uk", "name": "UK (Londres)"},
        ],
        "today_theme": "auto",
        "today_day_fr": get_jour_semaine_fr()
    }


@router.get("/magazine/week-plan")
async def get_week_content_plan():
    """
    📅 Génère un plan de contenu pour la semaine
    """
    generator = MagazineContentGenerator()
    week_plan = await generator.generate_week_content_plan()
    
    return {
        "week_plan": week_plan,
        "current_day": get_jour_semaine_fr(),
        "description": "Plan éditorial suggéré pour la semaine"
    }


@router.post("/magazine/batch-generate")
async def batch_generate_magazine_posts(
    count: int = Query(default=3, le=7, description="Nombre de posts à générer"),
    background_tasks: BackgroundTasks = None
):
    """
    📦 Génère plusieurs posts magazine en lot
    
    Utile pour préparer une semaine de contenu.
    Chaque post aura un thème et pays différent.
    """
    logger.info(f"📦 Génération batch: {count} posts magazine")
    
    themes = ["tendance_coupe", "comparatif_extensions", "conseils_erreurs", "quiet_luxury", "inspiration_internationale"]
    countries = ["france", "italy", "usa", "uk"]
    
    posts = []
    generator = MagazineContentGenerator()
    
    for i in range(count):
        theme = themes[i % len(themes)]
        country = countries[i % len(countries)]
        
        try:
            result = await generator.generate_magazine_post(theme=theme, country_inspiration=country)
            posts.append({
                "index": i + 1,
                "theme": result["theme"],
                "country": result["country_inspiration"],
                "title": result["title"],
                "full_text": result["full_text"],
                "image_prompt": result["image_prompt"],
                "hashtags": result["hashtags"]
            })
        except Exception as e:
            logger.error(f"Erreur post {i+1}: {e}")
            posts.append({
                "index": i + 1,
                "error": str(e)
            })
    
    return {
        "success": True,
        "posts_generated": len([p for p in posts if "error" not in p]),
        "posts": posts
    }


# ============================================
# ENDPOINTS - SCAN CLASSIQUE
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
