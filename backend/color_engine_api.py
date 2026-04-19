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
from PIL import Image, ImageFilter, ImageEnhance
import io
import base64
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)

# Import optionnel de cv2 - le serveur démarre même sans
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    cv2 = None
    logger.warning("⚠️ OpenCV (cv2) non disponible - Color Engine désactivé")


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
    
    VERSION 10: NOIR NATUREL
    ========================
    Détection intelligente des couleurs noires:
    - Si la cible est NOIR (V < 50, S < 50): on assombrit SANS changer la teinte
    - Sinon: transfert normal HSV
    
    Ceci produit un noir naturel au lieu d'un noir verdâtre.
    """
    logger.info(f"🎨 Color Engine V10 - Recoloring with blend={blend}")
    logger.info(f"📐 Input resolution: {gabarit.shape[1]}x{gabarit.shape[0]}")
    
    # ============================================
    # ÉTAPE 1: Créer le masque des cheveux
    # ============================================
    hair_mask = create_hair_mask(gabarit)
    hair_pixels = np.sum(hair_mask > 128)
    total_pixels = hair_mask.shape[0] * hair_mask.shape[1]
    logger.info(f"🎭 Hair mask: {hair_pixels} pixels ({hair_pixels/total_pixels*100:.1f}%)")
    
    # ============================================
    # ÉTAPE 2: Extraire la couleur cible de la référence
    # ============================================
    target_h, target_s, target_v = get_average_color_hsv(reference)
    logger.info(f"🎯 Target HSV: H={target_h:.1f}, S={target_s:.1f}, V={target_v:.1f}")
    
    # ============================================
    # ÉTAPE 3: Détecter si c'est une couleur NOIRE
    # ============================================
    # Noir = très sombre (V < 50) ET faible saturation (S < 60)
    is_black_target = (target_v < 50) and (target_s < 60)
    
    if is_black_target:
        logger.info(f"🌑 NOIR détecté - Mode assombrissement naturel")
    
    # ============================================
    # ÉTAPE 4: Extraire la couleur source du gabarit
    # ============================================
    source_h, source_s, source_v = get_average_color_hsv(gabarit, hair_mask)
    logger.info(f"📊 Source HSV: H={source_h:.1f}, S={source_s:.1f}, V={source_v:.1f}")
    
    # ============================================
    # ÉTAPE 5: Convertir en HSV
    # ============================================
    hsv = cv2.cvtColor(gabarit, cv2.COLOR_RGB2HSV).astype(np.float32)
    
    # Masque lissé pour transitions douces
    mask_float = hair_mask.astype(np.float32) / 255.0
    mask_blur = cv2.GaussianBlur(mask_float, (15, 15), 0)
    mask_blend = mask_blur * blend
    
    h_channel = hsv[:, :, 0]
    s_channel = hsv[:, :, 1]
    v_channel = hsv[:, :, 2]
    
    # ============================================
    # ÉTAPE 6: Appliquer la transformation
    # ============================================
    
    if is_black_target:
        # MODE NOIR: Conserver la teinte originale, juste assombrir
        new_h = h_channel  # PAS de changement de teinte
        
        # Réduire légèrement la saturation pour un noir naturel
        new_s = s_channel * (1 - mask_blend * 0.3)  # 30% de désaturation
        new_s = np.clip(new_s, 0, 255)
        
        # Assombrir fortement
        # Calculer la nouvelle luminosité relative
        v_min = np.min(v_channel[hair_mask > 128])
        v_max = np.max(v_channel[hair_mask > 128])
        v_range = max(v_max - v_min, 1)
        v_normalized = (v_channel - v_min) / v_range
        
        # Plage très sombre pour le noir: V de 5 à 45
        target_v_min = 5
        target_v_max = 45
        
        new_v_base = target_v_min + v_normalized * (target_v_max - target_v_min)
        new_v = v_channel * (1 - mask_blend) + new_v_base * mask_blend
        new_v = np.clip(new_v, 0, 255)
        
        logger.info(f"🔄 Mode NOIR: V range [{target_v_min}, {target_v_max}], pas de changement de teinte")
        
    else:
        # MODE COULEUR: Transfert normal HSV
        # Teinte: remplacement direct
        new_h = h_channel * (1 - mask_blend) + target_h * mask_blend
        new_h = np.mod(new_h, 180)
        
        # Saturation: remplacement direct
        new_s = s_channel * (1 - mask_blend) + target_s * mask_blend
        new_s = np.clip(new_s, 0, 255)
        
        # Luminosité: mapper sur la plage cible
        v_min = np.min(v_channel[hair_mask > 128])
        v_max = np.max(v_channel[hair_mask > 128])
        v_range = max(v_max - v_min, 1)
        v_normalized = (v_channel - v_min) / v_range
        
        # Plage basée sur la cible
        target_v_min = max(10, target_v * 0.4)
        target_v_max = min(target_v * 1.4, target_v + 50)
        
        new_v_base = target_v_min + v_normalized * (target_v_max - target_v_min)
        new_v = v_channel * (1 - mask_blend) + new_v_base * mask_blend
        new_v = np.clip(new_v, 0, 255)
        
        logger.info(f"🔄 Mode COULEUR: H={target_h:.0f}, S={target_s:.0f}, V=[{target_v_min:.0f}-{target_v_max:.0f}]")
    
    # ============================================
    # ÉTAPE 7: Reconstruire l'image
    # ============================================
    result_hsv = np.stack([new_h, new_s, new_v], axis=-1).astype(np.uint8)
    result = cv2.cvtColor(result_hsv, cv2.COLOR_HSV2RGB)
    
    # ============================================
    # ÉTAPE 8: Vérification finale
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
