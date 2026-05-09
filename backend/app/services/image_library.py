"""
🖼️ LUXURA IMAGE LIBRARY - Sauvegarde des images générées dans Wix
==================================================================
Ce service:
1. Upload les images Grok vers Wix Media Manager
2. Stocke les URLs permanentes dans Supabase (table: generated_images)
3. Permet de réutiliser les images pour différents contenus

Usage:
    from app.services.image_library import save_generated_image, get_images_by_product
    
    # Sauvegarder une image
    wix_url = await save_generated_image(
        grok_url="https://imgen.x.ai/...",
        product_id="chocolat-profond-dc",
        scene="chateau-frontenac",
        post_type="facebook"
    )
    
    # Récupérer les images d'un produit
    images = await get_images_by_product("chocolat-profond-dc")
"""

import os
import uuid
import asyncio
import httpx
from datetime import datetime
from typing import Optional, List, Dict
import logging

log = logging.getLogger(__name__)

# Configuration Wix
WIX_API_KEY = os.getenv("WIX_API_KEY", "").strip()
WIX_SITE_ID = os.getenv("WIX_SITE_ID", "").strip()

# Configuration Supabase
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()


async def upload_to_wix_media(
    image_url: str,
    product_id: str,
    scene: str,
    folder: str = "luxura-ai-images"
) -> Optional[str]:
    """
    Upload une image vers Wix Media Manager.
    
    Args:
        image_url: URL temporaire de l'image (Grok)
        product_id: ID du produit (ex: "chocolat-profond-dc")
        scene: Nom de la scène (ex: "chateau-frontenac")
        folder: Dossier Wix pour organiser
    
    Returns:
        URL permanente Wix (https://static.wixstatic.com/media/...)
    """
    if not WIX_API_KEY or not WIX_SITE_ID:
        log.warning("❌ WIX_API_KEY ou WIX_SITE_ID manquant")
        return None
    
    try:
        # Générer un nom de fichier unique et descriptif
        timestamp = datetime.now().strftime("%Y%m%d-%H%M")
        unique_id = uuid.uuid4().hex[:6]
        file_name = f"luxura-{product_id}-{scene}-{timestamp}-{unique_id}.jpg"
        
        log.info(f"📤 Upload vers Wix: {file_name}")
        
        async with httpx.AsyncClient(timeout=90.0) as client:
            # 1. Importer l'image depuis l'URL
            import_response = await client.post(
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
                    "filePath": f"/{folder}/{file_name}"
                }
            )
            
            if import_response.status_code not in (200, 201):
                log.error(f"❌ Erreur import Wix: {import_response.status_code}")
                log.error(import_response.text[:500])
                return None
            
            data = import_response.json()
            file_id = data.get("file", {}).get("id") or data.get("id")
            
            if not file_id:
                log.error("❌ Pas de file_id dans la réponse Wix")
                return None
            
            log.info(f"   📁 File ID: {file_id}")
            
            # 2. Attendre que l'image soit READY (max 60 sec)
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
                        wix_url = f"https://static.wixstatic.com/media/{file_id}"
                        log.info(f"✅ Image prête: {wix_url}")
                        return wix_url
                    
                    if status == "FAILED":
                        log.error("❌ Upload Wix échoué")
                        return None
                
                await asyncio.sleep(1)
            
            log.warning("⚠️ Timeout en attendant que l'image soit prête")
            # Retourner quand même l'URL, elle devrait fonctionner
            return f"https://static.wixstatic.com/media/{file_id}"
            
    except Exception as e:
        log.error(f"❌ Exception upload Wix: {e}")
        return None


