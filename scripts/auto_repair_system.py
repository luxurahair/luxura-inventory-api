#!/usr/bin/env python3
"""
🔧 LUXURA AUTO-REPAIR SYSTEM
============================
Système de surveillance et réparation automatique pour Render.

Fonctionnalités:
- Vérifie la santé de l'API toutes les 15 minutes
- Crée un backup automatique quand tout fonctionne à 100%
- Redéploie automatiquement en cas de panne
- Envoie des notifications par email

Usage:
    python scripts/auto_repair_system.py --check
    python scripts/auto_repair_system.py --repair
    python scripts/auto_repair_system.py --backup
    python scripts/auto_repair_system.py --full-cycle
"""

import os
import sys
import json
import httpx
import argparse
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
import subprocess
import time

# =============================================================================
# CONFIGURATION
# =============================================================================

# Render API
RENDER_API_KEY = os.getenv("RENDER_API_KEY", "")
RENDER_SERVICE_ID = os.getenv("RENDER_SERVICE_ID", "srv-d46bkg2li9vc73dean4g")  # luxura-inventory-api
RENDER_API_BASE = "https://api.render.com/v1"

# API URLs
API_URL = os.getenv("RENDER_SERVICE_URL", "https://luxura-inventory-api.onrender.com")

# Email notifications
EMAIL_USER = os.getenv("EMAIL_USERNAME", "")
EMAIL_PASS = os.getenv("EMAIL_PASSWORD", "")
NOTIFY_EMAIL = os.getenv("NOTIFY_EMAIL", "info@luxuradistribution.com")

# GitHub
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_REPO = "luxurahair/luxura-inventory-api"

# Timeouts
HEALTH_CHECK_TIMEOUT = 30
REPAIR_WAIT_TIME = 300  # 5 minutes après un repair

# =============================================================================
# ENDPOINTS CRITIQUES À VÉRIFIER
# =============================================================================

CRITICAL_ENDPOINTS = [
    {"method": "GET", "path": "/api/health", "name": "Health Check", "critical": True},
    {"method": "GET", "path": "/api/ping", "name": "Ping", "critical": True},
    {"method": "GET", "path": "/api/products", "name": "Products API", "critical": True, "params": {"limit": "1"}},
    {"method": "GET", "path": "/api/categories", "name": "Categories API", "critical": True},
    {"method": "POST", "path": "/wix/sync", "name": "Wix Sync", "critical": True, "params": {"dry_run": "true", "limit": "1"}},
]

OPTIONAL_ENDPOINTS = [
    {"method": "GET", "path": "/api/blog", "name": "Blog API", "critical": False},
    {"method": "GET", "path": "/api/colors", "name": "Colors API", "critical": False},
    {"method": "GET", "path": "/seo/by_wix_id", "name": "SEO API", "critical": False},
]

# =============================================================================
# UTILITAIRES
# =============================================================================

def log(msg: str, level: str = "INFO"):
    """Log avec timestamp"""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    emoji = {"INFO": "ℹ️", "SUCCESS": "✅", "WARNING": "⚠️", "ERROR": "❌", "REPAIR": "🔧"}.get(level, "📝")
    print(f"[{timestamp}] {emoji} {level}: {msg}")


def send_notification(subject: str, body: str, is_html: bool = False):
    """Envoie une notification par email"""
    if not EMAIL_USER or not EMAIL_PASS:
        log("Email non configuré - notification ignorée", "WARNING")
        return False
    
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"[Luxura Auto-Repair] {subject}"
        msg["From"] = EMAIL_USER
        msg["To"] = NOTIFY_EMAIL
        
        content_type = "html" if is_html else "plain"
        msg.attach(MIMEText(body, content_type))
        
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_USER, EMAIL_PASS)
            server.sendmail(EMAIL_USER, NOTIFY_EMAIL, msg.as_string())
        
        log(f"Notification envoyée: {subject}", "SUCCESS")
        return True
    except Exception as e:
        log(f"Erreur envoi email: {e}", "ERROR")
        return False


# =============================================================================
# HEALTH CHECK
# =============================================================================

def check_endpoint(url: str, method: str = "GET", params: dict = None) -> Tuple[bool, int, str]:
    """Vérifie un endpoint et retourne (ok, status_code, message)"""
    try:
        with httpx.Client(timeout=HEALTH_CHECK_TIMEOUT) as client:
            if method == "GET":
                response = client.get(url, params=params)
            elif method == "POST":
                response = client.post(url, params=params)
            else:
                response = client.request(method, url, params=params)
            
            is_ok = response.status_code < 400 or response.status_code in [401, 403]
            return is_ok, response.status_code, response.text[:200]
    except httpx.TimeoutException:
        return False, 0, "Timeout"
    except Exception as e:
        return False, 0, str(e)


