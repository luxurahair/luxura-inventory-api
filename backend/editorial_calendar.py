"""
EDITORIAL CALENDAR - Calendrier éditorial optimisé femmes Québec
Version: 2.0
Date: 2026-03-31

🎯 CIBLE: Femmes québécoises 25-55 ans intéressées par la beauté/coiffure

📅 ROTATION SUR 2 SEMAINES (7 jours/semaine):
- Lundi-Vendredi: Mix consommateur/B2B
- Samedi-Dimanche: Contenu lifestyle/inspiration (meilleur engagement)

⏰ HEURES DE POINTE QUÉBEC (femmes):
- Matin: 7h-9h (préparation, transport)
- Midi: 12h-13h (pause lunch)
- Soir: 19h-21h (détente après souper)
- Weekend: 10h-11h et 20h-21h
"""

import os
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

# =====================================================
# CONFIGURATION DU CALENDRIER - OPTIMISÉ FEMMES QUÉBEC
# =====================================================

# Heures de publication optimales (fuseau Montreal)
PEAK_HOURS = {
    "monday": 7,      # Lundi 7h - début de semaine motivation
    "tuesday": 12,    # Mardi 12h - pause lunch
    "wednesday": 19,  # Mercredi 19h - soirée détente
    "thursday": 7,    # Jeudi 7h - préparation
    "friday": 12,     # Vendredi 12h - avant le weekend
    "saturday": 10,   # Samedi 10h - matinée relaxe
    "sunday": 20,     # Dimanche 20h - planification semaine
}

# Rotation sur 2 semaines (14 slots)
EDITORIAL_ROTATION = [
    # ========== SEMAINE 1 ==========
    {
        "slot": 1,
        "week": 1,
        "day": "monday",
        "hour": 7,
        "category": "transformation",
        "type": "consommateur",
        "target": "femmes",
        "description": "Transformation capillaire - Avant/Après inspirants"
    },
    {
        "slot": 2,
        "week": 1,
        "day": "tuesday",
        "hour": 12,
        "category": "cheveux_fins",
        "type": "consommateur",
        "target": "femmes",
        "description": "Solutions cheveux fins - Volume et densité"
    },
    {
        "slot": 3,
        "week": 1,
        "day": "wednesday",
        "hour": 19,
        "category": "comparatif",
        "type": "consommateur",
        "target": "femmes",
        "description": "Comparatif méthodes - Aide au choix"
    },
    {
        "slot": 4,
        "week": 1,
        "day": "thursday",
        "hour": 7,
        "category": "b2b_salon",
        "type": "b2b",
        "target": "salons",
        "description": "Article B2B - Avantages salons partenaires"
    },
    {
        "slot": 5,
        "week": 1,
        "day": "friday",
        "hour": 12,
        "category": "tendances",
        "type": "consommateur",
        "target": "femmes",
        "description": "Tendances coiffure - Styles du moment"
    },
    {
        "slot": 6,
        "week": 1,
        "day": "saturday",
        "hour": 10,
        "category": "inspiration",
        "type": "lifestyle",
        "target": "femmes",
        "description": "Inspiration weekend - Looks et idées"
    },
    {
        "slot": 7,
        "week": 1,
        "day": "sunday",
        "hour": 20,
        "category": "temoignages",
        "type": "lifestyle",
        "target": "femmes",
        "description": "Témoignages clientes - Histoires inspirantes"
    },
    
    # ========== SEMAINE 2 ==========
    {
        "slot": 8,
        "week": 2,
        "day": "monday",
        "hour": 7,
        "category": "entretien",
        "type": "consommateur",
        "target": "femmes",
        "description": "Entretien extensions - Soins et durabilité"
    },
    {
        "slot": 9,
        "week": 2,
        "day": "tuesday",
        "hour": 12,
        "category": "guide",
        "type": "consommateur",
        "target": "femmes",
        "description": "Guide complet - Conseils achat et choix"
    },
    {
        "slot": 10,
        "week": 2,
        "day": "wednesday",
        "hour": 19,
        "category": "occasions",
        "type": "consommateur",
        "target": "femmes",
        "description": "Extensions occasions spéciales - Mariage, gala"
    },
    {
        "slot": 11,
        "week": 2,
        "day": "thursday",
        "hour": 7,
        "category": "b2b_inventaire",
        "type": "b2b",
        "target": "salons",
        "description": "Article B2B - Programme dépôt inventaire"
    },
    {
        "slot": 12,
        "week": 2,
        "day": "friday",
        "hour": 12,
        "category": "couleurs",
        "type": "consommateur",
        "target": "femmes",
        "description": "Guide couleurs - Trouver sa teinte parfaite"
    },
    {
        "slot": 13,
        "week": 2,
        "day": "saturday",
        "hour": 10,
        "category": "tutoriel",
        "type": "lifestyle",
        "target": "femmes",
        "description": "Tutoriel coiffure - Styles avec extensions"
    },
    {
        "slot": 14,
        "week": 2,
        "day": "sunday",
        "hour": 20,
        "category": "self_care",
        "type": "lifestyle",
        "target": "femmes",
        "description": "Self-care beauté - Routine capillaire complète"
    }
]

