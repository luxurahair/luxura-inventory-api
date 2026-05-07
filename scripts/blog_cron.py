#!/usr/bin/env python3
"""
LUXURA BLOG CRON v2 - ÉVÉNEMENTS QUÉBEC
=======================================
Cron dédié à la génération automatique de blogs SEO.
Intègre maintenant les ÉVÉNEMENTS QUÉBEC/CANADA féminins.

V2 NOUVEAUTÉS:
- Détection automatique des événements (Fête des Mères, Saint-Jean, etc.)
- Priorité aux événements CRITIQUES sur le calendrier éditorial
- Contenu adapté aux occasions féminines québécoises

Fonctionnement:
1. Vérifie si un événement CRITIQUE est actif
2. Si oui: génère du contenu événementiel
3. Sinon: suit le calendrier éditorial normal
4. Envoie un email d'approbation

=== CONFIGURATION RENDER CRON JOB ===

Build Command: pip install requests
Start Command: python scripts/blog_cron.py
Schedule: 0 11,16,23 * * * (11h, 16h, 23h UTC = 7h, 12h, 19h Montréal)

"""

import os
import sys
import requests
from datetime import datetime

# Configuration
API_URL = os.getenv("API_URL", "https://luxura-inventory-api.onrender.com").rstrip("/")

# =====================================================
# 🎉 ÉVÉNEMENTS QUÉBEC - PRIORITÉ HAUTE
# =====================================================

# Import du module événements (sera disponible via l'API)
def get_current_event_from_api():
    """Récupère l'événement actuel depuis l'API."""
    try:
        resp = requests.get(f"{API_URL}/api/events/current", timeout=30)
        if resp.status_code == 200:
            return resp.json()
    except:
        pass
    return None


# Événements hardcodés comme fallback
QUEBEC_EVENTS_FALLBACK = {
    # Format: (month, day_start, day_end): event_config
    (5, 1, 15): {  # 1-15 mai = Fête des Mères
        "name": "Fête des Mères",
        "category": "fete_meres",
        "priority": "critical",
        "themes": ["cadeau maman", "mère-fille", "spa day"],
        "hashtags": ["#FêteDesMères", "#MerciMaman", "#CadeauMaman"],
    },
    (6, 17, 25): {  # 17-25 juin = Saint-Jean
        "name": "Saint-Jean-Baptiste",
        "category": "saint_jean",
        "priority": "high",
        "themes": ["fierté québécoise", "été", "festival"],
        "hashtags": ["#SaintJean", "#FêteNationale", "#Québec"],
    },
    (6, 1, 30): {  # Juin = Mariages
        "name": "Saison des mariages",
        "category": "mariages",
        "priority": "high",
        "themes": ["mariée", "demoiselle d'honneur"],
        "hashtags": ["#MariageQuébec", "#Mariée2026"],
    },
    (12, 1, 24): {  # Décembre = Noël/Partys
        "name": "Temps des Fêtes",
        "category": "fetes",
        "priority": "critical",
        "themes": ["party", "famille", "cadeaux"],
        "hashtags": ["#TempsDesFêtes", "#Noël"],
    },
    (2, 7, 14): {  # 7-14 février = Saint-Valentin
        "name": "Saint-Valentin",
        "category": "saint_valentin",
        "priority": "high",
        "themes": ["romantique", "date night"],
        "hashtags": ["#SaintValentin", "#DateNight"],
    },
}


def check_active_event():
    """Vérifie si un événement est actif."""
    today = datetime.now()
    month = today.month
    day = today.day
    
    for (m, d_start, d_end), event in QUEBEC_EVENTS_FALLBACK.items():
        if month == m and d_start <= day <= d_end:
            return event
    
    return None


# =====================================================
# CALENDRIER ÉDITORIAL - FEMMES QUÉBEC
# =====================================================

# Heures de publication par jour (heure Montréal)
PEAK_HOURS = {
    "monday": 7,
    "tuesday": 12,
    "wednesday": 19,
    "thursday": 7,
    "friday": 12,
    "saturday": 10,
    "sunday": 20,
}

