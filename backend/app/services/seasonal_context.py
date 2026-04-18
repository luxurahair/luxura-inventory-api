"""
Contexte saisonnier et événementiel pour Luxura Distribution
Adapte automatiquement le contenu selon la période de l'année
"""

from datetime import datetime, timedelta
from typing import Dict, List, Tuple

# ==================== SAISONS ====================

SEASONS = {
    "winter": {
        "name_fr": "Hiver",
        "months": [12, 1, 2],
        "colors": ["blanc", "argenté", "bleu glacé", "bordeaux"],
        "atmosphere": "cozy winter scene, soft snow, warm indoor lighting, elegant winter fashion",
        "keywords": ["hiver", "fêtes", "Noël", "nouvel an", "cocooning"],
        "image_elements": "winter coat, scarf, cozy cafe window, soft snow outside, warm tones"
    },
    "spring": {
        "name_fr": "Printemps",
        "months": [3, 4, 5],
        "colors": ["rose", "vert tendre", "lavande", "pêche"],
        "atmosphere": "spring cherry blossoms, fresh morning light, blooming flowers, renewal",
        "keywords": ["printemps", "renouveau", "fraîcheur", "floraison"],
        "image_elements": "cherry blossom trees, spring flowers, soft pink petals, morning sunlight, fresh green leaves"
    },
    "summer": {
        "name_fr": "Été",
        "months": [6, 7, 8],
        "colors": ["doré", "turquoise", "corail", "blanc soleil"],
        "atmosphere": "golden summer sunset, beach vibes, outdoor lifestyle, warm golden hour",
        "keywords": ["été", "soleil", "vacances", "plage", "festival"],
        "image_elements": "golden sunset, beach waves, summer dress, outdoor terrace, warm sunlight"
    },
    "fall": {
        "name_fr": "Automne",
        "months": [9, 10, 11],
        "colors": ["roux", "bordeaux", "moutarde", "brun chaud"],
        "atmosphere": "autumn leaves, golden hour, cozy fall fashion, warm rustic setting",
        "keywords": ["automne", "feuilles", "rentrée", "Halloween", "Action de grâce"],
        "image_elements": "autumn leaves, orange and red foliage, cozy sweater, pumpkin spice atmosphere, warm golden light"
    }
}

# ==================== ÉVÉNEMENTS ====================

EVENTS = [
    # Hiver
    {"date": (12, 25), "name": "Noël", "name_fr": "Noël", "theme": "festif, cadeaux, famille, élégance des fêtes", "image": "christmas lights, elegant holiday party, festive atmosphere"},
    {"date": (12, 31), "name": "Nouvel An", "name_fr": "Nouvel An", "theme": "glamour, soirée, paillettes, champagne", "image": "new year party, sparkling dress, midnight celebration"},
    {"date": (2, 14), "name": "Saint-Valentin", "name_fr": "Saint-Valentin", "theme": "romantique, amour, rouge, dîner en amoureux", "image": "romantic dinner, red roses, candlelight, elegant date night"},
    
    # Printemps
    {"date": (5, 10), "name": "Fête des Mères", "name_fr": "Fête des Mères", "theme": "cadeau, amour maternel, élégance, brunch", "image": "mother daughter moment, spring flowers, elegant brunch, gift giving"},
    {"date": (5, 15), "name": "Bals de graduation", "name_fr": "Bal de graduation", "theme": "glamour, jeunesse, robe de bal, coiffure spéciale", "image": "prom night, elegant gown, special hairstyle, graduation celebration", "range": 45},
    {"date": (4, 20), "name": "Pâques", "name_fr": "Pâques", "theme": "printemps, famille, pastel, renouveau", "image": "easter spring, pastel colors, family gathering, fresh flowers"},
    
    # Été
    {"date": (6, 21), "name": "Été", "name_fr": "Début de l'été", "theme": "soleil, liberté, vacances, plage", "image": "summer sunshine, beach vacation, outdoor lifestyle, golden tan"},
    {"date": (6, 24), "name": "Saint-Jean-Baptiste", "name_fr": "Fête nationale du Québec", "theme": "fierté québécoise, célébration, bleu et blanc", "image": "outdoor celebration, summer festival, Quebec pride, fireworks"},
    {"date": (7, 1), "name": "Fête du Canada", "name_fr": "Fête du Canada", "theme": "été, célébration, rouge et blanc", "image": "canada day celebration, summer outdoor event, red and white"},
    {"date": (6, 1), "name": "Saison des mariages", "name_fr": "Saison des mariages", "theme": "romantique, élégance, coiffure de mariée, glamour", "image": "wedding preparation, bridal hairstyle, romantic setting, elegant bride", "range": 90},
    
    # Automne
    {"date": (10, 31), "name": "Halloween", "name_fr": "Halloween", "theme": "costumes, transformation, looks audacieux", "image": "halloween glam, costume party, dramatic makeup, autumn night"},
    {"date": (10, 14), "name": "Action de grâce", "name_fr": "Action de grâce", "theme": "famille, gratitude, repas, automne", "image": "thanksgiving gathering, autumn harvest, family dinner, cozy home"},
    {"date": (11, 25), "name": "Black Friday", "name_fr": "Vendredi fou", "theme": "promotions, shopping, offres spéciales", "image": "shopping excitement, special deals, beauty haul"},
    
    # Fêtes de fin d'année
    {"date": (12, 1), "name": "Temps des fêtes", "name_fr": "Temps des fêtes", "theme": "magie des fêtes, préparation, cadeaux", "image": "holiday preparation, christmas shopping, festive decorations", "range": 24},
]


