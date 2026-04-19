"""
Luxura Auto Color Engine
========================
Upload simplifié : envoie juste la référence couleur,
reçois l'image recolorisée avec le gabarit + watermark.
"""

import os
import numpy as np
from PIL import Image
import io
import base64
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Import optionnel de cv2 et rembg
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    cv2 = None
    logger.warning("⚠️ OpenCV (cv2) non disponible - Auto Color Engine désactivé")

try:
    from rembg import remove
    REMBG_AVAILABLE = True
except ImportError:
    REMBG_AVAILABLE = False
    def remove(img, **kwargs):
        return img  # No-op fallback
    logger.warning("⚠️ rembg non disponible - Background removal désactivé")

# Chemin du gabarit sauvegardé
TEMPLATE_PATH = Path(__file__).parent / "templates" / "gabarit_genius.jpg"


def load_template() -> np.ndarray:
    """Charge le gabarit Genius sauvegardé."""
    if not TEMPLATE_PATH.exists():
        raise FileNotFoundError(f"Gabarit non trouvé: {TEMPLATE_PATH}")
    img = Image.open(TEMPLATE_PATH).convert('RGB')
    return np.array(img)


def improve_hair_mask(image: np.ndarray) -> np.ndarray:
    """Crée un masque cheveux précis."""
    person = remove(image)
    gray = cv2.cvtColor(np.array(person), cv2.COLOR_RGBA2GRAY)
    _, person_mask = cv2.threshold(gray, 30, 255, cv2.THRESH_BINARY)

    hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
    skin_mask1 = cv2.inRange(hsv, (0, 20, 70), (20, 255, 255))
    skin_mask2 = cv2.inRange(hsv, (340, 20, 70), (180, 255, 255))
    skin_mask = skin_mask1 | skin_mask2

    hair_mask = cv2.bitwise_and(person_mask, cv2.bitwise_not(skin_mask))
    
    kernel = np.ones((5, 5), np.uint8)
    hair_mask = cv2.morphologyEx(hair_mask, cv2.MORPH_CLOSE, kernel)
    hair_mask = cv2.morphologyEx(hair_mask, cv2.MORPH_OPEN, kernel)
    
    return hair_mask


