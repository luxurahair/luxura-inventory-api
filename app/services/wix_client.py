# app/services/wix_client.py
import os
from typing import Any, Dict, List, Optional, Tuple

import requests

WIX_API_BASE = "https://www.wixapis.com"


class WixClient:
    """
    Client Wix Stores v1 (API KEY + wix-site-id).
    Pagination via cursorPaging (limit max 100).
    """

    def __init__(self) -> None:
        # Tolérant: supporte les deux noms
        self.api_key = os.getenv("WIX_API_KEY") or os.getenv("WIX_API_TOKEN")
        self.site_id = os.getenv("WIX_SITE_ID")

        if not self.api_key:
            raise RuntimeError("WIX_API_KEY / WIX_API_TOKEN manquant.")
        if not self.site_id:
            raise RuntimeError("WIX_SITE_ID manquant.")

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": self.api_key,  # pas Bearer
            "Content-Type": "application/json",
            "Accept": "application/json",
            "wix-site-id": self.site_id,
        }
  
    def query_inventory_items_v3(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Wix Stores Catalog v3 - Query inventory items (up to 1000).
        """
        url = f"{WIX_API_BASE}/stores/v3/inventory-items/query"
        body: Dict[str, Any] = {"query": {"paging": {"limit": min(max(int(limit), 1), 1000)}}}

        resp = requests.post(url, headers=self._headers(), json=body, timeout=30)
        if resp.status_code != 200:
            raise RuntimeError(f"Wix v3 inventory-items/query: {resp.status_code} {resp.text}")

        data = resp.json() or {}
        # Wix retourne souvent "inventoryItems" ou "items"
        return data.get("inventoryItems") or data.get("items") or []

    def query_products_v1(self, limit: int = 100, max_pages: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Récupère les produits via /stores/v1/products/query.
        Wix impose limit <= 100. On paginate avec cursorPaging.cursor.
        """
        url = f"{WIX_API_BASE}/stores/v1/products/query"

        per_page = min(max(int(limit), 1), 100)
        cursor: Optional[str] = None
        all_items: List[Dict[str, Any]] = []
        pages = 0

        while True:
            body: Dict[str, Any] = {"query": {"paging": {"limit": per_page}}}
            if cursor:
                body["cursorPaging"] = {"cursor": cursor}

            resp = requests.post(url, headers=self._headers(), json=body, timeout=30)
            if resp.status_code != 200:
                raise RuntimeError(f"Wix v1 products/query: {resp.status_code} {resp.text}")

            data = resp.json() or {}
            items = data.get("products") or data.get("items") or []
            all_items.extend(items)

            # Wix peut renvoyer le curseur à différents endroits selon versions/retours
            cursor = data.get("nextCursor") or (data.get("cursorPaging") or {}).get("nextCursor")

            pages += 1
            if not cursor:
                break
            if max_pages is not None and pages >= max_pages:
                break

        return all_items

    def query_variants_v1(self, product_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Récupère les variants d’un produit via:
        POST /stores/v1/products/{product_id}/variants/query

        Objectif: obtenir sku + choices (Longueur/Couleur) + inventory (si fourni).
        """
        url = f"{WIX_API_BASE}/stores/v1/products/{product_id}/variants/query"

        per_page = min(max(int(limit), 1), 100)
        body: Dict[str, Any] = {"query": {"paging": {"limit": per_page}}}

        resp = requests.post(url, headers=self._headers(), json=body, timeout=30)
        if resp.status_code != 200:
            raise RuntimeError(f"Wix v1 variants/query ({product_id}): {resp.status_code} {resp.text}")

        data = resp.json() or {}
        # Wix peut renvoyer "variants" ou "items"
        return data.get("variants") or data.get("items") or []
    
    # Ancienne signature si du code l'appelle encore
    def query_products(self, limit: int = 100) -> Tuple[str, List[Dict[str, Any]]]:
        products = self.query_products_v1(limit=limit)
        return "CATALOG_V1", products
