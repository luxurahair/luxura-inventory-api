"""
🏖️ LUXURA IMAGE PROMPT RULES v5 - QUEBEC GLAMOUR EDITION
=========================================================
Règles centralisées pour toutes les générations d'images Luxura.

V5 DISTRIBUTION GÉOGRAPHIQUE:
- 70% QUÉBEC (les plus belles places)
- 15% CANADA (hors Québec)
- 15% INTERNATIONAL (Europe, Caraïbes, etc.)

V5 NOUVEAUTÉS:
- Détection automatique des SAISONS
- 50+ lieux QUÉBEC glamour
- Styles SENSUELS et SEXY
- Références culturelles québécoises
- Templates storytelling émotionnel

STYLE: Glamour, sensuel, élégant, SEXY - Focus femme québécoise 25-45 ans
"""

import random
from datetime import datetime


# ============================================
# 🗓️ DÉTECTION AUTOMATIQUE DES SAISONS
# ============================================

def get_current_season() -> str:
    """Détecte la saison actuelle au Québec."""
    month = datetime.now().month
    if month in [12, 1, 2]:
        return "winter"
    elif month in [3, 4, 5]:
        return "spring"
    elif month in [6, 7, 8]:
        return "summer"
    else:
        return "fall"


def get_seasonal_context() -> dict:
    """Retourne le contexte saisonnier complet."""
    season = get_current_season()
    month = datetime.now().month
    
    contexts = {
        "winter": {
            "season": "winter",
            "weather": ["snowy elegant", "cozy chic", "frosty glamour", "winter wonderland"],
            "clothing_style": ["luxurious fur coat", "elegant cashmere sweater dress", "chic wool ensemble", "designer winter coat"],
            "mood": ["warm intimate", "cozy glamour", "romantic winter"],
            "avoid": ["beach", "swimsuit", "summer dress", "tropical"],
            "events": ["Noël glamour", "Jour de l'An", "Saint-Valentin romantique", "Carnaval de Québec"],
        },
        "spring": {
            "season": "spring",
            "weather": ["blooming fresh", "soft spring light", "renewal energy"],
            "clothing_style": ["light elegant dress", "chic trench coat", "floral designer dress", "pastel silk blouse"],
            "mood": ["fresh romantic", "renewal beauty", "spring awakening"],
            "avoid": ["heavy winter coat", "snow", "Christmas"],
            "events": ["Pâques élégant", "Fête des Mères", "Festival de Jazz preview"],
        },
        "summer": {
            "season": "summer",
            "weather": ["sunny golden", "warm sensual", "tropical heat", "beach perfect"],
            "clothing_style": ["elegant bikini", "flowing summer dress", "chic sundress", "designer swimwear"],
            "mood": ["hot sensual", "beach glamour", "summer paradise", "sexy vacation"],
            "avoid": ["winter coat", "snow", "heavy clothing"],
            "events": ["Saint-Jean-Baptiste", "Festival de Jazz", "Grand Prix F1", "Vacances all-inclusive"],
        },
        "fall": {
            "season": "fall",
            "weather": ["golden leaves", "crisp autumn air", "warm harvest tones"],
            "clothing_style": ["elegant sweater dress", "chic leather jacket", "cashmere wrap", "designer fall outfit"],
            "mood": ["cozy sensual", "autumn romance", "harvest glamour"],
            "avoid": ["swimsuit", "beach", "heavy snow"],
            "events": ["Action de grâce", "Halloween chic", "5 à 7 d'automne"],
        }
    }
    return contexts[season]


# ============================================
# 🍁 LIEUX QUÉBEC - 70% DES PUBLICATIONS
# Les plus belles places du Québec
# ============================================

