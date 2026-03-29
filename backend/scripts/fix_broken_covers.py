#!/usr/bin/env python3
"""
Script de migration pour réparer les covers cassées des anciens articles.
Utilise le format qui fonctionne: file_id simple + custom: True

Usage:
    python fix_broken_covers.py --dry-run    # Voir ce qui serait modifié
    python fix_broken_covers.py --fix        # Appliquer les corrections
"""

import os
import asyncio
import httpx
import argparse
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

WIX_API_KEY = os.getenv("WIX_API_KEY")
WIX_SITE_ID = os.getenv("WIX_SITE_ID")


async def get_recent_posts(limit: int = 20):
    """Récupère les posts récents"""
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            "https://www.wixapis.com/blog/v3/posts/query",
            headers={
                "Authorization": WIX_API_KEY,
                "wix-site-id": WIX_SITE_ID,
                "Content-Type": "application/json"
            },
            json={"paging": {"limit": limit}}
        )
        
        if response.status_code != 200:
            logger.error(f"Erreur: {response.status_code} - {response.text}")
            return []
        
        return response.json().get("posts", [])


def is_cover_broken(post: dict) -> bool:
    """Vérifie si la cover utilise l'ancien format cassé"""
    media = post.get("media", {})
    image = media.get("wixMedia", {}).get("image", {})
    image_id = image.get("id", "")
    custom = media.get("custom", False)
    
    # Ancien format cassé: wix:image://v1/... ou custom=False
    if image_id.startswith("wix:image://"):
        return True
    if image_id and not custom:
        return True
    
    return False


def extract_file_id_from_wix_uri(wix_uri: str) -> str:
    """Extrait le file_id simple d'une Wix URI"""
    # wix:image://v1/f1b961_xxx~mv2.png/filename.png#originWidth=...
    if wix_uri.startswith("wix:image://v1/"):
        parts = wix_uri.replace("wix:image://v1/", "").split("/")
        if parts:
            file_id = parts[0].split("#")[0]
            return file_id
    return wix_uri


async def fix_post_cover(post_id: str, current_image_id: str, dry_run: bool = True):
    """Corrige la cover d'un post avec le bon format"""
    
    # Extraire le file_id simple
    file_id = extract_file_id_from_wix_uri(current_image_id)
    
    if not file_id:
        logger.warning(f"  Impossible d'extraire file_id de: {current_image_id}")
        return False
    
    logger.info(f"  file_id extrait: {file_id}")
    
    if dry_run:
        logger.info(f"  [DRY-RUN] Aurait appliqué: file_id={file_id}, custom=True")
        return True
    
    # Créer un draft depuis le post publié pour le modifier
    # Note: On ne peut pas modifier directement un post publié,
    # il faut le convertir en draft, modifier, puis republier
    
    payload = {
        "draftPost": {
            "media": {
                "wixMedia": {
                    "image": {
                        "id": file_id
                    }
                },
                "displayed": True,
                "custom": True
            }
        }
    }
    
    async with httpx.AsyncClient(timeout=60) as client:
        # D'abord, créer un draft depuis le post
        revert_response = await client.post(
            f"https://www.wixapis.com/blog/v3/posts/{post_id}/revert-to-draft",
            headers={
                "Authorization": WIX_API_KEY,
                "wix-site-id": WIX_SITE_ID,
                "Content-Type": "application/json"
            }
        )
        
        if revert_response.status_code not in (200, 201):
            logger.error(f"  Erreur revert-to-draft: {revert_response.status_code}")
            return False
        
        draft_id = revert_response.json().get("draftPost", {}).get("id")
        logger.info(f"  Draft créé: {draft_id}")
        
        # PATCH le draft avec le bon format
        patch_response = await client.patch(
            f"https://www.wixapis.com/blog/v3/draft-posts/{draft_id}",
            headers={
                "Authorization": WIX_API_KEY,
                "wix-site-id": WIX_SITE_ID,
                "Content-Type": "application/json"
            },
            json=payload
        )
        
        if patch_response.status_code not in (200, 204):
            logger.error(f"  Erreur PATCH: {patch_response.status_code}")
            return False
        
        logger.info(f"  ✅ PATCH appliqué")
        
        # Republier le draft
        publish_response = await client.post(
            f"https://www.wixapis.com/blog/v3/draft-posts/{draft_id}/publish",
            headers={
                "Authorization": WIX_API_KEY,
                "wix-site-id": WIX_SITE_ID,
                "Content-Type": "application/json"
            }
        )
        
        if publish_response.status_code not in (200, 201):
            logger.error(f"  Erreur publish: {publish_response.status_code}")
            return False
        
        logger.info(f"  ✅ Republié avec succès")
        return True


async def main(dry_run: bool = True):
    logger.info("=" * 60)
    logger.info("MIGRATION DES COVERS CASSÉES")
    logger.info(f"Mode: {'DRY-RUN (simulation)' if dry_run else 'FIX (application réelle)'}")
    logger.info("=" * 60)
    
    posts = await get_recent_posts(20)
    logger.info(f"\n{len(posts)} posts récents trouvés\n")
    
    broken_posts = []
    
    for post in posts:
        title = post.get("title", "Sans titre")[:50]
        post_id = post.get("id")
        media = post.get("media", {})
        image = media.get("wixMedia", {}).get("image", {})
        image_id = image.get("id", "NONE")
        custom = media.get("custom", "N/A")
        
        is_broken = is_cover_broken(post)
        status = "❌ CASSÉ" if is_broken else "✅ OK"
        
        logger.info(f"{status} | {title}")
        logger.info(f"       id: {image_id[:60]}...")
        logger.info(f"       custom: {custom}")
        
        if is_broken:
            broken_posts.append({
                "id": post_id,
                "title": title,
                "image_id": image_id
            })
        
        logger.info("")
    
    logger.info("=" * 60)
    logger.info(f"RÉSUMÉ: {len(broken_posts)} posts cassés sur {len(posts)}")
    logger.info("=" * 60)
    
    if not broken_posts:
        logger.info("Rien à corriger!")
        return
    
    if dry_run:
        logger.info("\nPour appliquer les corrections, relancez avec --fix")
        return
    
    logger.info("\nApplication des corrections...")
    
    for post in broken_posts:
        logger.info(f"\nCorrection: {post['title']}")
        success = await fix_post_cover(
            post_id=post["id"],
            current_image_id=post["image_id"],
            dry_run=False
        )
        if not success:
            logger.error(f"  Échec de la correction")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fix broken blog covers")
    parser.add_argument("--dry-run", action="store_true", help="Simulation seulement")
    parser.add_argument("--fix", action="store_true", help="Appliquer les corrections")
    
    args = parser.parse_args()
    
    if not args.dry_run and not args.fix:
        print("Usage:")
        print("  python fix_broken_covers.py --dry-run    # Voir ce qui serait modifié")
        print("  python fix_broken_covers.py --fix        # Appliquer les corrections")
        exit(1)
    
    asyncio.run(main(dry_run=args.dry_run))
