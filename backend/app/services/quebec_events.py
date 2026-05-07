"""
🎉 ÉVÉNEMENTS QUÉBEC/CANADA - CALENDRIER FÉMININ
================================================
Détection automatique des événements pour publications ciblées.

Utilisé par tous les crons:
- blog_cron.py
- facebook_cron.py
- magazine_cron.py
- content generation

V1.0 - Mai 2026
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import calendar


# ============================================
# 📅 ÉVÉNEMENTS FÉMININS QUÉBEC/CANADA
# ============================================

QUEBEC_FEMININE_EVENTS = {
    # === JANVIER ===
    "new_year": {
        "name": "Nouvel An",
        "name_en": "New Year",
        "dates": [(1, 1), (1, 2)],  # 1-2 janvier
        "themes": ["résolutions beauté", "nouveau départ capillaire", "transformation 2026"],
        "hashtags": ["#NouvelAn", "#Résolutions2026", "#NouveauDépart"],
        "content_ideas": [
            "Nouvelle année, nouvelle chevelure : 5 résolutions beauté",
            "Commencez 2026 avec des cheveux de rêve",
            "Résolution #1 : Enfin avoir les cheveux longs que vous méritez",
        ],
        "image_context": "glamorous woman celebrating New Year's Eve party",
        "priority": "high",
    },
    
    # === FÉVRIER ===
    "valentines": {
        "name": "Saint-Valentin",
        "name_en": "Valentine's Day",
        "dates": [(2, 14)],
        "pre_event_days": 7,  # Commencer 7 jours avant
        "themes": ["romantique", "date night", "séduction", "couple goals"],
        "hashtags": ["#SaintValentin", "#DateNight", "#LoveIsInTheHair"],
        "content_ideas": [
            "Saint-Valentin : Les coiffures qui font craquer",
            "Date night parfaite : Extensions pour une soirée inoubliable",
            "Son regard quand il vous voit avec VOS nouveaux cheveux 😍",
            "Le cadeau qu'elle veut vraiment : Des cheveux de rêve",
        ],
        "image_context": "romantic couple dinner, woman with gorgeous long hair",
        "priority": "high",
    },
    
    # === MARS ===
    "womens_day": {
        "name": "Journée internationale des femmes",
        "name_en": "International Women's Day",
        "dates": [(3, 8)],
        "pre_event_days": 3,
        "themes": ["empowerment féminin", "confiance", "célébration femmes"],
        "hashtags": ["#JournéeDesFemmes", "#GirlPower", "#WomenEmpowerment"],
        "content_ideas": [
            "Célébrez votre féminité : Vous méritez de vous sentir belle",
            "Journée des femmes : Investissez en VOUS",
            "Femmes inspirantes du Québec et leurs cheveux de rêve",
        ],
        "image_context": "confident empowered women group, beautiful hair",
        "priority": "medium",
    },
    
    # === AVRIL ===
    "easter": {
        "name": "Pâques",
        "name_en": "Easter",
        "dates": "easter_sunday",  # Calculé dynamiquement
        "pre_event_days": 5,
        "themes": ["brunch familial", "printemps", "renouveau"],
        "hashtags": ["#Pâques", "#BrunchPâques", "#Printemps"],
        "content_ideas": [
            "Brunch de Pâques : Soyez la plus belle de la famille",
            "Printemps = Renouveau capillaire",
            "Photos de Pâques parfaites avec des cheveux parfaits",
        ],
        "image_context": "elegant woman at Easter brunch, spring flowers",
        "priority": "medium",
    },
    
    # === MAI ===
    "mothers_day": {
        "name": "Fête des Mères",
        "name_en": "Mother's Day",
        "dates": "mothers_day_ca",  # 2e dimanche de mai
        "pre_event_days": 14,  # 2 semaines avant!
        "themes": ["cadeau maman", "mère-fille", "gratitude", "spa day"],
        "hashtags": ["#FêteDesMères", "#MerciMaman", "#MomGoals", "#CadeauMaman"],
        "content_ideas": [
            "🎁 Le cadeau parfait pour maman : Des cheveux de star",
            "Fête des Mères : Offrez-lui la transformation qu'elle mérite",
            "Duo mère-fille : Extensions pour les deux! 💕",
            "Maman mérite de se sentir BELLE",
            "Idée cadeau Fête des Mères : Certificat-cadeau Luxura",
        ],
        "image_context": "mother and daughter together, both with beautiful long hair, spa day, celebration",
        "priority": "critical",  # TRÈS IMPORTANT
    },
    
    # === JUIN ===
    "saint_jean": {
        "name": "Saint-Jean-Baptiste (Fête nationale)",
        "name_en": "Quebec National Day",
        "dates": [(6, 24)],
        "pre_event_days": 7,
        "themes": ["fierté québécoise", "été", "festival", "party"],
        "hashtags": ["#SaintJean", "#FêteNationale", "#Québec", "#24Juin"],
        "content_ideas": [
            "Saint-Jean : Brillez sur les Plaines! 🎆",
            "Fête nationale : Cheveux de feu pour le feu de joie",
            "Party de la Saint-Jean avec des cheveux PARFAITS",
            "Fierté québécoise, cheveux de déesse",
        ],
        "image_context": "woman at outdoor Quebec festival, summer party, fireworks",
        "priority": "high",
    },
    "summer_weddings": {
        "name": "Saison des mariages",
        "name_en": "Wedding Season",
        "dates": [(6, 1), (6, 30)],  # Tout juin
        "themes": ["mariée", "demoiselle d'honneur", "invitée mariage"],
        "hashtags": ["#MariageQuébec", "#Mariée2026", "#WeddingHair"],
        "content_ideas": [
            "Mariée 2026 : Extensions pour le plus beau jour de votre vie",
            "Demoiselle d'honneur : Brillez sans voler la vedette",
            "Invitée à un mariage? Voici LE secret",
        ],
        "image_context": "bride with stunning long hair, wedding venue Quebec",
        "priority": "high",
    },
    
    # === JUILLET ===
    "canada_day": {
        "name": "Fête du Canada",
        "name_en": "Canada Day",
        "dates": [(7, 1)],
        "pre_event_days": 3,
        "themes": ["célébration", "été canadien", "feux d'artifice"],
        "hashtags": ["#FêteDuCanada", "#CanadaDay", "#1erJuillet"],
        "content_ideas": [
            "Fête du Canada : Rouge et blanc, cheveux parfaits!",
            "Célébrez le Canada avec style",
        ],
        "image_context": "woman at Canada Day celebration, fireworks, red and white",
        "priority": "medium",
    },
    "festival_jazz": {
        "name": "Festival de Jazz de Montréal",
        "name_en": "Montreal Jazz Festival",
        "dates": [(7, 1), (7, 10)],  # Approximatif
        "themes": ["festival", "Montréal", "musique", "terrasse"],
        "hashtags": ["#FestivalJazz", "#JazzMTL", "#Montréal"],
        "content_ideas": [
            "Festival de Jazz : Les coiffures qui font jaser",
            "Soirées jazz avec des cheveux qui swinguent",
        ],
        "image_context": "woman at outdoor jazz concert Montreal, summer evening",
        "priority": "medium",
    },
    
    # === AOÛT ===
    "back_to_school": {
        "name": "Rentrée scolaire",
        "name_en": "Back to School",
        "dates": [(8, 15), (8, 31)],
        "themes": ["rentrée", "nouveau look", "confiance"],
        "hashtags": ["#Rentrée2026", "#BackToSchool", "#NouveauLook"],
        "content_ideas": [
            "Rentrée : Nouveau look, nouvelle confiance",
            "Première journée d'école avec des cheveux WOW",
            "Enseignantes : Vous méritez aussi de vous sentir belles!",
        ],
        "image_context": "confident woman ready for fall, new look transformation",
        "priority": "medium",
    },
    
    # === SEPTEMBRE ===
    "labor_day": {
        "name": "Fête du Travail",
        "name_en": "Labour Day",
        "dates": "labor_day_ca",  # 1er lundi de septembre
        "themes": ["fin été", "long weekend", "dernière terrasse"],
        "hashtags": ["#FêteDuTravail", "#LongWeekend", "#FinDÉté"],
        "content_ideas": [
            "Dernier long weekend d'été : Profitez avec style!",
            "Bye bye été, bonjour cheveux d'automne",
        ],
        "image_context": "woman enjoying last summer weekend, terrace sunset",
        "priority": "low",
    },
    
    # === OCTOBRE ===
    "thanksgiving_ca": {
        "name": "Action de grâce",
        "name_en": "Thanksgiving",
        "dates": "thanksgiving_ca",  # 2e lundi d'octobre
        "pre_event_days": 7,
        "themes": ["famille", "gratitude", "automne", "souper familial"],
        "hashtags": ["#ActionDeGrâce", "#Thanksgiving", "#AutomneQuébec"],
        "content_ideas": [
            "Action de grâce : Soyez la star du souper familial",
            "Photos de famille parfaites avec des cheveux parfaits",
            "Gratitude pour... mes nouveaux cheveux! 💁‍♀️",
        ],
        "image_context": "family dinner, woman with beautiful fall hair, autumn decor",
        "priority": "medium",
    },
    "halloween": {
        "name": "Halloween",
        "name_en": "Halloween",
        "dates": [(10, 31)],
        "pre_event_days": 14,
        "themes": ["costume", "party", "glamour halloween"],
        "hashtags": ["#Halloween", "#HalloweenQuébec", "#CostumeGlamour"],
        "content_ideas": [
            "Halloween glamour : Sorcière sexy avec des cheveux de rêve",
            "Costume + Extensions = Transformation COMPLÈTE",
            "Party d'Halloween : Votre meilleur look ever",
        ],
        "image_context": "glamorous woman in Halloween costume, long dramatic hair",
        "priority": "medium",
    },
    
    # === NOVEMBRE ===
    "black_friday": {
        "name": "Vendredi Fou / Black Friday",
        "name_en": "Black Friday",
        "dates": "black_friday",  # 4e vendredi de novembre
        "pre_event_days": 7,
        "themes": ["rabais", "shopping", "investissement beauté"],
        "hashtags": ["#VendrediFou", "#BlackFriday", "#Rabais"],
        "content_ideas": [
            "🔥 VENDREDI FOU : Les extensions dont vous rêvez EN RABAIS",
            "Black Friday : Investissez en VOUS",
            "Offres exclusives Luxura - 24h seulement!",
        ],
        "image_context": "excited woman shopping, holding shopping bags, beautiful hair",
        "priority": "critical",
    },
    
    # === DÉCEMBRE ===
    "christmas_party": {
        "name": "Partys de Noël",
        "name_en": "Christmas Parties",
        "dates": [(12, 1), (12, 23)],
        "themes": ["party bureau", "famille", "glamour fêtes"],
        "hashtags": ["#PartyDeNoël", "#TempsDesFêtes", "#GlamourFêtes"],
        "content_ideas": [
            "Party de bureau : Soyez celle dont tout le monde parle",
            "Temps des Fêtes : Brillez plus que le sapin! ✨",
            "Guide coiffure pour TOUS vos partys de décembre",
        ],
        "image_context": "glamorous woman at Christmas party, festive decorations, elegant dress",
        "priority": "high",
    },
    "christmas": {
        "name": "Noël",
        "name_en": "Christmas",
        "dates": [(12, 25)],
        "pre_event_days": 14,
        "themes": ["famille", "cadeaux", "magie Noël"],
        "hashtags": ["#Noël", "#Christmas", "#MagieDesFêtes"],
        "content_ideas": [
            "🎄 Noël : Le cadeau qu'ELLE veut vraiment",
            "Certificat-cadeau Luxura : Le hit sous le sapin",
            "Photos de Noël parfaites = cheveux parfaits",
        ],
        "image_context": "family Christmas celebration, woman with beautiful hair, Christmas tree",
        "priority": "critical",
    },
    "new_years_eve": {
        "name": "Réveillon du Jour de l'An",
        "name_en": "New Year's Eve",
        "dates": [(12, 31)],
        "pre_event_days": 7,
        "themes": ["party", "glamour", "countdown", "champagne"],
        "hashtags": ["#RéveillonNouvelAn", "#NYE", "#Glamour"],
        "content_ideas": [
            "31 décembre : Votre plus belle soirée de l'année",
            "Countdown avec des cheveux de STAR",
            "NYE glam : Extensions pour briller à minuit 🥂",
        ],
        "image_context": "glamorous woman at New Year's Eve party, champagne, sparkles, countdown",
        "priority": "high",
    },
}


# ============================================
# 📆 CALCUL DES DATES DYNAMIQUES
# ============================================

def get_easter_sunday(year: int) -> datetime:
    """Calcule la date de Pâques (algorithme de Meeus/Jones/Butcher)."""
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return datetime(year, month, day)


def get_mothers_day_ca(year: int) -> datetime:
    """2e dimanche de mai (Canada)."""
    may_first = datetime(year, 5, 1)
    first_sunday = may_first + timedelta(days=(6 - may_first.weekday()) % 7)
    if first_sunday.day == 1 and may_first.weekday() == 6:
        return first_sunday + timedelta(days=7)
    return first_sunday + timedelta(days=7)


def get_labor_day_ca(year: int) -> datetime:
    """1er lundi de septembre (Canada)."""
    sept_first = datetime(year, 9, 1)
    days_until_monday = (7 - sept_first.weekday()) % 7
    if sept_first.weekday() == 0:
        return sept_first
    return sept_first + timedelta(days=days_until_monday)


def get_thanksgiving_ca(year: int) -> datetime:
    """2e lundi d'octobre (Canada)."""
    oct_first = datetime(year, 10, 1)
    days_until_monday = (7 - oct_first.weekday()) % 7
    if oct_first.weekday() == 0:
        first_monday = oct_first
    else:
        first_monday = oct_first + timedelta(days=days_until_monday)
    return first_monday + timedelta(days=7)


