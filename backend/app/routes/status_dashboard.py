# app/routes/status_dashboard.py
"""
📊 LUXURA STATUS DASHBOARD - Monitoring en temps réel
=====================================================
Dashboard live accessible via /api/status/dashboard
"""
import os
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

import httpx
import asyncpg
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse

router = APIRouter(prefix="/api/status", tags=["status-dashboard"])
logger = logging.getLogger(__name__)

# Configuration
API_URL = os.getenv("RENDER_SERVICE_URL", "https://luxura-inventory-api.onrender.com")
DATABASE_URL = os.getenv("DATABASE_URL", "").replace("postgresql+psycopg://", "postgresql://")


async def check_service(name: str, check_func) -> Dict:
    """Vérifie un service et retourne son statut"""
    try:
        start = datetime.now()
        ok, message = await check_func()
        response_time = (datetime.now() - start).total_seconds() * 1000
        return {
            "name": name,
            "status": "ok" if ok else "error",
            "message": message,
            "response_time_ms": round(response_time, 2)
        }
    except Exception as e:
        return {
            "name": name,
            "status": "error",
            "message": str(e)[:100],
            "response_time_ms": 0
        }


async def check_api():
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(f"{API_URL}/api/ping")
        if r.status_code == 200:
            return (True, "API en ligne")
        return (False, f"HTTP {r.status_code}")


async def check_wix():
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(f"{API_URL}/api/ping")
        if r.status_code == 200:
            data = r.json()
            if data.get("wix_api") == "ok":
                return (True, "Token valide")
            return (False, f"wix_api: {data.get('wix_api')}")
        return (False, f"HTTP {r.status_code}")


async def check_wix_oauth():
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(f"{API_URL}/wix/oauth/status")
        if r.status_code == 200:
            data = r.json()
            if data.get("is_valid"):
                remaining = data.get("time_remaining", "").split(",")[0]
                has_refresh = "✓ auto-renew" if data.get("can_auto_renew") else "⚠️ pas de refresh"
                return (True, f"Valide ({remaining}) {has_refresh}")
            return (False, "Token expiré")
        return (False, f"HTTP {r.status_code}")


async def check_facebook():
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(f"{API_URL}/api/facebook/status")
        if r.status_code == 200:
            data = r.json()
            if data.get("local", {}).get("token_valid"):
                page_name = data.get("local", {}).get("page_name", "OK")
                return (True, page_name[:25])
            return (False, "Token invalide")
        return (False, f"HTTP {r.status_code}")


async def check_database():
    if not DATABASE_URL:
        return (False, "DATABASE_URL non configuré")
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        count = await conn.fetchval(
            "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'"
        )
        await conn.close()
        return (True, f"{count} tables")
    except Exception as e:
        return (False, str(e)[:50])


async def check_cron_endpoint(endpoint: str):
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(f"{API_URL}{endpoint}")
        if r.status_code in [200, 404, 405]:
            return (True, "Accessible")
        return (False, f"HTTP {r.status_code}")


@router.get("/live")
async def get_live_status():
    """
    📊 Retourne le statut live de toutes les connexions en JSON.
    Rafraîchir cette page pour voir le statut actuel.
    """
    # Tests parallèles pour rapidité
    results = await asyncio.gather(
        check_service("API Principale", check_api),
        check_service("Wix API", check_wix),
        check_service("Wix OAuth", check_wix_oauth),
        check_service("Facebook", check_facebook),
        check_service("Database", check_database),
        check_service("Blog Cron", lambda: check_cron_endpoint("/api/blog/auto-generate")),
        check_service("Wix Sync", lambda: check_cron_endpoint("/wix/sync")),
        check_service("Facebook Posts", lambda: check_cron_endpoint("/api/auto-content/facebook-posts")),
        check_service("Content Scan", lambda: check_cron_endpoint("/api/content/scan")),
    )
    
    ok_count = sum(1 for r in results if r["status"] == "ok")
    total = len(results)
    
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "ok": ok_count,
            "errors": total - ok_count,
            "total": total,
            "health_percent": round(ok_count / total * 100, 1)
        },
        "services": results
    }


