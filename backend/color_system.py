# ══════════════════════════════════════════════════════════════════
# SYSTÈME COULEUR LUXURA - BRANDING + SEO + CONVERSION
# ══════════════════════════════════════════════════════════════════
# 
# Ce fichier contient le mapping complet des couleurs Luxura avec:
# - Nom SKU technique
# - Nom marketing luxe
# - Description SEO optimisée Google
# - Type de coloration (SOLID/PIANO/OMBRE/BALAYAGE/OMBRE-PIANO)
# - Tonalité (FROID/CHAUD/NEUTRE)
# - Niveau de clarté (1-10, 1=noir, 10=platine)
# - Composition détaillée pour couleurs complexes
#
# ══════════════════════════════════════════════════════════════════

COLOR_SYSTEM = {
    # ════════════════════ NOIRS (Level 1-2) ════════════════════
    "1": {
        "sku": "ONYX-NOIR",
        "luxura": "Onyx Noir",
        "seo": "noir intense jet black extensions cheveux professionnelles",
        "type": "SOLID",
        "tone": "NEUTRE",
        "level": 1,
        "hex": "#0a0a0a",
        "description_fr": "Le noir le plus profond et intense. Éclat naturel sans reflets."
    },
    "1B": {
        "sku": "NOIR-SOIE",
        "luxura": "Noir Soie",
        "seo": "noir naturel off black doux extensions soyeux",
        "type": "SOLID",
        "tone": "NEUTRE",
        "level": 2,
        "hex": "#1a1a1a",
        "description_fr": "Noir naturel plus doux avec subtils reflets bruns. Très polyvalent."
    },
    
    # ════════════════════ BRUNS FONCÉS (Level 2-3) ════════════════════
    "2": {
        "sku": "ESPRESSO-INTENSE",
        "luxura": "Espresso Intense",
        "seo": "brun foncé espresso dark brown extensions professionnel",
        "type": "SOLID",
        "tone": "NEUTRE",
        "level": 2,
        "hex": "#2d1810",
        "description_fr": "Brun espresso profond et riche. Intensité maximale."
    },
    "DB": {
        "sku": "NUIT-MYSTERE",
        "luxura": "Nuit Mystère",
        "seo": "brun mystère foncé dark mystery brown extensions luxe",
        "type": "SOLID",
        "tone": "FROID",
        "level": 2,
        "hex": "#2a1f1a",
        "description_fr": "Brun mystérieux aux reflets froids. Élégance discrète."
    },
    "DC": {
        "sku": "CHOCOLAT-PROFOND",
        "luxura": "Chocolat Profond",
        "seo": "brun chocolat foncé dark chocolate brown extensions riche",
        "type": "SOLID",
        "tone": "CHAUD",
        "level": 3,
        "hex": "#3d2314",
        "description_fr": "Brun chocolat riche et gourmand. Reflets chauds naturels."
    },
    "CACAO": {
        "sku": "CACAO-VELOURS",
        "luxura": "Cacao Velours",
        "seo": "brun cacao velouté cocoa brown extensions doux",
        "type": "SOLID",
        "tone": "CHAUD",
        "level": 3,
        "hex": "#4a2c17",
        "description_fr": "Brun cacao velouté aux reflets chauds. Douceur naturelle."
    },
    "CHENGTU": {
        "sku": "SOIE-ORIENT",
        "luxura": "Soie d'Orient",
        "seo": "brun asiatique naturel asian brown silk extensions",
        "type": "SOLID",
        "tone": "NEUTRE",
        "level": 2,
        "hex": "#1f1610",
        "description_fr": "Brun asiatique naturel. Éclat soyeux unique."
    },
    "FOOCHOW": {
        "sku": "CACHEMIRE-ORIENTAL",
        "luxura": "Cachemire Oriental",
        "seo": "brun oriental luxe oriental cashmere brown extensions",
        "type": "SOLID",
        "tone": "CHAUD",
        "level": 3,
        "hex": "#3a251a",
        "description_fr": "Brun oriental luxueux aux reflets cachemire. Raffinement absolu."
    },
    
    # ════════════════════ CHÂTAIGNE (Level 3-4) ════════════════════
    "3": {
        "sku": "CHATAIGNE-NATURELLE",
        "luxura": "Châtaigne Naturelle",
        "seo": "brun châtaigne medium brown chestnut extensions naturel",
        "type": "SOLID",
        "tone": "NEUTRE",
        "level": 4,
        "hex": "#5a3825",
        "description_fr": "Châtaigne classique et naturelle. La couleur la plus polyvalente."
    },
    "CINNAMON": {
        "sku": "CANNELLE-EPICEE",
        "luxura": "Cannelle Épicée",
        "seo": "brun cannelle auburn cinnamon brown extensions chaleureux",
        "type": "SOLID",
        "tone": "CHAUD",
        "level": 4,
        "hex": "#6d3f2a",
        "description_fr": "Brun cannelle aux reflets cuivrés. Chaleur et caractère."
    },
    
    # ════════════════════ CHÂTAIGNE DIMENSION (Ombré + Piano) ════════════════════
    "3/3T24": {
        "sku": "CHATAIGNE-LUMIERE-DOREE",
        "luxura": "Châtaigne Lumière Dorée",
        "seo": "châtaigne ombré mèches blondes balayage brown to blonde piano",
        "type": "OMBRE-PIANO",
        "tone": "CHAUD",
        "level": 4,
        "composition": {
            "base": {"code": "3", "name": "Châtaigne", "percent": 60},
            "ombre": {"code": "3", "name": "Châtaigne", "direction": "racine"},
            "piano": {"code": "24", "name": "Blond Doré", "percent": 40}
        },
        "description_fr": "Châtaigne avec ombré naturel et mèches dorées. Dimension et mouvement."
    },
    
    # ════════════════════ CARAMEL (Level 6) ════════════════════
    "6": {
        "sku": "CARAMEL-DORE",
        "luxura": "Caramel Doré",
        "seo": "blond caramel doré golden caramel blonde extensions",
        "type": "SOLID",
        "tone": "CHAUD",
        "level": 6,
        "hex": "#8b6234",
        "description_fr": "Caramel doré classique. Chaleur et luminosité."
    },
    "BM": {
        "sku": "MIEL-SAUVAGE",
        "luxura": "Miel Sauvage",
        "seo": "brun miel honey brown natural extensions doux",
        "type": "SOLID",
        "tone": "CHAUD",
        "level": 5,
        "hex": "#7a5530",
        "description_fr": "Brun miel naturel et sauvage. Douceur et authenticité."
    },
    
    # ════════════════════ CARAMEL DIMENSION ════════════════════
    "6/24": {
        "sku": "GOLDEN-HOUR",
        "luxura": "Golden Hour",
        "seo": "balayage caramel doré golden hour blonde highlights extensions",
        "type": "BALAYAGE",
        "tone": "CHAUD",
        "level": 7,
        "composition": {
            "base": {"code": "6", "name": "Caramel", "percent": 50},
            "balayage": {"code": "24", "name": "Blond Doré", "percent": 50}
        },
        "description_fr": "Balayage caramel vers blond doré. L'heure dorée capturée."
    },
    "6/6T24": {
        "sku": "CARAMEL-SOLEIL",
        "luxura": "Caramel Soleil",
        "seo": "caramel ombré piano mèches blondes sun-kissed highlights extensions",
        "type": "OMBRE-PIANO",
        "tone": "CHAUD",
        "level": 7,
        "composition": {
            "base": {"code": "6", "name": "Caramel", "percent": 50},
            "ombre": {"code": "6", "name": "Caramel", "direction": "racine"},
            "piano": {"code": "24", "name": "Blond Doré", "percent": 50}
        },
        "description_fr": "Caramel avec ombré et mèches dorées. Effet soleil naturel."
    },
    
    # ════════════════════ BLONDS PIANO (Level 8-9) ════════════════════
    # #18 = Beige naturel froid + #22 = Blond doré clair chaud = Champagne parfait
    "18/22": {
        "sku": "CHAMPAGNE-DORE",
        "luxura": "Champagne Doré",
        "seo": "blond champagne beige doré clair piano highlights multidimensionnel extensions",
        "type": "PIANO",
        "tone": "NEUTRE",  # Équilibre parfait froid/chaud
        "level": 8,
        "composition": {
            "piano_froid": {"code": "18", "name": "Beige Naturel", "tone": "FROID", "percent": 50},
            "piano_chaud": {"code": "22", "name": "Blond Doré Clair", "tone": "CHAUD", "percent": 50}
        },
        "description_fr": "Blond champagne multidimensionnel. Équilibre parfait entre beige froid et doré chaud. Effet salon haut de gamme.",
        "note": "Une des meilleures couleurs pour vendre - ni trop froid ni trop chaud"
    },
    
    # ════════════════════ BLONDS PLATINE (Level 9-10) ════════════════════
    "60A": {
        "sku": "PLATINE-PUR",
        "luxura": "Platine Pur",
        "seo": "blond platine pur platinum blonde ice extensions glacé",
        "type": "SOLID",
        "tone": "FROID",
        "level": 10,
        "hex": "#e8dcc8",
        "description_fr": "Platine pur et glacé. Blond le plus clair et lumineux."
    },
    "PHA": {
        "sku": "CENDRE-CELESTE",
        "luxura": "Cendré Céleste",
        "seo": "blond cendré pur ash blonde silver extensions élégant",
        "type": "SOLID",
        "tone": "FROID",
        "level": 9,
        "hex": "#c4b8a8",
        "description_fr": "Blond cendré pur et céleste. Élégance raffinée."
    },
    "613/18A": {
        "sku": "DIAMANT-GLACE",
        "luxura": "Diamant Glacé",
        "seo": "platine balayage cendré platinum ash highlights diamond extensions",
        "type": "BALAYAGE",
        "tone": "FROID",
        "level": 10,
        "composition": {
            "base": {"code": "613", "name": "Platine", "percent": 60},
            "balayage": {"code": "18A", "name": "Cendré", "percent": 40}
        },
        "description_fr": "Platine avec balayage cendré. Éclat diamant glacé."
    },
    
    # ════════════════════ BLANCS PRÉCIEUX (Level 10+) ════════════════════
    "IVORY": {
        "sku": "IVOIRE-PRECIEUX",
        "luxura": "Ivoire Précieux",
        "seo": "blanc ivoire precious ivory white extensions luxe crème",
        "type": "SOLID",
        "tone": "CHAUD",
        "level": 10,
        "hex": "#f5f0e6",
        "description_fr": "Blanc ivoire précieux aux reflets chauds. Luxe ultime."
    },
    "ICW": {
        "sku": "CRISTAL-POLAIRE",
        "luxura": "Cristal Polaire",
        "seo": "blanc polaire ice white crystal platinum extensions glacé",
        "type": "SOLID",
        "tone": "FROID",
        "level": 10,
        "hex": "#f8f8f8",
        "description_fr": "Blanc glacé cristallin. Pureté arctique."
    },
    
    # ════════════════════ OMBRÉS SIGNATURE ════════════════════
    "CB": {
        "sku": "MIEL-SAUVAGE-OMBRE",
        "luxura": "Miel Sauvage Ombré",
        "seo": "ombré miel brun vers blond honey ombre transition extensions",
        "type": "OMBRE",
        "tone": "CHAUD",
        "level": 6,
        "composition": {
            "racine": {"tone": "brun", "level": 4},
            "transition": {"smooth": True},
            "pointe": {"tone": "miel", "level": 7}
        },
        "description_fr": "Ombré naturel du brun vers le miel. Transition douce et sauvage."
    },
    "HPS": {
        "sku": "CENDRE-ETOILE",
        "luxura": "Cendré Étoilé",
        "seo": "ombré cendré luxe ash ombre silver blonde transition extensions",
        "type": "OMBRE",
        "tone": "FROID",
        "level": 8,
        "composition": {
            "racine": {"tone": "ash brown", "level": 5},
            "transition": {"smooth": True},
            "pointe": {"tone": "ash blonde", "level": 9}
        },
        "description_fr": "Ombré cendré étoilé. Transition sophistiquée du brun cendré au blond argenté."
    },
    "5AT60": {
        "sku": "AURORE-GLACIALE",
        "luxura": "Aurore Glaciale",
        "seo": "ombré glacier brun vers platine arctic ombre brown to platinum extensions",
        "type": "OMBRE",
        "tone": "FROID",
        "level": 9,
        "composition": {
            "racine": {"code": "5", "tone": "châtain", "level": 5},
            "transition": {"dramatic": True},
            "pointe": {"code": "60", "tone": "platine", "level": 10}
        },
        "description_fr": "Ombré glacier dramatique. Du châtain au platine comme une aurore arctique."
    },
    "5ATP18B62": {
        "sku": "AURORE-BOREALE",
        "luxura": "Aurore Boréale",
        "seo": "ombré nordique multi-ton nordic aurora ombre extensions complexe",
        "type": "OMBRE",
        "tone": "FROID",
        "level": 9,
        "composition": {
            "racine": {"code": "5", "level": 5},
            "mid": {"code": "18", "level": 8},
            "pointe": {"code": "62", "level": 9}
        },
        "description_fr": "Ombré nordique multi-dimensionnel. Comme les lumières de l'aurore boréale."
    },
    
    # ════════════════════ ESPRESSO DIMENSION ════════════════════
    "2BTP18/1006": {
        "sku": "ESPRESSO-LUMIERE",
        "luxura": "Espresso Lumière",
        "seo": "espresso ombré mèches highlights dark brown to blonde extensions",
        "type": "OMBRE-PIANO",
        "tone": "NEUTRE",
        "level": 5,
        "composition": {
            "base": {"code": "2B", "name": "Espresso", "percent": 50},
            "ombre": {"code": "18", "direction": "transition"},
            "piano": {"code": "1006", "name": "Highlights", "percent": 30}
        },
        "description_fr": "Espresso avec ombré et mèches lumineuses. Profondeur et éclat."
    },
    
    # ════════════════════ VÉNITIEN SIGNATURE ════════════════════
    "T14/P14/24": {
        "sku": "VENISE-DOREE",
        "luxura": "Venise Dorée",
        "seo": "balayage vénitien multi-dimensionnel venetian golden highlights extensions",
        "type": "OMBRE-PIANO",
        "tone": "CHAUD",
        "level": 8,
        "composition": {
            "ombre": {"code": "14", "name": "Dark Blonde", "direction": "transition"},
            "piano_1": {"code": "14", "name": "Dark Blonde", "percent": 30},
            "piano_2": {"code": "24", "name": "Golden Blonde", "percent": 30}
        },
        "description_fr": "Balayage vénitien luxueux. Multi-dimensions dorées comme les canaux de Venise."
    },
}