QUEBEC_LOCATIONS = {
    "summer": [
        # MONTRÉAL & ENVIRONS
        "terrasse rooftop du Ritz-Carlton Montréal avec vue sur la ville",
        "Vieux-Port de Montréal au coucher du soleil",
        "terrasse du Restaurant Toqué! Montréal",
        "jardin du Musée des Beaux-Arts de Montréal",
        "terrasse Nelligan dans le Vieux-Montréal",
        "rooftop bar du W Montréal au sunset",
        "Quartier DIX30 terrasse chic",
        "terrasse du Beaver Hall Montréal",
        "Mont-Royal belvédère Kondiaronk au golden hour",
        "Terrasse Place d'Armes Vieux-Montréal",
        
        # QUÉBEC CITY
        "terrasse du Château Frontenac avec vue sur le fleuve",
        "Petit Champlain rue pavée romantique",
        "terrasse du Fairmont Le Château Frontenac",
        "Plaines d'Abraham au coucher du soleil",
        "Île d'Orléans vignoble avec vue sur Québec",
        "terrasse du Château Bonne Entente",
        "Vieux-Québec fortifications romantiques",
        
        # CHARLEVOIX
        "terrasse du Fairmont Le Manoir Richelieu Charlevoix",
        "Baie-Saint-Paul galerie d'art terrasse",
        "La Malbaie vue sur le fleuve",
        "Isle-aux-Coudres paysage bucolique",
        "Route des Saveurs Charlevoix vignoble",
        
        # LAURENTIDES
        "terrasse du Fairmont Tremblant avec vue sur le lac",
        "village piétonnier Mont-Tremblant été",
        "Scandinave Spa Mont-Tremblant bains nordiques",
        "lac Tremblant plage privée",
        "Sainte-Adèle terrasse avec vue montagne",
        "Saint-Sauveur terrasse rue principale",
        "lac des Sables Sainte-Agathe",
        
        # CANTONS-DE-L'EST
        "Spa Eastman terrasse zen",
        "vignoble Orpailleur Dunham dégustation",
        "lac Memphrémagog Magog terrasse",
        "North Hatley auberge romantique",
        "Bromont terrasse avec vue montagne",
        "Sutton village charmant terrasse",
        
        # ÎLES & CÔTES
        "Îles-de-la-Madeleine plage de sable rouge",
        "Tadoussac terrasse vue sur le fjord",
        "Percé avec le Rocher en arrière-plan",
        "Kamouraska village côtier pittoresque",
        "Rimouski coucher de soleil sur le fleuve",
        
        # AUTRES RÉGIONS
        "Mauricie parc national terrasse lodge",
        "Saguenay fjord vue spectaculaire",
        "Lac-Saint-Jean plage sablonneuse",
        "Gaspésie côte sauvage glamour",
    ],
    
    "fall": [
        # LAURENTIDES AUTOMNE
        "Mont-Tremblant gondole avec feuillages spectaculaires",
        "Scandinave Spa Tremblant vapeur et couleurs d'automne",
        "Route 117 Laurentides panorama automnal",
        "lac Tremblant reflet des feuilles dorées",
        "Saint-Sauveur terrasse couleurs d'automne",
        "Sainte-Adèle forêt en feu de couleurs",
        
        # CHARLEVOIX AUTOMNE
        "Charlevoix Route des Saveurs récolte",
        "Baie-Saint-Paul feuillages artistiques",
        "Le Massif de Charlevoix train panoramique automne",
        "La Malbaie domaine Forget couleurs",
        
        # CANTONS-DE-L'EST AUTOMNE
        "vignoble Cantons-de-l'Est vendanges",
        "Sutton montagne en couleurs",
        "Knowlton village anglais automnal",
        "Orford parc national feuillages",
        "Magog lac avec couleurs automnales",
        
        # QUÉBEC AUTOMNE
        "Île d'Orléans récolte de pommes",
        "Plaines d'Abraham feuilles dorées",
        "Vieux-Québec terrasse automne",
        "Château Frontenac couleurs d'automne",
        
        # MONTRÉAL AUTOMNE
        "Mont-Royal belvédère couleurs spectaculaires",
        "Vieux-Montréal pavés et feuilles mortes",
        "Jardin botanique de Montréal automne",
        "Canal Lachine promenade automnale",
    ],
    
    "winter": [
        # SKI & MONTAGNE
        "chalet luxueux Mont-Tremblant feu de foyer",
        "village Mont-Tremblant décorations de Noël",
        "Scandinave Spa Tremblant bains chauds neige",
        "terrasse ski-in/ski-out Tremblant",
        "Le Massif de Charlevoix ski avec vue fleuve",
        "Bromont chalet après-ski élégant",
        
        # QUÉBEC HIVER
        "Château Frontenac Noël féerique",
        "Carnaval de Québec palais de glace",
        "Vieux-Québec rues enneigées romantiques",
        "Petit Champlain décorations hivernales",
        "Hôtel de Glace Québec",
        
        # MONTRÉAL HIVER
        "Vieux-Montréal lumières de Noël",
        "patinoire Atrium 1000 De La Gauchetière",
        "Ritz-Carlton Montréal lobby cozy",
        "Saint-Denis cafés chaleureux hiver",
        
        # SPA HIVER
        "Strøm Spa Nordique Vieux-Montréal neige",
        "Bota Bota spa sur l'eau hiver",
        "Spa Scandinave Tremblant aurore boréale",
    ],
    
    "spring": [
        # MONTRÉAL PRINTEMPS
        "Jardin botanique Montréal floraison",
        "Mont-Royal cerisiers en fleurs",
        "Vieux-Port terrasses qui ouvrent",
        "canal Lachine vélo et tulipes",
        
        # QUÉBEC PRINTEMPS  
        "Plaines d'Abraham tulipes",
        "Île d'Orléans vergers en fleurs",
        "Château Frontenac terrasse printemps",
        
        # AUTRES
        "Ottawa tulipes (proche Québec)",
        "Charlevoix réveil printanier",
        "Cantons-de-l'Est vignobles bourgeonnants",
    ],
}


# ============================================
# 🍁 LIEUX CANADA (HORS QC) - 15%
# ============================================

CANADA_LOCATIONS = {
    "summer": [
        "Toronto Yorkville rooftop terrasse chic",
        "Vancouver waterfront restaurant sunset",
        "Whistler village d'été terrasse montagne",
        "Banff Springs Hotel terrasse Rocheuses",
        "Lake Louise turquoise waters",
        "Muskoka lakeside cottage dock Ontario",
        "Niagara-on-the-Lake wine estate terrace",
        "Prince Edward County vineyard sunset",
        "Halifax waterfront boardwalk",
        "Victoria Inner Harbour afternoon tea",
        "Tofino beach Pacific Rim",
        "Kelowna Okanagan wine country",
    ],
    "fall": [
        "Muskoka fall colors lakeside Ontario",
        "Niagara wine region harvest",
        "Algonquin Park autumn panorama",
        "Ottawa Parliament autumn colors",
        "Vancouver Stanley Park fall",
        "Toronto Distillery District autumn",
    ],
    "winter": [
        "Whistler ski village après-ski",
        "Banff hot springs winter",
        "Lake Louise frozen fairytale",
        "Toronto CN Tower winter lights",
        "Vancouver Grouse Mountain snow",
    ],
    "spring": [
        "Vancouver cherry blossoms Stanley Park",
        "Ottawa tulip festival",
        "Toronto High Park spring bloom",
        "Victoria Butchart Gardens",
        "Niagara Falls spring rainbow",
    ],
}


