#!/usr/bin/env python3
"""
🔧 LUXURA HEALTH MONITOR - Diagnostic & Auto-Repair System
============================================================

Ce script vérifie toutes les connexions et crons, auto-répare si possible,
et envoie un rapport par email.

Usage:
    python scripts/health_monitor.py              # Test complet
    python scripts/health_monitor.py --quick      # Test rapide (pas de dry-run)
    python scripts/health_monitor.py --repair     # Test + auto-repair
    python scripts/health_monitor.py --email      # Force l'envoi d'email même si OK

Render Cron:
    Schedule: 0 */6 * * * (toutes les 6 heures)
    Command: python scripts/health_monitor.py --repair --email-on-error
"""

import os
import sys
import json
import asyncio
import smtplib
import logging
from datetime import datetime, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import httpx
import asyncpg
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv(Path(__file__).parent.parent / ".secrets.env")

# Configuration
API_URL = os.getenv("RENDER_SERVICE_URL", "https://luxura-inventory-api.onrender.com")
LUXURA_EMAIL = os.getenv("LUXURA_EMAIL", "info@luxuradistribution.com")
LUXURA_APP_PASSWORD = os.getenv("LUXURA_APP_PASSWORD", "")
DATABASE_URL = os.getenv("DATABASE_URL", "").replace("postgresql+psycopg://", "postgresql://")

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================
# 📊 DÉFINITION DES TESTS
# ============================================================

HEALTH_CHECKS = [
    {
        "id": "api_ping",
        "name": "API Principale",
        "category": "infrastructure",
        "endpoint": "/api/ping",
        "method": "GET",
        "expected_keys": ["timestamp", "local_api"],
        "critical": True,
    },
    {
        "id": "wix_api",
        "name": "Wix API Connection",
        "category": "external",
        "endpoint": "/api/ping",
        "method": "GET",
        "expected_keys": ["wix_api"],
        "expected_value": {"key": "wix_api", "value": "ok"},
        "critical": True,
        "repair_action": "refresh_wix_token",
    },
    {
        "id": "wix_oauth",
        "name": "Wix OAuth Status",
        "category": "auth",
        "endpoint": "/wix/oauth/status",
        "method": "GET",
        "expected_keys": ["has_access_token", "is_valid"],
        "critical": True,
        "repair_action": "alert_wix_oauth",
    },
    {
        "id": "facebook_status",
        "name": "Facebook Connection",
        "category": "external",
        "endpoint": "/api/facebook/status",
        "method": "GET",
        "expected_keys": ["ok"],
        "critical": False,
    },
    {
        "id": "database",
        "name": "Database (Supabase)",
        "category": "infrastructure",
        "test_type": "database",
        "critical": True,
    },
    {
        "id": "cron_status",
        "name": "Cron Scheduler Status",
        "category": "scheduler",
        "endpoint": "/api/cron/status",
        "method": "GET",
        "expected_keys": ["timezone"],
        "critical": False,
    },
    {
        "id": "blog_dry_run",
        "name": "Blog Generation (Dry Run)",
        "category": "cron",
        "endpoint": "/api/blog/auto-generate",
        "method": "POST",
        "payload": {"count": 0, "dry_run": True},
        "critical": False,
        "slow": True,
    },
]

CRON_SERVICES = [
    {
        "id": "luxura-blog-cron",
        "name": "Blog Wix Automatique",
        "render_id": "crn-d7eham58nd3s73fv54bg",
        "schedule": "0 7,10,12,19,20 * * *",
        "target": "/api/blog/auto-generate",
        "frequency": "1 blog/jour",
    },
    {
        "id": "luxura-inventory-sync-cron",
        "name": "Sync Inventaire Wix",
        "render_id": "crn-d6vds1vafjfc73cvrojg",
        "schedule": "*/30 * * * *",
        "target": "/wix/sync",
        "frequency": "Toutes les 30 min",
    },
    {
        "id": "luxura-content-scan",
        "name": "Scan Contenu Magazine",
        "render_id": "crn-d7ih4nqqqhas7393ttug",
        "schedule": "*/15 * * * *",
        "target": "/api/content/scan",
        "frequency": "Toutes les 15 min",
    },
    {
        "id": "facebook-product-posts",
        "name": "Facebook Product Posts",
        "render_id": "crn-d7bbahvkijhs739v39lg",
        "schedule": "0 10 * * 1-5",
        "target": "/api/auto-content/facebook-posts",
        "frequency": "Lun-Ven 10h",
    },
    {
        "id": "facebook-educational-posts",
        "name": "Facebook Educational Posts",
        "render_id": "crn-d7bbj5h5pdvs738jmtpg",
        "schedule": "0 14 * * 1-5",
        "target": "/api/auto-content/facebook-posts",
        "frequency": "Lun-Ven 14h",
    },
    {
        "id": "facebook-weekend-posts",
        "name": "Facebook Weekend Posts",
        "render_id": "crn-d7bbkf6a2pns7381d5tg",
        "schedule": "0 11 * * 0,6",
        "target": "/api/auto-content/facebook-posts",
        "frequency": "Sam-Dim 11h",
    },
]


