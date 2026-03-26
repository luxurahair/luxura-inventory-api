# =====================================================
# IMAGE GENERATION MODULE V2 - Luxura Distribution
# Génération d'images contextuelles basées sur le TITRE + MOTS-CLÉS + PRODUIT
# =====================================================

import os
import base64
import uuid
import httpx
import logging
import random
from typing import Optional, Dict, Tuple, List
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Clé API pour la génération d'images
EMERGENT_LLM_KEY = os.getenv("EMERGENT_LLM_KEY")

# =====================================================
# RÈGLES BUSINESS LUXURA - IMPORTATEUR/DISTRIBUTEUR
# =====================================================

LUXURA_BASE_RULES = """
Professional luxury hair extension RESULT photography for Luxura Distribution Quebec Canada.
LUXURA IS A HIGH-END IMPORTER AND DISTRIBUTOR - NOT A SALON.

THE IMAGE MUST SHOW THE FINAL RESULT - A WOMAN WITH VERY LONG BEAUTIFUL HAIR EXTENSIONS.

CRITICAL SUBJECT REQUIREMENTS (ABSOLUTELY MANDATORY):
- ONLY FEMALE SUBJECTS - beautiful feminine woman with elegant features
- MUST be a woman, lady, female model - NEVER a man, male, masculine person
- NEVER show any male person, man, masculine features, beard, or short masculine haircut
- VERY LONG FLOWING FEMININE HAIR - minimum waist-length, preferably hip-length
- Hair MUST be visibly LONG - reaching at least the lower back or waist
- Feminine elegant appearance, glamorous female beauty
- Female model showcasing THE RESULT of wearing premium long hair extensions

MANDATORY VISUAL REQUIREMENTS:
- VERY LONG HAIR - waist length or longer (absolutely mandatory)
- Hair must be flowing, luxurious, thick and voluminous
- Beautiful FEMALE woman showing the AMAZING RESULT of wearing premium extensions
- Luxury glamour photography aesthetic
- Elegant realistic WOMAN (not cartoon, not mannequin)
- Clean, bright, professional lighting
- Premium lifestyle or glamour composition
- Hair should be the HERO of the image - long, beautiful, flowing

STRICTLY FORBIDDEN (WILL BE REJECTED):
- ANY MALE/MAN/MASCULINE PERSON - absolutely no men in the image
- Beards, facial hair, masculine jawlines
- SHORT HAIR - absolutely no short hair, no pixie cut, no bob haircut, no shoulder-length hair
- BRUSHING OR STYLING SCENES - no brushes, no combs, no styling tools
- Salon work scenes - no stylists, no application process
- Mannequin heads
- Text or watermarks in image
- Cartoon or illustration style
- Hair shorter than waist-length
- Any styling process or maintenance scene

FOCUS ON:
- THE RESULT: beautiful WOMAN with VERY LONG gorgeous flowing feminine hair extensions
- Hair reaching the waist or lower back
- Product beauty: showcase the quality of long luxurious extensions
- Lifestyle luxury: aspirational, premium, elegant feminine beauty
- The TRANSFORMATION: show what wearing extensions achieves - LONG BEAUTIFUL HAIR
"""

# =====================================================
# RÈGLES VISUELLES PAR CATÉGORIE - DISTRIBUTEUR
# =====================================================

