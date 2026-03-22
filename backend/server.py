from fastapi import FastAPI, APIRouter, HTTPException, Response, Request, Depends, BackgroundTasks
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
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

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection for local data (auth, cart, etc.)
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Luxura Inventory API (Render)
LUXURA_API_URL = "https://luxura-inventory-api.onrender.com"

# Wix API Configuration
WIX_API_KEY = os.getenv("WIX_API_KEY", "")
WIX_SITE_ID = os.getenv("WIX_SITE_ID", "")
WIX_API_BASE = "https://www.wixapis.com"
WIX_INSTANCE_ID = os.getenv("WIX_INSTANCE_ID", "")

# Luxura API - pour utiliser l'OAuth existant
LUXURA_RENDER_API = "https://luxura-inventory-api.onrender.com"

# Create the main app
app = FastAPI()

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

# ALLOWED CATEGORIES - Only these 5 categories are sold by Luxura
ALLOWED_CATEGORIES = {'genius', 'tape', 'i-tip', 'halo', 'essentiels'}

# EXCLUDED PRODUCTS - Products to skip (Clips, Ponytails, etc.)
EXCLUDED_KEYWORDS = ['clips', 'ponytail', 'queue de cheval', 'test']

def detect_category_from_handle(handle: str, name: str) -> str:
    """Detect product category from Wix handle - more accurate than name-based detection
    Returns None for products that should be excluded (Clips, Ponytails, etc.)
    """
    if not handle:
        handle = ""
    handle_lower = handle.lower()
    name_lower = name.lower()
    
    # EXCLUDE: Clips, Ponytails, and other non-sold products
    for excluded in EXCLUDED_KEYWORDS:
        if excluded in handle_lower or excluded in name_lower:
            return None  # Will be filtered out
    
    # Priority 1: Check handle (most reliable - matches Wix URLs)
    if 'genius' in handle_lower or 'vivian' in handle_lower or 'trame-invisible' in handle_lower:
        return 'genius'
    elif 'halo' in handle_lower or ('everly' in handle_lower and 'clips' not in handle_lower):
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
    
    # Priority 3: Fallback to name-based detection
    if 'genius' in name_lower or 'trame invisible' in name_lower or 'vivian' in name_lower:
        return 'genius'
    elif 'halo' in name_lower and 'clips' not in name_lower:
        return 'halo'
    elif 'bande' in name_lower or 'adhésive' in name_lower or 'aurora' in name_lower:
        return 'tape'
    elif 'i-tip' in name_lower or 'itip' in name_lower:
        return 'i-tip'
    
    # Default to essentiels for accessories, but may be filtered if not matching
    return 'essentiels'

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

