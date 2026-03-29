#!/usr/bin/env python3
"""
Script de migration V2 pour réparer les covers cassées des anciens articles Wix.
Format stable: file_id simple + custom: True

Usage:
    python fix_broken_covers.py --dry-run    # Voir ce qui serait modifié
    python fix_broken_covers.py --fix        # Appliquer les corrections
"""

import os
import asyncio
import httpx
import argparse
import logging
from typing import Optional, Dict, List
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
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


def extract_file_id_from_wix_uri(wix_uri: str) -> str:
    """Extrait le file_id simple d'une Wix URI"""
    if not wix_uri:
        return ""
    # wix:image://v1/f1b961_xxx~mv2.png/filename.png#originWidth=...
    if wix_uri.startswith("wix:image://v1/"):
        parts = wix_uri.replace("wix:image://v1/", "").split("/")
        if parts:
            file_id = parts[0].split("#")[0]
            return file_id
    return wix_uri


def is_cover_broken(post: dict) -> tuple:
    """Vérifie si la cover utilise l'ancien format cassé et retourne les infos"""
    media = post.get("media", {})
    image = media.get("wixMedia", {}).get("image", {})
    image_id = image.get("id", "")
    custom = media.get("custom", False)
    width = image.get("width", 1200)
    height = image.get("height", 630)
    
    # Ancien format cassé: wix:image://v1/... ou custom=False
    if image_id.startswith("wix:image://"):
        file_id = extract_file_id_from_wix_uri(image_id)
        return True, file_id, width, height
    if image_id and not custom:
        return True, image_id, width, height
    
    return False, image_id, width, height


async def revert_post_to_draft(api_key: str, site_id: str, post_id: str) -> Optional[str]:
    """Convertit un post publié en draft pour pouvoir le modifier"""
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            f"https://www.wixapis.com/blog/v3/posts/{post_id}/revert-to-draft",
            headers={
                "Authorization": api_key,
                "wix-site-id": site_id,
                "Content-Type": "application/json"
            }
        )
        
        if response.status_code not in (200, 201):
            logger.error(f"Erreur revert-to-draft: {response.status_code} - {response.text}")
            return None
        
        return response.json().get("draftPost", {}).get("id")


async def patch_cover_v2(
    api_key: str,
    site_id: str,
    draft_id: str,
    file_id: str,
    width: int = 1200,
    height: int = 630,
) -> bool:
    """
    Nouveau format stable Wix:
    - file_id simple
    - custom: True
    """
    payload = {
        "draftPost": {
            "media": {
                "custom": True,
                "wixMedia": {
                    "image": {
                        "id": file_id,
                        "width": width,
                        "height": height
                    }
                }
            }
        }
    }

    logger.info(f"  cover_file_id_used={file_id}")
    logger.info(f"  cover_patch_payload_version=v2")
    logger.info(f"  cover_patch_custom=True")

    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.patch(
            f"https://www.wixapis.com/blog/v3/draft-posts/{draft_id}",
            headers={
                "Authorization": api_key,
                "wix-site-id": site_id,
                "Content-Type": "application/json",
            },
            json=payload,
        )

        if r.status_code not in (200, 204):
            logger.error(f"PATCH failed for {draft_id}: {r.status_code} {r.text}")
            return False

        # Vérification
        g = await client.get(
            f"https://www.wixapis.com/blog/v3/draft-posts/{draft_id}",
            headers={
                "Authorization": api_key,
                "wix-site-id": site_id,
                "Content-Type": "application/json",
            },
        )

        if g.status_code != 200:
            logger.warning(f"PATCH ok but verify failed for {draft_id}: {g.status_code}")
            return True

        data = g.json().get("draftPost", {})
        media = data.get("media", {})
        image = media.get("wixMedia", {}).get("image", {})

        saved_id = image.get("id")
        saved_custom = media.get("custom")

        if saved_id == file_id and saved_custom is True:
            logger.info(f"  ✅ Cover verified: saved_id={saved_id}, custom={saved_custom}")
            return True

        logger.warning(
            f"PATCH accepted but mismatch for {draft_id} | saved_id={saved_id} custom={saved_custom}"
        )
        return False


