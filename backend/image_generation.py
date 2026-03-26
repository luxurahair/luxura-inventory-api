# =====================================================
# IMAGE GENERATION MODULE V3 - Luxura Distribution
# Génération APRÈS le blog + analyse du contenu + style soirée de filles chic
# =====================================================

import os
import uuid
import httpx
import logging
import random
import asyncio
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
- Only one woman alone (must be GROUP of 3-5 women), short hair on any woman, men, masculine features, brushes, combs, styling tools
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
    "rich brunette",
    "honey blonde", 
    "dark chocolate brown",
    "caramel balayage",
    "platinum blonde",
    "auburn copper",
    "golden blonde highlights",
    "ash brown",
    "warm chestnut",
    "ombre dark to caramel",
    "cool toned brown",
    "sun-kissed blonde"
]

_color_index = 0

def get_next_hair_color() -> str:
    """Retourne la prochaine couleur de cheveux en rotation."""
    global _color_index
    color = HAIR_COLORS[_color_index % len(HAIR_COLORS)]
    _color_index += 1
    return color


# =====================================================
# ANALYSE DU CONTENU DU BLOG POUR ADAPTER L'IMAGE
# =====================================================

def analyze_blog_content_for_image(blog_data: Dict) -> str:
    """Analyse le contenu réel du blog et retourne un thème visuel adapté."""
    content = (blog_data.get("content", "") + " " + blog_data.get("title", "")).lower()
    category = blog_data.get("category", "general")
    focus_product = blog_data.get("focus_product", "")

    # Détection du contexte basé sur le contenu réel du blog
    if any(word in content for word in ["soirée", "fille", "amies", "soiree", "girls night", "fête", "célébration"]):
        scene = "chic girls night out around elegant dinner table with candles, champagne glasses and warm lighting"
    elif any(word in content for word in ["installation", "pose", "étape", "tutoriel", "comment"]):
        scene = "elegant modern luxury salon with group of glamorous women admiring and touching their stunning very long hair extensions"
    elif any(word in content for word in ["entretien", "soins", "durée", "maintenir"]):
        scene = "joyful elegant women at a chic brunch table laughing together, showing off their healthy, shiny, extremely long flowing hair"
    elif any(word in content for word in ["halo", "wire", "fil"]):
        scene = "group of glamorous women at an elegant cocktail party, one touching her gorgeous long flowing Halo wire extensions while friends admire"
    elif any(word in content for word in ["genius", "weft", "trame"]):
        scene = "elegant women having a sophisticated dinner party, all with stunning waist-length Genius Weft extensions, laughing and toasting"
    elif any(word in content for word in ["tape", "adhésive", "bande"]):
        scene = "glamorous girlfriends getting ready together in a luxurious dressing room, all with sleek long Tape-in extensions"
    elif any(word in content for word in ["tendance", "2025", "2026", "mode", "style"]):
        scene = "fashion-forward group of women at a trendy rooftop bar, showcasing modern long hair trends with their gorgeous extensions"
    else:
        scene = "group of 4 elegant women having a lively chic soirée around a beautiful dinner table, laughing, toasting with champagne, proudly showing their extremely long luxurious flowing hair extensions"

    product_mention = f"featuring {focus_product}" if focus_product else "featuring premium Luxura hair extensions"
    return f"{scene} {product_mention} - warm, joyful and aspirational luxury atmosphere"


# =====================================================
# CONSTRUCTEUR DE PROMPT V3 - Soirée de filles chic
# =====================================================

def build_smart_image_prompt_v3(
    blog_data: Dict,
    image_type: str = "cover"
) -> str:
    """Prompt intelligent V3 qui analyse le blog complet pour générer des images contextuelles."""
    theme = analyze_blog_content_for_image(blog_data)
    hair_color = get_next_hair_color()
    
    # Variations de scènes pour cover vs content
    if image_type == "content":
        scene_variation = "Focus on a closer view showing the beautiful hair texture and the joyful interaction between friends."
    else:
        scene_variation = "Wide elegant composition showing the full glamorous scene with all women visible."

    base_prompt = f"""
{LUXURA_BASE_RULES}

SCENE DESCRIPTION:
{theme}

{scene_variation}

All 3 to 5 women have extremely long, thick, voluminous hair extensions in various shades including {hair_color}. 
Hair reaches their waist or hips minimum, flowing naturally with beautiful movement, healthy shine, and is the absolute hero of the image.

Atmosphere: joyful, friendly, elegant girls night, lots of genuine smiles and laughter, natural warm interaction between close friends.

Technical specifications:
- Ultra realistic 8K luxury photography
- Soft warm cinematic lighting with candles or ambient glow
- Horizontal 1200x630 composition for blog cover
- Photorealistic, extremely high detail on hair texture, skin and environment
- Magazine editorial quality
"""

    strict_rules = """
STRICT RULES (NEVER BREAK - CRITICAL):
- MUST show 3 to 5 beautiful feminine women together (NOT just one woman alone)
- Only beautiful feminine women, absolutely NO men, NO masculine features, NO beards
- Hair on EVERY woman must be VERY LONG (minimum waist length, preferably hip length)
- NO short hair, NO bob, NO shoulder length hair on ANY woman in the image
- NO brushes, NO combs, NO styling tools visible anywhere
- NO text, NO watermark, NO cartoon, NO illustration style
- All women must look joyful, happy, elegant and glamorous
"""

    return (base_prompt + strict_rules).strip()


