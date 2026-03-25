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

UNSPLASH_IMAGES = {
    "halo": [
        "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=800",  # Femme cheveux longs
        "https://images.unsplash.com/photo-1580618672591-eb180b1a973f?w=800",  # Salon coiffure
        "https://images.unsplash.com/photo-1560066984-138dadb4c035?w=800",  # Cheveux brillants
        "https://images.unsplash.com/photo-1519699047748-de8e457a634e?w=800",  # Femme blonde
        "https://images.unsplash.com/photo-1605497788044-5a32c7078486?w=800",  # Cheveux wavy
    ],
    "genius": [
        "https://images.unsplash.com/photo-1522337094846-8a818192de1f?w=800",  # Cheveux parfaits
        "https://images.unsplash.com/photo-1487412720507-e7ab37603c6f?w=800",  # Femme professionnelle
        "https://images.unsplash.com/photo-1526047932273-341f2a7631f9?w=800",  # Salon luxe
        "https://images.unsplash.com/photo-1616683693504-3ea7e9ad6fec?w=800",  # Extensions visibles
        "https://images.unsplash.com/photo-1559599101-f09722fb4948?w=800",  # Coiffeuse travail
    ],
    "tape": [
        "https://images.unsplash.com/photo-1595476108010-b4d1f102b1b1?w=800",  # Pose extensions
        "https://images.unsplash.com/photo-1562322140-8baeececf3df?w=800",  # Salon coiffure
        "https://images.unsplash.com/photo-1560066984-138dadb4c035?w=800",  # Application
        "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=800",  # Résultat
        "https://images.unsplash.com/photo-1502823403499-6ccfcf4fb453?w=800",  # Outils salon
    ],
    "itip": [
        "https://images.unsplash.com/photo-1527799820374-dcf8d9d4a388?w=800",  # Détail cheveux
        "https://images.unsplash.com/photo-1559599101-f09722fb4948?w=800",  # Application pro
        "https://images.unsplash.com/photo-1580618672591-eb180b1a973f?w=800",  # Salon
        "https://images.unsplash.com/photo-1522337094846-8a818192de1f?w=800",  # Cheveux naturels
        "https://images.unsplash.com/photo-1492106087820-71f1a00d2b11?w=800",  # Portrait femme
    ],
    "entretien": [
        "https://images.unsplash.com/photo-1527799820374-dcf8d9d4a388?w=800",  # Brossage
        "https://images.unsplash.com/photo-1522337094846-8a818192de1f?w=800",  # Soins
        "https://images.unsplash.com/photo-1519699047748-de8e457a634e?w=800",  # Cheveux sains
        "https://images.unsplash.com/photo-1560066984-138dadb4c035?w=800",  # Brillance
        "https://images.unsplash.com/photo-1502823403499-6ccfcf4fb453?w=800",  # Produits
    ],
    "tendances": [
        "https://images.unsplash.com/photo-1605497788044-5a32c7078486?w=800",  # Style moderne
        "https://images.unsplash.com/photo-1519699047748-de8e457a634e?w=800",  # Blonde tendance
        "https://images.unsplash.com/photo-1487412720507-e7ab37603c6f?w=800",  # Look pro
        "https://images.unsplash.com/photo-1492106087820-71f1a00d2b11?w=800",  # Style 2025
        "https://images.unsplash.com/photo-1580618672591-eb180b1a973f?w=800",  # Salon tendance
    ],
    "general": [
        "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=800",
        "https://images.unsplash.com/photo-1560066984-138dadb4c035?w=800",
        "https://images.unsplash.com/photo-1519699047748-de8e457a634e?w=800",
        "https://images.unsplash.com/photo-1522337094846-8a818192de1f?w=800",
        "https://images.unsplash.com/photo-1487412720507-e7ab37603c6f?w=800",
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

async def import_image_to_wix_media(
    api_key: str,
    site_id: str,
    image_url: str,
    file_name: str = None
) -> Optional[Dict]:
    """
    Importe une image externe dans le Wix Media Manager.
    
    Args:
        api_key: Clé API Wix
        site_id: ID du site Wix
        image_url: URL de l'image à importer (Unsplash, OpenAI, etc.)
        file_name: Nom du fichier (optionnel)
    
    Returns:
        Dict avec les infos du média Wix importé, ou None si erreur
    """
    try:
        if not file_name:
            # Générer un nom de fichier unique
            file_name = f"blog-cover-{uuid.uuid4().hex[:8]}.jpg"
        
        async with httpx.AsyncClient() as client:
            # Étape 1: Importer l'image via l'API Media Manager
            payload = {
                "url": image_url,
                "displayName": file_name,
                "mediaType": "IMAGE",
                "mimeType": "image/jpeg"
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
                timeout=60  # Plus de temps pour l'import
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                logger.info(f"Wix Media import successful: {result}")
                return result.get("file", result)
            else:
                logger.error(f"Wix Media import failed: {response.status_code} - {response.text}")
                return None
                
    except Exception as e:
        logger.error(f"Error importing image to Wix Media: {e}")
        return None

async def get_wix_media_url(media_file: Dict) -> Optional[str]:
    """
    Extrait l'URL ou l'ID utilisable depuis un fichier média Wix.
    
    Args:
        media_file: Réponse de l'import Wix Media
    
    Returns:
        URL ou ID du média pour utilisation dans les posts
    """
    if not media_file:
        return None
    
    # Wix retourne différentes structures selon l'endpoint
    # On cherche l'ID ou l'URL du média
    media_id = media_file.get("id") or media_file.get("fileId")
    media_url = media_file.get("url") or media_file.get("fileUrl")
    
    # Pour heroImage, Wix attend souvent le format wix:image://v1/...
    if media_id:
        return media_id
    if media_url:
        return media_url
    
    return None

async def attach_wix_image_to_draft(
    api_key: str,
    site_id: str,
    draft_id: str,
    wix_file_id: str,
    wix_image_url: str = None
) -> bool:
    """
    Associe l'image Wix importée au draft blog via PATCH.
    IMPORTANT: Inclure width/height pour éviter le bug w_NaN,h_NaN de Wix.
    """
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            logger.info(f"Attaching image {wix_file_id} to draft {draft_id}")
            
            # Construire l'URL si non fournie
            if not wix_image_url:
                wix_image_url = f"https://static.wixstatic.com/media/{wix_file_id}"
            
            # Format avec dimensions explicites (OBLIGATOIRE pour éviter le bug w_NaN,h_NaN)
            image_object = {
                "id": wix_file_id,
                "url": wix_image_url,
                "width": 1200,
                "height": 800,
                "filename": f"{wix_file_id}"
            }
            
            # Format 1: coverMedia avec objet image complet incluant dimensions
            response = await client.patch(
                f"https://www.wixapis.com/blog/v3/draft-posts/{draft_id}",
                headers={
                    "Authorization": api_key,
                    "wix-site-id": site_id,
                    "Content-Type": "application/json"
                },
                json={
                    "draftPost": {
                        "coverMedia": {
                            "enabled": True,
                            "displayed": True,
                            "image": image_object
                        }
                    }
                }
            )
            
            if response.status_code in [200, 204]:
                logger.info(f"Image attached with coverMedia + dimensions: {draft_id}")
                return True
            else:
                logger.warning(f"coverMedia with dimensions failed: {response.status_code} - {response.text}")
            
            # Format 2: media.wixMedia avec objet image
            response2 = await client.patch(
                f"https://www.wixapis.com/blog/v3/draft-posts/{draft_id}",
                headers={
                    "Authorization": api_key,
                    "wix-site-id": site_id,
                    "Content-Type": "application/json"
                },
                json={
                    "draftPost": {
                        "media": {
                            "wixMedia": {
                                "image": image_object
                            },
                            "displayed": True
                        }
                    }
                }
            )
            
            if response2.status_code in [200, 204]:
                logger.info(f"Image attached with media.wixMedia + dimensions: {draft_id}")
                return True
            else:
                logger.warning(f"media.wixMedia with dimensions failed: {response2.status_code} - {response2.text}")
            
            # Format 3: heroImage simple avec URL
            response3 = await client.patch(
                f"https://www.wixapis.com/blog/v3/draft-posts/{draft_id}",
                headers={
                    "Authorization": api_key,
                    "wix-site-id": site_id,
                    "Content-Type": "application/json"
                },
                json={
                    "draftPost": {
                        "heroImage": image_object
                    }
                }
            )
            
            if response3.status_code in [200, 204]:
                logger.info(f"Image attached with heroImage object: {draft_id}")
                return True
            else:
                logger.error(f"All formats failed: {response3.status_code} - {response3.text}")
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
    member_id: str = None
) -> Optional[Dict]:
    """
    Crée un brouillon de post sur Wix Blog v3 API (SANS image).
    
    L'image doit être attachée séparément via attach_wix_image_to_draft()
    après l'import dans Wix Media.
    
    Returns:
        Dict avec draftPost si succès, None sinon
    """
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            # Convertir le contenu HTML en format Ricos (Wix rich content)
            rich_content = html_to_ricos(content)
            
            logger.info(f"Creating Wix draft post: {title}")
            
            payload = {
                "draftPost": {
                    "title": title,
                    "excerpt": excerpt,
                    "richContent": rich_content,
                    "language": "fr"
                }
            }
            
            # Ajouter memberId (obligatoire pour apps tierces)
            if member_id:
                payload["draftPost"]["memberId"] = member_id
            
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
                logger.info(f"Wix draft created successfully: {draft_id}")
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

def html_to_ricos(html_content: str) -> Dict:
    """Convertit le HTML en format Ricos (Wix rich content format)"""
    import re
    
    nodes = []
    
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
    
    # Si aucun node, créer un paragraphe avec le contenu brut
    if not nodes:
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

STRUCTURE:
1. Titre H1 accrocheur avec mot-clé principal
2. Introduction engageante (100-150 mots)
3. Section 1 avec H2 + contenu détaillé
4. Section 2 avec H2 + contenu détaillé
5. Section 3 avec H2 + liste à puces des avantages
6. Conclusion avec appel à l'action Luxura Distribution

CONSIGNES:
- 800-1200 mots total
- Intégrer chaque mot-clé 2-3 fois naturellement
- Utiliser des balises HTML: <h1>, <h2>, <p>, <ul>, <li>, <strong>
- Mentionner Luxura Distribution comme expert
- Inclure des statistiques ou faits si pertinent
- Ton professionnel mais chaleureux

FORMAT JSON STRICT:
{{
  "title": "Titre SEO optimisé",
  "excerpt": "Résumé accrocheur de 150 caractères max",
  "content": "Contenu HTML complet",
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
        # PUBLIER SUR WIX (flux correct en 4 étapes)
        # ============================================
        if publish_to_wix and wix_api_key and wix_site_id:
            # ÉTAPE 1: Créer le brouillon (sans image)
            wix_result = await create_wix_draft_post(
                api_key=wix_api_key,
                site_id=wix_site_id,
                title=blog_post["title"],
                content=blog_post["content"],
                excerpt=blog_post["excerpt"],
                member_id=wix_member_id
            )
            
            if wix_result:
                draft_id = wix_result.get("draftPost", {}).get("id")
                
                if draft_id:
                    # ÉTAPE 2: Importer l'image dans Wix Media
                    image_url = blog_post.get("image")
                    if image_url:
                        logger.info(f"Step 2: Importing image to Wix Media for draft {draft_id}")
                        imported = await import_image_to_wix_media(
                            api_key=wix_api_key,
                            site_id=wix_site_id,
                            image_url=image_url,
                            file_name=f"blog-{draft_id[:8]}-cover.jpg"
                        )
                        
                        if imported:
                            # Extraire l'ID et l'URL du fichier Wix
                            wix_file_id = imported.get("id") or imported.get("fileId")
                            wix_image_url = imported.get("url") or imported.get("fileUrl")
                            
                            if wix_file_id:
                                # ÉTAPE 3: Attacher l'image au brouillon via PATCH
                                logger.info(f"Step 3: Attaching image {wix_file_id} to draft")
                                await attach_wix_image_to_draft(
                                    api_key=wix_api_key,
                                    site_id=wix_site_id,
                                    draft_id=draft_id,
                                    wix_file_id=wix_file_id,
                                    wix_image_url=wix_image_url
                                )
                    
                    # ÉTAPE 4: Publier le brouillon
                    logger.info(f"Step 4: Publishing draft {draft_id}")
                    published = await publish_wix_draft(wix_api_key, wix_site_id, draft_id)
                    if published:
                        await db.blog_posts.update_one(
                            {"id": post_id},
                            {"$set": {"published_to_wix": True, "wix_post_id": draft_id}}
                        )
                        blog_post["published_to_wix"] = True
        
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
