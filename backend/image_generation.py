# image_generation.py
# Version V4 - Utilise le brief généré par image_brief_generator.py
# Architecture propre: le brief décide QUOI montrer, ce module génère l'image

import os
import uuid
import httpx
import asyncio
import logging
import io
from typing import Optional, Dict, Tuple, List
from PIL import Image
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

EMERGENT_LLM_KEY = os.getenv("EMERGENT_LLM_KEY")

# Import du brief generator
from image_brief_generator import generate_image_brief

# Import du module logo overlay
from logo_overlay import get_luxura_logo, add_logo_to_image


def build_prompt_from_brief(brief: Dict, image_type: str = "cover") -> str:
    """Construit le prompt final à partir du brief visuel"""
    section = brief["cover"] if image_type == "cover" else brief["content"]
    
    return f"""
Professional luxury beauty photography for Luxura Distribution Quebec.

Scene: {section['scene']}

Style: {section['style']}
Focus: {section['focus']}
Hair rule: {brief.get('hair_length_rule', 'very long waist-length or longer hair')}

Technical:
- Ultra realistic 8K photography
- Soft warm cinematic lighting
- Horizontal 1200x630 for cover
- Photorealistic, high detail on hair texture

Avoid: {', '.join(section.get('avoid', []))}
No text. No watermark. No men. No short hair anywhere.
""".strip()


async def generate_blog_image_with_dalle(
    category: str,
    blog_title: str,
    blog_data: Dict = None,
    image_type: str = "cover",
    add_logo: bool = True
) -> Optional[bytes]:
    """Génère une image en utilisant le brief intelligent + ajoute le logo Luxura"""
    if not EMERGENT_LLM_KEY:
        logger.error("EMERGENT_LLM_KEY not configured")
        return None

    try:
        from emergentintegrations.llm.openai.image_generation import OpenAIImageGeneration

        if blog_data is None:
            blog_data = {"title": blog_title, "content": "", "category": category}

        # 1. Générer le brief visuel intelligent
        brief = generate_image_brief(blog_data)

        # 2. Construire le prompt à partir du brief
        prompt = build_prompt_from_brief(brief, image_type)

        logger.info(f"🎨 Generating [{image_type}] - Mode: {brief['visual_mode']} for: {blog_title[:50]}...")

        image_gen = OpenAIImageGeneration(api_key=EMERGENT_LLM_KEY)

        images = await image_gen.generate_images(
            prompt=prompt,
            model="gpt-image-1",
            number_of_images=1
        )

        if images and len(images) > 0:
            image_bytes = images[0]
            logger.info(f"✅ [{image_type}] Image generated ({len(image_bytes)} bytes)")
            
            # 3. Ajouter le logo Luxura si demandé
            if add_logo and brief.get("logo_overlay", True):
                logger.info(f"🏷️ Adding Luxura logo watermark (bottom-right, 15%)...")
                image_bytes = await add_logo_watermark(image_bytes)
            
            return image_bytes

        logger.error("No image returned from DALL-E")
        return None

    except Exception as e:
        logger.error(f"❌ Error generating image: {e}")
        import traceback
        traceback.print_exc()
        return None


async def add_logo_watermark(image_bytes: bytes) -> bytes:
    """Ajoute le logo Luxura en watermark sur l'image (coin bas-droit, 15%)"""
    try:
        # Ouvrir l'image générée
        base_image = Image.open(io.BytesIO(image_bytes))
        
        # Récupérer le logo
        logo = await get_luxura_logo()
        
        if logo is None:
            logger.warning("Logo not available, returning original image")
            return image_bytes
        
        # Ajouter le logo
        result_image = add_logo_to_image(
            base_image=base_image,
            logo=logo,
            position="bottom-right",
            size_percent=0.15,
            padding=20
        )
        
        # Convertir en bytes PNG
        output = io.BytesIO()
        result_image.save(output, format='PNG', quality=95)
        result_bytes = output.getvalue()
        
        logger.info(f"✅ Logo watermark added ({len(result_bytes)} bytes)")
        return result_bytes
        
    except Exception as e:
        logger.error(f"Error adding logo watermark: {e}")
        return image_bytes  # Retourner l'image originale en cas d'erreur


