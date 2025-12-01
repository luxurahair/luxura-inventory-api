from typing import Any, Dict


def normalize_product(wix_product: Dict[str, Any], version: str) -> Dict[str, Any]:
    """
    Transforme un produit Wix (V1 ou V3) en dict compatible avec Product.
    """

    if version == "CATALOG_V1":
        inventory = (wix_product.get("inventory") or {}) or {}
        price_data = (wix_product.get("priceData") or {}) or {}

        return {
            "wix_id": wix_product.get("id") or wix_product.get("_id"),
            "sku": wix_product.get("sku"),
            "name": wix_product.get("name"),
            "price": float(price_data.get("price") or 0),
            "description": wix_product.get("description"),
            "handle": wix_product.get("slug"),
            "is_in_stock": bool(inventory.get("inStock", True)),
            "quantity": int(inventory.get("quantity") or 0),
            "options": wix_product.get("productOptions") or {},
        }

    elif version == "CATALOG_V3":
        variants = wix_product.get("variants") or []
        first_variant = variants[0] if variants else {}
        stock = (first_variant.get("stock") or {}) or {}
        price_obj = (first_variant.get("price") or {}) or {}

        return {
            "wix_id": wix_product.get("id") or wix_product.get("_id"),
            "sku": first_variant.get("sku") or wix_product.get("productCode"),
            "name": wix_product.get("name"),
            "price": float(price_obj.get("amount") or 0),
            "description": wix_product.get("description"),
            "handle": wix_product.get("slug"),
            "is_in_stock": bool(stock.get("inStock", True)),
            "quantity": int(stock.get("quantity") or 0),
            "options": wix_product.get("options") or {},
        }

    else:
        raise ValueError(f"Version de catalogue inconnue: {version}")
