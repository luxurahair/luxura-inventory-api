import os
import sys
from typing import Any, Dict, Optional

# Permet d'importer "app.*" quand on lance ce script directement
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sqlmodel import Session, select  # type: ignore

from app.db.session import engine
from app.models.product import Product
from app.services.wix_client import WixClient
from app.services.catalog_normalizer import normalize_product, normalize_variant


BATCH_SIZE = 25

# Track des SKUs utilisés dans le batch courant (pas encore commités)
_batch_skus: set = set()


def _is_variant_record(prod: Product) -> bool:
    opts = prod.options if isinstance(prod.options, dict) else {}
    return bool(opts.get("wix_variant_id"))


def _safe_options(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _find_existing_parent(db: Session, wix_id: Optional[str], sku: Optional[str]) -> Optional[Product]:
    """
    Trouve un produit parent existant :
    1. par wix_id
    2. sinon par SKU
    """
    if wix_id:
        with db.no_autoflush:
            stmt = select(Product).where(Product.wix_id == wix_id)
            row = db.exec(stmt).first()
            if row and not _is_variant_record(row):
                return row

    if sku:
        with db.no_autoflush:
            stmt = select(Product).where(Product.sku == sku)
            row = db.exec(stmt).first()
            if row and not _is_variant_record(row):
                return row

    return None


def _find_existing_variant(
    db: Session,
    sku: Optional[str],
    wix_variant_id: Optional[str],
) -> Optional[Product]:
    if sku:
        with db.no_autoflush:
            stmt = select(Product).where(Product.sku == sku)
            found = db.exec(stmt).first()
            if found:
                return found

    if wix_variant_id:
        with db.no_autoflush:
            stmt = select(Product)
            rows = db.exec(stmt).all()

        for row in rows:
            opts = row.options if isinstance(row.options, dict) else {}
            if opts.get("wix_variant_id") == wix_variant_id:
                return row

    return None


def _upsert_product(db: Session, existing: Optional[Product], data: Dict[str, Any]) -> Product:
    """
    Upsert safe :
    - update si trouvé par wix_id (priorité)
    - sinon cherche par SKU
    - sinon insert
    - GÈRE les conflits de SKU (DB + batch en mémoire)
    """
    global _batch_skus
    
    clean_data = dict(data)

    if "options" in clean_data:
        clean_data["options"] = _safe_options(clean_data["options"])

    clean_data.pop("_track_quantity", None)
    clean_data.pop("_quantity", None)

    incoming_sku = (clean_data.get("sku") or "").strip() or None
    wix_id = (clean_data.get("wix_id") or "").strip() or None
    
    # Extraire le wix_variant_id pour les variantes
    options = _safe_options(clean_data.get("options"))
    wix_variant_id = options.get("wix_variant_id")

    # PRIORITÉ 1: Chercher par wix_id (le plus fiable)
    if not existing and wix_id:
        with db.no_autoflush:
            stmt = select(Product).where(Product.wix_id == wix_id)
            existing = db.exec(stmt).first()
            if existing:
                print(f"[SYNC] Trouvé par wix_id: ID={existing.id}, SKU actuel={existing.sku}, wix_id={wix_id}")

    # PRIORITÉ 2: Chercher par SKU si toujours pas trouvé
    if not existing and incoming_sku:
        with db.no_autoflush:
            stmt = select(Product).where(Product.sku == incoming_sku)
            existing = db.exec(stmt).first()
            if existing:
                print(f"[SYNC] Trouvé par SKU: ID={existing.id}, SKU={incoming_sku}")

    # ============================================================
    # GESTION DES CONFLITS SKU - DB + BATCH EN MÉMOIRE
    # ============================================================
    final_sku = incoming_sku
    
    if incoming_sku:
        # VÉRIFICATION 1: SKU déjà utilisé dans le batch courant (non commité)
        if incoming_sku in _batch_skus:
            # Générer un SKU unique pour cette variante
            if wix_variant_id:
                # Pour les variantes, utiliser le variant_id pour rendre unique
                variant_suffix = wix_variant_id[:8] if len(wix_variant_id) > 8 else wix_variant_id
                final_sku = f"{incoming_sku}-V{variant_suffix}"
            else:
                # Pour les autres cas, ajouter un compteur
                counter = 1
                while f"{incoming_sku}-{counter}" in _batch_skus:
                    counter += 1
                final_sku = f"{incoming_sku}-{counter}"
            
            print(f"[SYNC] ⚠️ SKU {incoming_sku} déjà dans batch → {final_sku}")
        else:
            # VÉRIFICATION 2: SKU existe en DB?
            with db.no_autoflush:
                stmt = select(Product).where(Product.sku == incoming_sku)
                sku_owner = db.exec(stmt).first()
                
                if sku_owner:
                    is_same_product = existing and sku_owner.id == existing.id
                    
                    if not is_same_product:
                        # CAS 1: Même wix_id → doublon
                        if wix_id and sku_owner.wix_id == wix_id:
                            try:
                                print(f"[SYNC] 🔄 Fusion doublon: SKU={incoming_sku}")
                                db.delete(sku_owner)
                                db.flush()
                                final_sku = incoming_sku
                                print(f"[SYNC] ✅ Doublon supprimé")
                            except Exception as e:
                                print(f"[SYNC] ⚠️ Échec fusion: {e}")
                                if wix_variant_id:
                                    final_sku = f"{incoming_sku}-V{wix_variant_id[:8]}"
                                else:
                                    final_sku = f"{incoming_sku}-NEW"
                        
                        # CAS 2: Conflit réel
                        else:
                            if existing and existing.sku and existing.sku not in _batch_skus:
                                final_sku = existing.sku
                                print(f"[SYNC] ⚠️ Conflit → garde SKU existant: {final_sku}")
                            elif wix_variant_id:
                                final_sku = f"{incoming_sku}-V{wix_variant_id[:8]}"
                                print(f"[SYNC] ⚠️ Conflit → nouveau SKU variante: {final_sku}")
                            else:
                                counter = 1
                                final_sku = f"{incoming_sku}-{counter}"
                                while final_sku in _batch_skus:
                                    counter += 1
                                    final_sku = f"{incoming_sku}-{counter}"
                                print(f"[SYNC] ⚠️ Conflit → nouveau SKU: {final_sku}")
    
    # Enregistrer le SKU dans le batch
    if final_sku:
        _batch_skus.add(final_sku)
    
    # Appliquer le SKU final
    clean_data["sku"] = final_sku

    # ============================================================
    # UPDATE ou INSERT
    # ============================================================
    if existing:
        print(f"[SYNC] UPDATE ID={existing.id}: SKU → {final_sku}")
        for field, value in clean_data.items():
            setattr(existing, field, value)
        return existing

    print(f"[SYNC] INSERT: SKU={final_sku}, wix_id={wix_id}")
    prod = Product(**clean_data)
    db.add(prod)
    return prod


def main() -> None:
    global _batch_skus
    
    client = WixClient()
    version, raw_products = client.query_products(limit=100)

    synced_parents = 0
    synced_variants = 0
    skipped_variants = 0
    processed_since_commit = 0
    
    # Reset le tracking des SKUs au début
    _batch_skus = set()

    with Session(engine) as db:
        for wp in raw_products:
            parent_data = normalize_product(wp, version)
            parent_wix_id = parent_data.get("wix_id")
            parent_sku = parent_data.get("sku")

            if not parent_wix_id and not parent_sku:
                continue

            with db.no_autoflush:
                existing_parent = _find_existing_parent(
                    db,
                    str(parent_wix_id).strip() if parent_wix_id else None,
                    str(parent_sku).strip() if parent_sku else None,
                )

            _upsert_product(db, existing_parent, parent_data)
            synced_parents += 1
            processed_since_commit += 1

            try:
                variants = (
                    client.query_variants_v1(
                        product_id=str(parent_wix_id),
                        limit=100,
                    )
                    if parent_wix_id
                    else []
                )
            except Exception as e:
                print(f"[WARN] Impossible de récupérer les variantes pour {parent_wix_id}: {e}")
                variants = []

            for variant in variants:
                variant_data = normalize_variant(wp, variant)
                if not variant_data:
                    skipped_variants += 1
                    continue

                variant_options = _safe_options(variant_data.get("options"))
                wix_variant_id = variant_options.get("wix_variant_id")
                sku = variant_data.get("sku")

                with db.no_autoflush:
                    existing_variant = _find_existing_variant(
                        db=db,
                        sku=str(sku).strip() if sku else None,
                        wix_variant_id=str(wix_variant_id).strip() if wix_variant_id else None,
                    )

                _upsert_product(db, existing_variant, variant_data)
                synced_variants += 1
                processed_since_commit += 1

                if processed_since_commit >= BATCH_SIZE:
                    db.commit()
                    processed_since_commit = 0
                    # Reset le tracking après commit (les SKUs sont maintenant en DB)
                    _batch_skus = set()

        if processed_since_commit > 0:
            db.commit()
            _batch_skus = set()

    print(
        f"[SYNC] Version catalogue: {version} | "
        f"Parents synchronisés: {synced_parents} | "
        f"Variantes synchronisées: {synced_variants} | "
        f"Variantes ignorées: {skipped_variants}"
    )


if __name__ == "__main__":
    main()
