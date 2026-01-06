# app/services/wix_client.py
import os
from typing import Any, Dict, List, Optional, Tuple

import requests

WIX_API_BASE = "https://www.wixapis.com"


class WixClient:
    """
    Client Wix Stores (CATALOG_V1).
    Auth: API KEY (ou API TOKEN) + wix-site-id.
    """

    def __init__(self) -> None:
        self.api_key = os.getenv("WIX_API_KEY") or os.getenv("WIX_API_TOKEN")
        self.site_id = os.getenv("WIX_SITE_ID")
        self.timeout = int(os.getenv("REQUEST_TIMEOUT", "30"))

        if not self.api_key:
            raise RuntimeError("WIX_API_KEY / WIX_API_TOKEN manquant.")
        if not self.site_id:
            raise RuntimeError("WIX_SITE_ID manquant.")

        self.session = requests.Session()

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": self.api_key,  # pas Bearer
            "Content-Type": "application/json",
            "Accept": "application/json",
            "wix-site-id": self.site_id,
        }

    # ---------------------------------------------------------
    # PRODUCTS (CATALOG_V1)
    # ---------------------------------------------------------
    def query_products_v1(self, limit: int = 100, max_pages: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Récupère les produits via /stores/v1/products/query.
        Pagination via cursorPaging.cursor (limit <= 100).
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

            resp = self.session.post(url, headers=self._headers(), json=body, timeout=self.timeout)
            if resp.status_code != 200:
                raise RuntimeError(f"Wix v1 products/query: {resp.status_code} {resp.text}")

            data = resp.json() or {}
            items = data.get("products") or data.get("items") or []
            if not isinstance(items, list):
                items = []

            all_items.extend(items)

            cursor = data.get("nextCursor") or (data.get("cursorPaging") or {}).get("nextCursor")

            pages += 1
            if not cursor:
                break
            if max_pages is not None and pages >= max_pages:
                break

        return all_items

    # ---------------------------------------------------------
    # VARIANTS (CATALOG_V1)
    # ---------------------------------------------------------
    def query_variants_v1(self, product_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Variants d’un produit:
        /stores/v1/products/{productId}/variants/query
        """
        pid = str(product_id).strip()
        if not pid:
            return []

        url = f"{WIX_API_BASE}/stores/v1/products/{pid}/variants/query"
        per_page = min(max(int(limit), 1), 100)

        body: Dict[str, Any] = {"query": {"paging": {"limit": per_page}}}
        resp = self.session.post(url, headers=self._headers(), json=body, timeout=self.timeout)
        if resp.status_code != 200:
            raise RuntimeError(f"Wix v1 variants/query: {resp.status_code} {resp.text}")

        data = resp.json() or {}
        items = data.get("variants") or data.get("items") or []
        if not isinstance(items, list):
            items = []
        return items

    # ---------------------------------------------------------
    # INVENTORY (CATALOG_V1) ✅
    # ---------------------------------------------------------
    def query_inventory_items_v1(self, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """
        Inventory CATALOG_V1:
        /stores-reader/v2/inventoryItems/query
        Pagination via paging.limit + paging.offset (limit <= 100).
        """
        url = f"{WIX_API_BASE}/stores-reader/v2/inventoryItems/query"
        per_page = min(max(int(limit), 1), 100)
        off = max(int(offset), 0)

        body: Dict[str, Any] = {"query": {"paging": {"limit": per_page, "offset": off}}}
        resp = self.session.post(url, headers=self._headers(), json=body, timeout=self.timeout)
        if resp.status_code != 200:
            raise RuntimeError(f"Wix v1 inventoryItems/query: {resp.status_code} {resp.text}")

        return resp.json() or {}

    # ---------------------------------------------------------
    # INVENTORY (CATALOG_V3) ❌ (garde si migration future)
    # ---------------------------------------------------------
    def query_inventory_items_v3(self, limit: int = 1000) -> List[Dict[str, Any]]:
        url = f"{WIX_API_BASE}/stores/v3/inventory-items/query"
        body: Dict[str, Any] = {"query": {"paging": {"limit": min(max(int(limit), 1), 1000)}}}

        resp = self.session.post(url, headers=self._headers(), json=body, timeout=self.timeout)
        if resp.status_code != 200:
            raise RuntimeError(f"Wix v3 inventory-items/query: {resp.status_code} {resp.text}")

        data = resp.json() or {}
        return data.get("inventoryItems") or data.get("items") or []

    # ---------------------------------------------------------
    # LEGACY ALIAS (compat)
    # ---------------------------------------------------------
    def query_products(self, limit: int = 100) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Ancienne signature si du code l'appelle encore.
        Retourne (catalog_version, products).
        """
        products = self.query_products_v1(limit=limit)
        return "CATALOG_V1", products
