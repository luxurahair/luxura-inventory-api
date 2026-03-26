#!/usr/bin/env python3
"""
Script pour ajouter des images de couverture aux blogs existants.
Génère des images DALL-E uniques et les upload vers Wix.
"""

import asyncio
import httpx
import os
import uuid
from dotenv import load_dotenv

load_dotenv('/app/backend/.env')

# Import du module de génération d'images
import sys
sys.path.insert(0, '/app/backend')
from image_generation import generate_blog_image_with_dalle, upload_image_bytes_to_wix

WIX_API_KEY = os.getenv('WIX_API_KEY')
WIX_SITE_ID = os.getenv('WIX_SITE_ID')


def detect_category(title: str) -> str:
    """Détecte la catégorie du blog basé sur le titre."""
    title_lower = title.lower()
    if 'halo' in title_lower:
        return 'halo'
    elif 'genius' in title_lower or 'weft' in title_lower:
        return 'genius'
    elif 'tape' in title_lower or 'adhésive' in title_lower or 'bande' in title_lower:
        return 'tape'
    elif 'i-tip' in title_lower or 'kératine' in title_lower or 'itip' in title_lower:
        return 'itip'
    elif 'entretien' in title_lower or 'soins' in title_lower:
        return 'entretien'
    elif 'formation' in title_lower:
        return 'formation'
    elif 'tendance' in title_lower:
        return 'tendances'
    else:
        return 'general'


async def get_posts_without_cover():
    """Récupère les posts sans image de couverture."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            'https://www.wixapis.com/blog/v3/posts/query',
            headers={
                'Authorization': WIX_API_KEY,
                'wix-site-id': WIX_SITE_ID,
                'Content-Type': 'application/json'
            },
            json={'paging': {'limit': 100}}
        )
        
        if response.status_code != 200:
            print(f"Erreur API: {response.status_code}")
            return []
        
        posts = response.json().get('posts', [])
        
        no_cover = []
        for p in posts:
            media = p.get('media', {})
            wix_media = media.get('wixMedia', {})
            has_image = bool(wix_media.get('image'))
            
            if not has_image:
                no_cover.append({
                    'id': p.get('id'),
                    'title': p.get('title', ''),
                    'category': detect_category(p.get('title', ''))
                })
        
        return no_cover


async def add_cover_to_post(post_id: str, title: str, category: str):
    """Génère une image DALL-E et l'ajoute au post."""
    print(f"\n📸 Génération image pour: {title[:50]}...")
    print(f"   Catégorie détectée: {category}")
    
    # Générer l'image avec DALL-E
    image_bytes = await generate_blog_image_with_dalle(category, "cover")
    
    if not image_bytes:
        print(f"   ❌ Échec génération DALL-E")
        return False
    
    # Upload vers Wix
    image_data = await upload_image_bytes_to_wix(
        api_key=WIX_API_KEY,
        site_id=WIX_SITE_ID,
        image_bytes=image_bytes,
        file_name=f"cover-fix-{uuid.uuid4().hex[:8]}.png"
    )
    
    if not image_data:
        print(f"   ❌ Échec upload Wix")
        return False
    
    file_id = image_data.get('file_id')
    print(f"   ✅ Image uploadée: {file_id[:30]}...")
    
    # Mettre à jour le post via l'API (tentative)
    # Note: L'API Wix ne permet pas toujours de modifier les posts publiés
    # On essaie quand même
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Essayer de patcher directement
        patch_data = {
            "post": {
                "media": {
                    "wixMedia": {
                        "image": {
                            "id": file_id,
                            "width": image_data.get('width', 1200),
                            "height": image_data.get('height', 630)
                        }
                    },
                    "displayed": True,
                    "custom": True
                }
            }
        }
        
        response = await client.patch(
            f'https://www.wixapis.com/blog/v3/posts/{post_id}',
            headers={
                'Authorization': WIX_API_KEY,
                'wix-site-id': WIX_SITE_ID,
                'Content-Type': 'application/json'
            },
            json=patch_data
        )
        
        if response.status_code in (200, 204):
            print(f"   ✅ Post mis à jour avec succès!")
            return True
        else:
            print(f"   ⚠️ PATCH échoué ({response.status_code}) - Image disponible dans Media Manager")
            print(f"   📋 File ID: {file_id}")
            print(f"   🔗 URL: {image_data.get('static_url')}")
            return False


async def main():
    print("=" * 60)
    print("🖼️  AJOUT D'IMAGES AUX BLOGS SANS COVER")
    print("=" * 60)
    
    # Récupérer les posts sans cover
    posts = await get_posts_without_cover()
    print(f"\n📝 {len(posts)} posts sans image de couverture")
    
    if not posts:
        print("✅ Tous les posts ont déjà une image!")
        return
    
    # Traiter chaque post (limiter à 10 pour éviter timeout)
    success = 0
    failed = 0
    
    for i, post in enumerate(posts[:10], 1):
        print(f"\n--- [{i}/{min(len(posts), 10)}] ---")
        result = await add_cover_to_post(
            post['id'],
            post['title'],
            post['category']
        )
        
        if result:
            success += 1
        else:
            failed += 1
        
        # Pause pour éviter rate limiting
        await asyncio.sleep(2)
    
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ")
    print("=" * 60)
    print(f"✅ Succès: {success}")
    print(f"⚠️ Échecs (images dans Media Manager): {failed}")
    print(f"📝 Restants: {max(0, len(posts) - 10)}")


if __name__ == "__main__":
    asyncio.run(main())
