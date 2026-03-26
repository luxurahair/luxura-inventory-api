# =====================================================
# IMAGE GENERATION MODULE - Luxura Distribution
# Génère des images uniques avec DALL-E pour les blogs
# =====================================================

import os
import base64
import uuid
import httpx
import logging
from typing import Optional, Dict, Tuple
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Clé API pour la génération d'images
EMERGENT_LLM_KEY = os.getenv("EMERGENT_LLM_KEY")

# Prompts de base pour différentes catégories de cheveux
IMAGE_PROMPTS = {
    "halo": {
        "cover": "Professional beauty photography of a glamorous woman with very long flowing {hair_color} hair extensions, volume and shine, soft studio lighting, elegant pose, hair salon quality result, high-end luxury feel, 1200x630 aspect ratio",
        "content": "Close-up detail shot of beautiful long {hair_color} hair with invisible halo wire extensions, showing natural blend, professional hair photography"
    },
    "genius": {
        "cover": "Stunning portrait of a confident woman with luxurious long {hair_color} hair extensions, weft hair technique result, professional salon finish, sophisticated lighting, premium quality",
        "content": "Professional demonstration of genius weft hair extensions on a model, showing the thin seamless weft technology, salon environment"
    },
    "tape": {
        "cover": "Beautiful woman with gorgeous long {hair_color} tape-in hair extensions, silky smooth texture, professional lighting, luxury hair salon result, elegant and natural look",
        "content": "Close-up of tape-in hair extension application, showing seamless adhesive band blending with natural hair, professional technique"
    },
    "itip": {
        "cover": "Elegant portrait of a woman with stunning long {hair_color} i-tip keratin hair extensions, individual strands perfectly blended, salon professional result",
        "content": "Detail shot of i-tip keratin fusion hair extensions showing individual bonded strands, professional application technique"
    },
    "entretien": {
        "cover": "Beautiful woman caring for her long luxurious {hair_color} hair extensions, healthy shiny hair, hair care routine, professional beauty shot",
        "content": "Hair care products for extensions displayed elegantly, brushes and treatments for maintaining long hair, professional product photography"
    },
    "tendances": {
        "cover": "Fashion-forward woman with trendy long {hair_color} hair extensions styled in latest 2025 hairstyle, editorial beauty photography, high fashion look",
        "content": "Collage of modern hair extension styles and trends, various lengths and textures, fashion-forward looks"
    },
    "salon": {
        "cover": "Luxurious modern hair salon interior with a client getting long {hair_color} hair extensions, professional stylists, elegant atmosphere",
        "content": "Professional hair stylist applying extensions to a client in a premium salon, showing expertise and care"
    },
    "formation": {
        "cover": "Professional hair extension training session, instructor demonstrating technique on mannequin with long {hair_color} hair, educational setting",
        "content": "Hands-on hair extension course, students learning application techniques, professional training environment"
    },
    "general": {
        "cover": "Stunning portrait of a beautiful woman with very long luxurious {hair_color} hair extensions, perfect waves, professional beauty photography, high-end look",
        "content": "Variety of beautiful long hair extension styles, showing different textures and lengths, professional hair photography"
    }
}

# Couleurs de cheveux pour varier les images
HAIR_COLORS = [
    "blonde",
    "brunette",
    "dark brown",
    "honey blonde",
    "caramel highlights",
    "auburn",
    "platinum blonde",
    "chocolate brown",
    "golden blonde",
    "ash brown",
    "balayage ombre",
    "rich chestnut"
]

# Index pour rotation des couleurs
_color_index = 0


def get_next_hair_color() -> str:
    """Retourne la prochaine couleur de cheveux pour varier les images."""
    global _color_index
    color = HAIR_COLORS[_color_index % len(HAIR_COLORS)]
    _color_index += 1
    return color


async def generate_blog_image_with_dalle(
    category: str,
    image_type: str = "cover",  # "cover" ou "content"
    custom_prompt: str = None
) -> Optional[bytes]:
    """
    Génère une image unique avec DALL-E pour un blog.
    
    Args:
        category: Catégorie du blog (halo, genius, tape, etc.)
        image_type: "cover" pour image de couverture, "content" pour image dans l'article
        custom_prompt: Prompt personnalisé optionnel
    
    Returns:
        bytes de l'image générée ou None si échec
    """
    if not EMERGENT_LLM_KEY:
        logger.error("EMERGENT_LLM_KEY not configured")
        return None
    
    try:
        from emergentintegrations.llm.openai.image_generation import OpenAIImageGeneration
        
        # Obtenir le prompt approprié
        hair_color = get_next_hair_color()
        
        if custom_prompt:
            prompt = custom_prompt.format(hair_color=hair_color)
        else:
            prompts = IMAGE_PROMPTS.get(category, IMAGE_PROMPTS["general"])
            prompt_template = prompts.get(image_type, prompts["cover"])
            prompt = prompt_template.format(hair_color=hair_color)
        
        # Ajouter des instructions de qualité
        prompt += ". Ultra realistic, professional photography, 4K quality, soft natural lighting, no text or watermarks"
        
        logger.info(f"🎨 Generating DALL-E image: {prompt[:80]}...")
        
        # Initialiser le générateur
        image_gen = OpenAIImageGeneration(api_key=EMERGENT_LLM_KEY)
        
        # Générer l'image
        images = await image_gen.generate_images(
            prompt=prompt,
            model="gpt-image-1",
            number_of_images=1
        )
        
        if images and len(images) > 0:
            logger.info(f"✅ DALL-E image generated successfully ({len(images[0])} bytes)")
            return images[0]
        else:
            logger.error("No image returned from DALL-E")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error generating DALL-E image: {e}")
        return None


