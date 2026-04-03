"""
Luxura Color Engine V2
======================
Module de recolorisation intelligente des extensions capillaires.
Intégré dans l'API FastAPI existante.
"""

import numpy as np
import cv2
from PIL import Image
from rembg import remove
import io
import base64
from typing import Tuple, Optional


def improve_hair_mask(image: np.ndarray) -> np.ndarray:
    """
    Crée un masque cheveux précis en:
    1. Supprimant le background avec rembg
    2. Détectant et excluant la peau
    3. Nettoyant avec morphologie
    """
    # 1. Person mask ultra propre
    person = remove(image)
    gray = cv2.cvtColor(np.array(person), cv2.COLOR_RGBA2GRAY)
    _, person_mask = cv2.threshold(gray, 30, 255, cv2.THRESH_BINARY)

    # 2. Détection peau (pour enlever visage/cou)
    hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
    skin_mask1 = cv2.inRange(hsv, (0, 20, 70), (20, 255, 255))
    skin_mask2 = cv2.inRange(hsv, (340, 20, 70), (180, 255, 255))
    skin_mask = skin_mask1 | skin_mask2

    # 3. Masque cheveux = person - peau + nettoyage
    hair_mask = cv2.bitwise_and(person_mask, cv2.bitwise_not(skin_mask))
    
    # Nettoyage morphologique (bords propres)
    kernel = np.ones((5, 5), np.uint8)
    hair_mask = cv2.morphologyEx(hair_mask, cv2.MORPH_CLOSE, kernel)
    hair_mask = cv2.morphologyEx(hair_mask, cv2.MORPH_OPEN, kernel)
    
    return hair_mask


def extract_reference_color(reference: np.ndarray) -> Tuple[int, float]:
    """
    Extrait la teinte et saturation moyennes de la référence.
    """
    ref_person = remove(reference)
    ref_hsv = cv2.cvtColor(reference, cv2.COLOR_RGB2HSV)
    ref_gray = cv2.cvtColor(np.array(ref_person), cv2.COLOR_RGBA2GRAY)
    _, ref_hair = cv2.threshold(ref_gray, 30, 255, cv2.THRESH_BINARY)
    
    if np.sum(ref_hair > 0) == 0:
        return 90, 0.5  # Valeurs par défaut
    
    target_hue = int(np.median(ref_hsv[:, :, 0][ref_hair > 0]))
    target_sat = np.mean(ref_hsv[:, :, 1][ref_hair > 0]) / 255.0
    
    return target_hue, target_sat


def recolor_with_reference(
    gabarit: np.ndarray, 
    reference: np.ndarray, 
    blend: float = 0.65
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Recolorise un gabarit avec les couleurs d'une référence.
    
    Args:
        gabarit: Image du gabarit à recoloriser (RGB)
        reference: Image de référence pour la couleur (RGB)
        blend: Intensité du mélange (0.3-0.9)
    
    Returns:
        Tuple[image_recolorisée, masque_cheveux]
    """
    hair_mask = improve_hair_mask(gabarit)
    target_hue, target_sat = extract_reference_color(reference)

    # Recolorisation LAB (luminosité préservée + couleur naturelle)
    lab = cv2.cvtColor(gabarit, cv2.COLOR_RGB2LAB)
    l, a, b = cv2.split(lab)
    
    # Appliquer nouvelle teinte proportionnellement (ombré racine)
    height = lab.shape[0]
    for y in range(height):
        ratio = y / height
        mask_row = hair_mask[y] > 0
        if np.any(mask_row):
            adjusted_a = a[y][mask_row].astype(np.float32) + (target_hue - 90) * (1 - ratio * 0.3)
            adjusted_b = b[y][mask_row].astype(np.float32) + (target_sat * 50 - 25) * (1 - ratio * 0.2)
            a[y][mask_row] = np.clip(adjusted_a, 0, 255).astype(np.uint8)
            b[y][mask_row] = np.clip(adjusted_b, 0, 255).astype(np.uint8)

    recolored_lab = cv2.merge([l, a, b])
    recolored = cv2.cvtColor(recolored_lab, cv2.COLOR_LAB2RGB)

    # Mélange pour garder mèches/reflets originaux
    original = gabarit.copy()
    final = (recolored.astype(np.float32) * blend + original.astype(np.float32) * (1 - blend))
    final = np.clip(final, 0, 255).astype(np.uint8)
    
    return final, hair_mask


def image_to_base64(image: np.ndarray, format: str = "PNG") -> str:
    """Convertit une image numpy en base64."""
    pil_image = Image.fromarray(image)
    buffer = io.BytesIO()
    pil_image.save(buffer, format=format)
    return base64.b64encode(buffer.getvalue()).decode('utf-8')


def base64_to_image(b64_string: str) -> np.ndarray:
    """Convertit une string base64 en image numpy RGB."""
    image_data = base64.b64decode(b64_string)
    pil_image = Image.open(io.BytesIO(image_data)).convert('RGB')
    return np.array(pil_image)


async def process_color_engine(
    gabarit1_b64: str,
    gabarit2_b64: Optional[str],
    reference_b64: str,
    blend: float = 0.65
) -> dict:
    """
    Fonction principale pour le traitement Color Engine.
    
    Args:
        gabarit1_b64: Gabarit 1 en base64
        gabarit2_b64: Gabarit 2 en base64 (optionnel)
        reference_b64: Image référence en base64
        blend: Intensité du mélange
    
    Returns:
        Dict avec les images résultantes en base64
    """
    # Charger les images
    gabarit1 = base64_to_image(gabarit1_b64)
    reference = base64_to_image(reference_b64)
    
    # Traiter gabarit 1
    result1, mask1 = recolor_with_reference(gabarit1, reference, blend)
    
    results = {
        "gabarit1": image_to_base64(result1),
        "mask1": image_to_base64(mask1),
        "success": True
    }
    
    # Traiter gabarit 2 si fourni
    if gabarit2_b64:
        gabarit2 = base64_to_image(gabarit2_b64)
        result2, mask2 = recolor_with_reference(gabarit2, reference, blend)
        results["gabarit2"] = image_to_base64(result2)
        results["mask2"] = image_to_base64(mask2)
    
    return results
