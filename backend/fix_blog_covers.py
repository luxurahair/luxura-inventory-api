#!/usr/bin/env python3
"""
Script pour corriger les images de couverture des blogs Wix existants.
Remplace les images inappropriées par des images de cheveux longs luxueux.
"""

import os
import asyncio
import httpx
import random
import uuid
from dotenv import load_dotenv

load_dotenv()

# Clés API Wix
WIX_API_KEY = os.getenv("WIX_API_KEY")
WIX_SITE_ID = os.getenv("WIX_SITE_ID")

# Images de cheveux longs luxueux pour les couvertures
COVER_IMAGES = [
    "https://images.unsplash.com/photo-1605980776566-0486c3ac7617?w=1200&h=630&fit=crop",  # Cheveux extra longs luxueux
    "https://images.unsplash.com/photo-1595959183082-7b570b7e1dfa?w=1200&h=630&fit=crop",  # Cheveux lisses parfaits
    "https://images.unsplash.com/photo-1502823403499-6ccfcf4fb453?w=1200&h=630&fit=crop",  # Ondulations glamour
    "https://images.unsplash.com/photo-1519735777090-ec97162dc266?w=1200&h=630&fit=crop",  # Blonde cheveux longs
    "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=1200&h=630&fit=crop",  # Cheveux soyeux volume
    "https://images.unsplash.com/photo-1596178060810-72660fc43bd1?w=1200&h=630&fit=crop",  # Cheveux naturels longs
    "https://images.unsplash.com/photo-1580618672591-eb180b1a973f?w=1200&h=630&fit=crop",  # Cheveux brillants longs
]

_used_images = set()

def get_random_cover_image():
    """Sélectionne une image de couverture sans répétition."""
    global _used_images
    available = [img for img in COVER_IMAGES if img not in _used_images]
    if not available:
        _used_images.clear()
        available = COVER_IMAGES
    selected = random.choice(available)
    _used_images.add(selected)
    return selected


