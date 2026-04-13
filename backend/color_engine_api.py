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
    Crée un masque des cheveux en utilisant rembg + détection de peau.
    Version simplifiée et robuste.
    """
    try:
        # 1. Supprimer le background avec rembg
        pil_img = Image.fromarray(image)
        removed = remove(pil_img)
        
        # Convertir en numpy et extraire le canal alpha
        removed_np = np.array(removed)
        if removed_np.shape[2] == 4:
            alpha = removed_np[:, :, 3]
            person_mask = (alpha > 128).astype(np.uint8) * 255
        else:
            # Pas de canal alpha, utiliser la luminosité
            gray = cv2.cvtColor(removed_np, cv2.COLOR_RGB2GRAY)
            _, person_mask = cv2.threshold(gray, 30, 255, cv2.THRESH_BINARY)
        
        # 2. Détecter la peau pour l'exclure
        hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
        
        # Plage de couleur peau (étendue)
        lower_skin1 = np.array([0, 20, 60])
        upper_skin1 = np.array([25, 180, 255])
        lower_skin2 = np.array([160, 20, 60])
        upper_skin2 = np.array([180, 180, 255])
        
        skin1 = cv2.inRange(hsv, lower_skin1, upper_skin1)
        skin2 = cv2.inRange(hsv, lower_skin2, upper_skin2)
        skin_mask = cv2.bitwise_or(skin1, skin2)
        
        # Dilater le masque de peau pour couvrir les bords
        kernel = np.ones((7, 7), np.uint8)
        skin_mask = cv2.dilate(skin_mask, kernel, iterations=2)
        
        # 3. Masque cheveux = personne - peau
        hair_mask = cv2.bitwise_and(person_mask, cv2.bitwise_not(skin_mask))
        
        # 4. Nettoyer le masque
        kernel = np.ones((5, 5), np.uint8)
        hair_mask = cv2.morphologyEx(hair_mask, cv2.MORPH_CLOSE, kernel)
        hair_mask = cv2.morphologyEx(hair_mask, cv2.MORPH_OPEN, kernel)
        
        return hair_mask
        
    except Exception as e:
        logger.error(f"Error creating hair mask: {e}")
        # Fallback: masque simple basé sur la luminosité
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        _, mask = cv2.threshold(gray, 80, 255, cv2.THRESH_BINARY)
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
    
    VERSION 4: Remplacement DIRECT de la teinte HSV.
    
    Args:
        gabarit: Image RGB du gabarit
        reference: Image RGB de la couleur de référence
        blend: Intensité (0.5-1.0)
    
    Returns:
        (image_recolorisée, masque_cheveux)
    """
    logger.info(f"🎨 Color Engine V4 - Recoloring with blend={blend}")
    
    # 1. Créer le masque des cheveux
    hair_mask = create_hair_mask(gabarit)
    hair_pixels = np.sum(hair_mask > 128)
    logger.info(f"📋 Hair mask: {hair_pixels} pixels")
    
    # 2. Extraire la couleur cible de la référence
    target_h, target_s, target_v = get_average_color_hsv(reference)
    logger.info(f"🎯 Target color: H={target_h:.1f}, S={target_s:.1f}, V={target_v:.1f}")
    
    # 3. Extraire la couleur source du gabarit (zone cheveux)
    source_h, source_s, source_v = get_average_color_hsv(gabarit, hair_mask)
    logger.info(f"📊 Source color: H={source_h:.1f}, S={source_s:.1f}, V={source_v:.1f}")
    
    # 4. Convertir le gabarit en HSV
    hsv = cv2.cvtColor(gabarit, cv2.COLOR_RGB2HSV).astype(np.float64)
    
    # 5. Créer un masque flou pour des transitions douces
    mask_float = hair_mask.astype(np.float64) / 255.0
    mask_blur = cv2.GaussianBlur(mask_float, (25, 25), 0)
    
    # 6. Appliquer la transformation de couleur
    # Pour chaque pixel dans la zone des cheveux:
    # - Remplacer la teinte (H) par celle de la référence
    # - Ajuster la saturation (S) proportionnellement
    # - Garder la luminosité (V) relative pour préserver les détails
    
    h_channel = hsv[:, :, 0]
    s_channel = hsv[:, :, 1]
    v_channel = hsv[:, :, 2]
    
    # Calculer les ratios de changement
    h_shift = target_h - source_h
    s_ratio = target_s / max(source_s, 1)
    v_ratio = target_v / max(source_v, 1)
    
    logger.info(f"🔄 Transform: H_shift={h_shift:.1f}, S_ratio={s_ratio:.2f}, V_ratio={v_ratio:.2f}")
    
    # Appliquer les changements avec le masque
    for y in range(hsv.shape[0]):
        for x in range(hsv.shape[1]):
            m = mask_blur[y, x] * blend
            if m > 0.1:
                # Nouvelle teinte = déplacer vers la cible
                new_h = h_channel[y, x] + h_shift * m
                h_channel[y, x] = new_h % 180
                
                # Nouvelle saturation = ajuster vers la cible
                new_s = s_channel[y, x] * (1 + (s_ratio - 1) * m)
                s_channel[y, x] = np.clip(new_s, 0, 255)
                
                # Nouvelle luminosité = légère ajustement
                new_v = v_channel[y, x] * (1 + (v_ratio - 1) * m * 0.3)
                v_channel[y, x] = np.clip(new_v, 0, 255)
    
    # 7. Reconvertir en RGB
    hsv[:, :, 0] = h_channel
    hsv[:, :, 1] = s_channel
    hsv[:, :, 2] = v_channel
    
    result = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB)
    
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
