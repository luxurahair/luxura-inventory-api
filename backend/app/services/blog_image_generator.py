"""
🖼️ BLOG IMAGE GENERATOR - Génération d'images uniques pour blogs Wix
====================================================================
Utilise Grok (grok-imagine-image) pour générer des images uniques
avec les règles de style Luxura (cheveux volumineux, glamour, etc.)

IMPORTANT: Chaque blog obtient une image UNIQUE générée par IA!
"""

import os
import io
import logging
import requests
import base64
from typing import Optional, Tuple
from PIL import Image

# Import des règles de prompts Luxura
from app.services.luxura_image_prompts import (
    generate_luxura_image_prompt,
    get_prompt_for_content_type,
    get_preset_prompt,
    LUXURA_HAIR_DESCRIPTIONS,
    LUXURY_LOCATIONS,
    PHOTO_ANGLES,
)
from app.services.watermark import create_gold_text_watermark

logger = logging.getLogger(__name__)

# Configuration API xAI
XAI_API_KEY = os.getenv("XAI_API_KEY")
XAI_BASE_URL = "https://api.x.ai/v1"


def _get_xai_headers():
    """Retourne les headers pour l'API xAI"""
    if not XAI_API_KEY:
        raise Exception("XAI_API_KEY non configuré - impossible de générer des images")
    return {
        "Authorization": f"Bearer {XAI_API_KEY}",
        "Content-Type": "application/json"
    }


def _map_topic_to_content_type(topic: str) -> str:
    """
    Mappe un sujet de blog vers un type de contenu pour les prompts.
    
    Args:
        topic: Titre ou sujet du blog
    
    Returns:
        Type de contenu (product, educational, weekend, testimonial, b2b, magazine)
    """
    topic_lower = topic.lower()
    
    # Mapping basé sur les mots-clés
    if any(word in topic_lower for word in ['mariage', 'wedding', 'cérémonie', 'fête', 'événement', 'gala']):
        return "magazine"
    elif any(word in topic_lower for word in ['tendance', 'trend', '2025', '2026', 'mode', 'style', 'saison']):
        return "magazine"
    elif any(word in topic_lower for word in ['entretien', 'soin', 'laver', 'brush', 'conseils', 'comment']):
        return "educational"
    elif any(word in topic_lower for word in ['fournisseur', 'salon', 'professionnel', 'partenaire', 'b2b', 'grossiste']):
        return "b2b"
    elif any(word in topic_lower for word in ['genius', 'tape', 'installation', 'technique', 'pose']):
        return "educational"
    elif any(word in topic_lower for word in ['été', 'vacances', 'plage', 'weekend', 'voyage']):
        return "weekend"
    elif any(word in topic_lower for word in ['avis', 'témoignage', 'client', 'résultat', 'transformation']):
        return "testimonial"
    elif any(word in topic_lower for word in ['produit', 'collection', 'nouveau', 'lancement']):
        return "product"
    else:
        # Par défaut: magazine (les plus belles images)
        return "magazine"


def generate_blog_image_prompt(topic: str, keywords: list = None) -> str:
    """
    Génère un prompt optimisé pour une image de blog basée sur le sujet.
    
    Args:
        topic: Titre ou sujet du blog
        keywords: Mots-clés additionnels (optionnel)
    
    Returns:
        Prompt complet pour Grok
    """
    content_type = _map_topic_to_content_type(topic)
    
    # Utiliser le générateur centralisé
    prompt = get_prompt_for_content_type(content_type)
    
    # Ajouter des éléments contextuels si keywords fournis
    if keywords:
        keyword_context = ", ".join(keywords[:3])  # Max 3 keywords
        prompt = f"{prompt}, related to {keyword_context}"
    
    logger.info(f"📝 Prompt généré pour '{topic[:50]}...' (type: {content_type})")
    return prompt


