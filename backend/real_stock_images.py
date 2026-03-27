# real_stock_images.py - V8
"""
Banque d'images RÉELLES (stock photos) pour les articles techniques
Ces images montrent de VRAIES techniques d'installation, pas des images IA

V8: Ajout du mode installation_halo_wire
"""

# =====================================================
# IMAGES RÉELLES - UNSPLASH & PEXELS (gratuites, commerciales)
# =====================================================

# Images de femmes avec cheveux très longs - pour résultats
REAL_LONG_HAIR_WOMEN = [
    # Femmes avec cheveux très longs - Unsplash
    "https://images.unsplash.com/photo-1519699047748-de8e457a634e?w=1200&h=630&fit=crop",  # Femme cheveux longs ondulés
    "https://images.unsplash.com/photo-1596178060671-7a80dc8059ea?w=1200&h=630&fit=crop",  # Femme cheveux longs bruns
    "https://images.unsplash.com/photo-1580489944761-15a19d654956?w=1200&h=630&fit=crop",  # Portrait cheveux longs
    "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=1200&h=630&fit=crop",  # Femme élégante
    "https://images.unsplash.com/photo-1517841905240-472988babdf9?w=1200&h=630&fit=crop",  # Cheveux longs naturels
    "https://images.unsplash.com/photo-1488716820095-cbe80883c496?w=1200&h=630&fit=crop",  # Femme cheveux flowing
    "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=1200&h=630&fit=crop",  # Portrait femme souriante
    "https://images.unsplash.com/photo-1524504388940-b1c1722653e1?w=1200&h=630&fit=crop",  # Femme cheveux lisses
]

# Images salon de coiffure - pour installations
REAL_SALON_IMAGES = [
    "https://images.unsplash.com/photo-1560066984-138dadb4c035?w=1200&h=630&fit=crop",  # Salon de coiffure moderne
    "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=1200&h=630&fit=crop",  # Coiffeuse au travail
    "https://images.unsplash.com/photo-1595476108010-b4d1f102b1b1?w=1200&h=630&fit=crop",  # Salon élégant
    "https://images.unsplash.com/photo-1559599101-f09722fb4948?w=1200&h=630&fit=crop",  # Coiffure en cours
    "https://images.unsplash.com/photo-1562322140-8baeececf3df?w=1200&h=630&fit=crop",  # Femme au salon
    "https://images.unsplash.com/photo-1521590832167-7bcbfaa6381f?w=1200&h=630&fit=crop",  # Salon professionnel
]

# Images close-up cheveux - pour détails
REAL_HAIR_CLOSEUP = [
    "https://images.unsplash.com/photo-1522337094846-8a818192de1f?w=1200&h=630&fit=crop",  # Close-up cheveux
    "https://images.unsplash.com/photo-1527799820374-dcf8d9d4a388?w=1200&h=630&fit=crop",  # Texture cheveux
    "https://images.unsplash.com/photo-1519699047748-de8e457a634e?w=1200&h=630&fit=crop",  # Cheveux ondulés
    "https://images.unsplash.com/photo-1492106087820-71f1a00d2b11?w=1200&h=630&fit=crop",  # Cheveux lisses
]

# Images lifestyle - soirée de filles (images fournies par le client)
LUXURA_LIFESTYLE_IMAGES = [
    "https://customer-assets.emergentagent.com/job_hair-extensions-shop/artifacts/no4frw3t_vaVsE.jpg",
    "https://customer-assets.emergentagent.com/job_hair-extensions-shop/artifacts/oyi6y21r_Aq7eZ.jpg",
    "https://customer-assets.emergentagent.com/job_hair-extensions-shop/artifacts/21xcpk05_OdzWP.jpg",
]

# Images spécifiques Halo - pose facile à la maison
REAL_HALO_HOME_IMAGES = [
    # Femmes se préparant / devant miroir - représente la pose facile à la maison
    "https://images.unsplash.com/photo-1522337094846-8a818192de1f?w=1200&h=630&fit=crop",
    "https://images.unsplash.com/photo-1519699047748-de8e457a634e?w=1200&h=630&fit=crop",
    "https://images.unsplash.com/photo-1580489944761-15a19d654956?w=1200&h=630&fit=crop",
]

