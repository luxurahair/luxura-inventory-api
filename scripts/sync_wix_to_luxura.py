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

    sku = (clean_data.get("sku") or "").strip() or None
    wix_id = (clean_data.get("wix_id") or "").strip() or None

    # PRIORITÉ 1: Si on a déjà trouvé un produit existant (par wix_id), on l'utilise
    # Ne PAS re-chercher par SKU car cela causerait des conflits!
    
    # PRIORITÉ 2: Chercher par wix_id si pas déjà trouvé
    if not existing and wix_id:
        with db.no_autoflush:
            stmt = select(Product).where(Product.wix_id == wix_id)
            existing = db.exec(stmt).first()
            if existing:
                print(f"[SYNC] Trouvé par wix_id: ID={existing.id}, SKU actuel={existing.sku}")

    # PRIORITÉ 3: Chercher par SKU si toujours pas trouvé
    if not existing and sku:
        with db.no_autoflush:
            stmt = select(Product).where(Product.sku == sku)
            existing = db.exec(stmt).first()
            if existing:
                print(f"[SYNC] Trouvé par SKU: ID={existing.id}")

    # Vérifier si le SKU qu'on veut assigner existe déjà sur UN AUTRE produit
    if sku:
        with db.no_autoflush:
            stmt = select(Product).where(Product.sku == sku)
            sku_owner = db.exec(stmt).first()
            
            # Si le SKU appartient à un autre produit (pas celui qu'on update)
            if sku_owner and existing and sku_owner.id != existing.id:
                # L'autre produit a le même wix_id → fusionner (supprimer le doublon)
                if wix_id and sku_owner.wix_id == wix_id:
                    print(f"[SYNC] Fusion: SKU={sku} existe sur ID={sku_owner.id}, update ID={existing.id}")
                    db.delete(sku_owner)
                    db.flush()
                # Conflit réel → garder l'ancien SKU sur notre produit
                else:
                    print(f"[SYNC] ⚠️ Conflit SKU: {sku} appartient à ID={sku_owner.id}, on garde SKU actuel pour ID={existing.id}")
                    # Ne pas changer le SKU - garder l'ancien
                    if existing.sku:
                        clean_data["sku"] = existing.sku
                    else:
                        # Générer un SKU unique
                        counter = 1
                        while True:
                            new_sku = f"{sku}-{existing.id}"
                            with db.no_autoflush:
                                stmt = select(Product).where(Product.sku == new_sku)
                                if not db.exec(stmt).first():
                                    break
                            counter += 1
                        print(f"[SYNC] Nouveau SKU généré: {new_sku}")
                        clean_data["sku"] = new_sku
            
            # Si on insère un nouveau produit et le SKU existe déjà
            elif sku_owner and not existing:
                # Générer un SKU unique pour le nouveau produit
                counter = 1
                original_sku = sku
                while True:
                    new_sku = f"{original_sku}-NEW{counter}"
                    with db.no_autoflush:
                        stmt = select(Product).where(Product.sku == new_sku)
                        if not db.exec(stmt).first():
                            break
                    counter += 1
                print(f"[SYNC] Nouveau produit, SKU conflit: {original_sku} → {new_sku}")
                clean_data["sku"] = new_sku

    if existing:
        for field, value in clean_data.items():
            setattr(existing, field, value)
        return existing

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