async def generate_blog_image_with_grok(
    topic: str,
    keywords: list = None,
    add_watermark: bool = True
) -> Optional[dict]:
    """
    Génère une image unique pour un blog via Grok API.
    
    Args:
        topic: Titre du blog
        keywords: Mots-clés du blog
        add_watermark: Ajouter le watermark LUXURA doré
    
    Returns:
        Dict avec 'url' (URL de l'image générée) et 'prompt' (prompt utilisé)
        ou None si échec
    """
    if not XAI_API_KEY:
        logger.error("❌ XAI_API_KEY non configuré!")
        return None
    
    # Générer le prompt
    prompt = generate_blog_image_prompt(topic, keywords)
    
    logger.info(f"🎨 Génération image Grok pour blog: {topic[:50]}...")
    
    try:
        response = requests.post(
            f"{XAI_BASE_URL}/images/generations",
            headers=_get_xai_headers(),
            json={
                "model": "grok-imagine-image",
                "prompt": prompt,
                "n": 1
            },
            timeout=90  # 90 secondes timeout pour génération
        )
        
        if response.status_code == 200:
            data = response.json()
            images = data.get("data", [])
            
            if images and len(images) > 0:
                image_url = images[0].get("url")
                
                if image_url:
                    logger.info(f"✅ Image générée avec succès: {image_url[:80]}...")
                    
                    return {
                        "url": image_url,
                        "prompt": prompt,
                        "model": "grok-imagine-image",
                        "success": True
                    }
        
        logger.error(f"❌ Erreur Grok API: {response.status_code} - {response.text[:200]}")
        return None
        
    except requests.exceptions.Timeout:
        logger.error("❌ Timeout génération image Grok (90s)")
        return None
    except Exception as e:
        logger.error(f"❌ Erreur génération image: {str(e)}")
        return None


def generate_blog_image_sync(
    topic: str,
    keywords: list = None
) -> Optional[str]:
    """
    Version SYNCHRONE de la génération d'image pour blog.
    Retourne directement l'URL de l'image générée.
    
    Cette fonction est utilisée par le cron blog qui n'est pas async.
    
    Args:
        topic: Titre du blog
        keywords: Mots-clés du blog
    
    Returns:
        URL de l'image générée ou None
    """
    if not XAI_API_KEY:
        logger.error("❌ XAI_API_KEY non configuré!")
        return None
    
    # Générer le prompt
    prompt = generate_blog_image_prompt(topic, keywords)
    
    logger.info(f"🎨 [SYNC] Génération image Grok pour: {topic[:50]}...")
    
    try:
        response = requests.post(
            f"{XAI_BASE_URL}/images/generations",
            headers=_get_xai_headers(),
            json={
                "model": "grok-imagine-image",
                "prompt": prompt,
                "n": 1
            },
            timeout=90
        )
        
        if response.status_code == 200:
            data = response.json()
            images = data.get("data", [])
            
            if images and len(images) > 0:
                image_url = images[0].get("url")
                
                if image_url:
                    logger.info(f"✅ [SYNC] Image générée: {image_url[:80]}...")
                    return image_url
        
        logger.error(f"❌ [SYNC] Erreur Grok: {response.status_code}")
        return None
        
    except Exception as e:
        logger.error(f"❌ [SYNC] Erreur: {str(e)}")
        return None


# ============================================
# FALLBACK: Images statiques de secours
# ============================================

FALLBACK_IMAGES = [
    # Images glamour de haute qualité (Unsplash) - utilisées SEULEMENT si Grok échoue
    "https://images.unsplash.com/photo-1519699047748-de8e457a634e?w=1200&q=90",
    "https://images.unsplash.com/photo-1502823403499-6ccfcf4fb453?w=1200&q=90",
    "https://images.unsplash.com/photo-1529626455594-4ff0802cfb7e?w=1200&q=90",
    "https://images.unsplash.com/photo-1517841905240-472988babdf9?w=1200&q=90",
    "https://images.unsplash.com/photo-1531746020798-e6953c6e8e04?w=1200&q=90",
]


def get_fallback_image() -> str:
    """Retourne une image de secours aléatoire si Grok échoue"""
    import random
    return random.choice(FALLBACK_IMAGES)


def get_blog_image_for_topic_v2(topic: str, keywords: list = None) -> str:
    """
    NOUVELLE VERSION: Génère une image unique via Grok OU retourne fallback.
    
    Cette fonction remplace l'ancienne get_blog_image_for_topic() qui
    utilisait des images Unsplash statiques répétitives.
    
    Args:
        topic: Titre du blog
        keywords: Mots-clés optionnels
    
    Returns:
        URL de l'image (Grok générée ou fallback)
    """
    # Essayer de générer via Grok
    grok_url = generate_blog_image_sync(topic, keywords)
    
    if grok_url:
        return grok_url
    
    # Fallback si Grok échoue
    logger.warning(f"⚠️ Fallback image utilisée pour: {topic[:50]}")
    return get_fallback_image()
