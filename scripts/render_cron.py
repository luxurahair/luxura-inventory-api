#!/usr/bin/env python3
"""
LUXURA CRON COMPLET v3 - Pour Render
====================================
Script pour Render Cron Job qui fait:
1. ✅ Sync inventaire Wix → Supabase  
2. ✅ Génération de blog SELON LE CALENDRIER ÉDITORIAL
   - Mode BROUILLON avec approbation par email
   - Catégorie basée sur le jour et la semaine de rotation

CALENDRIER ÉDITORIAL (Rotation 2 semaines):
- Lundi 7h: Transformation / Entretien
- Mardi 12h: Cheveux fins / Guide
- Mercredi 19h: Comparatif / Occasions
- Jeudi 7h: B2B Salons / B2B Inventaire
- Vendredi 12h: Tendances / Couleurs
- Samedi 10h: Inspiration / Tutoriel
- Dimanche 20h: Témoignages / Self-care

Usage sur Render:
  Build Command: pip install requests python-dotenv
  Start Command: python scripts/render_cron.py
  Schedule: 0 7,10,12,19,20 * * * (heures optimales Montréal)
"""

import os
import sys
import requests
from datetime import datetime

# Configuration
API_URL = (os.getenv("API_URL") or os.getenv("LUXURA_API_URL") or "https://luxura-inventory-api.onrender.com").rstrip("/")
SEO_SECRET = (os.getenv("SEO_SECRET") or "").strip()

# =====================================================
# CALENDRIER ÉDITORIAL - FEMMES QUÉBEC
# =====================================================

PEAK_HOURS = {
    "monday": 7,
    "tuesday": 12,
    "wednesday": 19,
    "thursday": 7,
    "friday": 12,
    "saturday": 10,
    "sunday": 20,
}

EDITORIAL_ROTATION = {
    1: {
        "monday": {"category": "transformation", "desc": "Transformation capillaire"},
        "tuesday": {"category": "cheveux_fins", "desc": "Solutions cheveux fins"},
        "wednesday": {"category": "comparatif", "desc": "Comparatif méthodes"},
        "thursday": {"category": "b2b_salon", "desc": "B2B Salons partenaires"},
        "friday": {"category": "tendances", "desc": "Tendances coiffure"},
        "saturday": {"category": "inspiration", "desc": "Inspiration weekend"},
        "sunday": {"category": "temoignages", "desc": "Témoignages clientes"},
    },
    2: {
        "monday": {"category": "entretien", "desc": "Entretien extensions"},
        "tuesday": {"category": "guide", "desc": "Guide complet achat"},
        "wednesday": {"category": "occasions", "desc": "Occasions spéciales"},
        "thursday": {"category": "b2b_inventaire", "desc": "B2B Programme inventaire"},
        "friday": {"category": "couleurs", "desc": "Guide couleurs"},
        "saturday": {"category": "tutoriel", "desc": "Tutoriel coiffure"},
        "sunday": {"category": "self_care", "desc": "Self-care beauté"},
    }
}


def log(msg):
    print(f"[CRON] {datetime.now().strftime('%H:%M:%S')} {msg}")


def get_montreal_time():
    utc_hour = datetime.utcnow().hour
    utc_month = datetime.utcnow().month
    offset = -4 if 3 <= utc_month <= 10 else -5
    return (utc_hour + offset) % 24


def get_current_day():
    days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    return days[datetime.utcnow().weekday()]


def get_rotation_week():
    week_num = datetime.utcnow().isocalendar()[1]
    return 1 if week_num % 2 == 1 else 2


def get_todays_schedule():
    day = get_current_day()
    week = get_rotation_week()
    hour = PEAK_HOURS.get(day, 12)
    schedule = EDITORIAL_ROTATION.get(week, {}).get(day)
    if schedule:
        return {"day": day, "week": week, "hour": hour, "category": schedule["category"], "description": schedule["desc"]}
    return None


def sync_wix_inventory():
    log("=" * 50)
    log("📦 ÉTAPE 1: Synchronisation Inventaire Wix")
    log("=" * 50)
    
    if not SEO_SECRET:
        log("❌ SEO_SECRET manquant - sync impossible")
        return False
    
    url = f"{API_URL}/wix/sync"
    headers = {"X-SEO-SECRET": SEO_SECRET, "Accept": "application/json", "Content-Type": "application/json"}
    
    log(f"Appel de {url}...")
    
    try:
        resp = requests.post(url, headers=headers, params={"limit": 500, "dry_run": "false"}, timeout=300)
        if resp.status_code >= 400:
            log(f"❌ Erreur HTTP {resp.status_code}")
            log(resp.text[:500])
            return False
        
        data = resp.json()
        log("✅ Sync terminé avec succès!")
        log(f"   - Créés: {data.get('created', 0)}")
        log(f"   - Mis à jour: {data.get('updated', 0)}")
        log(f"   - Inventaire écrit: {data.get('inventory_written_entrepot', 0)}")
        return True
    except Exception as e:
        log(f"❌ Erreur: {e}")
        return False


def should_generate_blog():
    schedule = get_todays_schedule()
    if not schedule:
        return False, None
    
    current_hour = get_montreal_time()
    target_hour = schedule["hour"]
    
    if abs(current_hour - target_hour) <= 1:
        log(f"📰 Heure de publication! (Montréal: {current_hour}h)")
        log(f"   📅 Semaine {schedule['week']}/2 - {schedule['category']}")
        return True, schedule
    else:
        log(f"⏰ Pas l'heure de blog (Montréal: {current_hour}h, prévu: {target_hour}h)")
        return False, schedule


def generate_blog_draft(schedule):
    log("=" * 50)
    log("📝 ÉTAPE 2: Génération Blog (Calendrier Éditorial)")
    log("=" * 50)
    
    url = f"{API_URL}/api/blog/auto-generate"
    category = schedule.get("category") if schedule else None
    
    payload = {"count": 1, "publish_to_wix": True, "publish_to_facebook": False, "category": category}
    
    log(f"Catégorie: {category}")
    
    try:
        resp = requests.post(url, json=payload, timeout=300)
        if resp.status_code >= 400:
            log(f"❌ Erreur HTTP {resp.status_code}")
            return False
        
        data = resp.json()
        posts = data.get("posts", [])
        
        if posts:
            log("✅ Blog généré!")
            for post in posts:
                log(f"   📄 {post.get('title', 'Sans titre')[:50]}...")
            log("📧 EMAIL D'APPROBATION ENVOYÉ!")
        return True
    except Exception as e:
        log(f"❌ Erreur: {e}")
        return False


def main():
    schedule = get_todays_schedule()
    
    log("=" * 60)
    log("🚀 LUXURA CRON v3 - CALENDRIER ÉDITORIAL")
    log(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    log(f"🕐 Heure Montréal: {get_montreal_time()}h | Jour: {get_current_day()}")
    log(f"🔄 Semaine rotation: {get_rotation_week()}/2")
    log(f"🌐 API: {API_URL}")
    log("=" * 60)
    
    if schedule:
        log(f"📋 Planning: {schedule['hour']}h - {schedule['category']}")
    
    sync_wix_inventory()
    
    should_blog, blog_schedule = should_generate_blog()
    if should_blog:
        generate_blog_draft(blog_schedule)
    
    log("=" * 60)
    log("✅ CRON TERMINÉ")
    log("=" * 60)
    sys.exit(0)


if __name__ == "__main__":
    main()
