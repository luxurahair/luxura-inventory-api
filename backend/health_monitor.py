"""
LUXURA HEALTH MONITOR & AUTO-REPAIR SYSTEM
==========================================
Vérifie tous les endpoints critiques et génère un rapport de santé.
Peut être appelé via /api/health/full ou en ligne de commande.
"""

import httpx
import asyncio
import os
from datetime import datetime, timezone
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

# Configuration
RENDER_API_URL = os.getenv("RENDER_API_URL", "https://luxura-inventory-api.onrender.com")
LOCAL_API_URL = "http://localhost:8001"

# Liste de tous les endpoints critiques qui DOIVENT exister
CRITICAL_ENDPOINTS = [
    # Health & Status
    {"method": "GET", "path": "/api/health", "name": "Health Check", "critical": True},
    {"method": "GET", "path": "/api/ping", "name": "Ping", "critical": True},
    
    # Wix Sync (CRON)
    {"method": "POST", "path": "/wix/sync", "name": "Wix Sync (sans /api)", "critical": True, "params": {"dry_run": "true", "limit": "1"}},
    {"method": "POST", "path": "/api/wix/sync", "name": "Wix Sync (avec /api)", "critical": True, "params": {"dry_run": "true", "limit": "1"}},
    {"method": "POST", "path": "/inventory/sync", "name": "Inventory Sync (alias)", "critical": True, "params": {"dry_run": "true", "limit": "1"}},
    {"method": "GET", "path": "/wix/sync/last", "name": "Last Sync Status", "critical": False},
    
    # Wix Token
    {"method": "GET", "path": "/api/wix/token/refresh", "name": "Wix Token Refresh", "critical": False},
    
    # Products
    {"method": "GET", "path": "/api/products", "name": "Products List", "critical": True},
    
    # Auth
    {"method": "GET", "path": "/api/auth/me", "name": "Auth Me", "critical": False},
    
    # Blog
    {"method": "GET", "path": "/api/blog", "name": "Blog Posts", "critical": False},
    
    # Color Engine
    {"method": "GET", "path": "/api/colors", "name": "Colors List", "critical": False},
]


async def check_endpoint(client: httpx.AsyncClient, base_url: str, endpoint: Dict) -> Dict[str, Any]:
    """Vérifie un endpoint et retourne son status"""
    url = f"{base_url}{endpoint['path']}"
    method = endpoint.get("method", "GET")
    params = endpoint.get("params", {})
    
    try:
        if method == "GET":
            response = await client.get(url, params=params, timeout=10.0)
        elif method == "POST":
            response = await client.post(url, params=params, timeout=10.0)
        else:
            response = await client.request(method, url, params=params, timeout=10.0)
        
        # 200-299 = OK, 401/403 = Auth required (endpoint exists), 404 = Missing
        status = "ok" if response.status_code < 400 else "error"
        if response.status_code == 401 or response.status_code == 403:
            status = "auth_required"  # Endpoint exists but needs auth
        elif response.status_code == 404:
            status = "missing"
        elif response.status_code == 405:
            status = "method_not_allowed"
        
        return {
            "name": endpoint["name"],
            "path": endpoint["path"],
            "method": method,
            "status": status,
            "http_code": response.status_code,
            "critical": endpoint.get("critical", False),
            "response_preview": response.text[:200] if len(response.text) < 500 else response.text[:200] + "..."
        }
    except httpx.TimeoutException:
        return {
            "name": endpoint["name"],
            "path": endpoint["path"],
            "method": method,
            "status": "timeout",
            "http_code": None,
            "critical": endpoint.get("critical", False),
            "error": "Timeout after 10s"
        }
    except Exception as e:
        return {
            "name": endpoint["name"],
            "path": endpoint["path"],
            "method": method,
            "status": "error",
            "http_code": None,
            "critical": endpoint.get("critical", False),
            "error": str(e)
        }


