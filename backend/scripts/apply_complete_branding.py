#!/usr/bin/env python3
"""
Script pour appliquer les watermarks Luxura + Logo sur les images produits.
- Logo Luxura en haut à gauche
- Watermark de série en bas au centre
"""

from PIL import Image, ImageEnhance
import os
from pathlib import Path

# Paths
BASE_DIR = Path("/app/backend/luxura_images")
WATERMARKS_DIR = BASE_DIR / "watermarks"
OUTPUT_DIR = BASE_DIR / "final_images"

# Category to Watermark mapping
CATEGORY_WATERMARK = {
    'genius': 'VIVIAN.png',      # Série Vivian - Extensions à Trame Invisible
    'halo': 'EVERLY.png',        # Série Everly
    'tape': 'AURORA.png',        # Série Aurora - Extensions à Bandes Adhésives
    'i-tip': 'ELEANOR.png',      # Série Eleanor - Extensions à Kératine
}

def load_image_with_transparency(path, target_width=None, opacity=1.0):
    """Load image with proper transparency handling"""
    img = Image.open(path).convert('RGBA')
    
    if target_width:
        ratio = img.height / img.width
        new_height = int(target_width * ratio)
        img = img.resize((target_width, new_height), Image.Resampling.LANCZOS)
    
    if opacity < 1.0:
        alpha = img.split()[3]
        alpha = ImageEnhance.Brightness(alpha).enhance(opacity)
        img.putalpha(alpha)
    
    return img

def apply_dual_watermark(image_path, logo, series_watermark, output_path):
    """Apply Luxura logo (top-left) and series watermark (bottom-center)"""
    try:
        img = Image.open(image_path).convert('RGBA')
        img_width, img_height = img.size
        
        # Create a working copy
        result = img.copy()
        
        # 1. Apply LUXURA LOGO - top left with margin
        logo_width = int(img_width * 0.25)  # 25% of image width
        logo_ratio = logo.height / logo.width
        logo_resized = logo.resize((logo_width, int(logo_width * logo_ratio)), Image.Resampling.LANCZOS)
        
        logo_x = 20  # Left margin
        logo_y = 20  # Top margin
        result.paste(logo_resized, (logo_x, logo_y), logo_resized)
        
        # 2. Apply SERIES WATERMARK - bottom center
        wm_width = int(img_width * 0.40)  # 40% of image width
        wm_ratio = series_watermark.height / series_watermark.width
        wm_resized = series_watermark.resize((wm_width, int(wm_width * wm_ratio)), Image.Resampling.LANCZOS)
        
        wm_x = (img_width - wm_resized.width) // 2
        wm_y = img_height - wm_resized.height - 20  # 20px from bottom
        result.paste(wm_resized, (wm_x, wm_y), wm_resized)
        
        # Save as high-quality JPEG
        result = result.convert('RGB')
        result.save(output_path, 'JPEG', quality=95)
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("🎨 Luxura Complete Watermark Application")
    print("   Logo Luxura (top-left) + Série (bottom-center)")
    print("=" * 60)
    
    # Create output directory
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    # Load Luxura logo once
    logo_path = WATERMARKS_DIR / "LUXURA_LOGO.png"
    if not logo_path.exists():
        print(f"❌ Luxura logo not found: {logo_path}")
        return
    
    logo = Image.open(logo_path).convert('RGBA')
    print(f"✅ Luxura logo loaded: {logo.size}")
    
    # Create subdirectories
    for cat in CATEGORY_WATERMARK.keys():
        (OUTPUT_DIR / f"{cat.upper()}_final").mkdir(exist_ok=True)
    
    # Process each category
    total_processed = 0
    total_success = 0
    
    for category, watermark_file in CATEGORY_WATERMARK.items():
        print(f"\n{'='*60}")
        print(f"📁 Processing {category.upper()}")
        print(f"   Série: {watermark_file.replace('.png', '')}")
        print(f"{'='*60}")
        
        # Load series watermark
        watermark_path = WATERMARKS_DIR / watermark_file
        if not watermark_path.exists():
            print(f"   ⚠️ Watermark not found: {watermark_path}")
            continue
        
        series_watermark = Image.open(watermark_path).convert('RGBA')
        
        # Input/Output folders
        input_folder = BASE_DIR / f"{category.upper()}_pictures"
        output_folder = OUTPUT_DIR / f"{category.upper()}_final"
        
        if not input_folder.exists():
            print(f"   ⚠️ Input folder not found: {input_folder}")
            continue
        
        # Process each image
        images = list(input_folder.glob("*.jpg")) + list(input_folder.glob("*.png"))
        
        for img_path in images:
            total_processed += 1
            output_path = output_folder / f"{img_path.stem}_luxura.jpg"
            
            print(f"\n   🖼️ {img_path.name}")
            
            if apply_dual_watermark(img_path, logo, series_watermark, output_path):
                total_success += 1
                print(f"      ✅ → {output_path.name}")
            else:
                print(f"      ❌ Failed")
    
    # Summary
    print(f"\n{'='*60}")
    print(f"📊 SUMMARY")
    print(f"{'='*60}")
    print(f"   Total images processed: {total_processed}")
    print(f"   Successfully branded: {total_success}")
    print(f"   Failed: {total_processed - total_success}")
    
    print(f"\n📁 Output folder: {OUTPUT_DIR}")
    for cat in CATEGORY_WATERMARK.keys():
        folder = OUTPUT_DIR / f"{cat.upper()}_final"
        count = len(list(folder.glob("*.jpg")))
        print(f"   ├── {cat.upper()}_final/ ({count} images)")
    
    print(f"\n✅ Images prêtes pour upload sur Wix/Google Drive!")

if __name__ == "__main__":
    main()
