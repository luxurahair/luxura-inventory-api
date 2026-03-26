# =====================================================
# BLOG AUTOMATION SYSTEM - Luxura Distribution
# Génération automatique + Publication Wix + Images libres
# =====================================================

import os
import random
import uuid
import httpx
import asyncio
import json
from datetime import datetime, timezone
from typing import Optional, List, Dict
import logging

logger = logging.getLogger(__name__)

# =====================================================
# UNSPLASH FREE IMAGES - Catégorisées par sujet
# =====================================================

# FORMAT OPEN GRAPH: 1200x630 px (ratio 1.91:1) pour Wix Blog Cover
UNSPLASH_IMAGES = {
    "halo": [
        "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=1200&h=630&fit=crop",  # Femme cheveux longs
        "https://images.unsplash.com/photo-1580618672591-eb180b1a973f?w=1200&h=630&fit=crop",  # Salon coiffure
        "https://images.unsplash.com/photo-1560066984-138dadb4c035?w=1200&h=630&fit=crop",  # Cheveux brillants
        "https://images.unsplash.com/photo-1519699047748-de8e457a634e?w=1200&h=630&fit=crop",  # Femme blonde
        "https://images.unsplash.com/photo-1605497788044-5a32c7078486?w=1200&h=630&fit=crop",  # Cheveux wavy
    ],
    "genius": [
        "https://images.unsplash.com/photo-1522337094846-8a818192de1f?w=1200&h=630&fit=crop",  # Cheveux parfaits
        "https://images.unsplash.com/photo-1487412720507-e7ab37603c6f?w=1200&h=630&fit=crop",  # Femme professionnelle
        "https://images.unsplash.com/photo-1526047932273-341f2a7631f9?w=1200&h=630&fit=crop",  # Salon luxe
        "https://images.unsplash.com/photo-1616683693504-3ea7e9ad6fec?w=1200&h=630&fit=crop",  # Extensions visibles
        "https://images.unsplash.com/photo-1559599101-f09722fb4948?w=1200&h=630&fit=crop",  # Coiffeuse travail
    ],
    "tape": [
        "https://images.unsplash.com/photo-1595476108010-b4d1f102b1b1?w=1200&h=630&fit=crop",  # Pose extensions
        "https://images.unsplash.com/photo-1562322140-8baeececf3df?w=1200&h=630&fit=crop",  # Salon coiffure
        "https://images.unsplash.com/photo-1560066984-138dadb4c035?w=1200&h=630&fit=crop",  # Application
        "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=1200&h=630&fit=crop",  # Résultat
        "https://images.unsplash.com/photo-1502823403499-6ccfcf4fb453?w=1200&h=630&fit=crop",  # Outils salon
    ],
    "itip": [
        "https://images.unsplash.com/photo-1527799820374-dcf8d9d4a388?w=1200&h=630&fit=crop",  # Détail cheveux
        "https://images.unsplash.com/photo-1559599101-f09722fb4948?w=1200&h=630&fit=crop",  # Application pro
        "https://images.unsplash.com/photo-1580618672591-eb180b1a973f?w=1200&h=630&fit=crop",  # Salon
        "https://images.unsplash.com/photo-1522337094846-8a818192de1f?w=1200&h=630&fit=crop",  # Cheveux naturels
        "https://images.unsplash.com/photo-1492106087820-71f1a00d2b11?w=1200&h=630&fit=crop",  # Portrait femme
    ],
    "entretien": [
        "https://images.unsplash.com/photo-1527799820374-dcf8d9d4a388?w=1200&h=630&fit=crop",  # Brossage
        "https://images.unsplash.com/photo-1522337094846-8a818192de1f?w=1200&h=630&fit=crop",  # Soins
        "https://images.unsplash.com/photo-1519699047748-de8e457a634e?w=1200&h=630&fit=crop",  # Cheveux sains
        "https://images.unsplash.com/photo-1560066984-138dadb4c035?w=1200&h=630&fit=crop",  # Brillance
        "https://images.unsplash.com/photo-1502823403499-6ccfcf4fb453?w=1200&h=630&fit=crop",  # Produits
    ],
    "tendances": [
        "https://images.unsplash.com/photo-1605497788044-5a32c7078486?w=1200&h=630&fit=crop",  # Style moderne
        "https://images.unsplash.com/photo-1519699047748-de8e457a634e?w=1200&h=630&fit=crop",  # Blonde tendance
        "https://images.unsplash.com/photo-1487412720507-e7ab37603c6f?w=1200&h=630&fit=crop",  # Look pro
        "https://images.unsplash.com/photo-1492106087820-71f1a00d2b11?w=1200&h=630&fit=crop",  # Style 2025
        "https://images.unsplash.com/photo-1580618672591-eb180b1a973f?w=1200&h=630&fit=crop",  # Salon tendance
    ],
    "general": [
        "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=1200&h=630&fit=crop",
        "https://images.unsplash.com/photo-1560066984-138dadb4c035?w=1200&h=630&fit=crop",
        "https://images.unsplash.com/photo-1519699047748-de8e457a634e?w=1200&h=630&fit=crop",
        "https://images.unsplash.com/photo-1522337094846-8a818192de1f?w=1200&h=630&fit=crop",
        "https://images.unsplash.com/photo-1487412720507-e7ab37603c6f?w=1200&h=630&fit=crop",
    ]
}