def run_health_check() -> Dict[str, Any]:
    """Exécute un health check complet"""
    log("Démarrage du health check...")
    
    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "api_url": API_URL,
        "critical": [],
        "optional": [],
        "critical_ok": 0,
        "critical_failed": 0,
        "optional_ok": 0,
        "optional_failed": 0,
        "health_score": 0,
        "status": "unknown"
    }
    
    # Vérifier endpoints critiques
    for endpoint in CRITICAL_ENDPOINTS:
        url = f"{API_URL}{endpoint['path']}"
        ok, code, msg = check_endpoint(url, endpoint.get("method", "GET"), endpoint.get("params"))
        
        result = {
            "name": endpoint["name"],
            "path": endpoint["path"],
            "ok": ok,
            "status_code": code,
            "message": msg[:100]
        }
        results["critical"].append(result)
        
        if ok:
            results["critical_ok"] += 1
            log(f"  {endpoint['name']}: OK ({code})", "SUCCESS")
        else:
            results["critical_failed"] += 1
            log(f"  {endpoint['name']}: FAILED ({code}) - {msg[:50]}", "ERROR")
    
    # Vérifier endpoints optionnels
    for endpoint in OPTIONAL_ENDPOINTS:
        url = f"{API_URL}{endpoint['path']}"
        ok, code, msg = check_endpoint(url, endpoint.get("method", "GET"), endpoint.get("params"))
        
        result = {
            "name": endpoint["name"],
            "path": endpoint["path"],
            "ok": ok,
            "status_code": code,
            "message": msg[:100]
        }
        results["optional"].append(result)
        
        if ok:
            results["optional_ok"] += 1
        else:
            results["optional_failed"] += 1
    
    # Calculer le score de santé
    total_critical = len(CRITICAL_ENDPOINTS)
    total_optional = len(OPTIONAL_ENDPOINTS)
    
    # Score: 80% basé sur critiques, 20% sur optionnels
    critical_score = (results["critical_ok"] / total_critical) * 80 if total_critical > 0 else 0
    optional_score = (results["optional_ok"] / total_optional) * 20 if total_optional > 0 else 20
    results["health_score"] = int(critical_score + optional_score)
    
    # Déterminer le status
    if results["critical_failed"] == 0:
        if results["health_score"] == 100:
            results["status"] = "healthy"
        else:
            results["status"] = "degraded"
    else:
        results["status"] = "critical"
    
    log(f"Health Score: {results['health_score']}% - Status: {results['status']}")
    return results


# =============================================================================
# RENDER API OPERATIONS
# =============================================================================

