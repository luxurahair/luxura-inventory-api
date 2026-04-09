#!/usr/bin/env python3
"""
Script pour appliquer les watermarks Luxura sur les images produits.
Applique le watermark correspondant à chaque catégorie en bas de l'image.
"""

from PIL import Image, ImageEnhance
import os
from pathlib import Path

# Paths
BASE_DIR = Path("/app/backend/luxura_images")
WATERMARKS_DIR = BASE_DIR / "watermarks"
OUTPUT_DIR = BASE_DIR / "watermarked"

# Category to Watermark mapping
CATEGORY_WATERMARK = {
    'genius': 'VIVIAN.png',      # Série Vivian - Extensions à Trame Invisible
    'halo': 'EVERLY.png',        # Série Everly
    'tape': 'AURORA.png',        # Série Aurora - Extensions à Bandes Adhésives
    'i-tip': 'ELEANOR.png',      # Série Eleanor - Extensions à Kératine
}

def load_watermark(watermark_name, target_width, opacity=0.85):
    """Load and prepare watermark with proper size and transparency"""
    watermark_path = WATERMARKS_DIR / watermark_name
    
    if not watermark_path.exists():
        print(f"❌ Watermark not found: {watermark_path}")
        return None
    
    watermark = Image.open(watermark_path).convert('RGBA')
    
    # Calculate new size (watermark width = 40% of image width)
    wm_ratio = watermark.height / watermark.width
    new_width = int(target_width * 0.40)
    new_height = int(new_width * wm_ratio)
    
    watermark = watermark.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # Apply opacity
    if opacity < 1.0:
        alpha = watermark.split()[3]
        alpha = ImageEnhance.Brightness(alpha).enhance(opacity)
        watermark.putalpha(alpha)
    
    return watermark

def apply_watermark(image_path, watermark, output_path):
    """Apply watermark to bottom center of image"""
    try:
        img = Image.open(image_path).convert('RGBA')
        img_width, img_height = img.size
        wm_width, wm_height = watermark.size
        
        # Position: bottom center with 20px margin from bottom
        x = (img_width - wm_width) // 2
        y = img_height - wm_height - 20
        
        # Create a copy for compositing
        result = img.copy()
        
        # Paste watermark with transparency
        result.paste(watermark, (x, y), watermark)
        
        # Convert back to RGB for JPEG saving
        result = result.convert('RGB')
        result.save(output_path, 'JPEG', quality=95)
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("🎨 Luxura Watermark Application Script")
    print("=" * 60)
    
    # Create output directory
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    # Create subdirectories for each category
    for cat in CATEGORY_WATERMARK.keys():
        (OUTPUT_DIR / f"{cat.upper()}_watermarked").mkdir(exist_ok=True)
    
    # Process each category
    total_processed = 0
    total_success = 0
    
    for category, watermark_file in CATEGORY_WATERMARK.items():
        print(f"\n{'='*60}")
        print(f"📁 Processing {category.upper()}")
        print(f"   Watermark: {watermark_file}")
        print(f"{'='*60}")
        
        # Load watermark (sized for 1200px images)
        watermark = load_watermark(watermark_file, 1200, opacity=0.90)
        if watermark is None:
            print(f"   ⚠️ Skipping {category} - watermark not found")
            continue
        
        print(f"   Watermark size: {watermark.size}")
        
        # Input folder
        input_folder = BASE_DIR / f"{category.upper()}_pictures"
        output_folder = OUTPUT_DIR / f"{category.upper()}_watermarked"
        
        if not input_folder.exists():
            print(f"   ⚠️ Input folder not found: {input_folder}")
            continue
        
        # Process each image
        images = list(input_folder.glob("*.jpg")) + list(input_folder.glob("*.png"))
        
        for img_path in images:
            total_processed += 1
            output_path = output_folder / f"{img_path.stem}_watermarked.jpg"
            
            print(f"\n   🖼️ {img_path.name}")
            
            if apply_watermark(img_path, watermark, output_path):
                total_success += 1
                print(f"      ✅ → {output_path.name}")
            else:
                print(f"      ❌ Failed")
    
    # Summary
    print(f"\n{'='*60}")
    print(f"📊 SUMMARY")
    print(f"{'='*60}")
    print(f"   Total images processed: {total_processed}")
    print(f"   Successfully watermarked: {total_success}")
    print(f"   Failed: {total_processed - total_success}")
    
    print(f"\n📁 Output folder: {OUTPUT_DIR}")
    for cat in CATEGORY_WATERMARK.keys():
        folder = OUTPUT_DIR / f"{cat.upper()}_watermarked"
        count = len(list(folder.glob("*.jpg")))
        print(f"   ├── {cat.upper()}_watermarked/ ({count} images)")

if __name__ == "__main__":
    main()
