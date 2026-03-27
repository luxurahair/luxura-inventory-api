# services/video_brief_generator.py
"""
Génération des briefs vidéo pour Runway/Kling
Version V1 - Structure de base
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Modes vidéo supportés
VIDEO_MODES = {
    "installation_halo_wire",
    "installation_halo",
    "installation_itip_bead", 
    "installation_itip",
    "installation_tape_sandwich",
    "installation_tape",
    "installation_genius_sewn",
    "installation_genius",
    "installation_pro",
    "lifestyle_result",
    "editorial_lifestyle",
    "result_natural"
}


def should_generate_video(video_brief: Dict) -> bool:
    """
    Détermine si une vidéo doit être générée pour ce brief.
    Pour l'instant, on génère pour les installations et lifestyle.
    """
    mode = video_brief.get("video_mode", "none")
    
    # Activer pour les installations et lifestyle
    return mode.startswith("installation_") or mode in ("lifestyle_result", "editorial_lifestyle", "result_natural")


def generate_video_brief(blog_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Génère un brief vidéo basé sur le contenu du blog.
    
    FAL.AI/Kling supporte uniquement 5 ou 10 secondes.
    """
    text = " ".join([
        str(blog_data.get("title", "")),
        str(blog_data.get("excerpt", "")),
        str(blog_data.get("content", ""))[:500]
    ]).lower()
    
    product = blog_data.get("focus_product", "extensions Luxura")
    category = blog_data.get("category", "general")
    
    # Détecter le mode vidéo
    # IMPORTANT: On montre le RÉSULTAT, pas l'installation (trop difficile pour l'IA)
    if "halo" in text or "fil invisible" in text or category == "halo":
        mode = "installation_halo"
        # Montrer le RÉSULTAT glamour, pas la pose technique
        scene = f"Stunning woman with extremely long flowing hair gently moving in soft breeze. She touches her beautiful voluminous hair with confidence. Cinematic beauty shot, golden hour lighting, elegant lifestyle moment."
        motion = "gentle hair flow in breeze, soft natural movement, confident hair touch"
        
    elif "i-tip" in text or "microbille" in text or category == "itip":
        mode = "installation_itip"
        scene = f"Beautiful woman showing off her gorgeous very long thick hair after professional i-tip extension installation. She runs her fingers through her luxurious hair. Salon mirror visible, satisfied smile."
        motion = "fingers running through long hair, natural shine, confident reveal"
        
    elif "tape" in text or "sandwich" in text or category == "tape":
        mode = "installation_tape"
        scene = f"Elegant woman with stunning long silky hair after tape-in extensions. Natural hair movement, premium salon result, she admires her transformation in mirror."
        motion = "silky hair movement, mirror admiration, gentle head turn"
        
    elif "genius" in text or "weft" in text or category == "genius":
        mode = "installation_genius"
        scene = f"Sophisticated woman showcasing her incredible long thick hair after genius weft installation. Cinematic beauty shot, she touches her voluminous hair with amazement."
        motion = "voluminous hair flow, amazed expression, luxurious texture showcase"
        
    else:
        mode = "lifestyle_result"
        scene = f"Beautiful woman with extremely long flowing {product} hair, natural movement, glamorous lifestyle moment"
        motion = "natural hair flow, confident movement, cinematic beauty"

    return {
        "video_mode": mode,
        "duration_seconds": 5,  # FAL.AI/Kling: seulement 5 ou 10 secondes
        "aspect_ratio": "16:9",
        "scene": scene,
        "motion": motion,
        "style": "cinematic realistic beauty video, natural lighting, premium hair quality",
        "use_image_to_video": True,
        "is_technical": mode.startswith("installation_")
    }


def generate_video_brief(blog_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Génère un brief vidéo basé sur le contenu du blog.
    
    Le brief contient:
    - video_mode: type de vidéo (installation, lifestyle, etc.)
    - scene: description de la scène
    - motion: type de mouvement
    - duration_seconds: durée cible
    - aspect_ratio: format vidéo
    """
    text = " ".join([
        str(blog_data.get("title", "")),
        str(blog_data.get("excerpt", "")),
        str(blog_data.get("content", ""))[:500]  # Limiter pour performance
    ]).lower()
    
    product = blog_data.get("focus_product", "extensions Luxura")
    category = blog_data.get("category", "general")
    
    # Détecter le mode vidéo
    if "halo" in text or "fil invisible" in text or category == "halo":
        mode = "installation_halo_wire"
        scene = f"Simple and elegant demonstration of Halo extension. Woman placing invisible wire halo on her head in one smooth motion at home. Natural lighting, clean background."
        motion = "Single fluid motion of placing halo, gentle hair fall, natural movement"
        
    elif "i-tip" in text or "microbille" in text or category == "itip":
        mode = "installation_itip_bead"
        scene = f"Professional close-up of I-Tip micro-bead installation. Stylist hands using pliers to carefully clamp silicone-lined microbead onto natural hair strand."
        motion = "Precise clamping motion, slow-motion detail of bead closing"
        
    elif "tape" in text or "sandwich" in text or "adhésive" in text or category == "tape":
        mode = "installation_tape_sandwich"
        scene = f"Clean demonstration of Tape-in sandwich method. Two adhesive wefts being aligned and pressed together with natural hair section in between."
        motion = "Smooth pressing motion, adhesive strips meeting, hair settling"
        
    elif "genius" in text or "weft" in text or "couture" in text or "rangée perlée" in text or category == "genius":
        mode = "installation_genius_sewn"
        scene = f"Detailed demonstration of Genius Weft sewing technique. Stylist sewing ultra-thin weft onto beaded row track, visible silicone beads and precise stitching."
        motion = "Sewing needle moving through weft, thread pulling, final secure attachment"
        
    elif any(k in text for k in ["soirée", "fille", "amies", "girls night"]):
        mode = "editorial_lifestyle"
        scene = f"Group of elegant women with extremely long luxurious hair extensions enjoying a glamorous girls night. Warm candlelight, toasting champagne, beautiful flowing hair."
        motion = "Natural hair flow, gentle head turns, joyful interaction"
        
    else:
        mode = "result_natural"
        scene = f"Beautiful woman with very long flowing {product} hair extensions. Natural movement showing hair quality and shine."
        motion = "Gentle hair flow, natural movement, texture showcase"
    
    # Règles de sécurité strictes
    safety_rules = """
STRICT VIDEO RULES:
- ONLY beautiful feminine women with EXTREMELY LONG hair (waist to hip length)
- NO men, NO short hair, NO masculine features
- Professional quality, cinematic lighting
- No text overlays in the video
"""
    
    return {
        "video_mode": mode,
        "category": category,
        "product": product,
        "duration_seconds": 18,  # Runway Gen-3 optimal
        "aspect_ratio": "9:16",  # Format Reels/TikTok
        "scene": scene.strip(),
        "motion": motion.strip(),
        "style": "cinematic realistic beauty video, natural lighting, high detail on hair texture and movement",
        "safety_rules": safety_rules.strip(),
        "use_image_to_video": True,
        "is_technical": mode.startswith("installation_")
    }