# Wix product images mapping - scraped from luxuradistribution.com categories
# Format: handle -> image_url (400x400 optimized)
WIX_PRODUCT_IMAGES = {
    # GENIUS
    "genius-trame-invisible-série-vivian-noir-foncé-1": "https://static.wixstatic.com/media/f1b961_0765bab9e407403289c86e98fcb27476~mv2.png",
    "genius-trame-invisible-série-vivian-dark-chocolate-dc": "https://static.wixstatic.com/media/f1b961_58c11630ff1349728c47e56190218422~mv2.png",
    "genius-ssd-trame-invisible-série-vivian-brun-cacao": "https://static.wixstatic.com/media/f1b961_11271a5d5d91485883888a201592829c~mv2.jpg",
    "genius-trame-invisible-série-vivian-brun-2": "https://static.wixstatic.com/media/f1b961_2596437db6134f7bbdc1c5b2d72907fd~mv2.jpg",
    "genius-trame-invisible-série-vivian-brun-moyen-3": "https://static.wixstatic.com/media/f1b961_47ff485b2f674fdc9245cc856004cd46~mv2.png",
    "genius-série-vivian-brun-lumineux-blond-foncé-6": "https://static.wixstatic.com/media/f1b961_5769d9b826004a6f91eb9112dc140cfb~mv2.png",
    "genius-trame-invisible-série-vivian-foochow": "https://static.wixstatic.com/media/f1b961_28d930f0f9924b229beb3be484bc1fbd~mv2.jpg",
    "genius-trame-invisible-série-vivian-blond-platine-60a": "https://static.wixstatic.com/media/f1b961_c3168b50e6d9464db8365cdef0b16557~mv2.png",
    "genius-trame-invisible-série-vivian-balayage-blond-beige-18-22": "https://static.wixstatic.com/media/f1b961_b7d3eb648bf443cb8d30e3e23fa62ad8~mv2.png",
    "genius-trame-invisible-série-vivian-balayage-blond-foncé-6-24": "https://static.wixstatic.com/media/f1b961_387bbe6d47cd4217a7b0157f398d9a63~mv2.png",
    "genius-série-vivian-balayage-blond-cendré-613-18a": "https://static.wixstatic.com/media/f1b961_c15e5a01c6024a1699cb92a2be325f8f~mv2.png",
    "genius-trame-invisible-série-vivian-5atp18b62": "https://static.wixstatic.com/media/f1b961_0e7cf48e1d59418bbf1b562c21494176~mv2.jpg",
    "genius-trame-invisible-série-vivian-chengtu": "https://static.wixstatic.com/media/f1b961_e440aecc44e44c69b0d56dad273a95e9~mv2.jpg",
    "genius-série-vivian-ombré-blond-miel-cb": "https://static.wixstatic.com/media/f1b961_5e027a0d94d749e99ad76830129b42da~mv2.png",
    "genius-nouvelle-trame-invisible-série-vivian-cannelle-cinnamon": "https://static.wixstatic.com/media/f1b961_23960136c3df4e84852f5dde15475d17~mv2.jpg",
    "genius-trame-invisible-série-vivian-t14-p14-24": "https://static.wixstatic.com/media/f1b961_9c2192c6fa5f4458913d46ea8a8f9dae~mv2.jpg",
    "genius-trame-invisible-série-vivian-blanc-polar-ivory": "https://static.wixstatic.com/media/f1b961_2dbcedc5036044b69e1ba01c58cc93d4~mv2.jpg",
    "genius-trame-invisible-série-vivian-perfect-highlift-ash-pha": "https://static.wixstatic.com/media/f1b961_54514ba920d34aed9aa1f10c62f1759a~mv2.jpg",
    "genius-sdd-série-vivian-ombré-2btp18-1006": "https://static.wixstatic.com/media/f1b961_75316de55cf441ecb82211cbc8d91010~mv2.jpg",
    "genius-ssd-série-vivian-ombré-blond-cendré-5at60": "https://static.wixstatic.com/media/f1b961_9f8115b4f7614340b0dc9aeba39bd699~mv2.jpg",
    "genius-ombré-blond-moka-6-6t24": "https://static.wixstatic.com/media/f1b961_276e2a0ba6ab4e92a0da09977692256e~mv2.png",
    # HALO
    "halo-série-everly-noir-foncé-1": "https://static.wixstatic.com/media/f1b961_7c4c9a8b07484a5eb66b12e9b9322b4a~mv2.jpg",
    "halo-série-everly-noir-doux-brun-foncé-1b": "https://static.wixstatic.com/media/f1b961_42148bb43bbe484f9ca8f1127a4d30e4~mv2.png",
    "halo-série-everly-brun-moyen-3": "https://static.wixstatic.com/media/f1b961_d1bb2905a7b748f5ac4676d5c96bae2a~mv2.png",
    "halo-série-everly-brun-lumineux-blond-foncé-6": "https://static.wixstatic.com/media/f1b961_5b61b7d6874a47abb7997a78d99c7125~mv2.png",
    "halo-série-everly-blond-platine-60a": "https://static.wixstatic.com/media/f1b961_1e9953c3551440479117fa2954918173~mv2.png",
    "halo-série-everly-balayage-blond-foncé-6-24": "https://static.wixstatic.com/media/f1b961_7858886b3ecb41e5bdf5be80b2aa4359~mv2.png",
    "halo-série-everly-balayage-blond-cendré-613-18a": "https://static.wixstatic.com/media/f1b961_2fba27c18fe14584a828cfa9880a3146~mv2.png",
    "halo-série-everly-balayage-blond-beige-18-22": "https://static.wixstatic.com/media/f1b961_ed52f5195856485796099c2a1823a0fd~mv2.png",
    "halo-série-everly-ombré-blond-miel-cb": "https://static.wixstatic.com/media/f1b961_7ba6134ca87e4423817e9b0fa07754c1~mv2.png",
    "halo-série-everly-ombré-brun-nuit-db": "https://static.wixstatic.com/media/f1b961_601ee2f6e66b48d6b09e471501537fc9~mv2.png",
    "halo-série-everly-ombré-blond-moka-6-6t24": "https://static.wixstatic.com/media/f1b961_276e2a0ba6ab4e92a0da09977692256e~mv2.png",
    "halo-série-everly-ombré-brun-cacao-3-3t24": "https://static.wixstatic.com/media/f1b961_bc6218e7631045ff801eeb0195b3b8c9~mv2.png",
    "halo-série-everly-ombré-blond-cendré-hps": "https://static.wixstatic.com/media/f1b961_13645139441a4ad0bdae63bca7d65c37~mv2.png",
    # CLIPS (Halo category)
    "clips-série-everly-noir-foncé-1": "https://static.wixstatic.com/media/f1b961_7c4c9a8b07484a5eb66b12e9b9322b4a~mv2.jpg",
    "clips-série-everly-noir-doux-brun-foncé-1b": "https://static.wixstatic.com/media/f1b961_42148bb43bbe484f9ca8f1127a4d30e4~mv2.png",
    "clips-série-everly-noir-doux-brun-foncé-3": "https://static.wixstatic.com/media/f1b961_d1bb2905a7b748f5ac4676d5c96bae2a~mv2.png",
    "clips-série-everly-brun-lunimeux-blond-foncé-6": "https://static.wixstatic.com/media/f1b961_5b61b7d6874a47abb7997a78d99c7125~mv2.png",
    "clips-série-everly-blond-platine-60a": "https://static.wixstatic.com/media/f1b961_1e9953c3551440479117fa2954918173~mv2.png",
    "clips-série-everly-18-22": "https://static.wixstatic.com/media/f1b961_ed52f5195856485796099c2a1823a0fd~mv2.png",
    "clips-série-everly-balaya-blond-beige-613-18a": "https://static.wixstatic.com/media/f1b961_2fba27c18fe14584a828cfa9880a3146~mv2.png",
    "clips-série-everly-ombré-blond-cendré-hps": "https://static.wixstatic.com/media/f1b961_13645139441a4ad0bdae63bca7d65c37~mv2.png",
    # TAPE / BANDE ADHESIVE
    "bande-invisible-série-aurora-ice-white-icw": "https://static.wixstatic.com/media/f1b961_9b2d02f5f8fe47369534f67678bbc79d~mv2.jpg",
    "bande-adhésive-série-aurora-dark-chocolate-dc": "https://static.wixstatic.com/media/f1b961_fa7cd15003c94b16a263bd39d22dc48c~mv2.jpg",
    "bande-adhésive-série-aurora-noir-foncé-1-jet-black": "https://static.wixstatic.com/media/f1b961_8bed6fa0069a41c3971d7dcb51ab1cec~mv2.png",
    "bande-adhésive-série-aurora-brun-foncé-noir-doux-1b": "https://static.wixstatic.com/media/f1b961_088e24bf74854319bab62d49634b608a~mv2.png",
    "bande-adhésive-série-aurora-brun-lumineux-blond-foncé-6": "https://static.wixstatic.com/media/f1b961_5d6668fdf8114e3d99f528fe612222f0~mv2.png",
    "bande-adhésive-série-aurora-brun-moyen-3": "https://static.wixstatic.com/media/f1b961_a0bb462af6f44e25aa751ea359024bba~mv2.png",
    "bande-adhésive-série-aurora-blond-platine-60a": "https://static.wixstatic.com/media/f1b961_e75015e3740242dab6c3567bf8445811~mv2.png",
    "bande-adhésive-série-aurora-blond-pha": "https://static.wixstatic.com/media/f1b961_54514ba920d34aed9aa1f10c62f1759a~mv2.jpg",
    "bande-adhésive-série-aurora-ombré-blond-miel-cb": "https://static.wixstatic.com/media/f1b961_5e027a0d94d749e99ad76830129b42da~mv2.png",
    "bande-adhésive-série-aurora-ombré-blond-cendré-hps": "https://static.wixstatic.com/media/f1b961_13645139441a4ad0bdae63bca7d65c37~mv2.png",
    "bande-adhésive-série-aurora-balayage-blond-foncé-6-24": "https://static.wixstatic.com/media/f1b961_387bbe6d47cd4217a7b0157f398d9a63~mv2.png",
    "bande-adhésive-tenue-ultra": "https://static.wixstatic.com/media/de6cdb_5ba6af2b449d44039ce9c23d3517953b~mv2.jpg",
    "pince-d-application-bande-adhésive": "https://static.wixstatic.com/media/de6cdb_5ba6af2b449d44039ce9c23d3517953b~mv2.jpg",
    # PONYTAILS
    "ponytail-queue-de-cheval-série-everly-noir-foncé-1": "https://static.wixstatic.com/media/f1b961_7c4c9a8b07484a5eb66b12e9b9322b4a~mv2.jpg",
    "ponytail-queue-de-cheval-série-everly-ombré-brun-miel-du": "https://static.wixstatic.com/media/f1b961_7ba6134ca87e4423817e9b0fa07754c1~mv2.png",
    # ESSENTIALS
    "anneau-de-couleur-haut-de-gamme": "https://static.wixstatic.com/media/de6cdb_5ba6af2b449d44039ce9c23d3517953b~mv2.jpg",
    "ensemble-installation": "https://static.wixstatic.com/media/de6cdb_5ba6af2b449d44039ce9c23d3517953b~mv2.jpg",
    "fer-à-friser-rotatif": "https://static.wixstatic.com/media/de6cdb_5ba6af2b449d44039ce9c23d3517953b~mv2.jpg",
    "brosse-volumisante-et-séchante": "https://static.wixstatic.com/media/de6cdb_5ba6af2b449d44039ce9c23d3517953b~mv2.jpg",
}

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