async def get_all_wix_posts():
    """Récupère tous les posts publiés sur Wix Blog."""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://www.wixapis.com/blog/v3/posts/query",
                headers={
                    "Authorization": WIX_API_KEY,
                    "wix-site-id": WIX_SITE_ID,
                    "Content-Type": "application/json"
                },
                json={
                    "paging": {"limit": 100},
                    "sort": [{"fieldName": "firstPublishedDate", "order": "DESC"}]
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                posts = data.get("posts", [])
                print(f"✅ {len(posts)} blogs trouvés sur Wix")
                return posts
            else:
                print(f"❌ Erreur récupération blogs: {response.status_code} - {response.text}")
                return []
    except Exception as e:
        print(f"❌ Exception: {e}")
        return []


async def import_image_to_wix(image_url: str) -> dict:
    """Importe une image dans Wix Media et attend qu'elle soit prête."""
    try:
        file_name = f"cover-{uuid.uuid4().hex[:8]}.jpg"
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Étape 1: Importer l'image
            print(f"   📤 Import image: {image_url[:60]}...")
            response = await client.post(
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
            
            if response.status_code not in (200, 201):
                print(f"   ❌ Import échoué: {response.status_code}")
                return None
            
            data = response.json()
            file_id = data.get("file", {}).get("id") or data.get("id")
            
            if not file_id:
                print("   ❌ Pas de file ID retourné")
                return None
            
            # Étape 2: Attendre que le fichier soit READY
            print(f"   ⏳ Attente statut READY pour {file_id}...")
            for attempt in range(60):
                check_response = await client.get(
                    f"https://www.wixapis.com/site-media/v1/files/{file_id}",
                    headers={
                        "Authorization": WIX_API_KEY,
                        "wix-site-id": WIX_SITE_ID,
                    }
                )
                
                if check_response.status_code == 200:
                    file_data = check_response.json().get("file", {})
                    status = file_data.get("operationStatus")
                    
                    if status == "READY":
                        print(f"   ✅ Image prête!")
                        
                        # Extraire les dimensions
                        media = file_data.get("media", {})
                        image_wrapper = media.get("image", {}) if isinstance(media, dict) else {}
                        image_info = image_wrapper.get("image", {}) if isinstance(image_wrapper, dict) else {}
                        width = image_info.get("width") or 1200
                        height = image_info.get("height") or 630
                        display_name = file_data.get("displayName", file_name)
                        
                        wix_uri = f"wix:image://v1/{file_id}/{display_name}#originWidth={width}&originHeight={height}"
                        
                        return {
                            "file_id": file_id,
                            "wix_uri": wix_uri,
                            "width": width,
                            "height": height
                        }
                    
                    elif status == "FAILED":
                        print(f"   ❌ Import FAILED")
                        return None
                
                await asyncio.sleep(1)
            
            print(f"   ❌ Timeout - image jamais READY")
            return None
            
    except Exception as e:
        print(f"   ❌ Exception import: {e}")
        return None


async def get_draft_for_post(post_id: str) -> str:
    """Récupère ou crée un brouillon pour un post publié."""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Essayer de récupérer le brouillon existant pour ce post
            response = await client.post(
                "https://www.wixapis.com/blog/v3/draft-posts/query",
                headers={
                    "Authorization": WIX_API_KEY,
                    "wix-site-id": WIX_SITE_ID,
                    "Content-Type": "application/json"
                },
                json={
                    "filter": {"originPostId": {"$eq": post_id}},
                    "paging": {"limit": 1}
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                drafts = data.get("draftPosts", [])
                if drafts:
                    return drafts[0].get("id")
            
            # Pas de brouillon existant - on ne peut pas créer de brouillon à partir d'un post publié via API
            return None
            
    except Exception as e:
        print(f"   ❌ Exception get_draft: {e}")
        return None


async def update_post_cover_image(post_id: str, image_data: dict, post_title: str = "") -> bool:
    """
    Met à jour l'image de couverture d'un post publié.
    
    IMPORTANT: L'API Wix Blog v3 ne permet pas de modifier directement un post publié.
    Il faut utiliser le endpoint draft-posts avec l'ID du brouillon correspondant,
    ou accepter que cette modification nécessite une intervention manuelle.
    """
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            wix_uri = image_data["wix_uri"]
            
            # Essayer d'abord avec draft-posts (si le post a un brouillon associé)
            draft_id = await get_draft_for_post(post_id)
            
            if draft_id:
                print(f"   🔄 PATCH draft {draft_id[:12]}... avec image de couverture...")
                
                payload = {
                    "draftPost": {
                        "media": {
                            "wixMedia": {
                                "image": {
                                    "id": wix_uri,
                                    "width": image_data["width"],
                                    "height": image_data["height"]
                                }
                            }
                        }
                    }
                }
                
                response = await client.patch(
                    f"https://www.wixapis.com/blog/v3/draft-posts/{draft_id}",
                    headers={
                        "Authorization": WIX_API_KEY,
                        "wix-site-id": WIX_SITE_ID,
                        "Content-Type": "application/json"
                    },
                    json=payload
                )
                
                if response.status_code in (200, 204):
                    print(f"   ✅ Brouillon mis à jour!")
                    
                    # Republier le brouillon
                    pub_response = await client.post(
                        f"https://www.wixapis.com/blog/v3/draft-posts/{draft_id}/publish",
                        headers={
                            "Authorization": WIX_API_KEY,
                            "wix-site-id": WIX_SITE_ID,
                            "Content-Type": "application/json"
                        }
                    )
                    
                    if pub_response.status_code in (200, 201):
                        print(f"   ✅ Post republié avec nouvelle image!")
                        return True
                    else:
                        print(f"   ⚠️ Brouillon OK mais republication échouée: {pub_response.status_code}")
                        return False
                else:
                    print(f"   ❌ PATCH brouillon échoué: {response.status_code}")
                    return False
            else:
                # Pas de brouillon - marquer comme nécessitant modification manuelle
                print(f"   ⚠️ Pas de brouillon trouvé - modification manuelle requise")
                print(f"   📝 Image Wix Media prête: {wix_uri[:60]}...")
                return False
                
    except Exception as e:
        print(f"   ❌ Exception PATCH: {e}")
        return False


async def fix_all_blog_covers():
    """Corrige les images de couverture de tous les blogs."""
    print("=" * 60)
    print("🔧 CORRECTION DES IMAGES DE COUVERTURE LUXURA")
    print("=" * 60)
    print()
    
    # Récupérer tous les posts
    posts = await get_all_wix_posts()
    
    if not posts:
        print("❌ Aucun blog à corriger")
        return
    
    print()
    print("=" * 60)
    print("📝 LISTE DES BLOGS À CORRIGER")
    print("=" * 60)
    
    for i, post in enumerate(posts, 1):
        title = post.get("title", "Sans titre")[:50]
        post_id = post.get("id", "N/A")
        has_cover = bool(post.get("media", {}).get("wixMedia", {}).get("image"))
        cover_status = "✅" if has_cover else "❌"
        print(f"{i}. {cover_status} [{post_id[:12]}...] {title}")
    
    print()
    print("=" * 60)
    print("🚀 DÉBUT DE LA CORRECTION")
    print("=" * 60)
    
    success_count = 0
    fail_count = 0
    
    for i, post in enumerate(posts, 1):
        title = post.get("title", "Sans titre")[:40]
        post_id = post.get("id")
        
        print()
        print(f"--- [{i}/{len(posts)}] {title} ---")
        
        # Sélectionner une nouvelle image de cheveux longs
        new_image_url = get_random_cover_image()
        print(f"   📷 Nouvelle image: {new_image_url[:50]}...")
        
        # Importer l'image dans Wix Media
        image_data = await import_image_to_wix(new_image_url)
        
        if not image_data:
            print(f"   ❌ Échec import image")
            fail_count += 1
            continue
        
        # Mettre à jour la couverture du post
        success = await update_post_cover_image(post_id, image_data)
        
        if success:
            success_count += 1
        else:
            fail_count += 1
        
        # Pause pour éviter le rate limiting
        await asyncio.sleep(2)
    
    print()
    print("=" * 60)
    print("📊 RÉSUMÉ")
    print("=" * 60)
    print(f"✅ Succès: {success_count}")
    print(f"❌ Échecs: {fail_count}")
    print(f"📝 Total: {len(posts)}")


if __name__ == "__main__":
    asyncio.run(fix_all_blog_covers())
