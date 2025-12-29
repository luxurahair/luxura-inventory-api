# app/services/wix_client.py
import os
from typing import Any, Dict, List, Tuple
import requests

WIX_API_BASE = "https://www.wixapis.com"

class WixClient:
    """
    Client minimal. (On peut ne plus l'utiliser, mais il doit compiler.)
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

    def query_products_v1(self, limit: int = 100) -> List[Dict[str, Any]]:
        url = f"{WIX_API_BASE}/stores/v1/products/query"
        payload = {"query": {"paging": {"limit": limit}}}
        resp = requests.post(url, headers=self._headers(), json=payload, timeout=30)
        if resp.status_code != 200:
            raise RuntimeError(f"Wix v1 products/query: {resp.status_code} {resp.text}")
        data = resp.json() or {}
        return data.get("products") or data.get("items") or []

    # Ancienne signature si du code l'appelle encore
    def query_products(self, limit: int = 100) -> Tuple[str, List[Dict[str, Any]]]:
        products = self.query_products_v1(limit=limit)
        return "CATALOG_V1", products
