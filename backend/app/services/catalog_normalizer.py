from typing import Any, Dict, Optional


def _clean_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        v = value.strip()
        return v or None
    v = str(value).strip()
    return v or None


def _first_non_empty_str(*values: Any) -> Optional[str]:
    for v in values:
        s = _clean_str(v)
        if s:
            return s
    return None


def _normalize_options_payload(value: Any) -> Dict[str, Any]:
    """
    Normalise productOptions Wix pour qu'ils soient toujours stockés
    sous forme de dict compatible avec le champ Product.options.
    """
    if isinstance(value, dict):
        return value
    if isinstance(value, list):
        return {"productOptions": value}
    return {}


def normalize_variant(parent: Dict[str, Any], variant: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    1 variant Wix = 1 Product Luxura

    Règle SKU:
      - si Wix fournit un SKU de variante non vide -> on le prend
      - sinon fallback stable: "<wix_product_id>:<wix_variant_id>"
    """
    wix_product_id = parent.get("id") or parent.get("_id")
    wix_variant_id = variant.get("id") or variant.get("_id") or variant.get("variantId")

    if not wix_product_id or not wix_variant_id:
        return None

    wix_product_id_s = str(wix_product_id).strip()
    wix_variant_id_s = str(wix_variant_id).strip()

    sku_field = variant.get("sku")  # peut être str OU dict OU vide

    sku = _first_non_empty_str(
        sku_field if isinstance(sku_field, str) else None,
        (variant.get("variant") or {}).get("sku"),
        (sku_field or {}).get("value") if isinstance(sku_field, dict) else None,
        variant.get("stockKeepingUnit"),
        (variant.get("skuData") or {}).get("sku"),
        variant.get("vendorSku"),
        variant.get("itemNumber"),
    )

    if not sku:
        sku = f"{wix_product_id_s}:{wix_variant_id_s}"

    choices = variant.get("choices") or variant.get("options") or {}
    if not isinstance(choices, dict):
        choices = {}

    base_name = _clean_str(parent.get("name")) or "Sans nom"
    suffix = " ".join(str(v) for v in choices.values() if v)
    name = f"{base_name} — {suffix}".strip(" —") if suffix else base_name

    inv = variant.get("inventory") or {}
    if not isinstance(inv, dict):
        inv = {}

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
    try:
        price = float(price_variant or 0)
    except Exception:
        price = 0.0

    handle = _clean_str(parent.get("slug") or parent.get("handle") or parent.get("urlPart"))

    # =========================================
    # EXTRACTION DES IMAGES DU PRODUIT WIX
    # =========================================
    images = []
    
    def extract_image_url(media_obj):
        """Extrait l'URL d'image depuis un objet media Wix (plusieurs formats possibles)"""
        if not isinstance(media_obj, dict):
            return None
        
        # Format 1: media_obj est directement {url: "..."} ou {image: {url: "..."}}
        url = (
            media_obj.get("url") or
            media_obj.get("src") or
            media_obj.get("fullUrl") or
            (media_obj.get("image") or {}).get("url") or
            (media_obj.get("image") or {}).get("src")
        )
        
        if url and isinstance(url, str) and url.startswith("http"):
            return url
        return None
    
    # 1. Images de la variante (priorité - rarement présentes)
    variant_media = variant.get("media") or variant.get("mediaItems") or {}
    if isinstance(variant_media, dict):
        # Essayer mainMedia d'abord
        main_media = variant_media.get("mainMedia")
        if main_media:
            url = extract_image_url(main_media)
            if url and url not in images:
                images.append(url)
        
        # Puis les items
        items = variant_media.get("items") or []
        if isinstance(items, list):
            for item in items:
                url = extract_image_url(item)
                if url and url not in images:
                    images.append(url)
    
    # 2. Images du parent (IMPORTANT: c'est là que sont les vraies images)
    parent_media = parent.get("media") or parent.get("mediaItems") or {}
    if isinstance(parent_media, dict):
        # mainMedia contient l'image principale du produit
        main_media = parent_media.get("mainMedia")
        if main_media:
            url = extract_image_url(main_media)
            if url and url not in images:
                images.append(url)
        
        # items contient toutes les images (incluant mainMedia parfois)
        items = parent_media.get("items") or []
        if isinstance(items, list):
            for item in items:
                url = extract_image_url(item)
                if url and url not in images:
                    images.append(url)
    
    # Limiter à 5 images max
    images = images[:5]

    return {
        "wix_id": wix_product_id_s,
        "sku": sku,
        "name": name,
        "description": parent.get("description") or None,
        "price": price,
        "handle": handle,
        "is_in_stock": bool(is_in_stock),
        "quantity": int(qty),
        "options": {
            "wix_variant_id": wix_variant_id_s,
            "choices": choices,
            "images": images,  # AJOUT DES IMAGES
        },
        "_track_quantity": track,
        "_quantity": qty,
    }


def normalize_product(wix_product: Dict[str, Any], version: str) -> Dict[str, Any]:
    """
    Transforme un produit Wix (parent) en dict compatible avec Product.
    NOTE: sku vide -> None pour éviter de casser un UNIQUE sur sku.
    """
    if version == "CATALOG_V1":
        inventory = wix_product.get("inventory") or {}
        if not isinstance(inventory, dict):
            inventory = {}

        price_data = wix_product.get("priceData") or {}
        if not isinstance(price_data, dict):
            price_data = {}

        sku = _clean_str(wix_product.get("sku"))

        try:
            price = float(price_data.get("price") or 0)
        except Exception:
            price = 0.0

        qty_raw = inventory.get("quantity") or 0
        try:
            qty = int(qty_raw or 0)
        except Exception:
            qty = 0

        return {
            "wix_id": wix_product.get("id") or wix_product.get("_id"),
            "sku": sku,
            "name": wix_product.get("name"),
            "price": price,
            "description": wix_product.get("description"),
            "handle": wix_product.get("slug"),
            "is_in_stock": bool(inventory.get("inStock", True)),
            "quantity": qty,
            "options": _normalize_options_payload(wix_product.get("productOptions")),
        }

    raise ValueError(f"Version de catalogue inconnue: {version}")
