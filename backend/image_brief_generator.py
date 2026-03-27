# image_brief_generator.py
"""
Module responsable de créer un brief visuel intelligent à partir du contenu du blog.
Il décide QUOI montrer avant que l'image ne soit générée.
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def _detect_visual_mode(blog_data: Dict[str, Any]) -> str:
    """Détecte le type d'image le plus adapté selon le contenu du blog"""
    text = " ".join([
        str(blog_data.get("title", "")),
        str(blog_data.get("excerpt", "")),
        str(blog_data.get("content", "")),
    ]).lower()

    # Articles techniques (installation, pose, étapes)
    if any(k in text for k in ["installation", "pose", "étape", "tutoriel", "comment", "microbilles", "adhésif", "sandwich", "kératine", "couture"]):
        return "installation_pro"

    # Articles d'entretien / soins / durée
    if any(k in text for k in ["entretien", "soins", "durée", "repositionnement", "brosse", "shampoing", "sans sulfate"]):
        return "result_maintenance"

    # Articles lifestyle / soirée / look
    if any(k in text for k in ["soirée", "fille", "amies", "soiree", "girls night", "table", "dîner", "élégant", "glamour"]):
        return "editorial_lifestyle"

    # Par défaut : résultat naturel
    return "result_natural"


def generate_image_brief(blog_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Génère un brief visuel structuré basé sur le contenu réel du blog.
    C'est ici qu'on décide du style (soirée de filles OU installation technique).
    """
    mode = _detect_visual_mode(blog_data)
    category = blog_data.get("category", "general")
    product = blog_data.get("focus_product", "extensions capillaires")

    logger.info(f"📋 Brief Generator - Mode détecté: {mode} pour catégorie: {category}")

    if mode == "installation_pro":
        cover_scene = f"close-up professionnel et élégant de l'installation de {product} dans un salon moderne et lumineux. Mains de coiffeuse visible, sectionnement propre, focus sur la technique précise."
        content_scene = f"détail technique de la pose {product} : adhésif, microbeads ou couture selon la méthode, rendu propre et professionnel."
    
    elif mode == "editorial_lifestyle":
        cover_scene = f"groupe de 4 à 5 femmes élégantes en soirée chic autour d'une belle table, riant, complices, toasts avec des verres de vin, ambiance chaleureuse et joyeuse. Toutes ont de très longs cheveux luxueux."
        content_scene = f"femme souriante touchant ses très longs cheveux volumineux, ambiance intime et féminine lors d'une soirée entre amies."
    
    elif mode == "result_maintenance":
        cover_scene = f"belles femmes élégantes montrant leurs cheveux très longs, sains et brillants après un bon entretien, ambiance chaleureuse et naturelle."
        content_scene = f"close-up sur la texture brillante et le mouvement naturel de cheveux très longs bien entretenus."
    
    else:  # result_natural
        cover_scene = f"belle femme élégante avec de très longs cheveux volumineux et naturels grâce aux {product}, résultat réaliste, lumineux et premium."
        content_scene = f"focus sur la qualité et le mouvement des très longs cheveux après pose {product}."

    brief = {
        "brand": "Luxura Distribution",
        "category": category,
        "product": product,
        "visual_mode": mode,
        "cover": {
            "scene": cover_scene,
            "style": "luxury beauty lifestyle photography, soft warm lighting, elegant composition",
            "focus": "cheveux très longs, volume naturel, qualité premium, émotion",
            "avoid": ["texte dans l'image", "watermark", "homme", "cheveux courts", "style cartoon", "trop artificiel"]
        },
        "content": {
            "scene": content_scene,
            "style": "editorial or technical beauty shot",
            "focus": "résultat naturel ou détail technique selon le sujet",
            "avoid": ["texte", "watermark", "cheveux courts"]
        },
        "logo_overlay": True,
        "hair_length_rule": "extremely long hair on every woman - minimum waist length, preferably hip length"
    }

    logger.info(f"   Cover scene: {cover_scene[:80]}...")
    logger.info(f"   Content scene: {content_scene[:80]}...")

    return brief
