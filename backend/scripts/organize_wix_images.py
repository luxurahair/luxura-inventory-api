#!/usr/bin/env python3
"""
Script pour organiser les images Wix par catégorie dans Google Drive
et créer un mapping précis SKU -> Image pour chaque catégorie
"""

import os
import json
import httpx
import asyncio
from pathlib import Path
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload
from io import BytesIO
from dotenv import load_dotenv

load_dotenv()

# Google Drive configuration
GOOGLE_SERVICE_ACCOUNT_JSON = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
GOOGLE_DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID", "0AP66guFE3lalUk9PVA")

# Categories to organize
CATEGORIES = ['halo', 'genius', 'tape', 'i-tip', 'ponytail', 'clip-in']

# Wix image URL format
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

def get_drive_service():
    """Initialize Google Drive service"""
    if not GOOGLE_SERVICE_ACCOUNT_JSON:
        print("❌ GOOGLE_SERVICE_ACCOUNT_JSON not set")
        return None
    
    try:
        creds_dict = json.loads(GOOGLE_SERVICE_ACCOUNT_JSON)
        creds = service_account.Credentials.from_service_account_info(
            creds_dict,
            scopes=['https://www.googleapis.com/auth/drive']
        )
        return build('drive', 'v3', credentials=creds)
    except Exception as e:
        print(f"❌ Error initializing Drive service: {e}")
        return None

def create_folder(service, name, parent_id=None):
    """Create a folder in Google Drive"""
    file_metadata = {
        'name': name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    if parent_id:
        file_metadata['parents'] = [parent_id]
    
    # Check if folder already exists
    query = f"name='{name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    if parent_id:
        query += f" and '{parent_id}' in parents"
    
    results = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    files = results.get('files', [])
    
    if files:
        print(f"  📁 Folder '{name}' already exists")
        return files[0]['id']
    
    folder = service.files().create(body=file_metadata, fields='id').execute()
    print(f"  📁 Created folder '{name}'")
    return folder.get('id')

async def download_image(url):
    """Download image from URL"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            if response.status_code == 200:
                return response.content
    except Exception as e:
        print(f"  ❌ Error downloading {url}: {e}")
    return None

def upload_to_drive(service, folder_id, filename, image_data, mime_type='image/jpeg'):
    """Upload image to Google Drive"""
    # Check if file already exists
    query = f"name='{filename}' and '{folder_id}' in parents and trashed=false"
    results = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    files = results.get('files', [])
    
    if files:
        print(f"    ⏭️ {filename} already exists")
        return files[0]['id']
    
    file_metadata = {
        'name': filename,
        'parents': [folder_id]
    }
    
    media = MediaIoBaseUpload(BytesIO(image_data), mimetype=mime_type, resumable=True)
    file = service.files().create(body=file_metadata, media_body=media, fields='id,webViewLink').execute()
    print(f"    ✅ Uploaded {filename}")
    return file.get('id')

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

async def main():
    print("🚀 Starting Wix Image Organization for Google Drive")
    print("=" * 60)
    
    # Initialize Google Drive
    service = get_drive_service()
    if not service:
        return
    
    # Create main folder for Luxura images (at root level)
    print("\n📁 Creating folder structure...")
    main_folder_id = create_folder(service, "Luxura_Product_Images", None)  # None = root
    
    # Create subfolders for each category
    category_folders = {}
    for cat in CATEGORIES:
        folder_name = f"{cat.upper()}_pictures"
        category_folders[cat] = create_folder(service, folder_name, main_folder_id)
    
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
    
    # Download and upload images for each category
    image_mapping = {}  # {category: {color_code: {drive_id, url, filename}}}
    
    for cat in CATEGORIES:
        cat_products = products_by_category.get(cat, [])
        print(f"\n{'='*60}")
        print(f"📷 Processing {cat.upper()} ({len(cat_products)} products)")
        print(f"{'='*60}")
        
        folder_id = category_folders[cat]
        image_mapping[cat] = {}
        
        # Track unique colors to avoid duplicates
        processed_colors = set()
        
        for p in cat_products:
            name = p.get('name', '')
            color_code = extract_color_code(name) or p.get('color_code', 'unknown')
            images = p.get('images', [])
            
            if not images or color_code in processed_colors:
                continue
            
            processed_colors.add(color_code)
            
            # Get the image URL
            image_url = format_wix_url(images[0])
            if not image_url:
                continue
            
            # Create filename: CATEGORY_COLOR_luxura.jpg
            safe_color = color_code.replace('/', '-')
            filename = f"{cat.upper()}_{safe_color}_luxura.jpg"
            
            print(f"\n  🖼️ {name}")
            print(f"     Color: {color_code}")
            print(f"     File: {filename}")
            
            # Download image
            image_data = await download_image(image_url)
            if image_data:
                # Upload to Google Drive
                file_id = upload_to_drive(service, folder_id, filename, image_data)
                
                image_mapping[cat][color_code] = {
                    'drive_id': file_id,
                    'filename': filename,
                    'wix_url': images[0],
                    'name': name
                }
    
    # Save mapping to file
    mapping_file = Path(__file__).parent.parent / "image_mapping.json"
    with open(mapping_file, 'w', encoding='utf-8') as f:
        json.dump(image_mapping, f, indent=2, ensure_ascii=False)
    print(f"\n✅ Image mapping saved to {mapping_file}")
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    for cat in CATEGORIES:
        count = len(image_mapping.get(cat, {}))
        print(f"  {cat.upper()}: {count} images")
    
    print("\n✅ Done! Images organized in Google Drive.")
    print(f"📁 Main folder: Luxura_Product_Images")
    print(f"   Subfolders: {', '.join([f'{c.upper()}_pictures' for c in CATEGORIES])}")

if __name__ == "__main__":
    asyncio.run(main())