def get_product_image(handle: str, category: str) -> str:
    """Get product image from Wix mapping or category fallback"""
    if handle:
        # Direct match
        if handle in WIX_PRODUCT_IMAGES:
            return format_wix_image_url(WIX_PRODUCT_IMAGES[handle])
        
        # Try partial match for similar products
        handle_lower = handle.lower()
        for key, url in WIX_PRODUCT_IMAGES.items():
            # Match base product type (e.g., genius-série-vivian matches genius-trame-invisible-série-vivian)
            key_parts = key.split('-')
            handle_parts = handle_lower.split('-')
            
            # Check if main identifiers match (product type + color code)
            if len(key_parts) >= 3 and len(handle_parts) >= 3:
                # Match product type (genius, halo, clips, etc.)
                if key_parts[0] == handle_parts[0]:
                    # Try to match color code at the end
                    if key_parts[-1] == handle_parts[-1] or key_parts[-2:] == handle_parts[-2:]:
                        return format_wix_image_url(url)
    
    # Category-specific default images (real product photos from Wix)
    category_images = {
        "genius": "https://static.wixstatic.com/media/f1b961_0765bab9e407403289c86e98fcb27476~mv2.png",
        "halo": "https://static.wixstatic.com/media/f1b961_42148bb43bbe484f9ca8f1127a4d30e4~mv2.png",
        "tape": "https://static.wixstatic.com/media/f1b961_8bed6fa0069a41c3971d7dcb51ab1cec~mv2.png",
        "i-tip": "https://static.wixstatic.com/media/f1b961_0d440382da1f450da579fd73c14daf88~mv2.png",
        "essentiels": "https://static.wixstatic.com/media/de6cdb_5ba6af2b449d44039ce9c23d3517953b~mv2.jpg"
    }
    return format_wix_image_url(category_images.get(category, category_images["genius"]))

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
    
    session_doc = await db.user_sessions.find_one(
        {"session_token": session_token},
        {"_id": 0}
    )
    
    if not session_doc:
        return None
    
    expires_at = session_doc["expires_at"]
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        return None
    
    user_doc = await db.users.find_one(
        {"user_id": session_doc["user_id"]},
        {"_id": 0}
    )
    
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
    
    # Find or create user
    existing_user = await db.users.find_one({"email": email}, {"_id": 0})
    
    if existing_user:
        user_id = existing_user["user_id"]
        await db.users.update_one(
            {"email": email},
            {"$set": {"name": name, "picture": picture}}
        )
    else:
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        user = User(
            user_id=user_id,
            email=email,
            name=name,
            picture=picture
        )
        await db.users.insert_one(user.model_dump())
    
    # Create session
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    session = UserSession(
        session_token=session_token,
        user_id=user_id,
        expires_at=expires_at
    )
    
    await db.user_sessions.delete_many({"user_id": user_id})
    await db.user_sessions.insert_one(session.model_dump())
    
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
        max_age=7 * 24 * 60 * 60
    )
    
    user_doc = await db.users.find_one({"user_id": user_id}, {"_id": 0})
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
        await db.user_sessions.delete_many({"session_token": session_token})
    
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