def get_black_friday(year: int) -> datetime:
    """4e vendredi de novembre (lendemain de Thanksgiving US)."""
    nov_first = datetime(year, 11, 1)
    days_until_friday = (4 - nov_first.weekday()) % 7
    first_friday = nov_first + timedelta(days=days_until_friday)
    return first_friday + timedelta(days=21)  # 4e vendredi


def resolve_event_dates(event_key: str, dates_spec, year: int) -> List[datetime]:
    """Résout les dates d'un événement (statiques ou dynamiques)."""
    if isinstance(dates_spec, str):
        # Date dynamique
        if dates_spec == "easter_sunday":
            return [get_easter_sunday(year)]
        elif dates_spec == "mothers_day_ca":
            return [get_mothers_day_ca(year)]
        elif dates_spec == "labor_day_ca":
            return [get_labor_day_ca(year)]
        elif dates_spec == "thanksgiving_ca":
            return [get_thanksgiving_ca(year)]
        elif dates_spec == "black_friday":
            return [get_black_friday(year)]
    elif isinstance(dates_spec, list):
        # Dates statiques (month, day) tuples
        return [datetime(year, m, d) for m, d in dates_spec]
    return []


# ============================================
# 🎯 DÉTECTION ÉVÉNEMENTS ACTUELS
# ============================================

