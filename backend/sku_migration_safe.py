#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════
LUXURA - MIGRATION SKU SÉCURISÉE
═══════════════════════════════════════════════════════════════════════════
Script de migration des SKUs vers le format Luxura, un produit à la fois
avec délais pour éviter les timeouts de l'API Render.

Usage:
    python sku_migration_safe.py --dry-run              # Prévisualiser
    python sku_migration_safe.py --category halo        # Migrer une catégorie
    python sku_migration_safe.py --all                  # Migrer tout
═══════════════════════════════════════════════════════════════════════════
"""

import requests
import time
import argparse
import json
import re
from datetime import datetime
from color_system import get_color_info

# ═══════════════════ CONFIGURATION ═══════════════════

LUXURA_API_URL = "https://luxura-inventory-api.onrender.com"
DELAY_BETWEEN_REQUESTS = 0.5  # Secondes entre chaque requête
TIMEOUT = 30  # Timeout par requête
MAX_RETRIES = 3

# Categories autorisées
ALLOWED_CATEGORIES = {'genius', 'tape', 'i-tip', 'halo', 'essentiels'}

# Mots-clés exclus
EXCLUDED_KEYWORDS = ['clips', 'ponytail', 'queue de cheval', 'test']


# ═══════════════════ HELPERS ═══════════════════

def log(msg, level="INFO"):
    """Log avec timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    prefix = {"INFO": "✓", "WARN": "⚠", "ERROR": "✗", "SUCCESS": "✅"}.get(level, "•")
    print(f"[{timestamp}] {prefix} {msg}")


def detect_category_from_handle(handle: str, name: str) -> str:
    """Détecter la catégorie du produit"""
    if not handle:
        handle = ""
    handle_lower = handle.lower()
    name_lower = name.lower()
    
    # EXCLUDE
    for excluded in EXCLUDED_KEYWORDS:
        if excluded in handle_lower or excluded in name_lower:
            return None
    
    # Detect category
    if 'genius' in handle_lower or 'vivian' in handle_lower or 'trame-invisible' in handle_lower:
        return 'genius'
    elif 'halo' in handle_lower or ('everly' in handle_lower and 'clips' not in handle_lower):
        return 'halo'
    elif 'bande' in handle_lower or 'aurora' in handle_lower or 'tape' in handle_lower or 'adhésive' in handle_lower:
        return 'tape'
    elif 'i-tip' in handle_lower or 'itip' in handle_lower or 'eleanor' in handle_lower:
        return 'i-tip'
    
    # Essentiels
    essentials_keywords = ['spray', 'brosse', 'fer', 'shampooing', 'lotion', 'anneau', 'ensemble', 
                          'duo', 'kit', 'accessoire', 'outil', 'colle', 'remover', 'peigne', 
                          'tenue ultra', 'installation']
    for keyword in essentials_keywords:
        if keyword in name_lower or keyword in handle_lower:
            return 'essentiels'
    
    # Fallback name check
    if 'genius' in name_lower or 'trame invisible' in name_lower or 'vivian' in name_lower:
        return 'genius'
    elif 'halo' in name_lower and 'clips' not in name_lower:
        return 'halo'
    elif 'bande' in name_lower or 'adhésive' in name_lower or 'aurora' in name_lower:
        return 'tape'
    elif 'i-tip' in name_lower or 'itip' in name_lower:
        return 'i-tip'
    
    return 'essentiels'


def extract_color_code(name: str) -> str:
    """Extraire le code couleur du nom"""
    if not name:
        return ''
    code_match = re.search(r'#([A-Za-z0-9/]+)', name)
    return code_match.group(1).upper() if code_match else ''