# =====================================================
# GÉNÉRATION D'IMAGE AVEC DALL-E V3
# =====================================================

async def generate_blog_image_with_dalle(
    category: str,
    blog_title: str,
    keywords: List[str] = None,
    focus_product: str = None,
    image_type: str = "cover",
    blog_data: Dict = None
) -> Optional[bytes]:
    """
    Génère une image unique avec DALL-E basée sur le CONTENU COMPLET du blog.
    
    V3: Utilise le contenu réel du blog pour adapter les images au contexte.
    """
    if not EMERGENT_LLM_KEY:
        logger.error("EMERGENT_LLM_KEY not configured")
        return None

    try:
        from emergentintegrations.llm.openai.image_generation import OpenAIImageGeneration

        # Construire blog_data si non fourni
        if blog_data is None:
            blog_data = {
                "title": blog_title, 
                "content": "", 
                "category": category, 
                "focus_product": focus_product
            }
        else:
            # S'assurer que tous les champs existent
            blog_data.setdefault("title", blog_title)
            blog_data.setdefault("category", category)
            blog_data.setdefault("focus_product", focus_product)

        prompt = build_smart_image_prompt_v3(blog_data, image_type)

        logger.info(f"🎨 Generating V3 image [{image_type}] for: {blog_title[:60]}...")
        logger.debug(f"Scene theme: {analyze_blog_content_for_image(blog_data)[:100]}...")
        
        image_gen = OpenAIImageGeneration(api_key=EMERGENT_LLM_KEY)
        
        images = await image_gen.generate_images(
            prompt=prompt,
            model="gpt-image-1",
            number_of_images=1
        )

        if images and len(images) > 0:
            logger.info(f"✅ V3 Image generated successfully ({len(images[0])} bytes)")
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
# GÉNÉRATION ET UPLOAD DES 2 IMAGES V3
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
    """
    Génère et upload les images de couverture ET de contenu pour un blog.
    
    V3: Passe le CONTENU COMPLET du blog pour adapter les images.
    """
    cover_data = None
    content_data = None
    
    # Construire le blog_data pour l'analyse
    blog_data_for_image = {
        "title": blog_title,
        "content": blog_content or "",
        "category": category,
        "focus_product": focus_product
    }
    
    logger.info(f"📸 V3 Generating lifestyle images for: {blog_title[:50]}...")
    logger.info(f"   Category: {category}, Product: {focus_product}")
    logger.info(f"   Content length: {len(blog_content or '')} chars")
    
    # 1. Générer l'image de couverture (style soirée de filles)
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
            file_name=f"cover-v3-{uuid.uuid4().hex[:8]}.png"
        )
        if cover_data:
            logger.info(f"   ✅ Cover uploaded: {cover_data.get('static_url', '')[:50]}...")
    
    # 2. Générer l'image de contenu (variante avec focus différent)
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
            file_name=f"content-v3-{uuid.uuid4().hex[:8]}.png"
        )
        if content_data:
            logger.info(f"   ✅ Content uploaded: {content_data.get('static_url', '')[:50]}...")
    
    return cover_data, content_data


# =====================================================
# UPLOAD IMAGE VERS WIX MEDIA (via catbox.moe fallback)
# =====================================================

async def upload_image_bytes_to_wix(
    api_key: str,
    site_id: str,
    image_bytes: bytes,
    file_name: str
) -> Optional[Dict]:
    """
    Upload une image (bytes) vers Wix Media Manager.
    Utilise catbox.moe comme hébergeur intermédiaire si nécessaire.
    """
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
                                        static_url = f"https://static.wixstatic.com/media/{file_id}"
                                        logger.info(f"✅ Direct Wix upload success: {static_url[:60]}...")
                                        return {
                                            "file_id": file_id,
                                            "static_url": static_url,
                                            "width": 1200,
                                            "height": 630
                                        }
                                
                                await asyncio.sleep(1)
            
            # Méthode 2: Fallback via catbox.moe
            logger.info(f"⬆️ Using catbox.moe fallback for {file_name}...")
            
            import io
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
# FALLBACK UNSPLASH - SOIRÉE DE FILLES CHIC
# =====================================================

FALLBACK_UNSPLASH_IMAGES = {
    "general": [
        # Images lifestyle soirée de filles (backup si DALL-E échoue)
        "https://customer-assets.emergentagent.com/job_hair-extensions-shop/artifacts/no4frw3t_vaVsE.jpg",
        "https://customer-assets.emergentagent.com/job_hair-extensions-shop/artifacts/oyi6y21r_Aq7eZ.jpg",
        "https://customer-assets.emergentagent.com/job_hair-extensions-shop/artifacts/21xcpk05_OdzWP.jpg",
        "https://images.unsplash.com/photo-1529156069898-49953e39b3ac?w=1200&h=630&fit=crop",
        "https://images.unsplash.com/photo-1600948836101-f9ffda59d250?w=1200&h=630&fit=crop",
    ]
}

_fallback_index = 0

def get_fallback_unsplash_image() -> str:
    """Retourne une image de fallback style soirée de filles."""
    global _fallback_index
    images = FALLBACK_UNSPLASH_IMAGES["general"]
    image = images[_fallback_index % len(images)]
    _fallback_index += 1
    return image