def get_current_events(lookahead_days: int = 14) -> List[Dict]:
    """
    Retourne les événements actifs ou à venir dans les X prochains jours.
    
    Args:
        lookahead_days: Nombre de jours à regarder en avance
    
    Returns:
        Liste d'événements triés par priorité et proximité
    """
    today = datetime.now()
    year = today.year
    
    active_events = []
    
    for event_key, event_data in QUEBEC_FEMININE_EVENTS.items():
        dates = resolve_event_dates(event_key, event_data["dates"], year)
        pre_days = event_data.get("pre_event_days", 3)
        
        for event_date in dates:
            # Calculer la fenêtre active (pre_event_days avant jusqu'à 1 jour après)
            start_window = event_date - timedelta(days=pre_days)
            end_window = event_date + timedelta(days=1)
            
            # Vérifier si on est dans la fenêtre ou si l'événement est dans lookahead
            if start_window <= today <= end_window:
                days_until = (event_date - today).days
                active_events.append({
                    **event_data,
                    "key": event_key,
                    "event_date": event_date,
                    "days_until": days_until,
                    "is_active": True,
                })
            elif today < start_window <= today + timedelta(days=lookahead_days):
                days_until = (event_date - today).days
                active_events.append({
                    **event_data,
                    "key": event_key,
                    "event_date": event_date,
                    "days_until": days_until,
                    "is_active": False,
                })
    
    # Trier par priorité puis par proximité
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    active_events.sort(key=lambda x: (priority_order.get(x["priority"], 99), x["days_until"]))
    
    return active_events