CATEGORY_VISUAL_RULES = {
    "genius": {
        "must_have": ["long flowing hair result", "seamless weft visible", "premium product quality", "natural luxury result", "thin invisible weft"],
        "avoid": ["salon application", "training", "short hair", "pixie", "bob"],
        "style": "sophisticated luxury product result"
    },
    "halo": {
        "must_have": ["very long hair", "natural blend", "soft glamour", "invisible wire look", "instant volume result"],
        "avoid": ["short hair", "application process", "salon tools"],
        "style": "effortless glamour, luxury lifestyle"
    },
    "tape": {
        "must_have": ["smooth sleek hair result", "premium quality", "natural look", "volume and length"],
        "avoid": ["application process", "visible tape edges", "salon scene"],
        "style": "sleek professional result"
    },
    "itip": {
        "must_have": ["natural strand-by-strand result", "seamless blend", "individual strands look natural"],
        "avoid": ["application process", "visible bonds", "salon scene"],
        "style": "ultra-natural premium result"
    },
    "entretien": {
        "must_have": ["healthy shiny hair", "well-maintained extensions", "premium hair care products"],
        "avoid": ["damaged hair", "salon scene"],
        "style": "healthy maintained luxury hair"
    },
    "tendances": {
        "must_have": ["trendy styling", "modern look", "fashion-forward", "2025 hair trends"],
        "avoid": ["dated styles", "basic plain look"],
        "style": "contemporary fashion-forward beauty"
    },
    "general": {
        "must_have": ["long beautiful hair", "premium result", "elegant woman", "high-end quality"],
        "avoid": ["short hair", "unprofessional", "salon work"],
        "style": "luxury hair extension result"
    }
}

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
    """Retourne la prochaine couleur de cheveux."""
    global _color_index
    color = HAIR_COLORS[_color_index % len(HAIR_COLORS)]
    _color_index += 1
    return color


# =====================================================
# CONSTRUCTEUR DE PROMPT V3 - Style Pinterest/Grok Optimisé
# Plus efficace pour gpt-image-1 (2026)
# =====================================================

