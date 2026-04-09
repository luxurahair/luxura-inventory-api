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
    - GÈRE les conflits de SKU (si le SKU existe déjà sur un autre produit)
    """
    clean_data = dict(data)

    if "options" in clean_data:
        clean_data["options"] = _safe_options(clean_data["options"])

    clean_data.pop("_track_quantity", None)
    clean_data.pop("_quantity", None)

    incoming_sku = (clean_data.get("sku") or "").strip() or None
    wix_id = (clean_data.get("wix_id") or "").strip() or None

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
    # GESTION DES CONFLITS SKU - AVANT d'appliquer les modifications
    # ============================================================
    final_sku = incoming_sku
    
    if incoming_sku:
        with db.no_autoflush:
            stmt = select(Product).where(Product.sku == incoming_sku)
            sku_owner = db.exec(stmt).first()
            
            # Le SKU appartient à un AUTRE produit?
            if sku_owner:
                is_same_product = existing and sku_owner.id == existing.id
                
                if not is_same_product:
                    # CAS 1: L'autre produit a le même wix_id → doublon à supprimer
                    if wix_id and sku_owner.wix_id == wix_id:
                        try:
                            print(f"[SYNC] 🔄 Fusion doublon: SKU={incoming_sku} sur ID={sku_owner.id} sera supprimé, update vers ID={existing.id if existing else 'NEW'}")
                            db.delete(sku_owner)
                            db.flush()
                            # Vérifier que la suppression a réellement fonctionné
                            with db.no_autoflush:
                                stmt_verify = select(Product).where(Product.sku == incoming_sku)
                                if not db.exec(stmt_verify).first():
                                    final_sku = incoming_sku
                                    print(f"[SYNC] ✅ Doublon supprimé, SKU {incoming_sku} disponible")
                                else:
                                    raise Exception("SKU existe toujours après suppression")
                        except Exception as e:
                            print(f"[SYNC] ⚠️ Échec suppression doublon: {e}")
                            # Fallback: résolution de conflit comme CAS 2
                            if existing and existing.sku:
                                final_sku = existing.sku
                                print(f"[SYNC] → Fallback: on garde SKU actuel {existing.sku}")
                            else:
                                product_id = existing.id if existing else "NEW"
                                final_sku = f"{incoming_sku}-ID{product_id}"
                                print(f"[SYNC] → Fallback: nouveau SKU {final_sku}")
                    
                    # CAS 2: Conflit réel - le SKU appartient à un produit différent (wix_id différent)
                    else:
                        if existing and existing.sku:
                            # Garder l'ancien SKU du produit existant
                            print(f"[SYNC] ⚠️ Conflit SKU: {incoming_sku} appartient à ID={sku_owner.id} (wix_id={sku_owner.wix_id})")
                            print(f"[SYNC] → On garde le SKU actuel: {existing.sku} pour ID={existing.id}")
                            final_sku = existing.sku
                        else:
                            # Générer un SKU unique basé sur l'ID du produit
                            product_id = existing.id if existing else "NEW"
                            new_sku = f"{incoming_sku}-ID{product_id}"
                            
                            # Vérifier que ce nouveau SKU n'existe pas non plus
                            counter = 1
                            while True:
                                with db.no_autoflush:
                                    stmt = select(Product).where(Product.sku == new_sku)
                                    if not db.exec(stmt).first():
                                        break
                                new_sku = f"{incoming_sku}-ID{product_id}-{counter}"
                                counter += 1
                            
                            print(f"[SYNC] ⚠️ Conflit SKU: {incoming_sku} appartient à ID={sku_owner.id}")
                            print(f"[SYNC] → Nouveau SKU généré: {new_sku}")
                            final_sku = new_sku
    
    # Appliquer le SKU final (résolu)
    clean_data["sku"] = final_sku

    # ============================================================
    # UPDATE ou INSERT
    # ============================================================
    if existing:
        print(f"[SYNC] UPDATE ID={existing.id}: SKU {existing.sku} → {final_sku}, wix_id={wix_id}")
        for field, value in clean_data.items():
            setattr(existing, field, value)
        return existing

    print(f"[SYNC] INSERT nouveau produit: SKU={final_sku}, wix_id={wix_id}")
    prod = Product(**clean_data)
    db.add(prod)
    return prod


def main() -> None:
    client = WixClient()
    version, raw_products = client.query_products(limit=100)

    synced_parents = 0
    synced_variants = 0
    skipped_variants = 0
    processed_since_commit = 0

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

        if processed_since_commit > 0:
            db.commit()

    print(
        f"[SYNC] Version catalogue: {version} | "
        f"Parents synchronisés: {synced_parents} | "
        f"Variantes synchronisées: {synced_variants} | "
        f"Variantes ignorées: {skipped_variants}"
    )


if __name__ == "__main__":
    main()