# ============================================
# 🌍 LIEUX INTERNATIONAUX - 15%
# ============================================

INTERNATIONAL_LOCATIONS = {
    "summer": [
        # CARAÏBES (populaire pour vacances QC)
        "Punta Cana all-inclusive beach resort",
        "Cancun Riviera Maya plage turquoise",
        "Cuba Varadero plage paradisiaque",
        "République Dominicaine resort luxueux",
        "Aruba Palm Beach sunset",
        
        # EUROPE
        "Amalfi Coast Italy terrasse vue mer",
        "Santorini Greece white buildings sunset",
        "Monaco yacht harbor glamour",
        "Paris rooftop Eiffel Tower view",
        "Barcelona beach club Mediterranean",
        "Ibiza sunset beach party",
        "Côte d'Azur Saint-Tropez beach club",
        "Positano Italy colorful coastline",
        
        # USA
        "Miami South Beach art deco",
        "Las Vegas pool party",
        "Malibu beach California",
        "New York rooftop Manhattan skyline",
    ],
    "fall": [
        "Tuscany vineyard harvest Italy",
        "Paris autumn Champs-Élysées",
        "New York Central Park fall colors",
        "Napa Valley wine country autumn",
    ],
    "winter": [
        "Maldives winter sun escape",
        "Dubai beach winter warmth",
        "Caribbean cruise ship deck",
        "Mexican Riviera resort",
        "Swiss Alps ski chalet luxury",
        "Aspen Colorado ski lodge",
    ],
    "spring": [
        "Paris cherry blossoms Trocadéro",
        "Amsterdam tulip fields",
        "Japan cherry blossom garden",
        "Greek Islands early season",
    ],
}


# ============================================
# 📍 SÉLECTEUR DE LIEU AVEC DISTRIBUTION 70/15/15
# ============================================

def get_location_by_distribution(season: str = None) -> tuple:
    """
    Retourne un lieu selon la distribution:
    - 70% Québec
    - 15% Canada (hors QC)
    - 15% International
    
    Returns: (location_string, region_type)
    """
    if season is None:
        season = get_current_season()
    
    # Déterminer la région selon probabilité
    rand = random.random()
    
    if rand < 0.70:  # 70% Québec
        region = "quebec"
        locations = QUEBEC_LOCATIONS.get(season, QUEBEC_LOCATIONS["summer"])
    elif rand < 0.85:  # 15% Canada
        region = "canada"
        locations = CANADA_LOCATIONS.get(season, CANADA_LOCATIONS["summer"])
    else:  # 15% International
        region = "international"
        locations = INTERNATIONAL_LOCATIONS.get(season, INTERNATIONAL_LOCATIONS["summer"])
    
    location = random.choice(locations) if locations else "terrasse luxueuse avec vue"
    return (location, region)


# ============================================
# 👗 TENUES GLAMOUR SEXY PAR SAISON
# ============================================

GLAMOROUS_OUTFITS = {
    "beach_summer": [
        "elegant high-cut one-piece swimsuit showing curves",
        "chic designer bikini with flowing sheer sarong",
        "barely-there string bikini with gold accents",
        "sexy cutout one-piece revealing toned body",
        "Brazilian cut bikini flattering silhouette",
    ],
    "evening": [
        "flowing red silk backless evening gown",
        "elegant black plunging neckline cocktail dress",
        "champagne silk body-hugging maxi dress",
        "designer sequined gown with thigh-high slit",
        "stunning red carpet backless dress",
    ],
    "daytime_summer": [
        "chic white mini sundress showing legs",
        "elegant silk slip dress",
        "designer flowy maxi dress with deep neckline",
        "sexy off-shoulder top with flowing pants",
        "sophisticated short summer dress",
    ],
    "daytime_spring": [
        "elegant trench coat over silk dress",
        "chic pastel designer dress",
        "sophisticated floral midi dress",
        "light cashmere sweater dress",
    ],
    "daytime_fall": [
        "elegant sweater dress hugging curves",
        "chic leather pants with cashmere top",
        "sophisticated wool coat over silk blouse",
        "designer fall dress with knee-high boots",
    ],
    "winter_outdoor": [
        "luxurious fur coat showing elegant figure",
        "designer cashmere coat with sexy boots",
        "chic ski outfit flattering silhouette",
        "elegant wool coat with fur trim",
    ],
    "winter_indoor": [
        "cozy cashmere sweater dress",
        "elegant silk robe by fireplace",
        "chic loungewear showing figure",
    ],
    "spa": [
        "elegant white spa robe slightly open",
        "chic towel wrap showing shoulders",
        "luxury swimsuit at thermal baths",
    ],
}


# ============================================
# 💇 DESCRIPTIONS CHEVEUX LUXURA
# ============================================