def build_smart_image_prompt(
    category: str,
    blog_title: str,
    keywords: List[str] = None,
    focus_product: str = None,
    image_type: str = "cover",
    hair_color: str = None
) -> str:
    """
    Construit un prompt intelligent V3 pour LUXURA DISTRIBUTION.
    
    AMÉLIORATIONS V3 (2026) - Style Grok/Pinterest:
    - Prompts ultra-spécifiques pour cheveux TRÈS LONGS
    - Processus de pose visible (pour tutoriels)
    - Résultat final glamour (pour articles généraux)
    - Anti-hommes renforcé en fin de prompt
    """
    title_lower = (blog_title or "").lower()
    keywords = keywords or []
    hair_color = hair_color or get_next_hair_color()
    cat_rules = CATEGORY_VISUAL_RULES.get(category, CATEGORY_VISUAL_RULES["general"])

    # Détection du type d'article
    is_comparison = any(k in title_lower for k in ["vs", "versus", "comparatif", "comparaison", "différence"])
    is_entretien = any(k in title_lower for k in ["entretien", "soins", "durée", "maintenu", "prolonger"])
    is_tendances = any(k in title_lower for k in ["tendance", "2025", "2026", "mode", "style", "balayage"])
    is_installation = any(k in title_lower for k in ["installation", "pose", "comment", "étape", "tutoriel", "guide"])
    is_halo = "halo" in title_lower
    is_genius = "genius" in title_lower or "weft" in title_lower
    is_tape = "tape" in title_lower or "adhésive" in title_lower or "bande" in title_lower
    is_itip = "i-tip" in title_lower or "itip" in title_lower or "kératine" in title_lower

    # =====================================================
    # PROMPTS PAR CATÉGORIE - Style Grok/Pinterest
    # =====================================================
    
    if is_itip:
        if is_installation or image_type == "content":
            # I-TIP - Processus de pose
            prompt = f"""Ultra realistic photograph of a beautiful woman getting professional I-Tip hair extensions installed in a luxury salon. Elegant feminine model with long {hair_color} hair, hairstylist applying keratin I-Tip extensions strand by strand using small microbeads close to the scalp.

Show the beautiful transformation: very long, thick, voluminous waist-length hair extensions with perfect natural blend. Focus on the application moment and the luxurious final length.

Soft natural lighting, clean modern salon with white and beige tones, photorealistic 8K hair details, elegant beauty photography, horizontal 1200x630 composition."""
        else:
            # I-TIP - Résultat final
            prompt = f"""Beautiful elegant woman showing the final result after I-Tip keratin extensions, very long waist-length thick and shiny {hair_color} hair flowing naturally. Luxurious long hair reaching her waist or hips, healthy shine, realistic texture.

Soft glamour lighting, luxurious hair texture, photorealistic, clean bright background, horizontal format 1200x630."""
    
    elif is_tape:
        if is_installation or image_type == "content":
            # TAPE-IN - Processus de pose sandwich
            prompt = f"""Ultra realistic photograph of a beautiful woman getting professional Tape-in hair extensions installed. Elegant feminine model with {hair_color} hair, showing the sandwich application technique with thin adhesive tape extensions being pressed together.

Very long, thick waist-length hair as the final result, smooth and sleek appearance. Focus on the thin seamless tape bonds and the beautiful long hair transformation.

Bright modern salon, soft natural lighting, photorealistic 8K detail, horizontal 1200x630 composition."""
        else:
            # TAPE-IN - Résultat final
            prompt = f"""Beautiful elegant woman with smooth sleek Tape-in hair extensions result, very long waist-length {hair_color} hair flowing naturally. Thick, voluminous, seamless blend, healthy shine.

The hair must reach her waist or lower back, luxurious and natural-looking. Soft glamour lighting, clean background, photorealistic, horizontal 1200x630."""
    
    elif is_genius:
        if is_installation or image_type == "content":
            # GENIUS WEFT - Processus de couture
            prompt = f"""Ultra realistic photograph of a beautiful woman getting Genius Weft extensions installed in a luxury salon. Elegant feminine model, showing the ultra-thin 0.78mm weft being sewn onto a beaded row near the scalp.

Very long waist-length {hair_color} hair as the final result, seamless thin weft blending perfectly. Focus on the professional sewing technique and the luxurious long hair transformation.

Clean modern salon, soft natural lighting, photorealistic 8K detail, horizontal 1200x630 composition."""
        else:
            # GENIUS WEFT - Résultat final
            prompt = f"""Beautiful elegant woman with Genius Weft extensions result, very long waist-length {hair_color} hair, sleek and seamless. Ultra-thin invisible weft, thick voluminous hair reaching her waist or hips.

Sophisticated luxury appearance, healthy shine, natural movement. Soft glamour lighting, clean background, photorealistic, horizontal 1200x630."""
    
    elif is_halo:
        if is_installation or image_type == "content":
            # HALO - Pose simple
            prompt = f"""Ultra realistic photograph of a beautiful woman putting on a Halo wire hair extension. Elegant feminine model positioning the invisible wire on her head, showing the instant volume transformation.

Very long waist-length {hair_color} hair flowing down, thick and voluminous. Focus on the ease of application and the dramatic long hair result.

Bright lifestyle setting, soft natural lighting, photorealistic, horizontal 1200x630 composition."""
        else:
            # HALO - Résultat final
            prompt = f"""Beautiful elegant woman wearing Halo wire extensions, very long waist-length {hair_color} hair with instant volume. Invisible wire hidden, thick voluminous hair reaching her waist or hips, natural movement.

Effortless glamour, luxury lifestyle feel, healthy shine. Soft lighting, aspirational setting, photorealistic, horizontal 1200x630."""
    
    elif is_entretien:
        # ENTRETIEN - Cheveux bien entretenus
        prompt = f"""Beautiful elegant woman with perfectly maintained very long hair extensions, waist-length {hair_color} hair that is healthy, shiny and voluminous. The result of proper care - gorgeous flowing long hair.

Showing the beautiful texture and shine of well-maintained extensions. Optional: luxury hair care products elegantly displayed.

Soft natural lighting, clean bright background, photorealistic, horizontal 1200x630."""
    
    elif is_tendances:
        # TENDANCES - Style moderne
        prompt = f"""Fashion-forward beautiful woman with trendy very long {hair_color} hair extensions, waist-length modern styling with balayage or ombre effect. Contemporary 2026 hair trend, thick voluminous flowing hair.

Editorial fashion photography feel, Instagram-worthy long hair result. Stylish and aspirational, horizontal 1200x630."""
    
    elif is_comparison:
        # COMPARATIF - Résultat premium
        prompt = f"""Beautiful elegant woman with very long luxurious {hair_color} hair extensions reaching her waist. Premium quality result showing thick, voluminous, healthy hair. Comparison-ready: perfect example of high-end extension result.

Clean studio background, professional beauty photography, soft lighting, horizontal 1200x630."""
    
    else:
        # GÉNÉRAL - Femme avec cheveux très longs style Pinterest
        prompt = f"""Beautiful confident feminine woman with very long luxurious {hair_color} hair extensions reaching her waist or hips. Thick, voluminous, healthy shiny hair flowing naturally with beautiful movement.

The hair is the absolute hero of the image - long, beautiful, flowing. Premium extension result, aspirational lifestyle feel.

Soft glamour lighting, clean bright background, photorealistic 8K quality, horizontal 1200x630 composition."""

    # =====================================================
    # AJOUT DES RÈGLES STRICTES ANTI-HOMMES (FIN DU PROMPT)
    # =====================================================
    
    strict_rules = """

Strict rule: ONLY beautiful feminine woman, absolutely no male person or masculine features in the image. No men, no beards, no masculine jawlines. Hair must be very long (minimum waist length), no short hair, no pixie cut, no bob. No brushes, no combs, no styling tools. Photorealistic only, no cartoon, no illustration, no text, no watermark."""

    if focus_product:
        strict_rules += f" Featured Luxura product: {focus_product}."

    return prompt.strip() + strict_rules


