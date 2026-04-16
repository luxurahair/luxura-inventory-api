# image_generation.py
# Version V5 - Exploite vraiment le brief visuel Luxura
# Luxura = distributeur/importateur, vente en ligne + salons affiliés
# On garde la structure existante, mais on corrige le prompt engineering

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

from image_brief_generator import generate_image_brief
from logo_overlay import get_luxura_logo, add_logo_to_image


def _join_clean(parts: List[str]) -> str:
    return "\n".join([p.strip() for p in parts if p and str(p).strip()])


def build_prompt_from_brief(brief: Dict, image_type: str = "cover") -> str:
    """
    Construit un vrai prompt à partir du brief.
    Avant, on envoyait presque juste section['scene'].
    Maintenant on utilise:
    - scène
    - style
    - focus
    - avoid
    - règles marque Luxura
    - distinction cover vs content
    """
    section = brief["cover"] if image_type == "cover" else brief["content"]
    avoid = ", ".join(section.get("avoid", []))
    style = section.get("style", "")
    focus = section.get("focus", "")
    brand_rules = brief.get("brand_rules", "")
    product = brief.get("product", "extensions capillaires Luxura")
    visual_mode = brief.get("visual_mode", "consumer_guide")
    hair_rule = brief.get(
        "hair_length_rule",
        "mid-back to very long hair preferred; believable extension result only"
    )

    framing = (
        "Create a horizontal 1200x630 premium blog cover image with a strong simple composition, readable at thumbnail size."
        if image_type == "cover"
        else "Create a realistic editorial image for the blog body, with slightly closer framing and more detail."
    )

    extra_rules = (
        "The image must clearly support Luxura Distribution as a premium importer/distributor and salon partner brand in Quebec."
        " The image must not feel like a classroom, certification course, or training workshop."
        " It must feel commercial, premium, believable, and relevant to hair extensions."
    )

    prompt = _join_clean([
        f"Brand: Luxura Distribution.",
        f"Product context: {product}.",
        f"Visual mode: {visual_mode}.",
        "",
        "SCENE:",
        section.get("scene", ""),
        "",
        "STYLE:",
        style,
        "",
        "FOCUS:",
        focus,
        "",
        "HAIR RULES:",
        hair_rule,
        "",
        "BRAND RULES:",
        brand_rules,
        "",
        "COMPOSITION:",
        framing,
        "",
        "BUSINESS CONTEXT:",
        extra_rules,
        "",
        "AVOID:",
        avoid,
        "",
        "MANDATORY OUTPUT RULES:",
        "Photorealistic image only.",
        "No text, no letters, no watermark, no collage.",
        "No men.",
        "No short hair, no pixie cut, no bob haircut.",
        "Hair must be extension-relevant and visually believable.",
        "Keep the aesthetic premium, realistic, elegant, and commercially usable for Luxura blog content."
    ])

    return prompt.strip()


async def generate_blog_image_with_dalle(
    category: str,
    blog_title: str,
    blog_data: Dict = None,
    image_type: str = "cover",
    add_logo: bool = True
) -> Optional[bytes]:
    """
    Génère une image avec DALL-E via l'API OpenAI directement (comme les crons Facebook).
    Utilise OPENAI_API_KEY ou EMERGENT_LLM_KEY.
    """
    import requests
    import base64
    
    # Essayer OPENAI_API_KEY d'abord, puis EMERGENT_LLM_KEY
    api_key = os.environ.get("OPENAI_API_KEY") or EMERGENT_LLM_KEY
    
    if not api_key:
        logger.error("No API key configured (OPENAI_API_KEY or EMERGENT_LLM_KEY)")
        return None

    try:
        if blog_data is None:
            blog_data = {
                "title": blog_title,
                "content": "",
                "category": category
            }

        blog_data.setdefault("title", blog_title)
        blog_data.setdefault("category", category)

        brief = generate_image_brief(blog_data)
        prompt = build_prompt_from_brief(brief, image_type)

        logger.info(
            f"🎨 Generating [{image_type}] | mode={brief.get('visual_mode')} | "
            f"title={blog_title[:70]}"
        )

        # Appel direct à l'API OpenAI DALL-E (comme les crons Facebook)
        response = requests.post(
            "https://api.openai.com/v1/images/generations",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "dall-e-3",
                "prompt": prompt,
                "size": "1792x1024",
                "quality": "standard",
                "n": 1,
                "response_format": "b64_json"  # Retourne l'image en base64
            },
            timeout=120
        )

        if response.status_code == 200:
            data = response.json()
            image_b64 = data["data"][0]["b64_json"]
            image_bytes = base64.b64decode(image_b64)
            logger.info(f"✅ [{image_type}] DALL-E image generated ({len(image_bytes)} bytes)")
            
            if add_logo and brief.get("logo_overlay", True):
                logger.info("🏷️ Adding Luxura logo overlay...")
                image_bytes = await add_logo_watermark(image_bytes)

            return image_bytes
        else:
            logger.error(f"❌ DALL-E API error: {response.status_code} - {response.text[:200]}")
            return None

    except Exception as e:
        logger.error(f"❌ Error generating image: {e}")
        import traceback
        traceback.print_exc()
        return None