LUXURA_HAIR_DESCRIPTIONS = [
    # BLONDES
    "spectacular platinum blonde flowing mane with incredible volume",
    "sun-kissed honey blonde waves cascading past shoulders",
    "cool ash blonde hair with editorial-worthy volume",
    "golden highlighted extensions catching light beautifully",
    "creamy blonde balayage with beachy textured waves",
    
    # BRUNETTES
    "rich chocolate brown cascading waves with stunning shine",
    "deep espresso brown voluminous curls Hollywood glamour",
    "glossy chestnut hair extensions flowing dramatically",
    "dimensional brunette balayage with sophisticated volume",
    "warm caramel highlights through thick brown waves",
    
    # AUBURN/RED
    "fiery auburn hair extensions flowing in the breeze",
    "warm copper tones in thick voluminous sensual waves",
    "rich burgundy tinted hair with luxurious body",
    "strawberry blonde waves with romantic soft curls",
    
    # BLACK
    "sleek jet black hair with mirror-like shine dramatic length",
    "raven black voluminous waves with blue undertones",
    
    # SPECIAL
    "honey blonde ombre fading from dark roots beautifully",
    "mermaid-length flowing hair romantic soft waves",
    "natural brunette extensions with effortless glamour",
]


# ============================================
# 💃 POSES ET EXPRESSIONS SENSUELLES
# ============================================

SENSUAL_POSES = [
    "running fingers seductively through her hair",
    "hair caught in gentle breeze revealing elegant neck",
    "tossing hair back with confident sexy movement",
    "wind-swept hair moment eyes half-closed",
    "touching her hair softly with knowing smile",
    "hair dramatically blowing looking over shoulder",
    "arching back showing curves hair flowing down",
    "hand on hip hair cascading sensually",
    "turning head with smoldering gaze",
    "walking away hair bouncing showing figure",
]

SENSUAL_EXPRESSIONS = [
    "mysterious confident smirk",
    "sultry bedroom eyes",
    "playful seductive look",
    "dreamy sensual gaze",
    "confident radiant smile",
    "intense passionate expression",
    "natural candid sexy moment",
    "joyful carefree laughing",
    "smoldering come-hither look",
    "innocent yet knowing expression",
]

SENSUAL_ANGLES = [
    "from 3/4 back angle showing curves and hair",
    "in semi-profile highlighting silhouette",
    "looking over her bare shoulder seductively",
    "turning head with hair in dramatic motion",
    "from behind showing hair length and figure",
    "side profile with hair flowing down back",
]


# ============================================
# 🎯 GÉNÉRATEUR DE PROMPTS V5 (70/15/15)
# ============================================

def generate_luxura_image_prompt(
    context: str = "general",
    force_season: str = None,
    sexy_level: str = "elegant_sexy",
) -> str:
    """
    Génère un prompt d'image style Luxura V5.
    Distribution: 70% Québec, 15% Canada, 15% International
    """
    season = force_season or get_current_season()
    seasonal_ctx = get_seasonal_context()
    
    # Obtenir lieu avec distribution 70/15/15
    location, region = get_location_by_distribution(season)
    
    # Sélectionner la tenue appropriée
    if season == "summer":
        if any(x in location.lower() for x in ["beach", "plage", "piscine", "spa", "bain", "pool", "lac"]):
            outfit = random.choice(GLAMOROUS_OUTFITS["beach_summer"] + GLAMOROUS_OUTFITS["spa"])
        else:
            outfit = random.choice(GLAMOROUS_OUTFITS["daytime_summer"])
    elif season == "winter":
        if any(x in location.lower() for x in ["spa", "bain", "thermal"]):
            outfit = random.choice(GLAMOROUS_OUTFITS["spa"])
        elif any(x in location.lower() for x in ["chalet", "ski", "feu", "foyer"]):
            outfit = random.choice(GLAMOROUS_OUTFITS["winter_indoor"])
        else:
            outfit = random.choice(GLAMOROUS_OUTFITS["winter_outdoor"])
    elif season == "spring":
        outfit = random.choice(GLAMOROUS_OUTFITS["daytime_spring"])
    else:
        outfit = random.choice(GLAMOROUS_OUTFITS["daytime_fall"])
    
    # Contexte soirée override
    if any(x in location.lower() for x in ["gala", "casino", "opera", "ritz", "toqué", "restaurant"]):
        outfit = random.choice(GLAMOROUS_OUTFITS["evening"])
    
    # Sélections
    hair = random.choice(LUXURA_HAIR_DESCRIPTIONS)
    pose = random.choice(SENSUAL_POSES)
    expression = random.choice(SENSUAL_EXPRESSIONS)
    angle = random.choice(SENSUAL_ANGLES)
    weather = random.choice(seasonal_ctx['weather'])
    
    prompt = f"Real photograph of a sensual glamorous woman {angle} at {location}, {pose}, {hair}, wearing {outfit}, {expression}, {weather} natural lighting, seductive elegant mood, aspirational luxury lifestyle, no text, no watermarks"
    
    return prompt


def get_prompt_for_content_type(content_type: str) -> str:
    """Retourne un prompt adapté au type de contenu."""
    return generate_luxura_image_prompt(context=content_type)


# ============================================
# 📝 TEMPLATES STORYTELLING LUXURA
# Style émotionnel québécois
# ============================================

