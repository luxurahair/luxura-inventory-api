"""
🍁 AMBIANCES QUÉBEC V2 - LIEUX UNIQUES & ACTUALITÉ
===================================================
Ambiances détaillées des plus beaux endroits du Québec.
Anti-redondance: chaque lieu a sa personnalité unique.

ACTUALITÉ MAI-JUIN 2026:
- Festival MURAL (5-15 juin) - art urbain Saint-Laurent
- Festival Jazz MTL (25 juin - 4 juil.) - Quartier des Spectacles
- Jardins Gamelin - terrasse festive mai-sept
- Pouzza Fest (15-17 mai) - punk rock
- Les Premiers Vendredis - Parc Olympique

TENDANCES BEAUTÉ 2026:
- Frange rideau style années 70
- Ondulations bohèmes gaufrées
- Cheveux ultra-longs glamour
- Balayage lumineux
- Prix Contessa 2026 - coiffure couture canadienne

NOTE: JAMAIS de foulard/scarf dans les prompts d'images.
"""

import random
from datetime import datetime


# ============================================
# 🏔️ AMBIANCES UNIQUES - QUÉBEC (pas génériques!)
# ============================================

QUEBEC_UNIQUE_AMBIANCES = {
    # === MONTRÉAL ===
    "vieux_montreal_cobblestones": {
        "lieu": "Vieux-Montréal rue pavée",
        "ambiance": "European charm meets North American energy, century-old limestone buildings, gas-lit lanterns reflecting on wet cobblestones after rain, horse-drawn carriages passing by, intimate French bistro terraces",
        "vibe": "romantic European escape in Canada",
        "best_for": ["romantic", "evening", "fall"],
        "unique_details": "cobblestones, old stone walls, antique street lamps",
    },
    "terrasse_nelligan": {
        "lieu": "Terrasse Nelligan Vieux-Montréal",
        "ambiance": "Chic rooftop overlooking Notre-Dame Basilica, twinkling city lights, sophisticated Montreal crowd sipping local cocktails, string lights and lush greenery, sunset reflecting off church spires",
        "vibe": "glamorous Montreal nightlife",
        "best_for": ["evening", "summer", "date_night"],
        "unique_details": "basilica view, string lights, rooftop garden",
    },
    "plateau_colorful_stairs": {
        "lieu": "Escaliers colorés du Plateau Mont-Royal",
        "ambiance": "Iconic rainbow spiral staircases, vibrant street art murals, bohemian neighborhood vibes, local artists and creative types, café terraces spilling onto sidewalks, vintage shops and indie boutiques",
        "vibe": "artistic bohemian Montreal",
        "best_for": ["casual", "creative", "spring"],
        "unique_details": "colorful spiral stairs, street murals, artistic vibe",
    },
    "mont_royal_belvedere": {
        "lieu": "Belvédère Kondiaronk Mont-Royal",
        "ambiance": "Breathtaking panoramic view of downtown Montreal skyline, sunset painting the sky orange and pink, couples picnicking on grass, joggers on trails, iconic cross illuminated at dusk",
        "vibe": "nature escape with city panorama",
        "best_for": ["sunset", "romantic", "active"],
        "unique_details": "skyline view, illuminated cross, maple trees",
    },
    "jardins_gamelin": {
        "lieu": "Jardins Gamelin Quartier des Spectacles",
        "ambiance": "Urban oasis pop-up terrasse, DJ spinning chill beats, food trucks serving local cuisine, young Montreal crowd dancing under string lights, art installations and murals, festival energy",
        "vibe": "summer festival Montreal",
        "best_for": ["summer", "festival", "social"],
        "unique_details": "DJ booth, food trucks, urban garden",
        "event_2026": "Open mai-septembre 2026",
    },
    "mural_festival": {
        "lieu": "Boulevard Saint-Laurent Festival MURAL",
        "ambiance": "Live street art being created on building walls, international artists with spray cans, vibrant colors everywhere, music stages, trendy crowds admiring new murals, open-air museum energy",
        "vibe": "cutting-edge urban art scene",
        "best_for": ["summer", "creative", "trendy"],
        "unique_details": "live mural painting, street art, international artists",
        "event_2026": "Festival MURAL 5-15 juin 2026",
    },
    "w_hotel_rooftop": {
        "lieu": "Rooftop W Montréal",
        "ambiance": "Ultra-modern luxury rooftop, infinity pool vibes, stunning view of Old Montreal and river, fashionable clientele in designer wear, DJ playing house music, champagne flowing",
        "vibe": "luxury pool party Montreal",
        "best_for": ["summer", "luxury", "party"],
        "unique_details": "modern architecture, pool, skyline view",
    },
    "canal_lachine_bike": {
        "lieu": "Canal Lachine piste cyclable",
        "ambiance": "Scenic bike path along historic canal, converted factory lofts, trendy Atwater Market nearby, kayakers on water, sunset reflecting on canal, runners and cyclists, picnic on grass",
        "vibe": "active lifestyle Montreal",
        "best_for": ["active", "summer", "casual"],
        "unique_details": "canal reflections, industrial chic, bikes",
    },
    
    # === QUÉBEC CITY ===
    "chateau_frontenac_terrace": {
        "lieu": "Terrasse Dufferin Château Frontenac",
        "ambiance": "Iconic castle hotel backdrop, sweeping St. Lawrence River view, street performers and musicians, tourists and elegant locals, boardwalk promenade, fairy-tale European atmosphere",
        "vibe": "fairy-tale European elegance",
        "best_for": ["romantic", "iconic", "all_seasons"],
        "unique_details": "castle silhouette, river view, wooden boardwalk",
    },
    "petit_champlain": {
        "lieu": "Quartier Petit Champlain",
        "ambiance": "Narrow cobblestone streets, charming boutiques with hand-painted signs, stone buildings draped in flowers, intimate cafés, oldest commercial district in North America, romantic fairy-tale setting",
        "vibe": "old-world European charm",
        "best_for": ["romantic", "shopping", "photo_op"],
        "unique_details": "narrow streets, hanging flowers, stone walls",
    },
    "grande_allee_terrasse": {
        "lieu": "Grande Allée terrasse 5 à 7",
        "ambiance": "Quebec City's party street, packed terraces with young professionals, live music spilling from bars, Victorian mansions converted to restaurants, summer festival energy, flirty atmosphere",
        "vibe": "Quebec City nightlife hotspot",
        "best_for": ["party", "social", "summer"],
        "unique_details": "Victorian architecture, packed terraces, live music",
    },
    "plaines_abraham": {
        "lieu": "Plaines d'Abraham",
        "ambiance": "Historic battlefield turned urban park, panoramic city and river views, free summer concerts, picnickers on rolling hills, joggers at sunset, maple trees in fall colors",
        "vibe": "historic park with stunning views",
        "best_for": ["active", "concerts", "fall"],
        "unique_details": "open fields, historic cannons, maple trees",
    },
    "ile_orleans_vineyard": {
        "lieu": "Vignoble Île d'Orléans",
        "ambiance": "Rustic Quebec vineyard, rolling hills with grapevines, St. Lawrence River backdrop, charming century-old farmhouse, local wine tasting, agrotourism paradise, quintessential Quebec countryside",
        "vibe": "authentic Quebec wine country",
        "best_for": ["wine", "romantic", "fall"],
        "unique_details": "grapevines, farmhouse, river view",
    },
    
    # === CHARLEVOIX ===
    "manoir_richelieu_terrace": {
        "lieu": "Fairmont Manoir Richelieu Charlevoix",
        "ambiance": "Grand castle-like resort overlooking St. Lawrence, infinity pool with mountain backdrop, elegant guests in resort wear, world-class spa, sunset cocktails on panoramic terrace",
        "vibe": "luxury resort escape",
        "best_for": ["luxury", "spa", "romantic"],
        "unique_details": "castle architecture, infinity pool, mountain view",
    },
    "baie_st_paul_artistic": {
        "lieu": "Baie-Saint-Paul rue des artistes",
        "ambiance": "Charming artist village, galleries showcasing local painters, colorful heritage houses, Charlevoix mountains backdrop, creative energy everywhere, intimate cafés with local art on walls",
        "vibe": "artistic mountain village",
        "best_for": ["creative", "culture", "fall"],
        "unique_details": "art galleries, colorful houses, mountain backdrop",
    },
    "massif_charlevoix_train": {
        "lieu": "Le Massif de Charlevoix train panoramique",
        "ambiance": "Scenic train ride along cliff edge, breathtaking river and mountain views, vintage rail cars, gourmet dining onboard, fall foliage spectacular, unique Canadian experience",
        "vibe": "scenic luxury train journey",
        "best_for": ["fall", "unique", "romantic"],
        "unique_details": "train windows, cliff views, fall colors",
    },
    
    # === LAURENTIDES ===
    "tremblant_village_pedestrian": {
        "lieu": "Village piétonnier Mont-Tremblant",
        "ambiance": "Colorful European-style pedestrian village, boutiques and restaurants with terraces, gondola rising to summit, après-ski vibes year-round, live music in village square, mountain backdrop",
        "vibe": "European mountain resort",
        "best_for": ["resort", "shopping", "all_seasons"],
        "unique_details": "colorful buildings, gondola, cobblestone paths",
    },
    "scandinave_spa_tremblant": {
        "lieu": "Scandinave Spa Mont-Tremblant",
        "ambiance": "Nordic spa in forest setting, outdoor hot baths with mountain view, steam rising into cool air, silence rule for ultimate relaxation, snow-covered trees in winter, ultimate self-care escape",
        "vibe": "zen forest spa sanctuary",
        "best_for": ["spa", "wellness", "winter"],
        "unique_details": "outdoor baths, forest setting, steam and snow",
    },
    "lac_tremblant_dock": {
        "lieu": "Lac Tremblant quai privé",
        "ambiance": "Crystal clear lake surrounded by mountains, private dock with Muskoka chairs, sunset reflecting on calm water, loons calling in distance, ultimate cottage country luxury",
        "vibe": "lakeside luxury retreat",
        "best_for": ["summer", "peaceful", "romantic"],
        "unique_details": "wooden dock, calm lake, mountain reflection",
    },
    "st_sauveur_main_street": {
        "lieu": "Rue Principale Saint-Sauveur",
        "ambiance": "Bustling mountain town main street, terraces packed with weekenders from Montreal, outlet shopping, live street performers, après-ski energy even in summer, Laurentian gateway vibe",
        "vibe": "lively mountain town",
        "best_for": ["shopping", "casual", "social"],
        "unique_details": "boutiques, crowded terraces, mountain town",
    },
    
    # === CANTONS-DE-L'EST ===
    "spa_eastman_zen": {
        "lieu": "Spa Eastman terrasse zen",
        "ambiance": "Holistic spa retreat, yoga pavilion overlooking gardens, organic farm-to-table restaurant, meditation paths through forest, wellness-focused clientele, disconnect from city life",
        "vibe": "wellness retreat sanctuary",
        "best_for": ["wellness", "detox", "quiet"],
        "unique_details": "yoga pavilion, organic garden, meditation paths",
    },
    "orpailleur_vineyard": {
        "lieu": "Vignoble de l'Orpailleur Dunham",
        "ambiance": "Award-winning Quebec vineyard, tasting room with vineyard views, fall harvest atmosphere, cycling tourists on wine route, rustic-chic barn venue, local cheese pairings",
        "vibe": "Quebec wine country sophistication",
        "best_for": ["wine", "fall", "cycling"],
        "unique_details": "vineyard rows, tasting glasses, rustic barn",
    },
    "north_hatley_auberge": {
        "lieu": "North Hatley auberge au lac",
        "ambiance": "Charming English-style village, Victorian inn on Lake Massawippi, sailboats and kayaks, literary history (homeland of poets), intimate fine dining, New England charm in Quebec",
        "vibe": "English village lakeside charm",
        "best_for": ["romantic", "quiet", "literary"],
        "unique_details": "Victorian inn, sailboats, English gardens",
    },
    
    # === ÎLES & CÔTES ===
    "madeleine_red_cliffs": {
        "lieu": "Îles-de-la-Madeleine falaises rouges",
        "ambiance": "Dramatic red sandstone cliffs meeting turquoise water, wild wind in hair, untouched beaches, colorful fishing villages, kite surfers riding waves, remote island paradise feel",
        "vibe": "wild island escape",
        "best_for": ["adventure", "nature", "unique"],
        "unique_details": "red cliffs, turquoise water, windswept beaches",
    },
    "tadoussac_whale_watching": {
        "lieu": "Tadoussac terrasse vue fjord",
        "ambiance": "Where river meets ocean, whale watching boats departing, historic red-roof hotel, dramatic fjord walls rising, marine biologists and nature lovers, raw natural beauty",
        "vibe": "nature adventure basecamp",
        "best_for": ["nature", "adventure", "summer"],
        "unique_details": "fjord view, whale watching boats, historic hotel",
    },
    "perce_rock_sunset": {
        "lieu": "Percé vue sur le Rocher",
        "ambiance": "Iconic pierced rock formation, Bonaventure Island gannet colony, dramatic Gaspésie coastline, sunset painting sky behind the rock, quintessential Quebec landmark",
        "vibe": "iconic Quebec natural wonder",
        "best_for": ["sunset", "nature", "iconic"],
        "unique_details": "rock formation, seabirds, dramatic coastline",
    },
}


