# scripts/sync_wix_to_luxura.py

import os
import time
import json
from typing import List, Dict, Any

import requests
from sqlmodel import Session, select

from app.database import engine
from app.models import Product, Salon, InventoryItem  # adapte les imports au besoin


WIX_API_KEY = os.getenv("WIX_API_KEY")
WIX_ACCOUNT_ID = os.getenv("WIX_ACCOUNT_ID")
WIX_SITE_ID = os.getenv("WIX_SITE_ID")
LUXURA_SALON_ID = os.getenv("LUXURA_SALON_ID")  # id du salon "Luxura Online" dans ta table salons


def log(msg: str):
    """Petit helper pour avoir des logs propres."""
    print(msg, flush=True)


def check_env() -> bool:
    """Vérifie qu'on a tout ce qu'il faut pour parler à Wix."""
    ok = True

    if not WIX_API_KEY:
        log("❌ WIX_API_KEY manquant dans les variables d'environnement")
        ok = False

    if not WIX_ACCOUNT_ID:
        log("❌ WIX_ACCOUNT_ID manquant dans les variables d'environnement")
        ok = False

    if not WIX_SITE_ID:
        log("❌ WIX_SITE_ID manquant dans les variables d'environnement")
        ok = False

    if not LUXURA_SALON_ID:
        log("❌ LUXURA_SALON_ID manquant dans les variables d'environnement (id du salon 'Luxura Online')")
        ok = False

    return ok


def fetch_wix_products() -> List[Dict[str, Any]]:
    """
    Appelle l’API Wix Stores pour récupérer les produits.

    Retourne une liste de dict (les produits Wix bruts).
    En cas de problème, retourne [] et log l’erreur.
    """
    if not check_env():
        log("⛔ Variables d'environnement incomplètes. Sync annulée.")
        return []

    url = "https://www.wixapis.com/stores/v1/products/query"

    headers = {
        # Clé API (ton “Jeton” dans l’interface Wix)
        "Authorization": WIX_API_KEY,
        # Contexte compte + site → évite le fameux “No Metasite Context in identity”
        "wix-account-id": WIX_ACCOUNT_ID,
        "wix-site-id": WIX_SITE_ID,
        "Content-Type": "application/json",
    }

    # On peut filtrer sur les produits visibles / actifs
    payload = {
        "query": {
            "filter": {
                # adapte ici si tu veux autre chose qu’uniquement les produits visibles
                "visible": True
            }
        },
        "paging": {
            "limit": 200
        },
    }

    log("🔄 Téléchargement produits Wix…")

    try:
        res = requests.post(url, headers=headers, json=payload, timeout=30)
    except Exception as e:
        log(f"⚠️  Erreur réseau en appelant Wix : {e}")
        return []

    log(f"   → Status Wix: {res.status_code}")

    # On essaie de logguer la réponse brute (mais sans tout péter si ce n’est pas du JSON)
    try:
        data = res.json()
        pretty = json.dumps(data, ensure_ascii=False)[:2000]  # on coupe au cas où ce serait énorme
        log(f"   → Réponse brute Wix (tronquée): {pretty}")
    except Exception:
        log(f"   → Réponse texte Wix: {res.text[:2000]}")
        data = None

    if not res.ok:
        log("⚠️  Wix renvoie une erreur, sync annulée.")
        return []

    if not isinstance(data, dict):
        log("⚠️  Réponse Wix inattendue (pas un objet JSON).")
        return []

    products = data.get("products", [])
    if not products:
        log("⚠️  Aucun produit retourné par Wix.")
        return []

    log(f"✅ {len(products)} produits récupérés depuis Wix.")
    return products


def sync_wix_to_luxura():
    """
    Synchronise les produits Wix vers la base Luxura.
    Ici je te laisse ton mapping / logique d’insertion,
    tu peux adapter la partie “for p in products” suivant ton modèle Product.
    """
    start = time.time()
    log("[SYNC] Début synchronisation Wix -> Luxura")

    products = fetch_wix_products()
    if not products:
        log("[SYNC] Aucun produit Wix à synchroniser. Fin.")
        return

    with Session(engine) as session:
        # Assure-toi que LUXURA_SALON_ID existe vraiment côté DB
        salon_id = int(LUXURA_SALON_ID)

        for p in products:
            # Exemple de mapping — à adapter selon ta structure Wix exacte
            sku = p.get("sku") or p.get("productSku") or ""
            name = p.get("name", "")
            description = p.get("description", "")

            # Prix : ça dépend de comment Wix renvoie les données
            price = 0.0
            price_data = p.get("price") or {}
            if isinstance(price_data, dict):
                price = price_data.get("price") or price_data.get("amount") or 0.0

            # On essaie de trouver un produit existant avec le même SKU
            if sku:
                existing = session.exec(select(Product).where(Product.sku == sku)).first()
            else:
                existing = None

            if existing:
                # Mise à jour
                existing.name = name
                existing.description = description
                existing.price = price
                existing.active = True
            else:
                # Création
                prod = Product(
                    sku=sku,
                    name=name,
                    description=description,
                    price=price,
                    active=True,
                    # adapte si tu as length/color/category obligatoires
                    length="",
                    color="",
                    category="",
                )
                session.add(prod)
                session.flush()  # pour obtenir prod.id

                # Optionnel : créer une ligne d’inventaire à 0 pour Luxura Online
                inv = InventoryItem(
                    salon_id=salon_id,
                    product_id=prod.id,
                    quantity=0,
                )
                session.add(inv)

        session.commit()

    duration = round(time.time() - start, 1)
    log(f"[SYNC] Synchro Wix -> Luxura TERMINÉE ✅ (en {duration} s)")