BLOG_TEMPLATES = {
    "transformation": {
        "title_templates": [
            "Comment {prenom} a retrouvé sa confiance (et son dating life) à {age} ans",
            "\"{probleme}\" : L'histoire de {prenom} qui a tout changé",
            "De invisible à irrésistible : La transformation de {prenom}",
            "{prenom}, {age} ans : \"Mon chum ne m'avait jamais vue comme ça\"",
        ],
        "intro_templates": [
            "{prenom} nous a écrit : \"{citation_probleme}\" Aujourd'hui, elle fait tourner les têtes. Voici son secret.",
            "Quand {prenom} est entrée dans notre salon, elle évitait les miroirs. Aujourd'hui, son Instagram explose.",
            "\"{citation_probleme}\" C'est ce que {prenom} nous a confié. Sa transformation va vous inspirer.",
        ],
        "emotional_hooks": [
            "😔 LE PROBLÈME QUE PERSONNE N'OSE AVOUER",
            "💡 LA DÉCOUVERTE QUI A TOUT CHANGÉ",
            "🔥 LE RÉSULTAT : DE \"INVISIBLE\" À \"IRRÉSISTIBLE\"",
            "💬 CE QUE SON CHUM LUI A DIT",
        ],
    },
    
    "occasion": {
        "title_templates": [
            "Mariage à {lieu_qc} : Le secret des cheveux de rêve",
            "Week-end entre copines à {lieu_qc} : Cheveux de déesse garantis",
            "Du bureau au 5 à 7 : Extensions qui font tourner les têtes",
            "Soirée {evenement} : Comment être LA plus belle de la soirée",
            "Vacances {destination} : Extensions parfaites pour le all-inclusive",
        ],
        "quebec_events": [
            "Grand Prix de Montréal",
            "Festival de Jazz",
            "Saint-Jean-Baptiste",
            "Noël au Château Frontenac",
            "Party de bureau",
            "5 à 7 sur une terrasse",
            "Brunch du dimanche",
        ],
    },
    
    "trend": {
        "title_templates": [
            "{couleur} à {lieu_qc} : La couleur qui fait craquer les Québécoises",
            "Tendance {tendance} : Pourquoi les femmes d'ici l'adorent",
            "Le look {celebrite} version Québec : Comment l'obtenir",
        ],
    },
    
    "seasonal": {
        "summer": {
            "titles": [
                "Extensions waterproof : Du Scandinave Spa à la piscine",
                "Été québécois : Les cheveux parfaits du lac au 5 à 7",
                "All-inclusive dans le Sud : Extensions qui survivent à TOUT",
            ],
        },
        "fall": {
            "titles": [
                "Automne à {lieu_qc} : La saison parfaite pour transformer vos cheveux",
                "Feuillages et cheveux de rêve : Le combo gagnant",
                "Du hoodie au cocktail : Extensions polyvalentes pour l'automne",
            ],
        },
        "winter": {
            "titles": [
                "Ski et glamour : Oui, c'est possible!",
                "Temps des Fêtes : Brillez plus que le sapin",
                "Du spa au chalet : Extensions qui endurent l'hiver québécois",
            ],
        },
        "spring": {
            "titles": [
                "Renouveau printanier : Transformez vos cheveux comme la nature",
                "Mariage de printemps : Le guide ultime des extensions",
            ],
        },
    },
}

# Prénoms québécois populaires pour storytelling
QUEBEC_PRENOMS = [
    "Marie-Ève", "Geneviève", "Karine", "Mélanie", "Stéphanie",
    "Caroline", "Isabelle", "Nathalie", "Julie", "Valérie",
    "Amélie", "Émilie", "Audrey", "Jessica", "Vanessa",
    "Laurie", "Maude", "Roxanne", "Chantal", "Sylvie",
    "Anne-Marie", "Marie-Claude", "Marie-Pier", "Sarah-Jeanne",
]

# Lieux QC pour les titres
QUEBEC_LIEUX_TITRES = [
    "Mont-Tremblant", "Charlevoix", "Château Frontenac",
    "Vieux-Montréal", "Vieux-Québec", "Laurentides",
    "Cantons-de-l'Est", "Tadoussac", "Îles-de-la-Madeleine",
    "Magog", "Bromont", "Saint-Sauveur", "Baie-Saint-Paul",
]

# Expressions québécoises pour authenticité
QUEBEC_EXPRESSIONS = {
    "boyfriend": "chum",
    "girlfriend": "blonde", 
    "party": "party",
    "hangover": "lendemain de veille",
    "bar_hopping": "5 à 7",
    "amazing": "malade",
    "beautiful": "belle en titi",
    "confidence": "confiance en soi",
    "transform": "se transformer",
    "weekend": "fin de semaine",
    "vacation": "vacances dans le Sud",
    "all_inclusive": "all-inclusive",
}


def generate_blog_title(template_type: str = "transformation") -> str:
    """Génère un titre de blog style Luxura."""
    templates = BLOG_TEMPLATES.get(template_type, BLOG_TEMPLATES["transformation"])
    title_template = random.choice(templates.get("title_templates", ["Transformation incroyable"]))
    
    # Remplacer les variables
    title = title_template.format(
        prenom=random.choice(QUEBEC_PRENOMS),
        age=random.randint(28, 45),
        lieu_qc=random.choice(QUEBEC_LIEUX_TITRES),
        probleme=random.choice(["Mes cheveux sont trop fins", "J'ai honte de mes cheveux", "Je ne me sens plus sexy"]),
        evenement=random.choice(BLOG_TEMPLATES["occasion"]["quebec_events"]),
        destination="dans le Sud",
        couleur=random.choice(["Mocha Mousse", "Caramel Highlights", "Honey Blonde"]),
        tendance=random.choice(["Ghost Waves", "Mermaid Length", "Money Pieces"]),
        celebrite=random.choice(["J.Lo", "Kim K", "Margot Robbie"]),
    )
    return title


