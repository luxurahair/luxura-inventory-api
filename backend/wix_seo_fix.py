#!/usr/bin/env python3
"""
Wix SEO Fix Script - Corrige les collections Clips et Ponytail
1. Ajoute les Clip-In Sophia à la collection Clips
2. Retire les Genius Vivian de la collection Clips
3. Ajoute les Ponytail Victoria à la collection Ponytail
"""

import asyncio
import httpx
import os
from dotenv import load_dotenv
from typing import List, Dict

load_dotenv()

WIX_API_KEY = os.getenv("WIX_API_KEY")
WIX_SITE_ID = os.getenv("WIX_SITE_ID")

HEADERS = {
    "Authorization": WIX_API_KEY,
    "wix-site-id": WIX_SITE_ID,
    "Content-Type": "application/json"
}

# IDs des collections
COLLECTION_IDS = {
    "clips": "e6f52b5b-fb69-4d04-b0c4-b8704b50fc86",
    "ponytail": "9e5314cd-e9f6-7f43-fd44-f6426dd3d72e",  # Collection principale Ponytail
    "ponytail_styled": "d6adc071-c1cd-4190-9691-9466377cd4cf",  # Queues de Cheval stylisées
}


async def get_all_products() -> List[Dict]:
    """Récupère tous les produits"""
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            "https://www.wixapis.com/stores/v1/products/query",
            headers=HEADERS,
            json={"query": {"paging": {"limit": 100}}, "includeVariants": False}
        )
        
        if response.status_code == 200:
            return response.json().get("products", [])
        return []


async def add_products_to_collection(collection_id: str, product_ids: List[str]) -> bool:
    """Ajoute des produits à une collection"""
    if not product_ids:
        return True
        
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            f"https://www.wixapis.com/stores/v1/collections/{collection_id}/productIds",
            headers=HEADERS,
            json={"productIds": product_ids}
        )
        
        if response.status_code in [200, 204]:
            print(f"   ✅ {len(product_ids)} produits ajoutés à la collection")
            return True
        else:
            print(f"   ❌ Erreur ajout: {response.status_code} - {response.text[:200]}")
            return False


async def remove_products_from_collection(collection_id: str, product_ids: List[str]) -> bool:
    """Retire des produits d'une collection"""
    if not product_ids:
        return True
        
    async with httpx.AsyncClient(timeout=60) as client:
        # Wix API utilise POST avec action remove pour retirer des produits
        response = await client.post(
            f"https://www.wixapis.com/stores/v1/collections/{collection_id}/productIds/delete",
            headers=HEADERS,
            json={"productIds": product_ids}
        )
        
        if response.status_code in [200, 204]:
            print(f"   ✅ {len(product_ids)} produits retirés de la collection")
            return True
        else:
            # Essayer avec une autre méthode
            print(f"   ⚠️ Méthode 1 échouée ({response.status_code}), essai méthode 2...")
            
            # Méthode alternative: mettre à jour le produit pour retirer la collection
            success_count = 0
            for pid in product_ids:
                try:
                    # Récupérer le produit
                    get_resp = await client.get(
                        f"https://www.wixapis.com/stores/v1/products/{pid}",
                        headers=HEADERS
                    )
                    if get_resp.status_code == 200:
                        product = get_resp.json().get("product", {})
                        current_cols = product.get("collectionIds", [])
                        
                        # Retirer la collection
                        new_cols = [c for c in current_cols if c != collection_id]
                        
                        # Mettre à jour
                        update_resp = await client.patch(
                            f"https://www.wixapis.com/stores/v1/products/{pid}",
                            headers=HEADERS,
                            json={"product": {"collectionIds": new_cols}}
                        )
                        if update_resp.status_code == 200:
                            success_count += 1
                except Exception as e:
                    print(f"   ⚠️ Erreur pour {pid}: {e}")
            
            print(f"   ✅ {success_count}/{len(product_ids)} produits retirés (méthode 2)")
            return success_count > 0


