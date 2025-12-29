import os
from typing import List, Dict, Any, Tuple
import requests

WIX_API_BASE = "https://www.wixapis.com"

class WixClient:
    def __init__(self) -> None:
        # 1) Mode API KEY (recommandé)
        self.api_key = os.getenv("WIX_API_KEY") or os.getenv("WIX_API_TOKEN")
        self.site_id = os.getenv("WIX_SITE_ID")
        self.account_id = os.getenv("WIX_ACCOUNT_ID")

        if not self.api_key:
            raise RuntimeError("WIX_API_KEY (ou WIX_API_TOKEN) manquant.")

        # Choisir UN SEUL header d'identité (site OU account)
        # Pour Wix Stores, site-level est généralement le bon choix.
        self.identity_header: Dict[str, str] = {}
        if self.site_id:
            self.identity_header = {"wix-site-id": self.site_id}
        elif self.account_id:
            self.identity_header = {"wix-account-id": self.account_id}
        else:
            raise RuntimeError("WIX_SITE_ID ou WIX_ACCOUNT_ID manquant (API key auth).")

    def _headers(self) -> Dict[str, str]:
        # IMPORTANT: pas de "Bearer" pour API Key auth
        h = {
            "Authorization": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        h.update(self.identity_header)
        return h

    def get_catalog_version(self) -> str:
        url = f"{WIX_API_BASE}/stores/v3/provision/version"
        resp = requests.get(url, headers=self._headers(), timeout=20)
        if resp.status_code != 200:
            raise RuntimeError(f"Erreur Wix get_catalog_version: {resp.status_code} {resp.text}")
        data = resp.json()
        return data.get("catalogVersion", "CATALOG_V1")

    def query_products(self, limit: int = 100) -> Tuple[str, List[Dict[str, Any]]]:
        version = self.get_catalog_version()

        if version == "CATALOG_V1":
            url = f"{WIX_API_BASE}/stores/v1/products/query"
            payload = {"query": {"paging": {"limit": limit}}}
        else:
            url = f"{WIX_API_BASE}/stores/v3/products/query"
            payload = {"query": {"paging": {"limit": limit}}}

        resp = requests.post(url, headers=self._headers(), json=payload, timeout=30)
        if resp.status_code != 200:
            raise RuntimeError(f"Erreur Wix query_products ({version}): {resp.status_code} {resp.text}")

        data = resp.json()
        products = data.get("products") or data.get("items") or []
        return version, products