# Topics spécifiques par catégorie (rotation pour varier)
CATEGORY_TOPICS = {
    "transformation": [
        "Transformation capillaire : de cheveux fins à volume spectaculaire",
        "Avant/Après : ces femmes qui ont osé les extensions",
        "Changement de look : comment les extensions ont transformé leur vie"
    ],
    "cheveux_fins": [
        "Solutions naturelles pour cheveux fins et clairsemés",
        "Extensions pour cheveux fins : le guide complet",
        "Comment ajouter du volume sans abîmer ses cheveux"
    ],
    "comparatif": [
        "Halo vs Tape-in : quelle méthode choisir ?",
        "Genius Weft vs extensions traditionnelles",
        "Extensions permanentes ou temporaires : le comparatif"
    ],
    "b2b_salon": [
        "Pourquoi les salons choisissent Luxura Distribution",
        "Devenir salon partenaire : avantages et opportunités",
        "Programme affilié Luxura pour coiffeurs professionnels"
    ],
    "tendances": [
        "Tendances coiffure 2026 : ce que veulent les Québécoises",
        "Les styles d'extensions les plus demandés cette saison",
        "Couleurs tendance : blond, balayage ou naturel ?"
    ],
    "inspiration": [
        "10 looks inspirants avec extensions pour le weekend",
        "Célébrités québécoises et leurs secrets capillaires",
        "Idées coiffures pour occasions spéciales"
    ],
    "temoignages": [
        "Marie, 35 ans : comment les extensions ont boosté ma confiance",
        "Témoignages de clientes satisfaites au Québec",
        "Histoires de transformation : elles racontent leur expérience"
    ],
    "entretien": [
        "Routine d'entretien quotidienne pour vos extensions",
        "Comment prolonger la durée de vie de vos extensions",
        "Les erreurs à éviter avec vos extensions capillaires"
    ],
    "guide": [
        "Guide complet : choisir ses premières extensions",
        "Tout savoir avant d'acheter des extensions au Québec",
        "Comment choisir la bonne longueur et texture"
    ],
    "occasions": [
        "Extensions pour votre mariage : le guide complet",
        "Coiffures de gala : sublimez-vous avec les extensions",
        "Extensions pour les fêtes : brillez toute la soirée"
    ],
    "b2b_inventaire": [
        "Programme dépôt d'inventaire : zéro investissement initial",
        "Gestion de stock salon simplifiée avec Luxura",
        "Avantages du programme revendeur pour votre salon"
    ],
    "couleurs": [
        "Trouver la couleur d'extensions parfaite pour votre teint",
        "Blond, brun ou roux : guide des teintes Luxura",
        "Extensions ombrées et balayage : tendances couleurs"
    ],
    "tutoriel": [
        "Tutoriel : 5 coiffures faciles avec extensions Halo",
        "Comment poser vos extensions Tape-in à la maison",
        "Styles rapides pour femmes actives"
    ],
    "self_care": [
        "Routine beauté complète : cheveux, peau et bien-être",
        "Prendre soin de soi : la beauté commence par les cheveux",
        "Dimanche self-care : chouchoutez vos extensions"
    ]
}


# =====================================================
# FONCTIONS CALENDRIER
# =====================================================

def get_current_week_number() -> int:
    """Retourne le numéro de semaine (1-52)"""
    return datetime.now().isocalendar()[1]


def get_current_rotation_week() -> int:
    """Retourne 1 ou 2 selon la semaine de rotation"""
    week_num = get_current_week_number()
    return 1 if week_num % 2 == 1 else 2


def get_current_day_of_week() -> str:
    """Retourne le jour en anglais (monday, tuesday, etc.)"""
    days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    return days[datetime.now().weekday()]


def get_todays_slot() -> Optional[Dict]:
    """Retourne le slot éditorial du jour, ou None si pas de publication prévue"""
    rotation_week = get_current_rotation_week()
    today = get_current_day_of_week()
    
    # Trouver le slot du jour dans la semaine actuelle
    for slot in EDITORIAL_ROTATION:
        if slot["week"] == rotation_week and slot["day"] == today:
            return slot
    
    return None


def get_todays_hour() -> int:
    """Retourne l'heure de publication optimale pour aujourd'hui"""
    today = get_current_day_of_week()
    return PEAK_HOURS.get(today, 8)


def get_next_category() -> Tuple[str, str, Dict]:
    """
    Retourne la prochaine catégorie à utiliser selon le calendrier.
    
    Returns:
        (category, description, full_slot_info)
    """
    slot = get_todays_slot()
    
    if slot:
        return slot["category"], slot["description"], slot
    
    # Fallback: si pas de slot trouvé
    return "cheveux_fins", "Article consommateur par défaut", EDITORIAL_ROTATION[0]


