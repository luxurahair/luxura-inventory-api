from fastapi import FastAPI, APIRouter, HTTPException, Response, Request, Depends, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import os
import logging
import re
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import httpx
import json
import asyncio
from color_system import COLOR_SYSTEM, get_color_info, get_seo_description, get_all_colors_for_filter, get_colors_by_category, get_colors_by_type
from color_engine_api import process_color_engine, base64_to_image, image_to_base64
from auto_color_engine import auto_recolor

# Import Supabase database functions
from database import (
    db_get_user_by_email, db_get_user_by_id, db_create_user, db_update_user,
    db_get_session, db_create_session, db_delete_user_sessions, db_delete_session,
    db_get_cart_items, db_get_cart_item, db_add_cart_item, db_update_cart_item,
    db_update_cart_item_by_product, db_delete_cart_item, db_clear_cart,
    db_get_blog_posts, db_get_blog_post, db_get_blog_titles, db_create_blog_post,
    db_update_blog_post, db_delete_blog_post, db_count_blog_posts,
    db_create_seo_log, db_get_seo_logs,
    db_create_backlink_run, db_get_backlink_runs,
    db_get_salons
)

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Setup logging FIRST
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================
# DATABASE: SUPABASE (PostgreSQL)
# ============================================
# On utilise SQLAlchemy pour PostgreSQL au lieu de MongoDB

from sqlalchemy import create_engine, Column, String, Integer, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.sql import func

DATABASE_URL = os.environ.get('DATABASE_URL', '')
if DATABASE_URL:
    # Fix pour Render/Supabase: remplacer postgres:// par postgresql://
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
    engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=300)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
    
    # Définition des modèles SQLAlchemy
    class UserDB(Base):
        __tablename__ = "users"
        user_id = Column(String, primary_key=True)
        email = Column(String, unique=True, nullable=False)
        name = Column(String, nullable=False)
        picture = Column(String, nullable=True)
        created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    class UserSessionDB(Base):
        __tablename__ = "user_sessions"
        id = Column(Integer, primary_key=True, autoincrement=True)
        session_token = Column(String, unique=True, nullable=False)
        user_id = Column(String, ForeignKey("users.user_id", ondelete="CASCADE"))
        expires_at = Column(DateTime(timezone=True), nullable=False)
        created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    class CartItemDB(Base):
        __tablename__ = "cart_items"
        id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
        user_id = Column(String, ForeignKey("users.user_id", ondelete="CASCADE"))
        product_id = Column(Integer, nullable=False)
        quantity = Column(Integer, default=1)
        created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    class BlogPostDB(Base):
        __tablename__ = "blog_posts"
        id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
        title = Column(String, nullable=False)
        content = Column(Text, nullable=False)
        excerpt = Column(Text, nullable=True)
        image = Column(String, nullable=True)
        author = Column(String, default="Luxura Distribution")
        wix_post_id = Column(String, nullable=True)
        published_to_wix = Column(Boolean, default=False)
        published_to_facebook = Column(Boolean, default=False)
        category = Column(String, nullable=True)
        created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    class SEOLogDB(Base):
        __tablename__ = "seo_generation_log"
        id = Column(Integer, primary_key=True, autoincrement=True)
        blog_id = Column(String, nullable=True)
        title = Column(String, nullable=True)
        category = Column(String, nullable=True)
        generated_at = Column(DateTime(timezone=True), server_default=func.now())
        status = Column(String, default="generated")
    
    # Créer les tables si elles n'existent pas
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Supabase/PostgreSQL connected")
    except Exception as e:
        logger.error(f"❌ Database error: {e}")
else:
    engine = None
    SessionLocal = None
    logger.warning("⚠️ DATABASE_URL not set - Database features disabled")

def get_db():
    """Dependency pour obtenir une session de base de données"""
    if SessionLocal is None:
        return None
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Luxura Inventory API (Render)
LUXURA_API_URL = "https://luxura-inventory-api.onrender.com"

# Wix API Configuration
WIX_API_KEY = os.getenv("WIX_API_KEY", "")
WIX_SITE_ID = os.getenv("WIX_SITE_ID", "")
WIX_API_BASE = "https://www.wixapis.com"
WIX_INSTANCE_ID = os.getenv("WIX_INSTANCE_ID", "")

# Luxura API - pour utiliser l'OAuth existant
LUXURA_RENDER_API = "https://luxura-inventory-api.onrender.com"

# Variable pour tracker si l'API Luxura a été pingée
luxura_api_awake = False

async def ping_luxura_api():
    """Ping l'API Luxura sur Render pour la réveiller (free tier dort après 15min d'inactivité)"""
    global luxura_api_awake
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{LUXURA_API_URL}/products?limit=1")
            if response.status_code == 200:
                luxura_api_awake = True
                logger.info("✅ Luxura API is awake and responding")
                return True
            else:
                logger.warning(f"⚠️ Luxura API responded with status {response.status_code}")
                return False
    except Exception as e:
        logger.error(f"❌ Failed to ping Luxura API: {e}")
        return False

async def keep_luxura_awake():
    """Background task to keep Luxura API awake"""
    while True:
        await ping_luxura_api()
        await asyncio.sleep(300)  # Ping every 5 minutes

# Create the main app with Swagger UI
app = FastAPI(
    title="Luxura Distribution API",
    description="API pour l'application mobile Luxura - Extensions de cheveux professionnels",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Servir les fichiers statiques (images générées)
STATIC_DIR = Path(__file__).parent / "static"
STATIC_DIR.mkdir(exist_ok=True)

# Dossier pour les images de produits watermarkées
PRODUCTS_IMG_DIR = STATIC_DIR / "products"
PRODUCTS_IMG_DIR.mkdir(exist_ok=True)

# Dossier pour les téléchargements (ZIP)
DOWNLOADS_DIR = STATIC_DIR / "downloads"
DOWNLOADS_DIR.mkdir(exist_ok=True)

@app.get("/api/static/{filename}")
async def serve_static_file(filename: str):
    """Sert les fichiers statiques (images générées)"""
    file_path = STATIC_DIR / filename
    if file_path.exists():
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="File not found")

@app.get("/api/downloads/{filename}")
async def download_file(filename: str):
    """Télécharger les fichiers ZIP d'images par catégorie"""
    file_path = DOWNLOADS_DIR / filename
    if file_path.exists():
        return FileResponse(
            file_path, 
            media_type="application/zip",
            filename=filename
        )
    raise HTTPException(status_code=404, detail="File not found")

@app.get("/api/downloads")
async def list_downloads():
    """Liste tous les fichiers disponibles au téléchargement"""
    files = []
    if DOWNLOADS_DIR.exists():
        for f in DOWNLOADS_DIR.glob("*.zip"):
            files.append({
                "name": f.name,
                "size_mb": round(f.stat().st_size / (1024*1024), 2),
                "url": f"/api/downloads/{f.name}"
            })
    return {"files": files}

@app.get("/api/color-engine")
async def color_engine_info():
    """Info about the Color Engine Streamlit app"""
    return {
        "name": "Luxura Color Engine PRO",
        "description": "Outil de recolorisation d'images d'extensions capillaires",
        "status": "running",
        "local_url": "http://localhost:8501",
        "note": "L'application Streamlit tourne sur le port 8501. Pour y accéder localement: streamlit run /app/backend/color_engine_app.py"
    }

# Color Library API
COLOR_LIBRARY_DIR = Path(__file__).parent / "luxura_images" / "color_library"

@app.get("/api/color-library/reference")
async def get_reference_colors():
    """Get all reference colors from the Elite color library"""
    import json
    
    ref_dir = COLOR_LIBRARY_DIR / "reference"
    mapping_file = ref_dir / "color_mapping.json"
    
    if mapping_file.exists():
        with open(mapping_file, "r", encoding="utf-8") as f:
            colors = json.load(f)
        
        # Add image URLs
        for color in colors:
            color["image_url"] = f"/api/color-library/reference/image/{color['code']}"
        
        return {"colors": colors, "total": len(colors)}
    
    return {"colors": [], "total": 0}

@app.get("/api/color-library/reference/image/{color_code}")
async def get_reference_color_image(color_code: str):
    """Get a specific reference color image"""
    ref_dir = COLOR_LIBRARY_DIR / "reference"
    
    # Find the file that starts with the color code
    for file in ref_dir.glob(f"{color_code}*.jpg"):
        return FileResponse(file, media_type="image/jpeg")
    
    raise HTTPException(status_code=404, detail=f"Color {color_code} not found")

@app.get("/api/color-library/{category}")
async def get_category_colors(category: str):
    """Get all colors for a specific category (genius, halo, tape, i-tip)"""
    cat_dir = COLOR_LIBRARY_DIR / category.lower()
    
    if not cat_dir.exists():
        return {"colors": [], "total": 0}
    
    colors = []
    for file in cat_dir.glob("*.jpg"):
        colors.append({
            "code": file.stem,
            "name": file.stem.replace("_", " "),
            "image_url": f"/api/color-library/{category}/image/{file.stem}"
        })
    
    return {"colors": colors, "total": len(colors)}

@app.get("/api/color-library/{category}/image/{color_code}")
async def get_category_color_image(category: str, color_code: str):
    """Get a specific category color image"""
    cat_dir = COLOR_LIBRARY_DIR / category.lower()
    file_path = cat_dir / f"{color_code}.jpg"
    
    if file_path.exists():
        return FileResponse(file_path, media_type="image/jpeg")
    
    raise HTTPException(status_code=404, detail=f"Color {color_code} not found in {category}")

@app.get("/api/products/image/{category}/{color_code}")
async def serve_product_image(category: str, color_code: str):
    """
    Sert les images de produits watermarkées locales.
    Format: /api/products/image/genius/cacao -> genius_cacao.jpg
    """
    # Normalize the color code and category
    cat_lower = category.lower()
    color_lower = color_code.lower().replace('/', '-')
    
    filename = f"{cat_lower}_{color_lower}.jpg"
    file_path = PRODUCTS_IMG_DIR / filename
    
    if file_path.exists():
        return FileResponse(file_path, media_type="image/jpeg")
    
    # If not found, return 404
    raise HTTPException(status_code=404, detail=f"Image not found: {filename}")

# Variable globale pour le scheduler
blog_scheduler = None

async def scheduled_blog_generation():
    """
    📅 CALENDRIER ÉDITORIAL: Génère des BROUILLONS selon la rotation
    
    Rotation sur 2 semaines:
    - Semaine 1: Lundi=consommateur, Mercredi=comparatif, Vendredi=B2B
    - Semaine 2: Lundi=entretien, Mercredi=guide, Vendredi=B2B
    
    Publication automatique: DÉSACTIVÉE (validation humaine obligatoire)
    """
    try:
        logger.info(f"🕐 CRON: Starting draft generation at {datetime.now(timezone.utc)}")
        
        # Import du calendrier éditorial
        try:
            from editorial_calendar import (
                get_cron_category,
                should_publish_today,
                log_calendar_status,
                get_suggested_topic
            )
            CALENDAR_AVAILABLE = True
        except ImportError:
            CALENDAR_AVAILABLE = False
            logger.warning("⚠️ Calendrier éditorial non disponible - fallback aléatoire")
        
        # Vérifier si on doit publier aujourd'hui
        if CALENDAR_AVAILABLE:
            log_calendar_status()
            should_pub, reason = should_publish_today()
            
            if not should_pub:
                logger.info(f"📅 {reason} - Pas de génération aujourd'hui")
                return
            
            category = get_cron_category()
            suggested_topic = get_suggested_topic()
            
            if suggested_topic:
                logger.info(f"📝 Sujet suggéré: {suggested_topic}")
        else:
            # Fallback: rotation aléatoire
            SAFE_CATEGORIES = ['entretien', 'comparatif', 'cheveux_fins', 'b2b_salon', 'guide']
            import random
            category = random.choice(SAFE_CATEGORIES)
        
        if not category:
            logger.info("📅 Pas de catégorie assignée - skip")
            return
        
        from blog_automation import generate_daily_blogs
        
        # Récupérer les clés API nécessaires
        openai_key = os.getenv("EMERGENT_LLM_KEY") or os.getenv("OPENAI_API_KEY")
        wix_api_key = os.getenv("WIX_API_KEY")
        wix_site_id = os.getenv("WIX_SITE_ID")
        fb_access_token = os.getenv("FB_PAGE_ACCESS_TOKEN")
        fb_page_id = os.getenv("FB_PAGE_ID")
        
        if not openai_key:
            logger.error("❌ CRON: Missing EMERGENT_LLM_KEY or OPENAI_API_KEY")
            return
        
        # 1 seul brouillon Wix + publication Facebook automatique
        results = await generate_daily_blogs(
            db=None,  # Migration Supabase: le paramètre db n'est plus utilisé
            openai_key=openai_key,  # ✅ Passer la clé OpenAI
            wix_api_key=wix_api_key,
            wix_site_id=wix_site_id,
            count=1,
            send_email=True,
            publish_to_wix=False,  # ❌ PAS DE PUBLICATION AUTO WIX (validation humaine)
            publish_to_facebook=True,  # ✅ PUBLICATION AUTO FACEBOOK
            fb_access_token=fb_access_token,
            fb_page_id=fb_page_id,
            force_category=category
        )
        
        if results:
            logger.info(f"✅ CRON: Generated {len(results)} DRAFT(s) - category={category}")
            logger.info(f"   ⚠️ Validation humaine requise avant publication!")
            for blog in results:
                logger.info(f"   - {blog.get('title', 'No title')[:50]}...")
        else:
            logger.warning("⚠️ CRON: No drafts generated")
            
    except Exception as e:
        logger.error(f"❌ CRON: Error in draft generation: {e}")
        import traceback
        traceback.print_exc()