def get_next_event() -> Optional[Dict]:
    """Retourne le prochain événement le plus important."""
    events = get_current_events(lookahead_days=30)
    return events[0] if events else None


def get_event_content_for_today() -> Optional[Dict]:
    """
    Retourne le contenu suggéré pour aujourd'hui basé sur les événements.
    
    Returns:
        Dict avec title_suggestion, content_ideas, hashtags, image_context
    """
    events = get_current_events(lookahead_days=7)
    
    if not events:
        return None
    
    # Prendre l'événement le plus prioritaire
    event = events[0]
    
    import random
    
    return {
        "event_name": event["name"],
        "event_key": event["key"],
        "days_until": event["days_until"],
        "is_today": event["days_until"] == 0,
        "title_suggestion": random.choice(event["content_ideas"]),
        "all_content_ideas": event["content_ideas"],
        "themes": event["themes"],
        "hashtags": event["hashtags"],
        "image_context": event["image_context"],
        "priority": event["priority"],
    }


# ============================================
# 📊 RAPPORT ÉVÉNEMENTS
# ============================================

def print_upcoming_events(days: int = 60):
    """Affiche les événements à venir."""
    events = get_current_events(lookahead_days=days)
    
    print(f"\n📅 ÉVÉNEMENTS QUÉBEC/CANADA - Prochains {days} jours")
    print("=" * 60)
    
    if not events:
        print("Aucun événement majeur dans cette période.")
        return
    
    for event in events:
        status = "🔴 ACTIF" if event["is_active"] else f"⏳ Dans {event['days_until']}j"
        priority_emoji = {"critical": "🔥", "high": "⭐", "medium": "📌", "low": "📍"}.get(event["priority"], "")
        
        print(f"\n{priority_emoji} {event['name']} ({event['event_date'].strftime('%d %B')})")
        print(f"   Status: {status}")
        print(f"   Idée: {event['content_ideas'][0]}")
        print(f"   Hashtags: {' '.join(event['hashtags'][:3])}")


# ============================================
# TEST
# ============================================

if __name__ == "__main__":
    print("=" * 60)
    print("🎉 CALENDRIER ÉVÉNEMENTS LUXURA")
    print("=" * 60)
    
    # Test Mother's Day
    year = datetime.now().year
    mothers_day = get_mothers_day_ca(year)
    print(f"\n👩 Fête des Mères {year}: {mothers_day.strftime('%A %d %B')}")
    
    # Événements actuels
    print_upcoming_events(60)
    
    # Contenu suggéré pour aujourd'hui
    print("\n" + "=" * 60)
    print("📝 CONTENU SUGGÉRÉ POUR AUJOURD'HUI:")
    print("=" * 60)
    
    content = get_event_content_for_today()
    if content:
        print(f"\n🎯 Événement: {content['event_name']}")
        print(f"📅 Dans: {content['days_until']} jours")
        print(f"💡 Titre suggéré: {content['title_suggestion']}")
        print(f"🏷️ Hashtags: {' '.join(content['hashtags'])}")
        print(f"📸 Image: {content['image_context']}")
    else:
        print("Pas d'événement majeur cette semaine.")