def generate_standardized_sku(product: dict) -> str:
    """Générer un SKU standardisé Luxura"""
    name = product.get('name') or ''
    handle = product.get('handle') or ''
    
    # Type prefix
    handle_lower = handle.lower()
    if 'halo' in handle_lower or 'everly' in handle_lower:
        prefix = 'H'
    elif 'genius' in handle_lower or 'vivian' in handle_lower:
        prefix = 'G'
    elif 'bande' in handle_lower or 'aurora' in handle_lower or 'tape' in handle_lower:
        prefix = 'T'
    elif 'i-tip' in handle_lower or 'eleanor' in handle_lower:
        prefix = 'I'
    else:
        prefix = 'E'
    
    # Extract length/weight
    length = ''
    weight = ''
    variant_match = re.search(r'(\d+)["\'\′]?\s*(\d+)\s*gram', name.lower())
    if variant_match:
        length = variant_match.group(1)
        weight = variant_match.group(2)
    
    # Color code
    color_code = extract_color_code(name)
    
    # Get SKU name from color system
    color_info = get_color_info(color_code)
    sku_name = color_info.get("sku", color_code.replace("/", "-"))
    
    # Clean color code for SKU
    clean_code = color_code.replace('/', '-')
    
    # Build SKU
    if length and weight:
        sku = f'{prefix}{length}{weight}-{clean_code}-{sku_name}'
    else:
        sku = f'{prefix}-{clean_code}-{sku_name}'
    
    return sku.upper()


# ═══════════════════ API FUNCTIONS ═══════════════════

def fetch_all_products():
    """Récupérer tous les produits de l'API Render avec retries"""
    log("Récupération des produits depuis l'API Render...")
    
    for attempt in range(MAX_RETRIES):
        try:
            log(f"  Tentative {attempt+1}/{MAX_RETRIES}...")
            response = requests.get(f"{LUXURA_API_URL}/products", timeout=60)  # Long timeout
            response.raise_for_status()
            products = response.json()
            log(f"Récupéré {len(products)} produits", "SUCCESS")
            return products
        except requests.exceptions.Timeout:
            log(f"  Timeout - attente avant retry...", "WARN")
            time.sleep(5)
        except Exception as e:
            log(f"  Erreur: {e}", "WARN")
            time.sleep(3)
    
    log("Impossible de récupérer les produits après plusieurs tentatives", "ERROR")
    return []


def update_product_sku(product_id: int, new_sku: str) -> bool:
    """Mettre à jour le SKU d'un produit avec retries"""
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.put(
                f"{LUXURA_API_URL}/products/{product_id}",
                json={"sku": new_sku},
                timeout=TIMEOUT
            )
            if response.status_code == 200:
                return True
            else:
                log(f"  HTTP {response.status_code} - Tentative {attempt+1}/{MAX_RETRIES}", "WARN")
        except requests.exceptions.Timeout:
            log(f"  Timeout - Tentative {attempt+1}/{MAX_RETRIES}", "WARN")
        except Exception as e:
            log(f"  Erreur: {e} - Tentative {attempt+1}/{MAX_RETRIES}", "WARN")
        
        if attempt < MAX_RETRIES - 1:
            time.sleep(DELAY_BETWEEN_REQUESTS * 2)
    
    return False


# ═══════════════════ MAIN MIGRATION ═══════════════════