async def generate_and_upload_blog_images(
    api_key: str,
    site_id: str,
    category: str,
    blog_title: str,
    keywords: List[str] = None,
    focus_product: str = None,
    blog_content: str = None,
    blog_data: Dict = None
) -> Tuple[Optional[Dict], Optional[Dict]]:
    """
    Génère et upload les 2 images (cover + content) basées sur le brief intelligent.
    Le brief analyse le contenu et décide du style approprié.
    """
    
    # Construire blog_data si non fourni
    if blog_data is None:
        blog_data = {
            "title": blog_title,
            "content": blog_content or "",
            "category": category,
            "focus_product": focus_product
        }
    else:
        # S'assurer que tous les champs sont présents
        blog_data.setdefault("title", blog_title)
        blog_data.setdefault("content", blog_content or "")
        blog_data.setdefault("category", category)
        blog_data.setdefault("focus_product", focus_product)

    cover_data = None
    content_data = None

    logger.info(f"📸 Smart Image Generation for: {blog_title[:50]}...")
    logger.info(f"   Content length: {len(blog_data.get('content', ''))} chars")

    # === IMAGE DE COUVERTURE ===
    logger.info(f"🖼️ [1/2] Generating COVER image...")
    cover_bytes = await generate_blog_image_with_dalle(
        category=category,
        blog_title=blog_title,
        blog_data=blog_data,
        image_type="cover"
    )

    if cover_bytes:
        cover_data = await upload_image_bytes_to_wix(
            api_key=api_key,
            site_id=site_id,
            image_bytes=cover_bytes,
            file_name=f"cover-v4-{uuid.uuid4().hex[:8]}.png"
        )
        if cover_data:
            logger.info(f"   ✅ Cover uploaded: {cover_data.get('static_url', '')[:60]}...")

    # === IMAGE DE CONTENU (scène différente) ===
    logger.info(f"🖼️ [2/2] Generating CONTENT image...")
    content_bytes = await generate_blog_image_with_dalle(
        category=category,
        blog_title=blog_title,
        blog_data=blog_data,
        image_type="content"
    )

    if content_bytes:
        content_data = await upload_image_bytes_to_wix(
            api_key=api_key,
            site_id=site_id,
            image_bytes=content_bytes,
            file_name=f"content-v4-{uuid.uuid4().hex[:8]}.png"
        )
        if content_data:
            logger.info(f"   ✅ Content uploaded: {content_data.get('static_url', '')[:60]}...")

    return cover_data, content_data


async def upload_image_bytes_to_wix(
    api_key: str,
    site_id: str,
    image_bytes: bytes,
    file_name: str
) -> Optional[Dict]:
    """Upload une image (bytes) vers Wix Media Manager via catbox.moe fallback"""
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            # Méthode 1: Essayer l'upload direct Wix
            logger.info(f"🔑 Trying direct Wix upload for {file_name}...")
            
            upload_url_response = await client.post(
                "https://www.wixapis.com/site-media/v1/files/generate-file-upload-url",
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
            
            if upload_url_response.status_code == 200:
                upload_data = upload_url_response.json()
                upload_url = upload_data.get("uploadUrl")
                
                if upload_url:
                    upload_response = await client.put(
                        upload_url,
                        content=image_bytes,
                        headers={"Content-Type": "image/png"}
                    )
                    
                    if upload_response.status_code in (200, 201):
                        file_id = upload_data.get("file", {}).get("id")
                        if file_id:
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
                                        static_url = f"https://static.wixstatic.com/media/{file_id}"
                                        logger.info(f"✅ Direct Wix upload success: {static_url[:60]}...")
                                        return {
                                            "file_id": file_id,
                                            "static_url": static_url,
                                            "wix_uri": f"wix:image://v1/{file_id}/{file_name}#originWidth=1200&originHeight=630",
                                            "width": 1200,
                                            "height": 630
                                        }
                                
                                await asyncio.sleep(1)
            
            # Méthode 2: Fallback via catbox.moe
            logger.info(f"⬆️ Using catbox.moe fallback for {file_name}...")
            
            files = {
                'reqtype': (None, 'fileupload'),
                'fileToUpload': (file_name, io.BytesIO(image_bytes), 'image/png')
            }
            
            catbox_response = await client.post(
                "https://catbox.moe/user/api.php",
                files=files,
                timeout=60.0
            )
            
            if catbox_response.status_code == 200:
                temp_url = catbox_response.text.strip()
                if temp_url.startswith('https://'):
                    logger.info(f"✅ Image hosted on catbox: {temp_url}")
                    
                    # Importer cette URL vers Wix
                    from blog_automation import import_image_and_get_wix_uri
                    result = await import_image_and_get_wix_uri(
                        api_key, site_id, temp_url, file_name.replace('.png', '.jpg')
                    )
                    return result
            
            logger.error("All upload methods failed")
            return None
            
    except Exception as e:
        logger.error(f"Error uploading image to Wix: {e}")
        import traceback
        traceback.print_exc()
        return None


# Fallback (ne devrait pas être utilisé si DALL-E fonctionne)
def get_fallback_unsplash_image() -> str:
    """Retourne une image de fallback"""
    return "https://images.unsplash.com/photo-1529156069898-49953e39b3ac?w=1200&h=630&fit=crop"
