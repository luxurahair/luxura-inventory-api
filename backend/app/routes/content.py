"""
Routes API pour le système de contenu automatisé
Inclut le nouveau générateur de contenu Magazine Féminin
+ Système d'approbation avec publication Facebook
+ Stockage PostgreSQL pour persistence cross-server
"""

import logging
import json
import os
import httpx
from typing import List, Optional, Dict
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from datetime import datetime
from pathlib import Path

from app.services.content_pipeline import ContentPipeline
from app.services.content_discovery import ContentDiscoveryService
from app.services.magazine_content_generator import MagazineContentGenerator, get_jour_semaine_fr
from app.services.facebook_publisher import FacebookPublisher

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/content", tags=["Content Automation"])

# ============================================
# STOCKAGE DES POSTS - REDIS-LIKE VIA API
# Pour que Render puisse accéder aux posts créés localement
# ============================================

# URL de l'API Render (pour sync des posts)
RENDER_API_URL = os.getenv("RENDER_API_URL", "https://luxura-inventory-api.onrender.com")

# Stockage local + remote sync
PENDING_POSTS_FILE = Path("/tmp/luxura_pending_posts.json")

# Cache en mémoire pour accès rapide
_pending_posts_cache: Dict = {}


def load_pending_posts_from_db() -> Dict:
    """Charge les posts en attente depuis Supabase"""
    try:
        import psycopg2
        DATABASE_URL = os.environ.get('DATABASE_URL', '')
        if DATABASE_URL.startswith("postgres://"):
            DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
        if DATABASE_URL.startswith("postgresql+psycopg://"):
            DATABASE_URL = DATABASE_URL.replace("postgresql+psycopg://", "postgresql://", 1)
        
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("""
            SELECT post_id, post_data 
            FROM pending_posts 
            WHERE status = 'pending'
            AND created_at > NOW() - INTERVAL '7 days'
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return {row[0]: row[1] for row in rows}
    except Exception as e:
        logger.warning(f"DB load failed, using file fallback: {e}")
        return {}


def save_pending_post_to_db(post_id: str, post_data: Dict):
    """Sauvegarde un post en attente dans Supabase"""
    try:
        import psycopg2
        DATABASE_URL = os.environ.get('DATABASE_URL', '')
        if DATABASE_URL.startswith("postgres://"):
            DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
        if DATABASE_URL.startswith("postgresql+psycopg://"):
            DATABASE_URL = DATABASE_URL.replace("postgresql+psycopg://", "postgresql://", 1)
        
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        from psycopg2.extras import Json
        cur.execute("""
            INSERT INTO pending_posts (post_id, post_data, status, created_at)
            VALUES (%s, %s, 'pending', NOW())
            ON CONFLICT (post_id) 
            DO UPDATE SET post_data = %s, status = 'pending', created_at = NOW()
        """, (post_id, Json(post_data), Json(post_data)))
        conn.commit()
        cur.close()
        conn.close()
        logger.info(f"✅ Post {post_id} sauvegardé en DB")
    except Exception as e:
        logger.warning(f"DB save failed: {e}")


def mark_post_processed_in_db(post_id: str):
    """Marque un post comme traité dans Supabase"""
    try:
        from database import get_connection
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE pending_posts 
                    SET status = 'processed', processed_at = NOW()
                    WHERE post_id = %s
                """, (post_id,))
                conn.commit()
    except Exception as e:
        logger.warning(f"DB mark processed failed: {e}")


def load_pending_posts() -> Dict:
    """Charge les posts en attente (DB > cache > fichier)"""
    global _pending_posts_cache
    
    # D'abord essayer la base de données (persistant)
    db_posts = load_pending_posts_from_db()
    if db_posts:
        _pending_posts_cache = db_posts.copy()
        return db_posts
    
    # Sinon essayer le cache mémoire
    if _pending_posts_cache:
        return _pending_posts_cache.copy()
    
    # Sinon charger depuis le fichier (fallback)
    try:
        if PENDING_POSTS_FILE.exists():
            with open(PENDING_POSTS_FILE, 'r') as f:
                _pending_posts_cache = json.load(f)
                return _pending_posts_cache.copy()
    except Exception as e:
        logger.error(f"Erreur chargement pending posts: {e}")
    
    return {}