# =====================================================
# SUJETS DE BLOG - Focus Halo, Genius, Tape, I-Tip
# =====================================================

BLOG_TOPICS_EXTENDED = [
    # === HALO EXTENSIONS ===
    {
        "topic": "Extensions Halo : La révolution du volume instantané sans engagement",
        "category": "halo",
        "keywords": ["extensions halo Québec", "volume instantané", "fil invisible", "extensions sans colle"],
        "focus_product": "Halo Everly"
    },
    {
        "topic": "Halo vs autres extensions : Pourquoi le fil invisible conquiert le Québec",
        "category": "halo", 
        "keywords": ["halo vs clip-in", "extensions fil invisible", "comparatif extensions"],
        "focus_product": "Halo Everly"
    },
    {
        "topic": "Comment porter des extensions Halo pour un look naturel parfait",
        "category": "halo",
        "keywords": ["tutoriel halo", "porter extensions halo", "look naturel extensions"],
        "focus_product": "Halo Everly"
    },
    {
        "topic": "Extensions Halo pour cheveux fins : La solution idéale au Québec",
        "category": "halo",
        "keywords": ["cheveux fins solution", "halo cheveux fins", "volume cheveux fins"],
        "focus_product": "Halo Everly"
    },
    
    # === GENIUS WEFT ===
    {
        "topic": "Genius Weft : La technologie révolutionnaire de trame invisible 0.78mm",
        "category": "genius",
        "keywords": ["genius weft Québec", "trame invisible", "extensions professionnelles"],
        "focus_product": "Genius Vivian"
    },
    {
        "topic": "Pourquoi les salons du Québec adoptent les extensions Genius Weft",
        "category": "genius",
        "keywords": ["genius weft salon", "extensions salon professionnel", "fournisseur extensions"],
        "focus_product": "Genius Vivian"
    },
    {
        "topic": "Installation Genius Weft : Guide complet pour professionnels",
        "category": "genius",
        "keywords": ["installer genius weft", "technique couture invisible", "formation extensions"],
        "focus_product": "Genius Vivian"
    },
    {
        "topic": "Genius Weft vs Tape-in : Quelle technique choisir pour votre cliente ?",
        "category": "genius",
        "keywords": ["genius vs tape", "comparatif extensions", "meilleure technique extensions"],
        "focus_product": "Genius Vivian"
    },
    
    # === TAPE-IN / BANDE ADHÉSIVE ===
    {
        "topic": "Extensions Bande Adhésive Aurora : Application sandwich professionnelle",
        "category": "tape",
        "keywords": ["tape-in extensions", "bande adhésive cheveux", "extensions sandwich"],
        "focus_product": "Tape Aurora"
    },
    {
        "topic": "Combien de temps durent les extensions Tape-in ? Guide complet",
        "category": "tape",
        "keywords": ["durée tape-in", "entretien tape extensions", "repose extensions"],
        "focus_product": "Tape Aurora"
    },
    {
        "topic": "Tape-in vs Genius Weft : Le match des extensions professionnelles",
        "category": "tape",
        "keywords": ["tape vs genius", "meilleures extensions salon", "comparatif technique"],
        "focus_product": "Tape Aurora"
    },
    {
        "topic": "Retrait et repositionnement des extensions Tape-in : Guide expert",
        "category": "tape",
        "keywords": ["retrait tape extensions", "repositionner extensions", "entretien tape-in"],
        "focus_product": "Tape Aurora"
    },
    
    # === I-TIP / KÉRATINE ===
    {
        "topic": "Extensions I-Tip kératine : La technique mèche par mèche ultime",
        "category": "itip",
        "keywords": ["i-tip extensions", "kératine cheveux", "extensions mèche par mèche"],
        "focus_product": "I-Tip Eleanor"
    },
    {
        "topic": "I-Tip vs Tape-in : Quelle méthode pour un résultat naturel ?",
        "category": "itip",
        "keywords": ["i-tip vs tape", "extensions naturelles", "kératine vs adhésive"],
        "focus_product": "I-Tip Eleanor"
    },
    {
        "topic": "Formation extensions I-Tip : Maîtriser la fusion kératine",
        "category": "itip",
        "keywords": ["formation i-tip", "technique kératine", "apprendre extensions"],
        "focus_product": "I-Tip Eleanor"
    },
    {
        "topic": "Entretien extensions I-Tip : Prolonger la durée de vie jusqu'à 6 mois",
        "category": "itip",
        "keywords": ["entretien i-tip", "durée extensions kératine", "soins extensions"],
        "focus_product": "I-Tip Eleanor"
    },
    
    # === SUJETS GÉNÉRAUX ===
    {
        "topic": "Tendances extensions cheveux 2025 : Balayage, ombré et couleurs naturelles",
        "category": "tendances",
        "keywords": ["tendances extensions 2025", "couleurs cheveux tendance", "balayage extensions"],
        "focus_product": None
    },
    {
        "topic": "Comment entretenir ses extensions cheveux : Guide professionnel complet",
        "category": "entretien",
        "keywords": ["entretien extensions", "soins extensions cheveux", "durée vie extensions"],
        "focus_product": None
    },
    {
        "topic": "Devenir partenaire Luxura : Programme salon extensions cheveux Québec",
        "category": "general",
        "keywords": ["partenaire salon extensions", "distributeur extensions Québec", "grossiste cheveux"],
        "focus_product": None
    },
    {
        "topic": "Extensions cheveux naturel vs synthétique : Le guide définitif",
        "category": "general",
        "keywords": ["extensions naturel vs synthétique", "cheveux remy", "qualité extensions"],
        "focus_product": None
    },
]