# =====================================================
# MAPPING PAR TYPE D'ARTICLE - V8 avec installation_halo_wire
# =====================================================

IMAGES_BY_MODE = {
    # === INSTALLATIONS TECHNIQUES ===
    
    # HALO - pose simple à la maison, fil invisible, pas de salon nécessaire
    "installation_halo_wire": {
        "cover": REAL_HALO_HOME_IMAGES + REAL_LONG_HAIR_WOMEN[:3],
        "content": REAL_HAIR_CLOSEUP,
        "description": "Halo - fil invisible qui se pose sans salon, pose ultra-simple"
    },
    # Ancien nom pour compatibilité
    "installation_halo": {
        "cover": REAL_HALO_HOME_IMAGES + REAL_LONG_HAIR_WOMEN[:3],
        "content": REAL_HAIR_CLOSEUP,
        "description": "Halo - fil invisible qui se pose sans salon"
    },
    
    # TAPE-IN - méthode sandwich en salon
    "installation_tape_sandwich": {
        "cover": REAL_SALON_IMAGES,
        "content": REAL_HAIR_CLOSEUP,
        "description": "Tape-in - méthode sandwich avec bandes adhésives"
    },
    
    # GENIUS WEFT - couture sur rangée perlée
    "installation_genius_sewn": {
        "cover": REAL_SALON_IMAGES,
        "content": REAL_HAIR_CLOSEUP,
        "description": "Genius Weft - cousu sur rangée perlée (beaded row)"
    },
    
    # I-TIP - microbilles avec pince
    "installation_itip_bead": {
        "cover": REAL_SALON_IMAGES,
        "content": REAL_HAIR_CLOSEUP,
        "description": "I-Tip - microbilles avec pince, mèche par mèche"
    },
    
    # Installation générique
    "installation_pro": {
        "cover": REAL_SALON_IMAGES,
        "content": REAL_HAIR_CLOSEUP,
        "description": "Installation professionnelle générique"
    },
    
    # === RÉSULTATS ET LIFESTYLE ===
    
    "result_natural": {
        "cover": REAL_LONG_HAIR_WOMEN,
        "content": REAL_HAIR_CLOSEUP,
        "description": "Résultat naturel - cheveux longs"
    },
    "result_maintenance": {
        "cover": REAL_LONG_HAIR_WOMEN,
        "content": REAL_HAIR_CLOSEUP,
        "description": "Entretien - soins"
    },
    "editorial_lifestyle": {
        "cover": LUXURA_LIFESTYLE_IMAGES + REAL_LONG_HAIR_WOMEN,
        "content": REAL_LONG_HAIR_WOMEN,
        "description": "Lifestyle / Soirée de filles"
    },
}

# Index pour rotation
_image_indices = {}

def get_real_image_for_mode(mode: str, image_type: str = "cover") -> str:
    """
    Retourne une vraie image stock pour le mode et type donné.
    Rotation automatique pour éviter les doublons.
    """
    global _image_indices
    
    key = f"{mode}_{image_type}"
    if key not in _image_indices:
        _image_indices[key] = 0
    
    # Récupérer la liste d'images pour ce mode
    mode_images = IMAGES_BY_MODE.get(mode, IMAGES_BY_MODE["result_natural"])
    images = mode_images.get(image_type, mode_images.get("cover", REAL_LONG_HAIR_WOMEN))
    
    # Sélectionner l'image et incrémenter l'index
    image = images[_image_indices[key] % len(images)]
    _image_indices[key] += 1
    
    return image


def get_all_images_for_mode(mode: str) -> dict:
    """Retourne toutes les images disponibles pour un mode donné."""
    return IMAGES_BY_MODE.get(mode, IMAGES_BY_MODE["result_natural"])
