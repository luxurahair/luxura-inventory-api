#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════
LUXURA - MIGRATION SKU ULTRA-ROBUSTE
═══════════════════════════════════════════════════════════════════════════
Version avec délais longs et sauvegarde de progression pour l'API Render lente.

Usage:
    python sku_migration_robust.py --category halo        # Migrer Halo
    python sku_migration_robust.py --all                  # Migrer tout
    python sku_migration_robust.py --resume               # Reprendre là où on s'est arrêté
═══════════════════════════════════════════════════════════════════════════
"""

import requests
import time
import argparse
import json
import re
import os
from datetime import datetime
from color_system import get_color_info

# ═══════════════════ CONFIGURATION ═══════════════════

LUXURA_API_URL = "https://luxura-inventory-api.onrender.com"
DELAY_BETWEEN_REQUESTS = 3.0  # 3 secondes entre chaque requête (API Render lente)
TIMEOUT = 60  # Timeout long
MAX_RETRIES = 5
PROGRESS_FILE = "/tmp/luxura_migration_progress.json"

# Categories autorisées
ALLOWED_CATEGORIES = {'genius', 'tape', 'i-tip', 'halo', 'essentiels'}

# Mots-clés exclus
EXCLUDED_KEYWORDS = ['clips', 'ponytail', 'queue de cheval', 'test']


# ═══════════════════ HELPERS ═══════════════════

def log(msg, level="INFO"):
    """Log avec timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    prefix = {"INFO": "✓", "WARN": "⚠", "ERROR": "✗", "SUCCESS": "✅", "SKIP": "⏭"}.get(level, "•")
    print(f"[{timestamp}] {prefix} {msg}")


def save_progress(completed_ids, category):
    """Sauvegarder la progression"""
    data = {
        "timestamp": datetime.now().isoformat(),
        "category": category,
        "completed_ids": list(completed_ids)
    }
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(data, f)


def load_progress():
    """Charger la progression précédente"""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return None


def detect_category_from_handle(handle: str, name: str) -> str:
    """Détecter la catégorie du produit"""
    if not handle:
        handle = ""
    handle_lower = handle.lower()
    name_lower = name.lower()
    
    for excluded in EXCLUDED_KEYWORDS:
        if excluded in handle_lower or excluded in name_lower:
            return None
    
    if 'genius' in handle_lower or 'vivian' in handle_lower or 'trame-invisible' in handle_lower:
        return 'genius'
    elif 'halo' in handle_lower or ('everly' in handle_lower and 'clips' not in handle_lower):
        return 'halo'
    elif 'bande' in handle_lower or 'aurora' in handle_lower or 'tape' in handle_lower or 'adhésive' in handle_lower:
        return 'tape'
    elif 'i-tip' in handle_lower or 'itip' in handle_lower or 'eleanor' in handle_lower:
        return 'i-tip'
    
    essentials_keywords = ['spray', 'brosse', 'fer', 'shampooing', 'lotion', 'anneau', 'ensemble', 
                          'duo', 'kit', 'accessoire', 'outil', 'colle', 'remover', 'peigne', 
                          'tenue ultra', 'installation']
    for keyword in essentials_keywords:
        if keyword in name_lower or keyword in handle_lower:
            return 'essentiels'
    
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
    
    length = ''
    weight = ''
    variant_match = re.search(r'(\d+)["\'\′]?\s*(\d+)\s*gram', name.lower())
    if variant_match:
        length = variant_match.group(1)
        weight = variant_match.group(2)
    
    color_code = extract_color_code(name)
    color_info = get_color_info(color_code)
    sku_name = color_info.get("sku", color_code.replace("/", "-"))
    clean_code = color_code.replace('/', '-')
    
    if length and weight:
        sku = f'{prefix}{length}{weight}-{clean_code}-{sku_name}'
    else:
        sku = f'{prefix}-{clean_code}-{sku_name}'
    
    return sku.upper()


# ═══════════════════ API FUNCTIONS ═══════════════════

def fetch_all_products():
    """Récupérer tous les produits avec retries"""
    log("Récupération des produits depuis l'API Render...")
    
    for attempt in range(MAX_RETRIES):
        try:
            log(f"  Tentative {attempt+1}/{MAX_RETRIES}...")
            time.sleep(2)  # Attente avant la requête
            response = requests.get(f"{LUXURA_API_URL}/products", timeout=90)
            response.raise_for_status()
            products = response.json()
            log(f"Récupéré {len(products)} produits", "SUCCESS")
            return products
        except Exception as e:
            log(f"  Erreur: {e}", "WARN")
            time.sleep(10)  # Attente longue avant retry
    
    return []


def update_product_sku(product_id: int, new_sku: str) -> bool:
    """Mettre à jour le SKU avec retries et délais longs"""
    for attempt in range(MAX_RETRIES):
        try:
            # Attente AVANT la requête (important pour Render)
            time.sleep(DELAY_BETWEEN_REQUESTS)
            
            response = requests.put(
                f"{LUXURA_API_URL}/products/{product_id}",
                json={"sku": new_sku},
                timeout=TIMEOUT
            )
            
            if response.status_code == 200:
                return True
            elif response.status_code == 500:
                log(f"    Erreur 500 - attente avant retry {attempt+1}/{MAX_RETRIES}", "WARN")
                time.sleep(5)  # Attente plus longue après 500
            else:
                log(f"    HTTP {response.status_code} - retry {attempt+1}/{MAX_RETRIES}", "WARN")
                time.sleep(3)
                
        except requests.exceptions.Timeout:
            log(f"    Timeout - retry {attempt+1}/{MAX_RETRIES}", "WARN")
            time.sleep(5)
        except Exception as e:
            log(f"    Erreur: {e}", "WARN")
            time.sleep(3)
    
    return False


