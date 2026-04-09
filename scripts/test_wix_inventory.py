#!/usr/bin/env python3
"""
Test script pour analyser la structure de l'inventaire Wix.
Objectif: comprendre comment productId, variantId, SKU et quantités sont liés.
"""
import os
import sys
import json

# Permet d'importer "app.*"
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.services.wix_client import WixClient


def test_inventory_structure():
    """Analyse la structure de l'inventaire Wix"""
    client = WixClient()
    
    print("=" * 80)
    print("TEST 1: Query Inventory Items (stores-reader/v2/inventoryItems/query)")
    print("=" * 80)
    
    try:
        inv_response = client.query_inventory_items_v1(limit=10, offset=0)
        
        print(f"\n📦 Clés de la réponse: {list(inv_response.keys())}")
        
        items = inv_response.get("inventoryItems") or inv_response.get("items") or []
        print(f"📊 Nombre d'items: {len(items)}")
        
        if items:
            print("\n--- STRUCTURE D'UN ITEM D'INVENTAIRE ---")
            print(json.dumps(items[0], indent=2, default=str))
            
            print("\n--- ANALYSE DE TOUS LES ITEMS ---")
            for i, item in enumerate(items[:5]):  # Premiers 5
                product_id = item.get("productId") or item.get("externalId")
                track_qty = item.get("trackQuantity", False)
                variants = item.get("variants") or []
                
                print(f"\n[Item {i+1}] productId: {product_id}")
                print(f"         trackQuantity: {track_qty}")
                print(f"         variants count: {len(variants)}")
                
                for j, v in enumerate(variants[:3]):  # Premiers 3 variants
                    vid = v.get("variantId") or v.get("id")
                    qty = v.get("quantity", 0)
                    sku = (
                        v.get("sku") or 
                        v.get("stockKeepingUnit") or 
                        v.get("vendorSku") or
                        (v.get("skuData") or {}).get("sku")
                    )
                    in_stock = v.get("inStock", False)
                    
                    print(f"         [Variant {j+1}] variantId: {vid}")
                    print(f"                     sku: {sku}")
                    print(f"                     quantity: {qty}")
                    print(f"                     inStock: {in_stock}")
                    
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()


def test_products_structure():
    """Analyse la structure des produits Wix"""
    client = WixClient()
    
    print("\n" + "=" * 80)
    print("TEST 2: Query Products (stores/v1/products/query)")
    print("=" * 80)
    
    try:
        version, products = client.query_products(limit=5)
        
        print(f"\n📦 Version catalogue: {version}")
        print(f"📊 Nombre de produits: {len(products)}")
        
        if products:
            print("\n--- STRUCTURE D'UN PRODUIT ---")
            # Afficher les clés principales
            p = products[0]
            print(f"Clés: {list(p.keys())}")
            
            print("\n--- ANALYSE DES PRODUITS ---")
            for i, p in enumerate(products[:5]):
                pid = p.get("id") or p.get("_id")
                name = p.get("name", "")[:50]
                sku = p.get("sku")
                
                # Inventory info
                inv = p.get("inventory") or p.get("stock") or {}
                qty = inv.get("quantity", "N/A")
                track = inv.get("trackQuantity", "N/A")
                in_stock = inv.get("inStock", "N/A")
                
                print(f"\n[Produit {i+1}] id: {pid}")
                print(f"            name: {name}")
                print(f"            sku: {sku}")
                print(f"            inventory.quantity: {qty}")
                print(f"            inventory.trackQuantity: {track}")
                print(f"            inventory.inStock: {in_stock}")
                
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()


