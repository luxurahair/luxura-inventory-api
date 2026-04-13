"""
Luxura Color Engine V8 - ULTRA HIGH RESOLUTION
===============================================
Module de recolorisation haute qualité professionnelle.
- Préserve 100% de la résolution originale
- Décomposition en fréquences pour préserver les détails
- Transfert de couleur HSV précis
- Aucune perte de netteté
"""

import numpy as np
import cv2
from PIL import Image, ImageFilter, ImageEnhance
import io
import base64
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


def create_hair_mask(image: np.ndarray) -> np.ndarray:
    """
    Crée un masque des cheveux.
    VERSION 5: Détection basée sur la luminosité et la saturation.
    """
    try:
        height, width = image.shape[:2]
        
        # Convertir en HSV
        hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
        h, s, v = hsv[:,:,0], hsv[:,:,1], hsv[:,:,2]
        
        # 1. Détecter le fond blanc
        is_white = (s < 40) & (v > 200)
        
        # 2. Détecter les pixels qui pourraient être des cheveux
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
        
        # 5. Garder seulement les régions significatives
        contours, _ = cv2.findContours(hair_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            final_mask = np.zeros_like(hair_mask)
            min_area = (width * height) * 0.005
            
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
        hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
        mask = (hsv[:, :, 2] < 150).astype(np.uint8) * 255
        return mask


def get_average_color_hsv(image: np.ndarray, mask: np.ndarray = None) -> Tuple[float, float, float]:
    """
    Calcule la couleur moyenne HSV d'une image (ou région masquée).
    """
    hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV).astype(np.float32)
    
    v_channel = hsv[:, :, 2]
    s_channel = hsv[:, :, 1]
    
    valid_mask = (v_channel > 20) & (v_channel < 245) & (s_channel > 10)
    
    if mask is not None:
        valid_mask = valid_mask & (mask > 128)
    
    if np.sum(valid_mask) < 100:
        valid_mask = v_channel < 250
        if np.sum(valid_mask) < 100:
            return float(np.median(hsv[:, :, 0])), float(np.median(hsv[:, :, 1])), float(np.median(hsv[:, :, 2]))
    
    h_vals = hsv[:, :, 0][valid_mask]
    s_vals = hsv[:, :, 1][valid_mask]
    v_vals = hsv[:, :, 2][valid_mask]
    
    return float(np.median(h_vals)), float(np.median(s_vals)), float(np.median(v_vals))


def extract_high_frequency(image: np.ndarray, kernel_size: int = 21) -> np.ndarray:
    """
    Extrait les hautes fréquences (détails, texture) de l'image.
    High freq = Original - Low freq (blurred)
    """
    # Blur pour obtenir les basses fréquences
    low_freq = cv2.GaussianBlur(image.astype(np.float32), (kernel_size, kernel_size), 0)
    
    # Hautes fréquences = différence
    high_freq = image.astype(np.float32) - low_freq
    
    return high_freq, low_freq