async def run_health_check(base_url: str = None) -> Dict[str, Any]:
    """Exécute une vérification complète de santé"""
    if base_url is None:
        base_url = RENDER_API_URL
    
    results = []
    critical_failures = []
    warnings = []
    
    async with httpx.AsyncClient() as client:
        for endpoint in CRITICAL_ENDPOINTS:
            result = await check_endpoint(client, base_url, endpoint)
            results.append(result)
            
            if result["status"] in ["missing", "error", "timeout"]:
                if result["critical"]:
                    critical_failures.append(result)
                else:
                    warnings.append(result)
    
    # Calcul du score de santé
    total = len(results)
    ok_count = len([r for r in results if r["status"] in ["ok", "auth_required"]])
    health_score = int((ok_count / total) * 100) if total > 0 else 0
    
    # Status global
    if len(critical_failures) > 0:
        overall_status = "critical"
    elif len(warnings) > 0:
        overall_status = "degraded"
    else:
        overall_status = "healthy"
    
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "base_url": base_url,
        "overall_status": overall_status,
        "health_score": health_score,
        "total_endpoints": total,
        "ok_count": ok_count,
        "critical_failures": critical_failures,
        "warnings": warnings,
        "all_results": results,
        "recommendations": generate_recommendations(critical_failures, warnings)
    }


def generate_recommendations(critical_failures: List, warnings: List) -> List[str]:
    """Génère des recommandations basées sur les erreurs"""
    recommendations = []
    
    # Check for missing wix/sync endpoints
    wix_sync_missing = any(
        f["path"] in ["/wix/sync", "/api/wix/sync", "/inventory/sync"] 
        for f in critical_failures if f["status"] == "missing"
    )
    if wix_sync_missing:
        recommendations.append(
            "🔴 CRITIQUE: Les endpoints /wix/sync sont manquants! "
            "Le code sur Render n'est pas à jour. Faire un 'Save to GitHub' depuis Emergent."
        )
    
    # Check for products endpoint
    products_missing = any(f["path"] == "/api/products" and f["status"] == "missing" for f in critical_failures)
    if products_missing:
        recommendations.append(
            "🔴 CRITIQUE: L'endpoint /api/products est manquant! "
            "L'API principale ne fonctionne pas correctement."
        )
    
    # Check for timeout issues
    timeouts = [f for f in critical_failures + warnings if f["status"] == "timeout"]
    if timeouts:
        recommendations.append(
            f"⚠️ {len(timeouts)} endpoint(s) en timeout. "
            "Le serveur peut être surchargé ou en cours de démarrage."
        )
    
    if not recommendations:
        recommendations.append("✅ Tous les endpoints critiques fonctionnent correctement!")
    
    return recommendations


def print_health_report(report: Dict):
    """Affiche un rapport de santé formaté"""
    print("\n" + "=" * 60)
    print("🏥 LUXURA HEALTH REPORT")
    print("=" * 60)
    print(f"📅 Timestamp: {report['timestamp']}")
    print(f"🌐 URL: {report['base_url']}")
    print(f"📊 Status: {report['overall_status'].upper()}")
    print(f"💯 Health Score: {report['health_score']}%")
    print(f"✅ OK: {report['ok_count']}/{report['total_endpoints']}")
    
    if report['critical_failures']:
        print("\n🔴 CRITICAL FAILURES:")
        for f in report['critical_failures']:
            print(f"   - {f['method']} {f['path']} → {f['status']} ({f.get('http_code', 'N/A')})")
    
    if report['warnings']:
        print("\n⚠️ WARNINGS:")
        for w in report['warnings']:
            print(f"   - {w['method']} {w['path']} → {w['status']} ({w.get('http_code', 'N/A')})")
    
    print("\n📋 RECOMMENDATIONS:")
    for rec in report['recommendations']:
        print(f"   {rec}")
    
    print("=" * 60 + "\n")


# CLI mode
if __name__ == "__main__":
    import sys
    
    url = sys.argv[1] if len(sys.argv) > 1 else RENDER_API_URL
    print(f"Checking health of {url}...")
    
    report = asyncio.run(run_health_check(url))
    print_health_report(report)
    
    # Exit code based on status
    if report['overall_status'] == 'critical':
        sys.exit(2)
    elif report['overall_status'] == 'degraded':
        sys.exit(1)
    else:
        sys.exit(0)
