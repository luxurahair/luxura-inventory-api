"""
Luxura Color Engine V3
======================
Module de recolorisation intelligente des extensions capillaires.
Version améliorée avec vrai transfert de couleur.
"""

import numpy as np
import cv2
from PIL import Image
from rembg import remove
import io
import base64
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


def improve_hair_mask(image: np.ndarray) -> np.ndarray:
    """
    Crée un masque cheveux précis en:
    1. Supprimant le background avec rembg
    2. Détectant et excluant la peau
    3. Nettoyant avec morphologie
    """
    try:
        # 1. Person mask ultra propre
        person = remove(image)
        gray = cv2.cvtColor(np.array(person), cv2.COLOR_RGBA2GRAY)
        _, person_mask = cv2.threshold(gray, 30, 255, cv2.THRESH_BINARY)

        # 2. Détection peau (pour enlever visage/cou)
        hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
        skin_mask1 = cv2.inRange(hsv, (0, 20, 70), (20, 255, 255))
        skin_mask2 = cv2.inRange(hsv, (160, 20, 70), (180, 255, 255))
        skin_mask = skin_mask1 | skin_mask2

        # 3. Masque cheveux = person - peau + nettoyage
        hair_mask = cv2.bitwise_and(person_mask, cv2.bitwise_not(skin_mask))
        
        # Nettoyage morphologique (bords propres)
        kernel = np.ones((5, 5), np.uint8)
        hair_mask = cv2.morphologyEx(hair_mask, cv2.MORPH_CLOSE, kernel)
        hair_mask = cv2.morphologyEx(hair_mask, cv2.MORPH_OPEN, kernel)
        
        return hair_mask
    except Exception as e:
        logger.error(f"Error creating hair mask: {e}")
        # Fallback: masque basé sur la luminosité
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        _, mask = cv2.threshold(gray, 50, 255, cv2.THRESH_BINARY)
        return mask


def extract_dominant_color_hsv(image: np.ndarray) -> Tuple[float, float, float]:
    """
    Extrait la couleur dominante d'une image en HSV.
    Retourne (H, S, V) moyens.
    """
    # Convertir en HSV
    hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
    
    # Masquer les pixels trop clairs ou trop foncés
    v_channel = hsv[:, :, 2]
    valid_mask = (v_channel > 30) & (v_channel < 240)
    
    if np.sum(valid_mask) < 100:
        # Fallback si pas assez de pixels valides
        return float(np.mean(hsv[:, :, 0])), float(np.mean(hsv[:, :, 1])), float(np.mean(hsv[:, :, 2]))
    
    h_mean = float(np.mean(hsv[:, :, 0][valid_mask]))
    s_mean = float(np.mean(hsv[:, :, 1][valid_mask]))
    v_mean = float(np.mean(hsv[:, :, 2][valid_mask]))
    
    return h_mean, s_mean, v_mean


def recolor_with_reference(
    gabarit: np.ndarray, 
    reference: np.ndarray, 
    blend: float = 0.75
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Recolorise un gabarit avec les couleurs d'une référence.
    VERSION 3.1: Transfert de couleur HSV DIRECT plus visible.
    
    Args:
        gabarit: Image du gabarit à recoloriser (RGB)
        reference: Image de référence pour la couleur (RGB)
        blend: Intensité du mélange (0.3-1.0)
    
    Returns:
        Tuple[image_recolorisée, masque_cheveux]
    """
    logger.info(f"🎨 Recoloring with blend={blend}")
    
    # 1. Créer le masque des cheveux
    hair_mask = improve_hair_mask(gabarit)
    logger.info(f"📋 Hair mask created: {np.sum(hair_mask > 0)} pixels")
    
    # 2. Extraire les couleurs de la référence
    ref_h, ref_s, ref_v = extract_dominant_color_hsv(reference)
    logger.info(f"🎯 Reference color HSV: H={ref_h:.1f}, S={ref_s:.1f}, V={ref_v:.1f}")
    
    # 3. Convertir le gabarit en HSV
    gabarit_hsv = cv2.cvtColor(gabarit, cv2.COLOR_RGB2HSV).astype(np.float32)
    
    # 4. Créer un masque flou pour des transitions douces
    hair_mask_float = hair_mask.astype(np.float32) / 255.0
    hair_mask_blur = cv2.GaussianBlur(hair_mask_float, (31, 31), 0)
    
    # 5. TRANSFERT DIRECT: Remplacer la teinte par celle de la référence
    result_hsv = gabarit_hsv.copy()
    
    for y in range(gabarit_hsv.shape[0]):
        for x in range(gabarit_hsv.shape[1]):
            mask_val = hair_mask_blur[y, x] * blend
            if mask_val > 0.1:
                # Remplacer directement la teinte (H) par celle de la référence
                # Mais garder un peu de la teinte originale pour les variations
                original_h = gabarit_hsv[y, x, 0]
                new_h = ref_h * mask_val + original_h * (1 - mask_val)
                result_hsv[y, x, 0] = new_h % 180
                
                # Ajuster la saturation vers celle de la référence
                original_s = gabarit_hsv[y, x, 1]
                new_s = ref_s * mask_val + original_s * (1 - mask_val)
                result_hsv[y, x, 1] = np.clip(new_s, 0, 255)
                
                # Ajuster légèrement la luminosité (garder les ombres/reflets)
                original_v = gabarit_hsv[y, x, 2]
                v_ratio = ref_v / max(gabarit_hsv[:, :, 2][hair_mask > 0].mean(), 1)
                new_v = original_v * (1 + (v_ratio - 1) * mask_val * 0.5)
                result_hsv[y, x, 2] = np.clip(new_v, 0, 255)
    
    # 6. Reconvertir en RGB
    result_hsv = result_hsv.astype(np.uint8)
    result_rgb = cv2.cvtColor(result_hsv, cv2.COLOR_HSV2RGB)
    
    logger.info("✅ Recoloring complete")
    
    return result_rgb, hair_mask


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
    blend: float = 0.75
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
