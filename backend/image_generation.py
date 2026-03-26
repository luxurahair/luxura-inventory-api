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
# CONSTRUCTEUR DE PROMPT INTELLIGENT - DISTRIBUTEUR
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
    Construit un prompt intelligent pour LUXURA DISTRIBUTION.
    
    LUXURA = Importateur/Distributeur de produits haut de gamme
    - Vend aux salons professionnels (B2B)
    - Vend en ligne aux consommateurs (B2C)
    - NE FAIT PAS de formation
    
    Focus: RÉSULTAT du produit, beauté, qualité premium
    """
    title_lower = (blog_title or "").lower()
    keywords = keywords or []
    hair_color = hair_color or get_next_hair_color()
    
    # Récupérer les règles de la catégorie
    cat_rules = CATEGORY_VISUAL_RULES.get(category, CATEGORY_VISUAL_RULES["general"])
    
    # =====================================================
    # DÉTECTION DU TYPE D'ARTICLE
    # =====================================================
    
    is_guide = any(word in title_lower for word in ["guide", "comment", "tutoriel", "étapes", "méthode", "choisir"])
    is_comparison = any(word in title_lower for word in ["vs", "versus", "comparatif", "comparaison", "différence"])
    is_entretien = any(word in title_lower for word in ["entretien", "soins", "entretenir", "durée", "prolonger"])
    is_tendances = any(word in title_lower for word in ["tendance", "2025", "mode", "style", "balayage", "ombré"])
    is_achat = any(word in title_lower for word in ["acheter", "prix", "commander", "qualité", "meilleur"])
    is_halo = "halo" in title_lower
    is_genius = "genius" in title_lower or "weft" in title_lower
    is_tape = "tape" in title_lower or "adhésive" in title_lower or "bande" in title_lower
    is_itip = "i-tip" in title_lower or "kératine" in title_lower or "itip" in title_lower
    
    # =====================================================
    # CONSTRUCTION DU PROMPT - FOCUS RÉSULTAT/PRODUIT
    # =====================================================
    
    if is_comparison:
        # Articles comparatifs - montrer les deux résultats
        if image_type == "cover":
            scene = f"""
Stunning FEMININE WOMAN with VERY LONG flowing {hair_color} hair extensions reaching her waist.
Gorgeous female model showing THE RESULT - beautiful long luxurious hair.
Hair must be waist-length or longer, thick and voluminous.
NO brushes, NO styling tools, NO salon scene.
Bright professional lighting, horizontal 1200x630 cover image.
"""
        else:
            scene = f"""
Beautiful FEMININE WOMAN showing her VERY LONG {hair_color} hair extensions.
Hair flowing down to waist or lower back, thick and luxurious.
NO styling, NO brushing - just showing the beautiful long hair result.
"""
    
    elif is_entretien:
        # Articles entretien - montrer le résultat de bons soins
        if image_type == "cover":
            scene = f"""
Stunning FEMININE WOMAN with perfectly maintained VERY LONG {hair_color} hair extensions.
Hair reaching waist or lower back, healthy, shiny, thick and voluminous.
THE RESULT of proper care - beautiful long flowing hair.
NO brushes, NO combs, NO styling tools in the image.
Soft lighting, horizontal 1200x630, luxury lifestyle.
"""
        else:
            scene = f"""
Beautiful FEMININE WOMAN showing her VERY LONG healthy {hair_color} hair extensions.
Hair flowing down past shoulders to waist, shiny and well-maintained.
NO brushing scene - just the beautiful long hair result.
"""
    
    elif is_tendances:
        # Articles tendances - montrer les styles modernes
        if image_type == "cover":
            scene = f"""
Fashion-forward FEMININE WOMAN with trendy VERY LONG {hair_color} hair extensions.
Hair reaching waist or lower, modern 2025 style, balayage or ombre.
THE RESULT - gorgeous long flowing trendy hair, not a styling scene.
NO brushes, NO styling tools, NO salon.
Horizontal 1200x630, stylish and aspirational.
"""
        else:
            scene = f"""
Beautiful FEMININE WOMAN with trendy VERY LONG {hair_color} hair extensions.
Modern style, hair flowing down to waist, thick and voluminous.
Fashion-forward beauty, Instagram-worthy long hair result.
"""
    
    elif is_achat or is_guide:
        # Articles achat/guide - montrer la qualité du produit
        if image_type == "cover":
            scene = f"""
Confident FEMININE WOMAN showcasing gorgeous VERY LONG {hair_color} hair extensions.
Hair reaching waist or lower back, thick, voluminous, luxurious.
THE RESULT of premium extensions - beautiful long flowing hair.
NO brushes, NO styling tools, NO salon scene.
Clean bright background, horizontal 1200x630.
"""
        else:
            scene = f"""
Beautiful FEMININE WOMAN with VERY LONG {hair_color} hair extensions.
Hair flowing down to waist, showing texture, shine and volume.
The beautiful result of wearing quality extensions.
"""
    
    elif is_halo:
        # Produit Halo - volume instantané, fil invisible
        if image_type == "cover":
            scene = f"""