async def publish_wix_draft(api_key: str, site_id: str, draft_id: str) -> bool:
    """Publie un draft"""
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post(
            f"https://www.wixapis.com/blog/v3/draft-posts/{draft_id}/publish",
            headers={
                "Authorization": api_key,
                "wix-site-id": site_id,
                "Content-Type": "application/json",
            },
        )
        return r.status_code in (200, 201)


async def fix_single_post(api_key: str, site_id: str, post: dict) -> bool:
    """Corrige un seul post: revert → patch → publish"""
    post_id = post.get("id")
    title = post.get("title", "")[:50]
    
    is_broken, file_id, width, height = is_cover_broken(post)
    
    if not is_broken:
        logger.info(f"  Post déjà OK, skip")
        return True
    
    if not file_id:
        logger.error(f"  Impossible d'extraire file_id")
        return False
    
    logger.info(f"  Revert to draft...")
    draft_id = await revert_post_to_draft(api_key, site_id, post_id)
    
    if not draft_id:
        logger.error(f"  Échec revert-to-draft")
        return False
    
    logger.info(f"  Draft créé: {draft_id}")
    
    logger.info(f"  PATCH cover v2...")
    patched = await patch_cover_v2(api_key, site_id, draft_id, file_id, width, height)
    
    if not patched:
        logger.error(f"  Échec PATCH")
        return False
    
    logger.info(f"  Republish...")
    published = await publish_wix_draft(api_key, site_id, draft_id)
    
    if not published:
        logger.error(f"  Échec publish")
        return False
    
    logger.info(f"  ✅ Post corrigé et republié!")
    return True


async def main(dry_run: bool = True):
    logger.info("=" * 60)
    logger.info("MIGRATION DES COVERS CASSÉES - V2")
    logger.info(f"Mode: {'DRY-RUN (simulation)' if dry_run else 'FIX (application réelle)'}")
    logger.info("=" * 60)
    
    posts = await get_recent_posts(20)
    logger.info(f"\n{len(posts)} posts récents trouvés\n")
    
    broken_posts = []
    
    for post in posts:
        title = post.get("title", "Sans titre")[:50]
        post_id = post.get("id")
        
        is_broken, file_id, width, height = is_cover_broken(post)
        status = "❌ CASSÉ" if is_broken else "✅ OK"
        
        media = post.get("media", {})
        custom = media.get("custom", "N/A")
        image_id = media.get("wixMedia", {}).get("image", {}).get("id", "NONE")
        
        logger.info(f"{status} | {title}")
        logger.info(f"       id: {image_id[:60]}...")
        logger.info(f"       custom: {custom}")
        
        if is_broken:
            broken_posts.append(post)
        
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
    
    logger.info("\n" + "=" * 60)
    logger.info("APPLICATION DES CORRECTIONS")
    logger.info("=" * 60 + "\n")
    
    fixed = 0
    failed = 0
    
    for post in broken_posts:
        title = post.get("title", "")[:50]
        logger.info(f"\n📝 Correction: {title}")
        
        success = await fix_single_post(WIX_API_KEY, WIX_SITE_ID, post)
        
        if success:
            fixed += 1
        else:
            failed += 1
    
    logger.info("\n" + "=" * 60)
    logger.info(f"TERMINÉ: {fixed} corrigés, {failed} échecs")
    logger.info("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fix broken blog covers V2")
    parser.add_argument("--dry-run", action="store_true", help="Simulation seulement")
    parser.add_argument("--fix", action="store_true", help="Appliquer les corrections")
    
    args = parser.parse_args()
    
    if not args.dry_run and not args.fix:
        print("Usage:")
        print("  python fix_broken_covers.py --dry-run    # Voir ce qui serait modifié")
        print("  python fix_broken_covers.py --fix        # Appliquer les corrections")
        exit(1)
    
    asyncio.run(main(dry_run=args.dry_run))
