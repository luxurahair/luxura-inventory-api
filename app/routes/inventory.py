# app/routes/inventory.py

import json
from typing import Any, Dict, List, Optional
from io import BytesIO
from datetime import datetime

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from sqlmodel import Session, select

from app.db import get_session
from app.models.inventory import InventoryItem, InventoryRead
from app.models.product import Product
from app.models.salon import Salon

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.get(
    "",
    response_model=List[InventoryRead],
    summary="Lister l’inventaire par salon & produit",
)
def list_inventory(
    salon_id: Optional[int] = None,
    product_id: Optional[int] = None,
    session: Session = Depends(get_session),
) -> List[InventoryRead]:
    """
    Retourne l’inventaire.

    - Sans paramètre : tous les enregistrements
    - Avec salon_id : filtre par salon
    - Avec product_id : filtre par produit
    """
    stmt = select(InventoryItem)
    if salon_id is not None:
        stmt = stmt.where(InventoryItem.salon_id == salon_id)
    if product_id is not None:
        stmt = stmt.where(InventoryItem.product_id == product_id)

    return session.exec(stmt).all()


@router.get(
    "/view",
    summary="Vue lisible de l’inventaire (JOIN Product)",
)
def inventory_view(
    salon_id: Optional[int] = None,
    product_id: Optional[int] = None,
    session: Session = Depends(get_session),
) -> List[Dict[str, Any]]:
    """
    Vue lisible de l’inventaire (JOIN InventoryItem -> Product)
    Retourne: sku + name + quantity + options + price (si dispo).
    """
    stmt = select(InventoryItem, Product).join(Product, Product.id == InventoryItem.product_id)

    if salon_id is not None:
        stmt = stmt.where(InventoryItem.salon_id == salon_id)
    if product_id is not None:
        stmt = stmt.where(InventoryItem.product_id == product_id)

    rows = session.exec(stmt).all()

    out: List[Dict[str, Any]] = []
    for inv, prod in rows:
        out.append(
            {
                "inventory_id": inv.id,
                "salon_id": inv.salon_id,
                "product_id": inv.product_id,
                "quantity": inv.quantity,
                "sku": prod.sku,
                "name": prod.name,
                "price": getattr(prod, "price", None),
                "options": getattr(prod, "options", None),
                "wix_id": getattr(prod, "wix_id", None),
                "is_active": getattr(prod, "active", None),
            }
        )

    return out


def _autosize(ws) -> None:
    for col in ws.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            try:
                v = "" if cell.value is None else str(cell.value)
                max_len = max(max_len, len(v))
            except Exception:
                pass
        ws.column_dimensions[col_letter].width = min(max(10, max_len + 2), 60)


@router.get(
    "/export.xlsx",
    summary="Exporter l’inventaire Excel (1 feuille par salon)",
)
def export_inventory_xlsx(
    salon_id: Optional[int] = None,
    include_zero: bool = False,
    session: Session = Depends(get_session),
):
    """
    Exporte un fichier Excel:
    - Sans salon_id: 1 feuille par salon actif
    - Avec salon_id: seulement ce salon
    Colonnes: salon / sku / name / qty / price / value / wix_id / wix_variant_id / choices / vendor_sku
    """
    salons_stmt = select(Salon).where(Salon.is_active == True)  # noqa: E712
    if salon_id is not None:
        salons_stmt = select(Salon).where(Salon.id == salon_id)
    salons = session.exec(salons_stmt).all()

    wb = Workbook()
    wb.remove(wb.active)

    headers = [
        "salon_id",
        "salon",
        "sku",
        "name",
        "quantity",
        "price",
        "value",
        "wix_id",
        "wix_variant_id",
        "choices",
        "vendor_sku",
    ]

    summary: Dict[str, Dict[str, Any]] = {}

    for s in salons:
        title = (s.name or f"Salon {s.id}")[:31]
        ws = wb.create_sheet(title=title)
        ws.append(headers)

        stmt = (
            select(InventoryItem, Product)
            .join(Product, Product.id == InventoryItem.product_id)
            .where(InventoryItem.salon_id == s.id)
        )
        rows = session.exec(stmt).all()

        for inv, prod in rows:
            qty = int(inv.quantity or 0)
            if (not include_zero) and qty == 0:
                continue

            price = float(getattr(prod, "price", 0) or 0)
            value = qty * price

            opts = getattr(prod, "options", None) or {}
            wix_variant_id_val = None
            choices = None
            vendor_sku = None
            if isinstance(opts, dict):
                wix_variant_id_val = opts.get("wix_variant_id")
                choices = opts.get("choices")
                vendor_sku = opts.get("vendor_sku")

            # ✅ Excel n'accepte pas dict/list -> stringify
            if choices is None:
                choices_str = ""
            else:
                try:
                    choices_str = json.dumps(choices, ensure_ascii=False)
                except Exception:
                    choices_str = str(choices)

            vendor_sku_str = "" if vendor_sku is None else str(vendor_sku)
            wix_variant_id_str = "" if wix_variant_id_val is None else str(wix_variant_id_val)
            wix_id_str = "" if getattr(prod, "wix_id", None) is None else str(getattr(prod, "wix_id", None))

            ws.append(
                [
                    s.id,
                    s.name,
                    prod.sku,
                    prod.name,
                    qty,
                    price,
                    value,
                    wix_id_str,
                    wix_variant_id_str,
                    choices_str,
                    vendor_sku_str,
                ]
            )

            sku_key = prod.sku or ""
            if sku_key:
                agg = summary.get(sku_key) or {
                    "sku": sku_key,
                    "name": prod.name,
                    "qty": 0,
                    "price": price,
                    "value": 0.0,
                }
                agg["qty"] += qty
                agg["value"] += value
                if prod.name:
                    agg["name"] = prod.name
                agg["price"] = price
                summary[sku_key] = agg

        _autosize(ws)

    ws_sum = wb.create_sheet(title="Summary")
    ws_sum.append(["sku", "name", "total_qty", "price", "total_value"])
    for sku_key in sorted(summary.keys()):
        a = summary[sku_key]
        ws_sum.append([a["sku"], a["name"], a["qty"], a["price"], a["value"]])
    _autosize(ws_sum)

    bio = BytesIO()
    wb.save(bio)
    bio.seek(0)

    stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"luxura_inventory_{stamp}.xlsx"

    return StreamingResponse(
        bio,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
