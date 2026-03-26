# =====================================================
# IMAGE GENERATION MODULE V3 - Luxura Distribution
# Génération APRÈS le blog + analyse du contenu + style soirée de filles chic
# =====================================================

import os
import uuid
import httpx
import asyncio
import logging
import random
import io
from typing import Optional, Dict, Tuple, List
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

EMERGENT_LLM_KEY = os.getenv("EMERGENT_LLM_KEY")

# =====================================================
# RÈGLES BUSINESS LUXURA + STYLE SOIRÉE DE FILLES CHIC
# =====================================================

LUXURA_BASE_RULES = """
Professional luxury lifestyle photography for Luxura Distribution Quebec Canada.
LUXURA IS A HIGH-END IMPORTER AND DISTRIBUTOR - NOT A SALON.

MANDATORY SCENE REQUIREMENTS:
- Group of 3 to 5 beautiful elegant feminine women (late 20s to mid 30s)
- Joyful, lively, friendly girls night out or chic soirée atmosphere
- Smiles, laughter, complicity, natural interaction between friends
- Scene ideas: elegant dinner table with candles and wine glasses, chic evening soirée, or luxurious modern salon
- ALL women have EXTREMELY LONG, thick, voluminous, luxurious hair extensions reaching waist or hips
- Hair is flowing naturally, shiny, healthy and the absolute HERO of the image

STRICTLY FORBIDDEN:
- Only one woman, short hair on any woman, men, masculine features, brushes, combs, styling tools
- Hair shorter than waist length, bob, pixie, shoulder length
- Text, watermark, cartoon, illustration style

FOCUS ON:
- Joyful energy, elegance, confidence and friendship
- Very long, beautiful, flowing hair extensions as the main visual element
- Aspirational luxury lifestyle photography
"""

# =====================================================
# COULEURS DE CHEVEUX (rotation)
# =====================================================

HAIR_COLORS = [
    "rich brunette", "honey blonde", "dark chocolate brown", "caramel balayage",
    "platinum blonde", "auburn copper", "golden blonde highlights", "ash brown",
    "warm chestnut", "ombre dark to caramel", "sun-kissed blonde"
]

_color_index = 0

def get_next_hair_color() -> str:
    global _color_index
    color = HAIR_COLORS[_color_index % len(HAIR_COLORS)]
    _color_index += 1
    return color


# =====================================================
# ANALYSE DU CONTENU DU BLOG POUR ADAPTER L'IMAGE
# =====================================================