def migrate_products(category_filter=None, dry_run=True):
    """
    Migration principale des SKUs
    
    Args:
        category_filter: Filtrer par catégorie (genius, halo, tape, i-tip, essentiels)
        dry_run: True = prévisualisation, False = appliquer les changements
    """
    products = fetch_all_products()
    if not products:
        log("Aucun produit trouvé", "ERROR")
        return
    
    # Stats
    stats = {
        "total": len(products),
        "filtered": 0,
        "to_update": 0,
        "updated": 0,
        "skipped": 0,
        "errors": 0
    }
    
    # Filter and prepare
    to_migrate = []
    
    for p in products:
        name = p.get('name') or ''
        handle = p.get('handle') or ''
        product_id = p.get('id')
        
        # Skip test products
        if 'test' in name.lower() and p.get('price', 0) < 1:
            continue
        
        # Detect category
        category = detect_category_from_handle(handle, name)
        if category is None or category not in ALLOWED_CATEGORIES:
            continue
        
        # Filter by category if specified
        if category_filter and category != category_filter:
            continue
        
        stats["filtered"] += 1
        
        old_sku = p.get('sku') or ''
        new_sku = generate_standardized_sku(p)
        
        # Skip if no change
        if old_sku == new_sku:
            stats["skipped"] += 1
            continue
        
        to_migrate.append({
            "id": product_id,
            "name": name[:50],
            "old_sku": old_sku or "(aucun)",
            "new_sku": new_sku,
            "category": category
        })
    
    stats["to_update"] = len(to_migrate)
    
    # Display summary
    print("\n" + "═" * 60)
    print("LUXURA - MIGRATION SKU")
    print("═" * 60)
    print(f"Mode: {'🔍 PRÉVISUALISATION' if dry_run else '🚀 MIGRATION RÉELLE'}")
    print(f"Catégorie: {category_filter or 'TOUTES'}")
    print(f"Total produits: {stats['total']}")
    print(f"Produits filtrés: {stats['filtered']}")
    print(f"À mettre à jour: {stats['to_update']}")
    print(f"Déjà corrects: {stats['skipped']}")
    print("═" * 60 + "\n")
    
    if not to_migrate:
        log("Aucun produit à migrer!", "SUCCESS")
        return stats
    
    # Preview or migrate
    if dry_run:
        print("PRÉVISUALISATION DES CHANGEMENTS:")
        print("-" * 60)
        for item in to_migrate[:50]:  # Show first 50
            print(f"  [{item['category'].upper():8}] {item['name'][:30]:30}")
            print(f"           OLD: {item['old_sku']:35}")
            print(f"           NEW: {item['new_sku']:35}")
            print()
        
        if len(to_migrate) > 50:
            print(f"  ... et {len(to_migrate) - 50} autres produits")
        
        print("\n💡 Pour appliquer les changements, relancez sans --dry-run")
    
    else:
        print("MIGRATION EN COURS...")
        print("-" * 60)
        
        for i, item in enumerate(to_migrate, 1):
            print(f"[{i}/{len(to_migrate)}] {item['name'][:40]}")
            print(f"         {item['old_sku']} → {item['new_sku']}")
            
            success = update_product_sku(item['id'], item['new_sku'])
            
            if success:
                log("OK", "SUCCESS")
                stats["updated"] += 1
            else:
                log("ÉCHEC", "ERROR")
                stats["errors"] += 1
            
            # Delay to avoid rate limiting
            time.sleep(DELAY_BETWEEN_REQUESTS)
        
        # Final report
        print("\n" + "═" * 60)
        print("RAPPORT FINAL")
        print("═" * 60)
        print(f"✅ Mis à jour: {stats['updated']}")
        print(f"⏭️  Ignorés (déjà OK): {stats['skipped']}")
        print(f"❌ Erreurs: {stats['errors']}")
        print("═" * 60)
    
    return stats


# ═══════════════════ CLI ═══════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Migration sécurisée des SKUs Luxura",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  python sku_migration_safe.py --dry-run              Prévisualiser tous les changements
  python sku_migration_safe.py --category halo        Migrer seulement les Halo
  python sku_migration_safe.py --category genius      Migrer seulement les Genius
  python sku_migration_safe.py --all                  Migrer TOUS les produits
        """
    )
    
    parser.add_argument('--dry-run', action='store_true', 
                        help='Prévisualiser sans appliquer')
    parser.add_argument('--category', type=str, choices=['genius', 'halo', 'tape', 'i-tip', 'essentiels'],
                        help='Filtrer par catégorie')
    parser.add_argument('--all', action='store_true',
                        help='Migrer tous les produits (ATTENTION)')
    parser.add_argument('--delay', type=float, default=0.5,
                        help='Délai entre requêtes (défaut: 0.5s)')
    
    args = parser.parse_args()
    
    # Update delay
    global DELAY_BETWEEN_REQUESTS
    DELAY_BETWEEN_REQUESTS = args.delay
    
    # Determine mode
    if args.dry_run:
        dry_run = True
    elif args.all or args.category:
        dry_run = False
    else:
        # Default to dry run
        dry_run = True
        print("⚠️  Mode prévisualisation par défaut. Utilisez --all ou --category pour migrer.\n")
    
    # Run migration
    stats = migrate_products(
        category_filter=args.category,
        dry_run=dry_run
    )
    
    return 0 if stats and stats.get("errors", 0) == 0 else 1


if __name__ == "__main__":
    exit(main())
