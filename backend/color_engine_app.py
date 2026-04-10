#!/usr/bin/env python3
"""
Luxura Color Engine PRO - Série Vivian
Outil de recolorisation d'images d'extensions capillaires avec gabarit verrouillé.
"""

import streamlit as st
from PIL import Image, ImageEnhance, ImageFilter, ImageDraw, ImageFont
import numpy as np
import io
import colorsys
from pathlib import Path

# Configuration
st.set_page_config(
    page_title="Luxura Color Engine PRO",
    page_icon="🎨",
    layout="wide"
)

# Paths
WATERMARKS_DIR = Path(__file__).parent / "luxura_images" / "watermarks"

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

def extract_dominant_color(image, num_colors=5):
    """Extract dominant colors from reference image"""
    img = image.convert("RGB")
    img = img.resize((150, 150))
    pixels = list(img.getdata())
    
    # Simple color clustering
    from collections import Counter
    color_counts = Counter(pixels)
    dominant_colors = color_counts.most_common(num_colors)
    
    return [color for color, count in dominant_colors]

def rgb_to_hsv(r, g, b):
    """Convert RGB to HSV"""
    return colorsys.rgb_to_hsv(r/255, g/255, b/255)

def hsv_to_rgb(h, s, v):
    """Convert HSV to RGB"""
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return int(r*255), int(g*255), int(b*255)

def transfer_color(template_img, reference_img, intensity=0.8, preserve_highlights=True):
    """
    Transfer color from reference to template while preserving texture and shape.
    Uses LAB color space for better color transfer.
    """
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
        # Create luminance mask
        luminance = 0.299 * template_arr[:,:,0] + 0.587 * template_arr[:,:,1] + 0.114 * template_arr[:,:,2]
        highlight_mask = (luminance > 200).astype(np.float32)
        highlight_mask = np.stack([highlight_mask] * 3, axis=-1)
        
        # Blend highlights back
        result = result * (1 - highlight_mask * 0.5) + template_arr * (highlight_mask * 0.5)
    
    # Clip values
    result = np.clip(result, 0, 255).astype(np.uint8)
    
    return Image.fromarray(result)

def apply_color_overlay(template_img, color, intensity=0.6):
    """Apply a solid color overlay with blending"""
    template = template_img.convert("RGBA")
    
    # Create color overlay
    overlay = Image.new("RGBA", template.size, color + (int(255 * intensity),))
    
    # Blend using multiply mode
    result = Image.new("RGBA", template.size)
    
    for x in range(template.width):
        for y in range(template.height):
            t_pixel = template.getpixel((x, y))
            o_pixel = overlay.getpixel((x, y))
            
            # Multiply blend
            r = int((t_pixel[0] * o_pixel[0]) / 255)
            g = int((t_pixel[1] * o_pixel[1]) / 255)
            b = int((t_pixel[2] * o_pixel[2]) / 255)
            a = t_pixel[3]
            
            result.putpixel((x, y), (r, g, b, a))
    
    return result

def add_watermark(image, series="VIVIAN", add_logo=True):
    """Add series watermark and Luxura logo to image"""
    result = image.convert("RGBA")
    width, height = result.size
    
    # Add Luxura logo (top left)
    if add_logo:
        logo = load_logo()
        if logo:
            logo_width = int(width * 0.25)
            logo_ratio = logo.height / logo.width
            logo_height = int(logo_width * logo_ratio)
            logo = logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)
            result.paste(logo, (20, 20), logo)
    
    # Add series watermark (bottom center)
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
        enhancer = ImageEnhance.Brightness(result)
        result = enhancer.enhance(brightness)
    
    if contrast != 1.0:
        enhancer = ImageEnhance.Contrast(result)
        result = enhancer.enhance(contrast)
    
    if saturation != 1.0:
        enhancer = ImageEnhance.Color(result)
        result = enhancer.enhance(saturation)
    
    if sharpness != 1.0:
        enhancer = ImageEnhance.Sharpness(result)
        result = enhancer.enhance(sharpness)
    
    return result

# UI
st.title("🎨 Luxura Color Engine PRO")
st.markdown("### Série Vivian - Recolorisation avec Gabarit Verrouillé")