def get_blog_image_by_category(category: str) -> str:
    """Retourne une image libre de droits selon la catégorie"""
    images = UNSPLASH_IMAGES.get(category, UNSPLASH_IMAGES["general"])
    return random.choice(images)

# =====================================================
# WIX BLOG INTEGRATION
# =====================================================

async def get_wix_member_id(api_key: str, site_id: str) -> Optional[str]:
    """Récupère le member ID du propriétaire du site pour la publication"""
    try:
        async with httpx.AsyncClient() as client:
            # Try to get the current identity (site owner)
            response = await client.post(
                "https://www.wixapis.com/members/v1/members/query",
                headers={
                    "Authorization": api_key,
                    "wix-site-id": site_id,
                    "Content-Type": "application/json"
                },
                json={
                    "query": {
                        "paging": {"limit": 1}
                    }
                },
                timeout=30
            )
            logger.info(f"Wix members query response: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                members = data.get("members", [])
                if members:
                    member_id = members[0].get("id")
                    logger.info(f"Found Wix member ID: {member_id}")
                    return member_id
            
            # Alternative: Try to get site properties to find owner
            response2 = await client.get(
                "https://www.wixapis.com/site-properties/v4/properties",
                headers={
                    "Authorization": api_key,
                    "wix-site-id": site_id,
                    "Content-Type": "application/json"
                },
                timeout=30
            )
            logger.info(f"Wix site properties response: {response2.status_code}")
            if response2.status_code == 200:
                data = response2.json()
                logger.info(f"Site properties: {data}")
    except Exception as e:
        logger.error(f"Error getting Wix member ID: {e}")
    return None

# =====================================================
# WIX MEDIA MANAGER - Import d'images
# =====================================================

async def import_image_and_get_wix_uri(
    api_key: str,
    site_id: str,
    image_url: str,
    file_name: str = None
) -> Optional[Dict]:
    """
    Importe l'image et retourne un dict avec plusieurs formats d'URL.
    
    AMÉLIORATION: Retourne aussi l'URL statique (static.wixstatic.com)
    qui fonctionne mieux pour heroImage que le format wix:image://
    
    Returns:
        Dict avec:
        - wix_uri: format wix:image://v1/...
        - static_url: format https://static.wixstatic.com/media/...
        - file_id: ID du fichier Wix
        - width, height: dimensions
    """
    if not file_name:
        file_name = f"blog-cover-{uuid.uuid4().hex[:8]}.jpg"

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            payload = {
                "url": image_url,
                "displayName": file_name,
                "mediaType": "IMAGE",
                "mimeType": "image/jpeg",
                "filePath": f"/blog-covers/{file_name}"
            }

            logger.info(f"Importing image to Wix Media: {image_url[:60]}...")

            response = await client.post(
                "https://www.wixapis.com/site-media/v1/files/import",
                headers={
                    "Authorization": api_key,
                    "wix-site-id": site_id,
                    "Content-Type": "application/json"
                },
                json=payload
            )

            if response.status_code not in (200, 201):
                logger.error(f"Import failed: {response.status_code} - {response.text}")
                return None

            data = response.json()
            file_id = data.get("file", {}).get("id") or data.get("id")

            if not file_id:
                logger.error("No file ID returned from import")
                return None

            # Attendre que le fichier soit READY
            file_desc = await wait_until_wix_file_ready(api_key, site_id, file_id, timeout_sec=90)
            if not file_desc:
                logger.error("File never became READY")
                return None

            # Extraire les informations
            display_name = file_desc.get("displayName", file_name)
            media = file_desc.get("media", {}) or {}
            image_wrapper = media.get("image", {}) if isinstance(media, dict) else {}
            image_data = image_wrapper.get("image", {}) if isinstance(image_wrapper, dict) else {}
            width = image_data.get("width") or 1200
            height = image_data.get("height") or 630

            # Format wix:image:// (ne fonctionne pas bien)
            wix_uri = f"wix:image://v1/{file_id}/{display_name}#originWidth={width}&originHeight={height}"
            
            # Format URL statique avec ~mv2 (fonctionne mieux!)
            static_url = f"https://static.wixstatic.com/media/{file_id}"
            
            # Format avec dimensions explicites (évite w_NaN / h_NaN)
            static_url_with_size = f"https://static.wixstatic.com/media/{file_id}/v1/fill/w_{width},h_{height},al_c,q_90/{display_name}"
            
            logger.info(f"✅ Image ready - Static URL: {static_url}")
            logger.info(f"   Dimensions: {width}x{height}")
            
            return {
                "wix_uri": wix_uri,
                "static_url": static_url,
                "static_url_full": static_url_with_size,
                "file_id": file_id,
                "width": width,
                "height": height,
                "display_name": display_name
            }

    except Exception as e:
        logger.error(f"Error in import_image_and_get_wix_uri: {e}")
        return None


async def import_image_to_wix_media(
    api_key: str,
    site_id: str,
    image_url: str,
    file_name: str = None
) -> Optional[Dict]:
    """
    Importe une image externe dans le Wix Media Manager.
    IMPORTANT: L'import est asynchrone - il faut attendre operationStatus=READY
    """
    try:
        if not file_name:
            file_name = f"blog-cover-{uuid.uuid4().hex[:8]}.jpg"
        
        async with httpx.AsyncClient() as client:
            payload = {
                "url": image_url,
                "displayName": file_name,
                "mediaType": "IMAGE",
                "mimeType": "image/jpeg",
                "filePath": f"/blog/{file_name}"
            }
            
            logger.info(f"Importing image to Wix Media: {image_url[:50]}...")
            
            response = await client.post(
                "https://www.wixapis.com/site-media/v1/files/import",
                headers={
                    "Authorization": api_key,
                    "wix-site-id": site_id,
                    "Content-Type": "application/json"
                },
                json=payload,
                timeout=60
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                logger.info(f"Wix Media import initiated: {result}")
                return result.get("file", result)
            else:
                logger.error(f"Wix Media import failed: {response.status_code} - {response.text}")
                return None
                
    except Exception as e:
        logger.error(f"Error importing image to Wix Media: {e}")
        return None

async def wait_until_wix_file_ready(
    api_key: str,
    site_id: str,
    file_id: str,
    timeout_sec: int = 90
) -> Optional[Dict]:
    """
    Attend que le fichier Wix soit vraiment prêt (operationStatus=READY).
    Wix traite les imports de façon asynchrone - 200 OK ne veut pas dire prêt!
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            for attempt in range(timeout_sec):
                response = await client.get(
                    f"https://www.wixapis.com/site-media/v1/files/{file_id}",
                    headers={
                        "Authorization": api_key,
                        "wix-site-id": site_id,
                        "Content-Type": "application/json"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    file_desc = data.get("file", data)
                    
                    status = file_desc.get("operationStatus")
                    logger.info(f"File {file_id} status: {status} (attempt {attempt + 1})")
                    
                    if status == "READY":
                        logger.info(f"File {file_id} is READY!")
                        return file_desc
                    
                    if status == "FAILED":
                        logger.error(f"Wix media processing FAILED for file {file_id}")
                        return None
                
                # Attendre avant le prochain check
                await asyncio.sleep(1.5)
            
            logger.error(f"Timeout: File {file_id} was never READY after {timeout_sec}s")
            return None
            
    except Exception as e:
        logger.error(f"Error waiting for Wix file ready: {e}")
        return None

def build_wix_image_uri(file_desc: Dict) -> str:
    """
    Construit la vraie Wix image URI au format:
    wix:image://v1/<mediaId>/<filename>#originWidth=<w>&originHeight=<h>
    
    IMPORTANT: Utilise les vraies dimensions de l'image depuis file_desc.media.image.image
    """
    file_id = file_desc.get("id", "")
    display_name = file_desc.get("displayName", "cover.jpg")
    
    # Récupérer les dimensions depuis media.image.image (structure Wix réelle)
    media = file_desc.get("media", {})
    image_wrapper = media.get("image", {}) if isinstance(media, dict) else {}
    image_data = image_wrapper.get("image", {}) if isinstance(image_wrapper, dict) else {}
    
    # Utiliser les vraies dimensions ou fallback
    width = image_data.get("width") or 1200
    height = image_data.get("height") or 630
    
    wix_uri = f"wix:image://v1/{file_id}/{display_name}#originWidth={width}&originHeight={height}"
    logger.info(f"Built Wix image URI: {wix_uri}")
    return wix_uri


def get_wix_image_object(file_desc: Dict) -> Dict:
    """
    Construit l'objet image complet pour le PATCH du draft.
    Format attendu par media.wixMedia.image
    """
    file_id = file_desc.get("id", "")
    display_name = file_desc.get("displayName", "cover.jpg")
    url = file_desc.get("url", "")
    
    # Récupérer les dimensions depuis media.image.image
    media = file_desc.get("media", {})
    image_wrapper = media.get("image", {}) if isinstance(media, dict) else {}
    image_data = image_wrapper.get("image", {}) if isinstance(image_wrapper, dict) else {}
    
    width = image_data.get("width") or 1200
    height = image_data.get("height") or 630
    
    # Construire la Wix URI
    wix_uri = f"wix:image://v1/{file_id}/{display_name}#originWidth={width}&originHeight={height}"
    
    return {
        "id": wix_uri,
        "url": url,
        "width": width,
        "height": height
    }

async def attach_wix_image_to_draft(
    api_key: str,
    site_id: str,
    draft_id: str,
    file_desc: Dict
) -> bool:
    """
    Attache l'image au draft avec le format minimal recommandé.
    
    Format: media.wixMedia.image.id = "wix:image://v1/..."
    
    Note: Ce format est accepté par l'API (200 OK) et les données sont
    correctement stockées, mais il y a un bug Wix de rendu qui empêche
    parfois l'affichage de la cover dans l'interface.
    """
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Construire la Wix URI
            wix_image_uri = build_wix_image_uri(file_desc)
            logger.info(f"Attaching image to draft {draft_id}")
            logger.info(f"Wix URI: {wix_image_uri}")
            
            # Format minimal recommandé: seulement l'ID
            payload = {
                "draftPost": {
                    "media": {
                        "wixMedia": {
                            "image": {
                                "id": wix_image_uri
                            }
                        }
                    }
                }
            }
            
            response = await client.patch(
                f"https://www.wixapis.com/blog/v3/draft-posts/{draft_id}",
                headers={
                    "Authorization": api_key,
                    "wix-site-id": site_id,
                    "Content-Type": "application/json"
                },
                json=payload
            )
            
            if response.status_code in [200, 204]:
                logger.info(f"Image attached successfully to draft {draft_id}")
                return True
            else:
                logger.error(f"Attach image failed: {response.status_code} - {response.text}")
                return False
                
    except Exception as e:
        logger.error(f"Error attaching image to draft: {e}")
        return False

async def get_wix_blog_categories(api_key: str, site_id: str) -> List[Dict]:
    """Récupère les catégories de blog Wix existantes"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.wixapis.com/blog/v3/categories",
                headers={
                    "Authorization": api_key,
                    "wix-site-id": site_id,
                    "Content-Type": "application/json"
                },
                timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("categories", [])
    except Exception as e:
        logger.error(f"Error getting Wix blog categories: {e}")
    return []

async def create_wix_draft_post(
    api_key: str,
    site_id: str,
    title: str,
    content: str,
    excerpt: str,
    image_data: Optional[Dict] = None,  # Dict retourné par import_image_and_get_wix_uri
    member_id: str = None
) -> Optional[Dict]:
    """
    Crée un brouillon de post sur Wix Blog v3 API.
    
    VERSION ROBUSTE 2026:
    - heroImage avec dimensions explicites
    - coverMedia en fallback
    - Image dans richContent
    """
    try:
        async with httpx.AsyncClient(timeout=80) as client:
            # Extraire l'URI depuis image_data
            hero_image_uri = None
            if image_data and isinstance(image_data, dict):
                hero_image_uri = image_data.get("wix_uri")
            elif image_data and isinstance(image_data, str):
                hero_image_uri = image_data
            
            # Convertir le HTML en Ricos AVEC l'image dans le corps
            rich_content = html_to_ricos(content, hero_image_uri)
            
            logger.info(f"Creating Wix draft post: {title}")
            
            draft_post = {
                "title": title,
                "excerpt": excerpt,
                "richContent": rich_content,
                "language": "fr"
            }
            
            # Ajouter memberId (obligatoire pour apps tierces)
            if member_id:
                draft_post["memberId"] = member_id
            
            # Ajouter heroImage + coverMedia avec dimensions explicites
            if image_data and isinstance(image_data, dict):
                static_url = image_data.get("static_url")
                wix_uri = image_data.get("wix_uri")
                width = image_data.get("width", 1200)
                height = image_data.get("height", 630)
                
                logger.info(f"Adding heroImage + coverMedia with dimensions {width}x{height}")
                
                # heroImage principal avec dimensions
                draft_post["heroImage"] = {
                    "id": wix_uri,
                    "url": static_url,
                    "width": width,
                    "height": height,
                    "altText": f"{title} - Luxura Distribution Québec"
                }
                
                # coverMedia en fallback (recommandé par forum Wix)
                draft_post["coverMedia"] = {
                    "type": "IMAGE",
                    "image": {
                        "id": wix_uri,
                        "width": width,
                        "height": height,
                        "altText": f"{title} - Luxura"
                    }
                }
            elif hero_image_uri:
                # Fallback simple si seulement l'URI string est fournie
                draft_post["heroImage"] = {
                    "id": hero_image_uri,
                    "altText": f"{title} - Luxura"
                }
            
            payload = {"draftPost": draft_post}
            
            response = await client.post(
                "https://www.wixapis.com/blog/v3/draft-posts",
                headers={
                    "Authorization": api_key,
                    "wix-site-id": site_id,
                    "Content-Type": "application/json"
                },
                json=payload
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                draft_id = result.get('draftPost', {}).get('id')
                logger.info(f"✅ Wix draft created with heroImage + coverMedia: {draft_id}")
                return result
            else:
                logger.error(f"Wix draft creation failed: {response.status_code} - {response.text}")
                return None
                
    except Exception as e:
        logger.error(f"Error creating Wix draft: {e}")
        return None

async def publish_wix_draft(api_key: str, site_id: str, draft_id: str) -> bool:
    """Publie un brouillon de post Wix"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://www.wixapis.com/blog/v3/draft-posts/{draft_id}/publish",
                headers={
                    "Authorization": api_key,
                    "wix-site-id": site_id,
                    "Content-Type": "application/json"
                },
                timeout=30
            )
            return response.status_code in [200, 201]
    except Exception as e:
        logger.error(f"Error publishing Wix draft: {e}")
        return False

def html_to_ricos(html_content: str, hero_image_uri: str = None) -> Dict:
    """
    Convertit le HTML en format Ricos (Wix rich content format).
    
    Si hero_image_uri est fourni, l'image est insérée comme PREMIER élément
    du contenu (contourne le bug heroImage de Wix).
    """
    import re
    import uuid
    
    nodes = []
    
    # NOUVEAU: Insérer l'image comme premier élément du corps
    if hero_image_uri:
        image_node = {
            "type": "IMAGE",
            "id": str(uuid.uuid4()),
            "imageData": {
                "containerData": {
                    "width": {"size": "CONTENT"},
                    "alignment": "CENTER"
                },
                "image": {
                    "src": {
                        "id": hero_image_uri
                    },
                    "width": 1200,
                    "height": 630
                },
                "altText": "Extensions capillaires Luxura Distribution"
            }
        }
        nodes.append(image_node)
    
    # Nettoyer le HTML
    content = html_content.strip()
    
    # Parser les balises principales
    # H1
    for match in re.finditer(r'<h1[^>]*>(.*?)</h1>', content, re.DOTALL):
        nodes.append({
            "type": "HEADING",
            "headingData": {"level": 1},
            "nodes": [{"type": "TEXT", "textData": {"text": match.group(1).strip()}}]
        })
    
    # H2
    for match in re.finditer(r'<h2[^>]*>(.*?)</h2>', content, re.DOTALL):
        nodes.append({
            "type": "HEADING",
            "headingData": {"level": 2},
            "nodes": [{"type": "TEXT", "textData": {"text": match.group(1).strip()}}]
        })
    
    # H3
    for match in re.finditer(r'<h3[^>]*>(.*?)</h3>', content, re.DOTALL):
        nodes.append({
            "type": "HEADING", 
            "headingData": {"level": 3},
            "nodes": [{"type": "TEXT", "textData": {"text": match.group(1).strip()}}]
        })
    
    # Paragraphes
    for match in re.finditer(r'<p[^>]*>(.*?)</p>', content, re.DOTALL):
        text = re.sub(r'<[^>]+>', '', match.group(1)).strip()
        if text:
            nodes.append({
                "type": "PARAGRAPH",
                "nodes": [{"type": "TEXT", "textData": {"text": text}}]
            })
    
    # Listes
    for ul_match in re.finditer(r'<ul[^>]*>(.*?)</ul>', content, re.DOTALL):
        list_items = []
        for li_match in re.finditer(r'<li[^>]*>(.*?)</li>', ul_match.group(1), re.DOTALL):
            text = re.sub(r'<[^>]+>', '', li_match.group(1)).strip()
            list_items.append({
                "type": "LIST_ITEM",
                "nodes": [{"type": "PARAGRAPH", "nodes": [{"type": "TEXT", "textData": {"text": text}}]}]
            })
        if list_items:
            nodes.append({
                "type": "BULLETED_LIST",
                "nodes": list_items
            })
    
    # Si aucun node (sauf image), créer un paragraphe avec le contenu brut
    text_nodes = [n for n in nodes if n.get("type") != "IMAGE"]
    if not text_nodes:
        clean_text = re.sub(r'<[^>]+>', '\n', content).strip()
        for para in clean_text.split('\n\n'):
            if para.strip():
                nodes.append({
                    "type": "PARAGRAPH",
                    "nodes": [{"type": "TEXT", "textData": {"text": para.strip()}}]
                })
    
    return {
        "nodes": nodes,
        "metadata": {
            "version": 1,
            "createdTimestamp": datetime.now(timezone.utc).isoformat(),
            "updatedTimestamp": datetime.now(timezone.utc).isoformat()
        }
    }

# =====================================================
# FACEBOOK PUBLISHING
# =====================================================

def html_to_plain_text(html_content: str) -> str:
    """Convertit le HTML en texte brut pour Facebook"""
    import re
    # Remplacer les balises de titre par des lignes
    text = re.sub(r'<h[1-6][^>]*>(.*?)</h[1-6]>', r'\n\n📌 \1\n', html_content)
    # Remplacer les listes
    text = re.sub(r'<li[^>]*>(.*?)</li>', r'• \1\n', text)
    # Remplacer les paragraphes
    text = re.sub(r'<p[^>]*>(.*?)</p>', r'\1\n\n', text)
    # Supprimer toutes les autres balises
    text = re.sub(r'<[^>]+>', '', text)
    # Nettoyer les espaces multiples
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

async def publish_to_facebook_page(
    fb_access_token: str,
    fb_page_id: str,
    title: str,
    content: str,
    image_url: str = None,
    link: str = None
) -> Optional[Dict]:
    """
    Publie un article sur la page Facebook Luxura Distribution.
    
    Args:
        fb_access_token: Token d'accès de la page Facebook
        fb_page_id: ID de la page Facebook
        title: Titre du post
        content: Contenu HTML (sera converti en texte)
        image_url: URL de l'image (optionnel)
        link: Lien vers l'article complet (optionnel)
    
    Returns:
        Dict avec l'ID du post Facebook si succès, None sinon
    """
    try:
        # Convertir HTML en texte pour Facebook
        plain_text = html_to_plain_text(content)
        
        # Créer le message avec le titre
        message = f"✨ {title}\n\n{plain_text[:1500]}"  # Facebook limite à ~2000 caractères
        
        if link:
            message += f"\n\n🔗 Lire l'article complet: {link}"
        
        message += "\n\n#LuxuraDistribution #ExtensionsCheveux #Québec #Montréal #HairExtensions"
        
        async with httpx.AsyncClient() as client:
            # Si on a une image, on publie un post avec photo
            if image_url:
                response = await client.post(
                    f"https://graph.facebook.com/v19.0/{fb_page_id}/photos",
                    data={
                        "url": image_url,
                        "caption": message,
                        "access_token": fb_access_token
                    },
                    timeout=60
                )
            else:
                # Sinon, on publie un post texte simple
                response = await client.post(
                    f"https://graph.facebook.com/v19.0/{fb_page_id}/feed",
                    data={
                        "message": message,
                        "access_token": fb_access_token
                    },
                    timeout=30
                )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Facebook post published: {result.get('id') or result.get('post_id')}")
                return result
            else:
                logger.error(f"Facebook publish failed: {response.status_code} - {response.text}")
                return None
                
    except Exception as e:
        logger.error(f"Error publishing to Facebook: {e}")
        return None

# =====================================================
# GÉNÉRATION DE BLOG AVEC OPENAI
# =====================================================

async def generate_blog_with_ai(
    topic_data: Dict,
    openai_key: str,
    existing_titles: List[str] = None
) -> Optional[Dict]:
    """Génère un article de blog SEO optimisé avec OpenAI GPT-4"""
    try:
        import openai
        
        client = openai.AsyncOpenAI(api_key=openai_key)
        
        topic = topic_data["topic"]
        category = topic_data["category"]
        keywords = topic_data["keywords"]
        focus_product = topic_data.get("focus_product")
        
        # System message optimisé SEO Québec
        system_message = f"""Tu es un expert SEO francophone spécialisé dans les extensions capillaires au Québec.
Tu écris pour Luxura Distribution, le leader des extensions cheveux haut de gamme au Canada.

STYLE:
- Professionnel mais accessible
- Informatif et engageant
- Français québécois naturel
- SEO optimisé avec mots-clés intégrés naturellement

PRODUITS LUXURA:
- Genius Weft Vivian: Trame ultra-fine 0.78mm révolutionnaire, découpable, couture invisible
- Halo Everly: Fil invisible ajustable, volume instantané, aucune fixation permanente
- Tape Aurora: Bande adhésive médicale, pose sandwich, réutilisable 3-4 fois
- I-Tip Eleanor: Kératine italienne, fusion mèche par mèche, invisible

LOCALISATION: Québec, Montréal, Canada
LANGUE: Français québécois UNIQUEMENT"""

        product_mention = f"\nMentionne particulièrement le produit: {focus_product}" if focus_product else ""
        
        prompt = f"""Écris un article de blog SEO complet sur le sujet suivant:

SUJET: {topic}
CATÉGORIE: {category}
MOTS-CLÉS À INTÉGRER: {', '.join(keywords)}
{product_mention}

STRUCTURE IMPORTANTE:
1. Introduction engageante (100-150 mots) - SANS TITRE H1 car Wix l'affiche automatiquement
2. Section 1 avec H2 + contenu détaillé
3. Section 2 avec H2 + contenu détaillé
4. Section 3 avec H2 + liste à puces des avantages
5. Conclusion avec appel à l'action Luxura Distribution

CONSIGNES CRITIQUES:
- 800-1200 mots total
- NE PAS inclure de balise <h1> dans le contenu - Wix affiche le titre automatiquement
- Commencer directement par un paragraphe <p> d'introduction
- Intégrer chaque mot-clé 2-3 fois naturellement
- Utiliser des balises HTML: <h2>, <h3>, <p>, <ul>, <li>, <strong>
- Mentionner Luxura Distribution comme expert
- Inclure des statistiques ou faits si pertinent
- Ton professionnel mais chaleureux

FORMAT JSON STRICT:
{{
  "title": "Titre SEO optimisé (affiché par Wix automatiquement)",
  "excerpt": "Résumé accrocheur de 150 caractères max",
  "content": "Contenu HTML SANS h1 - commencer par <p>introduction</p>",
  "meta_description": "Description meta de 155 caractères max",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"]
}}"""

        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=3000
        )
        
        response_text = response.choices[0].message.content.strip()
        
        # Nettoyer les balises markdown
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
                return None
        
        # Ajouter l'image et les métadonnées
        blog_data["image"] = get_blog_image_by_category(category)
        blog_data["category"] = category
        blog_data["keywords"] = keywords
        blog_data["focus_product"] = focus_product
        
        return blog_data
        
    except Exception as e:
        logger.error(f"Error generating blog with OpenAI: {e}")
        return None

# =====================================================
# GÉNÉRATION AUTOMATIQUE 2x PAR JOUR
# =====================================================

async def generate_daily_blogs(
    db,
    openai_key: str,
    wix_api_key: str = None,
    wix_site_id: str = None,
    publish_to_wix: bool = True,
    count: int = 2,
    fb_access_token: str = None,
    fb_page_id: str = None,
    publish_to_facebook: bool = False
) -> List[Dict]:
    """Génère automatiquement les blogs quotidiens avec OpenAI"""
    results = []
    
    # Récupérer le member ID pour Wix si on veut publier
    wix_member_id = None
    if publish_to_wix and wix_api_key and wix_site_id:
        wix_member_id = await get_wix_member_id(wix_api_key, wix_site_id)
        if not wix_member_id:
            logger.warning("Could not get Wix member ID - will try publishing without it")
    
    # Récupérer les titres existants pour éviter les doublons
    existing_posts = await db.blog_posts.find({}, {"title": 1}).to_list(1000)
    existing_titles = [p.get("title", "").lower() for p in existing_posts]
    
    # Sélectionner des sujets non couverts
    available_topics = [
        t for t in BLOG_TOPICS_EXTENDED 
        if t["topic"].lower() not in existing_titles
    ]
    
    # Si tous les sujets sont couverts, réutiliser avec rotation
    if len(available_topics) < count:
        # Ajouter des variations aux sujets existants
        available_topics = BLOG_TOPICS_EXTENDED.copy()
        random.shuffle(available_topics)
    
    # Sélectionner les sujets pour aujourd'hui (diversifier les catégories)
    categories_used = []
    selected_topics = []
    
    for topic in available_topics:
        if len(selected_topics) >= count:
            break
        if topic["category"] not in categories_used or len(categories_used) >= 4:
            selected_topics.append(topic)
            categories_used.append(topic["category"])
    
    # Générer chaque blog
    for topic_data in selected_topics:
        blog_data = await generate_blog_with_ai(topic_data, openai_key, existing_titles)
        
        if not blog_data:
            continue
        
        # Créer l'entrée dans la base locale
        post_id = f"auto-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:4]}"
        
        blog_post = {
            "id": post_id,
            "title": blog_data.get("title", topic_data["topic"]),
            "excerpt": blog_data.get("excerpt", ""),
            "content": blog_data.get("content", ""),
            "meta_description": blog_data.get("meta_description", ""),
            "tags": blog_data.get("tags", topic_data["keywords"]),
            "image": blog_data.get("image"),
            "category": topic_data["category"],
            "author": "Luxura Distribution",
            "created_at": datetime.now(timezone.utc),
            "auto_generated": True,
            "published_to_wix": False,
            "published_to_facebook": False
        }
        
        await db.blog_posts.insert_one(blog_post)
        
        # ============================================
        # PUBLIER SUR WIX (flux AMÉLIORÉ 2026)
        # NOUVEAU: heroImage inclus directement à la création du draft
        # ============================================
        if publish_to_wix and wix_api_key and wix_site_id:
            # ÉTAPE 1: Importer l'image ET obtenir les données Wix
            image_data = None
            image_url = blog_post.get("image")
            
            if image_url:
                logger.info(f"Step 1: Importing image and getting Wix URI...")
                image_data = await import_image_and_get_wix_uri(
                    api_key=wix_api_key,
                    site_id=wix_site_id,
                    image_url=image_url,
                    file_name=f"luxura-cover-{uuid.uuid4().hex[:8]}.jpg"
                )
                
                if image_data:
                    logger.info(f"✅ Image ready: {image_data.get('static_url', '')}")
                else:
                    logger.warning("⚠️ Image import failed, proceeding without cover")
            
            # ÉTAPE 2: Créer le brouillon AVEC image
            logger.info(f"Step 2: Creating draft...")
            wix_result = await create_wix_draft_post(
                api_key=wix_api_key,
                site_id=wix_site_id,
                title=blog_post["title"],
                content=blog_post["content"],
                excerpt=blog_post["excerpt"],
                image_data=image_data,  # Passer le dict complet
                member_id=wix_member_id
            )
            
            if wix_result:
                draft_id = wix_result.get("draftPost", {}).get("id")
                
                if draft_id:
                    # ÉTAPE 3: Publier le brouillon
                    logger.info(f"Step 3: Publishing draft {draft_id}")
                    published = await publish_wix_draft(wix_api_key, wix_site_id, draft_id)
                    if published:
                        logger.info(f"✅ Blog published successfully to Wix!")
                        await db.blog_posts.update_one(
                            {"id": post_id},
                            {"$set": {"published_to_wix": True, "wix_post_id": draft_id}}
                        )
                        blog_post["published_to_wix"] = True
                    else:
                        logger.error(f"❌ Failed to publish draft {draft_id}")
            else:
                logger.error("❌ Failed to create Wix draft")
        
        # Publier sur Facebook si configuré
        if publish_to_facebook and fb_access_token and fb_page_id:
            fb_result = await publish_to_facebook_page(
                fb_access_token=fb_access_token,
                fb_page_id=fb_page_id,
                title=blog_post["title"],
                content=blog_post["content"],
                image_url=blog_post["image"],
                link=None  # Ajouter le lien vers l'article Wix si disponible
            )
            
            if fb_result:
                fb_post_id = fb_result.get("id") or fb_result.get("post_id")
                await db.blog_posts.update_one(
                    {"id": post_id},
                    {"$set": {"published_to_facebook": True, "facebook_post_id": fb_post_id}}
                )
                blog_post["published_to_facebook"] = True
        
        # Nettoyer pour la réponse
        blog_post.pop("_id", None)
        if isinstance(blog_post.get("created_at"), datetime):
            blog_post["created_at"] = blog_post["created_at"].isoformat()
        
        results.append(blog_post)
        existing_titles.append(blog_post["title"].lower())
    
    return results