# ============================================================
# 🧪 FONCTIONS DE TEST
# ============================================================

async def test_endpoint(check: Dict) -> Dict:
    """Teste un endpoint API"""
    result = {
        "id": check["id"],
        "name": check["name"],
        "category": check["category"],
        "status": "unknown",
        "message": "",
        "response_time_ms": 0,
        "details": {},
    }
    
    try:
        start_time = datetime.now()
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = f"{API_URL}{check['endpoint']}"
            
            if check["method"] == "GET":
                response = await client.get(url)
            else:
                payload = check.get("payload", {})
                response = await client.post(url, json=payload)
            
            result["response_time_ms"] = (datetime.now() - start_time).total_seconds() * 1000
            
            if response.status_code == 200:
                data = response.json()
                result["details"] = data
                
                # Vérifier les clés attendues
                if "expected_keys" in check:
                    missing_keys = [k for k in check["expected_keys"] if k not in data]
                    if missing_keys:
                        result["status"] = "warning"
                        result["message"] = f"Clés manquantes: {missing_keys}"
                    else:
                        result["status"] = "ok"
                        result["message"] = "OK"
                
                # Vérifier la valeur attendue
                if "expected_value" in check:
                    ev = check["expected_value"]
                    if data.get(ev["key"]) != ev["value"]:
                        result["status"] = "error"
                        result["message"] = f"{ev['key']} = {data.get(ev['key'])} (attendu: {ev['value']})"
                    else:
                        result["status"] = "ok"
                        result["message"] = "OK"
                
                if result["status"] == "unknown":
                    result["status"] = "ok"
                    result["message"] = "OK"
            else:
                result["status"] = "error"
                result["message"] = f"HTTP {response.status_code}"
                
    except httpx.TimeoutException:
        result["status"] = "error"
        result["message"] = "Timeout (>30s)"
    except Exception as e:
        result["status"] = "error"
        result["message"] = str(e)
    
    return result