st.markdown("""
**Instructions :**
1. Chargez votre **gabarit fixe** (la forme de mèche validée)
2. Chargez une **photo de référence couleur** (la couleur à appliquer)
3. Ajustez les paramètres si nécessaire
4. Générez et téléchargez le résultat
""")

st.divider()

# File uploaders
col1, col2 = st.columns(2)

with col1:
    st.subheader("📐 Gabarit Fixe")
    gabarit_file = st.file_uploader(
        "Chargez le gabarit (forme validée)",
        type=["png", "jpg", "jpeg"],
        key="gabarit"
    )
    if gabarit_file:
        gabarit_img = Image.open(gabarit_file)
        st.image(gabarit_img, caption="Gabarit chargé", use_container_width=True)

with col2:
    st.subheader("🎨 Référence Couleur")
    reference_file = st.file_uploader(
        "Chargez la photo de référence couleur",
        type=["png", "jpg", "jpeg"],
        key="reference"
    )
    if reference_file:
        reference_img = Image.open(reference_file)
        st.image(reference_img, caption="Référence couleur", use_container_width=True)

st.divider()

# Settings
st.subheader("⚙️ Paramètres")

col_settings1, col_settings2, col_settings3 = st.columns(3)

with col_settings1:
    intensity = st.slider("Intensité du transfert", 0.0, 1.0, 0.75, 0.05)
    preserve_highlights = st.checkbox("Préserver les reflets", value=True)

with col_settings2:
    brightness = st.slider("Luminosité", 0.5, 1.5, 1.0, 0.05)
    contrast = st.slider("Contraste", 0.5, 1.5, 1.0, 0.05)

with col_settings3:
    saturation = st.slider("Saturation", 0.5, 1.5, 1.0, 0.05)
    sharpness = st.slider("Netteté", 0.5, 2.0, 1.0, 0.1)

st.divider()

# Watermark settings
col_wm1, col_wm2 = st.columns(2)

with col_wm1:
    series = st.selectbox(
        "Série (Watermark)",
        ["VIVIAN", "EVERLY", "AURORA", "ELEANOR"],
        index=0
    )

with col_wm2:
    add_logo = st.checkbox("Ajouter le logo Luxura", value=True)
    add_watermark_option = st.checkbox("Ajouter le watermark de série", value=True)

st.divider()

# Generate button
if gabarit_file and reference_file:
    if st.button("🚀 Générer la Nouvelle Mèche", type="primary", use_container_width=True):
        with st.spinner("Application de la couleur sur le gabarit..."):
            # Step 1: Transfer color
            result = transfer_color(
                gabarit_img, 
                reference_img, 
                intensity=intensity,
                preserve_highlights=preserve_highlights
            )
            
            # Step 2: Apply enhancements
            result = enhance_image(
                result,
                brightness=brightness,
                contrast=contrast,
                saturation=saturation,
                sharpness=sharpness
            )
            
            # Step 3: Add watermarks
            if add_watermark_option or add_logo:
                result = add_watermark(
                    result,
                    series=series,
                    add_logo=add_logo
                )
            
            st.success("✅ Image générée avec succès !")
            
            # Display result
            st.subheader("📸 Résultat Final")
            st.image(result, caption=f"Série {series} - Nouvelle Couleur", use_container_width=True)
            
            # Download button
            buf = io.BytesIO()
            result_rgb = result.convert("RGB")
            result_rgb.save(buf, format="JPEG", quality=95)
            buf.seek(0)
            
            col_dl1, col_dl2 = st.columns(2)
            with col_dl1:
                st.download_button(
                    label="📥 Télécharger (JPEG)",
                    data=buf,
                    file_name=f"GENIUS_{series}_nouvelle_couleur.jpg",
                    mime="image/jpeg",
                    use_container_width=True
                )
            
            with col_dl2:
                buf_png = io.BytesIO()
                result.save(buf_png, format="PNG")
                buf_png.seek(0)
                st.download_button(
                    label="📥 Télécharger (PNG)",
                    data=buf_png,
                    file_name=f"GENIUS_{series}_nouvelle_couleur.png",
                    mime="image/png",
                    use_container_width=True
                )

else:
    st.info("👆 Chargez un gabarit et une référence couleur pour commencer")

# Footer
st.divider()
st.caption("🎨 Luxura Color Engine PRO • Gabarit verrouillé + Watermark automatique • Luxura Distribution")