async def fix_clips_collection(products: List[Dict], dry_run: bool = True):
    """Corrige la collection Clips"""
    print("\n" + "=" * 60)
    print("📎 CORRECTION - Collection CLIPS")
    print("=" * 60)
    
    clips_id = COLLECTION_IDS["clips"]
    
    # Trouver les Clip-In qui ne sont pas dans Clips
    clips_to_add = []
    # Trouver les Genius qui sont dans Clips (à retirer)
    genius_to_remove = []
    
    for p in products:
        name = p.get("name", "").lower()
        pid = p.get("id")
        cols = p.get("collectionIds", [])
        
        # Clip-In Sophia pas dans Clips
        if ("clip" in name or "sophia" in name) and "genius" not in name:
            if clips_id not in cols:
                clips_to_add.append(pid)
                print(f"   ➕ À AJOUTER: {p.get('name')[:50]}")
        
        # Genius dans Clips (mal placé)
        if "genius" in name or "vivian" in name:
            if clips_id in cols:
                genius_to_remove.append(pid)
                print(f"   ➖ À RETIRER: {p.get('name')[:50]}")
    
    print(f"\n📊 Résumé Clips:")
    print(f"   - {len(clips_to_add)} Clip-In à ajouter")
    print(f"   - {len(genius_to_remove)} Genius à retirer")
    
    if dry_run:
        print("\n⚠️ MODE DRY-RUN - Aucune modification effectuée")
        return {"to_add": clips_to_add, "to_remove": genius_to_remove}
    
    # Exécuter les corrections
    if clips_to_add:
        print("\n🔧 Ajout des Clip-In...")
        await add_products_to_collection(clips_id, clips_to_add)
    
    if genius_to_remove:
        print("\n🔧 Retrait des Genius...")
        await remove_products_from_collection(clips_id, genius_to_remove)
    
    return {"added": clips_to_add, "removed": genius_to_remove}


async def fix_ponytail_collection(products: List[Dict], dry_run: bool = True):
    """Corrige la collection Ponytail"""
    print("\n" + "=" * 60)
    print("🐴 CORRECTION - Collection PONYTAIL")
    print("=" * 60)
    
    pony_id = COLLECTION_IDS["ponytail"]
    pony_styled_id = COLLECTION_IDS["ponytail_styled"]
    
    # Trouver les Ponytail qui ne sont dans aucune collection Ponytail
    ponytails_to_add = []
    
    for p in products:
        name = p.get("name", "").lower()
        pid = p.get("id")
        cols = p.get("collectionIds", [])
        
        # Ponytail Victoria pas dans les collections Ponytail
        if "pony" in name or "victoria" in name:
            if pony_id not in cols and pony_styled_id not in cols:
                ponytails_to_add.append(pid)
                print(f"   ➕ À AJOUTER: {p.get('name')[:50]}")
    
    print(f"\n📊 Résumé Ponytail:")
    print(f"   - {len(ponytails_to_add)} Ponytail à ajouter")
    
    if dry_run:
        print("\n⚠️ MODE DRY-RUN - Aucune modification effectuée")
        return {"to_add": ponytails_to_add}
    
    # Exécuter les corrections - ajouter aux deux collections
    if ponytails_to_add:
        print("\n🔧 Ajout à la collection Ponytail principale...")
        await add_products_to_collection(pony_id, ponytails_to_add)
        
        print("\n🔧 Ajout à la collection Queues de Cheval stylisées...")
        await add_products_to_collection(pony_styled_id, ponytails_to_add)
    
    return {"added": ponytails_to_add}


async def main(dry_run: bool = True):
    """Point d'entrée principal"""
    print("🚀 SCRIPT DE CORRECTION SEO WIX")
    print("=" * 60)
    
    if dry_run:
        print("⚠️ MODE DRY-RUN ACTIVÉ - Aucune modification ne sera effectuée")
        print("   Pour appliquer les corrections, relancez avec dry_run=False")
    else:
        print("🔴 MODE LIVE - Les modifications seront appliquées!")
    
    # Récupérer tous les produits
    print("\n📦 Récupération des produits...")
    products = await get_all_products()
    print(f"   {len(products)} produits trouvés")
    
    # Corriger Clips
    clips_result = await fix_clips_collection(products, dry_run)
    
    # Corriger Ponytail
    pony_result = await fix_ponytail_collection(products, dry_run)
    
    print("\n" + "=" * 60)
    print("✅ ANALYSE TERMINÉE")
    print("=" * 60)
    
    if dry_run:
        print("\n💡 Pour appliquer les corrections, exécutez:")
        print("   python wix_seo_fix.py --apply")
    
    return {"clips": clips_result, "ponytail": pony_result}


if __name__ == "__main__":
    import sys
    
    dry_run = "--apply" not in sys.argv
    
    asyncio.run(main(dry_run=dry_run))