# Startup event - ping Luxura API to wake it up
@app.on_event("startup")
async def startup_event():
    """Au démarrage, lancer seulement les tâches internes non bloquantes"""
    global blog_scheduler
    
    logger.info("🚀 Starting Luxura Distribution API...")
    
    # ⚠️ DÉSACTIVÉ: Le self-ping bloque le démarrage sur Render
    # Le service essaie de se pinger lui-même avant d'avoir ouvert le port
    # await ping_luxura_api()
    # asyncio.create_task(keep_luxura_awake())
    logger.info("⏭️ Self-ping disabled (prevents Render startup deadlock)")
    
    # 🛡️ CRON OPTIMISÉ FEMMES QUÉBEC: 1 article/jour aux heures de pointe
    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        from apscheduler.triggers.cron import CronTrigger
        
        blog_scheduler = AsyncIOScheduler(timezone="America/Montreal")
        
        # 📅 HEURES DE POINTE PAR JOUR (optimisé engagement femmes Québec)
        # Lundi 7h, Mardi 12h, Mercredi 19h, Jeudi 7h, Vendredi 12h, Samedi 10h, Dimanche 20h
        CRON_SCHEDULE = [
            {"day": "mon", "hour": 7, "desc": "Lundi 7h - Transformation"},
            {"day": "tue", "hour": 12, "desc": "Mardi 12h - Cheveux fins"},
            {"day": "wed", "hour": 19, "desc": "Mercredi 19h - Comparatif"},
            {"day": "thu", "hour": 7, "desc": "Jeudi 7h - B2B Salon"},
            {"day": "fri", "hour": 12, "desc": "Vendredi 12h - Tendances"},
            {"day": "sat", "hour": 10, "desc": "Samedi 10h - Inspiration"},
            {"day": "sun", "hour": 20, "desc": "Dimanche 20h - Témoignages/Self-care"},
        ]
        
        for schedule in CRON_SCHEDULE:
            blog_scheduler.add_job(
                scheduled_blog_generation,
                CronTrigger(day_of_week=schedule["day"], hour=schedule["hour"], minute=0),
                id=f"blog_{schedule['day']}",
                name=f"Blog {schedule['desc']}"
            )
        
        blog_scheduler.start()
        
        # Log du calendrier éditorial
        try:
            from editorial_calendar import get_current_rotation_week, get_weekly_schedule, get_week_preview
            rotation_week = get_current_rotation_week()
            weekly_schedule = get_weekly_schedule()
            
            logger.info("=" * 50)
            logger.info("📅 CALENDRIER ÉDITORIAL - OPTIMISÉ FEMMES QUÉBEC")
            logger.info(f"   Semaine de rotation: {rotation_week}/2")
            logger.info("   🎯 Cible: Femmes québécoises 18-50 ans")
            logger.info("   ⏰ Heures de pointe optimisées:")
            for slot in weekly_schedule:
                hour = slot.get('hour', 8)
                target = slot.get('target', 'femmes')
                logger.info(f"   - {slot['day'].capitalize()} {hour}h: {slot['category']} ({target})")
            logger.info("   Publication: BROUILLON (validation humaine)")
            logger.info("=" * 50)
        except ImportError:
            logger.info("=" * 50)
            logger.info("🛡️ BLOG CRON - MODE FALLBACK")
            logger.info("   - 7 jours/semaine aux heures de pointe")
            logger.info("   - Catégories: rotation automatique")
            logger.info("=" * 50)
        
    except ImportError:
        logger.warning("⚠️ APScheduler not installed - CRON disabled")
    except Exception as e:
        logger.error(f"❌ Failed to start blog scheduler: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Arrêter proprement le scheduler"""
    global blog_scheduler
    if blog_scheduler:
        blog_scheduler.shutdown()
        logger.info("🛑 Blog scheduler stopped")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== MODELS ====================

class User(BaseModel):
    user_id: str
    email: str
    name: str
    picture: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserSession(BaseModel):
    session_token: str
    user_id: str
    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CartItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    product_id: int  # Now using Luxura API product ID
    quantity: int = 1
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CartItemCreate(BaseModel):
    product_id: int
    quantity: int = 1

class CartItemUpdate(BaseModel):
    quantity: int

class BlogPost(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    content: str
    excerpt: str
    image: Optional[str] = None
    author: str = "Luxura Distribution"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Salon(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    address: str
    city: str
    phone: Optional[str] = None
    website: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class Category(BaseModel):
    id: str
    name: str
    description: str
    image: Optional[str] = None
    wix_url: Optional[str] = None
    order: int = 0

# ==================== HELPER: Detect category from handle (Wix URL) ====================

# ALLOWED CATEGORIES - All 7 categories sold by Luxura
ALLOWED_CATEGORIES = {'genius', 'tape', 'i-tip', 'halo', 'essentiels', 'ponytail', 'clip-in'}

# EXCLUDED PRODUCTS - Products to skip (test products only)
EXCLUDED_KEYWORDS = ['test']

def detect_category_from_handle(handle: str, name: str) -> str:
    """Detect product category from Wix handle - more accurate than name-based detection
    Returns None for products that should be excluded (test products only)
    """
    if not handle:
        handle = ""
    handle_lower = handle.lower()
    name_lower = name.lower()
    
    # EXCLUDE: Test products only
    for excluded in EXCLUDED_KEYWORDS:
        if excluded in handle_lower or excluded in name_lower:
            return None  # Will be filtered out
    
    # PRIORITY 0: Check name FIRST for specific series names (most reliable)
    # This catches cases where handle is wrong but name is correct
    if 'vivian' in name_lower:
        return 'genius'
    if 'victoria' in name_lower:
        return 'ponytail'
    if 'sophia' in name_lower:
        return 'clip-in'
    if 'everly' in name_lower and ('clip' not in name_lower and 'ponytail' not in name_lower):
        return 'halo'
    if 'aurora' in name_lower:
        return 'tape'
    if 'eleanor' in name_lower:
        return 'i-tip'
    
    # Priority 1: Check handle (reliable for URLs)
    # NEW: Ponytail (Victoria series) - STRICT: must have ponytail keyword
    if 'ponytail' in handle_lower or 'queue-de-cheval' in handle_lower:
        return 'ponytail'
    # NEW: Clip-In (Sophia series) - STRICT: must have clip-in or clips keyword
    elif 'clip-in' in handle_lower or 'clips' in handle_lower:
        return 'clip-in'
    elif 'genius' in handle_lower or 'vivian' in handle_lower or 'trame-invisible' in handle_lower:
        return 'genius'
    elif 'halo' in handle_lower or 'everly' in handle_lower:
        return 'halo'
    elif 'bande' in handle_lower or 'aurora' in handle_lower or 'tape' in handle_lower or 'adhésive' in handle_lower:
        return 'tape'
    elif 'i-tip' in handle_lower or 'itip' in handle_lower or 'eleanor' in handle_lower:
        return 'i-tip'
    
    # Priority 2: Check name for essentials/accessories
    essentials_keywords = ['spray', 'brosse', 'fer', 'shampooing', 'lotion', 'anneau', 'ensemble', 
                          'duo', 'kit', 'accessoire', 'outil', 'colle', 'remover', 'peigne', 
                          'tenue ultra', 'installation']
    for keyword in essentials_keywords:
        if keyword in name_lower or keyword in handle_lower:
            return 'essentiels'
    
    # Priority 3: Fallback to name-based detection - STRICT matching
    if 'ponytail' in name_lower:
        return 'ponytail'
    elif 'clip-in' in name_lower:
        return 'clip-in'
    elif 'genius' in name_lower or 'trame invisible' in name_lower:
        return 'genius'
    elif 'halo' in name_lower:
        return 'halo'
    elif 'bande' in name_lower or 'adhésive' in name_lower:
        return 'tape'
    elif 'i-tip' in name_lower or 'itip' in name_lower:
        return 'i-tip'
    
    # Default to essentiels for accessories, but may be filtered if not matching
    return 'essentiels'

def extract_color_size_for_inventory(name):
    """Extract color code and size from product name for inventory matching"""
    import re
    color_match = re.search(r'#([A-Za-z0-9/]+)', name)
    color = color_match.group(1).upper() if color_match else ""
    size_match = re.search(r'(\d{2})["\']?\s*(\d{2,3})\s*gram', name, re.IGNORECASE)
    size = f"{size_match.group(1)}-{size_match.group(2)}" if size_match else ""
    return color, size

def extract_color_code_from_name(name: str) -> str:
    """
    Extract the color code from product name for deduplication.
    Ex: 'Genius Vivian Caramel Doré #6' → '6'
    Ex: 'Genius Vivian Golden Hour #6/24' → '6/24'
    Ex: 'Genius Vivian Diamant Glacé #613/18A' → '613/18A'
    """
    if not name:
        return ""
    # Match color code after # (including complex codes like 6/6T24, 613/18A)
    color_match = re.search(r'#([A-Za-z0-9/T]+)', name, re.IGNORECASE)
    if color_match:
        return color_match.group(1).upper()
    return ""

def get_dedup_key(category: str, color_code: str, name: str) -> str:
    """
    Generate a unique key for product deduplication.
    Groups products by category + color code to eliminate duplicates.
    """
    if color_code:
        return f"{category}|{color_code}"
    # Fallback: use cleaned name for products without color codes
    clean_name = name.split(' — ')[0].strip().lower()
    return f"{category}|{clean_name}"

def get_product_type_for_inventory(name, sku=""):
    """Determine product type from name or SKU for inventory matching"""
    name_lower = name.lower()
    sku_lower = (sku or "").lower()
    if 'genius' in name_lower or 'vivian' in name_lower or sku_lower.startswith('gw'):
        return 'genius'
    elif 'halo' in name_lower or 'everly' in name_lower:
        return 'halo'
    elif 'tape' in name_lower or 'aurora' in name_lower or 'bande' in name_lower:
        return 'tape'
    elif 'i-tip' in name_lower or 'eleanor' in name_lower:
        return 'i-tip'
    elif 'ponytail' in name_lower or 'victoria' in name_lower:
        return 'ponytail'
    elif 'clip' in name_lower or 'sophia' in name_lower:
        return 'clip-in'
    return 'other'

def generate_product_name_from_handle(handle: str, category: str) -> str:
    """
    Génère le nom de produit complet depuis le handle Wix
    Ex: 'halo-série-everly-noir-foncé-1' → 'Halo Everly Onyx Noir #1'
    Ex: 'halo-série-everly-balayage-blond-foncé-6-24' → 'Halo Everly Golden Hour #6/24'
    """
    if not handle:
        return ""
    
    # MAPPING DIRECT HANDLES GENIUS → NOMS OFFICIELS WIX (Avril 2025)
    GENIUS_WIX_NAMES = {
        "genius-ombré-blond-moka-6-6t24": "Genius Vivian Caramel Soleil #6/6T24",
        "genius-série-vivian-brun-lumineux-blond-foncé-6": "Genius Vivian Caramel Doré #6",
        "genius-trame-invisible-série-vivian-blanc-polar-ivory": "Genius Vivian Ivoire Précieux #IVORY",
        "genius-trame-invisible-série-vivian-brun-2": "Genius Vivian Espresso Intense #2",
        "genius-trame-invisible-série-vivian-ombré-brun-cacao-3-3t24": "Genius Vivian Châtaigne Lumière #3/3T24",
        "genius-sdd-série-vivian-ombré-2btp18-1006": "Genius Vivian Espresso Balayage Glacé #2BTP18/1006",
        "genius-trame-invisible-série-vivian-balayage-blond-beige-18-22": "Genius Vivian Champagne Doré #18/22",
        "genius-trame-invisible-série-vivian-brun-moyen-3": "Genius Vivian Châtaigne Douce #3",
        "genius-trame-invisible-série-vivian-t14-p14-24": "Genius Vivian Blond Balayage Doré #T14/P14/24",
        "genius-trame-invisible-série-vivian-ombré-brun-nuit-db": "Genius Vivian Nuit Mystère #DB",
        "genius-trame-invisible-série-vivian-balayage-blond-foncé-6-24": "Genius Vivian Golden Hour #6/24",
        "genius-ssd-trame-invisible-série-vivian-brun-cacao": "Genius Vivian Cacao Velours #CACAO",
        "genius-trame-invisible-série-vivian-foochow": "Genius Vivian Cachemire Oriental #FOOCHOW",
        "genius-trame-invisible-série-vivian-chengtu": "Genius Vivian Châtain Soyeux #CHENGTU",
        "genius-trame-invisible-série-vivian-5atp18b62": "Genius Vivian Noisette Balayage Cendré #5ATP18B62",
        "genius-ssd-série-vivian-ombré-blond-cendré-5at60": "Genius Vivian Noisette Ombré Platine #5AT60",
        "genius-nouvelle-trame-invisible-série-vivian-cannelle-cinnamon": "Genius Vivian Cannelle Épicée #CINNAMON",
        "genius-série-vivian-balayage-blond-cendré-613-18a": "Genius Vivian Diamant Glacé #613/18A",
        "genius-série-vivian-ombré-blond-cendré-hps": "Genius Vivian Cendré Étoilé #HPS",
        "genius-série-vivian-ombré-blond-miel-cb": "Genius Vivian Miel Sauvage Ombré #CB",
        "ponytail-queue-de-cheval-série-everly-ombré-brun-moka-bm": "Genius Vivian BM #BM",  # Handle ponytail mais c'est un Genius
        "genius-trame-invisible-série-vivian-blond-platine-60a": "Genius Vivian Platine Pur #60A",
        "genius-trame-invisible-série-vivian-dark-chocolate-dc": "Genius Vivian Chocolat Profond #DC",
        "genius-trame-invisible-série-vivian-perfect-highlift-ash-pha": "Genius Vivian Cendré Céleste #PHA",
        "clips-série-everly-noir-doux-brun-foncé-1b": "Genius Vivian Noir Soie #1B",  # Handle clips mais c'est un Genius
        "genius-trame-invisible-série-vivian-noir-foncé-1": "Genius Vivian Onyx Noir #1",
    }
    
    # Si c'est un Genius avec un nom direct, utiliser le mapping Wix
    handle_lower = handle.lower()
    if handle_lower in GENIUS_WIX_NAMES:
        return GENIUS_WIX_NAMES[handle_lower]
    
    # Mapping des codes couleur vers noms de luxe
    # Format: code-handle → (nom_luxe, code_display)
    color_luxe_map = {
        # Noirs
        "1": ("Onyx Noir", "#1"),
        "1b": ("Noir Soie", "#1B"),
        # Bruns
        "2": ("Espresso Intense", "#2"),
        "db": ("Nuit Mystère", "#DB"),
        "dc": ("Chocolat Profond", "#DC"),
        "cacao": ("Cacao Velours", "#CACAO"),
        "chengtu": ("Soie d'Orient", "#CHENGTU"),
        "foochow": ("Cachemire Oriental", "#FOOCHOW"),
        # Châtaignes
        "3": ("Châtaigne Douce", "#3"),
        "cinnamon": ("Cannelle Épicée", "#CINNAMON"),
        "3-3t24": ("Châtaigne Lumière", "#3/3T24"),
        # Caramels
        "6": ("Caramel Doré", "#6"),
        "bm": ("Miel Sauvage", "#BM"),
        "6-24": ("Golden Hour", "#6/24"),
        "6-6t24": ("Caramel Soleil", "#6/6T24"),
        # Blonds
        "18-22": ("Champagne Doré", "#18/22"),
        "60a": ("Platine Pur", "#60A"),
        "pha": ("Cendré Céleste", "#PHA"),
        "613-18a": ("Diamant Glacé", "#613/18A"),
        # Blancs
        "ivory": ("Ivoire Précieux", "#IVORY"),
        "icw": ("Cristal Polaire", "#ICW"),
        # Ombrés
        "cb": ("Miel Sauvage Ombré", "#CB"),
        "hps": ("Cendré Étoilé", "#HPS"),
        "5at60": ("Aurore Glaciale", "#5AT60"),
        "5atp18b62": ("Aurore Boréale", "#5ATP18B62"),
        "2btp18-1006": ("Espresso Lumière", "#2BTP18/1006"),
        "t14-p14-24": ("Venise Dorée", "#T14/P14/24"),
    }
    
    # Série par catégorie
    series_map = {
        "halo": "Everly",
        "genius": "Vivian",
        "tape": "Aurora",
        "i-tip": "Eleanor",
        "ponytail": "Victoria",
        "clip-in": "Sophia"
    }
    
    # Type de produit
    type_map = {
        "halo": "Halo",
        "genius": "Genius",
        "tape": "Bande Adhésive",
        "i-tip": "I-Tip",
        "ponytail": "Queue de Cheval",
        "clip-in": "Extensions à Clips"
    }
    
    handle_lower = handle.lower()
    
    # Extraire le code couleur depuis la fin du handle
    luxe_name = ""
    color_suffix = ""
    
    # Chercher le code couleur dans le handle (du plus long au plus court pour éviter les faux positifs)
    for code, (luxe, suffix) in sorted(color_luxe_map.items(), key=lambda x: -len(x[0])):
        # Chercher à la fin du handle
        if handle_lower.endswith(f"-{code}"):
            luxe_name = luxe
            color_suffix = suffix
            break
    
    # Construire le nom
    product_type = type_map.get(category, category.title())
    series = series_map.get(category, "")
    
    if luxe_name:
        name = f"{product_type} {series} {luxe_name} {color_suffix}".strip()
    else:
        # Fallback: extraire les infos du handle
        # Ex: 'halo-série-everly-noir-foncé-1' → 'Halo Everly Noir Foncé #1'
        parts = handle.split('-')
        
        # Chercher un code numérique à la fin
        color_code = ""
        if parts and parts[-1].replace('t', '').replace('p', '').isalnum():
            potential_code = parts[-1]
            if any(c.isdigit() for c in potential_code):
                color_code = f"#{potential_code.upper()}"
                parts = parts[:-1]
        
        # Nettoyer les parties
        skip_words = {'serie', 'série', 'trame', 'invisible', 'bande', 'adhesive', 'adhésive', 'aurora', 'everly', 'vivian', 'eleanor', 'victoria', 'sophia'}
        cleaned_parts = []
        for p in parts:
            p_lower = p.lower()
            if p_lower not in skip_words and p_lower != category:
                cleaned_parts.append(p.title())
        
        # Prendre les parties pertinentes
        if len(cleaned_parts) > 3:
            cleaned_parts = cleaned_parts[:1] + cleaned_parts[-2:]  # Type + couleur
        
        name = f"{product_type} {series} {' '.join(cleaned_parts)} {color_code}".strip()
        # Nettoyer les espaces multiples
        name = ' '.join(name.split())
    
    return name

def clean_html(text: str) -> str:
    """Remove HTML tags and clean up description text"""
    if not text:
        return ""
    # Remove HTML tags
    clean = re.sub(r'<[^>]+>', '', text)
    # Replace HTML entities
    clean = clean.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    clean = clean.replace('&#39;', "'").replace('&quot;', '"')
    # Remove extra whitespace
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean

# ==================== IMAGE MAPPING SYSTEM ====================
# Système de mapping d'images basé sur les codes couleur
# Les images sont organisées par catégorie et code couleur pour garantir la cohérence

# Images par code couleur - mapping universel basé sur la teinte
# Ces images sont les vraies photos des produits Luxura
COLOR_CODE_IMAGES = {
    # Noirs / Bruns foncés
    "1": "https://static.wixstatic.com/media/f1b961_7c4c9a8b07484a5eb66b12e9b9322b4a~mv2.jpg",  # Noir Foncé
    "1b": "https://static.wixstatic.com/media/f1b961_42148bb43bbe484f9ca8f1127a4d30e4~mv2.png",  # Noir Doux
    "2": "https://static.wixstatic.com/media/f1b961_2596437db6134f7bbdc1c5b2d72907fd~mv2.jpg",  # Brun
    "dc": "https://static.wixstatic.com/media/f1b961_58c11630ff1349728c47e56190218422~mv2.png",  # Dark Chocolate
    "cacao": "https://static.wixstatic.com/media/f1b961_11271a5d5d91485883888a201592829c~mv2.jpg",  # Cacao
    
    # Bruns moyens
    "3": "https://static.wixstatic.com/media/f1b961_d1bb2905a7b748f5ac4676d5c96bae2a~mv2.png",  # Brun Moyen
    "3/3t24": "https://static.wixstatic.com/media/f1b961_bc6218e7631045ff801eeb0195b3b8c9~mv2.png",  # Ombré Cacao
    
    # Bruns clairs / Caramel
    "6": "https://static.wixstatic.com/media/f1b961_5b61b7d6874a47abb7997a78d99c7125~mv2.png",  # Caramel Doré
    "6/24": "https://static.wixstatic.com/media/f1b961_7858886b3ecb41e5bdf5be80b2aa4359~mv2.png",  # Golden Hour
    "6/6t24": "https://static.wixstatic.com/media/f1b961_276e2a0ba6ab4e92a0da09977692256e~mv2.png",  # Caramel Soleil
    
    # Blonds
    "18/22": "https://static.wixstatic.com/media/f1b961_ed52f5195856485796099c2a1823a0fd~mv2.png",  # Champagne Doré
    "60a": "https://static.wixstatic.com/media/f1b961_1e9953c3551440479117fa2954918173~mv2.png",  # Platine Pur
    "613/18a": "https://static.wixstatic.com/media/f1b961_2fba27c18fe14584a828cfa9880a3146~mv2.png",  # Diamant Glacé
    
    # Cendrés / Spéciaux
    "hps": "https://static.wixstatic.com/media/f1b961_13645139441a4ad0bdae63bca7d65c37~mv2.png",  # Cendré Étoilé
    "pha": "https://static.wixstatic.com/media/f1b961_54514ba920d34aed9aa1f10c62f1759a~mv2.jpg",  # Cendré Céleste
    "icw": "https://static.wixstatic.com/media/f1b961_9b2d02f5f8fe47369534f67678bbc79d~mv2.jpg",  # Ice White
    "polar": "https://static.wixstatic.com/media/f1b961_2dbcedc5036044b69e1ba01c58cc93d4~mv2.jpg",  # Polar Ivory
    
    # Ombrés / Balayages
    "cb": "https://static.wixstatic.com/media/f1b961_7ba6134ca87e4423817e9b0fa07754c1~mv2.png",  # Blond Miel Ombré
    "db": "https://static.wixstatic.com/media/f1b961_601ee2f6e66b48d6b09e471501537fc9~mv2.png",  # Brun Nuit
    "du": "https://static.wixstatic.com/media/f1b961_7ba6134ca87e4423817e9b0fa07754c1~mv2.png",  # Brun Miel Ombré
    "cl": "https://static.wixstatic.com/media/f1b961_7ba6134ca87e4423817e9b0fa07754c1~mv2.png",  # Blond Ombré CL
    "sb": "https://static.wixstatic.com/media/f1b961_13645139441a4ad0bdae63bca7d65c37~mv2.png",  # Blond Cendré Ombré
    "mo": "https://static.wixstatic.com/media/f1b961_276e2a0ba6ab4e92a0da09977692256e~mv2.png",  # Moka Ombré
    "bm": "https://static.wixstatic.com/media/f1b961_7ba6134ca87e4423817e9b0fa07754c1~mv2.png",  # Blond Miel
    
    # Spéciaux Genius
    "5at60": "https://static.wixstatic.com/media/f1b961_9f8115b4f7614340b0dc9aeba39bd699~mv2.jpg",  # Aurore Glaciale
    "5atp18b62": "https://static.wixstatic.com/media/f1b961_0e7cf48e1d59418bbf1b562c21494176~mv2.jpg",  # Aurore Boréale
    "2btp18/1006": "https://static.wixstatic.com/media/f1b961_75316de55cf441ecb82211cbc8d91010~mv2.jpg",  # Ombré Spécial
    "t14/p14/24": "https://static.wixstatic.com/media/f1b961_9c2192c6fa5f4458913d46ea8a8f9dae~mv2.jpg",  # T14
    "foochow": "https://static.wixstatic.com/media/f1b961_28d930f0f9924b229beb3be484bc1fbd~mv2.jpg",  # Cachemire Oriental
    "chengtu": "https://static.wixstatic.com/media/f1b961_e440aecc44e44c69b0d56dad273a95e9~mv2.jpg",  # Cachemire Doré
    "cinnamon": "https://static.wixstatic.com/media/f1b961_23960136c3df4e84852f5dde15475d17~mv2.jpg",  # Cannelle
}

# Images spécifiques par catégorie (pour les produits qui ont des photos distinctes)
# MISE À JOUR 2025-04-11: Images Genius synchronisées depuis Wix
CATEGORY_SPECIFIC_IMAGES = {
    "genius": {
        # IMAGES WIX GENIUS (Mise à jour Avril 2025)
        "1": "https://static.wixstatic.com/media/f1b961_ebf51cc4c86346d8894294e7550cf082~mv2.jpg",  # Onyx Noir
        "1b": "https://static.wixstatic.com/media/f1b961_71de051f1f114c858d95f2a770eba544~mv2.jpg",  # Noir Soie
        "dc": "https://static.wixstatic.com/media/f1b961_be2093b37a7445fab7f8a23083c22f2d~mv2.jpg",  # Chocolat Profond
        "cacao": "https://static.wixstatic.com/media/f1b961_80553585b8c14372907f1aefb8364ee3~mv2.jpg",  # Cacao Velours
        "2": "https://static.wixstatic.com/media/f1b961_2596437db6134f7bbdc1c5b2d72907fd~mv2.jpg",  # Espresso Intense
        "3": "https://static.wixstatic.com/media/f1b961_47ff485b2f674fdc9245cc856004cd46~mv2.png",  # Châtaigne Douce
        "3/3t24": "https://static.wixstatic.com/media/f1b961_f7c08b4eeb9d454aa0da2db110ab359d~mv2.png",  # Châtaigne Lumière
        "6": "https://static.wixstatic.com/media/f1b961_5769d9b826004a6f91eb9112dc140cfb~mv2.png",  # Caramel Doré
        "6/24": "https://static.wixstatic.com/media/f1b961_387bbe6d47cd4217a7b0157f398d9a63~mv2.png",  # Golden Hour
        "6/6t24": "https://static.wixstatic.com/media/f1b961_b1da0ecc4ce04c86955047f5f172a44c~mv2.png",  # Caramel Soleil
        "60a": "https://static.wixstatic.com/media/f1b961_c3168b50e6d9464db8365cdef0b16557~mv2.png",  # Platine Pur
        "18/22": "https://static.wixstatic.com/media/f1b961_b7d3eb648bf443cb8d30e3e23fa62ad8~mv2.png",  # Champagne Doré
        "613/18a": "https://static.wixstatic.com/media/f1b961_c15e5a01c6024a1699cb92a2be325f8f~mv2.png",  # Diamant Glacé
        "cb": "https://static.wixstatic.com/media/f1b961_5e027a0d94d749e99ad76830129b42da~mv2.png",  # Miel Sauvage Ombré
        "bm": "https://static.wixstatic.com/media/f1b961_22ed1dd868004bca8afbe1a2b6e754c2~mv2.jpg",  # BM
        "db": "https://static.wixstatic.com/media/f1b961_b049d0356ab04230a0291ddadc1dfbe8~mv2.png",  # Nuit Mystère
        "hps": "https://static.wixstatic.com/media/f1b961_46c106d70c154c34918e15ad23452fc4~mv2.png",  # Cendré Étoilé
        "pha": "https://static.wixstatic.com/media/f1b961_0fdc2ccdccc64d65bde5f1ceb6629ce6~mv2.jpg",  # Cendré Céleste
        "ivory": "https://static.wixstatic.com/media/f1b961_2dbcedc5036044b69e1ba01c58cc93d4~mv2.jpg",  # IVORY
        "cinnamon": "https://static.wixstatic.com/media/f1b961_23960136c3df4e84852f5dde15475d17~mv2.jpg",  # Cannelle Épicée
        "foochow": "https://static.wixstatic.com/media/f1b961_1d56319f8a3c4e4dba09ce1c80385fbc~mv2.jpg",  # FOOCHOW
        "chengtu": "https://static.wixstatic.com/media/f1b961_302097ceefaf4f69a608838f489b57a2~mv2.jpg",  # Châtain Soyeux
        "5at60": "https://static.wixstatic.com/media/f1b961_5cab009ec1a64e689baa767cbf3bcb8e~mv2.jpg",  # Noisette Ombré Platine
        "5atp18b62": "https://static.wixstatic.com/media/f1b961_0e7cf48e1d59418bbf1b562c21494176~mv2.jpg",  # Noisette Balayage Cendré
        "2btp18/1006": "https://static.wixstatic.com/media/f1b961_75316de55cf441ecb82211cbc8d91010~mv2.jpg",  # Espresso Balayage Glacé
        "t14/p14/24": "https://static.wixstatic.com/media/f1b961_9c2192c6fa5f4458913d46ea8a8f9dae~mv2.jpg",  # Blond Balayage Doré
    },
    "tape": {
        "1": "https://static.wixstatic.com/media/f1b961_8bed6fa0069a41c3971d7dcb51ab1cec~mv2.png",
        "1b": "https://static.wixstatic.com/media/f1b961_088e24bf74854319bab62d49634b608a~mv2.png",
        "dc": "https://static.wixstatic.com/media/f1b961_fa7cd15003c94b16a263bd39d22dc48c~mv2.jpg",
        "3": "https://static.wixstatic.com/media/f1b961_a0bb462af6f44e25aa751ea359024bba~mv2.png",
        "6": "https://static.wixstatic.com/media/f1b961_5d6668fdf8114e3d99f528fe612222f0~mv2.png",
        "60a": "https://static.wixstatic.com/media/f1b961_e75015e3740242dab6c3567bf8445811~mv2.png",
        "cb": "https://static.wixstatic.com/media/f1b961_5e027a0d94d749e99ad76830129b42da~mv2.png",
    },
    "i-tip": {
        "default": "https://static.wixstatic.com/media/f1b961_0d440382da1f450da579fd73c14daf88~mv2.png",
    },
}

# Images par défaut par catégorie (fallback si pas de match de couleur)
CATEGORY_DEFAULT_IMAGES = {
    "genius": "https://static.wixstatic.com/media/f1b961_0765bab9e407403289c86e98fcb27476~mv2.png",
    "halo": "https://static.wixstatic.com/media/f1b961_42148bb43bbe484f9ca8f1127a4d30e4~mv2.png",
    "tape": "https://static.wixstatic.com/media/f1b961_8bed6fa0069a41c3971d7dcb51ab1cec~mv2.png",
    "i-tip": "https://static.wixstatic.com/media/f1b961_0d440382da1f450da579fd73c14daf88~mv2.png",
    "ponytail": "https://static.wixstatic.com/media/f1b961_7ba6134ca87e4423817e9b0fa07754c1~mv2.png",
    "clip-in": "https://static.wixstatic.com/media/f1b961_42148bb43bbe484f9ca8f1127a4d30e4~mv2.png",
    "essentiels": "https://static.wixstatic.com/media/de6cdb_5ba6af2b449d44039ce9c23d3517953b~mv2.jpg",
}

def extract_color_code_from_handle(handle: str) -> str:
    """Extrait le code couleur du handle pour le mapping d'images"""
    if not handle:
        return ""
    
    handle_lower = handle.lower()
    parts = handle_lower.replace('é', 'e').replace('ô', 'o').split('-')
    
    # Chercher les codes couleur connus dans le handle
    # Ordre de priorité : codes complexes d'abord, puis simples
    complex_codes = ['5atp18b62', '2btp18/1006', 't14/p14/24', '5at60', '613/18a', 
                     '6/6t24', '3/3t24', '18/22', '6/24']
    
    for code in complex_codes:
        if code in handle_lower or code.replace('/', '-') in handle_lower:
            return code
    
    # Chercher le code couleur à la fin du handle (pattern: -CODE ou -CODE-NUMBER)
    simple_codes = ['60a', 'hps', 'pha', 'icw', 'polar', 'cacao', 'cinnamon', 
                    'foochow', 'chengtu', 'dc', 'cb', 'db', 'du', 'cl', 'sb', 'mo', 'bm',
                    '1b', '1', '2', '3', '6']
    
    for code in simple_codes:
        # Check if code is at the end or followed by a number
        if handle_lower.endswith(f'-{code}') or f'-{code}-' in handle_lower:
            return code
        # Also check without hyphen for compound codes
        for part in parts[-3:]:  # Check last 3 parts
            if part == code or part.startswith(code):
                return code
    
    return ""

def format_wix_image_url(base_url: str, size: int = 400) -> str:
    """Format Wix image URL with proper size parameters"""
    if not base_url:
        return ""
    # Remove any existing size parameters and add our own
    if '/v1/fill/' in base_url:
        # Already has parameters, replace them
        parts = base_url.split('/v1/fill/')
        base = parts[0]
        # Get the filename after the parameters
        if '/' in parts[1]:
            filename = parts[1].split('/')[-1]
        else:
            filename = parts[1]
        return f"{base}/v1/fill/w_{size},h_{size},al_c,q_80/{filename}"
    else:
        # Add parameters
        return f"{base_url}/v1/fill/w_{size},h_{size},al_c,q_80/{base_url.split('/')[-1]}"

def get_product_image(handle: str, category: str, color_code: str = None) -> str:
    """
    Get product image based on color code and category.
    
    Priorité:
    1. Image spécifique à la catégorie + code couleur (CATEGORY_SPECIFIC_IMAGES)
    2. Image par code couleur universel (COLOR_CODE_IMAGES)
    3. Image par défaut de la catégorie (CATEGORY_DEFAULT_IMAGES)
    
    Args:
        handle: Le handle Wix du produit
        category: La catégorie du produit (genius, tape, etc.)
        color_code: Le code couleur optionnel (ex: "6", "HPS", "3/3T24")
    """
    if not handle and not color_code:
        return format_wix_image_url(CATEGORY_DEFAULT_IMAGES.get(category, CATEGORY_DEFAULT_IMAGES["genius"]))
    
    # Utiliser le code couleur fourni ou l'extraire du handle
    if not color_code:
        color_code = extract_color_code_from_handle(handle)
    
    # Normaliser le code couleur (minuscules pour la recherche)
    color_code_lower = color_code.lower() if color_code else ""
    
    if color_code_lower:
        # 1. Chercher d'abord dans les images spécifiques à la catégorie
        if category in CATEGORY_SPECIFIC_IMAGES:
            cat_images = CATEGORY_SPECIFIC_IMAGES[category]
            if color_code_lower in cat_images:
                return format_wix_image_url(cat_images[color_code_lower])
            if "default" in cat_images:
                return format_wix_image_url(cat_images["default"])
        
        # 2. Chercher dans le mapping universel par code couleur
        if color_code_lower in COLOR_CODE_IMAGES:
            return format_wix_image_url(COLOR_CODE_IMAGES[color_code_lower])
    
    # 3. Fallback: image par défaut de la catégorie
    return format_wix_image_url(CATEGORY_DEFAULT_IMAGES.get(category, CATEGORY_DEFAULT_IMAGES["genius"]))

# ==================== AUTH HELPERS ====================

async def get_current_user(request: Request) -> Optional[User]:
    """Get current user from session token in cookie or Authorization header"""
    session_token = request.cookies.get("session_token")
    
    if not session_token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            session_token = auth_header[7:]
    
    if not session_token:
        return None
    
    # Supabase: Récupérer la session
    session_doc = await db_get_session(session_token)
    
    if not session_doc:
        return None
    
    expires_at = session_doc["expires_at"]
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        return None
    
    # Supabase: Récupérer l'utilisateur
    user_doc = await db_get_user_by_id(session_doc["user_id"])
    
    if not user_doc:
        return None
    
    return User(**user_doc)

async def require_auth(request: Request) -> User:
    """Require authenticated user"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user

# ==================== AUTH ENDPOINTS ====================

@api_router.post("/auth/session")
async def exchange_session(request: Request, response: Response):
    """Exchange session_id for session_token"""
    body = await request.json()
    session_id = body.get("session_id")
    
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id required")
    
    # Call Emergent Auth to get user data
    async with httpx.AsyncClient() as client:
        auth_response = await client.get(
            "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
            headers={"X-Session-ID": session_id}
        )
    
    if auth_response.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    auth_data = auth_response.json()
    email = auth_data.get("email")
    name = auth_data.get("name")
    picture = auth_data.get("picture")
    session_token = auth_data.get("session_token")
    
    # Supabase: Find or create user
    existing_user = await db_get_user_by_email(email)
    
    if existing_user:
        user_id = existing_user["user_id"]
        await db_update_user(email, name, picture)
    else:
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        await db_create_user(user_id, email, name, picture)
    
    # Supabase: Create session
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    
    await db_delete_user_sessions(user_id)
    await db_create_session(session_token, user_id, expires_at)
    
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
        max_age=7 * 24 * 60 * 60
    )
    
    user_doc = await db_get_user_by_id(user_id)
    return user_doc

@api_router.get("/auth/me")
async def get_me(request: Request):
    """Get current authenticated user"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user.model_dump()

@api_router.post("/auth/logout")
async def logout(request: Request, response: Response):
    """Logout user"""
    session_token = request.cookies.get("session_token")
    if session_token:
        await db_delete_session(session_token)
    
    response.delete_cookie(key="session_token", path="/")
    return {"message": "Logged out successfully"}

# ==================== PRODUCT ENDPOINTS (from Luxura API) ====================

def is_variant_record(product: dict) -> bool:
    """Check if a product record is a variant (has wix_variant_id)"""
    options = product.get('options', {})
    return bool(options.get('wix_variant_id'))

def extract_variant_info(product: dict) -> dict:
    """Extract variant information from a product record"""
    options = product.get('options', {})
    choices = options.get('choices', {})
    
    # Parse the "Longeur" field which contains both length and weight
    longeur = choices.get('Longeur', '')
    
    # Parse formats like "20\" 50 grammes" or "18' 50 grammes"
    length = ''
    weight = ''
    
    if longeur:
        import re
        # Match patterns like: 20" 50 grammes, 18' 100 grammes, etc.
        match = re.match(r"(\d+[\"']?)\s*(\d+\s*grammes?)?", longeur.strip())
        if match:
            length = match.group(1) or ''
            weight = match.group(2) or ''
    
    return {
        'id': product.get('id'),
        'sku': product.get('sku'),
        'wix_variant_id': options.get('wix_variant_id'),
        'longeur_raw': longeur,
        'length': length,
        'weight': weight,
        'price': product.get('price', 0),
        'quantity': product.get('quantity', 0),
        'is_in_stock': product.get('is_in_stock', False)
    }

async def get_products_from_wix_fallback(
    category: Optional[str] = None,
    search: Optional[str] = None,
    in_stock: Optional[bool] = None
) -> List[Dict]:
    """
    Fallback: Récupère les produits directement depuis Wix API quand Luxura API est indisponible
    """
    try:
        wix_api_key = os.getenv("WIX_API_KEY")
        wix_site_id = os.getenv("WIX_SITE_ID")
        
        if not wix_api_key or not wix_site_id:
            logger.error("WIX_API_KEY ou WIX_SITE_ID non configuré pour le fallback")
            return []
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Query all products from Wix
            response = await client.post(
                f"{WIX_API_BASE}/stores/v1/products/query",
                headers={
                    "Authorization": wix_api_key,
                    "wix-site-id": wix_site_id,
                    "Content-Type": "application/json"
                },
                json={
                    "query": {
                        "paging": {"limit": 100}
                    },
                    "includeVariants": True
                }
            )
            
            if response.status_code != 200:
                logger.error(f"Wix fallback failed: {response.status_code} - {response.text[:200]}")
                return []
            
            data = response.json()
            wix_products = data.get("products", [])
            
            logger.info(f"📦 Wix fallback: {len(wix_products)} produits récupérés")
            
            result = []
            seen_handles = set()
            
            for p in wix_products:
                # Skip invisible products
                if not p.get("visible", True):
                    continue
                
                name = p.get("name", "")
                slug = p.get("slug", "")
                handle = slug  # Wix uses slug as handle
                
                # Skip duplicates
                if handle in seen_handles:
                    continue
                seen_handles.add(handle)
                
                # Skip test products
                if 'test' in name.lower():
                    continue
                
                # Detect category
                product_category = detect_category_from_handle(handle, name)
                if product_category is None:
                    continue
                
                # Filter by category if specified
                if category and product_category != category:
                    continue
                
                # Filter by search if specified
                if search:
                    search_lower = search.lower()
                    if search_lower not in name.lower() and search_lower not in slug.lower():
                        continue
                
                # Get price
                price_data = p.get("price", {}) or p.get("priceData", {})
                price = price_data.get("price", 0)
                
                # Get stock info
                stock_data = p.get("stock", {})
                is_in_stock = stock_data.get("inStock", True)
                
                # Filter by stock if specified
                if in_stock is not None:
                    if in_stock and not is_in_stock:
                        continue
                    if not in_stock and is_in_stock:
                        continue
                
                # Get image
                media = p.get("media", {})
                main_media = media.get("mainMedia", {})
                image_data = main_media.get("image", {})
                image_url = image_data.get("url", "")
                
                # Fallback image from our mapping
                if not image_url:
                    color_code = extract_color_code_from_name(name)
                    image_url = get_product_image(handle, product_category, color_code)
                
                # Get color code
                color_code = extract_color_code_from_name(name)
                
                # Series mapping
                series_map = {
                    "halo": "Everly",
                    "genius": "Vivian", 
                    "tape": "Aurora",
                    "i-tip": "Eleanor",
                    "ponytail": "Victoria",
                    "clip-in": "Sophia"
                }
                
                # Build Wix URL
                wix_url = f"https://www.luxuradistribution.com/product-page/{handle}" if handle else "https://www.luxuradistribution.com"
                
                product_data = {
                    "id": handle,
                    "name": name,
                    "price": price,
                    "description": clean_html(p.get("description", "")),
                    "category": product_category,
                    "series": series_map.get(product_category, "Luxura"),
                    "images": [image_url] if image_url else [],
                    "in_stock": is_in_stock,
                    "is_in_stock": is_in_stock,
                    "total_quantity": 10 if is_in_stock else 0,  # Estimate
                    "quantity": 10 if is_in_stock else 0,
                    "sku": p.get("sku", ""),
                    "wix_url": wix_url,
                    "handle": handle,
                    "color_code": color_code,
                    "variant_count": 0,
                    "luxura_id": p.get("id"),
                    "source": "wix_fallback"
                }
                
                result.append(product_data)
            
            # Sort by category order, then by name
            category_order = {'genius': 0, 'halo': 1, 'tape': 2, 'i-tip': 3, 'ponytail': 4, 'clip-in': 5, 'essentiels': 6}
            result.sort(key=lambda x: (category_order.get(x['category'], 99), x['name']))
            
            logger.info(f"✅ Wix fallback: {len(result)} produits retournés")
            return result
            
    except Exception as e:
        logger.error(f"Error in Wix fallback: {e}")
        import traceback
        traceback.print_exc()
        return []


@api_router.get("/products")
async def get_products(
    category: Optional[str] = None,
    search: Optional[str] = None,
    in_stock: Optional[bool] = None,
    include_variants: Optional[bool] = True  # Include variant details
):
    """Get all products from Luxura Inventory API - grouped by handle with variants
    ONLY returns: Genius, Tape (Bande Adhésive), I-Tip, Halo, Essentiels, Ponytail, Clip-in
    Falls back to Wix API if Luxura API is unavailable
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Fetch products AND inventory in parallel for accurate quantities
            products_task = client.get(f"{LUXURA_API_URL}/products")
            inventory_task = client.get(f"{LUXURA_API_URL}/inventory/view")
            
            products_response, inventory_response = await asyncio.gather(
                products_task, inventory_task, return_exceptions=True
            )
            
            # FALLBACK: If Luxura API fails, use Wix API directly
            if isinstance(products_response, Exception) or products_response.status_code != 200:
                logger.warning("⚠️ Luxura API unavailable, using Wix fallback")
                return await get_products_from_wix_fallback(category, search, in_stock)
            
            products = products_response.json()
            
            # Build inventory lookup by product name/sku for accurate quantities
            inventory_by_name = {}
            inventory_by_sku = {}
            inventory_by_key = {}  # New: lookup by type|color|size
            
            if not isinstance(inventory_response, Exception) and inventory_response.status_code == 200:
                inventory_data = inventory_response.json()
                for inv in inventory_data:
                    inv_name = inv.get('name', '')
                    inv_sku = inv.get('sku', '')
                    inv_qty = inv.get('quantity', 0)
                    if inv_name:
                        # Store by clean name (without variant suffix)
                        clean_inv_name = inv_name.split(' — ')[0].strip().lower()
                        if clean_inv_name not in inventory_by_name:
                            inventory_by_name[clean_inv_name] = 0
                        inventory_by_name[clean_inv_name] += inv_qty
                        # Also store full name
                        inventory_by_name[inv_name.lower()] = inventory_by_name.get(inv_name.lower(), 0) + inv_qty
                        
                        # NEW: Build key by type|color|size for better matching
                        ptype = get_product_type_for_inventory(inv_name, inv_sku)
                        color, size = extract_color_size_for_inventory(inv_name)
                        inv_key = f"{ptype}|{color}|{size}"
                        if inv_key not in inventory_by_key:
                            inventory_by_key[inv_key] = 0
                        inventory_by_key[inv_key] += inv_qty
                        
                    if inv_sku:
                        inventory_by_sku[inv_sku.upper()] = inventory_by_sku.get(inv_sku.upper(), 0) + inv_qty
            
            # NOUVEAU: Grouper par catégorie + code couleur pour éviter les doublons
            # Au lieu de grouper par handle (qui cause des doublons), on groupe par couleur unique
            products_by_dedup_key = {}
            
            # SKUs d'accessoires à exclure (pas des extensions capillaires)
            ACCESSORY_SKUS = {
                'brvolum', 'frotatif', 'wtapejr', 'ringcol', 'outkitins', 
                '35822369', 'wtultra60', 'p-tape', 'wtapec22'
            }
            
            for p in products:
                name = p.get('name', '')
                sku = (p.get('sku') or '').lower()
                
                # Skip accessory products (not hair extensions)
                if sku in ACCESSORY_SKUS:
                    continue
                
                # Skip products with "?" in name (broken/unmapped products)
                if '? #?' in name or name.endswith('? #?'):
                    continue
                
                # Skip test products
                if 'test' in name.lower() and p.get('price', 0) < 1:
                    continue
                
                handle = p.get('handle', '')
                if not handle:
                    continue
                
                # Detect category from handle - returns None for excluded products
                product_category = detect_category_from_handle(handle, name)
                
                # SKIP products with excluded categories (Clips, Ponytails, etc.)
                if product_category is None:
                    continue
                
                # SKIP products not in allowed categories
                if product_category not in ALLOWED_CATEGORIES:
                    continue
                
                # Filter by category if specified
                if category and product_category != category:
                    continue
                
                # Filter by search if specified
                if search:
                    search_lower = search.lower()
                    if search_lower not in name.lower() and search_lower not in (p.get('sku') or '').lower():
                        continue
                
                # NOUVEAU: Extraire le code couleur et créer une clé de déduplication
                color_code = extract_color_code_from_name(name)
                dedup_key = get_dedup_key(product_category, color_code, name)
                
                # Initialize dedup group if needed
                if dedup_key not in products_by_dedup_key:
                    products_by_dedup_key[dedup_key] = {
                        'parent': None,
                        'variants': [],
                        'category': product_category,
                        'color_code': color_code,
                        'any_in_stock': False,
                        'total_quantity': 0,
                        'handles': set(),  # Track all handles for this color
                        'best_handle': None  # The most specific handle for URLs
                    }
                
                # Track all handles for this product group
                products_by_dedup_key[dedup_key]['handles'].add(handle)
                
                # Select the best handle (prefer genius/tape specific handles over generic ones)
                current_best = products_by_dedup_key[dedup_key]['best_handle']
                if current_best is None:
                    products_by_dedup_key[dedup_key]['best_handle'] = handle
                elif product_category in handle.lower() and product_category not in current_best.lower():
                    # Prefer handles that contain the actual category name
                    products_by_dedup_key[dedup_key]['best_handle'] = handle
                
                # Check if this is a variant or parent
                if is_variant_record(p):
                    variant_info = extract_variant_info(p)
                    products_by_dedup_key[dedup_key]['variants'].append(variant_info)
                    
                    # Get real quantity from inventory - try multiple methods
                    sku = p.get('sku', '').upper()
                    variant_qty = 0
                    
                    # Method 1: Try by SKU
                    if sku in inventory_by_sku:
                        variant_qty = inventory_by_sku[sku]
                    else:
                        # Method 2: Try by type|color|size key
                        ptype = get_product_type_for_inventory(name, sku)
                        color, size = extract_color_size_for_inventory(name)
                        inv_key = f"{ptype}|{color}|{size}"
                        if inv_key in inventory_by_key:
                            variant_qty = inventory_by_key[inv_key]
                        else:
                            # Method 3: Try without size (parent level)
                            inv_key_no_size = f"{ptype}|{color}|"
                            if inv_key_no_size in inventory_by_key:
                                variant_qty = inventory_by_key[inv_key_no_size]
                    
                    variant_info['quantity'] = variant_qty
                    
                    # Update stock totals from variants
                    if variant_info['is_in_stock'] or variant_qty > 0:
                        products_by_dedup_key[dedup_key]['any_in_stock'] = True
                    products_by_dedup_key[dedup_key]['total_quantity'] += variant_qty
                else:
                    # This is a parent product - only set if we don't have one yet
                    if products_by_dedup_key[dedup_key]['parent'] is None:
                        products_by_dedup_key[dedup_key]['parent'] = p
                        
                        # Get real quantity from inventory - try multiple methods
                        clean_name = name.split(' — ')[0].strip().lower()
                        parent_qty = inventory_by_name.get(clean_name, 0)
                        
                        # If no match by name, try by type|color key
                        if parent_qty == 0:
                            ptype = get_product_type_for_inventory(name, p.get('sku', ''))
                            color, _ = extract_color_size_for_inventory(name)
                            inv_key = f"{ptype}|{color}|"
                            parent_qty = inventory_by_key.get(inv_key, 0)
                        
                        if parent_qty > 0:
                            products_by_dedup_key[dedup_key]['total_quantity'] += parent_qty
                            products_by_dedup_key[dedup_key]['any_in_stock'] = True
                        elif p.get('is_in_stock', False):
                            products_by_dedup_key[dedup_key]['any_in_stock'] = True
            
            # Build result from deduplicated products
            result = []
            for dedup_key, data in products_by_dedup_key.items():
                parent = data['parent']
                variants = data['variants']
                product_category = data['category']
                color_code = data['color_code']
                best_handle = data['best_handle']
                
                # If no parent, use first variant as base
                if parent is None and variants:
                    # Find a variant to use as base info
                    for v in variants:
                        if v.get('sku'):
                            parent = {'name': v.get('sku', '').split('-')[0] if v.get('sku') else best_handle}
                            break
                
                if parent is None:
                    continue
                
                name = parent.get('name', '')
                # Clean up name (remove variant suffix)
                clean_name = name.split(' — ')[0].strip()
                
                # TOUJOURS générer le nom de luxe depuis le handle pour TOUTES les catégories d'extensions
                # Cela garantit que les noms sont cohérents et utilisent la nomenclature Luxura
                if product_category in ['halo', 'genius', 'tape', 'i-tip', 'ponytail', 'clip-in']:
                    clean_name = generate_product_name_from_handle(best_handle, product_category)
                
                # Get image - use color_code for accurate image mapping
                image = get_product_image(best_handle, product_category, color_code)
                
                # Build Wix URL using the best handle
                wix_url = f"https://www.luxuradistribution.com/product-page/{best_handle}" if best_handle else "https://www.luxuradistribution.com"
                
                # Filter by stock if specified
                if in_stock is not None:
                    if in_stock and not data['any_in_stock']:
                        continue
                    if not in_stock and data['any_in_stock']:
                        continue
                
                # Get base price from parent or first variant
                price = parent.get('price', 0)
                if price == 0 and variants:
                    price = variants[0].get('price', 0)
                
                # Sort variants by length/weight and remove duplicates
                seen_variants = set()
                unique_variants = []
                for v in variants:
                    variant_key = f"{v.get('length', '')}|{v.get('weight', '')}"
                    if variant_key not in seen_variants:
                        seen_variants.add(variant_key)
                        unique_variants.append(v)
                
                sorted_variants = sorted(unique_variants, key=lambda v: (v.get('length', ''), v.get('weight', '')))
                
                # Mapping des séries par catégorie
                series_map = {
                    "halo": "Everly",
                    "genius": "Vivian", 
                    "tape": "Aurora",
                    "i-tip": "Eleanor",
                    "ponytail": "Victoria",
                    "clip-in": "Sophia"
                }
                
                # IMPORTANT: Use handle as the product ID for frontend navigation
                # This ensures consistency between list and detail pages
                # The handle is unique per product color variant in Wix
                product_data = {
                    "id": best_handle,  # Use handle as ID for consistent navigation
                    "name": clean_name,
                    "price": price,
                    "description": clean_html(parent.get('description', '')),
                    "category": product_category,
                    "series": series_map.get(product_category, "Luxura"),
                    "images": [image],
                    "in_stock": data['total_quantity'] > 0,  # Basé sur la quantité réelle, pas sur Wix
                    "is_in_stock": data['total_quantity'] > 0,
                    "total_quantity": data['total_quantity'],
                    "quantity": data['total_quantity'],  # Add quantity field for compatibility
                    "sku": parent.get('sku'),
                    "wix_url": wix_url,
                    "handle": best_handle,
                    "color_code": color_code,  # NEW: Expose color code
                    "variant_count": len(sorted_variants),
                    "luxura_id": parent.get('id')  # Keep original Luxura ID for reference
                }
                
                # Include variant details if requested
                if include_variants and sorted_variants:
                    product_data["variants"] = sorted_variants
                
                result.append(product_data)
            
            # Sort by category order, then by name
            category_order = {'genius': 0, 'halo': 1, 'tape': 2, 'i-tip': 3, 'ponytail': 4, 'clip-in': 5, 'essentiels': 6}
            result.sort(key=lambda x: (category_order.get(x['category'], 99), x['name']))
            
            return result
            
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Luxura API timeout")
    except Exception as e:
        logger.error(f"Error fetching products: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/products/{product_handle}")
async def get_product(product_handle: str):
    """Get a single product with all its variants from Luxura Inventory API
    Accepts handle (string) as identifier - this matches the ID used in /products list
    Fetches real inventory quantities from /inventory/view
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Fetch all products AND inventory in parallel
            # We search by handle instead of numeric ID
            all_products_task = client.get(f"{LUXURA_API_URL}/products")
            inventory_task = client.get(f"{LUXURA_API_URL}/inventory/view")
            
            all_response, inventory_response = await asyncio.gather(
                all_products_task, inventory_task, return_exceptions=True
            )
            
            if isinstance(all_response, Exception) or all_response.status_code != 200:
                raise HTTPException(status_code=502, detail="Unable to fetch products from Luxura API")
            
            all_products = all_response.json()
            
            # Find product by handle
            p = None
            matching_products = []
            for prod in all_products:
                if prod.get('handle') == product_handle:
                    matching_products.append(prod)
                    if p is None:
                        p = prod
            
            if not matching_products:
                raise HTTPException(status_code=404, detail="Product not found")
            
            handle = product_handle
            name = p.get('name', '')
            
            # Build inventory lookup by SKU AND by name for real quantities
            inventory_by_sku = {}
            inventory_by_name = {}
            if not isinstance(inventory_response, Exception) and inventory_response.status_code == 200:
                inventory_data = inventory_response.json()
                for inv in inventory_data:
                    inv_sku = inv.get('sku') or ''
                    inv_name = inv.get('name') or ''
                    inv_qty = inv.get('quantity') or 0
                    
                    # Index by SKU (uppercase)
                    if inv_sku and len(inv_sku) > 5:  # Valid SKU, not Wix UUID
                        inventory_by_sku[inv_sku.upper()] = inventory_by_sku.get(inv_sku.upper(), 0) + inv_qty
                    
                    # Index by full name (for exact matches)
                    if inv_name:
                        inv_name_lower = inv_name.lower().strip()
                        inventory_by_name[inv_name_lower] = inventory_by_name.get(inv_name_lower, 0) + inv_qty
            
            # Detect category from handle
            category = detect_category_from_handle(handle, name)
            
            # Get image from Wix mapping
            image = get_product_image(handle, category)
            
            # Build Wix URL
            wix_url = f"https://www.luxuradistribution.com/product-page/{handle}" if handle else "https://www.luxuradistribution.com"
            
            # Clean name (remove variant suffix)
            clean_name = name.split(' — ')[0].strip()
            
            # Générer le nom de luxe depuis le handle pour TOUTES les catégories d'extensions
            if category in ['halo', 'genius', 'tape', 'i-tip', 'ponytail', 'clip-in']:
                clean_name = generate_product_name_from_handle(handle, category)
            
            # Process variants with real inventory quantities
            if not isinstance(all_response, Exception) and all_response.status_code == 200:
                all_products = all_response.json()
                
                # Find all variants with same handle
                variants = []
                parent_product = None
                total_quantity = 0
                any_in_stock = False
                
                for prod in all_products:
                    if prod.get('handle') == handle:
                        if is_variant_record(prod):
                            variant_info = extract_variant_info(prod)
                            
                            # Get REAL quantity from inventory by SKU first, then by name
                            variant_sku = (prod.get('sku') or '').upper()
                            variant_name = (prod.get('name') or '').lower().strip()
                            real_qty = 0
                            
                            # Try SKU first (most accurate)
                            if variant_sku and variant_sku in inventory_by_sku:
                                real_qty = inventory_by_sku[variant_sku]
                            # Fallback to name match
                            elif variant_name and variant_name in inventory_by_name:
                                real_qty = inventory_by_name[variant_name]
                            
                            variant_info['quantity'] = real_qty
                            variant_info['is_in_stock'] = real_qty > 0
                            
                            variants.append(variant_info)
                            total_quantity += real_qty
                            if real_qty > 0:
                                any_in_stock = True
                        else:
                            parent_product = prod
                
                # Sort variants by length/weight
                variants = sorted(variants, key=lambda v: (v.get('length', ''), v.get('weight', '')))
                
                # Mapping des séries par catégorie
                series_map = {
                    "halo": "Everly",
                    "genius": "Vivian", 
                    "tape": "Aurora",
                    "i-tip": "Eleanor",
                    "ponytail": "Victoria",
                    "clip-in": "Sophia"
                }
                
                # Use parent product info if available
                if parent_product:
                    # Ne pas écraser clean_name si c'est un nom de luxe déjà généré
                    description = clean_html(parent_product.get('description', ''))
                else:
                    description = clean_html(p.get('description', ''))
                
                return {
                    "id": p.get('id'),
                    "name": clean_name,
                    "price": p.get('price', 0),
                    "description": description,
                    "category": category,
                    "series": series_map.get(category, "Luxura"),
                    "images": [image],
                    "in_stock": any_in_stock,
                    "total_quantity": total_quantity,
                    "sku": p.get('sku'),
                    "wix_url": wix_url,
                    "handle": handle,
                    "variants": variants if variants else None,
                    "variant_count": len(variants)
                }
            
            # Fallback if we can't get all products
            # Mapping des séries par catégorie
            series_map_fallback = {
                "halo": "Everly",
                "genius": "Vivian", 
                "tape": "Aurora",
                "i-tip": "Eleanor",
                "ponytail": "Victoria",
                "clip-in": "Sophia"
            }
            
            return {
                "id": p.get('id'),
                "name": clean_name,
                "price": p.get('price', 0),
                "description": clean_html(p.get('description', '')),
                "category": category,
                "series": series_map_fallback.get(category, "Luxura"),
                "images": [image],
                "in_stock": p.get('is_in_stock', False) or p.get('quantity', 0) > 0,
                "total_quantity": p.get('quantity', 0),
                "sku": p.get('sku'),
                "wix_url": wix_url,
                "handle": handle,
                "variants": None,
                "variant_count": 0
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching product: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== CATEGORY ENDPOINTS ====================

@api_router.get("/categories", response_model=List[Category])
async def get_categories():
    """Get all categories"""
    categories = [
        Category(id="genius", name="Genius", description="Extensions Genius Weft - Volume spectaculaire et confort", image="https://static.wixstatic.com/media/de6cdb_d16038b1f57044dabe702e8080aee3b4~mv2.jpg/v1/fill/w_600,h_600,q_85/pretty-woman-comic-book-art-full-body-shot.jpg", wix_url="https://www.luxuradistribution.com/genius", order=1),
        Category(id="halo", name="Halo", description="Extensions Halo - Effet naturel et invisible", image="https://static.wixstatic.com/media/de6cdb_6ad19e7a2a2749c8899daf8f972180fe~mv2.jpg/v1/fill/w_600,h_600,q_85/low-angle-young-woman-nature.jpg", wix_url="https://www.luxuradistribution.com/halo", order=2),
        Category(id="tape", name="Bande Adhésive", description="Extensions à bande adhésive professionnelle", image="https://static.wixstatic.com/media/de6cdb_8baf5d4bb6a14e0d9f8b302234b6f500~mv2.jpg/v1/fill/w_600,h_600,q_85/portrait-young-blonde-woman-with-with-tanned-skin-fashion-clothing.jpg", wix_url="https://www.luxuradistribution.com/tape", order=3),
        Category(id="i-tip", name="I-Tip", description="Extensions i-TIP - Précision et personnalisation", image="https://static.wixstatic.com/media/de6cdb_324e161652d54a5298af88e97359f00c~mv2.jpg/v1/fill/w_600,h_600,q_85/2024-11-29_11-29-28_edited.jpg", wix_url="https://www.luxuradistribution.com/i-tip", order=4),
        Category(id="ponytail", name="Queue de Cheval", description="Ponytail Victoria - Volume XXL instantané", image="https://static.wixstatic.com/media/f1b961_7ba6134ca87e4423817e9b0fa07754c1~mv2.png", wix_url="https://www.luxuradistribution.com/ponytail", order=5),
        Category(id="clip-in", name="Extensions à Clips", description="Clip-In Sophia - Volume et longueur sans engagement", image="https://static.wixstatic.com/media/f1b961_1e9953c3551440479117fa2954918173~mv2.png", wix_url="https://www.luxuradistribution.com/clip-in", order=6),
        Category(id="essentiels", name="Essentiels", description="Outils et produits d'entretien professionnels", image="https://static.wixstatic.com/media/de6cdb_5ba6af2b449d44039ce9c23d3517953b~mv2.jpg/v1/fill/w_600,h_600,q_85/s-l1200.jpg", wix_url="https://www.luxuradistribution.com/essentiels", order=7),
    ]
    return categories

# ==================== COLOR SYSTEM ENDPOINTS ====================

@api_router.get("/colors")
async def get_colors():
    """Get all Luxura colors with full info for filters and SEO"""
    return get_all_colors_for_filter()

@api_router.get("/colors/by-category")
async def get_colors_grouped_by_category():
    """Get all colors grouped by category (Noir, Brun, Caramel, Blond, Froid)"""
    return get_colors_by_category()

@api_router.get("/colors/by-type")
async def get_colors_grouped_by_type():
    """Get all colors grouped by type (Solid, Ombre, Balayage, Piano)"""
    return get_colors_by_type()

@api_router.get("/colors/detail/{color_code}")
async def get_color(color_code: str):
    """Get detailed info for a specific color code"""
    info = get_color_info(color_code)
    return {
        "code": color_code,
        **info
    }

@api_router.get("/colors/seo/{color_code}")
async def get_color_seo(color_code: str, product_type: str = "extensions"):
    """Get SEO description for a color"""
    info = get_color_info(color_code)
    return {
        "code": color_code,
        "luxura_name": info.get("luxura", ""),
        "seo_description": get_seo_description(color_code, product_type),
        "type": info.get("type", "SOLID"),
        "tone": info.get("tone", "NEUTRE")
    }


# ==================== SKU MIGRATION ENDPOINTS ====================

# MAPPING LUXE DES CODES COULEUR LUXURA
# Basé sur l'ANALYSE VISUELLE des images + codes standards
# Format: CODE -> (NOM_TECHNIQUE, NOM_LUXE, TYPE)

COLOR_CODE_MAPPING = {
    # ════════════════════ NOIRS INTENSES ════════════════════
    "1": ("JET-BLACK", "Onyx Intense", "SOLID"),           # Noir jet pur
    "1B": ("OFF-BLACK", "Noir Soie", "SOLID"),             # Noir naturel soyeux
    
    # ════════════════════ BRUNS LUXUEUX ════════════════════
    "2": ("ESPRESSO", "Espresso Intense", "SOLID"),        # Brun espresso
    "DB": ("DARK-MYSTERY", "Nuit Mystère", "SOLID"),       # Brun mystère foncé
    "DC": ("CHOCOLAT-PROFOND", "Chocolat Profond", "SOLID"),  # Brun foncé chocolat - PAS noir!
    "CACAO": ("CACAO-VELOURS", "Cacao Velours", "SOLID"),   # Brun cacao velouté
    "CHENGTU": ("SOIE-ORIENT", "Soie d'Orient", "SOLID"),   # Brun asiatique soyeux
    "FOOCHOW": ("CACHEMIRE-ORIENTAL", "Cachemire Oriental", "SOLID"), # Brun oriental
    
    # ════════════════════ BRUNS CHÂTAIGNE ════════════════════
    "3": ("CHESTNUT", "Châtaigne Naturelle", "SOLID"),     # Châtaigne unie
    "CINNAMON": ("CINNAMON-SPICE", "Cannelle Épicée", "SOLID"), # Cannelle chaude
    
    # ════════════════════ CHÂTAIGNE DIMENSION (Ombré + Piano) ════════════════════
    # Base #3 châtaigne + Ombré + Piano mèches #24 dorées
    "3/3T24": ("CHESTNUT-GOLDEN-DIMENSION", "Châtaigne Lumière Dorée", "OMBRE-PIANO"),
    
    # ════════════════════ CARAMEL & MIEL ════════════════════
    "6": ("CARAMEL", "Caramel Doré", "SOLID"),             # Caramel classique
    "BM": ("HONEY-WILD", "Miel Sauvage", "SOLID"),         # Brun miel naturel
    
    # ════════════════════ CARAMEL DIMENSION ════════════════════
    # Balayage caramel #6 vers doré #24
    "6/24": ("CARAMEL-BALAYAGE", "Golden Hour", "BALAYAGE"),
    # Caramel #6 + Ombré + Piano mèches #24 dorées
    "6/6T24": ("CARAMEL-GOLDEN-DIMENSION", "Caramel Soleil", "OMBRE-PIANO"),
    
    # ════════════════════ BLONDS PIANO HARMONISÉ ════════════════════
    # #18/22 = Ash blonde #18 + Light beige blonde #22 - PAS DE ROSE!
    # Analysé: blend harmonieux de blond cendré et beige doré, effet sun-kissed
    "18/22": ("CHAMPAGNE-DORE", "Champagne Doré", "PIANO"),
    
    # ════════════════════ BLONDS PLATINE ════════════════════
    "60A": ("PLATINUM", "Platine Pur", "SOLID"),           # Platine glacé
    "PHA": ("PURE-ASH", "Cendré Céleste", "SOLID"),        # Blond cendré pur
    # Platine #613 + balayage cendré #18A
    "613/18A": ("PLATINUM-BALAYAGE", "Diamant Glacé", "BALAYAGE"),
    
    # ════════════════════ BLANCS PRÉCIEUX ════════════════════
    "IVORY": ("IVOIRE-PRECIEUX", "Ivoire Précieux", "SOLID"), # Blanc ivoire
    "ICW": ("CRISTAL-POLAIRE", "Cristal Polaire", "SOLID"),   # Blanc glacé polaire
    
    # ════════════════════ OMBRÉS SIGNATURE ════════════════════
    "CB": ("HONEY-OMBRE", "Miel Sauvage Ombré", "OMBRE"),    # Ombré miel naturel
    "HPS": ("ASH-LUXE-OMBRE", "Cendré Étoilé", "OMBRE"),     # Ombré cendré luxe
    "5AT60": ("GLACIER-OMBRE", "Aurore Glaciale", "OMBRE"),  # Ombré vers platine
    "5ATP18B62": ("NORDIC-OMBRE", "Aurore Boréale", "OMBRE"), # Ombré nordique
    
    # ════════════════════ ESPRESSO DIMENSION ════════════════════
    "2BTP18/1006": ("ESPRESSO-LUMINOUS", "Espresso Lumière", "OMBRE-PIANO"),
    
    # ════════════════════ VÉNITIEN SIGNATURE ════════════════════
    # #T14/P14/24 = Ombré #14 (dark blonde) + Piano #14/#24 (ash + golden blonde)
    # Analysé: Blend sophistiqué multi-dimensionnel, ombré subtil avec piano highlights
    "T14/P14/24": ("VENISE-DOREE", "Venise Dorée", "OMBRE-PIANO"),
}

def get_color_info_from_code(color_code: str) -> tuple:
    """Obtenir les informations complètes de couleur à partir du code
    Retourne: (nom_technique, nom_luxe, type_coloration)
    """
    if not color_code:
        return ("UNKNOWN", "Inconnu", "SOLID")
    
    # Nettoyer le code
    clean_code = color_code.strip().upper()
    
    # Chercher correspondance exacte
    if clean_code in COLOR_CODE_MAPPING:
        return COLOR_CODE_MAPPING[clean_code]
    
    # Chercher correspondance sans /
    normalized = clean_code.replace("/", "-")
    for code, info in COLOR_CODE_MAPPING.items():
        if code.replace("/", "-") == normalized:
            return info
    
    # Fallback intelligent basé sur la structure du code
    color_type = "SOLID"
    
    # Détecter le type basé sur la structure
    if "T" in clean_code and "P" in clean_code:
        color_type = "OMBRE-PIANO"  # Transition + Piano
    elif "T" in clean_code:
        color_type = "OMBRE"  # Transition/Ombre
    elif "P" in clean_code:
        color_type = "PIANO"  # Piano/Mèches
    elif "/" in color_code and clean_code[0].isdigit():
        # Ex: 6/24 = balayage
        color_type = "BALAYAGE"
    
    # Générer un nom basé sur le niveau
    base_num = ''.join(filter(str.isdigit, clean_code[:2]))
    if base_num:
        level = int(base_num)
        if level <= 2:
            return (f"DARK-{clean_code.replace('/', '-')}", f"Brun Foncé {clean_code}", color_type)
        elif level <= 4:
            return (f"MEDIUM-{clean_code.replace('/', '-')}", f"Châtaigne {clean_code}", color_type)
        elif level <= 7:
            return (f"LIGHT-{clean_code.replace('/', '-')}", f"Caramel {clean_code}", color_type)
        else:
            return (f"BLONDE-{clean_code.replace('/', '-')}", f"Blond {clean_code}", color_type)
    
    return (clean_code.replace("/", "-"), clean_code, color_type)

def extract_color_info_for_sku(name: str) -> tuple:
    """Extraire le code couleur et le nom technique du nom du produit
    Retourne: (code_couleur, nom_technique)
    """
    if not name:
        return '', ''
    
    # Pattern pour trouver #CODE dans le nom
    code_match = re.search(r'#([A-Za-z0-9/]+)', name)
    color_code = code_match.group(1).upper() if code_match else ''
    
    # Obtenir les infos depuis le mapping
    tech_name, luxe_name, color_type = get_color_info_from_code(color_code)
    
    return color_code, tech_name

def generate_standardized_sku(product: dict) -> str:
    """Générer un SKU standardisé pour un produit
    Format: {TYPE}{LONGUEUR}{POIDS}-{CODE_COULEUR}-{NOM_SKU}
    Exemple: H20140-6-24-GOLDEN-HOUR
    """
    name = product.get('name') or ''
    handle = product.get('handle') or ''
    
    # Détecter le type de produit
    handle_lower = handle.lower()
    if 'halo' in handle_lower or 'everly' in handle_lower:
        prefix = 'H'
    elif 'genius' in handle_lower or 'vivian' in handle_lower:
        prefix = 'G'
    elif 'bande' in handle_lower or 'aurora' in handle_lower or 'tape' in handle_lower:
        prefix = 'T'
    elif 'i-tip' in handle_lower or 'eleanor' in handle_lower:
        prefix = 'I'
    else:
        prefix = 'E'  # Essentiels
    
    # Extraire longueur et poids du nom de variante
    length = ''
    weight = ''
    
    # Pattern: 20" 140 grammes ou 18" 25 grammes
    variant_match = re.search(r'(\d+)["\'\′]?\s*(\d+)\s*gram', name.lower())
    if variant_match:
        length = variant_match.group(1)
        weight = variant_match.group(2)
    
    # Extraire code couleur
    color_code, _ = extract_color_info_for_sku(name)
    
    # Obtenir le nom SKU depuis le système de couleurs
    color_info = get_color_info(color_code)
    sku_name = color_info.get("sku", color_code.replace("/", "-"))
    
    # Nettoyer le code couleur pour le SKU (remplacer / par -)
    clean_code = color_code.replace('/', '-')
    
    # Construire le SKU
    if length and weight:
        # Variante avec dimensions: H20140-6-24-GOLDEN-HOUR
        sku = f'{prefix}{length}{weight}-{clean_code}-{sku_name}'
    else:
        # Produit parent sans dimensions: H-6-24-GOLDEN-HOUR
        sku = f'{prefix}-{clean_code}-{sku_name}'
    
    return sku.upper()

@api_router.get("/sku/preview")
async def preview_sku_migration():
    """Prévisualiser les nouveaux SKUs sans les appliquer"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{LUXURA_API_URL}/products")
            if response.status_code != 200:
                raise HTTPException(status_code=502, detail="Unable to fetch products")
            
            products = response.json()
            
            preview = []
            for p in products:
                name = p.get('name') or ''
                handle = p.get('handle') or ''
                
                # Skip products that are not in our categories
                category = detect_category_from_handle(handle, name)
                if category is None:
                    continue
                
                old_sku = p.get('sku') or ''
                new_sku = generate_standardized_sku(p)
                
                # Only include if SKU would change
                if old_sku != new_sku:
                    preview.append({
                        "id": p.get('id'),
                        "name": name[:60],
                        "old_sku": old_sku or "AUCUN",
                        "new_sku": new_sku,
                        "category": category
                    })
            
            return {
                "total_products": len(products),
                "products_to_update": len(preview),
                "preview": preview[:100]  # Limit preview to 100 items
            }
            
    except Exception as e:
        logger.error(f"Error previewing SKU migration: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/sku/migrate")
async def migrate_skus(dry_run: bool = True, category: Optional[str] = None):
    """
    Migrer les SKUs vers le nouveau format standardisé
    - dry_run=True: Prévisualise uniquement (par défaut)
    - dry_run=False: Applique les changements
    - category: Filtrer par catégorie (genius, halo, tape, i-tip, essentiels)
    """
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(f"{LUXURA_API_URL}/products")
            if response.status_code != 200:
                raise HTTPException(status_code=502, detail="Unable to fetch products")
            
            products = response.json()
            
            results = {
                "dry_run": dry_run,
                "total_products": len(products),
                "updated": [],
                "skipped": [],
                "errors": []
            }
            
            for p in products:
                name = p.get('name') or ''
                handle = p.get('handle') or ''
                product_id = p.get('id')
                
                # Detect category
                prod_category = detect_category_from_handle(handle, name)
                if prod_category is None:
                    continue
                
                # Filter by category if specified
                if category and prod_category != category:
                    continue
                
                old_sku = p.get('sku') or ''
                new_sku = generate_standardized_sku(p)
                
                # Skip if SKU wouldn't change
                if old_sku == new_sku:
                    results["skipped"].append({
                        "id": product_id,
                        "name": name[:40],
                        "reason": "SKU already correct"
                    })
                    continue
                
                if dry_run:
                    results["updated"].append({
                        "id": product_id,
                        "name": name[:40],
                        "old_sku": old_sku or "AUCUN",
                        "new_sku": new_sku
                    })
                else:
                    # Actually update the product
                    try:
                        update_response = await client.put(
                            f"{LUXURA_API_URL}/products/{product_id}",
                            json={"sku": new_sku}
                        )
                        if update_response.status_code == 200:
                            results["updated"].append({
                                "id": product_id,
                                "name": name[:40],
                                "old_sku": old_sku or "AUCUN",
                                "new_sku": new_sku,
                                "status": "SUCCESS"
                            })
                        else:
                            results["errors"].append({
                                "id": product_id,
                                "name": name[:40],
                                "error": f"HTTP {update_response.status_code}"
                            })
                    except Exception as e:
                        results["errors"].append({
                            "id": product_id,
                            "name": name[:40],
                            "error": str(e)
                        })
            
            results["summary"] = {
                "updated_count": len(results["updated"]),
                "skipped_count": len(results["skipped"]),
                "error_count": len(results["errors"])
            }
            
            return results
            
    except Exception as e:
        logger.error(f"Error migrating SKUs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== CART ENDPOINTS ====================

@api_router.get("/cart")
async def get_cart(request: Request):
    """Get user's cart with product details"""
    user = await require_auth(request)
    
    # Supabase: Récupérer les items du panier
    cart_items = await db_get_cart_items(user.user_id)
    
    result = []
    total = 0
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for item in cart_items:
            try:
                response = await client.get(f"{LUXURA_API_URL}/products/{item['product_id']}")
                if response.status_code == 200:
                    p = response.json()
                    handle = p.get('handle', '')
                    name = p.get('name', '')
                    category = detect_category_from_handle(handle, name)
                    image = get_product_image(handle, category)
                    
                    product_data = {
                        "id": p.get('id'),
                        "name": name,
                        "price": p.get('price', 0),
                        "images": [image],
                        "in_stock": p.get('is_in_stock', False)
                    }
                    
                    item_total = p.get('price', 0) * item['quantity']
                    total += item_total
                    
                    result.append({
                        "id": item["id"],
                        "product": product_data,
                        "quantity": item["quantity"],
                        "item_total": item_total
                    })
            except Exception as e:
                logger.error(f"Error fetching product for cart: {e}")
    
    return {"items": result, "total": total, "count": len(result)}

@api_router.post("/cart")
async def add_to_cart(item: CartItemCreate, request: Request):
    """Add item to cart"""
    user = await require_auth(request)
    
    # Verify product exists in Luxura API
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{LUXURA_API_URL}/products/{item.product_id}")
        if response.status_code != 200:
            raise HTTPException(status_code=404, detail="Product not found")
    
    # Supabase: Check if item already in cart
    existing = await db_get_cart_item(user.user_id, item.product_id)
    
    if existing:
        new_quantity = existing["quantity"] + item.quantity
        await db_update_cart_item_by_product(user.user_id, item.product_id, new_quantity)
        return {"message": "Cart updated", "quantity": new_quantity}
    else:
        item_id = await db_add_cart_item(user.user_id, item.product_id, item.quantity)
        return {"message": "Added to cart", "id": item_id}

@api_router.put("/cart/{item_id}")
async def update_cart_item(item_id: str, update: CartItemUpdate, request: Request):
    """Update cart item quantity"""
    user = await require_auth(request)
    
    if update.quantity <= 0:
        await db_delete_cart_item(item_id, user.user_id)
        return {"message": "Item removed"}
    
    result = await db_update_cart_item(item_id, user.user_id, update.quantity)
    
    if not result:
        raise HTTPException(status_code=404, detail="Cart item not found")
    
    return {"message": "Cart updated"}

@api_router.delete("/cart/{item_id}")
async def remove_from_cart(item_id: str, request: Request):
    """Remove item from cart"""
    user = await require_auth(request)
    
    result = await db_delete_cart_item(item_id, user.user_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="Cart item not found")
    
    return {"message": "Item removed"}

@api_router.delete("/cart")
async def clear_cart(request: Request):
    """Clear all items from cart"""
    user = await require_auth(request)
    await db_clear_cart(user.user_id)
    return {"message": "Cart cleared"}

# ==================== BLOG ENDPOINTS ====================

# Blog images variées basées sur le sujet - Extensions cheveux professionnelles
BLOG_IMAGES = {
    # Images de salons et stylistes
    "salon": [
        "https://images.unsplash.com/photo-1560066984-138dadb4c035?w=800&q=80",  # Salon moderne
        "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=800&q=80",  # Coiffeuse professionnelle
        "https://images.unsplash.com/photo-1595475884562-073c30d45670?w=800&q=80",  # Salon luxe
        "https://images.unsplash.com/photo-1633681926035-ec1ac984418a?w=800&q=80",  # Styling
    ],
    # Images de cheveux et extensions
    "hair": [
        "https://images.unsplash.com/photo-1519699047748-de8e457a634e?w=800&q=80",  # Cheveux longs blonds
        "https://images.unsplash.com/photo-1580618672591-eb180b1a973f?w=800&q=80",  # Cheveux bruns luxueux
        "https://images.unsplash.com/photo-1522337094846-8a818192de1f?w=800&q=80",  # Cheveux ondulés
        "https://images.unsplash.com/photo-1605497788044-5a32c7078486?w=800&q=80",  # Cheveux brillants
        "https://images.unsplash.com/photo-1492106087820-71f1a00d2b11?w=800&q=80",  # Portrait femme cheveux
    ],
    # Images mariage et événements
    "wedding": [
        "https://images.unsplash.com/photo-1519741497674-611481863552?w=800&q=80",  # Mariée coiffure
        "https://images.unsplash.com/photo-1511285560929-80b456fea0bc?w=800&q=80",  # Préparation mariée
        "https://images.unsplash.com/photo-1595981234058-a9302fb97620?w=800&q=80",  # Coiffure élégante
    ],
    # Images tendances et mode
    "trends": [
        "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=800&q=80",  # Portrait mode
        "https://images.unsplash.com/photo-1517841905240-472988babdf9?w=800&q=80",  # Femme stylée
        "https://images.unsplash.com/photo-1529626455594-4ff0802cfb7e?w=800&q=80",  # Cheveux colorés
    ],
    # Images soins et entretien
    "care": [
        "https://images.unsplash.com/photo-1527799820374-dcf8d9d4a388?w=800&q=80",  # Produits capillaires
        "https://images.unsplash.com/photo-1522338140262-f46f5913618a?w=800&q=80",  # Soins cheveux
        "https://images.unsplash.com/photo-1616394584738-fc6e612e71b9?w=800&q=80",  # Brossage
    ],
    # Images B2B et professionnelles
    "b2b": [
        "https://images.unsplash.com/photo-1556742049-0cfed4f6a45d?w=800&q=80",  # Business meeting
        "https://images.unsplash.com/photo-1600880292203-757bb62b4baf?w=800&q=80",  # Équipe pro
        "https://images.unsplash.com/photo-1521737711867-e3b97375f902?w=800&q=80",  # Partenariat
    ],
}

def get_blog_image_for_topic(topic: str, keywords: list = None) -> str:
    """Sélectionne une image appropriée basée sur le sujet et les mots-clés"""
    import random
    topic_lower = topic.lower()
    
    # Mapping sujet → catégorie d'image
    if any(word in topic_lower for word in ['mariage', 'wedding', 'cérémonie', 'événement']):
        category = 'wedding'
    elif any(word in topic_lower for word in ['entretien', 'soin', 'laver', 'brush', 'care']):
        category = 'care'
    elif any(word in topic_lower for word in ['tendance', 'trend', '2025', 'mode', 'style']):
        category = 'trends'
    elif any(word in topic_lower for word in ['fournisseur', 'salon', 'professionnel', 'partenaire', 'b2b', 'grossiste']):
        category = 'b2b'
    elif any(word in topic_lower for word in ['technique', 'genius', 'tape', 'halo', 'installation']):
        category = 'salon'
    else:
        category = 'hair'
    
    # Sélectionner une image aléatoire de la catégorie
    images = BLOG_IMAGES.get(category, BLOG_IMAGES['hair'])
    return random.choice(images)

# SEO Keywords for Luxura Distribution - Hair Extensions Quebec
SEO_KEYWORDS = {
    "commercial": [
        "extensions capillaires Québec",
        "extensions cheveux naturel Québec",
        "acheter extensions cheveux professionnel",
        "extensions cheveux haut de gamme Canada",
        "rallonges cheveux naturel invisibles",
        "extensions trame invisible Québec",
        "extensions Genius weft Québec",
        "extensions cheveux salon professionnel"
    ],
    "long_tail": [
        "extensions cheveux blond balayage 20 pouces",
        "trame invisible cheveux naturel prix Québec",
        "extensions Genius weft avis Canada",
        "extensions cheveux pour salon professionnel fournisseur",
        "rallonges cheveux naturels sans colle",
        "extensions cheveux couture invisible durable",
        "extensions cheveux Remy vs synthétique différence",
        "extensions cheveux pour cheveux fins solution"
    ],
    "problems": [
        "cheveux fins que faire solution",
        "comment ajouter du volume cheveux",
        "perte de cheveux femme solution esthétique",
        "cheveux clairsemés femme solution",
        "comment épaissir cheveux naturellement"
    ],
    "b2b": [
        "fournisseur extensions cheveux Québec salon",
        "distributeur extensions capillaires Canada",
        "grossiste extensions cheveux professionnel",
        "extensions cheveux dépôt salon",
        "partenariat salon extensions cheveux",
        "extensions cheveux wholesale Canada"
    ],
    "branding": [
        "extensions cheveux luxe Québec",
        "extensions capillaires premium Canada",
        "extensions cheveux haut de gamme salon",
        "qualité professionnelle extensions cheveux",
        "extensions cheveux 100% naturels vierges"
    ]
}

BLOG_TOPICS = [
    {
        "topic": "Comment choisir ses extensions cheveux - Guide complet",
        "keywords": ["commercial", "long_tail"],
        "meta_description": "Guide expert pour choisir vos extensions cheveux naturel au Québec. Comparatif Genius Weft, Tape-in, Halo."
    },
    {
        "topic": "Extensions Genius Weft vs Tape-in : Quelle technique choisir ?",
        "keywords": ["commercial", "long_tail"],
        "meta_description": "Comparaison détaillée entre extensions Genius Weft et Tape-in. Avantages, durabilité et prix au Québec."
    },
    {
        "topic": "Solution cheveux fins : Extensions invisibles pour volume naturel",
        "keywords": ["problems", "long_tail"],
        "meta_description": "Découvrez comment les extensions trame invisible transforment les cheveux fins en chevelure volumineuse."
    },
    {
        "topic": "Fournisseur extensions cheveux salon : Pourquoi choisir Luxura",
        "keywords": ["b2b", "branding"],
        "meta_description": "Luxura Distribution - Votre partenaire grossiste extensions cheveux professionnelles au Québec et Canada."
    },
    {
        "topic": "Entretien extensions cheveux : Guide professionnel",
        "keywords": ["long_tail", "branding"],
        "meta_description": "Conseils d'experts pour entretenir vos extensions cheveux naturel. Durée de vie 12-18 mois garantie."
    },
    {
        "topic": "Tendances coiffure 2025 : Extensions balayage et couleurs naturelles",
        "keywords": ["long_tail", "branding"],
        "meta_description": "Les tendances extensions cheveux 2025 au Québec. Balayage blond, ombré naturel et couleurs luxe."
    },
    {
        "topic": "Extensions cheveux pour mariage : Transformation spectaculaire",
        "keywords": ["commercial", "problems"],
        "meta_description": "Extensions cheveux pour mariage au Québec. Volume et longueur spectaculaires pour le grand jour."
    },
    {
        "topic": "Cheveux clairsemés femme : Solutions professionnelles",
        "keywords": ["problems", "branding"],
        "meta_description": "Solutions extensions cheveux pour femmes aux cheveux clairsemés. Résultats naturels garantis."
    }
]

class BlogGenerateRequest(BaseModel):
    topic_index: Optional[int] = None

@api_router.get("/blog/keywords")
async def get_seo_keywords():
    """Get available SEO keywords for blog generation"""
    return {
        "keywords": SEO_KEYWORDS,
        "topics": [{"index": i, "topic": t["topic"], "meta": t["meta_description"]} for i, t in enumerate(BLOG_TOPICS)]
    }

@api_router.post("/blog/generate")
async def generate_seo_blog():
    """Generate a new SEO-optimized blog post using AI"""
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        import random
        
        emergent_key = os.getenv("EMERGENT_LLM_KEY")
        if not emergent_key:
            raise HTTPException(status_code=500, detail="EMERGENT_LLM_KEY not configured")
        
        # Get existing blog posts to avoid duplicates - Supabase
        existing_titles = await db_get_blog_titles()
        existing_titles = [t.lower() for t in existing_titles]
        
        # Select a topic that hasn't been covered
        available_topics = [t for t in BLOG_TOPICS if t["topic"].lower() not in existing_titles]
        
        if not available_topics:
            available_topics = BLOG_TOPICS
        
        topic_data = random.choice(available_topics)
        
        # Collect relevant keywords
        keywords_to_use = []
        for cat in topic_data["keywords"]:
            keywords_to_use.extend(random.sample(SEO_KEYWORDS[cat], min(3, len(SEO_KEYWORDS[cat]))))
        
        # Generate blog content using AI
        chat = LlmChat(
            api_key=emergent_key,
            session_id=f"blog-gen-{uuid.uuid4().hex[:8]}",
            system_message="""Tu es un expert SEO francophone spécialisé dans les extensions capillaires au Québec. 
Tu écris pour Luxura Distribution, le leader des extensions cheveux haut de gamme au Canada.
Ton style est professionnel, informatif et engageant. Tu utilises naturellement les mots-clés SEO fournis.
Tu connais parfaitement les produits: Genius Weft (trame invisible révolutionnaire), Tape-in, Halo, I-Tip.
IMPORTANT: Réponds UNIQUEMENT en français québécois."""
        ).with_model("openai", "gpt-4.1-mini")
        
        prompt = f"""Écris un article de blog SEO complet pour Luxura Distribution.

SUJET: {topic_data["topic"]}

MOTS-CLÉS À INTÉGRER NATURELLEMENT:
{', '.join(keywords_to_use)}

STRUCTURE REQUISE:
1. Titre accrocheur (H1) - inclure un mot-clé principal
2. Introduction (150 mots) - hook + présentation du sujet
3. Section 1 avec sous-titre H2
4. Section 2 avec sous-titre H2  
5. Section 3 avec sous-titre H2
6. Conclusion avec appel à l'action vers Luxura Distribution

CONSIGNES:
- Longueur totale: 800-1000 mots
- Intégrer les mots-clés naturellement (3-5 fois chacun)
- Mentionner Luxura Distribution comme expert
- Inclure des conseils pratiques
- Ton professionnel mais accessible
- Utiliser des listes à puces quand pertinent

FORMAT DE RÉPONSE (JSON):
{{
  "title": "Titre SEO optimisé",
  "excerpt": "Résumé de 150 caractères pour les aperçus",
  "content": "Contenu complet de l'article avec balises HTML basiques (h2, p, ul, li)",
  "meta_description": "Description meta SEO de 155 caractères max",
  "tags": ["tag1", "tag2", "tag3"]
}}"""

        user_message = UserMessage(text=prompt)
        response = await chat.send_message(user_message)
        
        # Parse the JSON response
        import json
        response_text = response.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        try:
            blog_data = json.loads(response_text.strip())
        except json.JSONDecodeError:
            import re
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                blog_data = json.loads(json_match.group())
            else:
                raise HTTPException(status_code=500, detail="Failed to parse AI response")
        
        # Create blog post document with varied image based on topic
        post_id = f"seo-{uuid.uuid4().hex[:8]}"
        topic_title = blog_data.get("title", topic_data["topic"])
        blog_image = get_blog_image_for_topic(topic_title, keywords_to_use)
        
        blog_post = {
            "id": post_id,
            "title": topic_title,
            "excerpt": blog_data.get("excerpt", topic_data["meta_description"]),
            "content": blog_data.get("content", ""),
            "meta_description": blog_data.get("meta_description", topic_data["meta_description"]),
            "tags": blog_data.get("tags", keywords_to_use[:5]),
            "image": blog_image,
            "author": "Luxura Distribution",
            "created_at": datetime.now(timezone.utc),
            "seo_keywords": keywords_to_use,
            "auto_generated": True
        }
        
        # Supabase: Create blog post
        await db_create_blog_post(blog_post)
        
        if isinstance(blog_post.get("created_at"), datetime):
            blog_post["created_at"] = blog_post["created_at"].isoformat()
        
        return {
            "success": True,
            "message": "Article SEO généré avec succès",
            "post": blog_post
        }
        
    except Exception as e:
        logger.error(f"Error generating blog: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.delete("/blog/{post_id}")
async def delete_blog_post_endpoint(post_id: str):
    """Delete a blog post"""
    result = await db_delete_blog_post(post_id)
    if not result:
        raise HTTPException(status_code=404, detail="Post not found")
    return {"message": "Post deleted successfully"}

# =====================================================
# BLOG AUTOMATIQUE - 2 blogs/jour + Publication Wix
# =====================================================

@api_router.post("/blog/auto-generate")
async def auto_generate_daily_blogs(
    count: int = 2,
    publish_to_wix: bool = True,
    publish_to_facebook: bool = False,
    category: str = None,
    custom_topic: str = None
):
    """
    Génère automatiquement des blogs SEO et les publie sur Wix et/ou Facebook.
    
    Args:
        count: Nombre de blogs à générer (défaut: 2)
        publish_to_wix: Publier sur Wix Blog (défaut: True)
        publish_to_facebook: Publier sur Facebook Page (défaut: False)
        category: Forcer une catégorie spécifique (halo, itip, tape, genius)
        custom_topic: Sujet personnalisé (optionnel)
    """
    try:
        from blog_automation import generate_daily_blogs, BLOG_TOPICS_EXTENDED
        
        openai_key = os.getenv("EMERGENT_LLM_KEY") or os.getenv("OPENAI_API_KEY")
        if not openai_key:
            raise HTTPException(status_code=500, detail="EMERGENT_LLM_KEY ou OPENAI_API_KEY non configuré")
        
        wix_api_key = os.getenv("WIX_API_KEY")
        wix_site_id = os.getenv("WIX_SITE_ID")
        fb_access_token = os.getenv("FB_PAGE_ACCESS_TOKEN")
        fb_page_id = os.getenv("FB_PAGE_ID")
        
        results = await generate_daily_blogs(
            db=None,  # Migration Supabase: le paramètre db n'est plus utilisé
            openai_key=openai_key,
            wix_api_key=wix_api_key,
            wix_site_id=wix_site_id,
            publish_to_wix=publish_to_wix,
            count=count,
            fb_access_token=fb_access_token,
            fb_page_id=fb_page_id,
            publish_to_facebook=publish_to_facebook,
            force_category=category
        )
        
        return {
            "success": True,
            "message": f"{len(results)} blog(s) générés avec succès",
            "posts": results,
            "published_to_wix": any(p.get("published_to_wix") for p in results),
            "published_to_facebook": any(p.get("published_to_facebook") for p in results)
        }
        
    except Exception as e:
        logger.error(f"Error in auto-generate blogs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/cron/status")
async def get_cron_status():
    """Retourne le statut du scheduler CRON et les prochaines exécutions"""
    global blog_scheduler
    
    try:
        from editorial_calendar import (
            get_current_rotation_week,
            get_weekly_schedule,
            get_cron_category,
            should_publish_today
        )
        CALENDAR_AVAILABLE = True
    except ImportError:
        CALENDAR_AVAILABLE = False
    
    status = {
        "scheduler_running": blog_scheduler.running if blog_scheduler else False,
        "timezone": "America/Montreal",
        "current_time": datetime.now(timezone.utc).isoformat(),
        "facebook_enabled": bool(os.getenv("FB_PAGE_ACCESS_TOKEN")) and bool(os.getenv("FB_PAGE_ID")),
        "wix_enabled": bool(os.getenv("WIX_API_KEY")) and bool(os.getenv("WIX_SITE_ID")),
    }
    
    if CALENDAR_AVAILABLE:
        should_pub, reason = should_publish_today()
        status.update({
            "calendar_available": True,
            "rotation_week": get_current_rotation_week(),
            "today_category": get_cron_category(),
            "should_publish_today": should_pub,
            "publish_reason": reason,
            "weekly_schedule": get_weekly_schedule()
        })
    else:
        status["calendar_available"] = False
    
    # Liste des jobs programmés
    if blog_scheduler:
        jobs = []
        for job in blog_scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None
            })
        status["scheduled_jobs"] = jobs
    
    return status

@api_router.post("/cron/trigger-now")
async def trigger_blog_generation_now():
    """Force la génération immédiate d'un blog avec publication Facebook"""
    try:
        from blog_automation import generate_daily_blogs
        from editorial_calendar import get_cron_category
        
        # Récupérer la catégorie du jour ou fallback
        try:
            category = get_cron_category()
        except:
            category = 'entretien'
        
        openai_key = os.getenv("EMERGENT_LLM_KEY") or os.getenv("OPENAI_API_KEY")
        wix_api_key = os.getenv("WIX_API_KEY")
        wix_site_id = os.getenv("WIX_SITE_ID")
        fb_access_token = os.getenv("FB_PAGE_ACCESS_TOKEN")
        fb_page_id = os.getenv("FB_PAGE_ID")
        
        if not openai_key:
            raise HTTPException(status_code=500, detail="EMERGENT_LLM_KEY ou OPENAI_API_KEY non configuré")
        
        results = await generate_daily_blogs(
            db=None,  # Migration Supabase: le paramètre db n'est plus utilisé
            openai_key=openai_key,
            wix_api_key=wix_api_key,
            wix_site_id=wix_site_id,
            count=1,
            send_email=True,
            publish_to_wix=False,  # Brouillon Wix uniquement (validation humaine)
            publish_to_facebook=True,  # Publication Facebook automatique
            fb_access_token=fb_access_token,
            fb_page_id=fb_page_id,
            force_category=category
        )
        
        return {
            "success": True,
            "message": f"Blog généré avec succès - catégorie: {category}",
            "blog_count": len(results),
            "facebook_published": any(r.get("published_to_facebook") for r in results),
            "wix_draft_created": any(r.get("wix_draft_id") for r in results),
            "posts": results
        }
        
    except Exception as e:
        logger.error(f"Error in trigger-now: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))



@api_router.get("/blog/wix-posts")
async def list_wix_blog_posts(limit: int = 50):
    """Liste les blogs publiés sur Wix"""
    try:
        wix_api_key = os.getenv("WIX_API_KEY")
        wix_site_id = os.getenv("WIX_SITE_ID")
        
        if not wix_api_key or not wix_site_id:
            raise HTTPException(status_code=500, detail="WIX_API_KEY ou WIX_SITE_ID non configuré")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{WIX_API_BASE}/blog/v3/posts/query",
                headers={
                    "Authorization": wix_api_key,
                    "wix-site-id": wix_site_id,
                    "Content-Type": "application/json"
                },
                json={
                    "paging": {"limit": limit},
                    "sort": [{"fieldName": "firstPublishedDate", "order": "DESC"}]
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=f"Wix API error: {response.text}")
            
            data = response.json()
            posts = data.get("posts", [])
            
            return {
                "total": len(posts),
                "posts": [
                    {
                        "id": p.get("id"),
                        "title": p.get("title"),
                        "excerpt": p.get("excerpt", "")[:100],
                        "url": p.get("url"),
                        "coverMedia": p.get("media", {}).get("wixMedia", {}).get("image", {}).get("url"),
                        "firstPublishedDate": p.get("firstPublishedDate"),
                        "slug": p.get("slug")
                    }
                    for p in posts
                ]
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing Wix posts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/blog/regenerate-images/{wix_post_id}")
async def regenerate_blog_images(wix_post_id: str, background_tasks: BackgroundTasks):
    """
    Régénère les images d'un blog Wix existant avec le système V5 (images techniques réalistes).
    Met à jour le blog sur Wix avec les nouvelles images.
    """
    try:
        from blog_automation import (
            create_wix_draft_post, 
            publish_wix_draft,
            html_to_ricos
        )
        from image_generation import generate_and_upload_blog_images
        from image_brief_generator import generate_image_brief
        
        wix_api_key = os.getenv("WIX_API_KEY")
        wix_site_id = os.getenv("WIX_SITE_ID")
        
        if not wix_api_key or not wix_site_id:
            raise HTTPException(status_code=500, detail="WIX_API_KEY ou WIX_SITE_ID non configuré")
        
        # 1. Récupérer le blog existant sur Wix
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{WIX_API_BASE}/blog/v3/posts/{wix_post_id}",
                headers={
                    "Authorization": wix_api_key,
                    "wix-site-id": wix_site_id
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=404, detail=f"Blog non trouvé sur Wix: {response.text}")
            
            wix_post = response.json().get("post", {})
        
        title = wix_post.get("title", "")
        content_text = wix_post.get("excerpt", "") + " " + title
        
        # Détecter la catégorie depuis le contenu
        category = "general"
        content_lower = content_text.lower()
        if "genius" in content_lower or "weft" in content_lower:
            category = "genius"
        elif "tape" in content_lower or "adhésif" in content_lower:
            category = "tape"
        elif "i-tip" in content_lower or "itip" in content_lower or "kératine" in content_lower:
            category = "itip"
        elif "halo" in content_lower:
            category = "halo"
        
        # 2. Générer le brief et les nouvelles images V5
        blog_data = {
            "title": title,
            "content": content_text,
            "excerpt": wix_post.get("excerpt", ""),
            "category": category
        }
        
        brief = generate_image_brief(blog_data)
        logger.info(f"🎨 Regenerating images for: {title[:50]}... (Mode: {brief['visual_mode']})")
        
        cover_data, content_data = await generate_and_upload_blog_images(
            api_key=wix_api_key,
            site_id=wix_site_id,
            category=category,
            blog_title=title,
            blog_data=blog_data
        )
        
        if not cover_data:
            raise HTTPException(status_code=500, detail="Échec de génération des images")
        
        # 3. Note: Wix API ne permet pas de mettre à jour les images d'un post publié directement
        # On retourne les nouvelles URLs pour mise à jour manuelle ou via Velo
        
        return {
            "success": True,
            "message": f"Images régénérées pour: {title[:50]}...",
            "wix_post_id": wix_post_id,
            "brief_mode": brief["visual_mode"],
            "is_technical": brief.get("is_technical", False),
            "new_images": {
                "cover": cover_data.get("static_url") if cover_data else None,
                "content": content_data.get("static_url") if content_data else None
            },
            "note": "Les images ont été uploadées sur Wix Media. Pour mettre à jour le blog, utilisez l'éditeur Wix ou l'API Velo."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error regenerating images: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/blog/regenerate-all-images")
async def regenerate_all_blog_images(limit: int = 10):
    """
    Régénère les images de tous les blogs récents avec le système V5.
    Retourne les nouvelles URLs d'images.
    """
    try:
        from image_generation import generate_and_upload_blog_images
        from image_brief_generator import generate_image_brief
        
        wix_api_key = os.getenv("WIX_API_KEY")
        wix_site_id = os.getenv("WIX_SITE_ID")
        
        if not wix_api_key or not wix_site_id:
            raise HTTPException(status_code=500, detail="WIX_API_KEY ou WIX_SITE_ID non configuré")
        
        # 1. Lister les blogs Wix
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{WIX_API_BASE}/blog/v3/posts/query",
                headers={
                    "Authorization": wix_api_key,
                    "wix-site-id": wix_site_id,
                    "Content-Type": "application/json"
                },
                json={
                    "paging": {"limit": limit},
                    "sort": [{"fieldName": "firstPublishedDate", "order": "DESC"}]
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=f"Wix API error")
            
            posts = response.json().get("posts", [])
        
        results = []
        
        for post in posts:
            try:
                title = post.get("title", "")
                content_text = post.get("excerpt", "") + " " + title
                
                # Détecter catégorie
                category = "general"
                content_lower = content_text.lower()
                if "genius" in content_lower or "weft" in content_lower:
                    category = "genius"
                elif "tape" in content_lower or "adhésif" in content_lower:
                    category = "tape"
                elif "i-tip" in content_lower or "itip" in content_lower:
                    category = "itip"
                elif "halo" in content_lower:
                    category = "halo"
                
                blog_data = {
                    "title": title,
                    "content": content_text,
                    "category": category
                }
                
                brief = generate_image_brief(blog_data)
                logger.info(f"🎨 [{len(results)+1}/{len(posts)}] Regenerating: {title[:40]}... (Mode: {brief['visual_mode']})")
                
                cover_data, content_data = await generate_and_upload_blog_images(
                    api_key=wix_api_key,
                    site_id=wix_site_id,
                    category=category,
                    blog_title=title,
                    blog_data=blog_data
                )
                
                results.append({
                    "wix_post_id": post.get("id"),
                    "title": title[:50],
                    "mode": brief["visual_mode"],
                    "success": cover_data is not None,
                    "new_cover_url": cover_data.get("static_url") if cover_data else None,
                    "new_content_url": content_data.get("static_url") if content_data else None
                })
                
            except Exception as post_error:
                logger.error(f"Error processing post {post.get('id')}: {post_error}")
                results.append({
                    "wix_post_id": post.get("id"),
                    "title": post.get("title", "")[:50],
                    "success": False,
                    "error": str(post_error)
                })
        
        return {
            "success": True,
            "total_processed": len(results),
            "successful": sum(1 for r in results if r.get("success")),
            "results": results,
            "note": "Les images ont été uploadées sur Wix Media. Mettez à jour les blogs manuellement dans l'éditeur Wix."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in regenerate-all: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/blog/topics")
async def get_blog_topics():
    """Liste tous les sujets de blog disponibles par catégorie"""
    try:
        from blog_automation import BLOG_TOPICS_EXTENDED
        
        # Grouper par catégorie
        by_category = {}
        for topic in BLOG_TOPICS_EXTENDED:
            cat = topic["category"]
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append({
                "topic": topic["topic"],
                "keywords": topic["keywords"],
                "focus_product": topic.get("focus_product")
            })
        
        return {
            "total_topics": len(BLOG_TOPICS_EXTENDED),
            "categories": by_category
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/blog/publish-to-wix/{post_id}")
async def publish_blog_to_wix(post_id: str):
    """Publie un blog existant sur Wix"""
    try:
        from blog_automation import create_wix_draft_post, publish_wix_draft
        
        # Supabase: Récupérer le blog
        post = await db_get_blog_post(post_id)
        if not post:
            raise HTTPException(status_code=404, detail="Blog non trouvé")
        
        if post.get("published_to_wix"):
            return {"message": "Blog déjà publié sur Wix", "wix_post_id": post.get("wix_post_id")}
        
        wix_api_key = os.getenv("WIX_API_KEY")
        wix_site_id = os.getenv("WIX_SITE_ID")
        
        if not wix_api_key or not wix_site_id:
            raise HTTPException(status_code=500, detail="Configuration Wix manquante")
        
        # Créer et publier le draft
        wix_result = await create_wix_draft_post(
            api_key=wix_api_key,
            site_id=wix_site_id,
            title=post["title"],
            content=post["content"],
            excerpt=post.get("excerpt", ""),
            cover_image=post.get("image", ""),
            tags=post.get("tags", [])
        )
        
        if wix_result:
            draft_id = wix_result.get("draftPost", {}).get("id")
            if draft_id:
                published = await publish_wix_draft(wix_api_key, wix_site_id, draft_id)
                if published:
                    await db_update_blog_post(post_id, {"published_to_wix": True, "wix_post_id": draft_id})
                    return {"success": True, "message": "Blog publié sur Wix", "wix_post_id": draft_id}
        
        raise HTTPException(status_code=500, detail="Échec de la publication sur Wix")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error publishing to Wix: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/blog")
async def get_blog_posts_endpoint():
    """Get all blog posts with varied images"""
    import random
    
    # Supabase: Récupérer les posts
    posts = await db_get_blog_posts(100)
    
    # Update any posts that have the old static image
    old_static_image = "https://static.wixstatic.com/media/de6cdb_ed493ddeab524054935dfbf0714b7e29~mv2.jpg"
    
    for post in posts:
        if post.get("image") == old_static_image:
            # Assign a varied image based on title
            new_image = get_blog_image_for_topic(post.get("title", ""))
            post["image"] = new_image
            # Update in database
            await db_update_blog_post(post["id"], {"image": new_image})
    
    if not posts:
        # Default posts with varied images
        default_posts = [
            {
                "id": "entretien-extensions",
                "title": "Comment entretenir vos extensions capillaires",
                "content": "Les extensions capillaires nécessitent un entretien régulier pour maintenir leur beauté et leur durabilité.",
                "excerpt": "Découvrez nos conseils d'experts pour maintenir vos extensions.",
                "image": get_blog_image_for_topic("entretien soin extensions"),
                "author": "Luxura Distribution",
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": "guide-genius-weft",
                "title": "Extensions Genius Weft : Guide complet pour professionnels",
                "content": "La technique Genius Weft révolutionne l'industrie des extensions capillaires au Québec.",
                "excerpt": "Tout savoir sur les extensions Genius Weft - la trame invisible révolutionnaire.",
                "image": get_blog_image_for_topic("salon professionnel technique"),
                "author": "Luxura Distribution",
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": "tendances-2025",
                "title": "Tendances coiffure 2025 : Balayage et extensions naturelles",
                "content": "Les tendances capillaires évoluent vers plus de naturel et de sophistication.",
                "excerpt": "Les couleurs et styles qui domineront 2025 au Québec.",
                "image": get_blog_image_for_topic("tendances mode style 2025"),
                "author": "Luxura Distribution",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
        ]
        return default_posts
    
    return posts

@api_router.get("/blog/{post_id}")
async def get_blog_post_by_id(post_id: str):
    """Get a single blog post"""
    post = await db_get_blog_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post

# ==================== WIX INTEGRATION & SEO MACHINE ====================

async def get_wix_access_token():
    """Get OAuth access token from Luxura API"""
    if not WIX_INSTANCE_ID:
        return None
    try:
        async with httpx.AsyncClient(timeout=15.0) as http_client:
            response = await http_client.post(
                f"{LUXURA_RENDER_API}/wix/token",
                params={"instance_id": WIX_INSTANCE_ID}
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("access_token")
    except Exception as e:
        logger.error(f"Error getting Wix token: {e}")
    return None

def get_wix_headers():
    """Get Wix API headers (for simple API key auth)"""
    return {
        "Authorization": WIX_API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json",
        "wix-site-id": WIX_SITE_ID,
    }

def get_wix_oauth_headers(access_token: str):
    """Get Wix API headers with OAuth token"""
    return {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

@api_router.get("/wix/capabilities")
async def get_wix_capabilities():
    """Check what we can do with Wix API - Hero, Blog, etc."""
    
    # Try to get OAuth token
    oauth_token = await get_wix_access_token()
    
    capabilities = {
        "api_configured": bool(WIX_API_KEY and WIX_SITE_ID),
        "oauth_configured": bool(WIX_INSTANCE_ID),
        "oauth_working": bool(oauth_token),
        "available_apis": {
            "stores": {
                "products": "✅ READ/WRITE - Modifier produits, descriptions SEO, prix",
                "inventory": "✅ READ/WRITE - Gérer stock multi-salons",
                "collections": "✅ READ - Lire les collections/catégories",
                "variants": "✅ READ/WRITE - Modifier variantes"
            },
            "blog": {
                "posts": "✅ CREATE/UPDATE - Publier articles SEO automatiquement",
                "categories": "✅ READ/WRITE - Organiser par catégories",
                "tags": "✅ READ/WRITE - Tags SEO"
            },
            "site": {
                "pages": "⚠️ LIMITED - Lecture seule via CMS",
                "hero_sections": "💡 VIA CMS - Crée une collection 'site_content' dans Wix CMS",
                "seo_settings": "✅ WRITE - Meta titles, descriptions par page"
            },
            "marketing": {
                "coupons": "✅ CREATE - Créer codes promo",
                "email_marketing": "⚠️ SEPARATE API"
            }
        },
        "luxura_api": {
            "url": LUXURA_RENDER_API,
            "wix_token_endpoint": f"{LUXURA_RENDER_API}/wix/token",
            "wix_seo_push": f"{LUXURA_RENDER_API}/wix/seo/push_one",
        },
        "luxura_specific": {
            "product_seo": "✅ Déjà implémenté - 2665 descriptions optimisées",
            "color_names": "✅ Déjà implémenté - Noms luxe (Noir Ébène, etc.)",
            "blog_automation": "✅ Prêt - Génération quotidienne SEO",
            "wix_push": "🔧 Via Luxura API OAuth"
        },
        "hero_modification_guide": {
            "step1": "Dans Wix Editor, crée une Collection CMS appelée 'site_content'",
            "step2": "Ajoute les champs: hero_title, hero_subtitle, hero_cta, hero_image",
            "step3": "Connecte ton Hero à cette collection via Dynamic Pages",
            "step4": "L'API peut alors modifier le contenu via Wix Data API",
            "note": "C'est la seule façon de modifier le Hero via API - Wix bloque la modification directe du design"
        }
    }
    
    # Test connection via OAuth if available
    if oauth_token:
        try:
            async with httpx.AsyncClient(timeout=10.0) as http_client:
                response = await http_client.post(
                    f"{WIX_API_BASE}/stores/v1/products/query",
                    headers=get_wix_oauth_headers(oauth_token),
                    json={"query": {"paging": {"limit": 1}}}
                )
                capabilities["wix_connection_oauth"] = "✅ CONNECTÉ via OAuth" if response.status_code == 200 else f"❌ Erreur {response.status_code}"
        except Exception as e:
            capabilities["wix_connection_oauth"] = f"❌ {str(e)}"
    else:
        capabilities["wix_connection_oauth"] = "⚠️ WIX_INSTANCE_ID non configuré"
    
    return capabilities

@api_router.post("/wix/blog/push/{post_id}")
async def push_blog_to_wix(post_id: str):
    """Push a blog post to Wix Blog"""
    if not WIX_API_KEY or not WIX_SITE_ID:
        raise HTTPException(status_code=500, detail="Wix API not configured")
    
    # Supabase: Get the blog post from our DB
    post = await db_get_blog_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as http_client:
            # Create draft post on Wix Blog
            wix_post_data = {
                "post": {
                    "title": post.get("title"),
                    "excerpt": post.get("excerpt", "")[:140],
                    "richContent": {
                        "nodes": [
                            {
                                "type": "PARAGRAPH",
                                "id": str(uuid.uuid4()),
                                "nodes": [{"type": "TEXT", "textData": {"text": post.get("content", "").replace("<p>", "").replace("</p>", "\n\n").replace("<h2>", "\n\n## ").replace("</h2>", "\n\n")}}]
                            }
                        ]
                    },
                    "seoData": {
                        "tags": [
                            {"type": "title", "props": {"content": post.get("title")}},
                            {"type": "meta", "props": {"name": "description", "content": post.get("meta_description", post.get("excerpt", ""))}}
                        ]
                    },
                    "featured": False
                }
            }
            
            response = await http_client.post(
                f"{WIX_API_BASE}/blog/v3/draft-posts",
                headers=get_wix_headers(),
                json=wix_post_data
            )
            
            if response.status_code in [200, 201]:
                wix_response = response.json()
                # Supabase: Update our record with Wix ID
                await db_update_blog_post(post_id, {
                    "wix_post_id": wix_response.get("draftPost", {}).get("id"),
                    "pushed_to_wix": True
                })
                return {
                    "success": True,
                    "message": "Article publié sur Wix (brouillon)",
                    "wix_post_id": wix_response.get("draftPost", {}).get("id"),
                    "note": "L'article est en brouillon. Publie-le depuis ton dashboard Wix."
                }
            else:
                return {
                    "success": False,
                    "error": response.text,
                    "status_code": response.status_code,
                    "note": "Wix Blog API peut nécessiter une configuration supplémentaire"
                }
                
    except Exception as e:
        logger.error(f"Error pushing to Wix: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/seo/daily-generation")
async def trigger_daily_seo_generation(background_tasks: BackgroundTasks):
    """Trigger daily SEO content generation - Can be called by external CRON"""
    
    async def generate_daily_content():
        """Background task to generate SEO content"""
        try:
            from emergentintegrations.llm.chat import LlmChat, UserMessage
            import random
            
            emergent_key = os.getenv("EMERGENT_LLM_KEY")
            if not emergent_key:
                logger.error("EMERGENT_LLM_KEY not configured")
                return
            
            # Supabase: Get existing posts to avoid duplicates
            existing_titles = await db_get_blog_titles()
            existing_titles = [t.lower() for t in existing_titles]
            
            # Extended topics for B2B focus (salons as partners)
            EXTENDED_TOPICS = [
                {
                    "topic": "Devenir partenaire Luxura : Programme salon extensions Québec",
                    "keywords": ["b2b", "branding"],
                    "meta_description": "Programme partenariat Luxura pour salons. Devenez distributeur extensions cheveux au Québec."
                },
                {
                    "topic": "Grossiste extensions cheveux Canada : Avantages pour votre salon",
                    "keywords": ["b2b", "commercial"],
                    "meta_description": "Luxura grossiste extensions cheveux professionnel. Prix distributeur pour salons au Canada."
                },
                {
                    "topic": "Formation extensions cheveux : Devenez expert Luxura",
                    "keywords": ["b2b", "branding"],
                    "meta_description": "Formation professionnelle extensions capillaires. Certification Luxura pour salons partenaires."
                },
                {
                    "topic": "Augmenter revenus salon : Extensions cheveux haut de gamme",
                    "keywords": ["b2b", "commercial"],
                    "meta_description": "Comment augmenter les revenus de votre salon avec extensions cheveux premium Luxura."
                },
                {
                    "topic": "Extensions cheveux en ligne Québec : Livraison rapide garantie",
                    "keywords": ["commercial", "long_tail"],
                    "meta_description": "Achetez extensions cheveux en ligne au Québec. Livraison express Luxura Distribution."
                }
            ]
            
            # Combine with existing topics
            all_topics = BLOG_TOPICS + EXTENDED_TOPICS
            available_topics = [t for t in all_topics if t["topic"].lower() not in existing_titles]
            
            if not available_topics:
                available_topics = all_topics
            
            topic_data = random.choice(available_topics)
            
            # Collect keywords with backlink-friendly terms
            keywords_to_use = []
            for cat in topic_data["keywords"]:
                if cat in SEO_KEYWORDS:
                    keywords_to_use.extend(random.sample(SEO_KEYWORDS[cat], min(3, len(SEO_KEYWORDS[cat]))))
            
            # Add internal backlink anchors
            internal_links = [
                "extensions Genius Weft Luxura",
                "extensions Tape-in professionnelles",
                "extensions Halo invisibles",
                "programme partenaire salon Luxura"
            ]
            
            chat = LlmChat(
                api_key=emergent_key,
                session_id=f"daily-seo-{uuid.uuid4().hex[:8]}",
                system_message="""Tu es un expert SEO francophone spécialisé dans les extensions capillaires au Québec.
Tu écris pour Luxura Distribution, importateur et leader des extensions cheveux haut de gamme au Canada.
MISSION LUXURA: Aider les salons à bâtir leur game d'extensions en tant que partenaires, ET vendre directement en ligne.
Tu intègres des liens internes naturellement dans le contenu.
IMPORTANT: Réponds UNIQUEMENT en français québécois professionnel."""
            ).with_model("openai", "gpt-4.1-mini")
            
            prompt = f"""Écris un article de blog SEO complet pour Luxura Distribution.

CONTEXTE BUSINESS:
- Luxura est importateur d'extensions cheveux haut de gamme
- Ils aident les salons à devenir partenaires et bâtir leur expertise extensions
- Ils vendent aussi directement en ligne aux consommateurs
- Marché cible: Québec et Canada

SUJET: {topic_data["topic"]}

MOTS-CLÉS SEO À INTÉGRER:
{', '.join(keywords_to_use)}

LIENS INTERNES À INCLURE (sous forme de texte ancré):
{', '.join(internal_links)}

STRUCTURE:
1. Titre H1 accrocheur avec mot-clé principal
2. Introduction (150 mots) - hook puissant
3. Section 1 (H2) - Problème/opportunité
4. Section 2 (H2) - Solution Luxura
5. Section 3 (H2) - Avantages concrets / témoignages
6. Conclusion avec CTA vers Luxura

CONSIGNES:
- 800-1000 mots
- Ton professionnel mais accessible
- Inclure des chiffres et statistiques quand pertinent
- Mentionner les avantages pour les salons ET consommateurs

FORMAT JSON:
{{
  "title": "...",
  "excerpt": "...",
  "content": "...",
  "meta_description": "...",
  "tags": ["...", "..."],
  "internal_links": ["url1", "url2"]
}}"""

            user_message = UserMessage(text=prompt)
            response = await chat.send_message(user_message)
            
            # Parse response
            response_text = response.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            try:
                blog_data = json.loads(response_text.strip())
            except json.JSONDecodeError:
                json_match = re.search(r'\{[\s\S]*\}', response_text)
                if json_match:
                    blog_data = json.loads(json_match.group())
                else:
                    logger.error("Failed to parse AI response for daily blog")
                    return
            
            # Create blog post with backlinks
            post_id = f"daily-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:4]}"
            blog_post = {
                "id": post_id,
                "title": blog_data.get("title", topic_data["topic"]),
                "excerpt": blog_data.get("excerpt", topic_data["meta_description"]),
                "content": blog_data.get("content", ""),
                "meta_description": blog_data.get("meta_description", topic_data["meta_description"]),
                "tags": blog_data.get("tags", keywords_to_use[:5]),
                "image": "https://static.wixstatic.com/media/de6cdb_ed493ddeab524054935dfbf0714b7e29~mv2.jpg",
                "author": "Luxura Distribution",
                "created_at": datetime.now(timezone.utc),
                "seo_keywords": keywords_to_use,
                "internal_links": blog_data.get("internal_links", []),
                "auto_generated": True,
                "generation_type": "daily_cron"
            }
            
            # Supabase: Create blog post
            await db_create_blog_post(blog_post)
            logger.info(f"Daily SEO blog generated: {blog_post['title']}")
            
            # Supabase: Log to SEO history
            await db_create_seo_log({
                "blog_id": post_id,
                "title": blog_post["title"],
                "category": topic_data.get("keywords", ["general"])[0] if topic_data.get("keywords") else "general",
                "status": "generated"
            })
            
        except Exception as e:
            logger.error(f"Daily SEO generation error: {e}")
            await db_create_seo_log({
                "title": "Error",
                "status": f"error: {str(e)[:100]}"
            })
    
    # Run in background
    background_tasks.add_task(generate_daily_content)
    
    return {
        "success": True,
        "message": "Génération SEO quotidienne démarrée en arrière-plan",
        "tip": "Configure un CRON externe pour appeler cet endpoint chaque jour à minuit"
    }

@api_router.get("/seo/backlink-opportunities")
async def get_backlink_opportunities():
    """Get external backlink opportunities and strategy"""
    
    opportunities = {
        "directories_quebec": [
            {"name": "Pages Jaunes Québec", "url": "https://www.pagesjaunes.ca", "type": "directory", "priority": "HIGH"},
            {"name": "Yelp Québec", "url": "https://www.yelp.ca", "type": "reviews", "priority": "HIGH"},
            {"name": "Google My Business", "url": "https://business.google.com", "type": "local_seo", "priority": "CRITICAL"},
            {"name": "IndexBeauté.ca", "url": "https://indexbeaute.ca", "type": "industry", "priority": "HIGH"},
        ],
        "industry_blogs": [
            {"name": "Elle Québec", "url": "https://www.ellequebec.com", "type": "magazine", "approach": "Guest post / PR"},
            {"name": "Clin d'œil", "url": "https://www.clindoeil.ca", "type": "magazine", "approach": "Product feature"},
            {"name": "Beautélive", "url": "https://beautylive.ca", "type": "blog", "approach": "Sponsored content"},
        ],
        "salon_partnerships": {
            "strategy": "Chaque salon partenaire = backlink naturel",
            "implementation": [
                "Page 'Où nous trouver' avec liens vers salons partenaires",
                "Salons mettent 'Extensions par Luxura' sur leur site",
                "Échange de liens légitimes (partenariat réel)"
            ],
            "potential_backlinks": "50+ si 50 salons partenaires"
        },
        "social_signals": [
            {"platform": "Instagram", "handle": "@luxuradistribution", "priority": "CRITICAL"},
            {"platform": "Facebook", "handle": "Luxura Distribution", "priority": "HIGH"},
            {"platform": "Pinterest", "handle": "luxuradistribution", "priority": "MEDIUM", "note": "Excellent pour cheveux/beauté"},
            {"platform": "TikTok", "handle": "@luxuradistribution", "priority": "HIGH", "note": "Tutoriels extensions viraux"},
        ],
        "content_linkable": [
            "Infographie: Types d'extensions comparées",
            "Guide PDF: Formation extensions pour salons",
            "Calculateur: Combien d'extensions me faut-il?",
            "Vidéo YouTube: Tutoriel pose Genius Weft"
        ],
        "automated_actions": {
            "blog_generation": "✅ ACTIF - 1 article SEO/jour",
            "wix_push": "🔧 Prêt - Push vers Wix Blog",
            "internal_linking": "✅ ACTIF - Liens entre articles",
            "external_outreach": "❌ Manuel - Nécessite intervention humaine"
        }
    }
    
    return opportunities

@api_router.get("/seo/stats")
async def get_seo_stats():
    """Get SEO generation statistics"""
    
    # Supabase: Get counts
    total_posts = await db_count_blog_posts()
    auto_generated = await db_count_blog_posts({"auto_generated": True})
    pushed_to_wix = await db_count_blog_posts({"pushed_to_wix": True})
    
    # Supabase: Get recent generation logs
    recent_logs = await db_get_seo_logs(10)
    
    return {
        "total_blog_posts": total_posts,
        "auto_generated_posts": auto_generated,
        "pushed_to_wix": pushed_to_wix,
        "recent_generations": [
            {
                "date": log.get("date").isoformat() if log.get("date") else None,
                "title": log.get("title"),
                "status": log.get("status")
            } for log in recent_logs
        ],
        "top_keywords_used": [],  # Simplified - no keyword tracking in new schema
        "recommendation": "Configure un CRON pour appeler POST /api/seo/daily-generation chaque jour"
    }

@api_router.get("/seo/luxura-business-info")
async def get_luxura_business_info():
    """Get Luxura business info for manual directory submissions"""
    return {
        "company": {
            "name": "Luxura Distribution",
            "name_full": "Luxura Distribution Inc.",
            "description": "Importateur et distributeur direct d'extensions capillaires professionnelles au Québec. Qualité salon haut de gamme, approvisionnement fiable et transparent.",
        },
        "headquarters": {
            "address": "1887, 83e Rue",
            "city": "St-Georges",
            "province": "Québec",
            "postal_code": "G6A 1M9",
            "country": "Canada",
            "full_address": "1887, 83e Rue, St-Georges, Québec, Canada G6A 1M9"
        },
        "contact": {
            "phone": "(418) 222-3939",
            "email": "info@luxuradistribution.com",
            "website": "https://www.luxuradistribution.com"
        },
        "showroom": {
            "name": "Salon Carouso",
            "website": "https://www.saloncarouso.com",
            "note": "Partenaire showroom pour voir les produits en personne"
        },
        "social_media": {
            "instagram": "https://www.instagram.com/luxura_distribution/",
            "facebook_messenger": "https://m.me/1838415193042352"
        },
        "categories": [
            "Extensions capillaires",
            "Produits de coiffure professionnels",
            "Distributeur beauté",
            "Grossiste cheveux",
            "Fournisseur salon",
            "Hair Extensions",
            "Beauty Supplies Wholesale"
        ],
        "seo_keywords": [
            "extensions cheveux québec",
            "extensions capillaires professionnelles",
            "genius weft quebec",
            "tape-in extensions canada",
            "fournisseur extensions salon",
            "grossiste extensions cheveux",
            "rallonges cheveux naturels"
        ],
        "business_hours": "Lundi-Vendredi: 9h-17h",
        "submission_checklist": [
            "✅ Google My Business (CRITIQUE)",
            "✅ Pages Jaunes Canada",
            "✅ Yelp Canada",
            "✅ 411.ca",
            "✅ Canpages.ca",
            "✅ Hotfrog.ca",
            "✅ Cylex.ca",
            "✅ IndexBeauté.ca (industrie)",
            "✅ Pinterest (créer pins produits)"
        ]
    }

@api_router.post("/backlinks/run")
async def run_backlink_automation(background_tasks: BackgroundTasks):
    """Run Playwright automation to submit to business directories"""
    
    async def run_automation():
        import subprocess
        import os
        
        # Create screenshots directory
        os.makedirs("/tmp/backlinks", exist_ok=True)
        
        # Run the backlink automation script
        try:
            result = subprocess.run(
                ["python3", "/app/backend/backlink_automation.py"],
                capture_output=True,
                text=True,
                timeout=300,
                cwd="/app/backend"
            )
            
            # Supabase: Log results
            await db_create_backlink_run({
                "directory": "backlink_automation",
                "status": "success" if result.returncode == 0 else f"exit_code_{result.returncode}",
                "message": result.stdout[:500] if result.stdout else None
            })
            
            logger.info(f"Backlink automation completed with code {result.returncode}")
            
        except subprocess.TimeoutExpired:
            await db_create_backlink_run({
                "directory": "backlink_automation",
                "status": "timeout",
                "message": "Timeout after 5 minutes"
            })
        except Exception as e:
            await db_create_backlink_run({
                "directory": "backlink_automation",
                "status": "error",
                "message": str(e)[:500]
            })
    
    background_tasks.add_task(run_automation)
    
    return {
        "success": True,
        "message": "Automatisation backlinks démarrée en arrière-plan",
        "note": "Vérifiez /api/backlinks/status pour les résultats"
    }

@api_router.get("/backlinks/status")
async def get_backlink_status():
    """Get status of backlink automation runs"""
    
    # Supabase: Get backlink runs
    runs = await db_get_backlink_runs(10)
    
    # Get screenshots if any
    screenshots = []
    if os.path.exists("/tmp/backlinks"):
        screenshots = os.listdir("/tmp/backlinks")
    
    # Get verification status
    verification_status = {}
    status_file = "/tmp/backlinks/verification_status.json"
    if os.path.exists(status_file):
        try:
            with open(status_file, 'r') as f:
                verification_status = json.load(f)
        except:
            pass
    
    return {
        "recent_runs": [
            {
                "date": run.get("date").isoformat() if run.get("date") else None,
                "status": run.get("status"),
                "message": run.get("message"),
                "directory": run.get("directory")
            } for run in runs
        ],
        "screenshots": screenshots,
        "screenshots_path": "/tmp/backlinks",
        "verification_status": verification_status
    }

@api_router.post("/backlinks/auto-verify")
async def start_auto_verification(background_tasks: BackgroundTasks):
    """Start automatic verification loop - checks every 10 minutes until all verified"""
    
    async def run_auto_verify():
        import subprocess
        try:
            # Run verification loop with 30 iterations, 10 minute intervals
            result = subprocess.run(
                ["python3", "/app/backend/auto_verification_loop.py", "30", "10"],
                capture_output=True,
                text=True,
                timeout=18000,  # 5 hours max
                cwd="/app/backend"
            )
            
            await db_create_backlink_run({
                "directory": "auto_verify_loop",
                "status": "success" if result.returncode == 0 else f"exit_code_{result.returncode}",
                "message": result.stdout[-500:] if result.stdout else None
            })
            
        except subprocess.TimeoutExpired:
            await db_create_backlink_run({
                "directory": "auto_verify_loop",
                "status": "completed",
                "message": "Loop completed after 5 hours"
            })
        except Exception as e:
            await db_create_backlink_run({
                "directory": "auto_verify_loop",
                "status": "error",
                "message": str(e)[:500]
            })
    
    background_tasks.add_task(run_auto_verify)
    
    return {
        "success": True,
        "message": "🔄 Boucle de vérification automatique démarrée!",
        "details": {
            "check_interval": "10 minutes",
            "max_duration": "5 heures",
            "email": "info@luxuradistribution.com"
        },
        "note": "Vérifiez /api/backlinks/status pour voir la progression"
    }

@api_router.get("/backlinks/verification-status")
async def get_verification_status():
    """Get current verification status for all directories"""
    
    status_file = "/tmp/backlinks/verification_status.json"
    status = {}
    
    if os.path.exists(status_file):
        try:
            with open(status_file, 'r') as f:
                status = json.load(f)
        except:
            pass
    
    verified_count = sum(1 for d in status.values() if d.get("verified"))
    submitted_count = sum(1 for d in status.values() if d.get("submitted"))
    
    return {
        "directories": status,
        "summary": {
            "verified": verified_count,
            "submitted": submitted_count,
            "pending": submitted_count - verified_count
        },
        "all_verified": verified_count >= submitted_count and submitted_count > 0
    }

# ==================== WIX SKU DIRECT PATCH (Format CHOICES corrigé) ====================

class WixVariantSkuPatch(BaseModel):
    """Modèle pour patcher un SKU de variante Wix"""
    wix_product_id: str
    variants: List[Dict[str, str]]  # [{"choice": "16\" 120 grammes", "sku": "H-16-120-3-3T24"}]

@api_router.post("/wix/patch-variant-skus")
async def patch_wix_variant_skus(data: WixVariantSkuPatch, secret: str = ""):
    """
    Patcher les SKU des variantes Wix directement avec le format CHOICES corrigé.
    
    ⚠️ BUG WIX API V1: L'utilisation de {"id": "...", "sku": "..."} applique le MÊME SKU
    à TOUTES les variantes du produit.
    
    ✅ SOLUTION: Utiliser {"choices": {"Longeur": "16\" 120 grammes"}, "variant": {"sku": "..."}}
    pour identifier précisément chaque variante.
    
    Args:
        data.wix_product_id: ID du produit Wix (ex: "c2e7afd1-810f-4003-9693-839d1912a818")
        data.variants: Liste de variantes à patcher
            [{"choice": "16\" 120 grammes", "sku": "H-16-120-3-3T24"}]
        secret: Secret pour authentification
    """
    # Vérifier le secret
    expected_secret = "9f3c2b8a7d1e4c5b9a0d7e6f3b2c1a9f"
    if secret != expected_secret:
        raise HTTPException(status_code=401, detail="Invalid secret")
    
    try:
        # Obtenir le token OAuth depuis l'API Render
        async with httpx.AsyncClient(timeout=60.0) as client:
            # D'abord obtenir un token frais
            token_response = await client.post(
                f"{LUXURA_RENDER_API}/wix/token",
                params={"instance_id": "ab8a5a88-69a5-4348-ad2e-06017de46f57"}
            )
            
            if token_response.status_code != 200:
                raise HTTPException(
                    status_code=502, 
                    detail=f"Failed to get Wix token: {token_response.text}"
                )
            
            token_data = token_response.json()
            access_token = token_data.get("access_token", "")
            
            if not access_token:
                raise HTTPException(status_code=502, detail="No access token returned")
            
            # Construire le payload avec le format CHOICES (LA SOLUTION AU BUG!)
            wix_variants = []
            for v in data.variants:
                wix_variants.append({
                    "choices": {"Longeur": v["choice"]},  # "Longeur" est le nom de l'option dans Wix
                    "variant": {"sku": v["sku"]}
                })
            
            payload = {"variants": wix_variants}
            
            # Appeler l'API Wix Stores V1
            wix_url = f"https://www.wixapis.com/stores/v1/products/{data.wix_product_id}/variants"
            
            patch_response = await client.patch(
                wix_url,
                headers={
                    "Authorization": access_token,
                    "Content-Type": "application/json"
                },
                json=payload
            )
            
            # Vérifier la réponse
            if patch_response.status_code not in [200, 204]:
                return {
                    "ok": False,
                    "error": f"Wix API error: {patch_response.status_code}",
                    "detail": patch_response.text[:500]
                }
            
            # Vérifier les SKU après la mise à jour
            verify_response = await client.get(
                wix_url,
                headers={"Authorization": access_token}
            )
            
            if verify_response.status_code == 200:
                verify_data = verify_response.json()
                updated_variants = []
                for v in verify_data.get("variants", []):
                    updated_variants.append({
                        "choices": v.get("choices", {}),
                        "sku": v.get("variant", {}).get("sku", "")
                    })
                
                return {
                    "ok": True,
                    "message": "SKU variants patched successfully with CHOICES format",
                    "patched_count": len(data.variants),
                    "verified_variants": updated_variants
                }
            
            return {
                "ok": True,
                "message": "Patch sent successfully, verification failed",
                "patched_count": len(data.variants)
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error patching Wix variant SKUs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/wix/token/refresh")
async def refresh_wix_token():
    """
    Rafraîchir le token Wix OAuth via l'API Render.
    Utile pour les CRON jobs qui ont besoin d'un token actif.
    """
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{LUXURA_RENDER_API}/wix/token",
                params={"instance_id": "ab8a5a88-69a5-4348-ad2e-06017de46f57"}
            )
            
            if response.status_code != 200:
                return {
                    "ok": False,
                    "error": f"Token refresh failed: {response.status_code}",
                    "detail": response.text[:200]
                }
            
            token_data = response.json()
            
            return {
                "ok": True,
                "message": "Token refreshed successfully",
                "has_access_token": bool(token_data.get("access_token")),
                "expires_in": token_data.get("expires_in")
            }
            
    except Exception as e:
        logger.error(f"Error refreshing Wix token: {e}")
        return {"ok": False, "error": str(e)}

# ==================== WIX INVENTORY SYNC ====================
# NOTE: The real sync is now handled by app/routes/wix.py mounted at /wix/*
# These routes under /api/* are kept for backwards compatibility

@api_router.post("/inventory/sync")
async def sync_inventory_api_alias(
    limit: int = 500, 
    dry_run: bool = False,
):
    """
    Alias pour /wix/sync - redirige vers le vrai endpoint.
    Pour la vraie sync, utilisez POST /wix/sync avec header X-SEO-SECRET
    """
    import httpx
    try:
        seo_secret = os.getenv("SEO_SECRET", "")
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                "http://localhost:8001/wix/sync",
                params={"limit": limit, "dry_run": str(dry_run).lower()},
                headers={"X-SEO-SECRET": seo_secret}
            )
            return response.json()
    except Exception as e:
        logger.error(f"Inventory sync alias error: {e}")
        return {"ok": False, "error": str(e)}

# ==================== FACEBOOK ENDPOINTS ====================
# Ces endpoints utilisent Render comme source de vérité si disponible

class FacebookPostRequest(BaseModel):
    message: str
    link: Optional[str] = None
    image_url: Optional[str] = None
    
class FacebookTokenUpdate(BaseModel):
    token: str

async def get_facebook_token_from_render() -> Optional[str]:
    """Essaie de récupérer le token Facebook depuis Render"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{LUXURA_RENDER_API}/facebook/status")
            if response.status_code == 200:
                data = response.json()
                if data.get("token_valid"):
                    return "RENDER"  # Utiliser Render pour poster
    except:
        pass
    return None

@api_router.post("/facebook/post")
async def post_to_facebook(request: FacebookPostRequest):
    """
    📘 Publier un message sur la page Facebook Luxura.
    
    Essaie d'abord via Render, sinon utilise le token local.
    """
    # Essayer d'abord via Render
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{LUXURA_RENDER_API}/facebook/post",
                json={"message": request.message, "link": request.link, "image_url": request.image_url}
            )
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    return {
                        "success": True,
                        "post_id": result.get("post_id"),
                        "message": "Publication réussie via Render!",
                        "source": "render",
                        "page_url": result.get("page_url")
                    }
    except Exception as e:
        logger.info(f"Render Facebook non disponible, utilisation du token local: {e}")
    
    # Fallback: utiliser le token local
    fb_token = os.getenv("FB_PAGE_ACCESS_TOKEN")
    fb_page_id = os.getenv("FB_PAGE_ID", "1838415193042352")
    
    if not fb_token:
        raise HTTPException(
            status_code=400, 
            detail="FB_PAGE_ACCESS_TOKEN non configuré. Ajoutez les endpoints Facebook sur Render ou configurez le token local."
        )
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            data = {"message": request.message, "access_token": fb_token}
            if request.link:
                data["link"] = request.link
            
            # Si image_url fournie, poster comme photo
            if request.image_url:
                response = await client.post(
                    f"https://graph.facebook.com/v25.0/{fb_page_id}/photos",
                    data={
                        "url": request.image_url,
                        "caption": request.message,
                        "access_token": fb_token
                    }
                )
            else:
                response = await client.post(
                    f"https://graph.facebook.com/v25.0/{fb_page_id}/feed",
                    data=data
                )
            
            result = response.json()
            
            if "error" in result:
                error = result["error"]
                if error.get("code") == 190:  # Token expired
                    raise HTTPException(
                        status_code=401,
                        detail=f"Token Facebook expiré: {error.get('message')}. Mettez à jour le token sur Render."
                    )
                raise HTTPException(status_code=400, detail=f"Erreur Facebook: {error.get('message')}")
            
            return {
                "success": True,
                "post_id": result.get("id"),
                "message": "Publication réussie via token local!",
                "source": "local",
                "page_url": f"https://www.facebook.com/{fb_page_id}"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur publication Facebook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/facebook/update-token")
async def update_facebook_token(request: FacebookTokenUpdate):
    """
    🔑 Mettre à jour le token Facebook Page Access Token (local).
    
    Note: Pour une solution permanente, mettez à jour le token sur Render Dashboard.
    """
    import re
    
    env_path = ROOT_DIR / '.env'
    
    try:
        # Lire le fichier .env
        with open(env_path, 'r') as f:
            content = f.read()
        
        # Mettre à jour ou ajouter le token
        if 'FB_PAGE_ACCESS_TOKEN=' in content:
            content = re.sub(
                r'FB_PAGE_ACCESS_TOKEN=.*',
                f'FB_PAGE_ACCESS_TOKEN={request.token}',
                content
            )
        else:
            content += f'\nFB_PAGE_ACCESS_TOKEN={request.token}\n'
        
        # Sauvegarder
        with open(env_path, 'w') as f:
            f.write(content)
        
        # Mettre à jour la variable d'environnement en mémoire
        os.environ['FB_PAGE_ACCESS_TOKEN'] = request.token
        
        return {
            "success": True,
            "message": "Token Facebook local mis à jour! Pour une solution permanente, mettez aussi à jour sur Render.",
            "token_preview": f"{request.token[:30]}...",
            "tip": "Ajoutez les endpoints Facebook sur luxura-inventory-api pour un contrôle centralisé."
        }
        
    except Exception as e:
        logger.error(f"Erreur mise à jour token Facebook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/facebook/status")
async def get_facebook_status():
    """
    📊 Vérifier le statut de la connexion Facebook (Render + Local).
    """
    fb_token = os.getenv("FB_PAGE_ACCESS_TOKEN")
    fb_page_id = os.getenv("FB_PAGE_ID", "1838415193042352")
    
    status = {
        "local": {
            "configured": bool(fb_token),
            "page_id": fb_page_id,
            "token_preview": f"{fb_token[:30]}..." if fb_token else None,
            "token_valid": False,
            "page_name": None
        },
        "render": {
            "available": False,
            "token_valid": False,
            "page_name": None
        }
    }
    
    # Vérifier Render
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{LUXURA_RENDER_API}/facebook/status")
            if response.status_code == 200:
                render_status = response.json()
                status["render"]["available"] = True
                status["render"]["token_valid"] = render_status.get("token_valid", False)
                status["render"]["page_name"] = render_status.get("page_name")
    except Exception as e:
        status["render"]["error"] = f"Render non disponible: {str(e)[:50]}"
    
    # Vérifier le token local
    if fb_token:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"https://graph.facebook.com/v25.0/{fb_page_id}",
                    params={"access_token": fb_token, "fields": "name,id"}
                )
                result = response.json()
                
                if "error" not in result:
                    status["local"]["token_valid"] = True
                    status["local"]["page_name"] = result.get("name")
                else:
                    status["local"]["error"] = result["error"].get("message")
                    
        except Exception as e:
            status["local"]["error"] = str(e)
    
    # Recommandation
    if status["render"]["available"] and status["render"]["token_valid"]:
        status["recommendation"] = "✅ Utilisez Render (centralisé, 24/7)"
    elif status["local"]["token_valid"]:
        status["recommendation"] = "⚠️ Token local OK, mais ajoutez les endpoints Facebook sur Render pour un contrôle permanent"
    else:
        status["recommendation"] = "❌ Aucun token valide. Configurez sur Render ou localement."
    
    return status

@api_router.post("/facebook/post-blog")
async def post_blog_to_facebook(
    title: str,
    excerpt: str,
    url: str,
    image_url: Optional[str] = None
):
    """
    📰 Publier un article de blog sur Facebook avec formatage automatique.
    """
    # Formater le message
    message = f"📰 NOUVEAU BLOG | {title}\n\n{excerpt[:200]}...\n\n👉 Lire l'article complet:\n{url}\n\n#LuxuraDistribution #ExtensionsCheveux #Quebec #Blog"
    
    # Utiliser l'endpoint principal
    request = FacebookPostRequest(message=message, link=url, image_url=image_url)
    return await post_to_facebook(request)

# ==================== SALON ENDPOINTS ====================

@api_router.get("/salons")
async def get_salons(city: Optional[str] = None):
    """Get all partner salons from Luxura API or local DB"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{LUXURA_API_URL}/salons")
            if response.status_code == 200:
                salons = response.json()
                if city:
                    salons = [s for s in salons if city.lower() in s.get('city', '').lower()]
                return salons
    except Exception as e:
        logger.error(f"Error fetching salons from Luxura API: {e}")
    
    # Fallback to local DB - Supabase
    salons = await db_get_salons(city)
    if not salons:
        return [
            {"id": "salon-1", "name": "Salon Carouso", "address": "123 Rue Principale", "city": "Montréal", "phone": "514-555-0001"},
            {"id": "salon-2", "name": "Salon Élégance", "address": "456 Boulevard Saint-Laurent", "city": "Montréal", "phone": "514-555-0002"},
            {"id": "salon-3", "name": "Coiffure Prestige", "address": "789 Avenue Cartier", "city": "Québec", "phone": "418-555-0003"},
        ]
    return salons

# ==================== HEALTH CHECK & PING ====================

@api_router.get("/ping")
async def ping_services():
    """Ping all external services to wake them up (Render cold start)"""
    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "local_api": "ok",
        "luxura_render_api": "unknown",
        "wix_api": "unknown"
    }
    
    try:
        # Ping Luxura Render API
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(f"{LUXURA_API_URL}/products", params={"limit": 1})
                results["luxura_render_api"] = "ok" if response.status_code == 200 else f"error_{response.status_code}"
            except Exception as e:
                results["luxura_render_api"] = f"error: {str(e)[:50]}"
            
            # Ping Wix API if configured
            if WIX_API_KEY and WIX_SITE_ID:
                try:
                    wix_response = await client.post(
                        f"{WIX_API_BASE}/stores/v1/products/query",
                        headers=get_wix_headers(),
                        json={"query": {"paging": {"limit": 1}}},
                        timeout=15.0
                    )
                    results["wix_api"] = "ok" if wix_response.status_code == 200 else f"error_{wix_response.status_code}"
                except Exception as e:
                    results["wix_api"] = f"error: {str(e)[:50]}"
    except Exception as e:
        results["error"] = str(e)
    
    return results

# ==================== BLOG APPROVAL ENDPOINTS ====================

@api_router.get("/blog/approve/{draft_id}")
async def approve_blog(draft_id: str):
    """
    ✅ Approuve et publie un brouillon de blog sur Wix
    Appelé depuis le lien dans l'email d'approbation
    """
    try:
        logger.info(f"📝 Approbation du brouillon: {draft_id}")
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Publier le brouillon sur Wix
            response = await client.post(
                f"{WIX_API_BASE}/blog/v3/draft-posts/{draft_id}/publish",
                headers=get_wix_headers(),
                json={}
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"✅ Blog publié avec succès: {draft_id}")
                # Retourner une page HTML de confirmation
                return Response(
                    content="""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <title>Blog Approuvé</title>
                        <style>
                            body { font-family: Arial; background: #0c0c0c; color: #fff; 
                                   display: flex; justify-content: center; align-items: center; 
                                   height: 100vh; margin: 0; }
                            .card { background: #1a1a1a; padding: 40px; border-radius: 12px; 
                                    text-align: center; max-width: 400px; }
                            .icon { font-size: 60px; margin-bottom: 20px; }
                            h1 { color: #c9a050; }
                            a { color: #c9a050; }
                        </style>
                    </head>
                    <body>
                        <div class="card">
                            <div class="icon">✅</div>
                            <h1>Blog Publié!</h1>
                            <p>Le brouillon a été approuvé et publié sur votre site Wix.</p>
                            <p><a href="https://www.luxuradistribution.com/blog">Voir le blog</a></p>
                        </div>
                    </body>
                    </html>
                    """,
                    media_type="text/html"
                )
            else:
                logger.error(f"❌ Erreur publication: {response.status_code} - {response.text}")
                raise HTTPException(status_code=response.status_code, detail=f"Erreur Wix: {response.text}")
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur approbation blog: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/blog/reject/{draft_id}")
async def reject_blog(draft_id: str):
    """
    ❌ Rejette et supprime un brouillon de blog sur Wix
    Appelé depuis le lien dans l'email d'approbation
    """
    try:
        logger.info(f"🗑️ Rejet du brouillon: {draft_id}")
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Supprimer le brouillon sur Wix
            response = await client.delete(
                f"{WIX_API_BASE}/blog/v3/draft-posts/{draft_id}",
                headers=get_wix_headers()
            )
            
            if response.status_code in [200, 204]:
                logger.info(f"✅ Brouillon supprimé: {draft_id}")
                return Response(
                    content="""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <title>Brouillon Rejeté</title>
                        <style>
                            body { font-family: Arial; background: #0c0c0c; color: #fff; 
                                   display: flex; justify-content: center; align-items: center; 
                                   height: 100vh; margin: 0; }
                            .card { background: #1a1a1a; padding: 40px; border-radius: 12px; 
                                    text-align: center; max-width: 400px; }
                            .icon { font-size: 60px; margin-bottom: 20px; }
                            h1 { color: #f44; }
                        </style>
                    </head>
                    <body>
                        <div class="card">
                            <div class="icon">🗑️</div>
                            <h1>Brouillon Supprimé</h1>
                            <p>Le brouillon a été rejeté et supprimé.</p>
                        </div>
                    </body>
                    </html>
                    """,
                    media_type="text/html"
                )
            else:
                logger.error(f"❌ Erreur suppression: {response.status_code}")
                raise HTTPException(status_code=response.status_code, detail="Erreur lors de la suppression")
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur rejet blog: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/")
async def root():
    return {"message": "Luxura Distribution API", "status": "running", "inventory_api": LUXURA_API_URL}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy"}

@api_router.get("/health/full")
async def full_health_check():
    """
    Vérification complète de santé de tous les endpoints critiques.
    Retourne un rapport détaillé avec recommandations.
    """
    try:
        from health_monitor import run_health_check, CRITICAL_ENDPOINTS
        
        # Run health check against ourselves (localhost)
        report = await run_health_check("http://localhost:8001")
        return report
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            "status": "error",
            "error": str(e),
            "message": "Could not run full health check"
        }

@api_router.get("/health/endpoints")
async def list_endpoints():
    """Liste tous les endpoints qui DOIVENT exister pour que le système fonctionne"""
    try:
        from health_monitor import CRITICAL_ENDPOINTS
        return {
            "total": len(CRITICAL_ENDPOINTS),
            "endpoints": CRITICAL_ENDPOINTS
        }
    except Exception as e:
        return {"error": str(e)}


# ==================== COLOR ENGINE API ====================

class ColorEngineRequest(BaseModel):
    """Requête pour le Color Engine"""
    gabarit1: str = Field(..., description="Image gabarit 1 en base64")
    gabarit2: Optional[str] = Field(None, description="Image gabarit 2 en base64 (optionnel)")
    reference: str = Field(..., description="Image référence couleur en base64")
    blend: float = Field(0.65, ge=0.3, le=0.9, description="Intensité du mélange")


@api_router.post("/color-engine/process")
async def color_engine_process(request: ColorEngineRequest):
    """
    Endpoint Color Engine V2 - Recolorisation intelligente des extensions.
    
    Envoie les images en base64, reçoit les images recolorisées en base64.
    """
    try:
        logger.info("🎨 Color Engine: Traitement en cours...")
        
        result = await process_color_engine(
            gabarit1_b64=request.gabarit1,
            gabarit2_b64=request.gabarit2,
            reference_b64=request.reference,
            blend=request.blend
        )
        
        logger.info("✅ Color Engine: Traitement terminé")
        return result
        
    except Exception as e:
        logger.error(f"❌ Color Engine erreur: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/color-engine/status")
async def color_engine_status():
    """Vérifie que le Color Engine est disponible"""
    return {
        "status": "ready",
        "version": "2.0",
        "features": [
            "LAB color space recoloring",
            "Improved hair mask (rembg + skin detection)",
            "Ombré preservation",
            "Texture/highlight blending"
        ]
    }


# ==================== COLOR ENGINE - ELITE COLORS LIBRARY ====================

@api_router.get("/color-engine/colors")
async def get_elite_colors():
    """
    Récupère la liste des couleurs Elite pour le Color Engine PRO
    Returns: Liste de couleurs avec code, nom et URL de l'image
    """
    try:
        import json
        
        mapping_path = "/app/backend/luxura_images/color_library/reference/color_mapping.json"
        
        if not os.path.exists(mapping_path):
            return {"colors": [], "message": "Color mapping not found"}
        
        with open(mapping_path, "r") as f:
            colors = json.load(f)
        
        # Construire les URLs pour chaque couleur
        result = []
        for color in colors:
            code = color.get("code", "")
            name = color.get("name", "")
            order = color.get("order", 0)
            filename = color.get("filename", "")
            
            # Vérifier si le fichier existe
            file_path = f"/app/backend/luxura_images/color_library/reference/{filename}"
            
            if os.path.exists(file_path):
                result.append({
                    "code": code,
                    "name": name,
                    "order": order,
                    "image_url": f"/api/color-engine/colors/{code}/image",
                    "filename": filename
                })
        
        # Trier par ordre
        result.sort(key=lambda x: x.get("order", 999))
        
        return {
            "colors": result,
            "total": len(result)
        }
        
    except Exception as e:
        logger.error(f"Error getting elite colors: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/color-engine/colors/{color_code}/image")
async def get_elite_color_image(color_code: str):
    """
    Récupère l'image d'une couleur Elite spécifique
    """
    from fastapi.responses import FileResponse
    import json
    
    try:
        base_path = "/app/backend/luxura_images/color_library/reference"
        
        # Charger le mapping pour trouver le bon fichier
        mapping_path = f"{base_path}/color_mapping.json"
        if os.path.exists(mapping_path):
            with open(mapping_path, "r") as f:
                colors = json.load(f)
            
            # Chercher la couleur par code
            # Le code peut être encodé différemment (/ -> -)
            search_code = color_code.replace('-', '/')
            
            for color in colors:
                if color.get("code") == search_code or color.get("code") == color_code:
                    filename = color.get("filename")
                    if filename:
                        file_path = f"{base_path}/{filename}"
                        if os.path.exists(file_path):
                            return FileResponse(
                                file_path,
                                media_type="image/jpeg",
                                headers={"Cache-Control": "public, max-age=86400"}
                            )
        
        raise HTTPException(status_code=404, detail=f"Color {color_code} not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting color image {color_code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== AUTO COLOR ENGINE (SIMPLIFIÉ) ====================

class GenerateColorRequest(BaseModel):
    """Requête pour la génération Color Engine depuis le frontend"""
    gabarit: Optional[str] = Field(None, description="Image gabarit en base64 (optionnel si on utilise le template)")
    reference: Optional[str] = Field(None, description="Image référence couleur en base64")
    elite_color_code: Optional[str] = Field(None, description="Code couleur Elite (ex: '1A', '6', 'Silver')")
    series: str = Field("genius", description="Série de produit (genius, halo, tape, i-tip)")
    intensity: float = Field(0.75, ge=0.3, le=1.0, description="Intensité du mélange")


@api_router.post("/color-engine/generate")
async def color_engine_generate(request: GenerateColorRequest):
    """
    🎨 COLOR ENGINE GENERATE - Endpoint principal pour le frontend
    
    Recolorise une image de gabarit avec une couleur de référence.
    Peut utiliser soit une image uploadée, soit une couleur Elite par son code.
    
    Args:
        gabarit: Image gabarit en base64 (optionnel - utilise le template par défaut)
        reference: Image référence en base64 (optionnel si elite_color_code est fourni)
        elite_color_code: Code d'une couleur Elite (ex: "1A", "6", "Silver")
        series: Série pour le watermark (genius, halo, tape, i-tip)
        intensity: Intensité de la recolorisation (0.3-1.0)
    
    Returns:
        image: Image résultante en base64 avec watermark
        success: Boolean
    """
    import glob
    from PIL import Image
    import io
    import numpy as np
    
    try:
        logger.info(f"🎨 Color Engine Generate: series={request.series}, intensity={request.intensity}")
        
        # 1. Charger la référence couleur
        reference_image = None
        
        if request.elite_color_code:
            # Charger depuis les couleurs Elite
            base_path = "/app/backend/luxura_images/color_library/reference"
            code = request.elite_color_code
            
            # Chercher le fichier
            patterns = [
                f"{base_path}/{code}_*.jpg",
                f"{base_path}/*_{code}.jpg",
                f"{base_path}/*{code}*.jpg",
            ]
            
            matches = []
            for pattern in patterns:
                matches.extend(glob.glob(pattern))
            
            if matches:
                ref_path = matches[0]
                reference_image = np.array(Image.open(ref_path).convert('RGB'))
                logger.info(f"📷 Loaded Elite color: {code} from {ref_path}")
            else:
                raise HTTPException(status_code=404, detail=f"Elite color '{code}' not found")
                
        elif request.reference:
            # Charger depuis base64
            reference_image = base64_to_image(request.reference.split(',')[-1])
            logger.info("📷 Loaded reference from base64")
        else:
            raise HTTPException(status_code=400, detail="Either 'reference' or 'elite_color_code' is required")
        
        # 2. Charger le gabarit
        if request.gabarit:
            gabarit_image = base64_to_image(request.gabarit.split(',')[-1])
            logger.info("📐 Loaded gabarit from base64")
        else:
            # Utiliser le template par défaut
            template_path = f"/app/backend/templates/gabarit_{request.series}.jpg"
            if not os.path.exists(template_path):
                # Fallback au template genius
                template_path = "/app/backend/templates/gabarit_genius.jpg"
            
            if os.path.exists(template_path):
                gabarit_image = np.array(Image.open(template_path).convert('RGB'))
                logger.info(f"📐 Loaded default template: {template_path}")
            else:
                raise HTTPException(status_code=404, detail="No template available. Please upload a gabarit image.")
        
        # 3. Recoloriser
        from color_engine_api import recolor_with_reference, image_to_base64
        
        result_image, hair_mask = recolor_with_reference(
            gabarit_image, 
            reference_image, 
            blend=request.intensity
        )
        
        # 4. Ajouter le watermark de la série
        result_with_watermark = add_series_watermark(result_image, request.series)
        
        # 5. Sauvegarder l'image générée
        from datetime import datetime
        import uuid
        
        save_dir = "/app/backend/luxura_images/color_engine_generated"
        os.makedirs(save_dir, exist_ok=True)
        
        # Générer un nom de fichier unique
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        color_code = request.elite_color_code or "custom"
        unique_id = str(uuid.uuid4())[:8]
        filename = f"{request.series}_{color_code}_{timestamp}_{unique_id}.png"
        filepath = os.path.join(save_dir, filename)
        
        # Sauvegarder l'image
        pil_result = Image.fromarray(result_with_watermark)
        pil_result.save(filepath, "PNG", quality=95)
        logger.info(f"💾 Image saved: {filename}")
        
        # 6. Convertir en base64
        result_b64 = image_to_base64(result_with_watermark)
        
        logger.info("✅ Color Engine Generate: Success")
        
        return {
            "success": True,
            "image": f"data:image/png;base64,{result_b64}",
            "series": request.series,
            "intensity": request.intensity,
            "elite_color": request.elite_color_code,
            "saved_filename": filename,
            "download_url": f"/api/color-engine/generated/{filename}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Color Engine Generate error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/color-engine/generated")
async def list_generated_images():
    """
    Liste toutes les images générées par le Color Engine
    """
    import glob
    from datetime import datetime
    
    save_dir = "/app/backend/luxura_images/color_engine_generated"
    
    if not os.path.exists(save_dir):
        return {"images": [], "total": 0}
    
    files = glob.glob(f"{save_dir}/*.png")
    
    images = []
    for filepath in files:
        filename = os.path.basename(filepath)
        # Parse filename: series_colorcode_timestamp_uuid.png
        parts = filename.replace('.png', '').split('_')
        
        stat = os.stat(filepath)
        file_size = stat.st_size
        created_at = datetime.fromtimestamp(stat.st_mtime).isoformat()
        
        images.append({
            "filename": filename,
            "series": parts[0] if len(parts) > 0 else "unknown",
            "color_code": parts[1] if len(parts) > 1 else "unknown",
            "created_at": created_at,
            "size_bytes": file_size,
            "size_kb": round(file_size / 1024, 1),
            "download_url": f"/api/color-engine/generated/{filename}",
            "preview_url": f"/api/color-engine/generated/{filename}?preview=true"
        })
    
    # Trier par date de création (plus récent en premier)
    images.sort(key=lambda x: x['created_at'], reverse=True)
    
    return {
        "images": images,
        "total": len(images)
    }


@api_router.get("/color-engine/generated/{filename}")
async def download_generated_image(filename: str, preview: bool = False):
    """
    Télécharge ou prévisualise une image générée
    """
    from fastapi.responses import FileResponse
    
    save_dir = "/app/backend/luxura_images/color_engine_generated"
    filepath = os.path.join(save_dir, filename)
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Sécurité: vérifier que le fichier est bien dans le dossier autorisé
    if not os.path.abspath(filepath).startswith(os.path.abspath(save_dir)):
        raise HTTPException(status_code=403, detail="Access denied")
    
    return FileResponse(
        filepath,
        media_type="image/png",
        filename=filename if not preview else None,
        headers={
            "Cache-Control": "public, max-age=3600",
            "Content-Disposition": "inline" if preview else f"attachment; filename={filename}"
        }
    )


@api_router.delete("/color-engine/generated/{filename}")
async def delete_generated_image(filename: str):
    """
    Supprime une image générée
    """
    save_dir = "/app/backend/luxura_images/color_engine_generated"
    filepath = os.path.join(save_dir, filename)
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Sécurité
    if not os.path.abspath(filepath).startswith(os.path.abspath(save_dir)):
        raise HTTPException(status_code=403, detail="Access denied")
    
    os.remove(filepath)
    logger.info(f"🗑️ Deleted generated image: {filename}")
    
    return {"success": True, "message": f"Image {filename} deleted"}




def add_series_watermark(image, series: str):
    """Ajoute le watermark Luxura + série sur l'image."""
    from PIL import Image, ImageDraw, ImageFont
    import numpy as np
    
    pil_image = Image.fromarray(image)
    draw = ImageDraw.Draw(pil_image)
    
    # Couleurs par série
    series_colors = {
        "genius": "#9333ea",  # Purple
        "halo": "#3b82f6",    # Blue
        "tape": "#22c55e",    # Green
        "i-tip": "#f59e0b",   # Orange
    }
    
    series_names = {
        "genius": "Série Vivian",
        "halo": "Série Everly", 
        "tape": "Série Aurora",
        "i-tip": "Série Eleanor",
    }
    
    # Position du watermark (coin inférieur droit)
    width, height = pil_image.size
    
    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
    except:
        font_large = ImageFont.load_default()
        font_small = font_large
    
    # Textes
    luxura_text = "LUXURA"
    series_text = series_names.get(series, "Extensions")
    
    # Dessiner le fond semi-transparent
    box_width = 150
    box_height = 50
    box_x = width - box_width - 10
    box_y = height - box_height - 10
    
    # Rectangle semi-transparent
    overlay = Image.new('RGBA', pil_image.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.rectangle(
        [(box_x - 5, box_y - 5), (box_x + box_width + 5, box_y + box_height + 5)],
        fill=(0, 0, 0, 150)
    )
    
    pil_image = pil_image.convert('RGBA')
    pil_image = Image.alpha_composite(pil_image, overlay)
    draw = ImageDraw.Draw(pil_image)
    
    # Texte LUXURA en doré
    draw.text((box_x + 10, box_y + 5), luxura_text, fill="#c9a050", font=font_large)
    
    # Texte série
    series_color = series_colors.get(series, "#ffffff")
    draw.text((box_x + 10, box_y + 30), series_text, fill=series_color, font=font_small)
    
    return np.array(pil_image.convert('RGB'))


class AutoColorRequest(BaseModel):
    """Requête simplifiée - juste la référence couleur"""
    reference: str = Field(..., description="Image référence couleur en base64")
    blend: float = Field(0.65, ge=0.3, le=0.9, description="Intensité du mélange")


@api_router.post("/color-engine/auto")
async def color_engine_auto(request: AutoColorRequest):
    """
    🎨 AUTO COLOR ENGINE - Upload simplifié
    
    Envoie SEULEMENT l'image de référence (couleur), 
    reçois l'image du gabarit Genius recolorisée avec watermark.
    
    Le gabarit est conservé côté serveur.
    """
    try:
        logger.info("🎨 Auto Color Engine: Traitement...")
        
        result = await auto_recolor(
            reference_b64=request.reference,
            blend=request.blend
        )
        
        logger.info("✅ Auto Color Engine: Terminé")
        return result
        
    except Exception as e:
        logger.error(f"❌ Auto Color Engine erreur: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/color-engine/auto-url")
async def color_engine_auto_url(image_url: str, blend: float = 0.65):
    """
    🎨 AUTO COLOR ENGINE par URL
    
    Envoie l'URL de l'image référence, reçois l'image recolorisée.
    """
    try:
        import httpx
        import base64
        
        logger.info(f"🎨 Auto Color Engine URL: {image_url[:50]}...")
        
        # Télécharger l'image
        async with httpx.AsyncClient() as client:
            response = await client.get(image_url)
            if response.status_code != 200:
                raise HTTPException(status_code=400, detail="Impossible de télécharger l'image")
            
            reference_b64 = base64.b64encode(response.content).decode('utf-8')
        
        result = await auto_recolor(
            reference_b64=reference_b64,
            blend=blend
        )
        
        logger.info("✅ Auto Color Engine URL: Terminé")
        return result
        
    except Exception as e:
        logger.error(f"❌ Auto Color Engine URL erreur: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== SEO IMAGE OPTIMIZER ====================

# Import SEO module - functions use dynamic imports to get latest changes
import seo_image_optimizer as seo_module

class SEOGenerateRequest(BaseModel):
    product_type: str  # genius, tape, halo, i-tip, ponytail, clip-in
    color_code: str    # 1, 6, 60a, hps, etc.
    length: Optional[str] = None  # 16, 18, 20, 22, 24
    geo_variation: int = 0  # Rotation des régions (0-12)

class SEOBatchRequest(BaseModel):
    dry_run: bool = True  # Si False, applique les changements sur Wix

@api_router.post("/seo/image/generate")
async def generate_image_seo(request: SEOGenerateRequest):
    """
    🔍 Génère toutes les données SEO pour un produit.
    
    Retourne: filename, alt_text, meta_description, title_tag, keywords, geo_region
    
    Exemple:
    - product_type: "genius"
    - color_code: "60a"
    - length: "20"
    - geo_variation: 0 (Québec), 1 (Beauce), 2 (Lévis), etc.
    """
    seo_data = seo_module.generate_product_seo_data(
        product_type=request.product_type,
        color_code=request.color_code,
        length=request.length,
        variation_index=request.geo_variation
    )
    
    return {
        "success": True,
        "seo_data": seo_data,
        "available_regions": seo_module.GEO_KEYWORDS,
        "tip": "Utilise geo_variation pour alterner les régions (0=Québec, 1=Beauce, 2=Lévis...)"
    }

@api_router.get("/seo/image/preview")
async def preview_seo_variations(
    product_type: str = "genius",
    color_code: str = "60a",
    length: str = "20"
):
    """
    👀 Prévisualise les variations SEO pour toutes les régions.
    
    Utile pour voir comment les noms de fichiers et alt texts varient.
    """
    variations = []
    
    for i, geo in enumerate(seo_module.GEO_KEYWORDS):
        seo_data = seo_module.generate_product_seo_data(
            product_type=product_type,
            color_code=color_code,
            length=length,
            variation_index=i
        )
        variations.append({
            "geo_index": i,
            "region": geo,
            "filename": seo_data["filename"],
            "alt_text": seo_data["alt_text"],
            "title_tag": seo_data["title_tag"]
        })
    
    return {
        "product": f"{product_type.upper()} #{color_code}",
        "variations": variations,
        "total_variations": len(variations)
    }

@api_router.post("/seo/catalog/batch-update")
async def batch_update_seo(request: SEOBatchRequest):
    """
    🔄 Met à jour le SEO de tout le catalogue Wix.
    
    ⚠️ ATTENTION: Si dry_run=False, les changements sont appliqués sur Wix!
    
    - dry_run=True: Prévisualise les changements sans les appliquer
    - dry_run=False: Applique les changements sur tous les produits
    """
    if not WIX_API_KEY:
        raise HTTPException(
            status_code=400, 
            detail="WIX_API_KEY non configurée. Impossible de mettre à jour le catalogue."
        )
    
    report = await seo_module.batch_update_catalog_seo(dry_run=request.dry_run)
    
    return {
        "success": True,
        "dry_run": report["dry_run"],
        "total_products": report["total_products"],
        "updated": report["updated"],
        "skipped": report["skipped"],
        "errors": report["errors"],
        "sample_changes": report["changes"][:5] if report["changes"] else [],
        "warning": "Pour appliquer les changements, envoyez dry_run=false" if report["dry_run"] else "Changements appliqués sur Wix!"
    }

@api_router.get("/seo/config")
async def get_seo_config():
    """
    📋 Retourne la configuration SEO disponible.
    
    - Régions géographiques ciblées
    - Types de produits avec mots-clés
    - Codes couleur avec noms SEO
    """
    return {
        "geo_keywords": seo_module.GEO_KEYWORDS,
        "product_types": {
            k: {
                "name": v["name"],
                "keywords": v["keywords"][:3],
                "benefits": v["benefits"][:2]
            } for k, v in seo_module.PRODUCT_TYPES_SEO.items()
        },
        "color_codes": {
            k: {
                "name": v["name"],
                "keywords": v["keywords"][:2]
            } for k, v in list(seo_module.COLOR_SEO_MAP.items())[:15]  # Top 15 couleurs
        },
        "naming_format": "luxura-{rallonge|extension}-{type}-{couleur}-{région}-{longueur}po.jpg",
        "example": seo_module.generate_product_seo_data("genius", "60a", "20", 0)
    }

@api_router.get("/seo/filename-generator")
async def generate_seo_filenames_bulk(
    product_type: str = "genius",
    color_codes: str = "1,2,3,6,60a,hps"
):
    """
    📁 Génère des noms de fichiers SEO pour plusieurs couleurs et régions.
    
    Parfait pour renommer un lot d'images avant upload sur Wix.
    
    Args:
        product_type: Type de produit (genius, tape, halo, etc.)
        color_codes: Liste de codes couleur séparés par virgules
    """
    # Config SEO inline pour éviter les problèmes de cache
    GEO_REGIONS = ["Québec", "Beauce", "Lévis", "Chaudière-Appalaches", "Rive-Sud", "St-Georges"]
    
    COLOR_NAMES = {
        "1": "Noir Foncé", "1b": "Noir Naturel", "2": "Brun Foncé", "3": "Châtain Moyen",
        "6": "Châtain Clair", "6/24": "Balayage Caramel", "18/22": "Blond Cendré",
        "60a": "Blond Platine", "613/18a": "Blond Glacé", "hps": "Blond Cendré Foncé",
        "pha": "Blond Perle", "cb": "Ombré Miel", "db": "Brun Nuit", "dc": "Chocolat Profond",
        "cacao": "Cacao", "cinnamon": "Cannelle"
    }
    
    TYPE_NAMES = {
        "genius": "Genius Trame Invisible", "tape": "Bande Adhésive", "halo": "Halo",
        "i-tip": "I-Tip Kératine", "ponytail": "Queue de Cheval", "clip-in": "Extensions à Clips"
    }
    
    def normalize_text(text: str) -> str:
        """Normalise les caractères spéciaux pour les URLs"""
        text = text.lower()
        replacements = {"é": "e", "è": "e", "ê": "e", "â": "a", "à": "a", "î": "i", "ï": "i", 
                       "ô": "o", "û": "u", "ù": "u", "ç": "c", "'": "", " ": "-"}
        for old, new in replacements.items():
            text = text.replace(old, new)
        return re.sub(r'-+', '-', text).strip('-')
    
    def gen_filename(ptype: str, color: str, geo_idx: int) -> str:
        word = "rallonge" if geo_idx % 2 == 0 else "extension"
        color_name = normalize_text(COLOR_NAMES.get(color, color))
        region = normalize_text(GEO_REGIONS[geo_idx % len(GEO_REGIONS)])
        return f"luxura-{word}-{ptype}-{color_name}-{region}-20po.jpg"
    
    def gen_alt(ptype: str, color: str, geo_idx: int) -> str:
        word = "Rallonge" if geo_idx % 2 == 0 else "Extension"
        type_name = TYPE_NAMES.get(ptype, ptype.title())
        color_name = COLOR_NAMES.get(color, color)
        region = GEO_REGIONS[geo_idx % len(GEO_REGIONS)]
        return f"{word} {type_name} {color_name} 20 pouces - Luxura Distribution {region}"
    
    codes = [c.strip() for c in color_codes.split(",")]
    filenames = []
    
    for code in codes:
        for geo_idx in range(min(3, len(GEO_REGIONS))):
            filenames.append({
                "color_code": code,
                "color_name": COLOR_NAMES.get(code, code),
                "region": GEO_REGIONS[geo_idx],
                "filename": gen_filename(product_type, code, geo_idx),
                "alt_text": gen_alt(product_type, code, geo_idx)
            })
    
    return {
        "product_type": product_type,
        "generated_filenames": filenames,
        "total": len(filenames),
        "available_regions": GEO_REGIONS,
        "tip": "Télécharge les images et renomme-les avec ces noms avant upload sur Wix"
    }


# Include backlinks routes FIRST (priority over legacy routes in api_router)
try:
    from backlinks.backlink_routes import router as backlinks_router
    app.include_router(backlinks_router)
    logger.info("✅ Routes backlinks V2 chargées (priorité)")
except ImportError as e:
    logger.warning(f"⚠️ Routes backlinks non disponibles: {e}")

# Marketing Automation Routes
try:
    from routes.marketing.campaigns import router as marketing_router
    from routes.marketing.templates import router as templates_router
    app.include_router(marketing_router, prefix="/api")
    app.include_router(templates_router, prefix="/api")
    logger.info("✅ Routes Marketing Automation chargées")
    logger.info("✅ Routes Templates Marketing chargées")
except ImportError as e:
    logger.warning(f"⚠️ Routes marketing non disponibles: {e}")

# Include the main router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Note: La fonction shutdown_db_client a été supprimée car MongoDB n'est plus utilisé.
# Supabase/PostgreSQL utilise une pool de connexions SQLAlchemy gérée automatiquement.

# ==================== WIX ROUTES (from app/routes/wix.py - April 9th version) ====================
# Mount the real wix router from app/routes/wix.py instead of our fallback
try:
    from app.routes.wix import router as wix_router
    app.include_router(wix_router)
    logger.info("✅ Mounted app/routes/wix.py router (real sync implementation)")
except Exception as e:
    logger.warning(f"⚠️ Could not mount wix router: {e}")
    # Fallback routes if the real router fails to load
    @app.post("/wix/sync")
    async def wix_sync_fallback(limit: int = 500, dry_run: bool = False):
        return {"ok": False, "error": f"Wix router not available: {e}"}

# ==================== WIX TOKEN ROUTES (compatibilité avec anciennes versions) ====================

@app.post("/wix/token")
async def wix_token_endpoint(instance_id: str = None):
    """
    Endpoint pour obtenir/rafraîchir le token Wix OAuth.
    Utilisé par le système de sync Wix.
    """
    try:
        from wix_cron_service import refresh_wix_token, token_cache
        
        # Essayer de récupérer le token du cache
        token = token_cache.get_token()
        
        if token:
            return {
                "ok": True,
                "access_token": token,
                "source": "cache"
            }
        
        # Sinon, rafraîchir
        result = await refresh_wix_token()
        
        if result.get("ok"):
            token = token_cache.get_token()
            return {
                "ok": True,
                "access_token": token,
                "source": "refreshed",
                "expires_in": result.get("expires_in")
            }
        else:
            return {"ok": False, "error": result.get("error")}
            
    except ImportError:
        # Si wix_cron_service n'est pas disponible, retourner une erreur plus claire
        return {
            "ok": False,
            "error": "Wix OAuth service not configured. Need WIX_CLIENT_ID and WIX_CLIENT_SECRET."
        }
    except Exception as e:
        logger.error(f"Wix token error: {e}")
        return {"ok": False, "error": str(e)}

@app.get("/wix/token")
async def wix_token_get(instance_id: str = None):
    """Alias GET pour le token Wix"""
    return await wix_token_endpoint(instance_id)

@app.get("/wix/cron/status")
async def wix_cron_status():
    """Vérifier l'état du token Wix en cache"""
    try:
        from wix_cron_service import token_cache
        return {
            "ok": True,
            "cache": token_cache.get_status()
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.get("/wix/cron/refresh-token")
async def wix_cron_refresh():
    """Endpoint pour le CRON de rafraîchissement du token"""
    try:
        from wix_cron_service import refresh_wix_token
        result = await refresh_wix_token()
        return result
    except Exception as e:
        return {"ok": False, "error": str(e)}

# ==================== WIX SYNC ROUTES (FALLBACK) ====================
# Routes pour le cron job - utilisent notre implémentation sync_wix_inventory

@app.post("/wix/sync")
async def wix_sync_endpoint(
    limit: int = 500, 
    dry_run: bool = False,
    background_tasks: BackgroundTasks = None
):
    """
    Endpoint principal pour synchroniser l'inventaire Wix → Supabase.
    Utilisé par le cron job luxura-inventory-sync-cron.
    """
    return await sync_wix_inventory(limit=limit, dry_run=dry_run, background_tasks=background_tasks)

@app.post("/inventory/sync")
async def inventory_sync_endpoint(
    limit: int = 500, 
    dry_run: bool = False,
    background_tasks: BackgroundTasks = None
):
    """
    Alias pour /wix/sync - compatibilité avec anciennes versions.
    """
    return await sync_wix_inventory(limit=limit, dry_run=dry_run, background_tasks=background_tasks)

@app.get("/wix/sync/last")
async def wix_sync_last():
    """Retourne le statut de la dernière sync (stub pour compatibilité)"""
    return {"ok": True, "exists": False, "message": "Sync history not implemented in this version"}
