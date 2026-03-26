#!/usr/bin/env python3
"""
Script pour générer un rapport des images de couverture à mettre à jour manuellement sur Wix.
Les images sont importées dans Wix Media Manager pour un copier-coller facile.
"""

import os
import asyncio
import httpx
import random
import uuid
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

WIX_API_KEY = os.getenv("WIX_API_KEY")
WIX_SITE_ID = os.getenv("WIX_SITE_ID")

# Images de cheveux longs luxueux
COVER_IMAGES = [
    "https://images.unsplash.com/photo-1605980776566-0486c3ac7617?w=1200&h=630&fit=crop",
    "https://images.unsplash.com/photo-1595959183082-7b570b7e1dfa?w=1200&h=630&fit=crop",
    "https://images.unsplash.com/photo-1502823403499-6ccfcf4fb453?w=1200&h=630&fit=crop",
    "https://images.unsplash.com/photo-1519735777090-ec97162dc266?w=1200&h=630&fit=crop",
    "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=1200&h=630&fit=crop",
    "https://images.unsplash.com/photo-1596178060810-72660fc43bd1?w=1200&h=630&fit=crop",
    "https://images.unsplash.com/photo-1580618672591-eb180b1a973f?w=1200&h=630&fit=crop",
]

_used = set()

def get_image():
    global _used
    avail = [i for i in COVER_IMAGES if i not in _used]
    if not avail:
        _used.clear()
        avail = COVER_IMAGES
    sel = random.choice(avail)
    _used.add(sel)
    return sel


async def get_all_posts():
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            "https://www.wixapis.com/blog/v3/posts/query",
            headers={
                "Authorization": WIX_API_KEY,
                "wix-site-id": WIX_SITE_ID,
                "Content-Type": "application/json"
            },
            json={"paging": {"limit": 100}}
        )
        if response.status_code == 200:
            return response.json().get("posts", [])
        return []


async def import_to_wix_media(image_url: str) -> str:
    """Importe l'image et retourne l'URL Wix statique."""
    try:
        file_name = f"cover-luxura-{uuid.uuid4().hex[:6]}.jpg"
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                "https://www.wixapis.com/site-media/v1/files/import",
                headers={
                    "Authorization": WIX_API_KEY,
                    "wix-site-id": WIX_SITE_ID,
                    "Content-Type": "application/json"
                },
                json={
                    "url": image_url,
                    "displayName": file_name,
                    "mediaType": "IMAGE",
                    "mimeType": "image/jpeg",
                    "filePath": f"/blog-covers/{file_name}"
                }
            )
            
            if resp.status_code in (200, 201):
                data = resp.json()
                file_id = data.get("file", {}).get("id") or data.get("id")
                
                # Attendre READY
                for _ in range(30):
                    check = await client.get(
                        f"https://www.wixapis.com/site-media/v1/files/{file_id}",
                        headers={
                            "Authorization": WIX_API_KEY,
                            "wix-site-id": WIX_SITE_ID,
                        }
                    )
                    if check.status_code == 200:
                        fd = check.json().get("file", {})
                        if fd.get("operationStatus") == "READY":
                            return f"https://static.wixstatic.com/media/{file_id}"
                    await asyncio.sleep(1)
    except Exception as e:
        print(f"Error: {e}")
    return None


async def generate_report():
    print("=" * 70)
    print("📋 RAPPORT - IMAGES DE COUVERTURE À METTRE À JOUR SUR WIX")
    print("=" * 70)
    print()
    
    posts = await get_all_posts()
    print(f"📝 {len(posts)} blogs trouvés")
    print()
    
    report = []
    
    for i, post in enumerate(posts[:10], 1):  # Limiter à 10 pour le test
        title = post.get("title", "Sans titre")[:50]
        slug = post.get("slug", "")
        
        print(f"[{i}] {title}...")
        
        # Sélectionner et importer une nouvelle image
        new_img_url = get_image()
        wix_url = await import_to_wix_media(new_img_url)
        
        if wix_url:
            print(f"    ✅ Image prête: {wix_url[:60]}...")
            report.append({
                "title": title,
                "slug": slug,
                "wix_url": wix_url,
                "original_url": new_img_url
            })
        else:
            print(f"    ❌ Échec import")
        
        await asyncio.sleep(1)
    
    # Générer le rapport HTML
    print()
    print("=" * 70)
    print("📄 INSTRUCTIONS POUR MISE À JOUR MANUELLE")
    print("=" * 70)
    print()
    print("Pour chaque blog ci-dessous:")
    print("1. Allez dans Dashboard Wix → Blog → Posts")
    print("2. Cliquez sur le post à modifier")
    print("3. Cliquez sur 'Settings' (icône engrenage)")
    print("4. Dans 'Featured Image', cliquez pour changer l'image")
    print("5. Sélectionnez l'image depuis Media Manager (déjà importée)")
    print("6. Sauvegardez et publiez")
    print()
    print("-" * 70)
    
    for item in report:
        print(f"\n📌 {item['title']}")
        print(f"   Slug: {item['slug']}")
        print(f"   Image Wix: {item['wix_url']}")
    
    print()
    print("=" * 70)
    print(f"✅ {len(report)} images importées dans votre Wix Media Manager")
    print("   Elles sont disponibles dans le dossier /blog-covers/")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(generate_report())
