# facebook_publisher.py
"""
Module de publication automatique sur Facebook
Pour Luxura Distribution - Extensions capillaires
"""

import os
import httpx
import logging
from typing import Optional, Dict, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

# Configuration Facebook
FB_PAGE_ACCESS_TOKEN = os.getenv("FB_PAGE_ACCESS_TOKEN")
FB_PAGE_ID = os.getenv("FB_PAGE_ID")
FB_GRAPH_API_URL = "https://graph.facebook.com/v19.0"


async def verify_facebook_token() -> Tuple[bool, str]:
    """
    Vérifie que le token Facebook est valide
    """
    if not FB_PAGE_ACCESS_TOKEN or not FB_PAGE_ID:
        return False, "FB_PAGE_ACCESS_TOKEN ou FB_PAGE_ID non configuré"
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{FB_GRAPH_API_URL}/me",
                params={"access_token": FB_PAGE_ACCESS_TOKEN}
            )
            
            if response.status_code == 200:
                data = response.json()
                page_name = data.get("name", "Unknown")
                return True, f"Token valide - Page: {page_name}"
            else:
                error = response.json().get("error", {}).get("message", "Erreur inconnue")
                return False, f"Token invalide: {error}"
                
    except Exception as e:
        return False, f"Erreur de connexion: {str(e)}"


async def publish_photo_to_facebook(
    image_url: str = None,
    image_bytes: bytes = None,
    caption: str = "",
) -> Dict:
    """
    Publie une photo avec légende sur la page Facebook
    
    Args:
        image_url: URL publique de l'image (option 1)
        image_bytes: Bytes de l'image (option 2)
        caption: Texte de la publication
        
    Returns:
        Dict avec success, post_id, post_url ou error
    """
    if not FB_PAGE_ACCESS_TOKEN or not FB_PAGE_ID:
        return {
            "success": False,
            "error": "FB_PAGE_ACCESS_TOKEN ou FB_PAGE_ID non configuré"
        }
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            
            if image_bytes:
                # Upload de l'image en bytes
                logger.info("📤 Upload de l'image sur Facebook...")
                
                files = {
                    "source": ("image.png", image_bytes, "image/png")
                }
                data = {
                    "caption": caption,
                    "access_token": FB_PAGE_ACCESS_TOKEN
                }
                
                response = await client.post(
                    f"{FB_GRAPH_API_URL}/{FB_PAGE_ID}/photos",
                    files=files,
                    data=data
                )
                
            elif image_url:
                # Publication via URL
                logger.info(f"📤 Publication via URL: {image_url[:50]}...")
                
                response = await client.post(
                    f"{FB_GRAPH_API_URL}/{FB_PAGE_ID}/photos",
                    data={
                        "url": image_url,
                        "caption": caption,
                        "access_token": FB_PAGE_ACCESS_TOKEN
                    }
                )
            else:
                return {
                    "success": False,
                    "error": "Aucune image fournie (image_url ou image_bytes requis)"
                }
            
            if response.status_code == 200:
                data = response.json()
                post_id = data.get("post_id") or data.get("id")
                
                logger.info(f"✅ Publication Facebook réussie! Post ID: {post_id}")
                
                return {
                    "success": True,
                    "post_id": post_id,
                    "post_url": f"https://www.facebook.com/{post_id}",
                    "published_at": datetime.now().isoformat()
                }
            else:
                error_data = response.json()
                error_msg = error_data.get("error", {}).get("message", "Erreur inconnue")
                logger.error(f"❌ Erreur Facebook: {error_msg}")
                
                return {
                    "success": False,
                    "error": error_msg,
                    "error_code": error_data.get("error", {}).get("code")
                }
                
    except Exception as e:
        logger.error(f"❌ Exception lors de la publication Facebook: {e}")
        return {
            "success": False,
            "error": str(e)
        }


