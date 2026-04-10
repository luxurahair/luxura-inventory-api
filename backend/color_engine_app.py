#!/usr/bin/env python3
"""
Luxura Color Engine PRO v2
Avec répertoire de couleurs intégré pour créer et modifier les images produits.
"""

import streamlit as st
from PIL import Image, ImageEnhance, ImageFilter, ImageDraw, ImageFont
import numpy as np
import io
import os
import json
from pathlib import Path
from datetime import datetime

# Configuration
st.set_page_config(
    page_title="Luxura Color Engine PRO",
    page_icon="🎨",
    layout="wide"
)

# Paths
BASE_DIR = Path(__file__).parent / "luxura_images"
WATERMARKS_DIR = BASE_DIR / "watermarks"
COLOR_LIBRARY_DIR = BASE_DIR / "color_library"
COLOR_LIBRARY_DIR.mkdir(exist_ok=True)

# Séries disponibles
SERIES = {
    "genius": {"name": "Vivian", "watermark": "VIVIAN", "description": "Extensions à Trame Invisible"},
    "halo": {"name": "Everly", "watermark": "EVERLY", "description": "Extensions Halo"},
    "tape": {"name": "Aurora", "watermark": "AURORA", "description": "Extensions à Bandes Adhésives"},
    "i-tip": {"name": "Eleanor", "watermark": "ELEANOR", "description": "Extensions à Kératine"},
}

# Fichier JSON pour stocker les métadonnées des couleurs
COLOR_METADATA_FILE = COLOR_LIBRARY_DIR / "colors_metadata.json"