@api_router.get("/products")
async def get_products(
    category: Optional[str] = None,
    search: Optional[str] = None,
    in_stock: Optional[bool] = None,
    include_variants: Optional[bool] = True  # Include variant details
):
    """Get all products from Luxura Inventory API - grouped by handle with variants
    ONLY returns: Genius, Tape (Bande Adhésive), I-Tip, Halo, Essentiels
    EXCLUDES: Clips, Ponytails, test products
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Fetch products AND inventory in parallel for accurate quantities
            products_task = client.get(f"{LUXURA_API_URL}/products")
            inventory_task = client.get(f"{LUXURA_API_URL}/inventory/view")
            
            products_response, inventory_response = await asyncio.gather(
                products_task, inventory_task, return_exceptions=True
            )
            
            if isinstance(products_response, Exception) or products_response.status_code != 200:
                raise HTTPException(status_code=502, detail="Unable to fetch products from Luxura API")
            
            products = products_response.json()
            
            # Build inventory lookup by product name/sku for accurate quantities
            inventory_by_name = {}
            inventory_by_sku = {}
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
                    if inv_sku:
                        inventory_by_sku[inv_sku.upper()] = inventory_by_sku.get(inv_sku.upper(), 0) + inv_qty
            
            # Group products by handle
            products_by_handle = {}
            
            for p in products:
                name = p.get('name', '')
                
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
                
                # Initialize handle group if needed
                if handle not in products_by_handle:
                    products_by_handle[handle] = {
                        'parent': None,
                        'variants': [],
                        'category': product_category,
                        'any_in_stock': False,
                        'total_quantity': 0
                    }
                
                # Check if this is a variant or parent
                if is_variant_record(p):
                    variant_info = extract_variant_info(p)
                    products_by_handle[handle]['variants'].append(variant_info)
                    
                    # Get real quantity from inventory
                    sku = p.get('sku', '').upper()
                    variant_qty = inventory_by_sku.get(sku, variant_info['quantity'])
                    variant_info['quantity'] = variant_qty
                    
                    # Update stock totals from variants
                    if variant_info['is_in_stock'] or variant_qty > 0:
                        products_by_handle[handle]['any_in_stock'] = True
                    products_by_handle[handle]['total_quantity'] += variant_qty
                else:
                    # This is a parent product
                    if products_by_handle[handle]['parent'] is None:
                        products_by_handle[handle]['parent'] = p
                        
                        # Get real quantity from inventory by name
                        clean_name = name.split(' — ')[0].strip().lower()
                        parent_qty = inventory_by_name.get(clean_name, 0)
                        if parent_qty > 0:
                            products_by_handle[handle]['total_quantity'] += parent_qty
                            products_by_handle[handle]['any_in_stock'] = True
                        elif p.get('is_in_stock', False):
                            products_by_handle[handle]['any_in_stock'] = True
            
            # Build result
            result = []
            for handle, data in products_by_handle.items():
                parent = data['parent']
                variants = data['variants']
                category = data['category']
                
                # If no parent, use first variant as base
                if parent is None and variants:
                    # Find a variant to use as base info
                    base_name = variants[0].get('longeur_raw', '')
                    for v in variants:
                        if v.get('sku'):
                            parent = {'name': v.get('sku', '').split('-')[0] if v.get('sku') else handle}
                            break
                
                if parent is None:
                    continue
                
                name = parent.get('name', '')
                # Clean up name (remove variant suffix)
                clean_name = name.split(' — ')[0].strip()
                
                # Get image
                image = get_product_image(handle, category)
                
                # Build Wix URL
                wix_url = f"https://www.luxuradistribution.com/product-page/{handle}" if handle else "https://www.luxuradistribution.com"
                
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
                
                # Sort variants by length/weight
                sorted_variants = sorted(variants, key=lambda v: (v.get('length', ''), v.get('weight', '')))
                
                product_data = {
                    "id": parent.get('id'),
                    "name": clean_name,
                    "price": price,
                    "description": clean_html(parent.get('description', '')),
                    "category": category,
                    "images": [image],
                    "in_stock": data['any_in_stock'],
                    "total_quantity": data['total_quantity'],
                    "sku": parent.get('sku'),
                    "wix_url": wix_url,
                    "handle": handle,
                    "variant_count": len(variants)
                }
                
                # Include variant details if requested
                if include_variants and variants:
                    product_data["variants"] = sorted_variants
                
                result.append(product_data)
            
            # Sort by category order, then by name
            category_order = {'genius': 0, 'halo': 1, 'tape': 2, 'i-tip': 3, 'essentiels': 4}
            result.sort(key=lambda x: (category_order.get(x['category'], 99), x['name']))
            
            return result
            
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Luxura API timeout")
    except Exception as e:
        logger.error(f"Error fetching products: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/products/{product_id}")
async def get_product(product_id: int):
    """Get a single product with all its variants from Luxura Inventory API
    Fetches real inventory quantities from /inventory/view
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Fetch product, all products (for variants), AND inventory in parallel
            product_task = client.get(f"{LUXURA_API_URL}/products/{product_id}")
            all_products_task = client.get(f"{LUXURA_API_URL}/products")
            inventory_task = client.get(f"{LUXURA_API_URL}/inventory/view")
            
            response, all_response, inventory_response = await asyncio.gather(
                product_task, all_products_task, inventory_task, return_exceptions=True
            )
            
            if isinstance(response, Exception) or response.status_code == 404:
                raise HTTPException(status_code=404, detail="Product not found")
            
            if response.status_code != 200:
                raise HTTPException(status_code=502, detail="Unable to fetch product from Luxura API")
            
            p = response.json()
            handle = p.get('handle', '')
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
                
                # Use parent product info if available
                if parent_product:
                    clean_name = parent_product.get('name', clean_name).split(' — ')[0].strip()
                    description = clean_html(parent_product.get('description', ''))
                else:
                    description = clean_html(p.get('description', ''))
                
                return {
                    "id": p.get('id'),
                    "name": clean_name,
                    "price": p.get('price', 0),
                    "description": description,
                    "category": category,
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
            return {
                "id": p.get('id'),
                "name": clean_name,
                "price": p.get('price', 0),
                "description": clean_html(p.get('description', '')),
                "category": category,
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
        Category(id="essentiels", name="Essentiels", description="Outils et produits d'entretien professionnels", image="https://static.wixstatic.com/media/de6cdb_5ba6af2b449d44039ce9c23d3517953b~mv2.jpg/v1/fill/w_600,h_600,q_85/s-l1200.jpg", wix_url="https://www.luxuradistribution.com/essentiels", order=5),
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
    Format: {TYPE}{LONGUEUR}{POIDS}-{CODE_COULEUR}-{NOM_COULEUR}
    Exemple: H20140-613-18A-BLOND-CARAMEL
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
    
    # Extraire code couleur et nom
    color_code, color_name = extract_color_info_for_sku(name)
    
    # Nettoyer le code couleur (remplacer / par -)
    clean_code = color_code.replace('/', '-')
    
    # Construire le SKU
    if length and weight:
        sku = f'{prefix}{length}{weight}-{clean_code}-{color_name}'
    else:
        # Produit parent sans variante
        sku = f'{prefix}-{clean_code}-{color_name}' if clean_code else f'{prefix}-{color_name}'
    
    return sku.strip('-').upper()

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
    
    cart_items = await db.cart_items.find(
        {"user_id": user.user_id},
        {"_id": 0}
    ).to_list(100)
    
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
    
    # Check if item already in cart
    existing = await db.cart_items.find_one(
        {"user_id": user.user_id, "product_id": item.product_id},
        {"_id": 0}
    )
    
    if existing:
        new_quantity = existing["quantity"] + item.quantity
        await db.cart_items.update_one(
            {"id": existing["id"]},
            {"$set": {"quantity": new_quantity}}
        )
        return {"message": "Cart updated", "quantity": new_quantity}
    else:
        cart_item = CartItem(
            user_id=user.user_id,
            product_id=item.product_id,
            quantity=item.quantity
        )
        await db.cart_items.insert_one(cart_item.model_dump())
        return {"message": "Added to cart", "id": cart_item.id}

@api_router.put("/cart/{item_id}")
async def update_cart_item(item_id: str, update: CartItemUpdate, request: Request):
    """Update cart item quantity"""
    user = await require_auth(request)
    
    if update.quantity <= 0:
        await db.cart_items.delete_one({"id": item_id, "user_id": user.user_id})
        return {"message": "Item removed"}
    
    result = await db.cart_items.update_one(
        {"id": item_id, "user_id": user.user_id},
        {"$set": {"quantity": update.quantity}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Cart item not found")
    
    return {"message": "Cart updated"}

@api_router.delete("/cart/{item_id}")
async def remove_from_cart(item_id: str, request: Request):
    """Remove item from cart"""
    user = await require_auth(request)
    
    result = await db.cart_items.delete_one({"id": item_id, "user_id": user.user_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Cart item not found")
    
    return {"message": "Item removed"}

@api_router.delete("/cart")
async def clear_cart(request: Request):
    """Clear all items from cart"""
    user = await require_auth(request)
    await db.cart_items.delete_many({"user_id": user.user_id})
    return {"message": "Cart cleared"}

# ==================== BLOG ENDPOINTS ====================

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
        
        # Get existing blog posts to avoid duplicates
        existing_posts = await db.blog_posts.find({}, {"title": 1}).to_list(100)
        existing_titles = [p.get("title", "").lower() for p in existing_posts]
        
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
        
        # Create blog post document
        post_id = f"seo-{uuid.uuid4().hex[:8]}"
        blog_post = {
            "id": post_id,
            "title": blog_data.get("title", topic_data["topic"]),
            "excerpt": blog_data.get("excerpt", topic_data["meta_description"]),
            "content": blog_data.get("content", ""),
            "meta_description": blog_data.get("meta_description", topic_data["meta_description"]),
            "tags": blog_data.get("tags", keywords_to_use[:5]),
            "image": f"https://static.wixstatic.com/media/de6cdb_ed493ddeab524054935dfbf0714b7e29~mv2.jpg",
            "author": "Luxura Distribution",
            "created_at": datetime.now(timezone.utc),
            "seo_keywords": keywords_to_use,
            "auto_generated": True
        }
        
        await db.blog_posts.insert_one(blog_post)
        
        blog_post.pop("_id", None)
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
async def delete_blog_post(post_id: str):
    """Delete a blog post"""
    result = await db.blog_posts.delete_one({"id": post_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Post not found")
    return {"message": "Post deleted successfully"}

@api_router.get("/blog")
async def get_blog_posts():
    """Get all blog posts"""
    posts = await db.blog_posts.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)
    if not posts:
        return [
            {
                "id": "entretien-extensions",
                "title": "Comment entretenir vos extensions capillaires",
                "content": "Les extensions capillaires nécessitent un entretien régulier.",
                "excerpt": "Découvrez nos conseils d'experts pour maintenir vos extensions.",
                "image": "https://static.wixstatic.com/media/de6cdb_ed493ddeab524054935dfbf0714b7e29~mv2.jpg",
                "author": "Luxura Distribution",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
        ]
    return posts

@api_router.get("/blog/{post_id}")
async def get_blog_post(post_id: str):
    """Get a single blog post"""
    post = await db.blog_posts.find_one({"id": post_id}, {"_id": 0})
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
    
    # Get the blog post from our DB
    post = await db.blog_posts.find_one({"id": post_id}, {"_id": 0})
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
                # Update our record with Wix ID
                await db.blog_posts.update_one(
                    {"id": post_id},
                    {"$set": {"wix_post_id": wix_response.get("draftPost", {}).get("id"), "pushed_to_wix": True}}
                )
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
            
            # Get existing posts to avoid duplicates
            existing_posts = await db.blog_posts.find({}, {"title": 1}).to_list(100)
            existing_titles = [p.get("title", "").lower() for p in existing_posts]
            
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
            
            await db.blog_posts.insert_one(blog_post)
            logger.info(f"Daily SEO blog generated: {blog_post['title']}")
            
            # Log to SEO history
            await db.seo_generation_log.insert_one({
                "date": datetime.now(timezone.utc),
                "post_id": post_id,
                "title": blog_post["title"],
                "keywords": keywords_to_use,
                "success": True
            })
            
        except Exception as e:
            logger.error(f"Daily SEO generation error: {e}")
            await db.seo_generation_log.insert_one({
                "date": datetime.now(timezone.utc),
                "error": str(e),
                "success": False
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
    
    total_posts = await db.blog_posts.count_documents({})
    auto_generated = await db.blog_posts.count_documents({"auto_generated": True})
    pushed_to_wix = await db.blog_posts.count_documents({"pushed_to_wix": True})
    
    # Get recent generation logs
    recent_logs = await db.seo_generation_log.find({}).sort("date", -1).to_list(10)
    
    # Calculate keywords coverage
    all_keywords = []
    async for post in db.blog_posts.find({"seo_keywords": {"$exists": True}}):
        all_keywords.extend(post.get("seo_keywords", []))
    
    keyword_counts = {}
    for kw in all_keywords:
        keyword_counts[kw] = keyword_counts.get(kw, 0) + 1
    
    return {
        "total_blog_posts": total_posts,
        "auto_generated_posts": auto_generated,
        "pushed_to_wix": pushed_to_wix,
        "recent_generations": [
            {
                "date": log.get("date").isoformat() if log.get("date") else None,
                "title": log.get("title"),
                "success": log.get("success")
            } for log in recent_logs
        ],
        "top_keywords_used": sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:10],
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
            
            # Log results
            await db.backlink_runs.insert_one({
                "date": datetime.now(timezone.utc),
                "stdout": result.stdout[:5000] if result.stdout else None,
                "stderr": result.stderr[:5000] if result.stderr else None,
                "return_code": result.returncode,
                "success": result.returncode == 0
            })
            
            logger.info(f"Backlink automation completed with code {result.returncode}")
            
        except subprocess.TimeoutExpired:
            await db.backlink_runs.insert_one({
                "date": datetime.now(timezone.utc),
                "error": "Timeout after 5 minutes",
                "success": False
            })
        except Exception as e:
            await db.backlink_runs.insert_one({
                "date": datetime.now(timezone.utc),
                "error": str(e),
                "success": False
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
    
    runs = await db.backlink_runs.find({}).sort("date", -1).to_list(10)
    
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
                "success": run.get("success"),
                "error": run.get("error"),
                "return_code": run.get("return_code")
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
            
            await db.backlink_runs.insert_one({
                "date": datetime.now(timezone.utc),
                "type": "auto_verify_loop",
                "stdout": result.stdout[-5000:] if result.stdout else None,
                "return_code": result.returncode,
                "success": result.returncode == 0
            })
            
        except subprocess.TimeoutExpired:
            await db.backlink_runs.insert_one({
                "date": datetime.now(timezone.utc),
                "type": "auto_verify_loop",
                "error": "Loop completed after 5 hours",
                "success": True
            })
        except Exception as e:
            await db.backlink_runs.insert_one({
                "date": datetime.now(timezone.utc),
                "type": "auto_verify_loop",
                "error": str(e),
                "success": False
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
    
    # Fallback to local DB
    query = {}
    if city:
        query["city"] = {"$regex": city, "$options": "i"}
    
    salons = await db.salons.find(query, {"_id": 0}).to_list(100)
    if not salons:
        return [
            {"id": "salon-1", "name": "Salon Carouso", "address": "123 Rue Principale", "city": "Montréal", "phone": "514-555-0001"},
            {"id": "salon-2", "name": "Salon Élégance", "address": "456 Boulevard Saint-Laurent", "city": "Montréal", "phone": "514-555-0002"},
            {"id": "salon-3", "name": "Coiffure Prestige", "address": "789 Avenue Cartier", "city": "Québec", "phone": "418-555-0003"},
        ]
    return salons

# ==================== HEALTH CHECK ====================

@api_router.get("/")
async def root():
    return {"message": "Luxura Distribution API", "status": "running", "inventory_api": LUXURA_API_URL}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy"}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
