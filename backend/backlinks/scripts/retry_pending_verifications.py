#!/usr/bin/env python3
"""
Script CLI pour relancer les vérifications en attente.

Usage:
    python retry_pending_verifications.py
"""

import sys
import os
import asyncio

# Ajouter le path du backend
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backlinks.backlink_orchestrator import (
    run_verification_only,
    get_pending_directories
)


async def main():
    pending = get_pending_directories()
    
    print("\n📧 RELANCE DES VÉRIFICATIONS")
    print("=" * 50)
    print(f"Annuaires en attente: {len(pending)}")
    
    if pending:
        print("\nAnnuaires:")
        for d in pending:
            print(f"   - {d}")
    
    print("\n🔍 Lancement de la vérification...")
    report = await run_verification_only()
    
    print(f"\n✅ Terminé")
    print(f"   Emails trouvés: {report.get('emails_found', 0)}")
    print(f"   Liens cliqués: {report.get('links_clicked', 0)}")


if __name__ == "__main__":
    asyncio.run(main())
