import os
from io import BytesIO
from datetime import datetime

import cv2
import numpy as np
import streamlit as st
from PIL import Image, ImageOps
from rembg import remove

st.set_page_config(page_title="Luxura Color Engine PRO", layout="wide")
st.title("Luxura Color Engine PRO")
st.caption("Recolorisation produit avec watermark protégé, aperçu live et export SKU.")

OUTPUT_DIR = "outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ----------------------------
# Utils
# ----------------------------
def pil_to_rgb_np(img: Image.Image) -> np.ndarray:
    return np.array(img.convert("RGB"))


def rgb_np_to_pil(arr: np.ndarray) -> Image.Image:
    return Image.fromarray(arr.astype(np.uint8), mode="RGB")


def remove_bg_rgba(rgb_np: np.ndarray) -> np.ndarray:
    pil_img = Image.fromarray(rgb_np)
    out = remove(pil_img)
    if isinstance(out, bytes):
        out = Image.open(BytesIO(out))
    return np.array(out.convert("RGBA"))


def alpha_mask_from_rgba(rgba: np.ndarray, threshold: int = 10) -> np.ndarray:
    alpha = rgba[:, :, 3]
    return np.where(alpha > threshold, 255, 0).astype(np.uint8)


def clean_mask(mask: np.ndarray, blur: int = 5, morph: int = 5) -> np.ndarray:
    kernel = np.ones((morph, morph), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    if blur > 0:
        if blur % 2 == 0:
            blur += 1
        mask = cv2.GaussianBlur(mask, (blur, blur), 0)
    return mask


def mask_to_3ch(mask: np.ndarray) -> np.ndarray:
    return np.stack([mask, mask, mask], axis=-1)


def resize_profile(profile: np.ndarray, target_h: int) -> np.ndarray:
    if len(profile) == target_h:
        return profile
    x_old = np.linspace(0, 1, len(profile))
    x_new = np.linspace(0, 1, target_h)
    out = np.zeros((target_h, 3), dtype=np.float32)
    for c in range(3):
        out[:, c] = np.interp(x_new, x_old, profile[:, c])
    return out


# ----------------------------
# Hair mask
# ----------------------------
def estimate_object_mask(rgb_np: np.ndarray) -> np.ndarray:
    rgba = remove_bg_rgba(rgb_np)
    mask = alpha_mask_from_rgba(rgba, threshold=8)
    mask = clean_mask(mask, blur=5, morph=5)
    return mask


def build_protected_zone_mask(
    rgb_np: np.ndarray,
    protect_top_ratio: float,
    protect_bottom_ratio: float,
    protect_left_ratio: float,
    protect_right_ratio: float,
) -> np.ndarray:
    """
    Zone à ne jamais traiter :
    typiquement watermark / texte / logos placés dans certaines zones.
    """
    h, w = rgb_np.shape[:2]
    protected = np.zeros((h, w), dtype=np.uint8)

    top = int(h * protect_top_ratio)
    bottom = int(h * protect_bottom_ratio)
    left = int(w * protect_left_ratio)
    right = int(w * protect_right_ratio)

    if top > 0:
        protected[:top, :] = 255
    if bottom > 0:
        protected[h - bottom :, :] = 255
    if left > 0:
        protected[:, :left] = 255
    if right > 0:
        protected[:, w - right :] = 255

    return protected


def estimate_hair_mask_product(
    rgb_np: np.ndarray,
    protect_top_ratio: float = 0.18,
    protect_bottom_ratio: float = 0.02,
    protect_left_ratio: float = 0.08,
    protect_right_ratio: float = 0.08,
) -> np.ndarray:
    """
    Pour visuels produit/extensions :
    - on isole l'objet principal
    - on retire des zones protégées pour éviter watermark / texte / UI
    """
    obj_mask = estimate_object_mask(rgb_np)
    protected = build_protected_zone_mask(
        rgb_np,
        protect_top_ratio=protect_top_ratio,
        protect_bottom_ratio=protect_bottom_ratio,
        protect_left_ratio=protect_left_ratio,
        protect_right_ratio=protect_right_ratio,
    )

    hair_mask = cv2.bitwise_and(obj_mask, cv2.bitwise_not(protected))
    hair_mask = clean_mask(hair_mask, blur=5, morph=5)
    return hair_mask


# ----------------------------
# Reference color analysis
# ----------------------------
def compute_reference_profile(ref_rgb: np.ndarray, ref_mask: np.ndarray) -> np.ndarray:
    """
    Extrait un profil vertical LAB moyen depuis la référence.
    Garde l'idée du dégradé haut/bas sans casser la texture du gabarit.
    """
    ref_lab = cv2.cvtColor(ref_rgb, cv2.COLOR_RGB2LAB).astype(np.float32)
    h, _ = ref_mask.shape

    profile = np.zeros((h, 3), dtype=np.float32)

    for y in range(h):
        row_mask = ref_mask[y] > 0
        if np.any(row_mask):
            row_pixels = ref_lab[y][row_mask]
            profile[y] = row_pixels.mean(axis=0)
        else:
            profile[y] = np.array([0, 128, 128], dtype=np.float32)

    valid = profile[:, 0] > 0
    if valid.any():
        valid_idx = np.where(valid)[0]
        for c in range(3):
            profile[:, c] = np.interp(np.arange(h), valid_idx, profile[valid_idx, c])
    else:
        profile[:] = np.array([200, 128, 128], dtype=np.float32)

    return profile


# ----------------------------
# Recolor pipeline
# ----------------------------
def recolor_hair_with_reference(
    target_rgb: np.ndarray,
    target_mask: np.ndarray,
    ref_profile: np.ndarray,
    strength: float = 0.65,
    root_boost: float = 0.10,
    warmth_shift: float = 0.0,
) -> np.ndarray:
    """
    - garde la luminosité L du gabarit -> texture/reflets conservés
    - transfère surtout a/b -> couleur
    - root_boost renforce légèrement le haut
    - warmth_shift permet d'ajuster chaud/froid
    """
    target_lab = cv2.cvtColor(target_rgb, cv2.COLOR_RGB2LAB).astype(np.float32)
    h, w = target_mask.shape
    ref_profile = resize_profile(ref_profile, h)

    result = target_lab.copy()

    for y in range(h):
        row_mask = target_mask[y] > 0
        if not np.any(row_mask):
            continue

        vertical_ratio = y / max(h - 1, 1)
        boost = 1.0 + (1.0 - vertical_ratio) * root_boost

        ref_a = ref_profile[y, 1]
        ref_b = ref_profile[y, 2] + warmth_shift

        result[y, row_mask, 1] = (
            result[y, row_mask, 1] * (1 - strength) + ref_a * strength * boost
        )
        result[y, row_mask, 2] = (
            result[y, row_mask, 2] * (1 - strength) + ref_b * strength * boost
        )

    out = cv2.cvtColor(np.clip(result, 0, 255).astype(np.uint8), cv2.COLOR_LAB2RGB)
    return out


def feather_blend(original: np.ndarray, recolored: np.ndarray, mask: np.ndarray) -> np.ndarray:
    alpha = (mask.astype(np.float32) / 255.0)[..., None]
    blended = original.astype(np.float32) * (1 - alpha) + recolored.astype(np.float32) * alpha
    return np.clip(blended, 0, 255).astype(np.uint8)


def save_rgb_jpg(rgb_np: np.ndarray, path: str, quality: int = 97):
    bgr = cv2.cvtColor(rgb_np, cv2.COLOR_RGB2BGR)
    cv2.imwrite(path, bgr, [int(cv2.IMWRITE_JPEG_QUALITY), quality])


# ----------------------------
# UI
# ----------------------------
with st.sidebar:
    st.header("Réglages")

    sku = st.text_input("SKU / nom export", value="luxura-color")
    strength = st.slider("Force transfert couleur", 0.20, 1.00, 0.68, 0.01)
    root_boost = st.slider("Renfort racine / haut", 0.00, 0.30, 0.10, 0.01)
    warmth_shift = st.slider("Ajustement chaud ↔ froid", -20.0, 20.0, 0.0, 0.5)

    st.subheader("Protection zones")
    protect_top = st.slider("Protection haut", 0.00, 0.40, 0.18, 0.01)
    protect_bottom = st.slider("Protection bas", 0.00, 0.30, 0.02, 0.01)
    protect_left = st.slider("Protection gauche", 0.00, 0.35, 0.08, 0.01)
    protect_right = st.slider("Protection droite", 0.00, 0.35, 0.08, 0.01)

    show_masks = st.toggle("Afficher les masques", value=True)
    jpg_quality = st.slider("Qualité JPG export", 90, 100, 97, 1)

col1, col2, col3 = st.columns(3)
with col1:
    gab1_file = st.file_uploader("Gabarit 1", type=["jpg", "jpeg", "png"])
with col2:
    gab2_file = st.file_uploader("Gabarit 2", type=["jpg", "jpeg", "png"])
with col3:
    ref_file = st.file_uploader("Référence couleur", type=["jpg", "jpeg", "png"])

generate = st.button("Générer", type="primary", use_container_width=True)

if generate and gab1_file and gab2_file and ref_file:
    gab1_rgb = pil_to_rgb_np(Image.open(gab1_file))
    gab2_rgb = pil_to_rgb_np(Image.open(gab2_file))
    ref_rgb = pil_to_rgb_np(Image.open(ref_file))

    with st.spinner("Analyse référence + masque + recolorisation..."):
        ref_mask = estimate_hair_mask_product(
            ref_rgb,
            protect_top_ratio=protect_top,
            protect_bottom_ratio=protect_bottom,
            protect_left_ratio=protect_left,
            protect_right_ratio=protect_right,
        )

        gab1_mask = estimate_hair_mask_product(
            gab1_rgb,
            protect_top_ratio=protect_top,
            protect_bottom_ratio=protect_bottom,
            protect_left_ratio=protect_left,
            protect_right_ratio=protect_right,
        )

        gab2_mask = estimate_hair_mask_product(
            gab2_rgb,
            protect_top_ratio=protect_top,
            protect_bottom_ratio=protect_bottom,
            protect_left_ratio=protect_left,
            protect_right_ratio=protect_right,
        )

        ref_profile = compute_reference_profile(ref_rgb, ref_mask)

        gab1_recolored = recolor_hair_with_reference(
            gab1_rgb, gab1_mask, ref_profile,
            strength=strength,
            root_boost=root_boost,
            warmth_shift=warmth_shift
        )
        gab2_recolored = recolor_hair_with_reference(
            gab2_rgb, gab2_mask, ref_profile,
            strength=strength,
            root_boost=root_boost,
            warmth_shift=warmth_shift
        )

        out1 = feather_blend(gab1_rgb, gab1_recolored, gab1_mask)
        out2 = feather_blend(gab2_rgb, gab2_recolored, gab2_mask)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file1 = f"{sku}-gabarit1-{timestamp}.jpg"
        file2 = f"{sku}-gabarit2-{timestamp}.jpg"
        path1 = os.path.join(OUTPUT_DIR, file1)
        path2 = os.path.join(OUTPUT_DIR, file2)

        save_rgb_jpg(out1, path1, quality=jpg_quality)
        save_rgb_jpg(out2, path2, quality=jpg_quality)

    st.success("Génération terminée.")

    p1, p2 = st.columns(2)
    with p1:
        st.image(out1, caption="Gabarit 1 recolorisé", use_container_width=True)
        with open(path1, "rb") as f:
            st.download_button(
                "Télécharger Gabarit 1",
                f.read(),
                file_name=file1,
                mime="image/jpeg",
                use_container_width=True,
            )
        if show_masks:
            st.image(gab1_mask, caption="Masque Gabarit 1", use_container_width=True, clamp=True)

    with p2:
        st.image(out2, caption="Gabarit 2 recolorisé", use_container_width=True)
        with open(path2, "rb") as f:
            st.download_button(
                "Télécharger Gabarit 2",
                f.read(),
                file_name=file2,
                mime="image/jpeg",
                use_container_width=True,
            )
        if show_masks:
            st.image(gab2_mask, caption="Masque Gabarit 2", use_container_width=True, clamp=True)

    if show_masks:
        st.image(ref_mask, caption="Masque Référence", use_container_width=True, clamp=True)

else:
    st.info("Charge les 2 gabarits et 1 référence, puis clique sur Générer.")