def extract_color_profile(reference: np.ndarray) -> dict:
    """Extrait le profil couleur complet de la référence (teinte, sat, ombré)."""
    ref_person = remove(reference)
    ref_hsv = cv2.cvtColor(reference, cv2.COLOR_RGB2HSV)
    ref_lab = cv2.cvtColor(reference, cv2.COLOR_RGB2LAB)
    ref_gray = cv2.cvtColor(np.array(ref_person), cv2.COLOR_RGBA2GRAY)
    _, ref_hair = cv2.threshold(ref_gray, 30, 255, cv2.THRESH_BINARY)
    
    if np.sum(ref_hair > 0) == 0:
        return {"l_top": 80, "l_bottom": 200, "a_avg": 128, "b_avg": 128}
    
    height = reference.shape[0]
    
    # Diviser en sections pour analyser l'ombré
    top_mask = ref_hair[:height//5]  # Top 20%
    bottom_mask = ref_hair[4*height//5:]  # Bottom 20%
    
    # Extraire les valeurs LAB pour le haut (racines)
    top_l = ref_lab[:height//5, :, 0][top_mask > 0]
    top_a = ref_lab[:height//5, :, 1][top_mask > 0]
    top_b = ref_lab[:height//5, :, 2][top_mask > 0]
    
    # Extraire les valeurs LAB pour le bas (pointes)
    bottom_l = ref_lab[4*height//5:, :, 0][bottom_mask > 0]
    bottom_a = ref_lab[4*height//5:, :, 1][bottom_mask > 0]
    bottom_b = ref_lab[4*height//5:, :, 2][bottom_mask > 0]
    
    # Moyennes avec fallback
    l_top = int(np.median(top_l)) if len(top_l) > 0 else 80
    l_bottom = int(np.median(bottom_l)) if len(bottom_l) > 0 else 200
    
    a_top = int(np.median(top_a)) if len(top_a) > 0 else 128
    a_bottom = int(np.median(bottom_a)) if len(bottom_a) > 0 else 128
    
    b_top = int(np.median(top_b)) if len(top_b) > 0 else 128
    b_bottom = int(np.median(bottom_b)) if len(bottom_b) > 0 else 128
    
    return {
        "l_top": l_top, "l_bottom": l_bottom,
        "a_top": a_top, "a_bottom": a_bottom,
        "b_top": b_top, "b_bottom": b_bottom
    }


def recolor_template_with_reference(reference: np.ndarray, blend: float = 0.65) -> np.ndarray:
    """
    Recolorise le gabarit avec les couleurs de la référence.
    Retourne l'image finale avec watermark préservé.
    """
    gabarit = load_template()
    hair_mask = improve_hair_mask(gabarit)
    color_profile = extract_color_profile(reference)
    
    # Recolorisation LAB avec ombré complet
    lab = cv2.cvtColor(gabarit, cv2.COLOR_RGB2LAB)
    l, a, b = cv2.split(lab)
    
    # Valeurs originales du gabarit pour le blending
    original_lab = cv2.cvtColor(gabarit, cv2.COLOR_RGB2LAB)
    orig_l, orig_a, orig_b = cv2.split(original_lab)
    
    height = lab.shape[0]
    for y in range(height):
        ratio = y / height  # 0 en haut, 1 en bas
        mask_row = hair_mask[y] > 0
        
        if np.any(mask_row):
            # Interpoler L, A, B entre haut et bas
            target_l = int(color_profile["l_top"] * (1 - ratio) + color_profile["l_bottom"] * ratio)
            target_a = int(color_profile["a_top"] * (1 - ratio) + color_profile["a_bottom"] * ratio)
            target_b = int(color_profile["b_top"] * (1 - ratio) + color_profile["b_bottom"] * ratio)
            
            # Calculer la différence à appliquer (préserve la texture)
            current_l = orig_l[y][mask_row].astype(np.float32)
            current_a = orig_a[y][mask_row].astype(np.float32)
            current_b = orig_b[y][mask_row].astype(np.float32)
            
            # Appliquer la nouvelle couleur en préservant les variations locales
            # L (luminosité) : remplacer partiellement
            new_l = current_l * (1 - blend * 0.7) + target_l * (blend * 0.7)
            # A et B (couleur) : remplacer plus fortement
            new_a = current_a * (1 - blend) + target_a * blend
            new_b = current_b * (1 - blend) + target_b * blend
            
            l[y][mask_row] = np.clip(new_l, 0, 255).astype(np.uint8)
            a[y][mask_row] = np.clip(new_a, 0, 255).astype(np.uint8)
            b[y][mask_row] = np.clip(new_b, 0, 255).astype(np.uint8)

    recolored_lab = cv2.merge([l, a, b])
    final = cv2.cvtColor(recolored_lab, cv2.COLOR_LAB2RGB)
    
    return final


def image_to_base64(image: np.ndarray, format: str = "PNG") -> str:
    """Convertit une image numpy en base64."""
    pil_image = Image.fromarray(image)
    buffer = io.BytesIO()
    pil_image.save(buffer, format=format, quality=95)
    return base64.b64encode(buffer.getvalue()).decode('utf-8')


def base64_to_image(b64_string: str) -> np.ndarray:
    """Convertit une string base64 en image numpy RGB."""
    image_data = base64.b64decode(b64_string)
    pil_image = Image.open(io.BytesIO(image_data)).convert('RGB')
    return np.array(pil_image)


async def auto_recolor(reference_b64: str, blend: float = 0.65) -> dict:
    """
    Fonction principale pour recolorisation automatique.
    
    Args:
        reference_b64: Image référence couleur en base64
        blend: Intensité du mélange (0.3-0.9)
    
    Returns:
        Dict avec l'image résultante en base64
    """
    reference = base64_to_image(reference_b64)
    result = recolor_template_with_reference(reference, blend)
    
    return {
        "result": image_to_base64(result),
        "success": True,
        "message": "Image recolorisée avec le gabarit Genius + watermark"
    }