def get_current_season() -> Dict:
    """Retourne la saison actuelle avec ses attributs"""
    month = datetime.now().month
    
    for season_key, season_data in SEASONS.items():
        if month in season_data["months"]:
            return {"key": season_key, **season_data}
    
    return {"key": "spring", **SEASONS["spring"]}  # Fallback


def get_upcoming_events(days_ahead: int = 30) -> List[Dict]:
    """Retourne les événements à venir dans les X prochains jours"""
    today = datetime.now()
    current_year = today.year
    upcoming = []
    
    for event in EVENTS:
        month, day = event["date"]
        event_range = event.get("range", 7)  # Jours avant l'événement où on commence à en parler
        
        # Vérifier cette année et l'année prochaine
        for year in [current_year, current_year + 1]:
            try:
                event_date = datetime(year, month, day)
                days_until = (event_date - today).days
                
                # L'événement est pertinent si on est dans la période
                if -3 <= days_until <= days_ahead + event_range:
                    upcoming.append({
                        **event,
                        "event_date": event_date,
                        "days_until": days_until,
                        "is_today": days_until == 0,
                        "is_past": days_until < 0,
                        "is_soon": 0 < days_until <= 7
                    })
            except ValueError:
                continue
    
    # Trier par proximité
    upcoming.sort(key=lambda x: abs(x["days_until"]))
    return upcoming[:3]  # Max 3 événements


def get_seasonal_context() -> Dict:
    """Retourne le contexte complet: saison + événements"""
    season = get_current_season()
    events = get_upcoming_events(days_ahead=45)
    
    # Déterminer le thème principal
    if events and events[0]["days_until"] <= 14:
        primary_event = events[0]
        theme = primary_event["theme"]
        image_context = primary_event["image"]
        occasion = primary_event["name_fr"]
    else:
        primary_event = None
        theme = f"{season['name_fr']}, {', '.join(season['keywords'][:3])}"
        image_context = season["image_elements"]
        occasion = season["name_fr"]
    
    return {
        "season": season,
        "events": events,
        "primary_event": primary_event,
        "theme": theme,
        "image_context": image_context,
        "occasion": occasion,
        "date": datetime.now().strftime("%d %B %Y"),
        "month_fr": get_french_month(datetime.now().month)
    }


def get_french_month(month: int) -> str:
    """Retourne le nom du mois en français"""
    months = {
        1: "janvier", 2: "février", 3: "mars", 4: "avril",
        5: "mai", 6: "juin", 7: "juillet", 8: "août",
        9: "septembre", 10: "octobre", 11: "novembre", 12: "décembre"
    }
    return months.get(month, "")


def get_image_prompt_context() -> str:
    """Retourne le contexte pour les prompts d'images"""
    ctx = get_seasonal_context()
    season = ctx["season"]
    
    base = f"{season['atmosphere']}, {season['image_elements']}"
    
    if ctx["primary_event"]:
        base = f"{ctx['primary_event']['image']}, {season['atmosphere']}"
    
    return base


def get_post_intro() -> str:
    """Retourne une intro de post adaptée au contexte"""
    ctx = get_seasonal_context()
    
    if ctx["primary_event"]:
        event = ctx["primary_event"]
        if event["is_today"]:
            return f"🎉 C'est {event['name_fr']}!"
        elif event["is_soon"]:
            return f"⏰ {event['name_fr']} approche!"
        elif event["days_until"] <= 14:
            return f"✨ Préparez-vous pour {event['name_fr']}!"
        else:
            return f"🌟 Bientôt {event['name_fr']}..."
    else:
        season = ctx["season"]
        intros = {
            "spring": "🌸 Le printemps est là!",
            "summer": "☀️ Profitez de l'été!",
            "fall": "🍂 L'automne s'installe!",
            "winter": "❄️ La magie de l'hiver!"
        }
        return intros.get(season["key"], "✨")


# ==================== TEST ====================

if __name__ == "__main__":
    ctx = get_seasonal_context()
    print(f"📅 Date: {ctx['date']}")
    print(f"🌿 Saison: {ctx['season']['name_fr']}")
    print(f"🎯 Occasion: {ctx['occasion']}")
    print(f"🎨 Thème: {ctx['theme']}")
    print(f"📷 Image context: {ctx['image_context'][:80]}...")
    print(f"\n📌 Événements à venir:")
    for e in ctx["events"]:
        print(f"   - {e['name_fr']} (dans {e['days_until']} jours)")
    print(f"\n💬 Intro: {get_post_intro()}")
