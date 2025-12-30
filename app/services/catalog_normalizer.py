from typing import Any, Dict, Optional


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
