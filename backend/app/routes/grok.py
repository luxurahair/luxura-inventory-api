# app/routes/grok.py
"""
🤖 GROK/xAI ROUTER - Luxura Inventory API
==========================================
Génération d'images et vidéos via l'API xAI (Grok).

Endpoints:
- GET  /grok/status          : Vérifier la connexion
- POST /grok/image           : Générer une image
- POST /grok/video           : Générer une vidéo
- POST /grok/luxura-image    : Image produit Luxura (prompt optimisé)
- POST /grok/luxura-video    : Vidéo produit Luxura (prompt optimisé)

Variables d'environnement requises:
- XAI_API_KEY : Clé API xAI (console.x.ai)
"""

import os
import json
import logging
import requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

router = APIRouter(prefix="/grok", tags=["Grok / xAI"])

# Configuration
XAI_API_KEY = os.getenv("XAI_API_KEY")
XAI_BASE_URL = "https://api.x.ai/v1"

logger = logging.getLogger(__name__)


# ==================== MODELS ====================

class ImageRequest(BaseModel):
    prompt: str
    n: Optional[int] = 1
    model: Optional[str] = "grok-2-image"


class VideoRequest(BaseModel):
    prompt: str
    image_url: Optional[str] = None  # Pour image-to-video
    duration: Optional[int] = 8
    model: Optional[str] = "grok-imagine-video"


class LuxuraProductRequest(BaseModel):
    product_type: str  # "trame_genius", "rallonges_ombre", "clip_ins", etc.
    color: str  # "blonde", "ombre_brun_blonde", "noir", etc.
    style: Optional[str] = "salon_premium"  # "salon_premium", "studio_blanc", "lifestyle"
    offer_type: Optional[str] = "direct_sale"  # "direct_sale", "salon_affilie"


# ==================== PROMPTS LUXURA ====================

LUXURA_CONTEXT = """Tu es un générateur d'images/vidéos pour Luxura Distribution, 
importateur direct d'extensions capillaires premium au Québec.

RÈGLES:
- Style: luxe, élégant, premium, professionnel
- Focus: texture soyeuse, brillance, qualité premium
- Contexte: salon de coiffure haut de gamme ou studio neutre
- Mains: élégantes, manucure soignée, réalistes
- Éclairage: commercial beauté, doux, premium
- Pas de: texte, watermark, mains déformées, doigts extra
"""

LUXURA_IMAGE_PROMPTS = {
    "salon_demo": """Close-up luxury beauty shot of a professional hairstylist's elegant hands 
demonstrating premium {color} hair extensions. One hand holds the top of the extension piece, 
the other hand smoothly glides down the silky hair showing texture and shine. 
Premium salon lighting, elegant manicured nails, realistic hands, commercial beauty style, 
clean neutral background, product-focused, high-end quality.""",
    
    "product_showcase": """Premium product photography of {product_type} hair extensions in {color}. 
Clean white studio background, professional lighting highlighting the silky texture and natural shine. 
Hair laid out elegantly showing the full length and color gradient. 
Luxury beauty commercial style, high resolution, product catalog quality.""",
    
    "lifestyle": """Beautiful woman with flowing {color} hair extensions, natural movement, 
golden hour lighting, elegant and confident pose. Premium beauty editorial style, 
soft focus background, hair texture and shine emphasized. High-end fashion photography.""",
    
    "before_after": """Split view beauty transformation showing hair before and after 
premium {color} hair extensions. Left side: natural hair. Right side: luxurious voluminous 
result with extensions blended perfectly. Salon setting, professional lighting, 
dramatic transformation, beauty commercial quality."""
}

LUXURA_VIDEO_PROMPTS = {
    "hand_demo": """Cinematic close-up beauty video. A professional hairstylist's elegant hands 
slowly demonstrate premium {color} hair extensions. One hand holds the extension at the top, 
the other hand glides smoothly downward through the silky hair showing the premium texture. 
Slow, elegant, satisfying movement. Luxury salon atmosphere, soft professional lighting, 
shallow depth of field. No distorted hands, realistic motion, premium commercial quality.""",
    
    "flowing_hair": """Slow motion video of beautiful flowing {color} hair extensions. 
Soft breeze creates gentle natural movement. Light catches the shine and texture. 
Premium beauty commercial style, cinematic lighting, elegant and luxurious atmosphere.""",
    
    "salon_application": """Professional hairstylist applying premium {color} hair extensions 
in a luxury salon. Skilled hands working with care. Client transformation visible. 
Elegant salon interior, professional lighting, before and after reveal. 
Beauty makeover documentary style, high-end production quality."""
}


# ==================== HELPERS ====================

def get_headers():
    """Retourne les headers pour l'API xAI"""
    if not XAI_API_KEY:
        raise Exception("XAI_API_KEY non configuré")
    return {
        "Authorization": f"Bearer {XAI_API_KEY}",
        "Content-Type": "application/json"
    }