async def publish_text_to_facebook(message: str) -> Dict:
    """
    Publie un texte simple (sans image) sur la page Facebook
    """
    if not FB_PAGE_ACCESS_TOKEN or not FB_PAGE_ID:
        return {
            "success": False,
            "error": "FB_PAGE_ACCESS_TOKEN ou FB_PAGE_ID non configuré"
        }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{FB_GRAPH_API_URL}/{FB_PAGE_ID}/feed",
                data={
                    "message": message,
                    "access_token": FB_PAGE_ACCESS_TOKEN
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                post_id = data.get("id")
                
                return {
                    "success": True,
                    "post_id": post_id,
                    "post_url": f"https://www.facebook.com/{post_id}",
                    "published_at": datetime.now().isoformat()
                }
            else:
                error_data = response.json()
                error_msg = error_data.get("error", {}).get("message", "Erreur inconnue")
                
                return {
                    "success": False,
                    "error": error_msg
                }
                
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


async def publish_wedding_promo(
    image_bytes: bytes,
    partners: list = None
) -> Dict:
    """
    Publie la promo mariage avec les partenaires
    """
    if partners is None:
        partners = [
            {"name": "Stephanie & Rebekka", "salon": "Salon Carouso"},
            {"name": "Cindy Fecteau", "salon": "CF Concept"}
        ]
    
    # Construire le texte de la publication
    partners_text = "\n".join([
        f"👑 𝐒𝐭𝐞𝐩𝐡𝐚𝐧𝐢𝐞 & 𝐑𝐞𝐛𝐞𝐤𝐤𝐚 — Salon Carouso",
        f"👑 𝐂𝐢𝐧𝐝𝐲 𝐅𝐞𝐜𝐭𝐞𝐚𝐮 — CF Concept"
    ])
    
    caption = f"""✨ VOTRE JOURNÉE DE RÊVE MÉRITE UNE CHEVELURE DE RÊVE ✨

Chères futures mariées du Québec,

Votre mariage approche et vous rêvez d'une chevelure longue, volumineuse et absolument parfaite pour le plus beau jour de votre vie? 💍

Chez 𝐋𝐮𝐱𝐮𝐫𝐚 𝐃𝐢𝐬𝐭𝐫𝐢𝐛𝐮𝐭𝐢𝐨𝐧, nous sommes fiers de collaborer avec des artistes coiffeuses exceptionnelles:

═══════════════════════════════

{partners_text}

═══════════════════════════════

𝗣𝗼𝘂𝗿𝗾𝘂𝗼𝗶 𝗰𝗵𝗼𝗶𝘀𝗶𝗿 𝗟𝘂𝘅𝘂𝗿𝗮 𝗽𝗼𝘂𝗿 𝘃𝗼𝘁𝗿𝗲 𝗺𝗮𝗿𝗶𝗮𝗴𝗲?

✨ Extensions 100% cheveux naturels Remy Hair
✨ Qualité haut de gamme importée
✨ Résultat naturel et invisible
✨ Longueur et volume spectaculaires
✨ Pose par des expertes certifiées
✨ Tenue parfaite toute la journée (et la nuit! 💃)

📅 𝐑𝐄́𝐒𝐄𝐑𝐕𝐄𝐙 𝐕𝐎𝐓𝐑𝐄 𝐏𝐋𝐀𝐂𝐄 𝐃𝐄̀𝐒 𝐌𝐀𝐈𝐍𝐓𝐄𝐍𝐀𝐍𝐓

Les dates de mariage 2025 et 2026 partent vite!

💌 Contactez votre salon partenaire préféré
ou écrivez-nous: info@luxuradistribution.com

Parce que chaque mariée mérite de se sentir absolument magnifique. 💫

#MariéeQuébec #Mariage2025 #Mariage2026 #ExtensionsCheveux #ChevelureDeRêve #FutureMariée #WeddingHair #LuxuraDistribution #SalonCarouso #CFConcept #BeauceQuébec"""
    
    return await publish_photo_to_facebook(
        image_bytes=image_bytes,
        caption=caption
    )
