from typing import Any, Dict, Optional


def normalize_variant(parent: Dict[str, Any], variant: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    wix_product_id = parent.get("id") or parent.get("_id")
    wix_variant_id = variant.get("id") or variant.get("_id") or variant.get("variantId")

    if not wix_product_id or not wix_variant_id:
        return None

    sku = (variant.get("sku") or "").strip()
    if not sku:
        sku = f"{wix_product_id}:{wix_variant_id}"

    choices = variant.get("choices") or variant.get("options") or {}
    if not isinstance(choices, dict):
        choices = {}


    base_name = (parent.get("name") or "Sans nom").strip()
    suffix = " ".join(str(v) for v in choices.values() if v)
    name = f"{base_name} — {suffix}".strip(" —") if suffix else base_name

    inv = variant.get("inventory") or {}
    track = bool(inv.get("trackQuantity", False))

    qty_raw = inv.get("quantity", 0)
    try:
        qty = int(qty_raw or 0)
    except Exception:
        qty = 0

    in_stock = inv.get("inStock")
    if isinstance(in_stock, bool):
        is_in_stock = in_stock
    else:
        is_in_stock = qty > 0

    price_parent = (parent.get("priceData") or {}).get("price") or 0
    price_variant = (variant.get("priceData") or {}).get("price", price_parent) or 0

    return {
        # parent wix id (pas unique)
        "wix_id": str(wix_product_id),

        # unique logique
        "sku": sku,

        # data produit
        "name": name,
        "description": parent.get("description") or None,
        "price": float(price_variant),
        "handle": parent.get("slug") or parent.get("handle") or parent.get("urlPart"),

        # stock (optionnel, mais pratique)
        "is_in_stock": bool(is_in_stock),
        "quantity": int(qty),

        # options utiles
        "options": {
            "wix_variant_id": variant.get("id") or variant.get("_id") or variant.get("variantId"),
            "choices": choices,
        },

        # internes pour inventory_entrepot
        "_track_quantity": track,
        "_quantity": qty,
    }


def _clean_sku(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        v = value.strip()
        return v if v else None
    return str(value).strip() or None


def normalize_product(wix_product: Dict[str, Any], version: str) -> Dict[str, Any]:
    """
    Transforme un produit Wix en dict compatible avec Product.
    NOTE: sku vide -> None pour éviter de casser un UNIQUE sur sku.
    """
    if version == "CATALOG_V1":
        inventory = (wix_product.get("inventory") or {}) or {}
        price_data = (wix_product.get("priceData") or {}) or {}

        sku = _clean_sku(wix_product.get("sku"))

        return {
            "wix_id": wix_product.get("id") or wix_product.get("_id"),
            "sku": sku,
            "name": wix_product.get("name"),
            "price": float(price_data.get("price") or 0),
            "description": wix_product.get("description"),
            "handle": wix_product.get("slug"),
            "is_in_stock": bool(inventory.get("inStock", True)),
            "quantity": int(inventory.get("quantity") or 0),
            "options": wix_product.get("productOptions") or {},
        }

    raise ValueError(f"Version de catalogue inconnue: {version}")
