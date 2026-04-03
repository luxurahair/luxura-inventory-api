import os
from io import BytesIO
from datetime import datetime

import cv2
import numpy as np
import streamlit as st
from PIL import Image
from rembg import remove

st.set_page_config(page_title="Luxura Color Engine", layout="wide")
st.title("Luxura Color Engine")
st.caption("Upload 2 gabarits + 1 référence. Le gabarit reste intact, seule la mèche est recolorisée.")

OUTPUT_DIR = "outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def pil_to_rgb_np(img: Image.Image) -> np.ndarray:
    return np.array(img.convert("RGB"))


def remove_bg_rgba(rgb_np: np.ndarray) -> np.ndarray:
    pil_img = Image.fromarray(rgb_np)
    out = remove(pil_img)
    if isinstance(out, bytes):
        out = Image.open(BytesIO(out))
    return np.array(out.convert("RGBA"))


def alpha_mask_from_rgba(rgba: np.ndarray, threshold: int = 10) -> np.ndarray:
    alpha = rgba[:, :, 3]
    mask = np.where(alpha > threshold, 255, 0).astype(np.uint8)
    return mask


def clean_mask(mask: np.ndarray, ksize: int = 5) -> np.ndarray:
    kernel = np.ones((ksize, ksize), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.GaussianBlur(mask, (5, 5), 0)
    return mask


def estimate_hair_mask(rgb_np: np.ndarray) -> np.ndarray:
    """
    Base simple :
    - rembg isole l'objet principal
    - on nettoie le masque
    Pour les extensions produit sur fond uni, ça marche bien mieux que pour un humain complet.
    """
    rgba = remove_bg_rgba(rgb_np)
    mask = alpha_mask_from_rgba(rgba)
    mask = clean_mask(mask, 5)
    return mask


def compute_reference_profile(ref_rgb: np.ndarray, ref_mask: np.ndarray):
    """
    Extrait un profil couleur vertical moyen sur la référence.
    Permet de récupérer l'idée de l'ombré sans réinventer toute l'image.
    """
    ref_lab = cv2.cvtColor(ref_rgb, cv2.COLOR_RGB2LAB).astype(np.float32)

    h, w = ref_mask.shape
    profile = []

    for y in range(h):
        row_mask = ref_mask[y] > 0
        if np.any(row_mask):
            row_pixels = ref_lab[y][row_mask]
            mean_lab = row_pixels.mean(axis=0)
        else:
            mean_lab = np.array([0, 128, 128], dtype=np.float32)
        profile.append(mean_lab)

    profile = np.array(profile, dtype=np.float32)

    # Remplissage des trous éventuels
    valid = profile[:, 0] > 0
    if valid.any():
        valid_idx = np.where(valid)[0]
        for c in range(3):
            profile[:, c] = np.interp(
                np.arange(h),
                valid_idx,
                profile[valid_idx, c]
            )
    else:
        profile[:] = np.array([200, 128, 128], dtype=np.float32)

    return profile


def recolor_hair_with_reference(
    target_rgb: np.ndarray,
    target_mask: np.ndarray,
    ref_profile: np.ndarray,
    strength: float = 0.65
) -> np.ndarray:
    """
    Recolorise uniquement la zone cheveux.
    Garde la luminosité et la texture du gabarit autant que possible.
    """
    target_lab = cv2.cvtColor(target_rgb, cv2.COLOR_RGB2LAB).astype(np.float32)
    h, w = target_mask.shape

    if len(ref_profile) != h:
        # Redimensionne le profil vertical à la hauteur du gabarit
        x_old = np.linspace(0, 1, len(ref_profile))
        x_new = np.linspace(0, 1, h)
        resized = np.zeros((h, 3), dtype=np.float32)
        for c in range(3):
            resized[:, c] = np.interp(x_new, x_old, ref_profile[:, c])
        ref_profile = resized

    result = target_lab.copy()

    for y in range(h):
        row_mask = target_mask[y] > 0
        if not np.any(row_mask):
            continue

        # On garde L du gabarit pour conserver relief/reflets.
        ref_a = ref_profile[y, 1]
        ref_b = ref_profile[y, 2]

        result[y, row_mask, 1] = (
            result[y, row_mask, 1] * (1 - strength) + ref_a * strength
        )
        result[y, row_mask, 2] = (
            result[y, row_mask, 2] * (1 - strength) + ref_b * strength
        )

    out = cv2.cvtColor(np.clip(result, 0, 255).astype(np.uint8), cv2.COLOR_LAB2RGB)
    return out


def save_rgb_jpg(rgb_np: np.ndarray, path: str):
    bgr = cv2.cvtColor(rgb_np, cv2.COLOR_RGB2BGR)
    cv2.imwrite(path, bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 95])


col1, col2, col3 = st.columns(3)
with col1:
    gab1_file = st.file_uploader("Gabarit 1", type=["jpg", "jpeg", "png"])
with col2:
    gab2_file = st.file_uploader("Gabarit 2", type=["jpg", "jpeg", "png"])
with col3:
    ref_file = st.file_uploader("Référence", type=["jpg", "jpeg", "png"])

strength = st.slider("Force de transfert couleur", 0.2, 1.0, 0.65, 0.05)
show_masks = st.toggle("Afficher les masques", value=True)

if st.button("Générer", type="primary") and gab1_file and gab2_file and ref_file:
    gab1 = pil_to_rgb_np(Image.open(gab1_file))
    gab2 = pil_to_rgb_np(Image.open(gab2_file))
    ref = pil_to_rgb_np(Image.open(ref_file))

    with st.spinner("Analyse et recolorisation en cours..."):
        ref_mask = estimate_hair_mask(ref)
        gab1_mask = estimate_hair_mask(gab1)
        gab2_mask = estimate_hair_mask(gab2)

        ref_profile = compute_reference_profile(ref, ref_mask)

        out1 = recolor_hair_with_reference(gab1, gab1_mask, ref_profile, strength)
        out2 = recolor_hair_with_reference(gab2, gab2_mask, ref_profile, strength)

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path1 = os.path.join(OUTPUT_DIR, f"luxura-gabarit1-{ts}.jpg")
        path2 = os.path.join(OUTPUT_DIR, f"luxura-gabarit2-{ts}.jpg")

        save_rgb_jpg(out1, path1)
        save_rgb_jpg(out2, path2)

    st.success("Images générées.")

    a, b = st.columns(2)
    with a:
        st.image(out1, caption="Gabarit 1", use_container_width=True)
        with open(path1, "rb") as f:
            st.download_button("Télécharger Gabarit 1", f.read(), file_name=os.path.basename(path1), mime="image/jpeg")
        if show_masks:
            st.image(gab1_mask, caption="Masque Gabarit 1", use_container_width=True, clamp=True)

    with b:
        st.image(out2, caption="Gabarit 2", use_container_width=True)
        with open(path2, "rb") as f:
            st.download_button("Télécharger Gabarit 2", f.read(), file_name=os.path.basename(path2), mime="image/jpeg")
        if show_masks:
            st.image(gab2_mask, caption="Masque Gabarit 2", use_container_width=True, clamp=True)

    if show_masks:
        st.image(ref_mask, caption="Masque Référence", use_container_width=True, clamp=True)
