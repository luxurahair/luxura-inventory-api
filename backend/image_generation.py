# image_generation.py
# Version V7 - IMAGES RÉELLES pour installations, DALL-E pour lifestyle/résultats
# Architecture: Brief → Détecte mode → Stock réel OU DALL-E selon le type

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
from logo_overlay import get_luxura_logo, add_logo_to_image, process_image_with_logo

# Import des images stock réelles
from real_stock_images import get_real_image_for_mode, IMAGES_BY_MODE


def should_use_real_images(mode: str) -> bool:
    """
    Détermine si on doit utiliser des images réelles (stock) ou DALL-E.
    
    IMAGES RÉELLES pour: installations techniques (on ne peut pas faker ça)
    DALL-E pour: résultats, lifestyle, beauté (peut générer des femmes avec cheveux longs)
    """
    # Installations = TOUJOURS images réelles
    if mode.startswith("installation_"):
        return True
    
    # Entretien et résultats = DALL-E peut générer
    return False


def build_prompt_from_brief(brief: Dict, image_type: str = "cover") -> str:
    """V7: Construit le prompt avec règles STRICTES anti-hommes"""
    section = brief["cover"] if image_type == "cover" else brief["content"]
    prompt = section['scene']
    return prompt


async def get_image_for_blog(
    category: str,
    blog_title: str,
    blog_data: Dict = None,
    image_type: str = "cover",
    add_logo: bool = True
) -> Optional[bytes]:
    """
    V7: Fonction principale qui décide entre images réelles ou DALL-E.
    
    - Installations → Images stock réelles
    - Lifestyle/Résultats → DALL-E avec règles strictes
    """
    if blog_data is None:
        blog_data = {"title": blog_title, "content": "", "category": category}
    
    # Générer le brief pour détecter le mode
    brief = generate_image_brief(blog_data)
    mode = brief["visual_mode"]
    
    logger.info(f"🎯 V7 Mode: {mode} | Type: {image_type} | Title: {blog_title[:40]}...")
    
    # Décider: images réelles ou DALL-E?
    if should_use_real_images(mode):
        logger.info(f"📷 Using REAL stock image (installation technique)")
        return await get_real_stock_image_with_logo(mode, image_type, add_logo)
    else:
        logger.info(f"🎨 Using DALL-E generation (lifestyle/result)")
        return await generate_blog_image_with_dalle(
            category=category,
            blog_title=blog_title,
            blog_data=blog_data,
            image_type=image_type,
            add_logo=add_logo
        )


async def get_real_stock_image_with_logo(
    mode: str, 
    image_type: str = "cover",
    add_logo: bool = True
) -> Optional[bytes]:
    """
    Télécharge une vraie image stock et ajoute le logo Luxura.
    """
    try:
        # Obtenir l'URL de l'image réelle
        image_url = get_real_image_for_mode(mode, image_type)
        logger.info(f"   Stock image URL: {image_url[:60]}...")
        
        # Télécharger l'image
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(image_url)
            if response.status_code != 200:
                logger.error(f"Failed to download stock image: {response.status_code}")
                return None
            
            image_bytes = response.content
            logger.info(f"   Downloaded: {len(image_bytes)} bytes")
        
        # Ajouter le logo si demandé
        if add_logo:
            image_bytes = await add_logo_watermark(image_bytes)
        
        return image_bytes
        
    except Exception as e:
        logger.error(f"Error getting real stock image: {e}")
        return None


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
    """Ajoute le logo Luxura en watermark sur l'image (coin bas-droit, 30% - visible en miniature)"""
    try:
        # Ouvrir l'image générée
        base_image = Image.open(io.BytesIO(image_bytes))
        
        # Récupérer le logo
        logo = await get_luxura_logo()
        
        if logo is None:
            logger.warning("Logo not available, returning original image")
            return image_bytes
        
        # Ajouter le logo - 30% pour être visible même en miniature
        result_image = add_logo_to_image(
            base_image=base_image,
            logo=logo,
            position="bottom-right",
            size_percent=0.30,  # 30% pour visibilité en miniature
            padding=10
        )
        
        # Convertir en bytes PNG
        output = io.BytesIO()
        result_image.save(output, format='PNG', quality=95)
        result_bytes = output.getvalue()
        
        logger.info(f"✅ Logo watermark added (30% size) ({len(result_bytes)} bytes)")
        return result_bytes
        
    except Exception as e:
        logger.error(f"Error adding logo watermark: {e}")
        import traceback
        traceback.print_exc()
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
    V7: Génère et upload les 2 images basées sur le mode détecté.
    
    - Installations → Images stock RÉELLES
    - Lifestyle/Résultats → DALL-E avec règles strictes
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
        blog_data.setdefault("title", blog_title)
        blog_data.setdefault("content", blog_content or "")
        blog_data.setdefault("category", category)
        blog_data.setdefault("focus_product", focus_product)

    cover_data = None
    content_data = None

    logger.info(f"📸 V7 Smart Image Generation: {blog_title[:50]}...")

    # === IMAGE DE COUVERTURE ===
    logger.info(f"🖼️ [1/2] Getting COVER image...")
    cover_bytes = await get_image_for_blog(
        category=category,
        blog_title=blog_title,
        blog_data=blog_data,
        image_type="cover",
        add_logo=True
    )

    if cover_bytes:
        cover_data = await upload_image_bytes_to_wix(
            api_key=api_key,
            site_id=site_id,
            image_bytes=cover_bytes,
            file_name=f"cover-v7-{uuid.uuid4().hex[:8]}.png"
        )
        if cover_data:
            logger.info(f"   ✅ Cover uploaded: {cover_data.get('static_url', '')[:60]}...")

    # === IMAGE DE CONTENU ===
    logger.info(f"🖼️ [2/2] Getting CONTENT image...")
    content_bytes = await get_image_for_blog(
        category=category,
        blog_title=blog_title,
        blog_data=blog_data,
        image_type="content",
        add_logo=True
    )

    if content_bytes:
        content_data = await upload_image_bytes_to_wix(
            api_key=api_key,
            site_id=site_id,
            image_bytes=content_bytes,
            file_name=f"content-v7-{uuid.uuid4().hex[:8]}.png"
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
