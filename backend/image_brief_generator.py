# image_brief_generator.py - V8 (Technique réaliste + Soirée de filles seulement quand pertinent)

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

def _detect_visual_mode(blog_data: Dict[str, Any]) -> str:
    text = " ".join([str(blog_data.get(k, "")) for k in ["title", "excerpt", "content"]]).lower()
    category = str(blog_data.get("category", "")).lower()

    # === TECHNIQUES D'INSTALLATION (priorité maximale) ===
    if any(k in text for k in ["installation", "pose", "étape", "tutoriel", "comment poser", "microbille", "sandwich", "couture", "rangée perlée", "beaded row"]):
        if category == "halo" or "fil invisible" in text or "halo" in text:
            return "installation_halo_wire"
        elif category == "itip" or "i-tip" in text or "microbille" in text:
            return "installation_itip_bead"
        elif category == "tape" or "tape-in" in text or "sandwich" in text or "adhésive" in text:
            return "installation_tape_sandwich"
        elif category == "genius" or "weft" in text or "trame" in text or "cousue" in text:
            return "installation_genius_sewn"
        else:
            return "installation_pro"

    # === Lifestyle seulement si l'article parle de soirée / résultat / entretien ===
    if any(k in text for k in ["soirée", "fille", "amies", "girls night", "table", "dîner", "soiree"]):
        return "editorial_lifestyle"

    if any(k in text for k in ["entretien", "soins", "durée", "résultat"]):
        return "result_maintenance"

    return "result_natural"


def generate_image_brief(blog_data: Dict[str, Any]) -> Dict[str, Any]:
    mode = _detect_visual_mode(blog_data)
    category = blog_data.get("category", "general")
    product = blog_data.get("focus_product", "extensions Luxura")

    logger.info(f"📸 Brief V8 - Mode détecté : {mode} | Produit : {product}")

    # Règle de sécurité ultra-stricte (ajoutée à la fin du prompt)
    safety = """
STRICT RULES - NEVER BREAK:
- ONLY beautiful feminine women
- Hair on EVERY woman must be EXTREMELY LONG (waist or hip length minimum)
- NO short hair, NO bob, NO shoulder length on any woman
- NO men, NO masculine features
- Photorealistic only, no cartoon, no text, no watermark
"""

    if mode.startswith("installation_"):
        # === PROMPTS TECHNIQUES RÉALISTES ===
        if mode == "installation_halo_wire":
            cover = f"Realistic close-up of easy Halo extension installation. Woman putting on invisible wire halo in one single motion at home. No salon needed. Natural light, documentary style."
            content = f"Detail of Halo wire being placed on head - simple, quick, non-permanent application. Real hands, real technique."
        elif mode == "installation_itip_bead":
            cover = f"Professional close-up of I-Tip micro-bead installation. Stylist hands using pliers to clamp silicone-lined microbead on natural hair. Individual strand, precise technique, documentary style."
            content = f"Extreme close-up of micro-bead being flattened with pliers on I-Tip keratin strand."
        elif mode == "installation_tape_sandwich":
            cover = f"Realistic close-up of Tape-in sandwich method. Two adhesive wefts being pressed together with natural hair in between. Clean section, professional hands, documentary style."
            content = f"Detail of tape sandwich application showing adhesive strips and hair placement."
        elif mode == "installation_genius_sewn":
            cover = f"Realistic close-up of Genius Weft sewing technique. Stylist sewing ultra-thin weft onto beaded row track. Visible silicone beads and thread, precise stitching, documentary style."
            content = f"Detail of beaded row with Genius Weft being sewn - invisible and secure method."
        else:
            cover = f"Professional close-up of {product} installation technique. Clean, precise, educational documentary style."
            content = f"Technical detail of {product} attachment method."

        cover += safety
        content += safety

    elif mode == "editorial_lifestyle":
        cover = f"Group of 4-5 elegant women at a chic girls night dinner. Warm candlelight, smiling, toasting. ALL have extremely long, thick, luxurious hair extensions reaching waist or hips."
        content = f"Close moment between girlfriends admiring each other's very long beautiful hair."
        cover += safety
        content += safety

    else:
        cover = f"Elegant woman showing healthy, shiny, very long hair with {product}. Natural lighting, premium beauty photography."
        content = f"Close-up on texture and shine of long luxurious hair."
        cover += safety
        content += safety

    return {
        "visual_mode": mode,
        "category": category,
        "product": product,
        "cover": {"scene": cover.strip(), "style": "professional realistic photography"},
        "content": {"scene": content.strip(), "style": "close-up realistic photography"},
        "is_technical": mode.startswith("installation_")
    }