def get_weekly_schedule() -> List[Dict]:
    """Retourne le planning de la semaine en cours"""
    rotation_week = get_current_rotation_week()
    return [s for s in EDITORIAL_ROTATION if s["week"] == rotation_week]


def get_full_rotation() -> List[Dict]:
    """Retourne la rotation complète sur 2 semaines"""
    return EDITORIAL_ROTATION


def should_publish_today() -> Tuple[bool, str]:
    """
    Vérifie si on doit publier aujourd'hui selon le calendrier.
    
    Returns:
        (should_publish, reason)
    """
    slot = get_todays_slot()
    
    if slot:
        target = slot.get("target", "femmes")
        return True, f"Jour de publication: {slot['description']} (cible: {target})"
    
    return False, "Pas de slot trouvé pour aujourd'hui"


def log_calendar_status():
    """Log le status du calendrier éditorial"""
    rotation_week = get_current_rotation_week()
    today = get_current_day_of_week()
    slot = get_todays_slot()
    hour = get_todays_hour()
    
    logger.info("=" * 50)
    logger.info("📅 CALENDRIER ÉDITORIAL - OPTIMISÉ FEMMES QUÉBEC")
    logger.info(f"   Semaine de rotation: {rotation_week}/2")
    logger.info(f"   Jour: {today.capitalize()}")
    logger.info(f"   Heure optimale: {hour}h (Montreal)")
    
    if slot:
        logger.info(f"   ✅ Publication prévue: {slot['category']}")
        logger.info(f"   🎯 Cible: {slot.get('target', 'femmes')}")
        logger.info(f"   📝 {slot['description']}")
    else:
        logger.info(f"   ⏸️ Pas de publication prévue aujourd'hui")
    
    logger.info("=" * 50)


# =====================================================
# INTÉGRATION AVEC LE CRON
# =====================================================

def get_cron_category() -> str:
    """
    Retourne la catégorie à utiliser pour le CRON journalier.
    Utilisé par le scheduler APScheduler.
    """
    should_pub, reason = should_publish_today()
    
    if should_pub:
        slot = get_todays_slot()
        if slot:
            logger.info(f"📅 Calendrier: {slot['category']} - {reason}")
            return slot["category"]
    
    logger.info(f"📅 Calendrier: {reason}")
    return None  # Ne pas publier


def get_suggested_topic() -> Optional[str]:
    """Retourne un sujet suggéré pour le slot du jour"""
    slot = get_todays_slot()
    
    if not slot:
        return None
    
    category = slot["category"]
    topics = CATEGORY_TOPICS.get(category, [])
    
    if topics:
        # Rotation basée sur le numéro de semaine
        week_num = get_current_week_number()
        index = week_num % len(topics)
        return topics[index]
    
    return None


def get_cron_hours() -> List[Dict]:
    """
    Retourne les heures de CRON pour chaque jour.
    Utilisé pour configurer APScheduler avec plusieurs triggers.
    """
    return [
        {"day": "mon", "hour": PEAK_HOURS["monday"]},
        {"day": "tue", "hour": PEAK_HOURS["tuesday"]},
        {"day": "wed", "hour": PEAK_HOURS["wednesday"]},
        {"day": "thu", "hour": PEAK_HOURS["thursday"]},
        {"day": "fri", "hour": PEAK_HOURS["friday"]},
        {"day": "sat", "hour": PEAK_HOURS["saturday"]},
        {"day": "sun", "hour": PEAK_HOURS["sunday"]},
    ]


# =====================================================
# RAPPORT CALENDRIER
# =====================================================

def generate_calendar_report() -> Dict:
    """Génère un rapport complet du calendrier"""
    rotation_week = get_current_rotation_week()
    today = get_current_day_of_week()
    slot = get_todays_slot()
    
    return {
        "current_week": get_current_week_number(),
        "rotation_week": rotation_week,
        "today": today,
        "todays_hour": get_todays_hour(),
        "todays_slot": slot,
        "should_publish": should_publish_today()[0],
        "weekly_schedule": get_weekly_schedule(),
        "full_rotation": get_full_rotation(),
        "suggested_topic": get_suggested_topic(),
        "peak_hours": PEAK_HOURS
    }


def get_week_preview() -> str:
    """Retourne un aperçu du planning de la semaine"""
    schedule = get_weekly_schedule()
    lines = ["📅 PLANNING SEMAINE:"]
    
    for slot in schedule:
        day = slot["day"].capitalize()
        hour = slot["hour"]
        cat = slot["category"]
        target = slot.get("target", "femmes")
        lines.append(f"   - {day} {hour}h: {cat} ({target})")
    
    return "\n".join(lines)
