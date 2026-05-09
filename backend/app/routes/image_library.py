"""
🖼️ LUXURA IMAGE LIBRARY API - Gestion des images générées
==========================================================
Routes pour consulter et réutiliser les images sauvegardées dans Wix.

Routes:
  GET  /api/images              - Liste toutes les images
  GET  /api/images/product/:id  - Images d'un produit spécifique
  GET  /api/images/scene/:name  - Images d'une scène spécifique
  GET  /api/images/stats        - Statistiques de la bibliothèque
"""

import os
import logging
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/images", tags=["Image Library"])

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()


class GeneratedImage(BaseModel):
    id: int
    grok_url: str
    wix_url: str
    product_id: str
    product_name: Optional[str]
    color_name: Optional[str]
    scene: Optional[str]
    post_type: Optional[str]
    created_at: datetime
    used_count: int


class ImageStats(BaseModel):
    total_images: int
    products_with_images: int
    scenes_used: int
    most_popular_product: Optional[str]
    most_popular_scene: Optional[str]


async def get_db_connection():
    """Obtient une connexion à la base de données."""
    if not DATABASE_URL:
        raise HTTPException(status_code=500, detail="DATABASE_URL non configuré")
    
    import asyncpg
    return await asyncpg.connect(DATABASE_URL)


@router.get("", response_model=List[dict])
async def list_all_images(
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0)
):
    """
    📋 Liste toutes les images générées.
    
    Retourne les images sauvegardées dans Wix avec leurs métadonnées.
    Triées par date de création (plus récentes en premier).
    """
    try:
        conn = await get_db_connection()
        
        rows = await conn.fetch("""
            SELECT id, grok_url, wix_url, product_id, product_name, 
                   color_name, scene, post_type, created_at, used_count
            FROM generated_images 
            ORDER BY created_at DESC 
            LIMIT $1 OFFSET $2
        """, limit, offset)
        
        await conn.close()
        
        return [dict(row) for row in rows]
        
    except Exception as e:
        log.error(f"Erreur liste images: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/product/{product_id}", response_model=List[dict])
async def get_images_by_product(
    product_id: str,
    limit: int = Query(default=20, le=100)
):
    """
    📦 Récupère toutes les images d'un produit spécifique.
    
    Exemple: /api/images/product/chocolat-profond-dc
    """
    try:
        conn = await get_db_connection()
        
        rows = await conn.fetch("""
            SELECT id, grok_url, wix_url, product_id, product_name, 
                   color_name, scene, post_type, created_at, used_count
            FROM generated_images 
            WHERE product_id = $1
            ORDER BY created_at DESC 
            LIMIT $2
        """, product_id, limit)
        
        await conn.close()
        
        if not rows:
            return []
        
        return [dict(row) for row in rows]
        
    except Exception as e:
        log.error(f"Erreur images produit: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scene/{scene_name}", response_model=List[dict])
async def get_images_by_scene(
    scene_name: str,
    limit: int = Query(default=20, le=100)
):
    """
    🎬 Récupère toutes les images d'une scène spécifique.
    
    Exemple: /api/images/scene/chateau-frontenac
    """
    try:
        conn = await get_db_connection()
        
        rows = await conn.fetch("""
            SELECT id, grok_url, wix_url, product_id, product_name, 
                   color_name, scene, post_type, created_at, used_count
            FROM generated_images 
            WHERE scene ILIKE $1
            ORDER BY created_at DESC 
            LIMIT $2
        """, f"%{scene_name}%", limit)
        
        await conn.close()
        
        return [dict(row) for row in rows]
        
    except Exception as e:
        log.error(f"Erreur images scène: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/color/{color_name}", response_model=List[dict])
async def get_images_by_color(
    color_name: str,
    limit: int = Query(default=20, le=100)
):
    """
    🎨 Récupère toutes les images d'une couleur spécifique.
    
    Exemple: /api/images/color/chocolat
    """
    try:
        conn = await get_db_connection()
        
        rows = await conn.fetch("""
            SELECT id, grok_url, wix_url, product_id, product_name, 
                   color_name, scene, post_type, created_at, used_count
            FROM generated_images 
            WHERE color_name ILIKE $1
            ORDER BY created_at DESC 
            LIMIT $2
        """, f"%{color_name}%", limit)
        
        await conn.close()
        
        return [dict(row) for row in rows]
        
    except Exception as e:
        log.error(f"Erreur images couleur: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=dict)
async def get_image_stats():
    """
    📊 Statistiques de la bibliothèque d'images.
    """
    try:
        conn = await get_db_connection()
        
        # Total images
        total = await conn.fetchval("SELECT COUNT(*) FROM generated_images")
        
        # Produits distincts
        products = await conn.fetchval(
            "SELECT COUNT(DISTINCT product_id) FROM generated_images"
        )
        
        # Scènes distinctes
        scenes = await conn.fetchval(
            "SELECT COUNT(DISTINCT scene) FROM generated_images"
        )
        
        # Produit le plus populaire
        top_product = await conn.fetchrow("""
            SELECT product_name, COUNT(*) as count 
            FROM generated_images 
            GROUP BY product_name 
            ORDER BY count DESC 
            LIMIT 1
        """)
        
        # Scène la plus populaire
        top_scene = await conn.fetchrow("""
            SELECT scene, COUNT(*) as count 
            FROM generated_images 
            GROUP BY scene 
            ORDER BY count DESC 
            LIMIT 1
        """)
        
        # Images par jour (7 derniers jours)
        daily = await conn.fetch("""
            SELECT DATE(created_at) as date, COUNT(*) as count
            FROM generated_images
            WHERE created_at > NOW() - INTERVAL '7 days'
            GROUP BY DATE(created_at)
            ORDER BY date DESC
        """)
        
        await conn.close()
        
        return {
            "total_images": total or 0,
            "products_with_images": products or 0,
            "scenes_used": scenes or 0,
            "most_popular_product": top_product["product_name"] if top_product else None,
            "most_popular_scene": top_scene["scene"] if top_scene else None,
            "images_per_day": [dict(row) for row in daily] if daily else []
        }
        
    except Exception as e:
        log.error(f"Erreur stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recent", response_model=List[dict])
async def get_recent_images(hours: int = Query(default=24, le=168)):
    """
    🕐 Récupère les images générées dans les dernières X heures.
    
    Exemple: /api/images/recent?hours=48
    """
    try:
        conn = await get_db_connection()
        
        rows = await conn.fetch(f"""
            SELECT id, grok_url, wix_url, product_id, product_name, 
                   color_name, scene, post_type, created_at, used_count
            FROM generated_images 
            WHERE created_at > NOW() - INTERVAL '{hours} hours'
            ORDER BY created_at DESC
        """)
        
        await conn.close()
        
        return [dict(row) for row in rows]
        
    except Exception as e:
        log.error(f"Erreur images récentes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


print("✅ Routes Image Library chargées")
