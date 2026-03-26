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
# RÈGLES BUSINESS LUXURA - OBLIGATOIRES
# =====================================================

LUXURA_BASE_RULES = """
Professional luxury hair extension photography for Luxura Distribution Quebec Canada.

MANDATORY REQUIREMENTS:
- Long or mid-length hair ONLY (minimum shoulder length)
- Visible hair extensions or visible premium salon result
- Premium luxury salon environment
- Elegant realistic woman (not cartoon, not mannequin unless training article)
- French Canadian luxury beauty market aesthetic
- Soft professional lighting
- Clean composition

STRICTLY FORBIDDEN:
- Short hair (no pixie cut, no bob haircut, no ear-length hair)
- Mannequin head unless explicitly training/formation article
- Text or watermarks in image
- Cartoon or illustration style
- Multiple people unless article specifically requires it
- Dark or moody lighting
- Messy or unprofessional appearance
- Fashion editorial without visible extensions
- Abstract or artistic compositions
"""

# =====================================================
# RÈGLES VISUELLES PAR CATÉGORIE
# =====================================================

CATEGORY_VISUAL_RULES = {
    "genius": {
        "must_have": ["long flowing hair", "seamless weft visible", "premium salon finish", "natural luxury result", "thin invisible weft"],
        "avoid": ["short hair", "pixie", "bob", "fashion-only portrait", "clip-in visible"],
        "style": "sophisticated professional salon result"
    },
    "halo": {
        "must_have": ["very long hair", "natural blend", "soft glamour", "invisible wire look", "instant volume"],
        "avoid": ["short hair", "technical salon tools visible", "application process"],
        "style": "effortless glamour, ready-to-wear luxury"
    },
    "tape": {
        "must_have": ["smooth sleek hair", "salon application implied", "adhesive bands technique", "sandwich method"],
        "avoid": ["curly messy editorial", "visible tape edges poorly done"],
        "style": "sleek professional salon finish"
    },
    "itip": {
        "must_have": ["natural strand-by-strand result", "keratin fusion visible", "individual bonds", "seamless blend"],
        "avoid": ["bulky bonds", "visible keratin tips poorly done"],
        "style": "ultra-natural strand integration"
    },
    "formation": {
        "must_have": ["trainer/educator", "real model with long hair", "education setting", "premium salon classroom", "demonstration"],
        "avoid": ["plastic mannequin only", "short hair model", "runway fashion", "no context"],
        "style": "professional education premium environment"
    },
    "entretien": {
        "must_have": ["healthy shiny hair", "care routine implied", "premium products", "maintenance result"],
        "avoid": ["damaged hair", "before photo only"],
        "style": "healthy maintained luxury hair"
    },
    "tendances": {
        "must_have": ["trendy styling", "modern look", "fashion-forward", "2025 hair trends"],
        "avoid": ["dated styles", "basic plain look"],
        "style": "contemporary fashion-forward beauty"
    },
    "general": {
        "must_have": ["long beautiful hair", "premium result", "elegant woman", "salon quality"],
        "avoid": ["short hair", "unprofessional"],
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
# CONSTRUCTEUR DE PROMPT INTELLIGENT
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
    Construit un prompt intelligent basé sur le TITRE du blog,
    les MOTS-CLÉS et le PRODUIT focus.
    
    C'est la fonction clé qui résout le problème des images génériques.
    """
    title_lower = (blog_title or "").lower()
    keywords = keywords or []
    hair_color = hair_color or get_next_hair_color()
    
    # Récupérer les règles de la catégorie
    cat_rules = CATEGORY_VISUAL_RULES.get(category, CATEGORY_VISUAL_RULES["general"])
    
    # =====================================================
    # DÉTECTION DU TYPE D'ARTICLE BASÉ SUR LE TITRE
    # =====================================================
    
    is_formation = any(word in title_lower for word in ["formation", "training", "apprendre", "cours", "maîtriser", "technique"])
    is_installation = any(word in title_lower for word in ["installation", "pose", "poser", "appliquer", "application"])
    is_guide = any(word in title_lower for word in ["guide", "comment", "tutoriel", "étapes", "méthode"])
    is_comparison = any(word in title_lower for word in ["vs", "versus", "comparatif", "comparaison", "différence"])
    is_entretien = any(word in title_lower for word in ["entretien", "soins", "entretenir", "durée", "prolonger"])
    is_tendances = any(word in title_lower for word in ["tendance", "2025", "mode", "style", "balayage", "ombré"])
    is_salon = any(word in title_lower for word in ["salon", "professionnel", "coiffeur", "partenaire"])
    is_halo = "halo" in title_lower
    is_genius = "genius" in title_lower or "weft" in title_lower
    is_tape = "tape" in title_lower or "adhésive" in title_lower or "bande" in title_lower
    is_itip = "i-tip" in title_lower or "kératine" in title_lower or "itip" in title_lower
    
    # =====================================================
    # CONSTRUCTION DU PROMPT SELON LE CONTEXTE
    # =====================================================
    
    if is_formation or is_installation:
        # Articles de formation / installation
        product_name = "hair extensions"
        if is_genius: product_name = "Genius Weft extensions"
        elif is_tape: product_name = "Tape-in extensions"
        elif is_itip: product_name = "I-Tip keratin extensions"
        elif is_halo: product_name = "Halo extensions"
        
        if image_type == "cover":
            scene = f"""
Professional luxury salon training scene in Quebec Canada.
Expert hair stylist educator demonstrating {product_name} installation technique
on a real female model with long {hair_color} hair.
Visible seamless extension result, premium salon classroom atmosphere,
clean beauty composition, educational but luxurious setting.
Horizontal 1200x630 cover image composition.
Model facing camera or 3/4 angle, confident professional look.
"""
        else:
            scene = f"""
Close-up professional beauty photo of skilled hands installing {product_name}
on a real model with long {hair_color} hair.
Detailed technique demonstration, seamless blend visible,
premium salon training environment, high detail realistic photography.
"""
    
    elif is_comparison:
        # Articles comparatifs (vs)
        if image_type == "cover":
            scene = f"""
Split composition showing two elegant women with long {hair_color} hair,
each demonstrating different hair extension techniques.
Premium salon result comparison, both looking luxurious and natural.
Clean professional beauty photography, horizontal 1200x630 format.
"""
        else:
            scene = f"""
Side-by-side detail of two different hair extension techniques
on models with long {hair_color} hair.
Professional comparison photography, visible difference in application method.
"""
    
    elif is_entretien:
        # Articles entretien / soins
        if image_type == "cover":
            scene = f"""
Beautiful woman with long healthy {hair_color} hair extensions,
showing the result of proper care and maintenance.
Shiny, voluminous, well-maintained premium hair.
Soft lighting, luxury beauty portrait, horizontal 1200x630.
Optional: premium hair care products subtly visible.
"""
        else:
            scene = f"""
Close-up of healthy, shiny long {hair_color} hair extensions
being gently brushed or cared for.
Premium hair texture detail, professional care routine implied.
"""
    
    elif is_tendances:
        # Articles tendances
        if image_type == "cover":
            scene = f"""
Fashion-forward woman with trendy long {hair_color} hair extensions,
modern 2025 hairstyle, balayage or ombre effect if applicable.
Contemporary luxury beauty portrait, editorial quality.
Horizontal 1200x630, stylish but professional.
"""
        else:
            scene = f"""
Detail shot of trendy hair extension styling,
modern texture and color technique on long {hair_color} hair.
Fashion-forward beauty photography.
"""
    
    elif is_salon:
        # Articles salon / professionnel
        if image_type == "cover":
            scene = f"""
Luxurious modern hair salon interior in Quebec,
professional stylist with client showing beautiful long {hair_color} hair extensions result.
Premium atmosphere, elegant decor, satisfied client.
Horizontal 1200x630 professional photography.
"""
        else:
            scene = f"""
Interior of premium hair extension salon,
stylist working on client with long {hair_color} hair.
Professional service environment, luxury atmosphere.
"""
    
    elif is_halo:
        # Articles Halo spécifiques
        if image_type == "cover":
            scene = f"""
Glamorous woman with very long flowing {hair_color} Halo hair extensions,
invisible wire perfectly hidden, instant volume and length.
Effortless luxury beauty, soft glamour portrait.
Natural movement in hair, horizontal 1200x630.
"""
        else:
            scene = f"""
Detail of Halo extension invisible wire blending seamlessly
with long {hair_color} natural hair.
Volume and length transformation, premium result.
"""
    
    elif is_genius:
        # Articles Genius Weft spécifiques
        if image_type == "cover":
            scene = f"""
Sophisticated woman with long sleek {hair_color} Genius Weft extensions,
ultra-thin 0.78mm weft invisible at the scalp.
Premium salon finish, natural luxury result.
Professional portrait, horizontal 1200x630.
"""
        else:
            scene = f"""
Close-up of Genius Weft thin weft installation,
seamless integration with long {hair_color} hair.
Invisible couture technique detail.
"""
    
    elif is_tape:
        # Articles Tape-in spécifiques
        if image_type == "cover":
            scene = f"""
Elegant woman with smooth long {hair_color} Tape-in hair extensions,
sleek professional salon finish, sandwich application result.
Premium beauty portrait, horizontal 1200x630.
"""
        else:
            scene = f"""
Detail of Tape-in extension adhesive band application,
seamless blend with long {hair_color} hair.
Professional technique close-up.
"""
    
    elif is_itip:
        # Articles I-Tip spécifiques
        if image_type == "cover":
            scene = f"""
Natural-looking woman with long {hair_color} I-Tip keratin extensions,
strand-by-strand fusion result, ultra-natural blend.
Premium beauty portrait showing hair movement and texture.
Horizontal 1200x630.
"""
        else:
            scene = f"""
Close-up of I-Tip keratin fusion bonds,
individual strands blending with long {hair_color} natural hair.
Professional technique detail.
"""
    
    else:
        # Articles généraux
        if image_type == "cover":
            scene = f"""
Beautiful confident woman with long luxurious {hair_color} hair extensions,
premium salon quality finish, healthy shine and volume.
Elegant beauty portrait, soft professional lighting.
Horizontal 1200x630 cover composition.
"""
        else:
            scene = f"""
Detail shot of beautiful long {hair_color} hair extensions,
premium texture and shine, professional result.
"""
    
    # =====================================================
    # AJOUT DU PRODUIT FOCUS SI SPÉCIFIÉ
    # =====================================================
    
    if focus_product:
        scene += f"\nFeatured Luxura product: {focus_product}."
    
    # =====================================================
    # AJOUT DES MOTS-CLÉS COMME THÈME VISUEL
    # =====================================================
    
    if keywords:
        # Filtrer les mots-clés pertinents pour l'image
        visual_keywords = [k for k in keywords[:5] if not any(skip in k.lower() for skip in ['québec', 'montréal', 'canada', 'prix', 'acheter'])]
        if visual_keywords:
            scene += f"\nVisual theme: {', '.join(visual_keywords)}."
    
    # =====================================================
    # ASSEMBLAGE FINAL
    # =====================================================
    
    # Ajouter les règles de la catégorie
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
no text, no watermark, professional beauty photography.
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