async def generate_and_upload_blog_images(
    api_key: str,
    site_id: str,
    category: str,
    blog_title: str = ""
) -> Tuple[Optional[Dict], Optional[Dict]]:
    """
    Génère et upload les images de couverture ET de contenu pour un blog.
    
    Returns:
        Tuple (cover_image_data, content_image_data)
    """
    cover_data = None
    content_data = None
    
    # 1. Générer l'image de couverture
    logger.info(f"📸 Generating cover image for: {blog_title[:40]}...")
    cover_bytes = await generate_blog_image_with_dalle(category, "cover")
    
    if cover_bytes:
        cover_data = await upload_image_bytes_to_wix(
            api_key=api_key,
            site_id=site_id,
            image_bytes=cover_bytes,
            file_name=f"cover-{uuid.uuid4().hex[:8]}.png"
        )
    
    # 2. Générer l'image de contenu (différente)
    logger.info(f"📸 Generating content image for: {blog_title[:40]}...")
    content_bytes = await generate_blog_image_with_dalle(category, "content")
    
    if content_bytes:
        content_data = await upload_image_bytes_to_wix(
            api_key=api_key,
            site_id=site_id,
            image_bytes=content_bytes,
            file_name=f"content-{uuid.uuid4().hex[:8]}.png"
        )
    
    return cover_data, content_data


async def upload_image_bytes_to_wix(
    api_key: str,
    site_id: str,
    image_bytes: bytes,
    file_name: str
) -> Optional[Dict]:
    """
    Upload une image (bytes) vers Wix Media Manager.
    """
    try:
        # Convertir en base64 pour l'upload
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            # Étape 1: Obtenir l'URL d'upload
            logger.info(f"🔑 Getting upload URL for {file_name}...")
            
            upload_url_response = await client.post(
                "https://www.wixapis.com/site-media/v1/files/generate-upload-url",
                headers={
                    "Authorization": api_key,
                    "wix-site-id": site_id,
                    "Content-Type": "application/json"
                },
                json={
                    "mimeType": "image/png",
                    "fileName": file_name,
                    "filePath": f"/blog-generated/{file_name}"
                }
            )
            
            if upload_url_response.status_code != 200:
                logger.error(f"Failed to get upload URL: {upload_url_response.status_code}")
                return None
            
            upload_data = upload_url_response.json()
            upload_url = upload_data.get("uploadUrl")
            
            if not upload_url:
                logger.error("No upload URL returned")
                return None
            
            # Étape 2: Upload l'image
            logger.info(f"⬆️ Uploading image to Wix...")
            
            upload_response = await client.put(
                upload_url,
                content=image_bytes,
                headers={
                    "Content-Type": "image/png"
                }
            )
            
            if upload_response.status_code not in (200, 201):
                logger.error(f"Upload failed: {upload_response.status_code}")
                return None
            
            # Étape 3: Récupérer les infos du fichier
            file_id = upload_data.get("file", {}).get("id")
            
            if not file_id:
                # Essayer de récupérer depuis la réponse d'upload
                file_info = upload_response.json() if upload_response.text else {}
                file_id = file_info.get("file", {}).get("id")
            
            if file_id:
                # Attendre que le fichier soit prêt
                for _ in range(30):
                    check_response = await client.get(
                        f"https://www.wixapis.com/site-media/v1/files/{file_id}",
                        headers={
                            "Authorization": api_key,
                            "wix-site-id": site_id,
                        }
                    )
                    
                    if check_response.status_code == 200:
                        file_desc = check_response.json().get("file", {})
                        if file_desc.get("operationStatus") == "READY":
                            width = 1200
                            height = 630
                            
                            # Essayer de récupérer les vraies dimensions
                            media = file_desc.get("media", {})
                            if isinstance(media, dict):
                                image_wrapper = media.get("image", {})
                                if isinstance(image_wrapper, dict):
                                    image_info = image_wrapper.get("image", {})
                                    width = image_info.get("width", 1200)
                                    height = image_info.get("height", 630)
                            
                            static_url = f"https://static.wixstatic.com/media/{file_id}"
                            
                            logger.info(f"✅ Image uploaded to Wix: {static_url[:60]}...")
                            
                            return {
                                "file_id": file_id,
                                "static_url": static_url,
                                "width": width,
                                "height": height
                            }
                    
                    import asyncio
                    await asyncio.sleep(1)
            
            logger.error("File never became READY or no file_id")
            return None
            
    except Exception as e:
        logger.error(f"Error uploading image to Wix: {e}")
        return None


# Fallback vers Unsplash si DALL-E échoue
FALLBACK_UNSPLASH_IMAGES = {
    "general": [
        "https://images.unsplash.com/photo-1605980776566-0486c3ac7617?w=1200&h=630&fit=crop",
        "https://images.unsplash.com/photo-1595959183082-7b570b7e1dfa?w=1200&h=630&fit=crop",
        "https://images.unsplash.com/photo-1502823403499-6ccfcf4fb453?w=1200&h=630&fit=crop",
        "https://images.unsplash.com/photo-1519735777090-ec97162dc266?w=1200&h=630&fit=crop",
        "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=1200&h=630&fit=crop",
    ]
}

_fallback_index = 0

def get_fallback_unsplash_image() -> str:
    """Retourne une image Unsplash de fallback."""
    global _fallback_index
    images = FALLBACK_UNSPLASH_IMAGES["general"]
    image = images[_fallback_index % len(images)]
    _fallback_index += 1
    return image
