# app/routes/wix.py

from typing import Dict, Any, List

from fastapi import APIRouter, Depends, Request
from sqlmodel import Session, select

from app.db import get_session
from app.models import Product, Salon, InventoryItem

router = APIRouter()

# On sait que Luxura Online a l'id 3 dans ta base
LUXURA_ONLINE_SALON_ID = 3
LUXURA_ONLINE_SALON_NAME = "Luxura Online"


def get_luxura_online_salon(session: Session) -> Salon:
    """
    Récupère le salon 'Luxura Online' (id=3).
    Si pour une raison quelconque l'id ne matche plus,
    on le retrouve par le nom.
    """
    salon = session.get(Salon, LUXURA_ONLINE_SALON_ID)
    if salon:
        return salon

    salon = session.exec(
        select(Salon).where(Salon.name == LUXURA_ONLINE_SALON_NAME)
    ).first()

    if not salon:
        salon = Salon(name=LUXURA_ONLINE_SALON_NAME, address="Entrepôt central")
        session.add(salon)
        session.commit()
        session.refresh(salon)

    return salon


@router.post("/wix/order-webhook", summary="Webhook commande Wix")
async def wix_order_webhook(
    request: Request,
    session: Session = Depends(get_session),
) -> Dict[str, Any]:
    """
    Reçoit une commande Wix et met à jour l'inventaire du salon 'Luxura Online'
    en décrémentant les quantités pour chaque SKU commandé.

    ⚠️ Le format exact du payload Wix reste à confirmer.
    Ici on suppose quelque chose comme :

    {
      "id": "12345",
      "status": "PAID",
      "lineItems": [
        { "sku": "TAPE-18-60A", "quantity": 2 },
        { "sku": "ITIP-20-MIX60A", "quantity": 1 }
      ]
    }
    """
    payload = await request.json()

    order_id = payload.get("id") or payload.get("_id") or "UNKNOWN"
    status = (payload.get("status") or payload.get("paymentStatus") or "").upper()

    # On ne traite que les commandes payées
    if status not in ["PAID", "PAID_IN_FULL", "FULFILLED", "COMPLETED"]:
        return {
            "ok": True,
            "ignored": True,
            "reason": f"status={status}",
            "order_id": order_id,
        }

    line_items: List[Dict[str, Any]] = (
        payload.get("lineItems") or payload.get("items") or []
    )

    if not line_items:
        return {
            "ok": False,
            "error": "No line items in payload",
            "order_id": order_id,
        }

    salon = get_luxura_online_salon(session)
    updated: List[Dict[str, Any]] = []

    for item in line_items:
        sku = item.get("sku")
        qty_raw = item.get("quantity") or item.get("qty") or 0

        try:
            quantity = int(qty_raw)
        except (TypeError, ValueError):
            quantity = 0

        if not sku or quantity <= 0:
            continue

        # Trouver le produit par son SKU
        product = session.exec(
            select(Product).where(Product.sku == sku)
        ).first()

        if not product:
            # TODO : logger ça plus tard, pour voir les SKU inconnus
            continue

        # Chercher la ligne d'inventaire Luxura Online pour ce produit
        inv = session.exec(
            select(InventoryItem)
            .where(InventoryItem.salon_id == salon.id)
            .where(InventoryItem.product_id == product.id)
        ).first()

        if not inv:
            # Si on n'a pas de ligne, on part de 0
            inv = InventoryItem(
                salon_id=salon.id,
                product_id=product.id,
                quantity=0,
            )
            session.add(inv)
            session.flush()

        old_qty = inv.quantity or 0
        new_qty = max(0, old_qty - quantity)  # jamais en dessous de 0
        inv.quantity = new_qty

        updated.append(
            {
                "sku": sku,
                "old_quantity": old_qty,
                "ordered_quantity": quantity,
                "new_quantity": new_qty,
            }
        )

    session.commit()

    return {
        "ok": True,
        "order_id": order_id,
        "updated_items": updated,
    }
