#!/usr/bin/env python3
"""
Wix SEO Cleanup Script
- Lister les catégories et produits
- Identifier les produits mal placés (ex: Genius dans Pony)
- Nettoyer les descriptions SEO
- Vérifier les 404
"""

import os
import asyncio
import httpx
import json
from dotenv import load_dotenv
from typing import Dict, List, Optional

load_dotenv()

WIX_API_KEY = os.getenv("WIX_API_KEY")
WIX_SITE_ID = os.getenv("WIX_SITE_ID")

HEADERS = {
    "Authorization": WIX_API_KEY,
    "wix-site-id": WIX_SITE_ID,
    "Content-Type": "application/json"
}


async def get_all_collections() -> List[Dict]:
    """Récupère toutes les collections (catégories) du store Wix"""
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            "https://www.wixapis.com/stores/v1/collections/query",
            headers=HEADERS,
            json={"query": {"paging": {"limit": 100}}}
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("collections", [])
        else:
            print(f"❌ Error getting collections: {response.status_code}")
            print(response.text)
            return []


async def get_products_in_collection(collection_id: str) -> List[Dict]:
    """Récupère tous les produits d'une collection"""
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            "https://www.wixapis.com/stores/v1/products/query",
            headers=HEADERS,
            json={
                "query": {
                    "filter": {
                        "collectionIds": {"$hasSome": [collection_id]}
                    },
                    "paging": {"limit": 100}
                },
                "includeVariants": False
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("products", [])
        else:
            print(f"❌ Error getting products: {response.status_code}")
            print(response.text[:500])
            return []


async def get_all_products() -> List[Dict]:
    """Récupère tous les produits du store"""
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            "https://www.wixapis.com/stores/v1/products/query",
            headers=HEADERS,
            json={
                "query": {
                    "paging": {"limit": 100}
                },
                "includeVariants": False
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("products", [])
        else:
            print(f"❌ Error getting products: {response.status_code}")
            print(response.text[:500])
            return []


async def update_product(product_id: str, updates: Dict) -> bool:
    """Met à jour un produit"""
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.patch(
            f"https://www.wixapis.com/stores/v1/products/{product_id}",
            headers=HEADERS,
            json={"product": updates}
        )
        
        if response.status_code == 200:
            print(f"✅ Product {product_id} updated")
            return True
        else:
            print(f"❌ Error updating product: {response.status_code}")
            print(response.text[:500])
            return False


async def remove_product_from_collection(product_id: str, collection_id: str) -> bool:
    """Retire un produit d'une collection"""
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            f"https://www.wixapis.com/stores/v1/collections/{collection_id}/removeProducts",
            headers=HEADERS,
            json={"productIds": [product_id]}
        )
        
        if response.status_code in [200, 204]:
            print(f"✅ Product {product_id} removed from collection {collection_id}")
            return True
        else:
            print(f"❌ Error removing product: {response.status_code}")
            print(response.text[:500])
            return False


def identify_misplaced_products(products: List[Dict], expected_keywords: List[str], collection_name: str) -> List[Dict]:
    """
    Identifie les produits qui ne correspondent pas à la catégorie.
    
    Args:
        products: Liste des produits dans la collection
        expected_keywords: Mots-clés attendus dans le nom (ex: ["clip", "clips"] pour Clips)
        collection_name: Nom de la collection pour le log
    
    Returns:
        Liste des produits mal placés
    """
    misplaced = []
    
    for product in products:
        name = product.get("name", "").lower()
        
        # Vérifie si le produit contient un des mots-clés attendus
        has_expected = any(kw in name for kw in expected_keywords)
        
        # Détecte les produits d'autres catégories
        is_genius = "genius" in name or "vivian" in name
        is_halo = "halo" in name or "everly" in name
        is_tape = "tape" in name or "aurora" in name
        is_itip = "i-tip" in name or "itip" in name or "eleanor" in name
        
        # Si c'est un produit d'une autre catégorie, il est mal placé
        if not has_expected:
            misplaced.append({
                "id": product.get("id"),
                "name": product.get("name"),
                "slug": product.get("slug"),
                "reason": f"Ne contient pas de mot-clé attendu pour {collection_name}",
                "detected_category": "genius" if is_genius else "halo" if is_halo else "tape" if is_tape else "itip" if is_itip else "unknown"
            })
    
    return misplaced


async def audit_collections():
    """Audit complet des collections Clips et Pony"""
    print("=" * 60)
    print("🔍 AUDIT SEO - Collections Wix")
    print("=" * 60)
    
    # 1. Récupérer toutes les collections
    print("\n📂 Récupération des collections...")
    collections = await get_all_collections()
    
    if not collections:
        print("❌ Aucune collection trouvée")
        return
    
    print(f"✅ {len(collections)} collections trouvées:\n")
    
    for col in collections:
        print(f"   - {col.get('name', 'N/A')} (ID: {col.get('id', 'N/A')[:8]}...)")
    
    # 2. Trouver Clips et Pony
    clips_col = None
    pony_col = None
    
    for col in collections:
        name_lower = col.get("name", "").lower()
        if "clip" in name_lower:
            clips_col = col
        if "pony" in name_lower or "queue" in name_lower:
            pony_col = col
    
    # 3. Analyser Clips
    print("\n" + "=" * 60)
    print("📎 ANALYSE - Collection CLIPS")
    print("=" * 60)
    
    if clips_col:
        print(f"ID: {clips_col.get('id')}")
        print(f"Nom: {clips_col.get('name')}")
        print(f"Description: {clips_col.get('description', 'Aucune')[:100]}...")
        
        products = await get_products_in_collection(clips_col.get("id"))
        print(f"\n📦 {len(products)} produits dans cette collection:")
        
        if products:
            for p in products:
                print(f"   - {p.get('name')} (slug: {p.get('slug')})")
            
            # Identifier les mal placés
            misplaced = identify_misplaced_products(products, ["clip", "clips"], "Clips")
            if misplaced:
                print(f"\n⚠️ {len(misplaced)} PRODUITS MAL PLACÉS:")
                for m in misplaced:
                    print(f"   🔴 {m['name']}")
                    print(f"      → Détecté comme: {m['detected_category']}")
                    print(f"      → Raison: {m['reason']}")
        else:
            print("   ⚠️ COLLECTION VIDE - Problème SEO!")
    else:
        print("❌ Collection Clips non trouvée")
    
    # 4. Analyser Pony
    print("\n" + "=" * 60)
    print("🐴 ANALYSE - Collection PONY / QUEUE DE CHEVAL")
    print("=" * 60)
    
    if pony_col:
        print(f"ID: {pony_col.get('id')}")
        print(f"Nom: {pony_col.get('name')}")
        print(f"Description: {pony_col.get('description', 'Aucune')[:100]}...")
        
        products = await get_products_in_collection(pony_col.get("id"))
        print(f"\n📦 {len(products)} produits dans cette collection:")
        
        if products:
            for p in products:
                print(f"   - {p.get('name')} (slug: {p.get('slug')})")
            
            # Identifier les mal placés
            misplaced = identify_misplaced_products(products, ["pony", "queue", "ponytail"], "Pony")
            if misplaced:
                print(f"\n⚠️ {len(misplaced)} PRODUITS MAL PLACÉS:")
                for m in misplaced:
                    print(f"   🔴 {m['name']}")
                    print(f"      → Détecté comme: {m['detected_category']}")
                    print(f"      → Raison: {m['reason']}")
        else:
            print("   ⚠️ COLLECTION VIDE - Problème SEO!")
    else:
        print("❌ Collection Pony non trouvée")
    
    # 5. Résumé
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ DE L'AUDIT")
    print("=" * 60)
    
    return {
        "clips": clips_col,
        "pony": pony_col,
        "all_collections": collections
    }


async def check_blog_404s():
    """Vérifie les articles de blog qui pourraient avoir des 404"""
    print("\n" + "=" * 60)
    print("🔗 VÉRIFICATION DES 404 - Articles de Blog")
    print("=" * 60)
    
    async with httpx.AsyncClient(timeout=60) as client:
        # Récupérer les posts publiés
        response = await client.post(
            "https://www.wixapis.com/blog/v3/posts/query",
            headers=HEADERS,
            json={
                "query": {
                    "paging": {"limit": 50}
                }
            }
        )
        
        if response.status_code != 200:
            print(f"❌ Erreur récupération blogs: {response.status_code}")
            return []
        
        data = response.json()
        posts = data.get("posts", [])
        
        print(f"📝 {len(posts)} articles trouvés\n")
        
        # Vérifier chaque URL
        problematic = []
        for post in posts:
            title = post.get("title", "Sans titre")
            url = post.get("url", "")
            slug = post.get("slug", "")
            
            if url:
                try:
                    check = await client.get(url, follow_redirects=True, timeout=10)
                    status = check.status_code
                    
                    if status == 404:
                        print(f"   🔴 404: {title[:50]}...")
                        print(f"      URL: {url}")
                        problematic.append({"title": title, "url": url, "status": 404})
                    elif status >= 400:
                        print(f"   🟠 {status}: {title[:50]}...")
                        problematic.append({"title": title, "url": url, "status": status})
                    else:
                        print(f"   ✅ {status}: {title[:40]}...")
                except Exception as e:
                    print(f"   ⚠️ Erreur check: {title[:40]}... - {e}")
        
        if problematic:
            print(f"\n⚠️ {len(problematic)} URLs PROBLÉMATIQUES trouvées!")
        else:
            print(f"\n✅ Tous les articles sont accessibles")
        
        return problematic


async def main():
    """Point d'entrée principal"""
    print("🚀 Démarrage de l'audit SEO Wix...\n")
    
    # Audit des collections
    result = await audit_collections()
    
    # Vérification des 404
    blog_issues = await check_blog_404s()
    
    print("\n" + "=" * 60)
    print("✅ AUDIT TERMINÉ")
    print("=" * 60)
    
    return {
        "collections": result,
        "blog_404s": blog_issues
    }


if __name__ == "__main__":
    asyncio.run(main())