@router.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard(request: Request):
    """
    📊 Dashboard HTML en temps réel avec auto-refresh.
    Ouvrir dans un navigateur pour voir le monitoring live.
    """
    
    # Obtenir le statut
    status = await get_live_status()
    
    # Générer le HTML
    services_html = ""
    for svc in status["services"]:
        color = "#4CAF50" if svc["status"] == "ok" else "#f44336"
        icon = "✅" if svc["status"] == "ok" else "❌"
        services_html += f"""
        <tr>
            <td style="padding: 12px; border-bottom: 1px solid #333;">
                <span style="color: {color}; font-size: 20px;">{icon}</span>
                {svc['name']}
            </td>
            <td style="padding: 12px; border-bottom: 1px solid #333; color: {color};">
                {svc['status'].upper()}
            </td>
            <td style="padding: 12px; border-bottom: 1px solid #333;">
                {svc['message']}
            </td>
            <td style="padding: 12px; border-bottom: 1px solid #333; color: #888;">
                {svc['response_time_ms']}ms
            </td>
        </tr>
        """
    
    health_color = "#4CAF50" if status["summary"]["health_percent"] >= 90 else (
        "#ff9800" if status["summary"]["health_percent"] >= 70 else "#f44336"
    )
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Luxura Status Dashboard</title>
        <meta charset="utf-8">
        <meta http-equiv="refresh" content="30">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
                background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                color: #fff;
                min-height: 100vh;
                padding: 20px;
            }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            .header {{
                text-align: center;
                padding: 30px;
                background: rgba(255,255,255,0.05);
                border-radius: 15px;
                margin-bottom: 30px;
            }}
            .header h1 {{ font-size: 2.5em; margin-bottom: 10px; }}
            .header .timestamp {{ color: #888; font-size: 0.9em; }}
            .health-score {{
                font-size: 4em;
                font-weight: bold;
                color: {health_color};
                margin: 20px 0;
            }}
            .summary {{
                display: flex;
                justify-content: center;
                gap: 40px;
                margin: 20px 0;
            }}
            .summary-item {{
                text-align: center;
                padding: 15px 30px;
                background: rgba(255,255,255,0.1);
                border-radius: 10px;
            }}
            .summary-item .value {{ font-size: 2em; font-weight: bold; }}
            .summary-item .label {{ color: #888; font-size: 0.9em; }}
            table {{
                width: 100%;
                border-collapse: collapse;
                background: rgba(255,255,255,0.05);
                border-radius: 15px;
                overflow: hidden;
            }}
            th {{
                background: rgba(255,255,255,0.1);
                padding: 15px;
                text-align: left;
                font-weight: 600;
            }}
            .diagram {{
                background: rgba(0,0,0,0.3);
                border-radius: 15px;
                padding: 20px;
                margin-top: 30px;
                font-family: monospace;
                white-space: pre;
                overflow-x: auto;
            }}
            .refresh-info {{
                text-align: center;
                color: #888;
                margin-top: 20px;
                font-size: 0.9em;
            }}
            .ok {{ color: #4CAF50; }}
            .error {{ color: #f44336; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔌 Luxura Status Dashboard</h1>
                <div class="timestamp">Dernière mise à jour: {status['timestamp'][:19].replace('T', ' ')} UTC</div>
                <div class="health-score">{status['summary']['health_percent']}%</div>
                <div class="summary">
                    <div class="summary-item">
                        <div class="value ok">{status['summary']['ok']}</div>
                        <div class="label">Services OK</div>
                    </div>
                    <div class="summary-item">
                        <div class="value error">{status['summary']['errors']}</div>
                        <div class="label">Erreurs</div>
                    </div>
                    <div class="summary-item">
                        <div class="value">{status['summary']['total']}</div>
                        <div class="label">Total</div>
                    </div>
                </div>
            </div>
            
            <table>
                <thead>
                    <tr>
                        <th>Service</th>
                        <th>Statut</th>
                        <th>Message</th>
                        <th>Temps</th>
                    </tr>
                </thead>
                <tbody>
                    {services_html}
                </tbody>
            </table>
            
            <div class="refresh-info">
                🔄 Auto-refresh toutes les 30 secondes
            </div>
        </div>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html)
