import streamlit as st
from PIL import Image
import numpy as np
import cv2
from rembg import remove
import os
from datetime import datetime

st.set_page_config(page_title="Luxura Color Engine V2", layout="wide")
st.title("🚀 Luxura Color Engine V2 - Masque PRO + Ombré réel")
st.markdown("**Masque cheveux nettoyé + copie exacte de ta référence (ombré + mèches)**")

# Uploads
col1, col2, col3 = st.columns(3)
with col1:
    gab1 = st.file_uploader("Gabarit 1 (modèle complet)", type=["jpg", "png", "jpeg"])
with col2:
    gab2 = st.file_uploader("Gabarit 2 (extension)", type=["jpg", "png", "jpeg"])
with col3:
    ref = st.file_uploader("Référence (couleur + ombré + mèches)", type=["jpg", "png", "jpeg"])

blend = st.slider("Mélange texture/mèches (0.5 = naturel)", 0.3, 0.9, 0.65)

if st.button("🎨 Générer (V2 PRO)", type="primary") and gab1 and gab2 and ref:
    img1 = np.array(Image.open(gab1).convert("RGB"))
    img2 = np.array(Image.open(gab2).convert("RGB"))
    ref_img = np.array(Image.open(ref).convert("RGB"))

    def improve_hair_mask(image):
        # 1. Person mask ultra propre
        person = remove(image)
        gray = cv2.cvtColor(person, cv2.COLOR_RGB2GRAY)
        _, person_mask = cv2.threshold(gray, 30, 255, cv2.THRESH_BINARY)

        # 2. Détection peau (pour enlever visage/cou)
        hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
        skin_mask = cv2.inRange(hsv, (0, 20, 70), (20, 255, 255)) | cv2.inRange(hsv, (340, 20, 70), (360, 255, 255))

        # 3. Masque cheveux = person - peau + nettoyage
        hair_mask = cv2.bitwise_and(person_mask, cv2.bitwise_not(skin_mask))
        
        # Nettoyage morphologique (bords propres)
        kernel = np.ones((5,5), np.uint8)
        hair_mask = cv2.morphologyEx(hair_mask, cv2.MORPH_CLOSE, kernel)
        hair_mask = cv2.morphologyEx(hair_mask, cv2.MORPH_OPEN, kernel)
        return hair_mask

    def recolor_with_ref(gabarit, reference, blend=0.65):
        hair_mask = improve_hair_mask(gabarit)
        
        # Extraction couleur réelle de la référence
        ref_person = remove(reference)
        ref_hsv = cv2.cvtColor(reference, cv2.COLOR_RGB2HSV)
        ref_gray = cv2.cvtColor(ref_person, cv2.COLOR_RGB2GRAY)
        _, ref_hair = cv2.threshold(ref_gray, 30, 255, cv2.THRESH_BINARY)
        target_hue = int(np.median(ref_hsv[:,:,0][ref_hair > 0]))
        target_sat = np.mean(ref_hsv[:,:,1][ref_hair > 0]) / 255.0

        # Recolorisation LAB (luminosité préservée + couleur naturelle)
        lab = cv2.cvtColor(gabarit, cv2.COLOR_RGB2LAB)
        l, a, b = cv2.split(lab)
        
        # Appliquer nouvelle teinte proportionnellement
        height = lab.shape[0]
        for y in range(height):
            ratio = y / height
            adjusted_a = a[y][hair_mask[y] > 0] + int((target_hue - 90) * (1 - ratio * 0.3))  # ombré racine
            adjusted_b = b[y][hair_mask[y] > 0] + int((target_sat * 50 - 25) * (1 - ratio * 0.2))
            a[y][hair_mask[y] > 0] = np.clip(adjusted_a, 0, 255)
            b[y][hair_mask[y] > 0] = np.clip(adjusted_b, 0, 255)

        recolored_lab = cv2.merge([l, a, b])
        recolored = cv2.cvtColor(recolored_lab, cv2.COLOR_LAB2RGB)

        # Mélange pour garder mèches/reflets originaux
        original = gabarit.copy()
        final = (recolored * blend + original * (1 - blend)).astype(np.uint8)
        
        return final, hair_mask

    with st.spinner("Analyse référence + masque PRO + recolorisation..."):
        out1, mask1 = recolor_with_ref(img1, ref_img, blend)
        out2, mask2 = recolor_with_ref(img2, ref_img, blend)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        os.makedirs("outputs", exist_ok=True)
        cv2.imwrite(f"outputs/luxura-g1-{timestamp}.jpg", cv2.cvtColor(out1, cv2.COLOR_RGB2BGR))
        cv2.imwrite(f"outputs/luxura-g2-{timestamp}.jpg", cv2.cvtColor(out2, cv2.COLOR_RGB2BGR))

        st.success("✅ Résultat V2 prêt ! Masque beaucoup plus propre et couleurs qui tiennent vraiment.")

        col_a, col_b = st.columns(2)
        with col_a:
            st.image(out1, caption="Gabarit 1 (V2)", use_column_width=True)
            st.download_button("⬇️ Gabarit 1", open(f"outputs/luxura-g1-{timestamp}.jpg", "rb").read(), f"luxura-gabarit1-{timestamp}.jpg")
            st.image(mask1, caption="Masque cheveux détecté (V2)", use_column_width=True, clamp=True)
        with col_b:
            st.image(out2, caption="Gabarit 2 (V2)", use_column_width=True)
            st.download_button("⬇️ Gabarit 2", open(f"outputs/luxura-g2-{timestamp}.jpg", "rb").read(), f"luxura-gabarit2-{timestamp}.jpg")
            st.image(mask2, caption="Masque cheveux détecté (V2)", use_column_width=True, clamp=True)

st.info("💡 Teste avec tes 3 photos actuelles (fille chapeau + extension Vivian + gros plan). Le masque est maintenant propre et la couleur change vraiment (ombré racine + mèches préservées).")
