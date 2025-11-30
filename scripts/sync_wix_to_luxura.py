"""
Script manuel pour lancer une synchro Wix → Luxura
depuis la ligne de commande.

Usage :
    python scripts/sync_wix_to_luxura.py
"""

import os
import sys

# Assure que le dossier racine du projet est dans PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.services.wix_sync import sync_wix_to_luxura


def main() -> None:
    print("==> Running 'python scripts/sync_wix_to_luxura.py'")

    try:
        result = sync_wix_to_luxura(source="script")
    except Exception as e:
        print("❌ ERREUR pendant la synchro :", str(e))
        return

    print("==> Synchro terminée.")
    print(result)


if __name__ == "__main__":
    main()