def save_pending_posts(posts: Dict):
    """Sauvegarde les posts en attente (DB + fichier fallback)"""
    global _pending_posts_cache
    _pending_posts_cache = posts.copy()
    
    # Sauvegarder chaque post en DB
    for post_id, post_data in posts.items():
        save_pending_post_to_db(post_id, post_data)
    
    # Aussi sauvegarder en fichier (fallback)
    try:
        with open(PENDING_POSTS_FILE, 'w') as f:
            json.dump(posts, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Erreur sauvegarde pending posts fichier: {e}")


def add_pending_post(post_id: str, post_data: Dict):
    """Ajoute un post en attente (DB + cache + fichier)"""
    global _pending_posts_cache
    
    post_with_meta = {
        **post_data,
        "created_at": datetime.now().isoformat(),
        "status": "pending"
    }
    
    # Sauvegarder en DB d'abord (persistant)
    save_pending_post_to_db(post_id, post_with_meta)
    
    # Mettre à jour le cache
    posts = load_pending_posts()
    posts[post_id] = post_with_meta
    _pending_posts_cache = posts.copy()
    
    # Aussi sauvegarder en fichier (fallback)
    try:
        with open(PENDING_POSTS_FILE, 'w') as f:
            json.dump(posts, f, indent=2, ensure_ascii=False)
    except:
        pass
    
    logger.info(f"📝 Post {post_id} ajouté en attente d'approbation (DB + cache)")


async def sync_post_to_render(post_id: str, post_data: Dict):
    """Synchronise un post vers Render pour persistence"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(
                f"{RENDER_API_URL}/api/content/sync-post",
                json={"post_id": post_id, "post_data": post_data}
            )
            logger.info(f"✅ Post {post_id} synced to Render")
    except Exception as e:
        logger.warning(f"Sync to Render failed (normal si local): {e}")


def get_pending_post(post_id: str) -> Optional[Dict]:
    """Récupère un post en attente (DB > cache > fichier)"""
    global _pending_posts_cache
    
    # D'abord vérifier le cache mémoire
    if post_id in _pending_posts_cache:
        return _pending_posts_cache[post_id]
    
    # Ensuite vérifier la base de données (persistant)
    try:
        import psycopg2
        DATABASE_URL = os.environ.get('DATABASE_URL', '')
        if DATABASE_URL.startswith("postgres://"):
            DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
        if DATABASE_URL.startswith("postgresql+psycopg://"):
            DATABASE_URL = DATABASE_URL.replace("postgresql+psycopg://", "postgresql://", 1)
        
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("""
            SELECT post_data 
            FROM pending_posts 
            WHERE post_id = %s AND status = 'pending'
        """, (post_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        
        if row:
            post_data = row[0] if isinstance(row[0], dict) else json.loads(row[0])
            _pending_posts_cache[post_id] = post_data
            logger.info(f"✅ Post {post_id} récupéré depuis DB")
            return post_data
    except Exception as e:
        logger.warning(f"DB lookup failed: {e}")
    
    # Sinon charger depuis fichier
    posts = load_pending_posts()
    if post_id in posts:
        return posts[post_id]
    
    return None
    return posts.get(post_id)


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


# ============================================
# 🌍 SCAN INTERNATIONAL - MODE FÉMININE
# ============================================

@router.post("/scan-international")
async def scan_international_content(
    max_posts: int = Query(default=3, le=5, description="Nombre max de posts à générer"),
    send_email: bool = Query(default=True, description="Envoyer email d'approbation"),
    background_tasks: BackgroundTasks = None
):
    """
    🌍 SCAN INTERNATIONAL - Tendances Mode Féminine
    
    Scrute les actualités mode féminine de:
    - 🇫🇷 France (Paris, Elle, Vogue)
    - 🇮🇹 Italie (Milan, Grazia)
    - 🇺🇸 USA (New York, Allure, Glamour)
    - 🇬🇧 UK (Londres, Harper's Bazaar)
    - 🇨🇦 Canada (Montréal, Fashion Magazine)
    
    Rotation automatique des pays par jour de la semaine.
    
    Processus:
    1. Scrutation Google News par pays
    2. Filtrage articles mode féminine/coiffure
    3. Traduction française (GPT-4o)
    4. Génération image contextuelle (Grok)
    5. Ajout watermark LUXURA doré
    6. Email approbation → Publication Facebook
    """
    logger.info(f"🌍 Lancement scan international (max_posts={max_posts})")
    
    try:
        from app.services.international_content_scanner import InternationalContentScanner, COUNTRY_CONFIG
        from app.services.watermark import process_image_with_watermark
        from app.services.email_approval import send_approval_email
        
        scanner = InternationalContentScanner()
        countries = scanner.get_todays_countries()
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "countries_scanned": [COUNTRY_CONFIG[c]["name"] for c in countries],
            "countries_flags": [COUNTRY_CONFIG[c]["flag"] for c in countries],
            "articles_found": 0,
            "posts_generated": 0,
            "posts": [],
            "errors": []
        }
        
        logger.info(f"🌍 Pays du jour: {', '.join([COUNTRY_CONFIG[c]['flag'] + ' ' + COUNTRY_CONFIG[c]['name'] for c in countries])}")
        
        # 1. Scanner les actualités
        articles = await scanner.scan_international_news(max_per_country=5)
        results["articles_found"] = len(articles)
        
        if not articles:
            logger.warning("Aucun article trouvé")
            return results
        
        # 2. Générer les posts
        for article in articles[:max_posts]:
            try:
                logger.info(f"📝 Génération: {article['country_flag']} {article['title'][:50]}...")
                
                # Générer le post complet (traduit + image Grok)
                post = await scanner.generate_luxura_post(article)
                
                # 3. Ajouter watermark LUXURA
                if post.get("image_url"):
                    logger.info(f"🏷️ Ajout watermark LUXURA...")
                    try:
                        watermarked_bytes = await process_image_with_watermark(post["image_url"])
                        if watermarked_bytes:
                            post["watermarked_image_bytes"] = watermarked_bytes
                            post["has_watermark"] = True
                            logger.info(f"   ✅ Watermark ajouté ({len(watermarked_bytes)} bytes)")
                    except Exception as wm_err:
                        logger.warning(f"   ⚠️ Watermark erreur: {wm_err}")
                        post["has_watermark"] = False
                
                results["posts"].append(post)
                results["posts_generated"] += 1
                
                # 4. Marquer l'article comme traité dans l'historique (anti-répétition)
                from app.services.international_content_scanner import mark_article_as_published
                mark_article_as_published(
                    article["title"], 
                    article.get("url", ""), 
                    article["country"]
                )
                
                # 5. Envoyer email d'approbation
                if send_email:
                    full_text = post["post_text"]
                    if post.get("hashtags"):
                        full_text += "\n\n" + " ".join(post["hashtags"])
                    
                    post_data = {
                        "text": post["post_text"],
                        "full_text": full_text,
                        "hashtags": post.get("hashtags", []),
                        "image_url": post.get("image_url"),
                        "source_title": f"{post['country_flag']} {post['title_fr'][:50]}",
                        "source_url": post["source_url"],
                        "country": post["country"],
                    }
                    
                    try:
                        email_result = await send_approval_email(post_data)
                        
                        if email_result.get("success"):
                            post_id = email_result.get("post_id")
                            # Sauvegarder le post avec watermark pour l'approbation
                            add_pending_post(post_id, {
                                **post_data,
                                "watermarked_image_bytes": post.get("watermarked_image_bytes"),
                                "has_watermark": post.get("has_watermark", False),
                            })
                            post["post_id"] = post_id
                            post["email_sent"] = True
                            logger.info(f"   📧 Email envoyé! ID: {post_id}")
                        else:
                            post["email_sent"] = False
                            logger.warning(f"   ⚠️ Email non envoyé")
                    except Exception as email_err:
                        post["email_sent"] = False
                        logger.warning(f"   ⚠️ Erreur email: {email_err}")
                
                # Nettoyer les bytes avant de retourner (trop gros pour JSON)
                if "watermarked_image_bytes" in post:
                    del post["watermarked_image_bytes"]
                
                logger.info(f"   ✅ Post généré: {post['country_flag']} {post['title_fr'][:40]}...")
                
            except Exception as e:
                logger.error(f"   ❌ Erreur: {e}")
                results["errors"].append(str(e))
        
        logger.info(f"🌍 Scan terminé: {results['posts_generated']} posts générés")
        return results
        
    except Exception as e:
        logger.error(f"Erreur scan international: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/international/countries")
async def list_international_countries():
    """
    🌍 Liste les pays configurés pour le scan international
    """
    from app.services.international_content_scanner import COUNTRY_CONFIG, DAILY_COUNTRY_ROTATION
    
    countries = []
    for code, config in COUNTRY_CONFIG.items():
        countries.append({
            "code": code,
            "name": config["name"],
            "flag": config["flag"],
            "city": config["city"],
            "language": config["language"],
            "queries_count": len(config["queries"]),
            "sources_count": len(config["sources"]),
        })
    
    # Pays du jour
    from datetime import datetime
    day = datetime.now().weekday()
    today_countries = DAILY_COUNTRY_ROTATION.get(day, ["france", "usa"])
    
    return {
        "countries": countries,
        "today_countries": today_countries,
        "today_countries_names": [COUNTRY_CONFIG[c]["flag"] + " " + COUNTRY_CONFIG[c]["name"] for c in today_countries],
        "rotation": {
            "lundi": ["france", "italy"],
            "mardi": ["usa", "uk"],
            "mercredi": ["france", "canada"],
            "jeudi": ["italy", "usa"],
            "vendredi": ["uk", "france"],
            "samedi": ["usa", "italy"],
            "dimanche": ["france", "uk"],
        }
    }


@router.get("/international/history")
async def get_published_articles_history():
    """
    📜 Historique des articles publiés (30 derniers jours)
    
    Permet de voir les articles déjà traités pour éviter les répétitions.
    """
    from app.services.international_content_scanner import load_article_history
    
    history = load_article_history()
    articles = history.get("articles", {})
    
    # Formatter pour affichage
    published_articles = []
    for key, data in articles.items():
        if "title" in data:  # Seulement les entrées avec titre (pas les hashes d'URL)
            published_articles.append({
                "title": data.get("title"),
                "country": data.get("country"),
                "published_at": data.get("published_at"),
            })
    
    # Trier par date (plus récent en premier)
    published_articles.sort(key=lambda x: x.get("published_at", ""), reverse=True)
    
    return {
        "total_articles": len(published_articles),
        "history_days": 30,
        "last_run": history.get("last_run"),
        "articles": published_articles[:50]  # Max 50 pour la réponse
    }


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


# ============================================
# ENDPOINTS - APPROBATION & PUBLICATION FACEBOOK
# ============================================

@router.post("/sync-post")
async def sync_post_from_external(post_id: str = None, post_data: Dict = None):
    """
    🔄 Endpoint pour synchroniser un post depuis un autre serveur
    Permet de persister les posts créés localement vers Render
    """
    if not post_id or not post_data:
        raise HTTPException(status_code=400, detail="post_id et post_data requis")
    
    global _pending_posts_cache
    _pending_posts_cache[post_id] = post_data
    save_pending_posts(_pending_posts_cache)
    
    logger.info(f"🔄 Post {post_id} synchronisé depuis externe")
    return {"success": True, "post_id": post_id}


@router.get("/approve/{post_id}", response_class=HTMLResponse)
async def approve_post(post_id: str):
    """
    ✅ Approuve un post et le publie sur Facebook
    
    Processus:
    1. Récupère le post en attente
    2. Ajoute le logo Luxura à l'image
    3. Ajoute les liens luxuradistribution.com
    4. Publie sur Facebook
    """
    logger.info(f"✅ Approbation reçue pour post: {post_id}")
    
    # Récupérer le post en attente
    post = get_pending_post(post_id)
    
    if not post:
        logger.warning(f"Post {post_id} non trouvé dans les pending")
        return HTMLResponse(content=f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Post non trouvé</title>
            <style>
                body {{ font-family: -apple-system, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; background: #f5f5f5; }}
                .container {{ text-align: center; padding: 40px; background: white; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                h1 {{ color: #dc3545; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>⚠️ Post non trouvé</h1>
                <p>Le post <code>{post_id}</code> n'existe pas ou a déjà été traité.</p>
                <p>Il a peut-être déjà été publié ou rejeté.</p>
            </div>
        </body>
        </html>
        """, status_code=404)
    
    # Publier sur Facebook
    try:
        publisher = FacebookPublisher()
        
        # Préparer le texte avec liens et hashtags
        full_text = post.get("text", post.get("full_text", ""))
        
        # Ajouter le lien du site si pas déjà présent
        if "luxuradistribution.com" not in full_text.lower():
            full_text += "\n\n🌐 luxuradistribution.com"
        
        # Ajouter les hashtags Luxura obligatoires
        hashtags = post.get("hashtags", [])
        luxura_hashtags = ["#LuxuraDistribution", "#ExtensionsCheveux", "#Québec"]
        
        # Fusionner les hashtags
        all_hashtags = list(set(hashtags + luxura_hashtags))[:7]  # Max 7 hashtags
        
        if all_hashtags:
            # Vérifier si les hashtags ne sont pas déjà dans le texte
            if "#LuxuraDistribution" not in full_text:
                full_text += "\n\n" + " ".join(all_hashtags)
        
        image_url = post.get("image_url", post.get("fallback_image_url"))
        
        # ============================================
        # AJOUTER LE LOGO LUXURA À L'IMAGE
        # ============================================
        final_image_url = image_url
        
        if image_url:
            try:
                from app.services.watermark import process_image_with_watermark
                
                logger.info(f"🏷️ Ajout du watermark doré LUXURA sur l'image...")
                
                # Créer l'image avec watermark doré
                image_bytes = await process_image_with_watermark(image_url)
                
                if image_bytes:
                    logger.info(f"✅ Watermark doré ajouté! Taille: {len(image_bytes)} bytes")
                else:
                    logger.warning("Watermark non ajouté, utilisation image originale")
                    image_bytes = None
                    
            except Exception as e:
                logger.warning(f"Erreur ajout watermark: {e} - utilisation image originale")
                image_bytes = None
        else:
            image_bytes = None
        
        logger.info(f"📘 Publication Facebook: {len(full_text)} caractères, image: {bool(image_url)}")
        
        # Publier (avec image bytes si logo ajouté, sinon URL)
        if image_bytes:
            success, fb_post_id, error = await publisher.publish_post_with_image_bytes(
                full_text, 
                image_bytes
            )
        else:
            success, fb_post_id, error = await publisher.publish_post(full_text, image_url)
        
        if success:
            # Mettre à jour le status
            posts = load_pending_posts()
            if post_id in posts:
                posts[post_id]["status"] = "published"
                posts[post_id]["fb_post_id"] = fb_post_id
                posts[post_id]["published_at"] = datetime.now().isoformat()
                save_pending_posts(posts)
            
            logger.info(f"✅ Post {post_id} publié sur Facebook! FB ID: {fb_post_id}")
            
            return HTMLResponse(content=f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Publié avec succès!</title>
                <style>
                    body {{ font-family: -apple-system, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }}
                    .container {{ text-align: center; padding: 40px; background: white; border-radius: 10px; box-shadow: 0 2px 20px rgba(0,0,0,0.2); max-width: 500px; }}
                    h1 {{ color: #28a745; margin-bottom: 10px; }}
                    .emoji {{ font-size: 60px; margin-bottom: 20px; }}
                    .fb-link {{ display: inline-block; margin-top: 20px; padding: 12px 24px; background: #1877f2; color: white; text-decoration: none; border-radius: 5px; }}
                    .fb-link:hover {{ background: #166fe5; }}
                    .post-id {{ color: #666; font-size: 12px; margin-top: 20px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="emoji">🎉</div>
                    <h1>Publié avec succès!</h1>
                    <p>Votre post a été publié sur la page Facebook Luxura Distribution.</p>
                    <a href="https://www.facebook.com/profile.php?id=61575105214807" target="_blank" class="fb-link">📘 Voir sur Facebook</a>
                    <p class="post-id">Post ID: {post_id} | FB ID: {fb_post_id}</p>
                </div>
            </body>
            </html>
            """)
        else:
            logger.error(f"❌ Erreur publication Facebook: {error}")
            return HTMLResponse(content=f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Erreur de publication</title>
                <style>
                    body {{ font-family: -apple-system, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; background: #f5f5f5; }}
                    .container {{ text-align: center; padding: 40px; background: white; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); max-width: 500px; }}
                    h1 {{ color: #dc3545; }}
                    .error {{ background: #f8d7da; padding: 15px; border-radius: 5px; color: #721c24; margin-top: 20px; text-align: left; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>❌ Erreur de publication</h1>
                    <p>Une erreur s'est produite lors de la publication sur Facebook.</p>
                    <div class="error">
                        <strong>Erreur:</strong> {error}
                    </div>
                    <p style="margin-top: 20px; color: #666;">Vérifiez que le token Facebook est valide.</p>
                </div>
            </body>
            </html>
            """, status_code=500)
            
    except Exception as e:
        logger.error(f"❌ Exception publication: {e}")
        return HTMLResponse(content=f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Erreur</title>
            <style>
                body {{ font-family: -apple-system, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; background: #f5f5f5; }}
                .container {{ text-align: center; padding: 40px; background: white; border-radius: 10px; }}
                h1 {{ color: #dc3545; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>❌ Erreur</h1>
                <p>{str(e)}</p>
            </div>
        </body>
        </html>
        """, status_code=500)


@router.get("/reject/{post_id}", response_class=HTMLResponse)
async def reject_post(post_id: str):
    """
    ❌ Rejette un post (ne sera pas publié)
    
    Appelé depuis l'email d'approbation.
    """
    logger.info(f"❌ Rejet reçu pour post: {post_id}")
    
    # Mettre à jour le status
    posts = load_pending_posts()
    if post_id in posts:
        posts[post_id]["status"] = "rejected"
        posts[post_id]["rejected_at"] = datetime.now().isoformat()
        save_pending_posts(posts)
    
    return HTMLResponse(content=f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Post rejeté</title>
        <style>
            body {{ font-family: -apple-system, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; background: #f5f5f5; }}
            .container {{ text-align: center; padding: 40px; background: white; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            h1 {{ color: #6c757d; }}
            .emoji {{ font-size: 60px; margin-bottom: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="emoji">🗑️</div>
            <h1>Post rejeté</h1>
            <p>Le post <code>{post_id}</code> a été rejeté et ne sera pas publié.</p>
        </div>
    </body>
    </html>
    """)


@router.get("/pending")
async def list_pending_posts():
    """
    📋 Liste les posts en attente d'approbation
    """
    posts = load_pending_posts()
    pending = [
        {"post_id": pid, **data}
        for pid, data in posts.items()
        if data.get("status") == "pending"
    ]
    return {
        "pending_count": len(pending),
        "posts": pending
    }


@router.post("/test-approval-flow")
async def test_approval_flow():
    """
    🧪 Test complet du flow d'approbation
    
    Crée un post de test, l'ajoute aux pending, et envoie l'email.
    """
    from app.services.email_approval import send_approval_email
    
    # Créer un post de test
    test_post = {
        "text": """✨ **Test du système d'approbation Luxura**

Ceci est un post de test pour vérifier que le système fonctionne correctement.

Quand vous cliquez "Approuver", ce post sera publié sur la page Facebook Luxura Distribution! 🎉

#Luxura #Test #ExtensionsCapillaires""",
        "full_text": """✨ **Test du système d'approbation Luxura**

Ceci est un post de test pour vérifier que le système fonctionne correctement.

Quand vous cliquez "Approuver", ce post sera publié sur la page Facebook Luxura Distribution! 🎉""",
        "hashtags": ["#Luxura", "#Test", "#ExtensionsCapillaires"],
        "image_url": "https://images.unsplash.com/photo-1496440737103-cd596325d314",
        "fallback_image_url": "https://images.unsplash.com/photo-1496440737103-cd596325d314",
        "source_title": "Test Système Approbation",
        "source_url": "https://luxuradistribution.com"
    }
    
    # Envoyer l'email et obtenir le post_id
    result = await send_approval_email(test_post)
    
    if result.get("success"):
        post_id = result.get("post_id")
        # Ajouter aux posts en attente
        add_pending_post(post_id, test_post)
        
        return {
            "success": True,
            "message": "Email de test envoyé! Vérifiez votre boîte mail.",
            "post_id": post_id,
            "approve_url": f"https://luxura-inventory-api.onrender.com/api/content/approve/{post_id}",
            "reject_url": f"https://luxura-inventory-api.onrender.com/api/content/reject/{post_id}"
        }
    else:
        return {
            "success": False,
            "error": result.get("message", "Erreur inconnue")
        }