def get_color_info(color_code: str) -> dict:
    """
    Obtenir toutes les informations de couleur pour un code donné.
    
    Retourne un dictionnaire avec:
    - sku: nom technique pour SKU
    - luxura: nom marketing luxe
    - seo: description SEO Google
    - type: SOLID/PIANO/OMBRE/BALAYAGE/OMBRE-PIANO
    - tone: FROID/CHAUD/NEUTRE
    - level: niveau clarté 1-10
    """
    if not color_code:
        return {
            "sku": "UNKNOWN",
            "luxura": "Inconnu",
            "seo": "extensions cheveux professionnelles",
            "type": "SOLID",
            "tone": "NEUTRE",
            "level": 5
        }
    
    clean_code = color_code.strip().upper()
    
    # Chercher correspondance exacte
    if clean_code in COLOR_SYSTEM:
        return COLOR_SYSTEM[clean_code]
    
    # Chercher correspondance sans /
    normalized = clean_code.replace("/", "-")
    for code, info in COLOR_SYSTEM.items():
        if code.replace("/", "-") == normalized:
            return info
    
    # Fallback intelligent
    return _generate_fallback_color_info(clean_code)


def _generate_fallback_color_info(code: str) -> dict:
    """Générer des infos couleur pour codes non mappés"""
    color_type = "SOLID"
    tone = "NEUTRE"
    level = 5
    
    # Détecter le type
    if "T" in code and "P" in code:
        color_type = "OMBRE-PIANO"
    elif "T" in code:
        color_type = "OMBRE"
    elif "P" in code or ("/" in code and code[0].isdigit()):
        color_type = "PIANO" if "P" in code else "BALAYAGE"
    
    # Détecter le niveau et tonalité
    base_num = ''.join(filter(str.isdigit, code[:2]))
    if base_num:
        num = int(base_num)
        level = min(10, max(1, num))
        if num <= 2:
            tone = "NEUTRE"
        elif num <= 5:
            tone = "CHAUD"
        else:
            tone = "FROID" if "A" in code else "CHAUD"
    
    return {
        "sku": code.replace("/", "-"),
        "luxura": f"Teinte {code}",
        "seo": f"extensions cheveux teinte {code} professionnel",
        "type": color_type,
        "tone": tone,
        "level": level
    }