# =====================================================
# GÉNÉRATION D'IMAGE AVEC DALL-E (V2 AMÉLIORÉE)
# =====================================================

async def generate_blog_image_with_dalle(
    category: str,
    blog_title: str,
    keywords: List[str] = None,
    focus_product: str = None,
    image_type: str = "cover",
    custom_prompt: str = None
) -> Optional[bytes]:
    """
    Génère une image unique avec DALL-E basée sur le CONTEXTE COMPLET du blog.
    
    CHANGEMENT V2: Utilise maintenant blog_title, keywords, focus_product
    pour générer des images PERTINENTES au contenu.
    
    Args:
        category: Catégorie du blog (halo, genius, tape, etc.)
        blog_title: TITRE du blog (CRUCIAL pour le contexte)
        keywords: Liste de mots-clés SEO du blog
        focus_product: Produit Luxura mis en avant
        image_type: "cover" pour image de couverture, "content" pour article
        custom_prompt: Prompt personnalisé optionnel (override)
    
    Returns:
        bytes de l'image générée ou None si échec
    """
    if not EMERGENT_LLM_KEY:
        logger.error("EMERGENT_LLM_KEY not configured")
        return None
    
    try:
        from emergentintegrations.llm.openai.image_generation import OpenAIImageGeneration
        
        # Construire le prompt intelligent basé sur le contexte
        if custom_prompt:
            prompt = custom_prompt
        else:
            prompt = build_smart_image_prompt(
                category=category,
                blog_title=blog_title,
                keywords=keywords,
                focus_product=focus_product,
                image_type=image_type
            )
        
        logger.info(f"🎨 DALL-E [{image_type}] for: {blog_title[:50]}...")
        logger.debug(f"Prompt: {prompt[:200]}...")
        
        # Initialiser le générateur
        image_gen = OpenAIImageGeneration(api_key=EMERGENT_LLM_KEY)
        
        # Générer l'image
        images = await image_gen.generate_images(
            prompt=prompt,
            model="gpt-image-1",
            number_of_images=1
        )
        
        if images and len(images) > 0:
            logger.info(f"✅ DALL-E image generated ({len(images[0])} bytes)")
            return images[0]
        else:
            logger.error("No image returned from DALL-E")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error generating DALL-E image: {e}")
        return None


