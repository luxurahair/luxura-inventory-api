"""
Luxura Color Engine V4
======================
Module de recolorisation simplifié et efficace.
Utilise un transfert de couleur direct en HSV.
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


def create_hair_mask(image: np.ndarray) -> np.ndarray:
    """
    Crée un masque des cheveux.
    VERSION 5: Détection basée sur la luminosité et la saturation.
    
    Pour un gabarit avec fond blanc:
    - Cheveux = pixels foncés (V<150) OU très saturés (S>100)
    - Exclure le fond blanc (V>220 AND S<30)
    """
    try:
        height, width = image.shape[:2]
        
        # Convertir en HSV
        hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
        h, s, v = hsv[:,:,0], hsv[:,:,1], hsv[:,:,2]
        
        # 1. Détecter le fond blanc
        is_white = (s < 40) & (v > 200)
        
        # 2. Détecter les pixels qui pourraient être des cheveux
        # Cheveux = soit foncés, soit colorés
        is_dark = v < 150  # Pixels foncés
        is_colored = s > 80  # Pixels avec bonne saturation
        is_hair_candidate = is_dark | is_colored
        
        # 3. Exclure le blanc
        hair_mask = is_hair_candidate & ~is_white
        hair_mask = hair_mask.astype(np.uint8) * 255
        
        # 4. Morphologie pour nettoyer
        kernel = np.ones((5, 5), np.uint8)
        hair_mask = cv2.morphologyEx(hair_mask, cv2.MORPH_CLOSE, kernel, iterations=2)
        hair_mask = cv2.morphologyEx(hair_mask, cv2.MORPH_OPEN, kernel, iterations=1)
        
        # 5. Garder seulement les régions d'au moins 0.5% de l'image
        contours, _ = cv2.findContours(hair_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            final_mask = np.zeros_like(hair_mask)
            min_area = (width * height) * 0.005  # 0.5% minimum
            
            for contour in contours:
                if cv2.contourArea(contour) >= min_area:
                    cv2.drawContours(final_mask, [contour], -1, 255, -1)
            
            if np.sum(final_mask > 0) > 0:
                hair_mask = final_mask
        
        hair_pixels = np.sum(hair_mask > 128)
        logger.info(f"Hair mask created: {hair_pixels} pixels ({hair_pixels / (width * height) * 100:.1f}%)")
        
        return hair_mask
        
    except Exception as e:
        logger.error(f"Error creating hair mask: {e}")
        import traceback
        traceback.print_exc()
        # Fallback: tout ce qui est foncé
        hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
        mask = (hsv[:, :, 2] < 150).astype(np.uint8) * 255
        return mask


def get_average_color_hsv(image: np.ndarray, mask: np.ndarray = None) -> Tuple[float, float, float]:
    """
    Calcule la couleur moyenne HSV d'une image (ou région masquée).
    Exclut automatiquement les pixels trop clairs (fond blanc) et trop sombres.
    """
    hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV).astype(np.float32)
    
    # Créer un masque pour exclure le fond blanc et les pixels très sombres
    v_channel = hsv[:, :, 2]
    s_channel = hsv[:, :, 1]
    
    # Pixels valides: pas trop clair (V < 245), pas trop sombre (V > 20), avec saturation
    valid_mask = (v_channel > 20) & (v_channel < 245) & (s_channel > 10)
    
    if mask is not None:
        # Combiner avec le masque fourni
        valid_mask = valid_mask & (mask > 128)
    
    if np.sum(valid_mask) < 100:
        # Fallback: utiliser tous les pixels non-blancs
        valid_mask = v_channel < 250
        if np.sum(valid_mask) < 100:
            # Dernier recours: moyenne de tout
            return float(np.median(hsv[:, :, 0])), float(np.median(hsv[:, :, 1])), float(np.median(hsv[:, :, 2]))
    
    h_vals = hsv[:, :, 0][valid_mask]
    s_vals = hsv[:, :, 1][valid_mask]
    v_vals = hsv[:, :, 2][valid_mask]
    
    return float(np.median(h_vals)), float(np.median(s_vals)), float(np.median(v_vals))


def recolor_with_reference(
    gabarit: np.ndarray, 
    reference: np.ndarray, 
    blend: float = 0.85
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Recolorise un gabarit avec la couleur d'une référence.
    
    VERSION 6: Opérations vectorielles pour qualité et rapidité.
    
    Args:
        gabarit: Image RGB du gabarit
        reference: Image RGB de la couleur de référence
        blend: Intensité (0.5-1.0)
    
    Returns:
        (image_recolorisée, masque_cheveux)
    """
    logger.info(f"🎨 Color Engine V6 - Recoloring with blend={blend}")
    
    # 1. Créer le masque des cheveux
    hair_mask = create_hair_mask(gabarit)
    
    # 2. Extraire la couleur cible de la référence
    target_h, target_s, target_v = get_average_color_hsv(reference)
    logger.info(f"🎯 Target color: H={target_h:.1f}, S={target_s:.1f}, V={target_v:.1f}")
    
    # 3. Extraire la couleur source du gabarit (zone cheveux)
    source_h, source_s, source_v = get_average_color_hsv(gabarit, hair_mask)
    logger.info(f"📊 Source color: H={source_h:.1f}, S={source_s:.1f}, V={source_v:.1f}")
    
    # 4. Convertir le gabarit en HSV (float pour précision)
    hsv = cv2.cvtColor(gabarit, cv2.COLOR_RGB2HSV).astype(np.float32)
    
    # 5. Créer un masque flou pour des transitions douces (sans boucle)
    mask_float = hair_mask.astype(np.float32) / 255.0
    mask_blur = cv2.GaussianBlur(mask_float, (15, 15), 0)
    
    # Appliquer le blend
    mask_blend = mask_blur * blend
    
    # Expand mask to 3D pour broadcasting
    mask_3d = mask_blend[:, :, np.newaxis]
    
    # 6. Calculer les transformations
    h_shift = target_h - source_h
    
    # Ratio de saturation et luminosité (éviter division par zéro)
    s_ratio = target_s / max(source_s, 1.0)
    v_ratio = target_v / max(source_v, 1.0)
    
    logger.info(f"🔄 Transform: H_shift={h_shift:.1f}, S_ratio={s_ratio:.2f}, V_ratio={v_ratio:.2f}")
    
    # 7. Appliquer les transformations de manière vectorielle
    h_channel = hsv[:, :, 0]
    s_channel = hsv[:, :, 1]
    v_channel = hsv[:, :, 2]
    
    # Nouvelle teinte = source + shift * mask
    new_h = h_channel + h_shift * mask_blend
    new_h = np.mod(new_h, 180)  # Wrap around 0-180
    
    # Nouvelle saturation = ajuster vers la cible
    new_s = s_channel * (1.0 + (s_ratio - 1.0) * mask_blend)
    new_s = np.clip(new_s, 0, 255)
    
    # Nouvelle luminosité = ajuster vers la cible (moins agressif)
    new_v = v_channel * (1.0 + (v_ratio - 1.0) * mask_blend * 0.7)
    new_v = np.clip(new_v, 0, 255)
    
    # 8. Reconstruire l'image HSV
    result_hsv = np.stack([new_h, new_s, new_v], axis=-1).astype(np.uint8)
    
    # 9. Convertir en RGB
    result = cv2.cvtColor(result_hsv, cv2.COLOR_HSV2RGB)
    
    # Vérifier le résultat
    result_h, result_s, result_v = get_average_color_hsv(result, hair_mask)
    logger.info(f"✅ Result color: H={result_h:.1f}, S={result_s:.1f}, V={result_v:.1f}")
    
    return result, hair_mask


def extract_dominant_color_hsv(image: np.ndarray) -> Tuple[float, float, float]:
    """Alias pour compatibilité avec l'ancien code."""
    return get_average_color_hsv(image)


def improve_hair_mask(image: np.ndarray) -> np.ndarray:
    """Alias pour compatibilité avec l'ancien code."""
    return create_hair_mask(image)


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
    blend: float = 0.85
) -> dict:
    """
    Fonction principale pour le traitement Color Engine.
    """
    gabarit1 = base64_to_image(gabarit1_b64)
    reference = base64_to_image(reference_b64)
    
    result1, mask1 = recolor_with_reference(gabarit1, reference, blend)
    
    results = {
        "gabarit1": image_to_base64(result1),
        "mask1": image_to_base64(mask1),
        "success": True
    }
    
    if gabarit2_b64:
        gabarit2 = base64_to_image(gabarit2_b64)
        result2, mask2 = recolor_with_reference(gabarit2, reference, blend)
        results["gabarit2"] = image_to_base64(result2)
        results["mask2"] = image_to_base64(mask2)
    
    return results