Glamorous FEMININE WOMAN with VERY LONG flowing {hair_color} Halo hair extensions.
Hair reaching waist or hips, thick, voluminous, moving naturally.
THE RESULT of Halo extensions - instant long beautiful hair.
NO brushes, NO styling tools, NO salon scene.
Aspirational lifestyle, horizontal 1200x630.
"""
        else:
            scene = f"""
Beautiful FEMININE WOMAN with VERY LONG {hair_color} Halo extensions.
Hair flowing down past waist, showing volume and movement.
The amazing result of wearing Halo extensions.
"""
    
    elif is_genius:
        # Produit Genius Weft - trame ultra-fine
        if image_type == "cover":
            scene = f"""
Sophisticated FEMININE WOMAN with VERY LONG sleek {hair_color} Genius Weft extensions.
Hair reaching waist or lower back, thick, seamless, natural looking.
THE RESULT of Genius Weft - beautiful long luxurious hair.
NO brushes, NO styling tools, NO salon scene.
Premium lighting, horizontal 1200x630.
"""
        else:
            scene = f"""
Beautiful FEMININE WOMAN with VERY LONG {hair_color} Genius Weft extensions.
Hair flowing down to waist, showing seamless thin weft result.
Gorgeous long hair extension result.
"""
    
    elif is_tape:
        # Produit Tape-in - résultat lisse
        if image_type == "cover":
            scene = f"""
Elegant FEMININE WOMAN with smooth VERY LONG {hair_color} Tape-in hair extensions.
Hair reaching waist or lower, sleek, thick, flowing naturally.
THE RESULT of Tape-in extensions - gorgeous long smooth hair.
NO brushes, NO styling tools, NO salon scene.
Clean bright lighting, horizontal 1200x630.
"""
        else:
            scene = f"""
Beautiful FEMININE WOMAN with VERY LONG {hair_color} Tape-in extensions.
Hair flowing down to waist, smooth and seamless blend.
The beautiful result of wearing Tape-in extensions.
"""
    
    elif is_itip:
        # Produit I-Tip - fusion naturelle
        if image_type == "cover":
            scene = f"""
Natural-looking FEMININE WOMAN with VERY LONG {hair_color} I-Tip keratin extensions.
Hair reaching waist or hips, ultra-natural blend, thick and flowing.
THE RESULT of I-Tip extensions - gorgeous long natural-looking hair.
NO brushes, NO styling tools, NO salon scene.
Luxury lifestyle, horizontal 1200x630.
"""
        else:
            scene = f"""
Beautiful FEMININE WOMAN with VERY LONG {hair_color} I-Tip extensions.
Hair flowing down past waist, individual strands blending naturally.
The amazing result of wearing I-Tip extensions.
"""
    
    else:
        # Articles généraux - résultat premium
        if image_type == "cover":
            scene = f"""
Beautiful confident FEMININE WOMAN with VERY LONG luxurious {hair_color} hair extensions.
Hair reaching waist or hips, thick, voluminous, healthy shine.
THE RESULT of premium extensions - gorgeous long flowing hair.
NO brushes, NO styling tools, NO salon scene.
Aspirational lifestyle, horizontal 1200x630.
"""
        else:
            scene = f"""
Beautiful FEMININE WOMAN with VERY LONG {hair_color} hair extensions.
Hair flowing down to waist, premium texture and shine.
The stunning result of wearing quality hair extensions.
"""
    
    # =====================================================
    # AJOUT DU PRODUIT FOCUS
    # =====================================================
    
    if focus_product:
        scene += f"\nFeatured Luxura product: {focus_product}."
    
    # =====================================================
    # AJOUT DES MOTS-CLÉS VISUELS
    # =====================================================
    
    if keywords:
        visual_keywords = [k for k in keywords[:5] if not any(skip in k.lower() for skip in ['québec', 'montréal', 'canada', 'prix', 'acheter', 'salon'])]
        if visual_keywords:
            scene += f"\nVisual theme: {', '.join(visual_keywords)}."
    
    # =====================================================
    # ASSEMBLAGE FINAL
    # =====================================================
    
    must_have = ", ".join(cat_rules["must_have"][:3])
    avoid = ", ".join(cat_rules["avoid"][:3])
    
    final_prompt = f"""
{LUXURA_BASE_RULES}

SCENE DESCRIPTION:
{scene.strip()}

CATEGORY STYLE: {cat_rules['style']}
MUST INCLUDE: {must_have}
MUST AVOID: {avoid}

TECHNICAL: Ultra realistic photography, 4K quality, soft natural lighting, 
horizontal {1200 if image_type == 'cover' else 800}x{630 if image_type == 'cover' else 600} composition,
no text, no watermark, professional beauty/product photography, e-commerce ready.
"""
    
    return final_prompt.strip()


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
# FALLBACK UNSPLASH (au cas où DALL-E échoue)
# =====================================================

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
    """Retourne une image Unsplash de fallback (cheveux longs uniquement)."""
    global _fallback_index
    images = FALLBACK_UNSPLASH_IMAGES["general"]
    image = images[_fallback_index % len(images)]
    _fallback_index += 1
    return image