def get_contextual_prompt(title: str, content: str = "") -> str:
    """Génère un prompt basé sur le titre et contenu."""
    full_text = f"{title} {content}".lower()
    season = get_current_season()
    
    location, region = get_location_by_distribution(season)
    hair = random.choice(LUXURA_HAIR_DESCRIPTIONS)
    pose = random.choice(SENSUAL_POSES)
    expression = random.choice(SENSUAL_EXPRESSIONS)
    
    # Contexte selon mots-clés
    if any(w in full_text for w in ["mariage", "wedding", "mariée"]):
        outfit = random.choice(GLAMOROUS_OUTFITS["evening"])
        mood = "romantic bridal elegance"
    elif any(w in full_text for w in ["spa", "scandinave", "bain", "piscine"]):
        outfit = random.choice(GLAMOROUS_OUTFITS["spa"])
        mood = "relaxed sensual spa vibes"
    elif any(w in full_text for w in ["5 à 7", "party", "soirée", "gala"]):
        outfit = random.choice(GLAMOROUS_OUTFITS["evening"])
        mood = "glamorous evening out"
    elif any(w in full_text for w in ["plage", "beach", "sud", "all-inclusive"]):
        outfit = random.choice(GLAMOROUS_OUTFITS["beach_summer"])
        mood = "tropical vacation glamour"
    else:
        seasonal_ctx = get_seasonal_context()
        outfit = random.choice(seasonal_ctx.get("clothing_style", ["elegant dress"]))
        mood = random.choice(seasonal_ctx.get("mood", ["elegant sensual"]))
    
    prompt = f"Real photograph of a sensual glamorous woman at {location}, {pose}, {hair}, wearing {outfit}, {expression}, {mood}, golden hour natural lighting, no text, no watermarks"
    
    return prompt


# ============================================
# 📱 SELFIES PRODUITS LUXURA - AVEC LIENS CLIQUABLES
# Pour annonces des vraies catégories de produits
# ============================================

PRODUCT_CATEGORIES = {
    "genius": {
        "name": "Genius Weft",
        "collection": "Vivian",
        "description": "extensions weft cousues ultra-plates",
        "benefits": ["invisibles", "légères", "volume naturel", "installation rapide"],
        "ideal_for": "volume maximal sans poids",
        "selfie_context": [
            "showing off her new voluminous weft extensions",
            "flipping her thick gorgeous hair from genius weft",
            "running fingers through her incredibly full hair",
            "showing the seamless blend of her new weft extensions",
        ],
        "hashtags": ["#GeniusWeft", "#VolumeMaximal", "#LuxuraGenius"],
    },
    "tape": {
        "name": "Tape Extensions", 
        "collection": "Aurora",
        "description": "extensions adhésives ultra-discrètes",
        "benefits": ["pose rapide 45min", "réutilisables", "indétectables", "confortables"],
        "ideal_for": "discrétion absolue et confort quotidien",
        "selfie_context": [
            "revealing her secret tape-in extensions",
            "showing how invisible her tape extensions are",
            "flaunting her natural-looking tape-in transformation",
            "proving tape extensions are undetectable",
        ],
        "hashtags": ["#TapeExtensions", "#AuroraCollection", "#LuxuraTape"],
    },
    "halo": {
        "name": "Halo Extensions",
        "collection": "Everly", 
        "description": "extensions fil invisible sans clips",
        "benefits": ["pose 60 secondes", "aucun dommage", "réversible", "facile"],
        "ideal_for": "transformation instantanée sans engagement",
        "selfie_context": [
            "after putting on her Halo in just 60 seconds",
            "showing her instant hair transformation with Halo",
            "loving her damage-free Halo extensions",
            "proving anyone can have long hair in a minute",
        ],
        "hashtags": ["#HaloExtensions", "#60Secondes", "#LuxuraHalo"],
    },
    "i-tip": {
        "name": "I-Tip Extensions",
        "collection": "Eleanor",
        "description": "extensions kératine micro-anneaux",
        "benefits": ["durée 4-6 mois", "mouvement naturel", "sans chaleur", "premium"],
        "ideal_for": "résultat longue durée haut de gamme",
        "selfie_context": [
            "4 months into her I-Tip journey still looking perfect",
            "showing the natural movement of her I-Tip extensions",
            "flaunting her premium keratin bond extensions",
            "loving how her I-Tips move like real hair",
        ],
        "hashtags": ["#ITipExtensions", "#EleanorCollection", "#LuxuraITip"],
    },
    "ponytail": {
        "name": "Queue de Cheval",
        "collection": "Victoria",
        "description": "ponytail clip-in glamour",
        "benefits": ["pose instantanée", "volume dramatique", "événements spéciaux"],
        "ideal_for": "look glamour pour occasions spéciales",
        "selfie_context": [
            "rocking her dramatic ponytail for date night",
            "showing off her red carpet worthy ponytail",
            "loving her instant glamour ponytail transformation",
            "proving a ponytail can be THIS dramatic",
        ],
        "hashtags": ["#PonytailExtensions", "#VictoriaCollection", "#LuxuraPonytail"],
    },
    "clip-in": {
        "name": "Extensions à Clips",
        "collection": "Sophia",
        "description": "extensions clips amovibles",
        "benefits": ["aucun engagement", "versatile", "weekend glamour", "DIY facile"],
        "ideal_for": "transformation occasionnelle sans engagement",
        "selfie_context": [
            "clip-ins in for the weekend vibes",
            "showing her DIY clip-in transformation",
            "loving how easy clip-ins are for special occasions",
            "weekend hair don't care with her clip-ins",
        ],
        "hashtags": ["#ClipInExtensions", "#SophiaCollection", "#LuxuraClips"],
    },
}

