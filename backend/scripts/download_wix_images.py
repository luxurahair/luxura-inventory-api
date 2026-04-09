#!/usr/bin/env python3
"""
Script pour créer un mapping précis des images Wix par catégorie et code couleur.
Sauvegarde les images localement pour upload manuel vers Google Drive.
"""

import os
import json
import httpx
import asyncio
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Categories principales
CATEGORIES = ['halo', 'genius', 'tape', 'i-tip', 'ponytail', 'clip-in']

# Output directories
OUTPUT_DIR = Path("/app/backend/luxura_images")

def format_wix_url(url, size=800):
    """Format Wix image URL with proper size"""
    if not url:
        return None
    if '/v1/fill/' in url:
        parts = url.split('/v1/fill/')
        base = parts[0]
        filename = parts[1].split('/')[-1] if '/' in parts[1] else parts[1]
        return f"{base}/v1/fill/w_{size},h_{size},al_c,q_90/{filename}"
    return url

async def download_image(url, output_path):
    """Download image from URL"""
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(url)
            if response.status_code == 200:
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                return True
    except Exception as e:
        print(f"  ❌ Error downloading: {e}")
    return False

async def get_products_from_api():
    """Get all products from local API"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get("http://localhost:8001/api/products?limit=200")
        if response.status_code == 200:
            return response.json()
    return []

def extract_color_code(name):
    """Extract color code from product name"""
    import re
    match = re.search(r'#([A-Za-z0-9/]+)', name)
    return match.group(1).upper() if match else None

def extract_color_name(name):
    """Extract color name from product name"""
    import re
    # Pattern: "Série Everly COLOR_NAME #CODE"
    match = re.search(r'(?:Everly|Vivian|Aurora|Eleanor|Victoria|Sophia)\s+([^#]+?)\s*#', name)
    if match:
        return match.group(1).strip()
    return None

async def main():
    print("🚀 Creating Luxura Image Mapping & Downloading Images")
    print("=" * 60)
    
    # Create output directories
    OUTPUT_DIR.mkdir(exist_ok=True)
    for cat in CATEGORIES:
        (OUTPUT_DIR / f"{cat.upper()}_pictures").mkdir(exist_ok=True)
    
    # Get products from API
    print("\n📦 Fetching products from API...")
    products = await get_products_from_api()
    print(f"  Found {len(products)} products")
    
    # Organize by category
    products_by_category = {}
    for p in products:
        cat = p.get('category', 'other')
        if cat in CATEGORIES:
            if cat not in products_by_category:
                products_by_category[cat] = []
            products_by_category[cat].append(p)
    
    # Create mapping and download images
    image_mapping = {}  # {category: {color_code: {filename, wix_url, color_name, name}}}
    
    for cat in CATEGORIES:
        cat_products = products_by_category.get(cat, [])
        print(f"\n{'='*60}")
        print(f"📷 Processing {cat.upper()} ({len(cat_products)} products)")
        print(f"{'='*60}")
        
        cat_dir = OUTPUT_DIR / f"{cat.upper()}_pictures"
        image_mapping[cat] = {}
        
        # Track unique colors to avoid duplicates
        processed_colors = set()
        
        for p in cat_products:
            name = p.get('name', '')
            color_code = extract_color_code(name) or p.get('color_code', 'unknown')
            color_name = extract_color_name(name) or 'Unknown'
            images = p.get('images', [])
            
            if not images or color_code.upper() in processed_colors:
                continue
            
            processed_colors.add(color_code.upper())
            
            # Get the image URL - high quality
            image_url = format_wix_url(images[0], size=1200)
            if not image_url:
                continue
            
            # Create filename: CATEGORY_COLORCODE_colorname.jpg
            safe_color = color_code.replace('/', '-').replace(' ', '_')
            safe_name = color_name.replace(' ', '_').replace("'", "")[:30]
            filename = f"{cat.upper()}_{safe_color}_{safe_name}.jpg"
            output_path = cat_dir / filename
            
            print(f"\n  🖼️ {name}")
            print(f"     Color Code: #{color_code}")
            print(f"     Color Name: {color_name}")
            print(f"     File: {filename}")
            
            # Download image
            success = await download_image(image_url, output_path)
            
            if success:
                print(f"     ✅ Downloaded")
                image_mapping[cat][color_code] = {
                    'filename': filename,
                    'local_path': str(output_path),
                    'wix_url': images[0],
                    'color_name': color_name,
                    'product_name': name,
                    'handle': p.get('id')
                }
            else:
                print(f"     ❌ Failed to download")
    
    # Save mapping to JSON
    mapping_file = OUTPUT_DIR / "image_mapping.json"
    with open(mapping_file, 'w', encoding='utf-8') as f:
        json.dump(image_mapping, f, indent=2, ensure_ascii=False)
    print(f"\n✅ Image mapping saved to {mapping_file}")
    
    # Create a summary CSV for easy viewing
    csv_file = OUTPUT_DIR / "image_summary.csv"
    with open(csv_file, 'w', encoding='utf-8') as f:
        f.write("Category,Color_Code,Color_Name,Filename,Product_Name\n")
        for cat, colors in image_mapping.items():
            for code, info in colors.items():
                f.write(f"{cat},{code},{info['color_name']},{info['filename']},{info['product_name']}\n")
    print(f"✅ Summary CSV saved to {csv_file}")
    
    # Print final summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    total = 0
    for cat in CATEGORIES:
        count = len(image_mapping.get(cat, {}))
        total += count
        folder = f"{cat.upper()}_pictures"
        print(f"  {cat.upper()}: {count} images → {OUTPUT_DIR / folder}")
    print(f"\n  TOTAL: {total} images downloaded")
    
    print("\n📁 Folder Structure:")
    print(f"   {OUTPUT_DIR}/")
    for cat in CATEGORIES:
        folder = f"{cat.upper()}_pictures"
        count = len(image_mapping.get(cat, {}))
        print(f"   ├── {folder}/ ({count} images)")
    print(f"   ├── image_mapping.json")
    print(f"   └── image_summary.csv")

if __name__ == "__main__":
    asyncio.run(main())
