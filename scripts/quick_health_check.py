#!/usr/bin/env python3
"""
🏥 QUICK HEALTH CHECK
=====================
Vérifie rapidement si l'API Luxura est en ligne.
Utilisé par les crons Render avant d'exécuter leurs tâches.
"""

import httpx
import sys
import os

API_URL = os.getenv("RENDER_SERVICE_URL", "https://luxura-inventory-api.onrender.com")

def main():
    try:
        with httpx.Client(timeout=10) as client:
            response = client.get(f"{API_URL}/api/health")
            if response.status_code == 200:
                print(f"✅ API is healthy: {response.json()}")
                return 0
            else:
                print(f"⚠️ API returned {response.status_code}")
                return 1
    except Exception as e:
        print(f"❌ API is DOWN: {e}")
        return 2

if __name__ == "__main__":
    sys.exit(main())