# Couleurs de cheveux pour matcher les produits
PRODUCT_HAIR_COLORS = {
    "blonde": ["Platine Pur #60A", "Champagne Doré #18/22", "Blond Balayage Doré", "Cendré Étoilé"],
    "brunette": ["Châtaigne Douce #3", "Chocolat Profond", "Caramel Doré #6", "Noisette Balayage"],
    "black": ["Onyx Noir #1", "Noir Soie #1B", "Noir Jet Black"],
    "auburn": ["Caramel Soleil", "Golden Hour", "Cuivré Oriental"],
    "ombre": ["Ombré Balayage", "Cachemire Oriental", "Cristal Polaire"],
}

# Contextes selfie glamour
SELFIE_CONTEXTS = {
    "mirror": [
        "taking a mirror selfie in her luxurious bathroom",
        "mirror selfie showing her new hair transformation",
        "bathroom vanity mirror selfie revealing gorgeous hair",
        "full-length mirror selfie flaunting her new look",
    ],
    "car": [
        "car selfie with perfect lighting showing her hair",
        "driving seat selfie with hair cascading over shoulder",
        "golden hour car selfie with stunning hair",
    ],
    "outdoor": [
        "outdoor selfie with wind in her beautiful hair",
        "terrasse selfie with hair glowing in sunset",
        "balcony selfie showing her glamorous mane",
    ],
    "event": [
        "getting ready selfie before her big night out",
        "pre-event selfie showing her special occasion hair",
        "date night ready selfie with perfect hair",
    ],
    "casual": [
        "casual cozy selfie with gorgeous flowing hair",
        "morning coffee selfie with effortlessly beautiful hair",
        "work from home selfie still looking glamorous",
    ],
}

# Expressions selfie
SELFIE_EXPRESSIONS = [
    "confident smile showing off her transformation",
    "sultry look into camera with hair framing face",
    "playful hair flip captured mid-motion",
    "serene confident gaze with perfect hair",
    "joyful candid moment touching her new hair",
    "mysterious half-smile with hair draped sensually",
    "proud confident expression showing results",
]

# Angles selfie
SELFIE_ANGLES = [
    "front-facing selfie angle",
    "slightly angled showing hair length",
    "side profile selfie showing volume",
    "looking over shoulder selfie",
    "hair flip action shot selfie",
]


def generate_product_selfie_prompt(
    category: str,
    hair_color_type: str = None,
    selfie_type: str = None,
) -> dict:
    """
    Génère un prompt selfie pour un produit spécifique.
    
    Args:
        category: genius, tape, halo, i-tip, ponytail, clip-in
        hair_color_type: blonde, brunette, black, auburn, ombre
        selfie_type: mirror, car, outdoor, event, casual
    
    Returns:
        dict avec prompt, product_info, hashtags, caption_template
    """
    if category not in PRODUCT_CATEGORIES:
        category = random.choice(list(PRODUCT_CATEGORIES.keys()))
    
    product = PRODUCT_CATEGORIES[category]
    
    # Sélectionner couleur de cheveux
    if hair_color_type is None:
        hair_color_type = random.choice(list(PRODUCT_HAIR_COLORS.keys()))
    hair_color = random.choice(PRODUCT_HAIR_COLORS.get(hair_color_type, PRODUCT_HAIR_COLORS["brunette"]))
    
    # Sélectionner type de selfie
    if selfie_type is None:
        selfie_type = random.choice(list(SELFIE_CONTEXTS.keys()))
    selfie_context = random.choice(SELFIE_CONTEXTS[selfie_type])
    
    # Contexte produit spécifique
    product_context = random.choice(product["selfie_context"])
    
    # Expression et angle
    expression = random.choice(SELFIE_EXPRESSIONS)
    angle = random.choice(SELFIE_ANGLES)
    
    # Construire le prompt
    prompt = f"Real photograph selfie of a gorgeous sensual woman {selfie_context}, {product_context}, {angle}, beautiful {hair_color_type} hair in shade {hair_color}, {expression}, iPhone quality natural selfie lighting, authentic social media style, glamorous yet relatable, no heavy filters, no text, no watermarks"
    
    # Template de caption pour les réseaux sociaux
    caption_templates = [
        f"Obsédée par mes nouvelles {product['name']} 😍 Collection {product['collection']} en {hair_color}! {' '.join(product['hashtags'])} #Luxura",
        f"Le secret de mes cheveux? {product['name']} {product['collection']} 💁‍♀️ {product['benefits'][0].capitalize()}! {' '.join(product['hashtags'])}",
        f"Transformation: AVANT vs APRÈS 🔥 Merci {product['name']}! {' '.join(product['hashtags'])} #TransformationCapillaire",
        f"Mon chum: \"T'as fait quoi à tes cheveux?!\" Moi: \"😏\" {' '.join(product['hashtags'])} #Luxura",
        f"60 secondes. C'est tout ce que ça prend. 💫 {product['name']} {product['collection']} {' '.join(product['hashtags'])}",
    ]
    
    return {
        "prompt": prompt,
        "category": category,
        "product_name": product["name"],
        "collection": product["collection"],
        "hair_color": hair_color,
        "hair_color_type": hair_color_type,
        "benefits": product["benefits"],
        "ideal_for": product["ideal_for"],
        "hashtags": product["hashtags"],
        "caption": random.choice(caption_templates),
        "product_link": f"/products?category={category}",
        "cta": f"Découvrez la collection {product['collection']} →",
    }


