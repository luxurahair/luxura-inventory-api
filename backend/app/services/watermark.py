"""
🏷️ WATERMARK LUXURA - Logo doré sur toutes les images
=====================================================
Ajoute le logo/texte "LUXURA" en watermark doré léger
sur toutes les images générées pour les posts Facebook.
"""

import os
import io
import logging
import httpx
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# Configuration du watermark
WATERMARK_CONFIG = {
    "text": "LUXURA",
    "position": "bottom-right",  # bottom-right, bottom-left, bottom-center
    "opacity": 0.4,  # 40% opacité (léger)
    "color_gold": (212, 175, 55),  # Or/Gold RGB
    "color_gold_light": (255, 215, 0),  # Gold plus clair
    "font_size_ratio": 0.06,  # 6% de la largeur de l'image
    "padding": 20,  # Pixels depuis le bord
}

# URL du logo Luxura (si disponible)
LOGO_URL = os.getenv("LUXURA_LOGO_URL", None)


async def download_image(url: str) -> Optional[bytes]:
    """Télécharge une image depuis une URL"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            if response.status_code == 200:
                return response.content
    except Exception as e:
        logger.error(f"Erreur téléchargement image: {e}")
    return None


def create_gold_text_watermark(
    image: Image.Image,
    text: str = "LUXURA",
    position: str = "bottom-right",
    opacity: float = 0.4
) -> Image.Image:
    """
    Crée un watermark texte doré sur l'image
    
    Args:
        image: Image PIL
        text: Texte du watermark
        position: Position (bottom-right, bottom-left, bottom-center)
        opacity: Opacité (0.0 à 1.0)
    
    Returns:
        Image avec watermark
    """
    # Convertir en RGBA si nécessaire
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    
    width, height = image.size
    
    # Calculer la taille de la police basée sur la largeur de l'image
    font_size = int(width * WATERMARK_CONFIG["font_size_ratio"])
    
    # Essayer de charger une police élégante, sinon utiliser la police par défaut
    try:
        # Essayer différentes polices système
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        ]
        font = None
        for path in font_paths:
            if os.path.exists(path):
                font = ImageFont.truetype(path, font_size)
                break
        if font is None:
            font = ImageFont.load_default()
            font_size = 40  # Taille fixe pour police par défaut
    except Exception:
        font = ImageFont.load_default()
    
    # Créer un calque transparent pour le watermark
    watermark_layer = Image.new('RGBA', image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(watermark_layer)
    
    # Calculer la taille du texte
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # Calculer la position
    padding = WATERMARK_CONFIG["padding"]
    
    if position == "bottom-right":
        x = width - text_width - padding
        y = height - text_height - padding
    elif position == "bottom-left":
        x = padding
        y = height - text_height - padding
    elif position == "bottom-center":
        x = (width - text_width) // 2
        y = height - text_height - padding
    else:
        x = width - text_width - padding
        y = height - text_height - padding
    
    # Couleur dorée avec opacité
    gold_color = WATERMARK_CONFIG["color_gold"]
    alpha = int(255 * opacity)
    
    # Dessiner une ombre légère d'abord (pour lisibilité)
    shadow_offset = 2
    draw.text(
        (x + shadow_offset, y + shadow_offset),
        text,
        font=font,
        fill=(0, 0, 0, int(alpha * 0.5))  # Ombre noire semi-transparente
    )
    
    # Dessiner le texte doré
    draw.text(
        (x, y),
        text,
        font=font,
        fill=(*gold_color, alpha)
    )
    
    # Fusionner le watermark avec l'image originale
    watermarked = Image.alpha_composite(image, watermark_layer)
    
    return watermarked


async def add_watermark_to_image_url(
    image_url: str,
    text: str = "LUXURA",
    position: str = "bottom-right",
    opacity: float = 0.4
) -> Optional[bytes]:
    """
    Télécharge une image, ajoute le watermark doré, et retourne les bytes
    
    Args:
        image_url: URL de l'image source
        text: Texte du watermark
        position: Position du watermark
        opacity: Opacité (0.0 à 1.0)
    
    Returns:
        Bytes de l'image avec watermark (JPEG)
    """
    logger.info(f"🏷️ Ajout watermark '{text}' sur image...")
    
    # Télécharger l'image
    image_bytes = await download_image(image_url)
    if not image_bytes:
        logger.error("Impossible de télécharger l'image")
        return None
    
    try:
        # Ouvrir l'image
        image = Image.open(io.BytesIO(image_bytes))
        
        # Ajouter le watermark
        watermarked = create_gold_text_watermark(
            image,
            text=text,
            position=position,
            opacity=opacity
        )
        
        # Convertir en RGB pour JPEG
        if watermarked.mode == 'RGBA':
            # Créer un fond blanc
            background = Image.new('RGB', watermarked.size, (255, 255, 255))
            background.paste(watermarked, mask=watermarked.split()[3])
            watermarked = background
        
        # Sauvegarder en bytes
        output = io.BytesIO()
        watermarked.save(output, format='JPEG', quality=95)
        output.seek(0)
        
        logger.info(f"✅ Watermark ajouté! Taille: {len(output.getvalue())} bytes")
        return output.getvalue()
        
    except Exception as e:
        logger.error(f"Erreur ajout watermark: {e}")
        return None


async def add_logo_watermark(
    image_url: str,
    logo_url: str = None
) -> Optional[bytes]:
    """
    Ajoute un logo en watermark sur l'image
    
    Args:
        image_url: URL de l'image source
        logo_url: URL du logo (optionnel, sinon utilise texte)
    
    Returns:
        Bytes de l'image avec watermark
    """
    # Si pas de logo URL, utiliser le watermark texte
    if not logo_url:
        return await add_watermark_to_image_url(image_url)
    
    logger.info(f"🏷️ Ajout logo watermark...")
    
    # Télécharger l'image et le logo
    image_bytes = await download_image(image_url)
    logo_bytes = await download_image(logo_url)
    
    if not image_bytes:
        logger.error("Impossible de télécharger l'image")
        return None
    
    try:
        image = Image.open(io.BytesIO(image_bytes))
        
        if logo_bytes:
            logo = Image.open(io.BytesIO(logo_bytes))
            
            # Redimensionner le logo (15% de la largeur de l'image)
            logo_width = int(image.width * 0.15)
            logo_ratio = logo_width / logo.width
            logo_height = int(logo.height * logo_ratio)
            logo = logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)
            
            # Convertir en RGBA
            if image.mode != 'RGBA':
                image = image.convert('RGBA')
            if logo.mode != 'RGBA':
                logo = logo.convert('RGBA')
            
            # Appliquer opacité au logo
            alpha = logo.split()[3]
            alpha = ImageEnhance.Brightness(alpha).enhance(0.4)  # 40% opacité
            logo.putalpha(alpha)
            
            # Position bottom-right
            padding = 20
            x = image.width - logo_width - padding
            y = image.height - logo_height - padding
            
            # Coller le logo
            image.paste(logo, (x, y), logo)
        else:
            # Fallback vers watermark texte
            image = create_gold_text_watermark(image)
        
        # Convertir en RGB pour JPEG
        if image.mode == 'RGBA':
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[3])
            image = background
        
        # Sauvegarder
        output = io.BytesIO()
        image.save(output, format='JPEG', quality=95)
        output.seek(0)
        
        return output.getvalue()
        
    except Exception as e:
        logger.error(f"Erreur ajout logo: {e}")
        return None


# Fonction simplifiée pour l'intégration
async def process_image_with_watermark(image_url: str) -> Optional[bytes]:
    """
    Fonction principale pour ajouter le watermark Luxura doré
    
    Args:
        image_url: URL de l'image
    
    Returns:
        Bytes de l'image avec watermark LUXURA doré
    """
    return await add_watermark_to_image_url(
        image_url,
        text="LUXURA",
        position="bottom-right",
        opacity=0.35  # 35% opacité - léger mais visible
    )