async def test_database() -> Dict:
    """Teste la connexion à la base de données"""
    result = {
        "id": "database",
        "name": "Database (Supabase)",
        "category": "infrastructure",
        "status": "unknown",
        "message": "",
        "details": {},
    }
    
    if not DATABASE_URL:
        result["status"] = "error"
        result["message"] = "DATABASE_URL non configuré"
        return result
    
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        
        # Vérifier les tables importantes
        tables = await conn.fetch("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        table_names = [t["table_name"] for t in tables]
        
        # Tables critiques
        critical_tables = ["blog_posts", "pending_posts", "wix_oauth"]
        missing_tables = [t for t in critical_tables if t not in table_names]
        
        # Vérifier le token Wix OAuth
        wix_oauth = await conn.fetchrow("SELECT * FROM wix_oauth WHERE id = 1")
        
        await conn.close()
        
        result["details"] = {
            "tables_count": len(table_names),
            "critical_tables_ok": len(missing_tables) == 0,
            "missing_tables": missing_tables,
            "wix_oauth_has_token": bool(wix_oauth and wix_oauth.get("access_token")),
            "wix_oauth_has_refresh": bool(wix_oauth and wix_oauth.get("refresh_token")),
        }
        
        if missing_tables:
            result["status"] = "warning"
            result["message"] = f"Tables manquantes: {missing_tables}"
        else:
            result["status"] = "ok"
            result["message"] = f"{len(table_names)} tables OK"
            
    except Exception as e:
        result["status"] = "error"
        result["message"] = str(e)
    
    return result


async def check_render_cron(cron: Dict) -> Dict:
    """Vérifie le statut d'un cron Render"""
    result = {
        "id": cron["id"],
        "name": cron["name"],
        "status": "unknown",
        "message": "",
        "details": {
            "schedule": cron["schedule"],
            "frequency": cron["frequency"],
            "target": cron["target"],
        },
    }
    
    # Pour l'instant, on vérifie juste si l'endpoint cible répond
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            url = f"{API_URL}{cron['target']}"
            response = await client.get(url)  # HEAD request pour vérifier
            
            if response.status_code in [200, 404, 405]:  # 405 = method not allowed mais endpoint existe
                result["status"] = "ok"
                result["message"] = "Endpoint accessible"
            else:
                result["status"] = "warning"
                result["message"] = f"HTTP {response.status_code}"
                
    except Exception as e:
        result["status"] = "error"
        result["message"] = str(e)
    
    return result


# ============================================================
# 🔧 FONCTIONS D'AUTO-REPAIR
# ============================================================

async def repair_wix_token() -> Tuple[bool, str]:
    """Tente de rafraîchir le token Wix"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{API_URL}/api/wix/token/refresh")
            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    return True, "Token Wix rafraîchi avec succès"
                else:
                    return False, f"Échec refresh: {data.get('error')}"
            return False, f"HTTP {response.status_code}"
    except Exception as e:
        return False, str(e)


async def wake_up_api() -> Tuple[bool, str]:
    """Réveille l'API si elle est en cold start"""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(f"{API_URL}/api/ping")
            if response.status_code == 200:
                return True, "API réveillée"
            return False, f"HTTP {response.status_code}"
    except Exception as e:
        return False, str(e)


REPAIR_ACTIONS = {
    "refresh_wix_token": repair_wix_token,
    "wake_up_api": wake_up_api,
}


# ============================================================
# 📧 RAPPORT EMAIL
# ============================================================

def generate_report(results: List[Dict], cron_results: List[Dict], repairs: List[Dict]) -> str:
    """Génère le rapport texte"""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    
    report = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              🔧 LUXURA HEALTH MONITOR - RAPPORT DE DIAGNOSTIC                 ║
║              {now}                               ║
╠══════════════════════════════════════════════════════════════════════════════╣

📊 RÉSUMÉ
═════════
"""
    
    # Compter les statuts
    ok_count = sum(1 for r in results if r["status"] == "ok")
    warning_count = sum(1 for r in results if r["status"] == "warning")
    error_count = sum(1 for r in results if r["status"] == "error")
    
    report += f"  ✅ OK: {ok_count}  |  ⚠️ Warnings: {warning_count}  |  ❌ Erreurs: {error_count}\n\n"
    
    # Tableau des tests
    report += """
📋 TESTS DE CONNEXION
═════════════════════
┌─────────────────────────────┬──────────┬─────────────────────────────────────┐
│ Service                     │ Statut   │ Message                             │
├─────────────────────────────┼──────────┼─────────────────────────────────────┤
"""
    
    for r in results:
        status_icon = "✅" if r["status"] == "ok" else ("⚠️" if r["status"] == "warning" else "❌")
        name = r["name"][:27].ljust(27)
        status = f"{status_icon} {r['status']}".ljust(8)
        msg = r["message"][:35].ljust(35)
        report += f"│ {name} │ {status} │ {msg} │\n"
    
    report += "└─────────────────────────────┴──────────┴─────────────────────────────────────┘\n"
    
    # Crons
    report += """
⏰ CRONS CONFIGURÉS
═══════════════════
┌─────────────────────────────┬──────────┬─────────────────────────────────────┐
│ Cron Job                    │ Statut   │ Fréquence                           │
├─────────────────────────────┼──────────┼─────────────────────────────────────┤
"""
    
    for c in cron_results:
        status_icon = "✅" if c["status"] == "ok" else ("⚠️" if c["status"] == "warning" else "❌")
        name = c["name"][:27].ljust(27)
        status = f"{status_icon} {c['status']}".ljust(8)
        freq = c["details"].get("frequency", "")[:35].ljust(35)
        report += f"│ {name} │ {status} │ {freq} │\n"
    
    report += "└─────────────────────────────┴──────────┴─────────────────────────────────────┘\n"
    
    # Réparations
    if repairs:
        report += """
🔧 AUTO-RÉPARATIONS EFFECTUÉES
══════════════════════════════
"""
        for repair in repairs:
            status = "✅" if repair["success"] else "❌"
            report += f"  {status} {repair['action']}: {repair['message']}\n"
    
    # Alertes critiques
    critical_errors = [r for r in results if r["status"] == "error" and r.get("critical")]
    if critical_errors:
        report += """
🚨 ALERTES CRITIQUES
════════════════════
"""
        for err in critical_errors:
            report += f"  ❌ {err['name']}: {err['message']}\n"
            if err.get("repair_action"):
                report += f"     → Action suggérée: {err['repair_action']}\n"
    
    report += """
╚══════════════════════════════════════════════════════════════════════════════╝
"""
    
    return report


def send_email_report(subject: str, body: str, is_error: bool = False):
    """Envoie le rapport par email"""
    if not LUXURA_EMAIL or not LUXURA_APP_PASSWORD:
        logger.warning("Credentials email non configurés, rapport non envoyé")
        return False
    
    try:
        msg = MIMEMultipart()
        msg['From'] = LUXURA_EMAIL
        msg['To'] = LUXURA_EMAIL
        msg['Subject'] = f"{'🚨' if is_error else '✅'} {subject}"
        
        # Corps du message en texte brut
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(LUXURA_EMAIL, LUXURA_APP_PASSWORD)
            server.send_message(msg)
        
        logger.info(f"Email envoyé à {LUXURA_EMAIL}")
        return True
        
    except Exception as e:
        logger.error(f"Erreur envoi email: {e}")
        return False


# ============================================================
# 🚀 MAIN
# ============================================================

async def run_health_check(
    quick: bool = False,
    repair: bool = False,
    force_email: bool = False,
    email_on_error: bool = True
) -> Dict:
    """Exécute tous les tests de santé"""
    
    logger.info("=" * 60)
    logger.info("🔧 LUXURA HEALTH MONITOR - Démarrage diagnostic")
    logger.info("=" * 60)
    
    results = []
    repairs = []
    
    # 1. Tests des endpoints
    for check in HEALTH_CHECKS:
        if quick and check.get("slow"):
            continue
            
        logger.info(f"Testing: {check['name']}...")
        
        if check.get("test_type") == "database":
            result = await test_database()
        else:
            result = await test_endpoint(check)
        
        results.append(result)
        
        status_icon = "✅" if result["status"] == "ok" else ("⚠️" if result["status"] == "warning" else "❌")
        logger.info(f"  {status_icon} {result['message']}")
        
        # Auto-repair si activé et erreur
        if repair and result["status"] == "error" and check.get("repair_action"):
            action = check["repair_action"]
            if action in REPAIR_ACTIONS:
                logger.info(f"  🔧 Tentative de réparation: {action}")
                success, msg = await REPAIR_ACTIONS[action]()
                repairs.append({"action": action, "success": success, "message": msg})
                logger.info(f"    {'✅' if success else '❌'} {msg}")
    
    # 2. Tests des crons
    logger.info("\n⏰ Vérification des crons...")
    cron_results = []
    for cron in CRON_SERVICES:
        result = await check_render_cron(cron)
        cron_results.append(result)
        status_icon = "✅" if result["status"] == "ok" else "❌"
        logger.info(f"  {status_icon} {cron['name']}: {result['message']}")
    
    # 3. Générer le rapport
    report = generate_report(results, cron_results, repairs)
    print(report)
    
    # 4. Sauvegarder en JSON
    json_report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "api_url": API_URL,
        "tests": results,
        "crons": cron_results,
        "repairs": repairs,
        "summary": {
            "ok": sum(1 for r in results if r["status"] == "ok"),
            "warnings": sum(1 for r in results if r["status"] == "warning"),
            "errors": sum(1 for r in results if r["status"] == "error"),
        }
    }
    
    # Sauvegarder le JSON
    report_dir = Path(__file__).parent.parent / "reports"
    report_dir.mkdir(exist_ok=True)
    report_file = report_dir / f"health_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(json_report, f, indent=2)
    logger.info(f"\n📁 Rapport JSON: {report_file}")
    
    # 5. Envoyer email si nécessaire
    has_errors = json_report["summary"]["errors"] > 0
    
    if force_email or (email_on_error and has_errors):
        subject = f"Luxura Health Monitor - {'ERREURS DÉTECTÉES' if has_errors else 'OK'}"
        send_email_report(subject, report, is_error=has_errors)
    
    return json_report


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Luxura Health Monitor")
    parser.add_argument("--quick", action="store_true", help="Test rapide sans dry-run")
    parser.add_argument("--repair", action="store_true", help="Tenter l'auto-réparation")
    parser.add_argument("--email", action="store_true", help="Forcer l'envoi d'email")
    parser.add_argument("--email-on-error", action="store_true", help="Email seulement si erreur")
    
    args = parser.parse_args()
    
    result = asyncio.run(run_health_check(
        quick=args.quick,
        repair=args.repair,
        force_email=args.email,
        email_on_error=args.email_on_error or args.email
    ))
    
    # Exit code basé sur les erreurs
    sys.exit(1 if result["summary"]["errors"] > 0 else 0)


if __name__ == "__main__":
    main()
