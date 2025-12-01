import os
from typing import List, Dict, Any

import requests

WIX_API_BASE = "https://www.wixapis.com"


class WixClient:
    def __init__(self) -> None:
        token = os.getenv("WIX_API_TOKEN")
        if not token:
            raise RuntimeError("WIX_API_TOKEN manquant dans les variables d'environnement.")
        self.token = token

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    def get_catalog_version(self) -> str:
        """
        Retourne 'CATALOG_V1' ou 'CATALOG_V3'
        """
        url = f"{WIX_API_BASE}/stores/v3/provision/version"
        resp = requests.get(url, headers=self._headers(), timeout=15)
        if resp.status_code != 200:
            raise RuntimeError(
                f"Erreur Wix get_catalog_version: {resp.status_code} {resp.text}"
            )
        data = resp.json()
        return data.get("catalogVersion", "CATALOG_V1")

    def query_products(self, limit: int = 100) -> tuple[str, List[Dict[str, Any]]]:
        """
        Récupère les produits Wix, peu importe V1 ou V3.
        Retourne (version, liste_de_produits_bruts)
        """
        version = self.get_catalog_version()

        if version == "CATALOG_V1":
            url = f"{WIX_API_BASE}/stores/v1/products/query"
            payload = {"query": {"paging": {"limit": limit}}}
        else:  # CATALOG_V3
            url = f"{WIX_API_BASE}/stores/v3/products/query"
            payload = {"query": {"paging": {"limit": limit}}}

        resp = requests.post(url, headers=self._headers(), json=payload, timeout=20)
        if resp.status_code != 200:
            raise RuntimeError(
                f"Erreur Wix query_products ({version}): {resp.status_code} {resp.text}"
            )

        data = resp.json()
        # suivant la version, ça peut être "products" ou "items"
        products = data.get("products") or data.get("items") or []
        return version, products