def test_variants_structure():
    """Analyse la structure des variants pour un produit"""
    client = WixClient()
    
    print("\n" + "=" * 80)
    print("TEST 3: Query Variants (stores/v1/products/{id}/variants/query)")
    print("=" * 80)
    
    try:
        # D'abord récupérer un produit
        version, products = client.query_products(limit=1)
        
        if not products:
            print("❌ Aucun produit trouvé")
            return
            
        product_id = products[0].get("id") or products[0].get("_id")
        product_name = products[0].get("name", "")[:50]
        
        print(f"\n🎯 Test avec produit: {product_name}")
        print(f"   productId: {product_id}")
        
        variants = client.query_variants_v1(product_id, limit=10)
        
        print(f"\n📊 Nombre de variants: {len(variants)}")
        
        if variants:
            print("\n--- STRUCTURE D'UN VARIANT ---")
            print(json.dumps(variants[0], indent=2, default=str))
            
            print("\n--- ANALYSE DES VARIANTS ---")
            for i, v in enumerate(variants[:5]):
                vid = v.get("id") or v.get("variantId")
                sku = v.get("sku") or v.get("variant", {}).get("sku")
                
                # Prix
                price_data = v.get("variant", {}).get("priceData") or v.get("priceData") or {}
                price = price_data.get("price", "N/A")
                
                # Stock
                stock = v.get("stock") or v.get("inventory") or {}
                qty = stock.get("quantity", "N/A")
                track = stock.get("trackQuantity", "N/A")
                in_stock = stock.get("inStock", "N/A")
                
                print(f"\n[Variant {i+1}] variantId: {vid}")
                print(f"            sku: {sku}")
                print(f"            price: {price}")
                print(f"            stock.quantity: {qty}")
                print(f"            stock.trackQuantity: {track}")
                print(f"            stock.inStock: {in_stock}")
                
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()


def test_mapping_comparison():
    """Compare les IDs entre products, variants et inventory"""
    client = WixClient()
    
    print("\n" + "=" * 80)
    print("TEST 4: COMPARAISON DES MAPPINGS")
    print("=" * 80)
    
    try:
        # 1. Récupérer l'inventaire
        inv_response = client.query_inventory_items_v1(limit=50, offset=0)
        items = inv_response.get("inventoryItems") or inv_response.get("items") or []
        
        # Construire le mapping comme dans wix.py
        inv_map = {}
        for item in items:
            pid = (item.get("productId") or "").strip()
            if not pid:
                continue
            
            for v in (item.get("variants") or []):
                vid = (v.get("variantId") or v.get("id") or "").strip()
                if not vid:
                    continue
                    
                qty = int(v.get("quantity") or 0)
                sku = v.get("sku") or v.get("stockKeepingUnit")
                
                key = f"{pid}:{vid}"
                inv_map[key] = {"qty": qty, "sku": sku, "track": item.get("trackQuantity", False)}
        
        print(f"\n📦 inv_map construit avec {len(inv_map)} entrées")
        print("\n--- Premières 10 clés de inv_map ---")
        for i, (k, v) in enumerate(list(inv_map.items())[:10]):
            print(f"  {k} -> qty={v['qty']}, sku={v['sku']}, track={v['track']}")
        
        # 2. Récupérer les produits et variants
        version, products = client.query_products(limit=5)
        
        print(f"\n\n🔍 Test de matching pour {len(products)} produits...")
        
        matches = 0
        misses = 0
        
        for p in products:
            product_id = p.get("id") or p.get("_id")
            product_name = p.get("name", "")[:40]
            
            variants = client.query_variants_v1(product_id, limit=10)
            
            for v in variants:
                variant_id = v.get("id") or v.get("variantId")
                sku = v.get("sku") or v.get("variant", {}).get("sku")
                
                # Essayer le matching comme dans wix.py
                key = f"{product_id}:{variant_id}"
                inv_data = inv_map.get(key)
                
                if inv_data:
                    matches += 1
                    print(f"\n✅ MATCH: {product_name}")
                    print(f"   Key: {key}")
                    print(f"   SKU: {sku}")
                    print(f"   Quantity: {inv_data['qty']}")
                else:
                    misses += 1
                    print(f"\n❌ NO MATCH: {product_name}")
                    print(f"   Key cherchée: {key}")
                    print(f"   SKU: {sku}")
                    
                    # Chercher des clés similaires
                    similar = [k for k in inv_map.keys() if product_id in k]
                    if similar:
                        print(f"   Clés similaires trouvées:")
                        for s in similar[:3]:
                            print(f"     - {s}")
        
        print(f"\n\n📊 RÉSUMÉ:")
        print(f"   Matches: {matches}")
        print(f"   Misses: {misses}")
        print(f"   Taux de match: {matches/(matches+misses)*100:.1f}%" if (matches+misses) > 0 else "   N/A")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("🧪 TESTS D'ANALYSE DE L'INVENTAIRE WIX")
    print("=" * 80)
    
    test_inventory_structure()
    test_products_structure()
    test_variants_structure()
    test_mapping_comparison()
    
    print("\n" + "=" * 80)
    print("🏁 TESTS TERMINÉS")
    print("=" * 80)