def get_seo_description(color_code: str, product_type: str = "extensions") -> str:
    """
    Générer une description SEO complète pour un produit.
    
    Args:
        color_code: Code couleur (ex: "6/24", "18/22")
        product_type: Type de produit (ex: "Halo", "Genius", "Tape")
    
    Returns:
        Description SEO optimisée
    """
    info = get_color_info(color_code)
    
    seo_parts = [
        info.get("seo", ""),
        f"{product_type.lower()} cheveux",
        info.get("luxura", ""),
    ]
    
    if info.get("tone") == "CHAUD":
        seo_parts.append("reflets chauds")
    elif info.get("tone") == "FROID":
        seo_parts.append("reflets froids")
    
    if info.get("type") in ["PIANO", "OMBRE-PIANO"]:
        seo_parts.append("mèches highlights")
    elif info.get("type") == "OMBRE":
        seo_parts.append("dégradé ombré")
    elif info.get("type") == "BALAYAGE":
        seo_parts.append("balayage naturel")
    
    return " ".join(seo_parts)


def get_all_colors_for_filter() -> list:
    """
    Retourner toutes les couleurs formatées pour un filtre frontend.
    
    Returns:
        Liste de dictionnaires avec id, name, seo pour chaque couleur
    """
    colors = []
    for code, info in COLOR_SYSTEM.items():
        colors.append({
            "id": code,
            "code": code,
            "name": info.get("luxura", code),
            "sku": info.get("sku", code),
            "seo": info.get("seo", ""),
            "type": info.get("type", "SOLID"),
            "tone": info.get("tone", "NEUTRE"),
            "level": info.get("level", 5),
            "hex": info.get("hex", "#808080")
        })
    
    # Trier par niveau de clarté
    colors.sort(key=lambda x: x["level"])
    
    return colors