def generate_all_category_selfies() -> list:
    """
    Génère un selfie pour chaque catégorie de produits.
    Utile pour créer une campagne complète.
    """
    selfies = []
    for category in PRODUCT_CATEGORIES.keys():
        selfie = generate_product_selfie_prompt(category)
        selfies.append(selfie)
    return selfies


def get_product_selfie_for_ad(category: str, color_preference: str = None) -> dict:
    """
    Génère un selfie optimisé pour une publicité avec lien cliquable.
    
    Returns dict avec:
    - prompt: pour générer l'image
    - ad_copy: texte publicitaire
    - cta_button: texte du bouton
    - landing_url: URL de destination
    """
    selfie = generate_product_selfie_prompt(category, color_preference)
    
    product = PRODUCT_CATEGORIES[category]
    
    ad_copies = [
        f"✨ {product['name']} Collection {product['collection']}\n\n{product['ideal_for'].capitalize()}.\n\n💫 {' • '.join(product['benefits'][:3])}\n\n👇 Cliquez pour découvrir votre teinte parfaite",
        f"🔥 NOUVEAU: {product['name']}\n\nLe secret des cheveux de rêve?\nCollection {product['collection']} - {selfie['hair_color']}\n\n{product['benefits'][0].capitalize()} | {product['benefits'][1].capitalize()}\n\n💁‍♀️ Trouvez votre match parfait →",
        f"Elle a dit OUI aux {product['name']} 💍\n\nCollection {product['collection']} en {selfie['hair_color']}\n\n✅ {product['benefits'][0]}\n✅ {product['benefits'][1]}\n✅ {product['benefits'][2]}\n\n🛒 Découvrez maintenant",
    ]
    
    return {
        "prompt": selfie["prompt"],
        "ad_copy": random.choice(ad_copies),
        "cta_button": f"Voir {product['name']} →",
        "landing_url": f"https://luxuradistribution.com/products?category={category}",
        "category": category,
        "collection": product["collection"],
        "hashtags": selfie["hashtags"],
        "price_range": "À partir de 199$",
    }


# ============================================
# 📊 TEMPLATES POSTS PRODUITS POUR RÉSEAUX SOCIAUX
# ============================================

SOCIAL_MEDIA_TEMPLATES = {
    "instagram_post": {
        "format": "square",
        "template": """
{selfie_prompt}

---
CAPTION:
{caption}

HASHTAGS:
{hashtags}

CTA: Lien en bio 👆 ou DM pour commander
""",
    },
    "facebook_ad": {
        "format": "landscape",
        "template": """
{selfie_prompt}

---
AD COPY:
{ad_copy}

BUTTON: {cta_button}
URL: {landing_url}
""",
    },
    "story": {
        "format": "vertical",
        "template": """
{selfie_prompt}, vertical 9:16 format for Instagram story

---
OVERLAY TEXT: "{product_name} 🔥"
SWIPE UP: {landing_url}
""",
    },
}


def generate_social_media_post(category: str, platform: str = "instagram_post") -> dict:
    """
    Génère un post complet pour les réseaux sociaux.
    
    Args:
        category: catégorie de produit
        platform: instagram_post, facebook_ad, story
    
    Returns:
        dict avec prompt, caption, hashtags, etc.
    """
    selfie = generate_product_selfie_prompt(category)
    ad_data = get_product_selfie_for_ad(category)
    
    template = SOCIAL_MEDIA_TEMPLATES.get(platform, SOCIAL_MEDIA_TEMPLATES["instagram_post"])
    
    return {
        "platform": platform,
        "format": template["format"],
        "prompt": selfie["prompt"],
        "caption": selfie["caption"],
        "hashtags": " ".join(selfie["hashtags"]),
        "ad_copy": ad_data["ad_copy"],
        "cta_button": ad_data["cta_button"],
        "landing_url": ad_data["landing_url"],
        "product_name": selfie["product_name"],
        "collection": selfie["collection"],
    }


# ============================================
# TEST
# ============================================

if __name__ == "__main__":
    print(f"Saison: {get_current_season()}")
    print("\n--- TEST DISTRIBUTION 70/15/15 ---")
    
    stats = {"quebec": 0, "canada": 0, "international": 0}
    for _ in range(100):
        loc, region = get_location_by_distribution()
        stats[region] += 1
    
    print(f"Québec: {stats['quebec']}%")
    print(f"Canada: {stats['canada']}%")
    print(f"International: {stats['international']}%")
    
    print("\n--- EXEMPLES PROMPTS ---")
    for _ in range(3):
        print(generate_luxura_image_prompt()[:200] + "...")
        print()
    
    print("\n--- EXEMPLES TITRES BLOG ---")
    for _ in range(5):
        print(f"• {generate_blog_title()}")
    
    print("\n" + "=" * 70)
    print("📱 SELFIES PRODUITS LUXURA")
    print("=" * 70)
    
    for category in ["genius", "tape", "halo", "i-tip"]:
        selfie = generate_product_selfie_prompt(category)
        print(f"\n🏷️ {selfie['product_name']} ({selfie['collection']})")
        print(f"   Couleur: {selfie['hair_color']}")
        print(f"   Prompt: {selfie['prompt'][:150]}...")
        print(f"   Caption: {selfie['caption']}")
        print(f"   Lien: {selfie['product_link']}")