# Rotation sur 2 semaines
EDITORIAL_ROTATION = {
    # Semaine 1 (impaire)
    1: {
        "monday": {"category": "transformation", "desc": "Transformation capillaire"},
        "tuesday": {"category": "cheveux_fins", "desc": "Solutions cheveux fins"},
        "wednesday": {"category": "comparatif", "desc": "Comparatif méthodes"},
        "thursday": {"category": "b2b_salon", "desc": "B2B Salons partenaires"},
        "friday": {"category": "tendances", "desc": "Tendances coiffure"},
        "saturday": {"category": "inspiration", "desc": "Inspiration weekend"},
        "sunday": {"category": "temoignages", "desc": "Témoignages clientes"},
    },
    # Semaine 2 (paire)
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
    """Log avec timestamp"""
    print(f"[BLOG CRON] {datetime.now().strftime('%H:%M:%S')} {msg}")


def get_montreal_hour():
    """Retourne l'heure actuelle à Montréal"""
    utc_hour = datetime.utcnow().hour
    utc_month = datetime.utcnow().month
    # Heure d'été (mars-oct): UTC-4, Heure d'hiver: UTC-5
    offset = -4 if 3 <= utc_month <= 10 else -5
    return (utc_hour + offset) % 24


def get_current_day():
    """Retourne le jour en anglais"""
    days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    return days[datetime.utcnow().weekday()]


def get_rotation_week():
    """Retourne 1 ou 2 selon la semaine"""
    week_num = datetime.utcnow().isocalendar()[1]
    return 1 if week_num % 2 == 1 else 2


def get_todays_schedule():
    """
    Retourne le planning du jour.
    PRIORITÉ: Événements Québec > Calendrier éditorial
    """
    # 1. Vérifier si un événement CRITIQUE est actif
    active_event = check_active_event()
    
    if active_event and active_event.get("priority") in ["critical", "high"]:
        log(f"🎉 ÉVÉNEMENT ACTIF: {active_event['name']}")
        return {
            "day": get_current_day(),
            "week": get_rotation_week(),
            "hour": PEAK_HOURS.get(get_current_day(), 12),
            "category": active_event["category"],
            "description": f"🎉 {active_event['name']}",
            "is_event": True,
            "event_data": active_event
        }
    
    # 2. Sinon, calendrier éditorial normal
    day = get_current_day()
    week = get_rotation_week()
    hour = PEAK_HOURS.get(day, 12)
    schedule = EDITORIAL_ROTATION.get(week, {}).get(day)
    
    if schedule:
        return {
            "day": day,
            "week": week,
            "hour": hour,
            "category": schedule["category"],
            "description": schedule["desc"],
            "is_event": False
        }
    return None


def should_generate_now(schedule):
    """Vérifie si c'est l'heure de publier"""
    if not schedule:
        return False
    
    current_hour = get_montreal_hour()
    target_hour = schedule["hour"]
    
    # Tolérance de +/- 1 heure
    return abs(current_hour - target_hour) <= 1


def generate_blog(category, event_data=None):
    """Appelle l'API pour générer un blog"""
    if event_data:
        log(f"🎉 Génération blog ÉVÉNEMENT: {event_data.get('name', category)}")
        log(f"   Thèmes: {', '.join(event_data.get('themes', []))}")
        log(f"   Hashtags: {' '.join(event_data.get('hashtags', []))}")
    else:
        log(f"📝 Génération blog catégorie: {category}")
    
    url = f"{API_URL}/api/blog/auto-generate"
    
    payload = {
        "count": 1,
        "publish_to_wix": True,       # Crée brouillon Wix
        "publish_to_facebook": False,  # PAS de publication FB auto
        "category": category
    }
    
    # Ajouter les données événement si disponibles
    if event_data:
        payload["event_name"] = event_data.get("name")
        payload["event_themes"] = event_data.get("themes", [])
        payload["event_hashtags"] = event_data.get("hashtags", [])
    
    try:
        resp = requests.post(url, json=payload, timeout=300)
        
        if resp.status_code == 200:
            data = resp.json()
            posts = data.get("posts", [])
            
            if posts:
                log("✅ Blog généré avec succès!")
                for post in posts:
                    log(f"   📄 {post.get('title', 'Sans titre')[:60]}...")
                    if post.get("wix_post_id"):
                        log(f"   🔗 Brouillon Wix: {post.get('wix_post_id')}")
                log("")
                log("📧 EMAIL D'APPROBATION ENVOYÉ!")
                log("   Vérifiez votre boîte mail pour approuver.")
                return True
            else:
                log("⚠️ Aucun blog généré (titre peut-être existant)")
                return True
        else:
            log(f"❌ Erreur API: {resp.status_code}")
            log(resp.text[:300])
            return False
            
    except requests.exceptions.Timeout:
        log("❌ Timeout (5 min)")
        return False
    except Exception as e:
        log(f"❌ Erreur: {e}")
        return False


def main():
    """Point d'entrée principal"""
    schedule = get_todays_schedule()
    
    log("=" * 60)
    log("🚀 LUXURA BLOG CRON v2 - ÉVÉNEMENTS QUÉBEC")
    log(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    log(f"🕐 Heure Montréal: {get_montreal_hour()}h")
    log(f"📆 Jour: {get_current_day().capitalize()}")
    log(f"🔄 Semaine: {get_rotation_week()}/2")
    log(f"🌐 API: {API_URL}")
    log("=" * 60)
    
    if schedule:
        if schedule.get("is_event"):
            log(f"🎉 ÉVÉNEMENT DÉTECTÉ: {schedule['description']}")
            log(f"   - Priorité: HAUTE (override calendrier)")
        else:
            log(f"📋 Planning du jour (calendrier éditorial):")
        log(f"   - Heure cible: {schedule['hour']}h")
        log(f"   - Catégorie: {schedule['category']}")
        log(f"   - Sujet: {schedule['description']}")
    else:
        log("⚠️ Pas de planning trouvé pour aujourd'hui")
        sys.exit(0)
    
    # Vérifier si c'est l'heure
    if should_generate_now(schedule):
        log("")
        if schedule.get("is_event"):
            log(f"🎉 GÉNÉRATION ÉVÉNEMENT: {schedule['description']}")
            generate_blog(schedule["category"], event_data=schedule.get("event_data"))
        else:
            log(f"✅ C'est l'heure de publication!")
            generate_blog(schedule["category"])
    else:
        log("")
        log(f"⏰ Pas l'heure de publication")
        log(f"   Heure actuelle: {get_montreal_hour()}h")
        log(f"   Heure prévue: {schedule['hour']}h")
    
    log("")
    log("=" * 60)
    log("✅ CRON TERMINÉ")
    log("=" * 60)
    
    sys.exit(0)


if __name__ == "__main__":
    main()
