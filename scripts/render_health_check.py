#!/usr/bin/env python3
"""
RENDER HEALTH CHECK & AUTO-REPAIR SCRIPT
========================================
À exécuter périodiquement pour vérifier l'état des services Render.
Peut être utilisé comme cron job Render.

Usage:
    python scripts/render_health_check.py
    python scripts/render_health_check.py --repair
    python scripts/render_health_check.py --url https://custom-url.com
"""

import os
import sys
import httpx
import json
from datetime import datetime, timezone

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

RENDER_API_URL = os.getenv("RENDER_API_URL", "https://luxura-inventory-api.onrender.com")
SEO_SECRET = os.getenv("SEO_SECRET", "")
TIMEOUT = 30

# Critical endpoints that MUST work for the system to function
CRITICAL_CHECKS = [
    {"method": "GET", "path": "/api/health", "name": "API Health"},
    {"method": "POST", "path": "/wix/sync", "name": "Wix Sync", "params": {"dry_run": "true", "limit": "1"}},
    {"method": "GET", "path": "/api/products", "name": "Products", "params": {"limit": "1"}},
]


def log(msg: str):
    """Log with timestamp"""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"[{timestamp}] {msg}")


def check_endpoint(url: str, method: str = "GET", params: dict = None) -> dict:
    """Check a single endpoint"""
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            if method == "GET":
                response = client.get(url, params=params)
            elif method == "POST":
                headers = {}
                if SEO_SECRET:
                    headers["X-SEO-SECRET"] = SEO_SECRET
                response = client.post(url, params=params, headers=headers)
            else:
                response = client.request(method, url, params=params)
            
            return {
                "ok": response.status_code < 400,
                "status_code": response.status_code,
                "response": response.text[:500]
            }
    except Exception as e:
        return {
            "ok": False,
            "status_code": None,
            "error": str(e)
        }


def run_health_checks(base_url: str) -> dict:
    """Run all health checks"""
    log(f"🏥 Starting health checks for {base_url}")
    
    results = []
    all_ok = True
    
    for check in CRITICAL_CHECKS:
        url = f"{base_url}{check['path']}"
        params = check.get("params", {})
        
        log(f"   Checking {check['method']} {check['path']}...")
        result = check_endpoint(url, check["method"], params)
        result["name"] = check["name"]
        result["path"] = check["path"]
        results.append(result)
        
        if result["ok"]:
            log(f"   ✅ {check['name']}: OK ({result['status_code']})")
        else:
            log(f"   ❌ {check['name']}: FAILED ({result.get('status_code', 'N/A')})")
            all_ok = False
    
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "base_url": base_url,
        "all_ok": all_ok,
        "results": results
    }


def generate_report(health_data: dict) -> str:
    """Generate a human-readable report"""
    lines = [
        "="*60,
        "LUXURA RENDER HEALTH REPORT",
        "="*60,
        f"Timestamp: {health_data['timestamp']}",
        f"URL: {health_data['base_url']}",
        f"Overall Status: {'✅ HEALTHY' if health_data['all_ok'] else '❌ UNHEALTHY'}",
        "",
        "Endpoint Results:",
    ]
    
    for result in health_data["results"]:
        status = "✅" if result["ok"] else "❌"
        code = result.get("status_code", "N/A")
        lines.append(f"  {status} {result['name']}: {result['path']} → {code}")
    
    if not health_data["all_ok"]:
        lines.extend([
            "",
            "⚠️ RECOMMENDATIONS:",
            "  1. Vérifiez que le code est à jour sur GitHub",
            "  2. Faites un 'Manual Deploy' → 'Clear cache & deploy' sur Render",
            "  3. Vérifiez les variables d'environnement (DATABASE_URL, SEO_SECRET)",
        ])
    
    lines.append("="*60)
    return "\n".join(lines)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Luxura Render Health Check")
    parser.add_argument("--url", default=RENDER_API_URL, help="Base URL to check")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--repair", action="store_true", help="Attempt auto-repair (future feature)")
    args = parser.parse_args()
    
    # Run checks
    health_data = run_health_checks(args.url)
    
    # Output
    if args.json:
        print(json.dumps(health_data, indent=2))
    else:
        print(generate_report(health_data))
    
    # Exit code
    if health_data["all_ok"]:
        log("🎉 All health checks passed!")
        sys.exit(0)
    else:
        log("💥 Some health checks failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
