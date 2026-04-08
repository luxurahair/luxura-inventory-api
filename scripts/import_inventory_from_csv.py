import csv
from pathlib import Path
from typing import Dict, Any

from sqlmodel import Session, select

from app.db.session import engine
from app.models import Product, InventoryItem, Salon


CSV_PATH = Path("catalog_products.csv")
ENTREPOT_CODE = "ENTREPOT"
ENTREPOT_NAME = "Luxura Entrepôt"


def get_or_create_entrepot(db: Session) -> Salon:
    salon = db.exec(select(Salon).where(Salon.code == ENTREPOT_CODE)).first()
    if not salon:
        salon = Salon(name=ENTREPOT_NAME, code=ENTREPOT_CODE, is_active=True)
        db.add(salon)
        db.commit()
        db.refresh(salon)
    return salon


def main():
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"CSV introuvable: {CSV_PATH.resolve()}")

    with Session(engine) as db:
        entrepot = get_or_create_entrepot(db)

        products_by_handle: Dict[str, Dict[str, Any]] = {}

        imported = 0
        skipped_no_sku = 0

        with CSV_PATH.open(encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for row in reader:
                field_type = row.get("fieldType")
                handle_id = row.get("handleId")

                # 1️⃣ Ligne PRODUCT → métadonnées
                if field_type == "Product":
                    products_by_handle[handle_id] = {
                        "name": row.get("name") or "",
                        "description": row.get("description") or "",
                        "option_name_1": row.get("productOptionName1"),
                    }

                # 2️⃣ Ligne VARIANT → SKU + inventaire
                elif field_type == "Variant":
                    sku = (row.get("sku") or "").strip()
                    if not sku:
                        skipped_no_sku += 1
                        continue

                    parent = products_by_handle.get(handle_id, {})
                    option_name = parent.get("option_name_1")
                    option_value = row.get("optionValue1")

                    options = {}
                    if option_name and option_value:
                        options[option_name] = option_value

                    name = parent.get("name", sku)
                    if option_value:
                        name = f"{name} — {option_value}"

                    qty = int(row.get("inventory.quantity") or 0)

                    # UPSERT PRODUCT par SKU
                    product = db.exec(select(Product).where(Product.sku == sku)).first()
                    if not product:
                        product = Product(
                            sku=sku,
                            name=name,
                            description=parent.get("description") or "",
                            options=options,
                        )
                        db.add(product)
                        db.commit()
                        db.refresh(product)
                    else:
                        product.name = name
                        product.options = options
                        db.commit()

                    # UPSERT INVENTORY (ENTREPOT SEULEMENT)
                    inv = db.exec(
                        select(InventoryItem).where(
                            InventoryItem.salon_id == entrepot.id,
                            InventoryItem.product_id == product.id,
                        )
                    ).first()

                    if not inv:
                        inv = InventoryItem(
                            salon_id=entrepot.id,
                            product_id=product.id,
                            quantity=qty,
                        )
                        db.add(inv)
                    else:
                        inv.quantity = qty

                    db.commit()
                    imported += 1

        print(
            f"[IMPORT CSV] Variants importés: {imported} | "
            f"Variants sans SKU ignorés: {skipped_no_sku}"
        )


if __name__ == "__main__":
    main()