def recolor_with_reference(
    gabarit: np.ndarray, 
    reference: np.ndarray, 
    blend: float = 0.95
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Recolorise un gabarit avec la couleur d'une référence.
    
    VERSION 8: ULTRA HIGH QUALITY
    =============================
    Utilise une décomposition en fréquences:
    1. Extraire les HAUTES FRÉQUENCES (détails, texture) de l'original
    2. Modifier la COULEUR sur les basses fréquences uniquement
    3. Réassembler: Color modifié + Détails originaux
    
    Résultat: Changement de couleur SANS perte de détails
    
    Args:
        gabarit: Image RGB du gabarit
        reference: Image RGB de la couleur de référence
        blend: Intensité (0.5-1.0)
    
    Returns:
        (image_recolorisée, masque_cheveux)
    """
    logger.info(f"🎨 Color Engine V8 ULTRA - Recoloring with blend={blend}")
    logger.info(f"📐 Input resolution: {gabarit.shape[1]}x{gabarit.shape[0]}")
    
    # ============================================
    # ÉTAPE 1: Créer le masque des cheveux
    # ============================================
    hair_mask = create_hair_mask(gabarit)
    hair_pixels = np.sum(hair_mask > 128)
    total_pixels = hair_mask.shape[0] * hair_mask.shape[1]
    logger.info(f"🎭 Hair mask: {hair_pixels} pixels ({hair_pixels/total_pixels*100:.1f}%)")
    
    # ============================================
    # ÉTAPE 2: Extraire la couleur cible
    # ============================================
    target_h, target_s, target_v = get_average_color_hsv(reference)
    logger.info(f"🎯 Target HSV: H={target_h:.1f}, S={target_s:.1f}, V={target_v:.1f}")
    
    # ============================================
    # ÉTAPE 3: Extraire la couleur source (cheveux du gabarit)
    # ============================================
    source_h, source_s, source_v = get_average_color_hsv(gabarit, hair_mask)
    logger.info(f"📊 Source HSV: H={source_h:.1f}, S={source_s:.1f}, V={source_v:.1f}")
    
    # ============================================
    # ÉTAPE 4: Extraire les détails (hautes fréquences) en grayscale
    # ============================================
    gray = cv2.cvtColor(gabarit, cv2.COLOR_RGB2GRAY)
    high_freq, _ = extract_high_frequency(gray, kernel_size=15)
    logger.info(f"📈 High frequency detail extracted")
    
    # ============================================
    # ÉTAPE 5: Convertir en HSV et modifier la couleur
    # ============================================
    hsv = cv2.cvtColor(gabarit, cv2.COLOR_RGB2HSV).astype(np.float32)
    
    # Masque lissé pour transitions douces
    mask_float = hair_mask.astype(np.float32) / 255.0
    mask_blur = cv2.GaussianBlur(mask_float, (21, 21), 0)
    mask_blend = mask_blur * blend
    
    # Calculer les transformations
    h_shift = target_h - source_h
    s_ratio = target_s / max(source_s, 1.0)
    v_ratio = target_v / max(source_v, 1.0)
    
    logger.info(f"🔄 Transform: H_shift={h_shift:.1f}, S_ratio={s_ratio:.2f}, V_ratio={v_ratio:.2f}")
    
    # ============================================
    # ÉTAPE 6: Appliquer les transformations HSV
    # ============================================
    h_channel = hsv[:, :, 0]
    s_channel = hsv[:, :, 1]
    v_channel = hsv[:, :, 2]
    
    # Nouvelle teinte
    new_h = h_channel + h_shift * mask_blend
    new_h = np.mod(new_h, 180)
    
    # Nouvelle saturation (préserver les variations)
    # On scale vers la cible mais garde la variance originale
    s_mean = np.mean(s_channel[hair_mask > 128])
    s_std = np.std(s_channel[hair_mask > 128])
    
    # Normaliser, puis rescale vers la cible
    new_s = target_s + (s_channel - source_s) * (target_s / max(source_s, 1.0)) * 0.5
    new_s = s_channel * (1 - mask_blend) + new_s * mask_blend
    new_s = np.clip(new_s, 0, 255)
    
    # Nouvelle luminosité (conserver les variations pour les reflets)
    # On applique le ratio mais garde 60% de la variance originale
    v_mean = np.mean(v_channel[hair_mask > 128])
    v_deviation = v_channel - v_mean  # Écart par rapport à la moyenne
    
    # Nouvelle moyenne + variance conservée
    new_v_mean = v_mean * v_ratio
    new_v = new_v_mean + v_deviation * 0.8  # 80% de la variance originale
    new_v = v_channel * (1 - mask_blend) + new_v * mask_blend
    new_v = np.clip(new_v, 0, 255)
    
    # ============================================
    # ÉTAPE 7: Reconstruire l'image
    # ============================================
    result_hsv = np.stack([new_h, new_s, new_v], axis=-1).astype(np.uint8)
    result = cv2.cvtColor(result_hsv, cv2.COLOR_HSV2RGB).astype(np.float32)
    
    # ============================================
    # ÉTAPE 8: RÉINJECTER les détails haute fréquence
    # ============================================
    # On ajoute les hautes fréquences aux 3 canaux RGB
    high_freq_3d = np.stack([high_freq, high_freq, high_freq], axis=-1)
    
    # Appliquer seulement sur la zone des cheveux (avec masque doux)
    mask_hf = mask_blur[:, :, np.newaxis] * 0.7  # 70% des détails
    
    result = result + high_freq_3d * mask_hf
    result = np.clip(result, 0, 255).astype(np.uint8)
    
    # ============================================
    # ÉTAPE 9: Vérification finale
    # ============================================
    result_h, result_s, result_v = get_average_color_hsv(result, hair_mask)
    logger.info(f"✅ Result HSV: H={result_h:.1f}, S={result_s:.1f}, V={result_v:.1f}")
    logger.info(f"📐 Output resolution: {result.shape[1]}x{result.shape[0]} (100% preserved)")
    
    return result, hair_mask


def extract_dominant_color_hsv(image: np.ndarray) -> Tuple[float, float, float]:
    """Alias pour compatibilité."""
    return get_average_color_hsv(image)


def improve_hair_mask(image: np.ndarray) -> np.ndarray:
    """Alias pour compatibilité."""
    return create_hair_mask(image)


def image_to_base64(image: np.ndarray, format: str = "PNG") -> str:
    """Convertit une image numpy en base64."""
    pil_image = Image.fromarray(image)
    buffer = io.BytesIO()
    pil_image.save(buffer, format=format, optimize=False)
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
    blend: float = 0.95
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
