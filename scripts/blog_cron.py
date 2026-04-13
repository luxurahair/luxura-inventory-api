#!/usr/bin/env python3
"""
LUXURA BLOG CRON v1
===================
Cron dédié à la génération automatique de blogs SEO.
Séparé du sync Wix pour plus de flexibilité.

Fonctionnement:
1. Vérifie si c'est l'heure de publication (calendrier éditorial)
2. Génère un blog en mode BROUILLON sur Wix
3. Envoie un email d'approbation
4. Ne publie PAS automatiquement

=== CONFIGURATION RENDER CRON JOB ===

Build Command: pip install requests
Start Command: python scripts/blog_cron.py
Schedule: 0 7,12,19 * * * (7h, 12h, 19h Montréal)

=== VARIABLES D'ENVIRONNEMENT (CRON) ===

API_URL = https://luxura-inventory-api.onrender.com

=== VARIABLES REQUISES SUR L'API luxura-inventory-api ===
(Ces variables doivent être sur le service API, pas sur le cron)

- EMERGENT_LLM_KEY ou OPENAI_API_KEY : Pour générer le contenu du blog
- WIX_API_KEY : Token OAuth Wix pour créer les brouillons
- WIX_SITE_ID : ID de votre site Wix
- LUXURA_APP_USER : Email Gmail pour envoyer les approbations
- LUXURA_APP_PASSWORD : Mot de passe app Gmail
- BLOG_APPROVAL_EMAIL : Email qui recevra les demandes d'approbation

"""

import os
import sys
import requests
from datetime import datetime

# Configuration
API_URL = os.getenv("API_URL", "https://luxura-inventory-api.onrender.com").rstrip("/")

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
    """Retourne le planning du jour"""
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
            "description": schedule["desc"]
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


def generate_blog(category):
    """Appelle l'API pour générer un blog"""
    log(f"📝 Génération blog catégorie: {category}")
    
    url = f"{API_URL}/api/blog/auto-generate"
    
    payload = {
        "count": 1,
        "publish_to_wix": True,       # Crée brouillon Wix
        "publish_to_facebook": False,  # PAS de publication FB auto
        "category": category
    }
    
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
    log("🚀 LUXURA BLOG CRON v1")
    log(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    log(f"🕐 Heure Montréal: {get_montreal_hour()}h")
    log(f"📆 Jour: {get_current_day().capitalize()}")
    log(f"🔄 Semaine: {get_rotation_week()}/2")
    log(f"🌐 API: {API_URL}")
    log("=" * 60)
    
    if schedule:
        log(f"📋 Planning du jour:")
        log(f"   - Heure cible: {schedule['hour']}h")
        log(f"   - Catégorie: {schedule['category']}")
        log(f"   - Sujet: {schedule['description']}")
    else:
        log("⚠️ Pas de planning trouvé pour aujourd'hui")
        sys.exit(0)
    
    # Vérifier si c'est l'heure
    if should_generate_now(schedule):
        log("")
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