def render_api_request(method: str, endpoint: str, data: dict = None) -> Optional[Dict]:
    """Fait une requête à l'API Render"""
    if not RENDER_API_KEY:
        log("RENDER_API_KEY non configurée", "ERROR")
        return None
    
    url = f"{RENDER_API_BASE}{endpoint}"
    headers = {
        "Authorization": f"Bearer {RENDER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        with httpx.Client(timeout=30) as client:
            if method == "GET":
                response = client.get(url, headers=headers)
            elif method == "POST":
                response = client.post(url, headers=headers, json=data or {})
            else:
                response = client.request(method, url, headers=headers, json=data)
            
            if response.status_code >= 400:
                log(f"Render API error: {response.status_code} - {response.text}", "ERROR")
                return None
            
            return response.json() if response.text else {}
    except Exception as e:
        log(f"Render API exception: {e}", "ERROR")
        return None


def get_service_status() -> Optional[Dict]:
    """Récupère le status du service Render"""
    return render_api_request("GET", f"/services/{RENDER_SERVICE_ID}")


def get_latest_deploys(limit: int = 5) -> List[Dict]:
    """Récupère les derniers déploiements"""
    result = render_api_request("GET", f"/services/{RENDER_SERVICE_ID}/deploys?limit={limit}")
    return result if result else []


def trigger_deploy(clear_cache: bool = False) -> Optional[str]:
    """Déclenche un nouveau déploiement"""
    log(f"Déclenchement d'un déploiement (clear_cache={clear_cache})...", "REPAIR")
    
    data = {}
    if clear_cache:
        data["clearCache"] = "clear"
    
    result = render_api_request("POST", f"/services/{RENDER_SERVICE_ID}/deploys", data)
    
    if result:
        deploy_id = result.get("id", "unknown")
        log(f"Déploiement déclenché: {deploy_id}", "SUCCESS")
        return deploy_id
    return None


def wait_for_deploy(deploy_id: str, max_wait: int = 600) -> bool:
    """Attend qu'un déploiement soit terminé"""
    log(f"Attente du déploiement {deploy_id}...")
    
    start_time = time.time()
    while time.time() - start_time < max_wait:
        deploys = get_latest_deploys(1)
        if deploys:
            status = deploys[0].get("deploy", {}).get("status", "unknown")
            log(f"  Status: {status}")
            
            if status == "live":
                log("Déploiement réussi!", "SUCCESS")
                return True
            elif status in ["deactivated", "build_failed", "update_failed", "canceled"]:
                log(f"Déploiement échoué: {status}", "ERROR")
                return False
        
        time.sleep(30)  # Vérifier toutes les 30 secondes
    
    log("Timeout en attendant le déploiement", "ERROR")
    return False


# =============================================================================
# BACKUP SYSTEM
# =============================================================================

def create_backup_tag() -> Optional[str]:
    """Crée un tag de backup dans Git quand tout fonctionne"""
    if not GITHUB_TOKEN:
        log("GITHUB_TOKEN non configuré - backup ignoré", "WARNING")
        return None
    
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    tag_name = f"backup-healthy-{timestamp}"
    
    try:
        # Récupérer le dernier commit
        with httpx.Client(timeout=30) as client:
            headers = {
                "Authorization": f"token {GITHUB_TOKEN}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            # Get latest commit SHA
            response = client.get(
                f"https://api.github.com/repos/{GITHUB_REPO}/commits/main",
                headers=headers
            )
            if response.status_code != 200:
                log(f"Erreur récupération commit: {response.status_code}", "ERROR")
                return None
            
            commit_sha = response.json()["sha"]
            
            # Créer le tag
            tag_data = {
                "tag": tag_name,
                "message": f"Auto-backup: API healthy at 100% - {timestamp}",
                "object": commit_sha,
                "type": "commit",
                "tagger": {
                    "name": "Luxura Auto-Repair",
                    "email": "auto-repair@luxuradistribution.com",
                    "date": datetime.now(timezone.utc).isoformat()
                }
            }
            
            response = client.post(
                f"https://api.github.com/repos/{GITHUB_REPO}/git/tags",
                headers=headers,
                json=tag_data
            )
            
            if response.status_code == 201:
                # Créer la référence du tag
                ref_data = {
                    "ref": f"refs/tags/{tag_name}",
                    "sha": response.json()["sha"]
                }
                client.post(
                    f"https://api.github.com/repos/{GITHUB_REPO}/git/refs",
                    headers=headers,
                    json=ref_data
                )
                
                log(f"Backup tag créé: {tag_name}", "SUCCESS")
                return tag_name
            else:
                log(f"Erreur création tag: {response.status_code} - {response.text}", "ERROR")
                return None
                
    except Exception as e:
        log(f"Erreur backup: {e}", "ERROR")
        return None


def get_latest_healthy_backup() -> Optional[str]:
    """Récupère le dernier backup healthy"""
    if not GITHUB_TOKEN:
        return None
    
    try:
        with httpx.Client(timeout=30) as client:
            headers = {
                "Authorization": f"token {GITHUB_TOKEN}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            response = client.get(
                f"https://api.github.com/repos/{GITHUB_REPO}/tags",
                headers=headers
            )
            
            if response.status_code == 200:
                tags = response.json()
                healthy_tags = [t for t in tags if t["name"].startswith("backup-healthy-")]
                if healthy_tags:
                    return healthy_tags[0]["name"]  # Le plus récent
            return None
    except:
        return None


# =============================================================================
# AUTO-REPAIR LOGIC
# =============================================================================

def auto_repair() -> bool:
    """Exécute la logique de réparation automatique"""
    log("=" * 60)
    log("DÉMARRAGE AUTO-REPAIR")
    log("=" * 60)
    
    # 1. Health check
    health = run_health_check()
    
    # 2. Si tout est OK, créer un backup
    if health["status"] == "healthy" and health["health_score"] == 100:
        log("Système 100% healthy - création d'un backup...", "SUCCESS")
        backup_tag = create_backup_tag()
        if backup_tag:
            send_notification(
                "✅ Système Healthy - Backup créé",
                f"L'API Luxura fonctionne à 100%.\n\nBackup tag: {backup_tag}\nScore: {health['health_score']}%"
            )
        return True
    
    # 3. Si dégradé mais pas critique, juste notifier
    if health["status"] == "degraded":
        log("Système dégradé mais fonctionnel", "WARNING")
        send_notification(
            "⚠️ Système Dégradé",
            f"L'API Luxura est dégradée.\n\nScore: {health['health_score']}%\n\nEndpoints en erreur:\n" +
            "\n".join([f"- {e['name']}: {e['status_code']}" for e in health["optional"] if not e["ok"]])
        )
        return True
    
    # 4. Si critique, tenter une réparation
    if health["status"] == "critical":
        log("ÉTAT CRITIQUE - Tentative de réparation...", "ERROR")
        
        send_notification(
            "🚨 CRITIQUE - Réparation en cours",
            f"L'API Luxura est en panne!\n\nScore: {health['health_score']}%\n\nEndpoints critiques en erreur:\n" +
            "\n".join([f"- {e['name']}: {e['status_code']} - {e['message'][:50]}" for e in health["critical"] if not e["ok"]])
        )
        
        # Tentative 1: Redéployer sans clear cache
        log("Tentative 1: Redéploiement standard...", "REPAIR")
        deploy_id = trigger_deploy(clear_cache=False)
        
        if deploy_id:
            time.sleep(60)  # Attendre 1 minute
            
            # Vérifier si ça a marché
            health2 = run_health_check()
            if health2["status"] != "critical":
                log("Réparation réussie après redéploiement!", "SUCCESS")
                send_notification(
                    "✅ Réparation Réussie",
                    f"L'API Luxura a été réparée.\n\nNouveau score: {health2['health_score']}%"
                )
                return True
        
        # Tentative 2: Redéployer avec clear cache
        log("Tentative 2: Redéploiement avec clear cache...", "REPAIR")
        deploy_id = trigger_deploy(clear_cache=True)
        
        if deploy_id:
            time.sleep(120)  # Attendre 2 minutes
            
            health3 = run_health_check()
            if health3["status"] != "critical":
                log("Réparation réussie après clear cache!", "SUCCESS")
                send_notification(
                    "✅ Réparation Réussie (Clear Cache)",
                    f"L'API Luxura a été réparée avec clear cache.\n\nNouveau score: {health3['health_score']}%"
                )
                return True
        
        # Échec de la réparation
        log("ÉCHEC DE LA RÉPARATION AUTOMATIQUE", "ERROR")
        send_notification(
            "❌ ÉCHEC Réparation - Intervention Manuelle Requise",
            f"La réparation automatique a échoué.\n\nActions tentées:\n- Redéploiement standard\n- Redéploiement avec clear cache\n\nVeuillez vérifier manuellement:\n{RENDER_API_BASE.replace('api.', 'dashboard.')}"
        )
        return False
    
    return True


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Luxura Auto-Repair System")
    parser.add_argument("--check", action="store_true", help="Run health check only")
    parser.add_argument("--repair", action="store_true", help="Run repair if needed")
    parser.add_argument("--backup", action="store_true", help="Create backup tag")
    parser.add_argument("--deploy", action="store_true", help="Trigger deploy")
    parser.add_argument("--clear-cache", action="store_true", help="Clear cache on deploy")
    parser.add_argument("--full-cycle", action="store_true", help="Run full check + repair + backup cycle")
    
    args = parser.parse_args()
    
    # Charger les variables d'environnement depuis .env si présent
    try:
        from dotenv import load_dotenv
        env_path = os.path.join(os.path.dirname(__file__), "..", "backend", ".env")
        if os.path.exists(env_path):
            load_dotenv(env_path)
        secrets_path = os.path.join(os.path.dirname(__file__), "..", ".secrets.env")
        if os.path.exists(secrets_path):
            load_dotenv(secrets_path)
    except:
        pass
    
    # Recharger les variables globales
    global RENDER_API_KEY, EMAIL_USER, EMAIL_PASS, GITHUB_TOKEN
    RENDER_API_KEY = os.getenv("RENDER_API_KEY", RENDER_API_KEY)
    EMAIL_USER = os.getenv("EMAIL_USERNAME", EMAIL_USER)
    EMAIL_PASS = os.getenv("EMAIL_PASSWORD", EMAIL_PASS)
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", GITHUB_TOKEN)
    
    if args.check:
        health = run_health_check()
        print(json.dumps(health, indent=2))
        sys.exit(0 if health["status"] != "critical" else 1)
    
    elif args.repair or args.full_cycle:
        success = auto_repair()
        sys.exit(0 if success else 1)
    
    elif args.backup:
        tag = create_backup_tag()
        sys.exit(0 if tag else 1)
    
    elif args.deploy:
        deploy_id = trigger_deploy(clear_cache=args.clear_cache)
        sys.exit(0 if deploy_id else 1)
    
    else:
        # Par défaut: health check
        health = run_health_check()
        print(json.dumps(health, indent=2))
        sys.exit(0 if health["status"] != "critical" else 1)


if __name__ == "__main__":
    main()