# =====================================================
# GÉNÉRATION ET UPLOAD DES 2 IMAGES (V2 AMÉLIORÉE)
# =====================================================

async def generate_and_upload_blog_images(
    api_key: str,
    site_id: str,
    category: str,
    blog_title: str,
    keywords: List[str] = None,
    focus_product: str = None
) -> Tuple[Optional[Dict], Optional[Dict]]:
    """
    Génère et upload les images de couverture ET de contenu pour un blog.
    
    CHANGEMENT V2: Passe maintenant TOUT le contexte du blog à la génération.
    
    Returns:
        Tuple (cover_image_data, content_image_data)
    """
    cover_data = None
    content_data = None
    
    logger.info(f"📸 Generating images for: {blog_title[:50]}...")
    logger.info(f"   Category: {category}, Product: {focus_product}")
    
    # 1. Générer l'image de couverture (contextualisée)
    cover_bytes = await generate_blog_image_with_dalle(
        category=category,
        blog_title=blog_title,
        keywords=keywords,
        focus_product=focus_product,
        image_type="cover"
    )
    
    if cover_bytes:
        cover_data = await upload_image_bytes_to_wix(
            api_key=api_key,
            site_id=site_id,
            image_bytes=cover_bytes,
            file_name=f"cover-{uuid.uuid4().hex[:8]}.png"
        )
        if cover_data:
            logger.info(f"   ✅ Cover uploaded: {cover_data.get('static_url', '')[:50]}...")
    
    # 2. Générer l'image de contenu (différente, contextualisée)
    content_bytes = await generate_blog_image_with_dalle(
        category=category,
        blog_title=blog_title,
        keywords=keywords,
        focus_product=focus_product,
        image_type="content"
    )
    
    if content_bytes:
        content_data = await upload_image_bytes_to_wix(
            api_key=api_key,
            site_id=site_id,
            image_bytes=content_bytes,
            file_name=f"content-{uuid.uuid4().hex[:8]}.png"
        )
        if content_data:
            logger.info(f"   ✅ Content uploaded: {content_data.get('static_url', '')[:50]}...")
    
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
    """
    Upload une image (bytes) vers Wix Media Manager.
    """
    try:
        import asyncio
        
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
                            
                            logger.info(f"✅ Image ready: {static_url[:60]}...")
                            
                            return {
                                "file_id": file_id,
                                "static_url": static_url,
                                "width": width,
                                "height": height
                            }
                    
                    await asyncio.sleep(1)
            
            logger.error("File never became READY or no file_id")
            return None
            
    except Exception as e:
        logger.error(f"Error uploading image to Wix: {e}")
        return None


# =====================================================
# FALLBACK UNSPLASH - FEMMES AVEC CHEVEUX TRÈS LONGS UNIQUEMENT
# =====================================================

FALLBACK_UNSPLASH_IMAGES = {
    "general": [
        # Femmes avec cheveux TRÈS LONGS - PAS de salon, PAS de brushing
        "https://images.unsplash.com/photo-1519699047748-de8e457a634e?w=1200&h=630&fit=crop",  # Femme cheveux longs
        "https://images.unsplash.com/photo-1529626455594-4ff0802cfb7e?w=1200&h=630&fit=crop",  # Femme cheveux longs glamour
        "https://images.unsplash.com/photo-1531746020798-e6953c6e8e04?w=1200&h=630&fit=crop",  # Portrait femme cheveux longs
        "https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=1200&h=630&fit=crop",  # Femme cheveux bruns longs
        "https://images.unsplash.com/photo-1508214751196-bcfd4ca60f91?w=1200&h=630&fit=crop",  # Portrait femme élégante
    ]
}

_fallback_index = 0

def get_fallback_unsplash_image() -> str:
    """Retourne une image Unsplash de fallback (cheveux longs uniquement)."""
    global _fallback_index
    images = FALLBACK_UNSPLASH_IMAGES["general"]
    image = images[_fallback_index % len(images)]
    _fallback_index += 1
    return image
