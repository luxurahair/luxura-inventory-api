# =====================================================
# BLOG AUTOMATION SYSTEM - Luxura Distribution
# Génération automatique + Publication Wix + Images DALL-E
# =====================================================

import os
import random
import uuid
import httpx
import asyncio
import json
import smtplib
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from datetime import datetime, timezone
from typing import Optional, List, Dict, Tuple
import logging

logger = logging.getLogger(__name__)

# Import du module de génération d'images
try:
    from image_generation import (
        generate_blog_image_with_dalle,
        generate_and_upload_blog_images,
        upload_image_bytes_to_wix,
        get_fallback_unsplash_image
    )
    DALLE_AVAILABLE = True
except ImportError:
    logger.warning("Image generation module not available, using Unsplash fallback")
    DALLE_AVAILABLE = False

# =====================================================
# EMAIL CONFIGURATION
# =====================================================

LUXURA_EMAIL = os.getenv("LUXURA_EMAIL", "info@luxuradistribution.com")
LUXURA_APP_PASSWORD = os.getenv("LUXURA_APP_PASSWORD")


async def send_blog_images_email(blogs: List[Dict], recipient_email: str = None):
    """
    Envoie un email avec les images des blogs générés.
    
    Args:
        blogs: Liste des blogs générés (avec 'title', 'image', 'wix_image_url')
        recipient_email: Email de destination (par défaut LUXURA_EMAIL)
    """
    if not LUXURA_APP_PASSWORD:
        logger.warning("LUXURA_APP_PASSWORD non configuré, email non envoyé")
        return False
    
    recipient = recipient_email or LUXURA_EMAIL
    
    try:
        # Créer le message
        msg = MIMEMultipart('related')
        msg['Subject'] = f"📸 Images Blog Luxura - {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        msg['From'] = LUXURA_EMAIL
        msg['To'] = recipient
        
        # Corps HTML avec les images
        html_content = """
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; padding: 20px; }
                .blog-card { margin-bottom: 30px; border: 1px solid #ddd; padding: 15px; border-radius: 8px; }
                .blog-title { color: #333; font-size: 18px; margin-bottom: 10px; }
                .blog-image { max-width: 600px; width: 100%; border-radius: 4px; }
                .image-urls { font-size: 12px; color: #666; margin-top: 10px; }
                a { color: #C9A66B; }
            </style>
        </head>
        <body>
            <h1>🌟 Blogs Luxura Générés</h1>
            <p>Voici les images des blogs générés automatiquement :</p>
        """
        
        for i, blog in enumerate(blogs):
            title = blog.get('title', 'Sans titre')
            unsplash_url = blog.get('image', '')
            wix_url = blog.get('wix_image_url', '')
            
            html_content += f"""
            <div class="blog-card">
                <h2 class="blog-title">{i+1}. {title}</h2>
                <p><strong>Image Unsplash :</strong></p>
                <img src="{unsplash_url}" class="blog-image" alt="{title}">
                <div class="image-urls">
                    <p>🔗 <strong>Unsplash:</strong> <a href="{unsplash_url}">{unsplash_url[:80]}...</a></p>
                    <p>📁 <strong>Wix Media:</strong> <a href="{wix_url}">{wix_url[:80]}...</a></p>
                </div>
            </div>
            """
        
        html_content += """
            <hr>
            <p style="color: #666; font-size: 12px;">
                Généré automatiquement par Luxura Blog Automation<br>
                Pour ajouter l'image de couverture manuellement sur Wix :<br>
                Dashboard → Blog → Article → Settings → Featured Image
            </p>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(html_content, 'html'))
        
        # Envoyer via Gmail SMTP
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(LUXURA_EMAIL, LUXURA_APP_PASSWORD)
            server.send_message(msg)
        
        logger.info(f"✅ Email envoyé à {recipient} avec {len(blogs)} images")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur envoi email: {e}")
        return False

# FORMAT OPEN GRAPH: 1200x630 px (ratio 1.91:1) pour Wix Blog Cover
# =============================================================================
# IMAGES LUXURA - UNIQUEMENT CHEVEUX LONGS, LUXUEUX ET VOLUMINEUX
# Images représentant le résultat des extensions capillaires professionnelles
# =============================================================================
UNSPLASH_IMAGES = {
    "halo": [
        # Femmes avec cheveux longs luxueux - idéal pour Halo extensions
        "https://images.unsplash.com/photo-1580618672591-eb180b1a973f?w=1200&h=630&fit=crop",  # Cheveux longs brillants
        "https://images.unsplash.com/photo-1519735777090-ec97162dc266?w=1200&h=630&fit=crop",  # Blonde cheveux longs fluides
        "https://images.unsplash.com/photo-1502823403499-6ccfcf4fb453?w=1200&h=630&fit=crop",  # Cheveux ondulés luxueux
        "https://images.unsplash.com/photo-1605980776566-0486c3ac7617?w=1200&h=630&fit=crop",  # Cheveux extra longs brillants
        "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=1200&h=630&fit=crop",  # Cheveux soyeux volume
        "https://images.unsplash.com/photo-1519699047748-de8e457a634e?w=1200&h=630&fit=crop",  # Blonde cheveux parfaits
        "https://images.unsplash.com/photo-1596178060810-72660fc43bd1?w=1200&h=630&fit=crop",  # Longs cheveux wavy
    ],
    "genius": [
        # Cheveux longs parfaits - résultat Genius Weft
        "https://images.unsplash.com/photo-1595959183082-7b570b7e1dfa?w=1200&h=630&fit=crop",  # Cheveux ultra longs lisses
        "https://images.unsplash.com/photo-1605980776566-0486c3ac7617?w=1200&h=630&fit=crop",  # Volume cheveux longs
        "https://images.unsplash.com/photo-1502823403499-6ccfcf4fb453?w=1200&h=630&fit=crop",  # Ondulations parfaites longues
        "https://images.unsplash.com/photo-1519735777090-ec97162dc266?w=1200&h=630&fit=crop",  # Cheveux blonds longs
        "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=1200&h=630&fit=crop",  # Cheveux soyeux
        "https://images.unsplash.com/photo-1596178060810-72660fc43bd1?w=1200&h=630&fit=crop",  # Cheveux longs naturels
        "https://images.unsplash.com/photo-1580618672591-eb180b1a973f?w=1200&h=630&fit=crop",  # Longs cheveux brillants
    ],
    "tape": [
        # Extensions Tape - résultat cheveux longs naturels
        "https://images.unsplash.com/photo-1605980776566-0486c3ac7617?w=1200&h=630&fit=crop",  # Cheveux extra longs
        "https://images.unsplash.com/photo-1502823403499-6ccfcf4fb453?w=1200&h=630&fit=crop",  # Cheveux ondulés glamour
        "https://images.unsplash.com/photo-1595959183082-7b570b7e1dfa?w=1200&h=630&fit=crop",  # Cheveux lisses luxueux
        "https://images.unsplash.com/photo-1519735777090-ec97162dc266?w=1200&h=630&fit=crop",  # Cheveux longs blonds
        "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=1200&h=630&fit=crop",  # Volume soyeux
        "https://images.unsplash.com/photo-1596178060810-72660fc43bd1?w=1200&h=630&fit=crop",  # Cheveux naturels longs
        "https://images.unsplash.com/photo-1580618672591-eb180b1a973f?w=1200&h=630&fit=crop",  # Résultat brillant
    ],
    "itip": [
        # I-Tip - cheveux longs mèche par mèche
        "https://images.unsplash.com/photo-1595959183082-7b570b7e1dfa?w=1200&h=630&fit=crop",  # Cheveux ultra longs
        "https://images.unsplash.com/photo-1605980776566-0486c3ac7617?w=1200&h=630&fit=crop",  # Volume luxueux
        "https://images.unsplash.com/photo-1519735777090-ec97162dc266?w=1200&h=630&fit=crop",  # Blond parfait
        "https://images.unsplash.com/photo-1502823403499-6ccfcf4fb453?w=1200&h=630&fit=crop",  # Ondulations longues
        "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=1200&h=630&fit=crop",  # Cheveux soyeux longs
        "https://images.unsplash.com/photo-1596178060810-72660fc43bd1?w=1200&h=630&fit=crop",  # Résultat naturel
        "https://images.unsplash.com/photo-1580618672591-eb180b1a973f?w=1200&h=630&fit=crop",  # Cheveux brillants
    ],
    "entretien": [
        # Entretien - beaux cheveux longs bien entretenus
        "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=1200&h=630&fit=crop",  # Cheveux soyeux parfaits
        "https://images.unsplash.com/photo-1502823403499-6ccfcf4fb453?w=1200&h=630&fit=crop",  # Cheveux brillants
        "https://images.unsplash.com/photo-1605980776566-0486c3ac7617?w=1200&h=630&fit=crop",  # Cheveux longs sains
        "https://images.unsplash.com/photo-1595959183082-7b570b7e1dfa?w=1200&h=630&fit=crop",  # Cheveux luxueux
        "https://images.unsplash.com/photo-1519735777090-ec97162dc266?w=1200&h=630&fit=crop",  # Blond entretenu
        "https://images.unsplash.com/photo-1596178060810-72660fc43bd1?w=1200&h=630&fit=crop",  # Cheveux naturels longs
        "https://images.unsplash.com/photo-1580618672591-eb180b1a973f?w=1200&h=630&fit=crop",  # Résultat soins
    ],
    "tendances": [
        # Tendances - looks avec cheveux longs
        "https://images.unsplash.com/photo-1605980776566-0486c3ac7617?w=1200&h=630&fit=crop",  # Tendance cheveux longs
        "https://images.unsplash.com/photo-1502823403499-6ccfcf4fb453?w=1200&h=630&fit=crop",  # Ondulations tendance
        "https://images.unsplash.com/photo-1595959183082-7b570b7e1dfa?w=1200&h=630&fit=crop",  # Style cheveux longs
        "https://images.unsplash.com/photo-1519735777090-ec97162dc266?w=1200&h=630&fit=crop",  # Look blonde
        "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=1200&h=630&fit=crop",  # Tendance volume
        "https://images.unsplash.com/photo-1596178060810-72660fc43bd1?w=1200&h=630&fit=crop",  # Style naturel long
        "https://images.unsplash.com/photo-1580618672591-eb180b1a973f?w=1200&h=630&fit=crop",  # Cheveux glamour
    ],
    "salon": [
        # Salon - résultats cheveux longs après pose
        "https://images.unsplash.com/photo-1605980776566-0486c3ac7617?w=1200&h=630&fit=crop",  # Résultat salon luxe
        "https://images.unsplash.com/photo-1595959183082-7b570b7e1dfa?w=1200&h=630&fit=crop",  # Cheveux parfaits
        "https://images.unsplash.com/photo-1502823403499-6ccfcf4fb453?w=1200&h=630&fit=crop",  # Finition salon
        "https://images.unsplash.com/photo-1519735777090-ec97162dc266?w=1200&h=630&fit=crop",  # Cliente satisfaite
        "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=1200&h=630&fit=crop",  # Résultat professionnel
        "https://images.unsplash.com/photo-1580618672591-eb180b1a973f?w=1200&h=630&fit=crop",  # Transformation salon
    ],
    "formation": [
        # Formation - résultats professionnels
        "https://images.unsplash.com/photo-1605980776566-0486c3ac7617?w=1200&h=630&fit=crop",  # Résultat formation
        "https://images.unsplash.com/photo-1595959183082-7b570b7e1dfa?w=1200&h=630&fit=crop",  # Technique pro
        "https://images.unsplash.com/photo-1502823403499-6ccfcf4fb453?w=1200&h=630&fit=crop",  # Finition experte
        "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=1200&h=630&fit=crop",  # Cheveux parfaits
        "https://images.unsplash.com/photo-1580618672591-eb180b1a973f?w=1200&h=630&fit=crop",  # Résultat master
    ],
    "general": [
        # Général - beaux cheveux longs pour tout article
        "https://images.unsplash.com/photo-1605980776566-0486c3ac7617?w=1200&h=630&fit=crop",  # Cheveux extra longs luxueux
        "https://images.unsplash.com/photo-1595959183082-7b570b7e1dfa?w=1200&h=630&fit=crop",  # Cheveux lisses parfaits
        "https://images.unsplash.com/photo-1502823403499-6ccfcf4fb453?w=1200&h=630&fit=crop",  # Ondulations glamour
        "https://images.unsplash.com/photo-1519735777090-ec97162dc266?w=1200&h=630&fit=crop",  # Blonde cheveux longs
        "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=1200&h=630&fit=crop",  # Cheveux soyeux volume
        "https://images.unsplash.com/photo-1596178060810-72660fc43bd1?w=1200&h=630&fit=crop",  # Cheveux naturels longs
        "https://images.unsplash.com/photo-1580618672591-eb180b1a973f?w=1200&h=630&fit=crop",  # Cheveux brillants longs
        "https://images.unsplash.com/photo-1519699047748-de8e457a634e?w=1200&h=630&fit=crop",  # Blond luxueux
        "https://images.unsplash.com/photo-1517841905240-472988babdf9?w=1200&h=630&fit=crop",  # Cheveux longs naturels
        "https://images.unsplash.com/photo-1529626455594-4ff0802cfb7e?w=1200&h=630&fit=crop",  # Modèle cheveux longs
    ]
}

# =====================================================
# SUJETS DE BLOG - Focus Halo, Genius, Tape, I-Tip
# SEO optimisé Québec avec durée 12+ mois
# =====================================================

BLOG_TOPICS_EXTENDED = [
    # === HALO EXTENSIONS ===
    {
        "topic": "Extensions Halo : Volume instantané garanti 12 mois et plus au Québec",
        "category": "halo",
        "keywords": ["extensions halo Québec", "rallonges volume Montréal", "fil invisible cheveux", "extensions sans colle Canada"],
        "focus_product": "Halo Everly"
    },
    {
        "topic": "Halo vs Clip-in : Pourquoi le fil invisible conquiert les salons du Québec",
        "category": "halo", 
        "keywords": ["halo vs clip-in Québec", "extensions fil invisible Montréal", "rallonges capillaires comparatif"],
        "focus_product": "Halo Everly"
    },
    {
        "topic": "Comment porter des extensions Halo : Guide complet salon Montréal",
        "category": "halo",
        "keywords": ["tutoriel halo extensions", "porter extensions Québec", "look naturel rallonges"],
        "focus_product": "Halo Everly"
    },
    {
        "topic": "Extensions Halo pour cheveux fins : Solution professionnelle Québec",
        "category": "halo",
        "keywords": ["cheveux fins solution Québec", "halo volume Montréal", "extensions légères Canada"],
        "focus_product": "Halo Everly"
    },
    {
        "topic": "Acheter extensions Halo Québec : Guide complet prix et qualité",
        "category": "halo",
        "keywords": ["acheter extensions Québec", "prix halo Montréal", "rallonges qualité Canada"],
        "focus_product": "Halo Everly"
    },
    
    # === GENIUS WEFT ===
    {
        "topic": "Genius Weft Québec : Trame invisible 0.78mm qui dure 12 mois et plus",
        "category": "genius",
        "keywords": ["genius weft Québec", "trame invisible Montréal", "extensions professionnelles Canada"],
        "focus_product": "Genius Vivian"
    },
    {
        "topic": "Salons Québec : Pourquoi adopter les extensions Genius Weft",
        "category": "genius",
        "keywords": ["salon extensions Montréal", "genius weft professionnel", "fournisseur extensions Québec"],
        "focus_product": "Genius Vivian"
    },
    {
        "topic": "Installation Genius Weft : Formation professionnelle Québec",
        "category": "genius",
        "keywords": ["formation extensions Québec", "technique couture invisible", "apprendre genius weft"],
        "focus_product": "Genius Vivian"
    },
    {
        "topic": "Genius Weft vs Tape-in : Comparatif extensions salon Québec",
        "category": "genius",
        "keywords": ["genius vs tape Québec", "comparatif extensions Montréal", "meilleures extensions Canada"],
        "focus_product": "Genius Vivian"
    },
    
    # === TAPE-IN / BANDE ADHÉSIVE ===
    {
        "topic": "Extensions Tape-in Québec : Pose professionnelle garantie 12 mois et plus",
        "category": "tape",
        "keywords": ["tape-in extensions Québec", "bande adhésive Montréal", "rallonges sandwich Canada"],
        "focus_product": "Tape Aurora"
    },
    {
        "topic": "Durée extensions Tape-in : Plus de 12 mois avec bon entretien Québec",
        "category": "tape",
        "keywords": ["durée tape-in Québec", "entretien tape Montréal", "extensions longue durée Canada"],
        "focus_product": "Tape Aurora"
    },
    {
        "topic": "Tape-in vs Genius Weft : Comparatif extensions salon Montréal",
        "category": "tape",
        "keywords": ["tape vs genius Québec", "meilleures extensions salon", "comparatif rallonges"],
        "focus_product": "Tape Aurora"
    },
    {
        "topic": "Retrait extensions Tape-in : Guide professionnel Québec",
        "category": "tape",
        "keywords": ["retrait tape Québec", "repositionner extensions Montréal", "entretien tape-in Canada"],
        "focus_product": "Tape Aurora"
    },
    {
        "topic": "Acheter extensions Tape-in Québec : Prix et qualité professionnelle",
        "category": "tape",
        "keywords": ["acheter tape-in Québec", "prix extensions Montréal", "tape-in professionnel Canada"],
        "focus_product": "Tape Aurora"
    },
    
    # === I-TIP / KÉRATINE ===
    {
        "topic": "Extensions I-Tip Kératine Québec : Résultat naturel garanti 12 mois et plus",
        "category": "itip",
        "keywords": ["i-tip extensions Québec", "kératine cheveux Montréal", "mèche par mèche Canada"],
        "focus_product": "I-Tip Eleanor"
    },
    {
        "topic": "I-Tip vs Tape-in Québec : Quelle méthode pour un look naturel",
        "category": "itip",
        "keywords": ["i-tip vs tape Québec", "extensions naturelles Montréal", "kératine vs adhésive Canada"],
        "focus_product": "I-Tip Eleanor"
    },
    {
        "topic": "Formation I-Tip Québec : Maîtriser la fusion kératine professionnelle",
        "category": "itip",
        "keywords": ["formation i-tip Québec", "technique kératine Montréal", "apprendre extensions Canada"],
        "focus_product": "I-Tip Eleanor"
    },
    {
        "topic": "Entretien I-Tip : Prolonger la durée de vie au-delà de 12 mois au Québec",
        "category": "itip",
        "keywords": ["entretien i-tip Québec", "durée extensions kératine", "soins extensions Montréal"],
        "focus_product": "I-Tip Eleanor"
    },
    {
        "topic": "Extensions I-Tip blondes : Conseils entretien couleurs claires Québec",
        "category": "itip",
        "keywords": ["extensions blondes Québec", "entretien blonde Montréal", "i-tip couleurs claires"],
        "focus_product": "I-Tip Eleanor"
    },
    
    # === SUJETS GÉNÉRAUX SEO ===
    {
        "topic": "Tendances extensions cheveux 2025 Québec : Balayage, ombré et couleurs",
        "category": "tendances",
        "keywords": ["tendances extensions 2025 Québec", "couleurs cheveux Montréal", "balayage extensions Canada"],
        "focus_product": None
    },
    {
        "topic": "Entretenir extensions cheveux : Guide professionnel Québec 12 mois et plus",
        "category": "entretien",
        "keywords": ["entretien extensions Québec", "soins extensions Montréal", "durée vie extensions Canada"],
        "focus_product": None
    },
    {
        "topic": "Devenir partenaire Luxura : Programme salon extensions Québec",
        "category": "general",
        "keywords": ["partenaire salon Québec", "distributeur extensions Montréal", "grossiste cheveux Canada"],
        "focus_product": None
    },
    {
        "topic": "Extensions cheveux naturel Remy : Guide qualité Québec",
        "category": "general",
        "keywords": ["extensions remy Québec", "cheveux naturels Montréal", "qualité extensions Canada"],
        "focus_product": None
    },
    {
        "topic": "Meilleur salon extensions Montréal : Comment choisir",
        "category": "general",
        "keywords": ["meilleur salon Montréal", "extensions professionnelles Québec", "salon beauté Canada"],
        "focus_product": None
    },
    {
        "topic": "Prix extensions cheveux Québec : Guide complet 2025",
        "category": "general",
        "keywords": ["prix extensions Québec", "coût rallonges Montréal", "tarif extensions Canada"],
        "focus_product": None
    },
]

# Historique des images utilisées pour éviter les répétitions
_used_images = set()

def get_blog_image_by_category(category: str) -> str:
    """
    Retourne une image libre de droits selon la catégorie.
    Évite de répéter les mêmes images en gardant un historique.
    """
    global _used_images
    
    images = UNSPLASH_IMAGES.get(category, UNSPLASH_IMAGES["general"])
    
    # Filtrer les images déjà utilisées
    available = [img for img in images if img not in _used_images]
    
    # Si toutes utilisées, réinitialiser l'historique
    if not available:
        _used_images.clear()
        available = images
    
    # Choisir une image au hasard
    selected = random.choice(available)
    _used_images.add(selected)
    
    return selected

# =====================================================
# WIX VELO INTEGRATION (Contourne le bug heroImage)
# =====================================================

async def publish_blog_via_velo(
    title: str,
    excerpt: str,
    content: str,
    image_url: str,
    member_id: str = None
) -> Optional[Dict]:
    """
    Publie un blog via Wix Velo HTTP Function (plus fiable que REST API).
    Endpoint: https://www.luxuradistribution.com/_functions/createBlog
    """
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            payload = {
                "title": title,
                "excerpt": excerpt,
                "content": content,
                "imageUrl": image_url,
                "memberId": member_id
            }
            
            logger.info(f"📤 Publishing via Velo: {title[:50]}...")
            
            response = await client.post(
                "https://www.luxuradistribution.com/_functions/createBlog",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    logger.info(f"✅ Blog published via Velo! Draft ID: {result.get('draftId')}")
                    return result
                else:
                    logger.error(f"❌ Velo error: {result.get('error')}")
                    return None
            else:
                logger.error(f"❌ Velo HTTP error: {response.status_code} - {response.text}")
                return None
                
    except Exception as e:
        logger.error(f"❌ Error calling Velo: {e}")
        return None


# =====================================================
# WIX BLOG INTEGRATION (REST API - Fallback)
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

async def import_image_with_retry(
    api_key: str,
    site_id: str,
    category: str,
    max_retries: int = 3
) -> Optional[Dict]:
    """
    Importe une image avec retry automatique.
    Si une image échoue, essaie avec une autre image de la même catégorie.
    """
    tried_images = set()
    
    for attempt in range(max_retries):
        # Sélectionner une image pas encore essayée
        image_url = get_blog_image_by_category(category)
        
        # Éviter les doublons
        while image_url in tried_images and len(tried_images) < len(UNSPLASH_IMAGES.get(category, UNSPLASH_IMAGES["general"])):
            image_url = get_blog_image_by_category(category)
        
        tried_images.add(image_url)
        
        logger.info(f"📷 Import image attempt {attempt + 1}/{max_retries}: {image_url[:50]}...")
        
        result = await import_image_and_get_wix_uri(
            api_key=api_key,
            site_id=site_id,
            image_url=image_url,
            file_name=f"luxura-cover-{uuid.uuid4().hex[:8]}.jpg"
        )
        
        if result and result.get("file_id"):
            logger.info(f"✅ Image imported successfully on attempt {attempt + 1}")
            result["source_url"] = image_url  # Garder l'URL source
            return result
        
        logger.warning(f"⚠️ Image import failed, trying another image...")
    
    logger.error(f"❌ All {max_retries} image import attempts failed")
    return None


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

            # Format wix:image:// 
            wix_uri = f"wix:image://v1/{file_id}/{display_name}#originWidth={width}&originHeight={height}"
            
            # Format le plus fiable pour heroImage (forum Wix 2025-2026)
            # Le file_id contient déjà ~mv2.jpg dans son nom
            static_url_mv2 = f"https://static.wixstatic.com/media/{file_id}"
            
            # Format avec dimensions explicites (évite w_NaN / h_NaN)
            static_url_full = f"https://static.wixstatic.com/media/{file_id}/v1/fill/w_{width},h_{height},al_c,q_90/{display_name}"
            
            logger.info(f"✅ Image ready - URL: {static_url_mv2}")
            logger.info(f"   Dimensions: {width}x{height}")
            
            return {
                "wix_uri": wix_uri,
                "static_url": static_url_mv2,      # Utilise celui-ci pour heroImage.id
                "static_url_full": static_url_full,
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
    cover_image_data: Optional[Dict] = None,  # Image de couverture pour le feed
    content_image_data: Optional[Dict] = None,  # 2ème image à insérer dans le contenu
    member_id: str = None
) -> Optional[Dict]:
    """
    Crée un brouillon de post sur Wix Blog v3 API.
    
    VERSION 2026 avec DALL-E:
    - cover_image_data: Image de couverture (s'affiche sur le feed/cards)
    - content_image_data: 2ème image différente insérée au milieu de l'article
    - displayed: True pour forcer l'affichage de la cover
    """
    try:
        async with httpx.AsyncClient(timeout=80) as client:
            # URLs statiques pour les images dans le contenu
            cover_static_url = cover_image_data.get("static_url") if cover_image_data else None
            content_static_url = content_image_data.get("static_url") if content_image_data else None
            
            # Convertir le HTML en Ricos avec les 2 images
            rich_content = html_to_ricos(
                content, 
                None,  # hero_image_uri deprecated
                cover_static_url,  # Image en haut du contenu
                content_static_url  # 2ème image au milieu
            )
            
            logger.info(f"Creating Wix draft post: {title}")
            if cover_static_url:
                logger.info(f"  - Cover image: {cover_static_url[:50]}...")
            if content_static_url:
                logger.info(f"  - Content image: {content_static_url[:50]}...")
            
            draft_post = {
                "title": title,
                "excerpt": excerpt,
                "richContent": rich_content,
                "language": "fr"
            }
            
            # Ajouter memberId (obligatoire pour apps tierces)
            if member_id:
                draft_post["memberId"] = member_id
            
            # FORMAT CORRIGÉ POUR IMAGE DE COUVERTURE
            if cover_image_data and isinstance(cover_image_data, dict):
                file_id = cover_image_data.get("file_id")
                width = cover_image_data.get("width", 1200)
                height = cover_image_data.get("height", 630)
                
                if file_id:
                    logger.info(f"Adding cover image with displayed:True - file_id: {file_id[:50]}...")
                    draft_post["media"] = {
                        "wixMedia": {
                            "image": {
                                "id": file_id,
                                "width": width,
                                "height": height
                            }
                        },
                        "displayed": True,
                        "custom": True
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
                draft_media = result.get('draftPost', {}).get('media', {})
                displayed = draft_media.get('displayed', False)
                logger.info(f"✅ Wix draft created: {draft_id} | displayed={displayed}")
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

# URL du logo Luxura Distribution
LUXURA_LOGO_URL = "https://static.wixstatic.com/media/f1b961_e8c5f3e0f0ff4c899c5cf99e2d0c8c4c~mv2.png"
LUXURA_WEBSITE = "https://www.luxuradistribution.com"

def html_to_ricos(html_content: str, hero_image_uri: str = None, static_image_url: str = None, content_image_url: str = None, add_logo: bool = True) -> Dict:
    """
    Convertit le HTML en format Ricos (Wix rich content format).
    
    Args:
        html_content: Le contenu HTML à convertir
        hero_image_uri: URI Wix de l'image principale (deprecated)
        static_image_url: URL statique de l'image de couverture (premier élément)
        content_image_url: URL de la 2ème image à insérer au milieu du contenu
        add_logo: Ajouter le logo Luxura à la fin du contenu
    """
    import re
    import uuid
    
    nodes = []
    
    # Insérer l'image de couverture comme premier élément
    image_src = static_image_url or hero_image_uri
    if image_src:
        image_node = {
            "type": "IMAGE",  # MAJUSCULE requis par Wix API
            "imageData": {
                "image": {
                    "src": {
                        "url": image_src
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
    text_nodes = [n for n in nodes if n.get("type") != "IMAGE" and n.get("type") != "image"]
    if not text_nodes:
        clean_text = re.sub(r'<[^>]+>', '\n', content).strip()
        for para in clean_text.split('\n\n'):
            if para.strip():
                nodes.append({
                    "type": "PARAGRAPH",
                    "nodes": [{"type": "TEXT", "textData": {"text": para.strip()}}]
                })
    
    # Insérer la 2ème image (content_image) AU MILIEU du contenu
    if content_image_url and len(nodes) > 3:
        # Trouver le point d'insertion (environ au milieu)
        mid_point = len(nodes) // 2
        
        content_image_node = {
            "type": "IMAGE",  # MAJUSCULE requis par Wix API
            "imageData": {
                "image": {
                    "src": {
                        "url": content_image_url
                    },
                    "width": 1200,
                    "height": 630
                },
                "altText": "Extensions capillaires professionnelles"
            }
        }
        
        # Insérer au milieu
        nodes.insert(mid_point, content_image_node)
    
    # Ajouter la signature Luxura à la fin
    if add_logo:
        # Séparateur
        nodes.append({
            "type": "DIVIDER",
            "dividerData": {
                "lineStyle": "DOUBLE",
                "width": "MEDIUM"
            }
        })
        
        # Signature Luxura
        nodes.append({
            "type": "PARAGRAPH",
            "nodes": [{
                "type": "TEXT", 
                "textData": {
                    "text": "📍 Luxura Distribution - Votre expert en extensions capillaires au Québec",
                    "decorations": [{"type": "BOLD"}]
                }
            }]
        })
        
        # Hashtags
        nodes.append({
            "type": "PARAGRAPH",
            "nodes": [{
                "type": "TEXT", 
                "textData": {
                    "text": "#LuxuraDistribution #ExtensionsCheveux #RallongesQuébec #BeautéMontréal #SalonProfessionnel"
                }
            }]
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

PRODUITS LUXURA (DURÉES DE VIE IMPORTANTES):
- Genius Weft Vivian: Trame ultra-fine 0.78mm révolutionnaire, découpable, couture invisible. Durée: 12+ mois avec bon entretien.
- Halo Everly: Fil invisible ajustable, volume instantané, aucune fixation permanente. Durée: 12+ mois avec bon entretien.
- Tape Aurora: Bande adhésive médicale, pose sandwich, réutilisable 3-4 fois. Durée: 12+ mois avec bon entretien.
- I-Tip Eleanor: Kératine italienne, fusion mèche par mèche, invisible. Durée: 12+ mois avec bon entretien.

⚠️ DURÉE DE VIE CRITIQUE:
- Toutes les extensions Luxura durent PLUS DE 12 MOIS avec des soins appropriés
- NE JAMAIS écrire "6 mois" - C'est TOUJOURS "12 mois et plus" ou "plus d'un an"
- Les couleurs BLONDES nécessitent plus de soins car le procédé de décoloration fragilise les cheveux
- Recommander des produits sans sulfate et sans alcool
- Éviter la chaleur excessive

MOTS-CLÉS SEO GOOGLE ADS À INTÉGRER:
- extensions cheveux Québec / Montréal / Canada
- rallonges capillaires professionnelles
- pose extensions salon Québec
- extensions naturelles Remy hair
- rallonges cheveux prix Québec
- extensions tape-in / genius weft / i-tip / halo
- salon extensions Montréal
- acheter extensions cheveux Canada
- extensions cheveux longue durée
- rallonges capillaires haut de gamme
- extension cheveux femme Québec
- beauté cheveux extensions

LOCALISATION: Québec, Montréal, Laval, Longueuil, Sherbrooke, Trois-Rivières, Canada
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
6. OBLIGATOIRE: Section "Découvrez nos collections" avec liens

LIENS CATÉGORIES À INCLURE (OBLIGATOIRE dans la conclusion):
<p><strong>Découvrez nos collections Luxura :</strong></p>
<ul>
<li><a href="https://www.luxuradistribution.com/genius-weft">Extensions Genius Weft</a></li>
<li><a href="https://www.luxuradistribution.com/halo-extensions">Extensions Halo</a></li>
<li><a href="https://www.luxuradistribution.com/tape-in-extensions">Extensions Tape-in</a></li>
<li><a href="https://www.luxuradistribution.com/i-tip-extensions">Extensions I-Tip</a></li>
<li><a href="https://www.luxuradistribution.com/boutique">Tous nos produits</a></li>
</ul>

CONSIGNES CRITIQUES:
- 800-1200 mots total
- NE PAS inclure de balise <h1> dans le contenu - Wix affiche le titre automatiquement
- Commencer directement par un paragraphe <p> d'introduction
- Intégrer chaque mot-clé 2-3 fois naturellement
- Utiliser des balises HTML: <h2>, <h3>, <p>, <ul>, <li>, <strong>, <a>
- Mentionner Luxura Distribution comme expert
- Inclure des statistiques ou faits si pertinent
- Ton professionnel mais chaleureux
- INCLURE les liens vers les catégories dans la conclusion

FORMAT JSON STRICT:
{{
  "title": "Titre SEO optimisé (affiché par Wix automatiquement)",
  "excerpt": "Résumé accrocheur de 150 caractères max",
  "content": "Contenu HTML SANS h1 - commencer par <p>introduction</p>... INCLURE liens catégories",
  "meta_description": "Description meta de 155 caractères max",
  "tags": ["extensions cheveux Québec", "rallonges capillaires", "salon beauté Montréal", "tag-spécifique-au-sujet", "Luxura Distribution"],
  "hashtags": "#LuxuraDistribution #ExtensionsCheveux #RallongesQuébec #BeautéMontréal #CheveuxLongs"
}}

RÈGLES TAGS SEO (TRÈS IMPORTANT):
- TOUJOURS inclure "extensions cheveux Québec" ou "rallonges capillaires Québec"
- TOUJOURS inclure le nom du produit (Genius Vivian, Halo Everly, Tape Aurora, I-Tip Eleanor)
- Ajouter des mots-clés locaux: Montréal, Québec, Canada
- Ajouter des mots-clés beauté: salon, coiffure, cheveux longs, volume
- Minimum 5 tags, maximum 8 tags par article

HASHTAGS LUXURA (pour réseaux sociaux):
- #LuxuraDistribution
- #ExtensionsCheveux
- #RallongesQuébec
- #ExtensionsProfessionnelles
- #BeautéMontréal
- #CheveuxLongs
- #SalonBeauté
- #GeniusWeft / #HaloExtensions / #TapeIn / #ITipExtensions (selon le sujet)"""

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
    publish_to_facebook: bool = False,
    send_email: bool = True  # NOUVEAU: Envoyer email avec images
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
        # PUBLIER SUR WIX AVEC IMAGES DALL-E UNIQUES
        # ============================================
        if publish_to_wix:
            category = topic_data.get("category", "general")
            blog_title = blog_post['title']
            
            logger.info(f"🚀 Publishing to Wix: {blog_title[:50]}...")
            
            if wix_api_key and wix_site_id:
                cover_image_data = None
                content_image_data = None
                
                # Option 1: Essayer DALL-E pour des images uniques
                if DALLE_AVAILABLE:
                    try:
                        logger.info(f"🎨 Generating unique images with DALL-E for: {category}")
                        
                        # Générer image de couverture avec DALL-E
                        cover_bytes = await generate_blog_image_with_dalle(category, "cover")
                        if cover_bytes:
                            cover_image_data = await upload_image_bytes_to_wix(
                                api_key=wix_api_key,
                                site_id=wix_site_id,
                                image_bytes=cover_bytes,
                                file_name=f"cover-dalle-{uuid.uuid4().hex[:8]}.png"
                            )
                        
                        # Générer 2ème image différente pour le contenu
                        content_bytes = await generate_blog_image_with_dalle(category, "content")
                        if content_bytes:
                            content_image_data = await upload_image_bytes_to_wix(
                                api_key=wix_api_key,
                                site_id=wix_site_id,
                                image_bytes=content_bytes,
                                file_name=f"content-dalle-{uuid.uuid4().hex[:8]}.png"
                            )
                        
                        if cover_image_data:
                            logger.info(f"✅ DALL-E cover image generated and uploaded")
                        if content_image_data:
                            logger.info(f"✅ DALL-E content image generated and uploaded")
                            
                    except Exception as e:
                        logger.error(f"⚠️ DALL-E generation failed: {e}, falling back to Unsplash")
                
                # Option 2: Fallback vers Unsplash si DALL-E échoue
                if not cover_image_data:
                    logger.info(f"📷 Using Unsplash fallback for cover image")
                    cover_image_data = await import_image_with_retry(
                        api_key=wix_api_key,
                        site_id=wix_site_id,
                        category=category,
                        max_retries=3
                    )
                
                # Fallback pour l'image de contenu aussi
                if not content_image_data:
                    logger.info(f"📷 Using Unsplash fallback for content image")
                    content_image_data = await import_image_with_retry(
                        api_key=wix_api_key,
                        site_id=wix_site_id,
                        category=category,
                        max_retries=2
                    )
                
                # Mettre à jour l'image principale dans blog_post
                if cover_image_data:
                    blog_post["image"] = cover_image_data.get("static_url", blog_post.get("image"))
                
                # Créer le draft Wix avec les 2 images
                wix_result = await create_wix_draft_post(
                    api_key=wix_api_key,
                    site_id=wix_site_id,
                    title=blog_post["title"],
                    content=blog_post["content"],
                    excerpt=blog_post["excerpt"],
                    cover_image_data=cover_image_data,
                    content_image_data=content_image_data,
                    member_id=wix_member_id
                )
                
                if wix_result:
                    draft_id = wix_result.get("draftPost", {}).get("id")
                    if draft_id:
                        published = await publish_wix_draft(wix_api_key, wix_site_id, draft_id)
                        if published:
                            logger.info(f"✅ Blog published successfully with 2 unique images!")
                            await db.blog_posts.update_one(
                                {"id": post_id},
                                {"$set": {"published_to_wix": True, "wix_post_id": draft_id}}
                            )
                            blog_post["published_to_wix"] = True
                            
                            # Ajouter les URLs des images pour l'email
                            if cover_image_data:
                                blog_post["wix_image_url"] = cover_image_data.get("static_url", "")
                            if content_image_data:
                                blog_post["wix_content_image_url"] = content_image_data.get("static_url", "")
                else:
                    logger.error(f"❌ Failed to create Wix draft")
        
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
    
    # Envoyer email avec les images après génération
    if results and send_email:
        await send_blog_images_email(results)
    
    return results
