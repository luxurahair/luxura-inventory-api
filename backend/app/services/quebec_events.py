"""
🎉 ÉVÉNEMENTS QUÉBEC/CANADA - CALENDRIER FÉMININ 2026
=====================================================
Détection automatique des événements pour publications ciblées.

DATES CLÉS 2026:
- Fête des Mères: 10 mai 2026
- Pâques: 5 avril 2026
- Saint-Jean: 24 juin 2026
- Action de grâce: 12 octobre 2026
- Black Friday: 27 novembre 2026

V2.0 - Mai 2026 - Dates exactes calculées
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import calendar


# ============================================
# 📅 ÉVÉNEMENTS FÉMININS QUÉBEC/CANADA 2026
# Dates exactes et fenêtres de publication
# ============================================

QUEBEC_FEMININE_EVENTS = {
    # === JANVIER ===
    "new_year": {
        "name": "Nouvel An",
        "date_2026": (1, 1),
        "window_before": 3,  # jours avant pour commencer
        "window_after": 2,   # jours après
        "themes": ["résolutions beauté", "nouveau départ", "transformation"],
        "hashtags": ["#NouvelAn", "#Résolutions2026", "#NouveauDépart"],
        "content_ideas": [
            "Nouvelle année, nouvelle chevelure : Vos résolutions beauté",
            "2026 : L'année où vous aurez ENFIN les cheveux de vos rêves",
        ],
        "priority": "high",
    },
    
    # === FÉVRIER ===
    "valentines": {
        "name": "Saint-Valentin",
        "date_2026": (2, 14),
        "window_before": 10,
        "window_after": 0,
        "themes": ["romantique", "date night", "séduction"],
        "hashtags": ["#SaintValentin", "#DateNight", "#LoveIsInTheHair"],
        "content_ideas": [
            "Saint-Valentin : Les cheveux qui font craquer",
            "Date night parfaite : Soyez irrésistible",
            "Le cadeau qu'ELLE veut vraiment 💕",
        ],
        "priority": "high",
    },
    
    # === MARS ===
    "womens_day": {
        "name": "Journée internationale des femmes",
        "date_2026": (3, 8),
        "window_before": 5,
        "window_after": 1,
        "themes": ["empowerment", "confiance", "célébration"],
        "hashtags": ["#JournéeDesFemmes", "#8Mars", "#GirlPower"],
        "content_ideas": [
            "Célébrez VOUS : Journée internationale des femmes",
            "Investissez en vous-même 💪",
        ],
        "priority": "medium",
    },
    "spring_break": {
        "name": "Semaine de relâche",
        "date_2026": (3, 2),  # Début mars généralement
        "window_before": 7,
        "window_after": 7,
        "themes": ["vacances", "voyage", "Sud"],
        "hashtags": ["#SemaineDeRelâche", "#Vacances", "#AllInclusive"],
        "content_ideas": [
            "Semaine de relâche : Extensions waterproof pour le Sud",
            "All-inclusive ready : Vos cheveux aussi!",
        ],
        "priority": "medium",
    },
    
    # === AVRIL ===
    "easter": {
        "name": "Pâques",
        "date_2026": (4, 5),  # Dimanche de Pâques 2026
        "window_before": 7,
        "window_after": 1,
        "themes": ["brunch", "famille", "printemps"],
        "hashtags": ["#Pâques", "#BrunchPâques", "#Printemps"],
        "content_ideas": [
            "Brunch de Pâques : Soyez la plus belle",
            "Printemps = Renouveau capillaire",
        ],
        "priority": "medium",
    },
    
    # === MAI ===
    "mothers_day": {
        "name": "Fête des Mères",
        "date_2026": (5, 10),  # 2e dimanche de mai 2026
        "window_before": 14,  # 2 semaines avant!
        "window_after": 0,
        "themes": ["cadeau maman", "mère-fille", "spa", "gratitude"],
        "hashtags": ["#FêteDesMères", "#MerciMaman", "#CadeauMaman", "#MèreFille"],
        "content_ideas": [
            "🎁 Le cadeau parfait pour maman",
            "Duo mère-fille : Extensions pour les deux! 💕",
            "Certificat-cadeau Luxura : LE hit de la Fête des Mères",
            "Maman mérite de se sentir BELLE",
        ],
        "priority": "critical",
    },
    
    # === JUIN ===
    "grad_season": {
        "name": "Saison des graduations",
        "date_2026": (6, 1),
        "window_before": 0,
        "window_after": 20,
        "themes": ["graduation", "bal", "célébration"],
        "hashtags": ["#Graduation2026", "#BalDesFinissants", "#ProudGrad"],
        "content_ideas": [
            "Graduation 2026 : Vos cheveux de rêve pour le grand jour",
            "Bal des finissants : Brillez!",
        ],
        "priority": "medium",
    },
    "saint_jean": {
        "name": "Saint-Jean-Baptiste",
        "date_2026": (6, 24),
        "window_before": 7,
        "window_after": 1,
        "themes": ["fierté québécoise", "festival", "été"],
        "hashtags": ["#SaintJean", "#FêteNationale", "#24Juin", "#Québec"],
        "content_ideas": [
            "Saint-Jean : Brillez sur les Plaines! 🎆",
            "Fierté québécoise, cheveux de déesse",
            "Party de la Saint-Jean : Look parfait",
        ],
        "priority": "high",
    },
    "wedding_season": {
        "name": "Saison des mariages",
        "date_2026": (6, 1),
        "window_before": 0,
        "window_after": 90,  # Juin-Juillet-Août
        "themes": ["mariée", "demoiselle d'honneur", "invitée"],
        "hashtags": ["#Mariage2026", "#Mariée", "#WeddingHair"],
        "content_ideas": [
            "Mariée 2026 : Vos cheveux de rêve",
            "Demoiselle d'honneur : Brillez sans voler la vedette",
        ],
        "priority": "high",
    },
    
    # === JUILLET ===
    "canada_day": {
        "name": "Fête du Canada",
        "date_2026": (7, 1),
        "window_before": 3,
        "window_after": 1,
        "themes": ["célébration", "été", "feux d'artifice"],
        "hashtags": ["#FêteDuCanada", "#CanadaDay", "#1erJuillet"],
        "content_ideas": [
            "Fête du Canada : Rouge, blanc et cheveux parfaits!",
        ],
        "priority": "low",
    },
    "festival_jazz": {
        "name": "Festival de Jazz MTL",
        "date_2026": (6, 25),  # Fin juin - début juillet
        "window_before": 7,
        "window_after": 10,
        "themes": ["festival", "Montréal", "été"],
        "hashtags": ["#FestivalJazz", "#JazzMTL", "#Montréal"],
        "content_ideas": [
            "Festival de Jazz : Les coiffures qui font jaser",
        ],
        "priority": "medium",
    },
    "summer_festivals": {
        "name": "Été des festivals",
        "date_2026": (7, 1),
        "window_before": 0,
        "window_after": 60,
        "themes": ["festivals", "terrasses", "été"],
        "hashtags": ["#ÉtéQuébec", "#Festivals", "#Terrasse"],
        "content_ideas": [
            "Été 2026 : Vos cheveux festival-ready",
            "Du festival à la terrasse : Extensions parfaites",
        ],
        "priority": "medium",
    },
    
    # === AOÛT ===
    "back_to_school": {
        "name": "Rentrée",
        "date_2026": (8, 20),
        "window_before": 14,
        "window_after": 7,
        "themes": ["rentrée", "nouveau look", "confiance"],
        "hashtags": ["#Rentrée2026", "#NouveauLook", "#BackToSchool"],
        "content_ideas": [
            "Rentrée : Nouveau look, nouvelle confiance",
            "Première journée avec des cheveux WOW",
        ],
        "priority": "medium",
    },
    
    # === SEPTEMBRE ===
    "labor_day": {
        "name": "Fête du Travail",
        "date_2026": (9, 7),  # 1er lundi de septembre
        "window_before": 3,
        "window_after": 1,
        "themes": ["fin été", "long weekend"],
        "hashtags": ["#FêteDuTravail", "#LongWeekend"],
        "content_ideas": [
            "Dernier long weekend d'été : Profitez!",
        ],
        "priority": "low",
    },
    "fall_fashion": {
        "name": "Mode automne",
        "date_2026": (9, 15),
        "window_before": 0,
        "window_after": 30,
        "themes": ["automne", "tendances", "mode"],
        "hashtags": ["#ModeAutomne", "#FallVibes", "#Tendances"],
        "content_ideas": [
            "Tendances cheveux automne 2026",
            "Du hoodie au cocktail : Extensions polyvalentes",
        ],
        "priority": "medium",
    },
    
    # === OCTOBRE ===
    "thanksgiving_ca": {
        "name": "Action de grâce",
        "date_2026": (10, 12),  # 2e lundi d'octobre
        "window_before": 7,
        "window_after": 1,
        "themes": ["famille", "gratitude", "automne"],
        "hashtags": ["#ActionDeGrâce", "#Thanksgiving", "#Automne"],
        "content_ideas": [
            "Action de grâce : Star du souper familial",
            "Photos de famille parfaites",
        ],
        "priority": "medium",
    },
    "halloween": {
        "name": "Halloween",
        "date_2026": (10, 31),
        "window_before": 14,
        "window_after": 1,
        "themes": ["costume", "party", "glamour"],
        "hashtags": ["#Halloween", "#Costume", "#HalloweenGlam"],
        "content_ideas": [
            "Halloween glamour : Sorcière sexy",
            "Costume + Extensions = WOW",
        ],
        "priority": "medium",
    },
    
    # === NOVEMBRE ===
    "black_friday": {
        "name": "Vendredi Fou",
        "date_2026": (11, 27),  # 4e vendredi de novembre
        "window_before": 7,
        "window_after": 3,
        "themes": ["rabais", "shopping", "offres"],
        "hashtags": ["#VendrediFou", "#BlackFriday", "#Rabais"],
        "content_ideas": [
            "🔥 VENDREDI FOU : Extensions en RABAIS!",
            "Black Friday : Investissez en VOUS",
        ],
        "priority": "critical",
    },
    "cyber_monday": {
        "name": "Cyber Monday",
        "date_2026": (11, 30),
        "window_before": 1,
        "window_after": 1,
        "themes": ["rabais", "online"],
        "hashtags": ["#CyberMonday", "#Rabais"],
        "content_ideas": [
            "Cyber Monday : Dernière chance!",
        ],
        "priority": "high",
    },
    
    # === DÉCEMBRE ===
    "holiday_parties": {
        "name": "Partys des Fêtes",
        "date_2026": (12, 1),
        "window_before": 0,
        "window_after": 23,
        "themes": ["party", "bureau", "famille"],
        "hashtags": ["#PartyDesFêtes", "#TempsDesFêtes", "#Glamour"],
        "content_ideas": [
            "Party de bureau : Soyez celle dont on parle",
            "Temps des Fêtes : Brillez plus que le sapin! ✨",
        ],
        "priority": "high",
    },
    "christmas": {
        "name": "Noël",
        "date_2026": (12, 25),
        "window_before": 21,
        "window_after": 1,
        "themes": ["cadeaux", "famille", "magie"],
        "hashtags": ["#Noël", "#Cadeaux", "#MagieDesFêtes"],
        "content_ideas": [
            "🎄 Le cadeau qu'ELLE veut vraiment",
            "Certificat-cadeau : Le hit sous le sapin",
        ],
        "priority": "critical",
    },
    "new_years_eve": {
        "name": "Réveillon",
        "date_2026": (12, 31),
        "window_before": 10,
        "window_after": 1,
        "themes": ["party", "glamour", "champagne"],
        "hashtags": ["#Réveillon", "#NYE", "#Glamour2027"],
        "content_ideas": [
            "31 décembre : Votre plus belle soirée",
            "Countdown avec des cheveux de STAR 🥂",
        ],
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
# 🎯 DÉTECTION ÉVÉNEMENTS ACTUELS V2
# ============================================

def get_current_events(lookahead_days: int = 14) -> List[Dict]:
    """
    Retourne les événements actifs ou à venir dans les X prochains jours.
    
    V2: Utilise les dates exactes 2026
    """
    today = datetime.now()
    year = today.year
    
    active_events = []
    
    for event_key, event_data in QUEBEC_FEMININE_EVENTS.items():
        # Obtenir la date de l'événement
        date_spec = event_data.get("date_2026")
        if not date_spec:
            continue
            
        month, day = date_spec
        event_date = datetime(year, month, day)
        
        # Fenêtres de publication
        window_before = event_data.get("window_before", 7)
        window_after = event_data.get("window_after", 1)
        
        start_window = event_date - timedelta(days=window_before)
        end_window = event_date + timedelta(days=window_after)
        
        # Vérifier si on est dans la fenêtre active
        if start_window <= today <= end_window:
            days_until = (event_date - today).days
            active_events.append({
                **event_data,
                "key": event_key,
                "event_date": event_date,
                "days_until": days_until,
                "is_active": True,
                "is_today": days_until == 0,
                "is_past": days_until < 0,
            })
        # Ou si l'événement arrive bientôt (dans lookahead_days)
        elif today < start_window <= today + timedelta(days=lookahead_days):
            days_until = (event_date - today).days
            active_events.append({
                **event_data,
                "key": event_key,
                "event_date": event_date,
                "days_until": days_until,
                "is_active": False,
                "is_today": False,
                "is_past": False,
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
    """
    events = get_current_events(lookahead_days=7)
    
    if not events:
        return None
    
    event = events[0]
    
    import random
    
    return {
        "event_name": event["name"],
        "event_key": event["key"],
        "days_until": event["days_until"],
        "is_today": event.get("is_today", False),
        "is_active": event.get("is_active", False),
        "title_suggestion": random.choice(event["content_ideas"]),
        "all_content_ideas": event["content_ideas"],
        "themes": event["themes"],
        "hashtags": event["hashtags"],
        "priority": event["priority"],
    }