# ═══════════════════ MAIN MIGRATION ═══════════════════

def migrate_products(category_filter=None, resume=False):
    """Migration avec sauvegarde de progression"""
    
    # Charger progression précédente si resume
    completed_ids = set()
    if resume:
        progress = load_progress()
        if progress:
            completed_ids = set(progress.get("completed_ids", []))
            prev_category = progress.get("category")
            log(f"Reprise depuis sauvegarde: {len(completed_ids)} produits déjà migrés (catégorie: {prev_category})", "INFO")
            if prev_category and not category_filter:
                category_filter = prev_category
    
    products = fetch_all_products()
    if not products:
        log("Aucun produit trouvé", "ERROR")
        return
    
    # Stats
    stats = {"total": len(products), "filtered": 0, "to_update": 0, "updated": 0, "skipped": 0, "errors": 0, "already_done": 0}
    
    # Préparer les produits à migrer
    to_migrate = []
    
    for p in products:
        name = p.get('name') or ''
        handle = p.get('handle') or ''
        product_id = p.get('id')
        
        if 'test' in name.lower() and p.get('price', 0) < 1:
            continue
        
        category = detect_category_from_handle(handle, name)
        if category is None or category not in ALLOWED_CATEGORIES:
            continue
        
        if category_filter and category != category_filter:
            continue
        
        stats["filtered"] += 1
        
        # Skip si déjà fait
        if product_id in completed_ids:
            stats["already_done"] += 1
            continue
        
        old_sku = p.get('sku') or ''
        new_sku = generate_standardized_sku(p)
        
        if old_sku == new_sku:
            stats["skipped"] += 1
            completed_ids.add(product_id)
            continue
        
        to_migrate.append({
            "id": product_id,
            "name": name[:50],
            "old_sku": old_sku or "(aucun)",
            "new_sku": new_sku,
            "category": category
        })
    
    stats["to_update"] = len(to_migrate)
    
    # Afficher résumé
    print("\n" + "═" * 60)
    print("LUXURA - MIGRATION SKU ROBUSTE")
    print("═" * 60)
    print(f"Catégorie: {category_filter or 'TOUTES'}")
    print(f"Total produits API: {stats['total']}")
    print(f"Produits filtrés: {stats['filtered']}")
    print(f"Déjà migrés (reprise): {stats['already_done']}")
    print(f"Déjà corrects: {stats['skipped']}")
    print(f"À mettre à jour: {stats['to_update']}")
    print(f"Délai entre requêtes: {DELAY_BETWEEN_REQUESTS}s")
    print(f"Temps estimé: ~{len(to_migrate) * DELAY_BETWEEN_REQUESTS / 60:.1f} minutes")
    print("═" * 60 + "\n")
    
    if not to_migrate:
        log("Aucun produit à migrer!", "SUCCESS")
        return stats
    
    # Migration
    print("MIGRATION EN COURS...")
    print("-" * 60)
    
    for i, item in enumerate(to_migrate, 1):
        print(f"\n[{i}/{len(to_migrate)}] {item['name']}")
        print(f"    {item['old_sku']} → {item['new_sku']}")
        
        success = update_product_sku(item['id'], item['new_sku'])
        
        if success:
            log("OK", "SUCCESS")
            stats["updated"] += 1
            completed_ids.add(item['id'])
        else:
            log("ÉCHEC", "ERROR")
            stats["errors"] += 1
        
        # Sauvegarder progression tous les 5 produits
        if i % 5 == 0:
            save_progress(completed_ids, category_filter)
            log(f"Progression sauvegardée ({len(completed_ids)} produits)")
    
    # Sauvegarder progression finale
    save_progress(completed_ids, category_filter)
    
    # Rapport final
    print("\n" + "═" * 60)
    print("RAPPORT FINAL")
    print("═" * 60)
    print(f"✅ Mis à jour: {stats['updated']}")
    print(f"⏭️  Déjà corrects: {stats['skipped']}")
    print(f"🔄 Reprise: {stats['already_done']}")
    print(f"❌ Erreurs: {stats['errors']}")
    print("═" * 60)
    
    if stats['errors'] > 0:
        print(f"\n💡 Relancez avec --resume pour retenter les échecs")
    
    return stats


# ═══════════════════ CLI ═══════════════════

def main():
    parser = argparse.ArgumentParser(description="Migration robuste des SKUs Luxura")
    parser.add_argument('--category', type=str, choices=['genius', 'halo', 'tape', 'i-tip', 'essentiels'])
    parser.add_argument('--all', action='store_true', help='Migrer tous les produits')
    parser.add_argument('--resume', action='store_true', help='Reprendre la migration interrompue')
    parser.add_argument('--delay', type=float, default=3.0, help='Délai entre requêtes (défaut: 3s)')
    
    args = parser.parse_args()
    
    global DELAY_BETWEEN_REQUESTS
    DELAY_BETWEEN_REQUESTS = args.delay
    
    if not args.category and not args.all and not args.resume:
        parser.print_help()
        print("\n⚠️  Spécifiez --category, --all ou --resume")
        return 1
    
    stats = migrate_products(
        category_filter=args.category,
        resume=args.resume
    )
    
    return 0 if stats and stats.get("errors", 0) == 0 else 1


if __name__ == "__main__":
    exit(main())