def build_luxura_prompt(template: str, product_type: str, color: str) -> str:
    """Construit un prompt Luxura optimisé"""
    color_descriptions = {
        "blonde": "luxurious platinum blonde",
        "ombre_brun_blonde": "stunning ombre from rich brown to golden blonde",
        "noir": "deep rich black",
        "chatain": "warm chestnut brown",
        "roux": "vibrant copper red",
        "balayage": "natural sun-kissed balayage"
    }
    
    product_descriptions = {
        "trame_genius": "Genius Weft seamless hair extension",
        "rallonges": "premium clip-in hair extensions",
        "tape_ins": "invisible tape-in extensions",
        "ponytail": "luxury ponytail extension",
        "bundle": "premium hair bundle"
    }
    
    color_desc = color_descriptions.get(color, color)
    product_desc = product_descriptions.get(product_type, product_type)
    
    return template.format(color=color_desc, product_type=product_desc)


# ==================== ENDPOINTS ====================

@router.get("/status")
def grok_status():
    """📊 Vérifier le statut de la connexion xAI/Grok"""
    if not XAI_API_KEY:
        return {
            "success": False,
            "error": "XAI_API_KEY non configuré",
            "fix": "Ajoutez XAI_API_KEY dans les variables d'environnement (console.x.ai)"
        }
    
    # Test simple avec l'API
    try:
        response = requests.get(
            f"{XAI_BASE_URL}/models",
            headers=get_headers(),
            timeout=10
        )
        
        if response.status_code == 200:
            return {
                "success": True,
                "message": "✅ Connecté à l'API xAI/Grok",
                "models_available": True
            }
        else:
            return {
                "success": False,
                "error": f"Erreur API: {response.status_code}",
                "detail": response.text[:200]
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/image")
def generate_image(request: ImageRequest):
    """
    🖼️ Générer une image avec Grok
    
    Args:
        prompt: Description de l'image
        n: Nombre d'images (1-10)
        model: Modèle (grok-2-image par défaut)
    """
    try:
        response = requests.post(
            f"{XAI_BASE_URL}/images/generations",
            headers=get_headers(),
            json={
                "model": request.model,
                "prompt": request.prompt,
                "n": request.n
            },
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "images": data.get("data", []),
                "model": request.model
            }
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/video")
def generate_video(request: VideoRequest):
    """
    🎬 Générer une vidéo avec Grok Imagine
    
    Args:
        prompt: Description de la vidéo
        image_url: Image source (optionnel, pour image-to-video)
        duration: Durée en secondes (max 10)
        model: Modèle vidéo
    """
    try:
        payload = {
            "model": request.model,
            "prompt": request.prompt,
            "duration": min(request.duration, 10)
        }
        
        if request.image_url:
            payload["image_url"] = request.image_url
        
        response = requests.post(
            f"{XAI_BASE_URL}/videos/generations",
            headers=get_headers(),
            json=payload,
            timeout=120
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "video": data,
                "model": request.model
            }
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/luxura-image")
def generate_luxura_image(request: LuxuraProductRequest):
    """
    🖼️ Générer une image produit Luxura (prompt optimisé)
    
    Args:
        product_type: Type de produit (trame_genius, rallonges, etc.)
        color: Couleur (blonde, ombre_brun_blonde, noir, etc.)
        style: Style visuel (salon_demo, product_showcase, lifestyle, before_after)
    """
    style = request.style if request.style in LUXURA_IMAGE_PROMPTS else "salon_demo"
    template = LUXURA_IMAGE_PROMPTS[style]
    prompt = build_luxura_prompt(template, request.product_type, request.color)
    
    logger.info(f"🖼️ Génération image Luxura: {request.product_type} / {request.color}")
    
    try:
        response = requests.post(
            f"{XAI_BASE_URL}/images/generations",
            headers=get_headers(),
            json={
                "model": "grok-2-image",
                "prompt": prompt,
                "n": 1
            },
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "product": request.product_type,
                "color": request.color,
                "style": style,
                "prompt_used": prompt[:200] + "...",
                "images": data.get("data", [])
            }
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/luxura-video")
def generate_luxura_video(request: LuxuraProductRequest):
    """
    🎬 Générer une vidéo produit Luxura (prompt optimisé)
    
    Args:
        product_type: Type de produit
        color: Couleur
        style: Style (hand_demo, flowing_hair, salon_application)
    """
    style = request.style if request.style in LUXURA_VIDEO_PROMPTS else "hand_demo"
    template = LUXURA_VIDEO_PROMPTS[style]
    prompt = build_luxura_prompt(template, request.product_type, request.color)
    
    logger.info(f"🎬 Génération vidéo Luxura: {request.product_type} / {request.color}")
    
    try:
        response = requests.post(
            f"{XAI_BASE_URL}/videos/generations",
            headers=get_headers(),
            json={
                "model": "grok-imagine-video",
                "prompt": prompt,
                "duration": 8
            },
            timeout=120
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "product": request.product_type,
                "color": request.color,
                "style": style,
                "prompt_used": prompt[:200] + "...",
                "video": data
            }
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/prompts")
def list_luxura_prompts():
    """📋 Lister les prompts Luxura disponibles"""
    return {
        "image_styles": list(LUXURA_IMAGE_PROMPTS.keys()),
        "video_styles": list(LUXURA_VIDEO_PROMPTS.keys()),
        "product_types": ["trame_genius", "rallonges", "tape_ins", "ponytail", "bundle"],
        "colors": ["blonde", "ombre_brun_blonde", "noir", "chatain", "roux", "balayage"],
        "context": LUXURA_CONTEXT
    }