def load_color_metadata():
    """Load color metadata from JSON file"""
    if COLOR_METADATA_FILE.exists():
        with open(COLOR_METADATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_color_metadata(metadata):
    """Save color metadata to JSON file"""
    with open(COLOR_METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

def get_colors_for_category(category):
    """Get all colors in a category"""
    cat_dir = COLOR_LIBRARY_DIR / category
    if not cat_dir.exists():
        cat_dir.mkdir(exist_ok=True)
        return []
    
    colors = []
    metadata = load_color_metadata()
    
    for img_file in cat_dir.glob("*.jpg"):
        color_code = img_file.stem
        color_info = metadata.get(f"{category}/{color_code}", {})
        colors.append({
            "code": color_code,
            "name": color_info.get("name", color_code),
            "path": str(img_file),
            "description": color_info.get("description", ""),
            "added_date": color_info.get("added_date", "")
        })
    
    for img_file in cat_dir.glob("*.png"):
        color_code = img_file.stem
        color_info = metadata.get(f"{category}/{color_code}", {})
        colors.append({
            "code": color_code,
            "name": color_info.get("name", color_code),
            "path": str(img_file),
            "description": color_info.get("description", ""),
            "added_date": color_info.get("added_date", "")
        })
    
    return colors

def save_color_to_library(image, category, color_code, color_name, description=""):
    """Save a color reference image to the library"""
    cat_dir = COLOR_LIBRARY_DIR / category
    cat_dir.mkdir(exist_ok=True)
    
    # Save image
    file_path = cat_dir / f"{color_code}.jpg"
    if image.mode == "RGBA":
        image = image.convert("RGB")
    image.save(file_path, "JPEG", quality=95)
    
    # Update metadata
    metadata = load_color_metadata()
    metadata[f"{category}/{color_code}"] = {
        "name": color_name,
        "description": description,
        "added_date": datetime.now().isoformat()
    }
    save_color_metadata(metadata)
    
    return file_path

def load_watermark(series_name="VIVIAN"):
    """Load the series watermark"""
    watermark_path = WATERMARKS_DIR / f"{series_name}.png"
    if watermark_path.exists():
        return Image.open(watermark_path).convert("RGBA")
    return None

def load_logo():
    """Load the Luxura logo"""
    logo_path = WATERMARKS_DIR / "LUXURA_LOGO.png"
    if logo_path.exists():
        return Image.open(logo_path).convert("RGBA")
    return None

def transfer_color(template_img, reference_img, intensity=0.8, preserve_highlights=True):
    """Transfer color from reference to template while preserving texture"""
    template = template_img.convert("RGB")
    reference = reference_img.convert("RGB")
    
    # Convert to numpy arrays
    template_arr = np.array(template, dtype=np.float32)
    reference_arr = np.array(reference.resize(template.size), dtype=np.float32)
    
    # Calculate mean and std for each channel
    t_mean = np.mean(template_arr, axis=(0, 1))
    t_std = np.std(template_arr, axis=(0, 1))
    r_mean = np.mean(reference_arr, axis=(0, 1))
    r_std = np.std(reference_arr, axis=(0, 1))
    
    # Normalize template, apply reference stats
    result = (template_arr - t_mean) * (r_std / (t_std + 1e-6)) + r_mean
    
    # Blend with original based on intensity
    result = template_arr * (1 - intensity) + result * intensity
    
    # Preserve highlights if requested
    if preserve_highlights:
        luminance = 0.299 * template_arr[:,:,0] + 0.587 * template_arr[:,:,1] + 0.114 * template_arr[:,:,2]
        highlight_mask = (luminance > 200).astype(np.float32)
        highlight_mask = np.stack([highlight_mask] * 3, axis=-1)
        result = result * (1 - highlight_mask * 0.5) + template_arr * (highlight_mask * 0.5)
    
    result = np.clip(result, 0, 255).astype(np.uint8)
    return Image.fromarray(result)

def add_watermark(image, series="VIVIAN", add_logo=True):
    """Add series watermark and Luxura logo to image"""
    result = image.convert("RGBA")
    width, height = result.size
    
    if add_logo:
        logo = load_logo()
        if logo:
            logo_width = int(width * 0.25)
            logo_ratio = logo.height / logo.width
            logo_height = int(logo_width * logo_ratio)
            logo = logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)
            result.paste(logo, (20, 20), logo)
    
    watermark = load_watermark(series)
    if watermark:
        wm_width = int(width * 0.4)
        wm_ratio = watermark.height / watermark.width
        wm_height = int(wm_width * wm_ratio)
        watermark = watermark.resize((wm_width, wm_height), Image.Resampling.LANCZOS)
        wm_x = (width - wm_width) // 2
        wm_y = height - wm_height - 20
        result.paste(watermark, (wm_x, wm_y), watermark)
    
    return result

def enhance_image(image, brightness=1.0, contrast=1.0, saturation=1.0, sharpness=1.0):
    """Apply image enhancements"""
    result = image.convert("RGB")
    
    if brightness != 1.0:
        result = ImageEnhance.Brightness(result).enhance(brightness)
    if contrast != 1.0:
        result = ImageEnhance.Contrast(result).enhance(contrast)
    if saturation != 1.0:
        result = ImageEnhance.Color(result).enhance(saturation)
    if sharpness != 1.0:
        result = ImageEnhance.Sharpness(result).enhance(sharpness)
    
    return result

# ==================== UI ====================

st.title("🎨 Luxura Color Engine PRO v2")

# Tabs for different functions
tab1, tab2, tab3 = st.tabs(["🖼️ Créer une Image", "📚 Répertoire de Couleurs", "⬆️ Ajouter une Couleur"])

# ==================== TAB 1: Create Image ====================
with tab1:
    st.markdown("### Créer une nouvelle image produit")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📐 Gabarit Fixe")
        gabarit_file = st.file_uploader(
            "Chargez le gabarit (forme validée)",
            type=["png", "jpg", "jpeg"],
            key="gabarit_create"
        )
        if gabarit_file:
            gabarit_img = Image.open(gabarit_file)
            st.image(gabarit_img, caption="Gabarit chargé", use_container_width=True)
    
    with col2:
        st.subheader("🎨 Couleur de Référence")
        
        # Choose between library or upload
        color_source = st.radio(
            "Source de la couleur",
            ["📚 Répertoire de couleurs", "📤 Uploader une nouvelle"],
            horizontal=True
        )
        
        reference_img = None
        selected_color_name = ""
        
        if color_source == "📚 Répertoire de couleurs":
            # Select category
            category = st.selectbox(
                "Catégorie",
                list(SERIES.keys()),
                format_func=lambda x: f"{SERIES[x]['name']} ({x.upper()})"
            )
            
            # Get colors for category
            colors = get_colors_for_category(category)
            
            if colors:
                # Display color grid
                color_cols = st.columns(4)
                for idx, color in enumerate(colors):
                    with color_cols[idx % 4]:
                        try:
                            img = Image.open(color["path"])
                            img_thumb = img.copy()
                            img_thumb.thumbnail((100, 100))
                            if st.button(f"📷", key=f"color_{idx}", help=color["name"]):
                                st.session_state["selected_color"] = color
                            st.image(img_thumb, caption=color["name"][:15], use_container_width=True)
                        except:
                            st.write(f"❌ {color['code']}")
                
                # Show selected color
                if "selected_color" in st.session_state:
                    selected = st.session_state["selected_color"]
                    reference_img = Image.open(selected["path"])
                    selected_color_name = selected["name"]
                    st.success(f"✅ Couleur sélectionnée: {selected_color_name}")
                    st.image(reference_img, caption=selected_color_name, use_container_width=True)
            else:
                st.warning("Aucune couleur dans cette catégorie. Ajoutez-en dans l'onglet '⬆️ Ajouter une Couleur'")
        
        else:
            # Upload new reference
            ref_file = st.file_uploader(
                "Photo de référence couleur",
                type=["png", "jpg", "jpeg"],
                key="ref_create"
            )
            if ref_file:
                reference_img = Image.open(ref_file)
                selected_color_name = ref_file.name.split(".")[0]
                st.image(reference_img, caption="Référence couleur", use_container_width=True)
    
    st.divider()
    
    # Settings
    st.subheader("⚙️ Paramètres")
    col_s1, col_s2, col_s3 = st.columns(3)
    
    with col_s1:
        intensity = st.slider("Intensité du transfert", 0.0, 1.0, 0.75, 0.05, key="int_create")
        preserve_highlights = st.checkbox("Préserver les reflets", value=True, key="ph_create")
    
    with col_s2:
        brightness = st.slider("Luminosité", 0.5, 1.5, 1.0, 0.05, key="br_create")
        contrast = st.slider("Contraste", 0.5, 1.5, 1.0, 0.05, key="co_create")
    
    with col_s3:
        saturation = st.slider("Saturation", 0.5, 1.5, 1.0, 0.05, key="sa_create")
        sharpness = st.slider("Netteté", 0.5, 2.0, 1.0, 0.1, key="sh_create")
    
    # Watermark settings
    col_w1, col_w2 = st.columns(2)
    with col_w1:
        series = st.selectbox(
            "Série (Watermark)",
            list(SERIES.keys()),
            format_func=lambda x: f"Série {SERIES[x]['name']}",
            key="series_create"
        )
    with col_w2:
        add_logo = st.checkbox("Logo Luxura", value=True, key="logo_create")
        add_wm = st.checkbox("Watermark de série", value=True, key="wm_create")
    
    st.divider()
    
    # Generate
    if gabarit_file and reference_img:
        if st.button("🚀 Générer l'Image", type="primary", use_container_width=True):
            with st.spinner("Génération en cours..."):
                result = transfer_color(gabarit_img, reference_img, intensity, preserve_highlights)
                result = enhance_image(result, brightness, contrast, saturation, sharpness)
                
                if add_wm or add_logo:
                    result = add_watermark(result, SERIES[series]["watermark"], add_logo)
                
                st.success("✅ Image générée !")
                st.image(result, caption=f"Série {SERIES[series]['name']} - {selected_color_name}", use_container_width=True)
                
                # Download
                buf = io.BytesIO()
                result.convert("RGB").save(buf, format="JPEG", quality=95)
                buf.seek(0)
                
                st.download_button(
                    "📥 Télécharger",
                    data=buf,
                    file_name=f"{series.upper()}_{selected_color_name.replace(' ', '_')}.jpg",
                    mime="image/jpeg",
                    use_container_width=True
                )
    else:
        st.info("👆 Chargez un gabarit et sélectionnez une couleur pour commencer")

# ==================== TAB 2: Color Library ====================
with tab2:
    st.markdown("### 📚 Répertoire de Couleurs")
    st.markdown("Toutes les couleurs de référence enregistrées")
    
    for cat_key, cat_info in SERIES.items():
        st.subheader(f"Série {cat_info['name']} ({cat_key.upper()})")
        st.caption(cat_info['description'])
        
        colors = get_colors_for_category(cat_key)
        
        if colors:
            cols = st.columns(5)
            for idx, color in enumerate(colors):
                with cols[idx % 5]:
                    try:
                        img = Image.open(color["path"])
                        st.image(img, caption=f"{color['name']}\n#{color['code']}", use_container_width=True)
                    except:
                        st.error(f"❌ {color['code']}")
        else:
            st.info(f"Aucune couleur pour {cat_info['name']}")
        
        st.divider()

# ==================== TAB 3: Add Color ====================
with tab3:
    st.markdown("### ⬆️ Ajouter une Nouvelle Couleur au Répertoire")
    
    col_add1, col_add2 = st.columns([1, 2])
    
    with col_add1:
        add_category = st.selectbox(
            "Catégorie",
            list(SERIES.keys()),
            format_func=lambda x: f"Série {SERIES[x]['name']}",
            key="add_cat"
        )
        
        color_code = st.text_input(
            "Code couleur (ex: 6, DC, HPS)",
            placeholder="6",
            key="add_code"
        )
        
        color_name = st.text_input(
            "Nom de la couleur",
            placeholder="Caramel Doré",
            key="add_name"
        )
        
        color_desc = st.text_area(
            "Description (optionnel)",
            placeholder="Couleur chaude avec reflets dorés",
            key="add_desc"
        )
    
    with col_add2:
        color_file = st.file_uploader(
            "Image de référence couleur",
            type=["png", "jpg", "jpeg"],
            key="add_file"
        )
        
        if color_file:
            color_img = Image.open(color_file)
            st.image(color_img, caption="Aperçu", use_container_width=True)
    
    if color_file and color_code and color_name:
        if st.button("💾 Enregistrer dans le Répertoire", type="primary"):
            saved_path = save_color_to_library(
                color_img,
                add_category,
                color_code.upper().replace(" ", "_"),
                color_name,
                color_desc
            )
            st.success(f"✅ Couleur '{color_name}' enregistrée !")
            st.info(f"📁 Chemin: {saved_path}")
            st.balloons()
    else:
        st.warning("Remplissez le code, le nom et uploadez une image pour enregistrer")

# Footer
st.divider()
st.caption("🎨 Luxura Color Engine PRO v2 • Répertoire de couleurs intégré • Luxura Distribution")
