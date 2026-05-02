#!/usr/bin/env python3
"""
🎨 LUXURA CONNECTION DIAGRAM GENERATOR
======================================
Génère un diagramme ASCII/Unicode des connexions avec statuts colorés.

Usage:
    python scripts/connection_diagram.py
    python scripts/connection_diagram.py --output diagram.txt
"""

import os
import sys
import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

import httpx
import asyncpg
from dotenv import load_dotenv

# Charger les variables
load_dotenv(Path(__file__).parent.parent / ".secrets.env")

API_URL = os.getenv("RENDER_SERVICE_URL", "https://luxura-inventory-api.onrender.com")
DATABASE_URL = os.getenv("DATABASE_URL", "").replace("postgresql+psycopg://", "postgresql://")

# Couleurs ANSI
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"
BOLD = "\033[1m"


async def test_connection(name: str, test_func) -> Tuple[str, bool, str]:
    """Teste une connexion et retourne (nom, succès, message)"""
    try:
        result = await test_func()
        return (name, result[0], result[1])
    except Exception as e:
        return (name, False, str(e)[:50])


async def test_api_ping() -> Tuple[bool, str]:
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(f"{API_URL}/api/ping")
        if r.status_code == 200:
            data = r.json()
            return (True, f"OK - {data.get('timestamp', '')[:19]}")
        return (False, f"HTTP {r.status_code}")


async def test_wix_api() -> Tuple[bool, str]:
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(f"{API_URL}/api/ping")
        if r.status_code == 200:
            data = r.json()
            if data.get("wix_api") == "ok":
                return (True, "Token valide")
            return (False, f"wix_api = {data.get('wix_api')}")
        return (False, f"HTTP {r.status_code}")


async def test_wix_oauth() -> Tuple[bool, str]:
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(f"{API_URL}/wix/oauth/status")
        if r.status_code == 200:
            data = r.json()
            if data.get("is_valid"):
                days = data.get("time_remaining", "").split(",")[0]
                return (True, f"Valide ({days})")
            return (False, "Token expiré")
        return (False, f"HTTP {r.status_code}")


async def test_facebook() -> Tuple[bool, str]:
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(f"{API_URL}/api/facebook/status")
        if r.status_code == 200:
            data = r.json()
            if data.get("local", {}).get("token_valid"):
                return (True, data.get("local", {}).get("page_name", "OK")[:30])
            return (False, "Token invalide")
        return (False, f"HTTP {r.status_code}")


async def test_database() -> Tuple[bool, str]:
    if not DATABASE_URL:
        return (False, "DATABASE_URL non configuré")
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        count = await conn.fetchval("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'")
        await conn.close()
        return (True, f"{count} tables")
    except Exception as e:
        return (False, str(e)[:40])


async def test_cron_endpoint(name: str, endpoint: str) -> Tuple[bool, str]:
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(f"{API_URL}{endpoint}")
        # 404 ou 405 = endpoint existe mais méthode incorrecte (OK pour GET sur POST endpoint)
        if r.status_code in [200, 404, 405]:
            return (True, "Accessible")
        return (False, f"HTTP {r.status_code}")


