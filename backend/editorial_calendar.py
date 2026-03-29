"""
EDITORIAL CALENDAR - Calendrier éditorial avec rotation automatique
Version: 1.0
Date: 2026-03-29

Rotation sur 2 semaines:
- Semaine 1: consommateur → comparatif → B2B salon
- Semaine 2: entretien → consommateur → B2B inventaire

Cadence: 2-3 articles par semaine max (SEO safe)
"""

import os
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

# =====================================================
# CONFIGURATION DU CALENDRIER
# =====================================================

# Rotation sur 2 semaines (6 slots)
EDITORIAL_ROTATION = [
    # Semaine 1
    {
        "slot": 1,
        "day": "monday",
        "category": "cheveux_fins",
        "type": "consommateur",
        "description": "Article consommateur - cheveux fins, volume, transformation"
    },
    {
        "slot": 2,
        "day": "wednesday",
        "category": "comparatif",
        "type": "comparatif",
        "description": "Comparatif entre méthodes ou produits"
    },
    {
        "slot": 3,
        "day": "friday",
        "category": "b2b_salon",
        "type": "b2b",
        "description": "Article B2B - salons affiliés, partenariats"
    },
    # Semaine 2
    {
        "slot": 4,
        "day": "monday",
        "category": "entretien",
        "type": "consommateur",
        "description": "Article entretien - soins, durée de vie"
    },
    {
        "slot": 5,
        "day": "wednesday",
        "category": "guide",
        "type": "consommateur",
        "description": "Guide complet - achat, choix, conseils"
    },
    {
        "slot": 6,
        "day": "friday",
        "category": "b2b_salon",
        "type": "b2b",
        "description": "Article B2B - dépôt inventaire, programme revendeur"
    }
]

# Topics spécifiques par slot (pour varier)
SLOT_TOPICS = {
    1: [  # Consommateur cheveux fins
        "Extensions pour cheveux fins",
        "Volume naturel avec extensions",
        "Transformation capillaire subtile"
    ],
    2: [  # Comparatif
        "Halo vs Tape-in",
        "Genius Weft vs I-Tip",
        "Extensions permanentes vs temporaires"
    ],
    3: [  # B2B Salon
        "Avantages salons partenaires Luxura",
        "Programme affilié pour coiffeurs",
        "Pourquoi proposer les extensions Luxura"
    ],
    4: [  # Entretien
        "Entretien quotidien des extensions",
        "Prolonger la durée de vie",
        "Soins recommandés par type"
    ],
    5: [  # Guide
        "Guide complet extensions capillaires",
        "Comment choisir ses extensions",
        "Extensions pour occasions spéciales"
    ],
    6: [  # B2B Inventaire
        "Dépôt d'inventaire sans frais",
        "Gestion de stock salon",
        "Avantages du programme revendeur"
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
    
    # Slots de la semaine actuelle
    if rotation_week == 1:
        week_slots = [s for s in EDITORIAL_ROTATION if s["slot"] <= 3]
    else:
        week_slots = [s for s in EDITORIAL_ROTATION if s["slot"] > 3]
    
    # Trouver le slot du jour
    for slot in week_slots:
        if slot["day"] == today:
            return slot
    
    return None


def get_next_category() -> Tuple[str, str, Dict]:
    """
    Retourne la prochaine catégorie à utiliser selon le calendrier.
    
    Returns:
        (category, description, full_slot_info)
    """
    slot = get_todays_slot()
    
    if slot:
        return slot["category"], slot["description"], slot
    
    # Fallback: si pas de slot aujourd'hui, utiliser le prochain dans la rotation
    rotation_week = get_current_rotation_week()
    today_index = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'].index(get_current_day_of_week())
    
    # Chercher le prochain jour avec un slot
    for i in range(1, 8):
        next_day_index = (today_index + i) % 7
        next_day = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'][next_day_index]
        
        for slot in EDITORIAL_ROTATION:
            if slot["day"] == next_day:
                # Vérifier si c'est dans la bonne semaine
                slot_week = 1 if slot["slot"] <= 3 else 2
                if slot_week == rotation_week or next_day_index < today_index:
                    return slot["category"], slot["description"], slot
    
    # Fallback ultime
    return "cheveux_fins", "Article consommateur par défaut", EDITORIAL_ROTATION[0]


def get_weekly_schedule() -> List[Dict]:
    """Retourne le planning de la semaine en cours"""
    rotation_week = get_current_rotation_week()
    
    if rotation_week == 1:
        return [s for s in EDITORIAL_ROTATION if s["slot"] <= 3]
    else:
        return [s for s in EDITORIAL_ROTATION if s["slot"] > 3]


def get_full_rotation() -> List[Dict]:
    """Retourne la rotation complète sur 2 semaines"""
    return EDITORIAL_ROTATION


def should_publish_today() -> Tuple[bool, Optional[str]]:
    """
    Vérifie si on doit publier aujourd'hui selon le calendrier.
    
    Returns:
        (should_publish, reason)
    """
    slot = get_todays_slot()
    
    if slot:
        return True, f"Jour de publication: {slot['description']}"
    
    today = get_current_day_of_week()
    if today in ['saturday', 'sunday']:
        return False, "Week-end - pas de publication"
    
    return False, "Pas dans le calendrier de rotation"


def log_calendar_status():
    """Log le status du calendrier éditorial"""
    rotation_week = get_current_rotation_week()
    today = get_current_day_of_week()
    slot = get_todays_slot()
    
    logger.info("=" * 50)
    logger.info("📅 CALENDRIER ÉDITORIAL")
    logger.info(f"   Semaine de rotation: {rotation_week}/2")
    logger.info(f"   Jour: {today.capitalize()}")
    
    if slot:
        logger.info(f"   ✅ Publication prévue: {slot['category']}")
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
    
    slot_num = slot["slot"]
    topics = SLOT_TOPICS.get(slot_num, [])
    
    if topics:
        # Rotation basée sur le numéro de semaine
        week_num = get_current_week_number()
        index = week_num % len(topics)
        return topics[index]
    
    return None


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
        "todays_slot": slot,
        "should_publish": should_publish_today()[0],
        "weekly_schedule": get_weekly_schedule(),
        "full_rotation": get_full_rotation(),
        "suggested_topic": get_suggested_topic()
    }