async def add_logo_watermark(image_bytes: bytes) -> bytes:
    """
    Ajoute le logo Luxura en bas à droite.
    On garde ton comportement existant.
    """
    try:
        base_image = Image.open(io.BytesIO(image_bytes))
        logo = await get_luxura_logo()

        if logo is None:
            logger.warning("Logo not available, returning original image")
            return image_bytes

        result_image = add_logo_to_image(
            base_image=base_image,
            logo=logo,
            position="bottom-right",
            size_percent=0.30,
            padding=10
        )

        output = io.BytesIO()
        result_image.save(output, format='PNG', quality=95)
        result_bytes = output.getvalue()

        logger.info(f"✅ Logo watermark added ({len(result_bytes)} bytes)")
        return result_bytes

    except Exception as e:
        logger.error(f"Error adding logo watermark: {e}")
        import traceback
        traceback.print_exc()
        return image_bytes


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
    Génère et upload:
    - 1 image cover
    - 1 image contenu

    Les prompts sont désormais pilotés par le brief Luxura complet.
    """
    if blog_data is None:
        blog_data = {
            "title": blog_title,
            "content": blog_content or "",
            "category": category,
            "focus_product": focus_product,
            "keywords": keywords or []
        }
    else:
        blog_data.setdefault("title", blog_title)
        blog_data.setdefault("content", blog_content or "")
        blog_data.setdefault("category", category)
        blog_data.setdefault("focus_product", focus_product)
        blog_data.setdefault("keywords", keywords or [])

    cover_data = None
    content_data = None

    logger.info(f"📸 Smart image generation started for: {blog_title[:80]}")
    logger.info(f"   category={category} | focus_product={focus_product}")

    # === COVER ===
    logger.info("🖼️ [1/2] Generating COVER image...")
    cover_bytes = await generate_blog_image_with_dalle(
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
            file_name=f"cover-v5-{uuid.uuid4().hex[:8]}.png"
        )
        if cover_data:
            logger.info(f"✅ Cover uploaded: {cover_data.get('static_url', '')[:80]}")

    # === CONTENT ===
    logger.info("🖼️ [2/2] Generating CONTENT image...")
    content_bytes = await generate_blog_image_with_dalle(
        category=category,
        blog_title=blog_title,
        blog_data=blog_data,
        image_type="content",
        add_logo=False  # image dans l'article = plus propre sans gros watermark
    )

    if content_bytes:
        content_data = await upload_image_bytes_to_wix(
            api_key=api_key,
            site_id=site_id,
            image_bytes=content_bytes,
            file_name=f"content-v5-{uuid.uuid4().hex[:8]}.png"
        )
        if content_data:
            logger.info(f"✅ Content uploaded: {content_data.get('static_url', '')[:80]}")

    return cover_data, content_data


async def upload_image_bytes_to_wix(
    api_key: str,
    site_id: str,
    image_bytes: bytes,
    file_name: str
) -> Optional[Dict]:
    """
    Upload image bytes to Wix Media Manager.
    1) tente upload direct
    2) fallback catbox
    3) import vers Wix
    """
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
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
                file_id = upload_data.get("file", {}).get("id")

                if upload_url:
                    upload_response = await client.put(
                        upload_url,
                        content=image_bytes,
                        headers={"Content-Type": "image/png"}
                    )

                    if upload_response.status_code in (200, 201) and file_id:
                        logger.info(f"📤 Direct upload accepted for file_id={file_id}")

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
                                    # Extraire les vraies dimensions de Wix
                                    media_info = file_desc.get("media", {}).get("image", {}).get("image", {})
                                    real_width = media_info.get("width", 1200)
                                    real_height = media_info.get("height", 630)
                                    display_name = file_desc.get("displayName", file_name)
                                    
                                    static_url = f"https://static.wixstatic.com/media/{file_id}"
                                    # Format wix_uri correct: utilise display_name de Wix, pas notre file_name
                                    wix_uri = f"wix:image://v1/{file_id}/{display_name}#originWidth={real_width}&originHeight={real_height}"
                                    
                                    logger.info(f"✅ Direct Wix upload success: {static_url[:80]}")
                                    logger.info(f"   wix_uri: {wix_uri}")
                                    return {
                                        "file_id": file_id,
                                        "static_url": static_url,
                                        "wix_uri": wix_uri,
                                        "width": real_width,
                                        "height": real_height,
                                        "display_name": display_name
                                    }

                            await asyncio.sleep(1)

            # === FALLBACK CATBOX ===
            logger.info(f"⬆️ Using catbox.moe fallback for {file_name}...")

            files = {
                "reqtype": (None, "fileupload"),
                "fileToUpload": (file_name, io.BytesIO(image_bytes), "image/png")
            }

            catbox_response = await client.post(
                "https://catbox.moe/user/api.php",
                files=files,
                timeout=60.0
            )

            if catbox_response.status_code == 200:
                temp_url = catbox_response.text.strip()
                if temp_url.startswith("https://"):
                    logger.info(f"✅ Temporary image hosted on catbox: {temp_url}")

                    from blog_automation import import_image_and_get_wix_uri
                    # On garde le file_name original sans changer l'extension
                    result = await import_image_and_get_wix_uri(
                        api_key,
                        site_id,
                        temp_url,
                        file_name  # Plus de .replace()
                    )
                    return result

            logger.error("All upload methods failed")
            return None

    except Exception as e:
        logger.error(f"Error uploading image to Wix: {e}")
        import traceback
        traceback.print_exc()
        return None


def get_fallback_unsplash_image() -> str:
    """
    Fallback ultime.
    À garder pour compatibilité, même si on veut s'en servir le moins possible.
    """
    return "https://customer-assets.emergentagent.com/job_hair-extensions-shop/artifacts/no4frw3t_vaVsE.jpg"
