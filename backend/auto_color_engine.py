"""
Luxura Auto Color Engine
========================
Upload simplifié : envoie juste la référence couleur,
reçois l'image recolorisée avec le gabarit + watermark.
"""

import os
import numpy as np
import cv2
from PIL import Image
from rembg import remove
import io
import base64
from pathlib import Path

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
    ref_gray = cv2.cvtColor(np.array(ref_person), cv2.COLOR_RGBA2GRAY)
    _, ref_hair = cv2.threshold(ref_gray, 30, 255, cv2.THRESH_BINARY)
    
    if np.sum(ref_hair > 0) == 0:
        return {"hue": 90, "sat": 0.5, "ombre_ratio": 0.2}
    
    # Analyser l'ombré (différence haut vs bas)
    height = reference.shape[0]
    top_section = ref_hair[:height//4]
    bottom_section = ref_hair[3*height//4:]
    
    top_hue = np.median(ref_hsv[:height//4, :, 0][top_section > 0]) if np.any(top_section > 0) else 90
    bottom_hue = np.median(ref_hsv[3*height//4:, :, 0][bottom_section > 0]) if np.any(bottom_section > 0) else 90
    
    return {
        "hue_top": int(top_hue),
        "hue_bottom": int(bottom_hue),
        "sat": np.mean(ref_hsv[:, :, 1][ref_hair > 0]) / 255.0,
        "ombre_ratio": abs(top_hue - bottom_hue) / 180.0
    }


def recolor_template_with_reference(reference: np.ndarray, blend: float = 0.65) -> np.ndarray:
    """
    Recolorise le gabarit avec les couleurs de la référence.
    Retourne l'image finale avec watermark préservé.
    """
    gabarit = load_template()
    hair_mask = improve_hair_mask(gabarit)
    color_profile = extract_color_profile(reference)
    
    # Recolorisation LAB avec ombré
    lab = cv2.cvtColor(gabarit, cv2.COLOR_RGB2LAB)
    l, a, b = cv2.split(lab)
    
    height = lab.shape[0]
    for y in range(height):
        ratio = y / height
        mask_row = hair_mask[y] > 0
        if np.any(mask_row):
            # Interpoler entre hue_top et hue_bottom pour l'ombré
            current_hue = color_profile["hue_top"] * (1 - ratio) + color_profile["hue_bottom"] * ratio
            
            adjusted_a = a[y][mask_row].astype(np.float32) + (current_hue - 90) * 0.8
            adjusted_b = b[y][mask_row].astype(np.float32) + (color_profile["sat"] * 50 - 25) * 0.8
            a[y][mask_row] = np.clip(adjusted_a, 0, 255).astype(np.uint8)
            b[y][mask_row] = np.clip(adjusted_b, 0, 255).astype(np.uint8)

    recolored_lab = cv2.merge([l, a, b])
    recolored = cv2.cvtColor(recolored_lab, cv2.COLOR_LAB2RGB)

    # Mélange pour préserver texture/reflets
    original = gabarit.copy()
    final = (recolored.astype(np.float32) * blend + original.astype(np.float32) * (1 - blend))
    final = np.clip(final, 0, 255).astype(np.uint8)
    
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