# ============================================
# 📰 ACTUALITÉ / TENDANCES 2026
# ============================================

TRENDS_2026 = {
    "hair": [
        "frange rideau style années 70",
        "ondulations bohèmes gaufrées",
        "cheveux ultra-longs ondulés glamour",
        "balayage lumineux dimension",
        "clavicut épaules Hailey Bieber",
        "texture spray anti-humidité",
    ],
    "events_mai_juin": [
        {"name": "Festival MURAL", "dates": "5-15 juin", "lieu": "Boul. Saint-Laurent"},
        {"name": "Festival Jazz MTL", "dates": "25 juin - 4 juil", "lieu": "Quartier des Spectacles"},
        {"name": "Jardins Gamelin", "dates": "mai-sept", "lieu": "Quartier des Spectacles"},
        {"name": "Pouzza Fest", "dates": "15-17 mai", "lieu": "Quartier des Spectacles"},
        {"name": "Les Premiers Vendredis", "dates": "mensuel", "lieu": "Parc Olympique"},
        {"name": "Festival Fringe", "dates": "27 mai - 16 juin", "lieu": "Plateau"},
    ],
    "terrasses_hot": [
        "Terrasse Nelligan - vue basilique",
        "Jardins Gamelin - DJ et food trucks",
        "Grande Allée - 5 à 7 festif",
        "W Montréal rooftop - piscine luxe",
    ],
}


