#!/usr/bin/env python3
"""
Script CLI pour lancer un cycle complet de backlinks.

Usage:
    python run_backlink_cycle.py
    python run_backlink_cycle.py --directories hotfrog cylex
    python run_backlink_cycle.py --no-verify
"""

import sys
import os
import asyncio
import argparse

# Ajouter le path du backend
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backlinks.backlink_orchestrator import (
    run_full_backlink_cycle,
    run_submission_only,
    list_available_directories
)


async def main():
    parser = argparse.ArgumentParser(description="Lance un cycle de backlinks")
    parser.add_argument(
        "--directories", "-d",
        nargs="+",
        help="Annuaires spécifiques (ex: hotfrog cylex)"
    )
    parser.add_argument(
        "--no-verify",
        action="store_true",
        help="Ne pas vérifier les emails après soumission"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Liste les annuaires disponibles"
    )
    
    args = parser.parse_args()
    
    if args.list:
        print("\n📋 ANNUAIRES DISPONIBLES:")
        print("-" * 50)
        for d in list_available_directories():
            print(f"   - {d['key']:15} | {d['name']:25} | P{d['priority']}")
        return
    
    if args.no_verify:
        print("\n🚀 Lancement des soumissions seulement...")
        results = await run_submission_only(directories=args.directories)
        print(f"\n✅ {len(results)} soumissions effectuées")
    else:
        print("\n🚀 Lancement du cycle complet...")
        report = await run_full_backlink_cycle(
            directories=args.directories,
            verify_emails=True
        )
        print(f"\n✅ Cycle terminé: {report.get_summary()}")


if __name__ == "__main__":
    asyncio.run(main())