# ============================================
# 📊 RAPPORT ÉVÉNEMENTS
# ============================================

def print_upcoming_events(days: int = 60):
    """Affiche les événements à venir."""
    events = get_current_events(lookahead_days=days)
    
    print(f"\n📅 ÉVÉNEMENTS FÉMININS QUÉBEC 2026 - Prochains {days} jours")
    print("=" * 60)
    
    if not events:
        print("Aucun événement majeur dans cette période.")
        return
    
    for event in events:
        if event["is_active"]:
            if event["is_today"]:
                status = "🔴 AUJOURD'HUI!"
            elif event["is_past"]:
                status = "✅ Passé (fenêtre active)"
            else:
                status = f"🟢 ACTIF - Dans {event['days_until']}j"
        else:
            status = f"⏳ Dans {event['days_until']}j"
        
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
    print("🎉 CALENDRIER ÉVÉNEMENTS FÉMININS LUXURA 2026")
    print("=" * 60)
    
    # Afficher tous les événements de l'année
    print("\n📅 TOUS LES ÉVÉNEMENTS 2026:")
    print("-" * 60)
    
    events_by_month = {}
    for key, event in QUEBEC_FEMININE_EVENTS.items():
        date = event.get("date_2026")
        if date:
            month = date[0]
            if month not in events_by_month:
                events_by_month[month] = []
            events_by_month[month].append(event)
    
    month_names = ["", "Janvier", "Février", "Mars", "Avril", "Mai", "Juin", 
                   "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]
    
    for month in sorted(events_by_month.keys()):
        print(f"\n📆 {month_names[month].upper()}")
        for event in events_by_month[month]:
            priority_emoji = {"critical": "🔥", "high": "⭐", "medium": "📌", "low": "📍"}.get(event["priority"], "")
            date = event["date_2026"]
            print(f"   {priority_emoji} {date[1]:02d}/{date[0]:02d} - {event['name']}")
    
    # Événements actuels
    print_upcoming_events(60)
    
    # Contenu suggéré pour aujourd'hui
    print("\n" + "=" * 60)
    print("📝 CONTENU SUGGÉRÉ POUR AUJOURD'HUI:")
    print("=" * 60)
    
    content = get_event_content_for_today()
    if content:
        status = "🔴 AUJOURD'HUI!" if content['is_today'] else f"Dans {content['days_until']} jours"
        print(f"\n🎯 Événement: {content['event_name']}")
        print(f"📅 Status: {status}")
        print(f"🔥 Priorité: {content['priority'].upper()}")
        print(f"💡 Titre suggéré: {content['title_suggestion']}")
        print(f"🏷️ Hashtags: {' '.join(content['hashtags'])}")
    else:
        print("Pas d'événement majeur cette semaine.")
