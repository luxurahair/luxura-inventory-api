# app/services/wix_client.py

import os
import time
from typing import Any, Dict, List, Optional, Tuple

import requests

WIX_API_BASE = "https://www.wixapis.com"

# Retry configuration
MAX_RETRIES = 3
RETRY_CODES = [502, 503, 504]  # Bad Gateway, Service Unavailable, Gateway Timeout


class WixClient:
    """
    Client Wix Stores (CATALOG_V1).
    Auth: API KEY (ou API TOKEN) + wix-site-id.
    V2: Ajout retry logic pour erreurs 503/timeout
    """

    def __init__(self) -> None:
        self.api_key = os.getenv("WIX_API_KEY") or os.getenv("WIX_API_TOKEN")
        self.site_id = os.getenv("WIX_SITE_ID")
        self.timeout = int(os.getenv("REQUEST_TIMEOUT", "60"))  # Augmenté à 60s

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

    def _request_with_retry(self, method: str, url: str, **kwargs) -> requests.Response:
        """Execute request with retry logic for 503/timeout errors."""
        kwargs.setdefault("timeout", self.timeout)
        
        for attempt in range(MAX_RETRIES):
            try:
                if method.upper() == "POST":
                    resp = self.session.post(url, **kwargs)
                else:
                    resp = self.session.get(url, **kwargs)
                
                # Success
                if resp.status_code == 200:
                    return resp
                
                # Retry on 502/503/504
                if resp.status_code in RETRY_CODES:
                    wait_time = (attempt + 1) * 5  # 5, 10, 15 seconds
                    print(f"⚠️ Wix API {resp.status_code}, retry {attempt+1}/{MAX_RETRIES} dans {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                
                # Other errors - return immediately (let caller handle)
                return resp
                
            except requests.exceptions.Timeout:
                wait_time = (attempt + 1) * 5
                print(f"⚠️ Wix API timeout, retry {attempt+1}/{MAX_RETRIES} dans {wait_time}s...")
                time.sleep(wait_time)
                continue
            except requests.exceptions.ConnectionError:
                wait_time = (attempt + 1) * 5
                print(f"⚠️ Wix connexion error, retry {attempt+1}/{MAX_RETRIES} dans {wait_time}s...")
                time.sleep(wait_time)
                continue
        
        # All retries exhausted - make one final attempt and let it fail naturally
        if method.upper() == "POST":
            return self.session.post(url, **kwargs)
        return self.session.get(url, **kwargs)

    # ---------------------------------------------------------
    # PRODUCTS (stores v1)
    # ---------------------------------------------------------
    def query_products_v1(self, limit: int = 100, max_pages: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        POST /stores/v1/products/query
        Pagination via cursorPaging (limit <= 100).
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

            resp = self._request_with_retry("POST", url, headers=self._headers(), json=body)
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
    # PRODUCTS (stores-reader v1)  ✅ pour collectionIds
    # ---------------------------------------------------------
    def query_products_reader_v1(self, limit: int = 100, max_pages: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        POST /stores-reader/v1/products/query
        Souvent plus riche (collectionIds, etc.)
        FIXED: Use offset-based pagination instead of cursor
        V2: Added retry logic for 503 errors
        """
        url = f"{WIX_API_BASE}/stores-reader/v1/products/query"
        per_page = min(max(int(limit), 1), 100)

        offset = 0
        all_items: List[Dict[str, Any]] = []
        pages = 0

        while True:
            body: Dict[str, Any] = {"query": {"paging": {"limit": per_page, "offset": offset}}}

            resp = self._request_with_retry("POST", url, headers=self._headers(), json=body)
            if resp.status_code != 200:
                raise RuntimeError(f"Wix reader v1 products/query: {resp.status_code} {resp.text}")

            data = resp.json() or {}
            items = data.get("products") or data.get("items") or []
            if not isinstance(items, list):
                items = []

            if not items:
                break  # No more products
                
            all_items.extend(items)
            
            pages += 1
            offset += per_page
            
            if max_pages is not None and pages >= max_pages:
                break

        return all_items

    # ---------------------------------------------------------
    # COLLECTIONS (stores-reader v1) ✅ catégories
    # ---------------------------------------------------------
    def query_collections_reader_v1(self, limit: int = 100, max_pages: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        POST /stores-reader/v1/collections/query
        V2: Added retry logic
        """
        url = f"{WIX_API_BASE}/stores-reader/v1/collections/query"
        per_page = min(max(int(limit), 1), 100)

        cursor: Optional[str] = None
        all_items: List[Dict[str, Any]] = []
        pages = 0

        while True:
            body: Dict[str, Any] = {"query": {"paging": {"limit": per_page}}}
            if cursor:
                body["cursorPaging"] = {"cursor": cursor}

            resp = self._request_with_retry("POST", url, headers=self._headers(), json=body)
            if resp.status_code != 200:
                raise RuntimeError(f"Wix reader v1 collections/query: {resp.status_code} {resp.text}")

            data = resp.json() or {}
            items = data.get("collections") or data.get("items") or []
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
    # VARIANTS (stores v1)
    # ---------------------------------------------------------
    def query_variants_v1(self, product_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        POST /stores/v1/products/{productId}/variants/query
        V2: Added retry logic
        """
        pid = str(product_id).strip()
        if not pid:
            return []

        url = f"{WIX_API_BASE}/stores/v1/products/{pid}/variants/query"
        per_page = min(max(int(limit), 1), 100)

        body: Dict[str, Any] = {"query": {"paging": {"limit": per_page}}}
        resp = self._request_with_retry("POST", url, headers=self._headers(), json=body)
        if resp.status_code != 200:
            raise RuntimeError(f"Wix v1 variants/query: {resp.status_code} {resp.text}")

        data = resp.json() or {}
        items = data.get("variants") or data.get("items") or []
        if not isinstance(items, list):
            items = []
        return items

    # ---------------------------------------------------------
    # INVENTORY (stores-reader v2) ✅
    # ---------------------------------------------------------
    def query_inventory_items_v1(self, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """
        POST /stores-reader/v2/inventoryItems/query
        V2: Added retry logic for 503 errors
        """
        url = f"{WIX_API_BASE}/stores-reader/v2/inventoryItems/query"
        per_page = min(max(int(limit), 1), 100)
        off = max(int(offset), 0)

        body: Dict[str, Any] = {"query": {"paging": {"limit": per_page, "offset": off}}}
        resp = self._request_with_retry("POST", url, headers=self._headers(), json=body)
        if resp.status_code != 200:
            raise RuntimeError(f"Wix v1 inventoryItems/query: {resp.status_code} {resp.text}")

        return resp.json() or {}

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
