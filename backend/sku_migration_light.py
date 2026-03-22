#!/usr/bin/env python3
"""
LUXURA - MIGRATION SKU LÉGÈRE
Utilise l'inventaire pour récupérer les IDs, puis met à jour un par un.
"""

import requests
import time
import re
import argparse
from datetime import datetime

LUXURA_API_URL = "https://luxura-inventory-api.onrender.com"
DELAY = 2.0
TIMEOUT = 30

# Import color system
import sys
sys.path.insert(0, '/app/backend')
from color_system import get_color_info

ALLOWED_CATEGORIES = {'genius', 'tape', 'i-tip', 'halo', 'essentiels'}
EXCLUDED_KEYWORDS = ['clips', 'ponytail', 'queue de cheval', 'test']


def log(msg, level="INFO"):
    ts = datetime.now().strftime("%H:%M:%S")
    prefix = {"INFO": "✓", "WARN": "⚠", "ERROR": "✗", "SUCCESS": "✅"}.get(level, "•")
    print(f"[{ts}] {prefix} {msg}")


def detect_category(handle: str, name: str):
    if not handle:
        handle = ""
    h = handle.lower()
    n = name.lower()
    
    for ex in EXCLUDED_KEYWORDS:
        if ex in h or ex in n:
            return None
    
    if 'genius' in h or 'vivian' in h or 'trame-invisible' in h:
        return 'genius'
    elif 'halo' in h or ('everly' in h and 'clips' not in h):
        return 'halo'
    elif 'bande' in h or 'aurora' in h or 'tape' in h:
        return 'tape'
    elif 'i-tip' in h or 'itip' in h or 'eleanor' in h:
        return 'i-tip'
    
    if 'genius' in n or 'vivian' in n:
        return 'genius'
    elif 'halo' in n:
        return 'halo'
    elif 'bande' in n or 'aurora' in n:
        return 'tape'
    elif 'i-tip' in n:
        return 'i-tip'
    
    essentials = ['spray', 'brosse', 'fer', 'shampooing', 'anneau', 'ensemble', 'kit', 'accessoire', 'outil', 'colle', 'peigne']
    for kw in essentials:
        if kw in n or kw in h:
            return 'essentiels'
    
    return 'essentiels'


def extract_color_code(name: str) -> str:
    if not name:
        return ''
    m = re.search(r'#([A-Za-z0-9/]+)', name)
    return m.group(1).upper() if m else ''


def generate_sku(product: dict) -> str:
    """
    Génère SKU format Luxura: TYPE-LONGUEUR-POIDS-CODE-NOM
    Ex: H-16-120-60A-PLATINE-PUR
    """
    name = product.get('name') or ''
    handle = product.get('handle') or ''
    
    h = handle.lower()
    if 'halo' in h or 'everly' in h:
        prefix = 'H'
    elif 'genius' in h or 'vivian' in h:
        prefix = 'G'
    elif 'bande' in h or 'aurora' in h or 'tape' in h:
        prefix = 'T'
    elif 'i-tip' in h or 'eleanor' in h:
        prefix = 'I'
    else:
        prefix = 'E'
    
    # Extraire longueur et poids: "16" 120 grammes" ou "20' 140 grammes"
    length, weight = '', ''
    m = re.search(r'(\d+)["\'\′]?\s*(\d+)\s*gram', name.lower())
    if m:
        length, weight = m.group(1), m.group(2)
    
    # Extraire code couleur et nom luxura
    color_code = extract_color_code(name)
    color_info = get_color_info(color_code)
    sku_name = color_info.get("sku", color_code.replace("/", "-"))
    clean_code = color_code.replace('/', '-')
    
    # Format: TYPE-LONGUEUR-POIDS-CODE-NOM
    if length and weight:
        return f'{prefix}-{length}-{weight}-{clean_code}-{sku_name}'.upper()
    else:
        # Produit sans variante (accessoire)
        return f'{prefix}-{clean_code}-{sku_name}'.upper()


def fetch_product(product_id: int) -> dict:
    """Récupère un produit par son ID"""
    try:
        r = requests.get(f"{LUXURA_API_URL}/products/{product_id}", timeout=TIMEOUT)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return None


def update_sku(product_id: int, new_sku: str) -> bool:
    """Met à jour le SKU"""
    for attempt in range(3):
        try:
            time.sleep(DELAY)
            r = requests.put(
                f"{LUXURA_API_URL}/products/{product_id}",
                json={"sku": new_sku},
                timeout=TIMEOUT
            )
            if r.status_code == 200:
                return True
            log(f"  HTTP {r.status_code} - retry {attempt+1}/3", "WARN")
        except Exception as e:
            log(f"  Erreur: {e} - retry {attempt+1}/3", "WARN")
        time.sleep(3)
    return False


def get_product_ids_from_range(start: int, end: int, category_filter: str = None):
    """Récupère les produits par plage d'IDs"""
    products = []
    log(f"Scan des IDs {start} à {end}...")
    
    for pid in range(start, end + 1):
        p = fetch_product(pid)
        if p:
            name = p.get('name', '')
            handle = p.get('handle', '')
            cat = detect_category(handle, name)
            
            if cat and cat in ALLOWED_CATEGORIES:
                if category_filter is None or cat == category_filter:
                    products.append(p)
        
        # Progress every 100
        if pid % 100 == 0:
            log(f"  Scanné jusqu'à ID {pid}, trouvé {len(products)} produits")
        
        time.sleep(0.1)  # Petit délai pour ne pas surcharger
    
    return products


def migrate_by_id_range(start_id: int, end_id: int, category_filter: str = None):
    """Migration par plage d'IDs"""
    
    # Récupérer les produits
    products = get_product_ids_from_range(start_id, end_id, category_filter)
    
    log(f"Trouvé {len(products)} produits à traiter", "SUCCESS")
    
    updated = 0
    skipped = 0
    errors = 0
    
    for i, p in enumerate(products, 1):
        pid = p.get('id')
        name = p.get('name', '')[:40]
        old_sku = p.get('sku') or ''
        new_sku = generate_sku(p)
        
        if old_sku == new_sku:
            skipped += 1
            continue
        
        print(f"\n[{i}/{len(products)}] {name}")
        print(f"    {old_sku or '(vide)'} → {new_sku}")
        
        if update_sku(pid, new_sku):
            log("OK", "SUCCESS")
            updated += 1
        else:
            log("ÉCHEC", "ERROR")
            errors += 1
    
    print("\n" + "=" * 50)
    print(f"✅ Mis à jour: {updated}")
    print(f"⏭️  Ignorés: {skipped}")
    print(f"❌ Erreurs: {errors}")
    print("=" * 50)


def main():
    parser = argparse.ArgumentParser(description="Migration SKU par plage d'IDs")
    parser.add_argument('--start', type=int, default=1000, help='ID de départ')
    parser.add_argument('--end', type=int, default=1500, help='ID de fin')
    parser.add_argument('--category', type=str, choices=['genius', 'halo', 'tape', 'i-tip', 'essentiels'])
    
    args = parser.parse_args()
    
    print("=" * 50)
    print("LUXURA - MIGRATION SKU LÉGÈRE")
    print("=" * 50)
    print(f"Plage: {args.start} - {args.end}")
    print(f"Catégorie: {args.category or 'TOUTES'}")
    print("=" * 50)
    
    migrate_by_id_range(args.start, args.end, args.category)


if __name__ == "__main__":
    main()