async def save_to_database(
    grok_url: str,
    wix_url: str,
    product_id: str,
    product_name: str,
    color_name: str,
    scene: str,
    post_type: str
) -> bool:
    """
    Sauvegarde les métadonnées de l'image dans Supabase.
    
    Table: generated_images
    """
    if not DATABASE_URL:
        log.warning("❌ DATABASE_URL manquant")
        return False
    
    try:
        import asyncpg
        
        conn = await asyncpg.connect(DATABASE_URL)
        
        # Créer la table si elle n'existe pas
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS generated_images (
                id SERIAL PRIMARY KEY,
                grok_url TEXT NOT NULL,
                wix_url TEXT NOT NULL,
                product_id VARCHAR(100) NOT NULL,
                product_name VARCHAR(255),
                color_name VARCHAR(100),
                scene VARCHAR(100),
                post_type VARCHAR(50),
                created_at TIMESTAMP DEFAULT NOW(),
                used_count INTEGER DEFAULT 0,
                last_used_at TIMESTAMP
            )
        """)
        
        # Créer les index
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_generated_images_product 
            ON generated_images(product_id)
        """)
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_generated_images_scene 
            ON generated_images(scene)
        """)
        
        # Insérer l'image
        await conn.execute("""
            INSERT INTO generated_images 
            (grok_url, wix_url, product_id, product_name, color_name, scene, post_type)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
        """, grok_url, wix_url, product_id, product_name, color_name, scene, post_type)
        
        await conn.close()
        log.info(f"✅ Image sauvegardée dans DB: {product_id} / {scene}")
        return True
        
    except Exception as e:
        log.error(f"❌ Erreur DB: {e}")
        return False


async def save_generated_image(
    grok_url: str,
    product_id: str,
    product_name: str,
    color_name: str,
    scene: str,
    post_type: str = "facebook"
) -> Optional[str]:
    """
    Fonction principale: Upload vers Wix + sauvegarde en DB.
    
    Returns:
        URL permanente Wix ou None si échec
    """
    log.info(f"🖼️ Sauvegarde image: {product_name} @ {scene}")
    
    # 1. Upload vers Wix
    wix_url = await upload_to_wix_media(
        image_url=grok_url,
        product_id=product_id,
        scene=scene.replace(" ", "-").lower()
    )
    
    if not wix_url:
        log.error("❌ Échec upload Wix")
        return None
    
    # 2. Sauvegarder en DB
    await save_to_database(
        grok_url=grok_url,
        wix_url=wix_url,
        product_id=product_id,
        product_name=product_name,
        color_name=color_name,
        scene=scene,
        post_type=post_type
    )
    
    return wix_url


async def get_images_by_product(product_id: str, limit: int = 20) -> List[Dict]:
    """
    Récupère toutes les images générées pour un produit.
    """
    if not DATABASE_URL:
        return []
    
    try:
        import asyncpg
        conn = await asyncpg.connect(DATABASE_URL)
        
        rows = await conn.fetch("""
            SELECT * FROM generated_images 
            WHERE product_id = $1 
            ORDER BY created_at DESC 
            LIMIT $2
        """, product_id, limit)
        
        await conn.close()
        return [dict(row) for row in rows]
        
    except Exception as e:
        log.error(f"Erreur récupération images: {e}")
        return []


async def get_images_by_scene(scene: str, limit: int = 20) -> List[Dict]:
    """
    Récupère toutes les images d'une scène spécifique.
    """
    if not DATABASE_URL:
        return []
    
    try:
        import asyncpg
        conn = await asyncpg.connect(DATABASE_URL)
        
        rows = await conn.fetch("""
            SELECT * FROM generated_images 
            WHERE scene ILIKE $1 
            ORDER BY created_at DESC 
            LIMIT $2
        """, f"%{scene}%", limit)
        
        await conn.close()
        return [dict(row) for row in rows]
        
    except Exception as e:
        log.error(f"Erreur récupération images: {e}")
        return []


async def get_all_images(limit: int = 100) -> List[Dict]:
    """
    Récupère toutes les images générées.
    """
    if not DATABASE_URL:
        return []
    
    try:
        import asyncpg
        conn = await asyncpg.connect(DATABASE_URL)
        
        rows = await conn.fetch("""
            SELECT * FROM generated_images 
            ORDER BY created_at DESC 
            LIMIT $1
        """, limit)
        
        await conn.close()
        return [dict(row) for row in rows]
        
    except Exception as e:
        log.error(f"Erreur récupération images: {e}")
        return []


async def mark_image_used(image_id: int) -> bool:
    """
    Marque une image comme utilisée (incrémente le compteur).
    """
    if not DATABASE_URL:
        return False
    
    try:
        import asyncpg
        conn = await asyncpg.connect(DATABASE_URL)
        
        await conn.execute("""
            UPDATE generated_images 
            SET used_count = used_count + 1, last_used_at = NOW()
            WHERE id = $1
        """, image_id)
        
        await conn.close()
        return True
        
    except Exception as e:
        log.error(f"Erreur mise à jour: {e}")
        return False


# ============================================
# 🧪 TEST
# ============================================

if __name__ == "__main__":
    import asyncio
    
    async def test():
        print("=" * 60)
        print("🖼️ TEST IMAGE LIBRARY")
        print("=" * 60)
        
        # Test avec une image Grok existante
        test_url = "https://imgen.x.ai/xai-imgen/xai-tmp-imgen-2c8190a5-e9de-427c-9e61-5e306e6fd206.jpeg"
        
        wix_url = await save_generated_image(
            grok_url=test_url,
            product_id="chocolat-profond-dc",
            product_name="Genius Vivian Chocolat Profond #DC",
            color_name="Chocolat Profond",
            scene="Château Frontenac",
            post_type="facebook"
        )
        
        if wix_url:
            print(f"\n✅ Image sauvegardée!")
            print(f"   🔗 Wix URL: {wix_url}")
        else:
            print("\n❌ Échec sauvegarde")
    
    asyncio.run(test())