# ============================================
# 🎯 GÉNÉRATEUR ANTI-REDONDANCE
# ============================================

# Tracking pour éviter répétitions
_used_ambiances = []
_used_trends = []


def get_unique_quebec_ambiance(
    mood: str = None,
    season: str = None,
    exclude_recent: int = 5
) -> dict:
    """
    Retourne une ambiance UNIQUE, pas déjà utilisée récemment.
    
    Args:
        mood: romantic, party, nature, luxury, creative, etc.
        season: summer, fall, winter, spring
        exclude_recent: nombre d'ambiances récentes à exclure
    """
    global _used_ambiances
    
    # Filtrer par mood/season si spécifié
    candidates = []
    for key, amb in QUEBEC_UNIQUE_AMBIANCES.items():
        if key in _used_ambiances[-exclude_recent:]:
            continue
        if mood and mood not in amb.get("best_for", []):
            continue
        if season and season not in amb.get("best_for", []) and "all_seasons" not in amb.get("best_for", []):
            continue
        candidates.append((key, amb))
    
    # Fallback si pas assez de candidats
    if not candidates:
        candidates = list(QUEBEC_UNIQUE_AMBIANCES.items())
    
    # Sélection aléatoire
    key, ambiance = random.choice(candidates)
    
    # Tracking
    _used_ambiances.append(key)
    if len(_used_ambiances) > 20:
        _used_ambiances = _used_ambiances[-10:]
    
    return {
        "key": key,
        "lieu": ambiance["lieu"],
        "ambiance": ambiance["ambiance"],
        "vibe": ambiance["vibe"],
        "unique_details": ambiance.get("unique_details", ""),
        "event_2026": ambiance.get("event_2026"),
    }