def generate_diagram(results: List[Tuple[str, bool, str]], cron_results: List[Tuple[str, bool, str]]) -> str:
    """Génère le diagramme ASCII avec couleurs"""
    
    def status_icon(ok: bool) -> str:
        return f"{GREEN}●{RESET}" if ok else f"{RED}●{RESET}"
    
    def status_text(ok: bool, msg: str) -> str:
        color = GREEN if ok else RED
        return f"{color}{msg}{RESET}"
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Compter les statuts
    ok_count = sum(1 for _, ok, _ in results + cron_results if ok)
    total = len(results) + len(cron_results)
    
    diagram = f"""
{BOLD}╔══════════════════════════════════════════════════════════════════════════════════════╗
║                    🔌 LUXURA CONNECTION DIAGRAM - {now}                    ║
╠══════════════════════════════════════════════════════════════════════════════════════╣
║                                                                                      ║
║   {GREEN}● = Connecté{RESET}     {RED}● = Erreur{RESET}     {YELLOW}● = Warning{RESET}                               ║
║                                                                                      ║
║   📊 Résumé: {ok_count}/{total} connexions OK                                                         ║
╠══════════════════════════════════════════════════════════════════════════════════════╣{RESET}
║                                                                                      ║
║  ┌─────────────────────────────────────────────────────────────────────────────────┐ ║
║  │                         📡 SOURCES EXTERNES                                     │ ║
║  │                                                                                 │ ║
"""
    
    # Trouver les résultats par nom
    def get_result(name: str) -> Tuple[bool, str]:
        for n, ok, msg in results:
            if n == name:
                return (ok, msg)
        return (False, "Non testé")
    
    wix_ok, wix_msg = get_result("Wix API")
    fb_ok, fb_msg = get_result("Facebook")
    db_ok, db_msg = get_result("Database")
    oauth_ok, oauth_msg = get_result("Wix OAuth")
    
    diagram += f"""║  │   {status_icon(wix_ok)} WIX API          {status_icon(fb_ok)} FACEBOOK        {status_icon(db_ok)} SUPABASE                    │ ║
║  │     {status_text(wix_ok, wix_msg[:15].ljust(15))}   {status_text(fb_ok, fb_msg[:15].ljust(15))}   {status_text(db_ok, db_msg[:15].ljust(15))}          │ ║
║  │                                                                                 │ ║
║  │   {status_icon(oauth_ok)} WIX OAUTH                                                              │ ║
║  │     {status_text(oauth_ok, oauth_msg[:40].ljust(40))}                         │ ║
║  │                                                                                 │ ║
║  └───────────────────────────────────┬─────────────────────────────────────────────┘ ║
║                                      │                                               ║
║                                      ▼                                               ║
║  ┌───────────────────────────────────────────────────────────────────────────────────┐║
║  │                     🌐 LUXURA-INVENTORY-API (Render)                              │║
║  │                     {API_URL}                     │║
"""
    
    api_ok, api_msg = get_result("API Principale")
    diagram += f"""║  │                     {status_icon(api_ok)} Status: {status_text(api_ok, api_msg[:40].ljust(40))}              │║
║  └───────────────────────────────────┬───────────────────────────────────────────────┘║
║                                      │                                               ║
║                                      ▼                                               ║
║  ┌───────────────────────────────────────────────────────────────────────────────────┐║
║  │                           ⏰ CRON JOBS                                            │║
║  │                                                                                   │║
"""
    
    # Afficher les crons
    for name, ok, msg in cron_results:
        short_name = name[:35].ljust(35)
        diagram += f"║  │   {status_icon(ok)} {short_name} {status_text(ok, msg[:20].ljust(20))}          │║\n"
    
    diagram += f"""║  │                                                                                   │║
║  └───────────────────────────────────────────────────────────────────────────────────┘║
║                                                                                      ║
╚══════════════════════════════════════════════════════════════════════════════════════╝
"""
    
    return diagram


async def main():
    print(f"\n{BOLD}🔍 Test des connexions en cours...{RESET}\n")
    
    # Tests des connexions principales
    results = []
    
    tests = [
        ("API Principale", test_api_ping),
        ("Wix API", test_wix_api),
        ("Wix OAuth", test_wix_oauth),
        ("Facebook", test_facebook),
        ("Database", test_database),
    ]
    
    for name, func in tests:
        print(f"  Testing {name}...", end=" ")
        result = await test_connection(name, func)
        results.append(result)
        icon = f"{GREEN}✓{RESET}" if result[1] else f"{RED}✗{RESET}"
        print(f"{icon}")
    
    # Tests des crons
    print(f"\n{BOLD}⏰ Test des endpoints cron...{RESET}\n")
    
    crons = [
        ("Blog Auto-Generate", "/api/blog/auto-generate"),
        ("Wix Sync", "/wix/sync"),
        ("Facebook Posts", "/api/auto-content/facebook-posts"),
        ("Content Scan", "/api/content/scan"),
        ("Cron Status", "/api/cron/status"),
    ]
    
    cron_results = []
    for name, endpoint in crons:
        print(f"  Testing {name}...", end=" ")
        ok, msg = await test_cron_endpoint(name, endpoint)
        cron_results.append((name, ok, msg))
        icon = f"{GREEN}✓{RESET}" if ok else f"{RED}✗{RESET}"
        print(f"{icon}")
    
    # Générer le diagramme
    diagram = generate_diagram(results, cron_results)
    print(diagram)
    
    # Sauvegarder
    output_dir = Path(__file__).parent.parent / "reports"
    output_dir.mkdir(exist_ok=True)
    
    # Version sans couleurs pour fichier
    diagram_plain = diagram
    for color in [GREEN, RED, YELLOW, BLUE, RESET, BOLD]:
        diagram_plain = diagram_plain.replace(color, "")
    
    output_file = output_dir / f"connection_diagram_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(output_file, 'w') as f:
        f.write(diagram_plain)
    
    print(f"\n📁 Diagramme sauvegardé: {output_file}")
    
    # Retourner le statut global
    all_ok = all(ok for _, ok, _ in results + cron_results)
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