def analyze_blog_content_for_image(blog_data: Dict, image_type: str = "cover") -> str:
    """Analyse le contenu réel du blog et retourne un thème visuel adapté"""
    content = (blog_data.get("content", "") + " " + blog_data.get("title", "")).lower()
    category = blog_data.get("category", "general")
    focus_product = blog_data.get("focus_product", "")

    # COVER: Scène principale
    if image_type == "cover":
        if any(word in content for word in ["soirée", "fille", "amies", "soiree", "girls night", "table", "dîner"]):
            scene = "chic girls night out around elegant dinner table with candles and wine glasses, 4 glamorous women laughing together"
        elif any(word in content for word in ["installation", "pose", "étape", "tutoriel", "comment"]):
            scene = "elegant modern luxury salon with group of 4 glamorous women admiring their stunning long hair extensions in mirrors"
        elif any(word in content for word in ["entretien", "soins", "durée", "repositionnement"]):
            scene = "joyful elegant women at a sophisticated brunch table showing off their healthy, shiny, very long flowing hair"
        elif "genius" in content or "weft" in content or "trame" in content:
            scene = "elegant sophisticated dinner party with 4 women toasting champagne, all with stunning waist-length Genius Weft hair extensions"
        elif "tape" in content or "adhésive" in content:
            scene = "glamorous girlfriends getting ready together in a luxurious dressing room, all with sleek long Tape-in extensions"
        elif "halo" in content or "wire" in content:
            scene = "group of glamorous women at an elegant cocktail party, one touching her gorgeous long flowing Halo extensions while friends admire"
        elif "i-tip" in content or "itip" in content or "kératine" in content:
            scene = "chic rooftop bar scene with 4 elegant women showing their natural-looking I-Tip keratin extensions"
        else:
            scene = "group of 4 elegant women having a lively chic soirée around a beautiful dinner table, laughing, toasting with champagne"
    
    # CONTENT: Scène intérieure différente (plus intime, focus cheveux)
    else:
        if any(word in content for word in ["installation", "pose", "étape", "tutoriel"]):
            scene = "close-up of 3 glamorous women in a luxury salon, one touching another's beautiful long extensions with admiration"
        elif any(word in content for word in ["entretien", "soins"]):
            scene = "intimate scene of 3 elegant women at a spa day, comparing their long shiny healthy hair extensions"
        elif "genius" in content or "weft" in content:
            scene = "3 best friends at a fancy restaurant, one showing her friends the seamless blend of her Genius Weft extensions"
        elif "tape" in content:
            scene = "glamorous women in a chic bathroom getting ready for a night out, admiring their sleek Tape-in extensions"
        elif "halo" in content:
            scene = "cozy elegant living room with 3 women having wine, one demonstrating how easy her Halo wire extensions are"
        else:
            scene = "intimate moment between 3 elegant girlfriends admiring each other's beautiful very long flowing hair extensions"

    product_text = f"featuring {focus_product}" if focus_product else "featuring premium Luxura hair extensions"
    return f"{scene}, {product_text} - warm, joyful and aspirational luxury atmosphere"


# =====================================================
# CONSTRUCTEUR DE PROMPT V3 - Soirée de filles chic
# =====================================================

def build_smart_image_prompt_v3(blog_data: Dict, image_type: str = "cover") -> str:
    """Prompt intelligent qui analyse le blog complet et génère des scènes DIFFÉRENTES pour cover vs content"""
    theme = analyze_blog_content_for_image(blog_data, image_type)
    hair_color = get_next_hair_color()

    base_prompt = f"""
{LUXURA_BASE_RULES}

SCENE DESCRIPTION:
{theme}

All women have extremely long, thick, voluminous {hair_color} hair extensions reaching their waist or hips. 
Hair is flowing naturally with beautiful movement, healthy shine, and is the hero of the image.

Atmosphere: joyful, friendly, elegant girls night, lots of smiles and laughter, natural interaction.

Technical specifications:
- Ultra realistic 8K luxury photography
- Soft warm cinematic lighting
- Horizontal 1200x630 composition
- Photorealistic, high detail on hair texture and skin
"""

    strict_rules = """
STRICT RULES (NEVER BREAK):
- Only beautiful feminine women, no men, no masculine features
- Hair on EVERY woman must be very long (minimum waist length, preferably hip length)
- No short hair, no bob, no shoulder length on any woman
- No brushes, no combs, no styling tools visible
- No text, no watermark, no cartoon, no illustration
"""

    return (base_prompt + strict_rules).strip()


# =====================================================
# GÉNÉRATION D'IMAGE AVEC DALL-E
# =====================================================