def get_trending_content() -> dict:
    """Retourne du contenu tendance 2026 non répétitif."""
    global _used_trends
    
    # Sélectionner une tendance cheveux pas utilisée récemment
    available_trends = [t for t in TRENDS_2026["hair"] if t not in _used_trends[-3:]]
    if not available_trends:
        available_trends = TRENDS_2026["hair"]
    
    trend = random.choice(available_trends)
    _used_trends.append(trend)
    if len(_used_trends) > 10:
        _used_trends = _used_trends[-5:]
    
    # Sélectionner un événement actuel
    event = random.choice(TRENDS_2026["events_mai_juin"])
    
    return {
        "hair_trend": trend,
        "current_event": event,
        "hot_terrasse": random.choice(TRENDS_2026["terrasses_hot"]),
    }


def generate_unique_image_prompt(
    product_category: str = None,
    mood: str = None,
    include_trend: bool = True
) -> dict:
    """
    Génère un prompt d'image UNIQUE avec ambiance Québec et tendance.
    
    Returns:
        dict avec prompt, lieu, ambiance, trend
    """
    # Obtenir ambiance unique
    ambiance = get_unique_quebec_ambiance(mood=mood)
    
    # Obtenir tendance
    trend_data = get_trending_content() if include_trend else {}
    
    # Construire le prompt détaillé
    hair_style = trend_data.get("hair_trend", "long flowing voluminous hair")
    
    prompt = f"""Real photograph of a gorgeous sensual glamorous woman at {ambiance['lieu']}, 
{ambiance['ambiance']}, 
showing off her stunning {hair_style} hair extensions, 
{ambiance['unique_details']},
{ambiance['vibe']} atmosphere, 
golden hour natural lighting, authentic Instagram lifestyle photography,
no text, no watermarks"""
    
    # Clean up prompt
    prompt = " ".join(prompt.split())
    
    return {
        "prompt": prompt,
        "lieu": ambiance["lieu"],
        "ambiance_key": ambiance["key"],
        "vibe": ambiance["vibe"],
        "unique_details": ambiance["unique_details"],
        "hair_trend": trend_data.get("hair_trend"),
        "current_event": trend_data.get("current_event"),
        "event_2026": ambiance.get("event_2026"),
    }


def generate_batch_unique_prompts(count: int = 5) -> list:
    """Génère plusieurs prompts TOUS DIFFÉRENTS."""
    prompts = []
    for _ in range(count):
        prompts.append(generate_unique_image_prompt())
    return prompts


# ============================================
# TEST
# ============================================

if __name__ == "__main__":
    print("=" * 70)
    print("🍁 AMBIANCES QUÉBEC V2 - TEST ANTI-REDONDANCE")
    print("=" * 70)
    
    print(f"\n📍 {len(QUEBEC_UNIQUE_AMBIANCES)} ambiances uniques disponibles")
    
    print("\n🎯 TEST: 5 prompts TOUS DIFFÉRENTS:\n")
    
    prompts = generate_batch_unique_prompts(5)
    for i, p in enumerate(prompts, 1):
        print(f"[{i}] 📍 {p['lieu']}")
        print(f"    Vibe: {p['vibe']}")
        print(f"    Tendance: {p['hair_trend']}")
        if p.get('event_2026'):
            print(f"    🎉 Event 2026: {p['event_2026']}")
        print()