async def generate_blog_image_with_dalle(
    category: str,
    blog_title: str,
    keywords: List[str] = None,
    focus_product: str = None,
    image_type: str = "cover",
    blog_data: Dict = None
) -> Optional[bytes]:
    """Génère une image unique avec DALL-E basée sur le contenu du blog"""
    if not EMERGENT_LLM_KEY:
        logger.error("EMERGENT_LLM_KEY not configured")
        return None

    try:
        from emergentintegrations.llm.openai.image_generation import OpenAIImageGeneration

        if blog_data is None:
            blog_data = {
                "title": blog_title,
                "content": "",
                "category": category,
                "focus_product": focus_product
            }

        prompt = build_smart_image_prompt_v3(blog_data, image_type)
        
        # Log le thème pour debug
        theme = analyze_blog_content_for_image(blog_data, image_type)
        logger.info(f"🎨 Generating [{image_type}] image for: {blog_title[:50]}...")
        logger.info(f"   Theme: {theme[:80]}...")

        image_gen = OpenAIImageGeneration(api_key=EMERGENT_LLM_KEY)

        images = await image_gen.generate_images(
            prompt=prompt,
            model="gpt-image-1",
            number_of_images=1
        )

        if images and len(images) > 0:
            logger.info(f"✅ [{image_type}] Image generated successfully ({len(images[0])} bytes)")
            return images[0]
        else:
            logger.error("No image returned from DALL-E")
            return None

    except Exception as e:
        logger.error(f"❌ Error generating DALL-E image: {e}")
        import traceback
        traceback.print_exc()
        return None


# =====================================================
# GÉNÉRATION ET UPLOAD DES 2 IMAGES
# =====================================================

async def generate_and_upload_blog_images(
    api_key: str,
    site_id: str,
    category: str,
    blog_title: str,
    keywords: List[str] = None,
    focus_product: str = None,
    blog_content: str = None
) -> Tuple[Optional[Dict], Optional[Dict]]:
    """Génère et upload les 2 images (cover + content) basées sur le contenu du blog"""
    
    blog_data_for_image = {
        "title": blog_title,
        "content": blog_content or "",
        "category": category,
        "focus_product": focus_product
    }

    cover_data = None
    content_data = None

    logger.info(f"📸 Generating chic girls night lifestyle images for: {blog_title[:50]}...")
    logger.info(f"   Blog content length: {len(blog_content or '')} chars")

    # === IMAGE DE COUVERTURE ===
    logger.info(f"🖼️ [1/2] Generating COVER image...")
    cover_bytes = await generate_blog_image_with_dalle(
        category=category,
        blog_title=blog_title,
        keywords=keywords,
        focus_product=focus_product,
        image_type="cover",
        blog_data=blog_data_for_image
    )

    if cover_bytes:
        cover_data = await upload_image_bytes_to_wix(
            api_key=api_key,
            site_id=site_id,
            image_bytes=cover_bytes,
            file_name=f"cover-{uuid.uuid4().hex[:8]}.png"
        )
        if cover_data:
            logger.info(f"   ✅ Cover uploaded: {cover_data.get('static_url', '')[:60]}...")

    # === IMAGE DE CONTENU (DIFFÉRENTE) ===
    logger.info(f"🖼️ [2/2] Generating CONTENT image (different scene)...")
    content_bytes = await generate_blog_image_with_dalle(
        category=category,
        blog_title=blog_title,
        keywords=keywords,
        focus_product=focus_product,
        image_type="content",
        blog_data=blog_data_for_image
    )

    if content_bytes:
        content_data = await upload_image_bytes_to_wix(
            api_key=api_key,
            site_id=site_id,
            image_bytes=content_bytes,
            file_name=f"content-{uuid.uuid4().hex[:8]}.png"
        )
        if content_data:
            logger.info(f"   ✅ Content uploaded: {content_data.get('static_url', '')[:60]}...")

    return cover_data, content_data


# =====================================================
# UPLOAD IMAGE VERS WIX MEDIA
# =====================================================

async def upload_image_bytes_to_wix(
    api_key: str,
    site_id: str,
    image_bytes: bytes,
    file_name: str
) -> Optional[Dict]:
    """Upload une image (bytes) vers Wix Media Manager via catbox.moe"""
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


# =====================================================
# FALLBACK - Pas utilisé si DALL-E fonctionne
# =====================================================

def get_fallback_unsplash_image() -> str:
    """Retourne une image de fallback (ne devrait pas être utilisé)"""
    return "https://images.unsplash.com/photo-1529156069898-49953e39b3ac?w=1200&h=630&fit=crop"
