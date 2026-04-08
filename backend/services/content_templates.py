"""
Luxura Distribution - Templates de contenu marketing
Positionnement: Importateur/Distributeur direct de rallonges capillaires premium au Québec

RÈGLES CRITIQUES:
- Luxura est un IMPORTATEUR/VENDEUR DIRECT, pas un salon de coiffure
- Ne JAMAIS mentionner "pose d'extensions" comme service
- Toujours mentionner: inventaire réel à St-Georges, livraison rapide, support français
- Numéro officiel: 418-222-3939
"""

from typing import List, Dict
from datetime import datetime, timedelta
import random

# ============ POSITIONNEMENT OFFICIEL ============

BRAND_POSITIONING = {
    "tagline": "Luxura Distribution – Importateur direct d'extensions capillaires professionnelles haut de gamme au Québec.",
    "sub_tagline": "Inventaire réel à St-Georges • Livraison rapide partout au Québec • Qualité Remy / Vierge • Adapté aux salons et aux clientes.",
    "phone": "418-222-3939",
    "website": "luxuradistribution.com",
    "location": "St-Georges, Québec",
    "salon_expo": "Salon Carouso",
    "advantages": [
        "Inventaire réel disponible immédiatement",
        "Livraison 1-2 jours partout au Québec",
        "Importateur direct = meilleurs prix",
        "Support en français",
        "Ramassage possible à St-Georges",
        "Qualité Remy / Vierge garantie"
    ]
}

# ============ TYPES DE CONTENU ============

CONTENT_CATEGORIES = {
    "product": {
        "emoji": "✨",
        "description": "Mise en vedette d'un produit spécifique",
        "frequency": 2  # fois par semaine
    },
    "educational": {
        "emoji": "📚",
        "description": "Contenu éducatif (méthodes, entretien, conseils)",
        "frequency": 2
    },
    "b2b_salon": {
        "emoji": "💼",
        "description": "Recrutement salons partenaires",
        "frequency": 1
    },
    "promo": {
        "emoji": "🔥",
        "description": "Offres spéciales et promotions",
        "frequency": 1
    },
    "local_trust": {
        "emoji": "🍁",
        "description": "Confiance locale, québécois",
        "frequency": 1
    }
}

# ============ PRODUITS VEDETTES ============

FEATURED_PRODUCTS = [
    {
        "name": "Genius Weft Série Vivian",
        "type": "genius_weft",
        "description": "Trame invisible ultra-légère, couture invisible, 100% cheveux naturels Remy",
        "benefits": ["Volume naturel sans démarcation", "Ultra-légère", "Pose rapide"],
        "ideal_for": "Volume naturel et discret"
    },
    {
        "name": "Bandes Adhésives Premium",
        "type": "tape_in",
        "description": "Extensions bandes adhésives haute tenue, cheveux Remy",
        "benefits": ["Tenue longue durée", "Volume important", "Réutilisables"],
        "ideal_for": "Volume et longueur durables"
    },
    {
        "name": "I-Tips Kératine",
        "type": "i_tips",
        "description": "Extensions pointe par pointe avec kératine",
        "benefits": ["Look très naturel", "Discrétion maximale", "Flexibilité de style"],
        "ideal_for": "Résultat naturel et personnalisé"
    },
    {
        "name": "Halo Luxura",
        "type": "halo",
        "description": "Extension fil invisible, pose en 5 minutes",
        "benefits": ["Aucune colle ni chaleur", "Pose soi-même", "Réutilisable"],
        "ideal_for": "Événements spéciaux, changement rapide"
    },
    {
        "name": "Micro Billes Premium",
        "type": "micro_beads",
        "description": "Extensions micro-anneaux sans chaleur",
        "benefits": ["Sans chaleur", "Ajustables", "Légères"],
        "ideal_for": "Cheveux fins ou fragiles"
    },
    {
        "name": "Fusion Froide",
        "type": "cold_fusion",
        "description": "Pose à froid avec ultrason",
        "benefits": ["Zéro dommage", "Liaison invisible", "Longue durée"],
        "ideal_for": "Protection maximale du cheveu"
    }
]

# ============ 8 TEMPLATES DE POSTS PRÊTS À L'EMPLOI ============

READY_TO_USE_POSTS = [
    # 1. Post vedette Genius Weft
    {
        "id": "genius_weft_star",
        "category": "product",
        "title": "Post Vedette Genius Weft",
        "photo_suggestion": "Paquet Genius Weft Série Vivian bien présenté + close-up texture",
        "caption": """✨ La trame invisible la plus discrète du marché est arrivée chez Luxura !

**Genius Weft Série Vivian** – ultra-légère, couture invisible, 100 % cheveux naturels Remy.

Idéale pour un volume naturel sans démarcation.
Disponible en plusieurs longueurs et couleurs.

Livraison rapide partout au Québec ! 🚚
👉 Voir tous les détails et commander : luxuradistribution.com

#GeniusWeft #ExtensionsQuebec #LuxuraDistribution #TrameInvisible #CheveuxNaturels""",
        "hashtags": ["GeniusWeft", "ExtensionsQuebec", "LuxuraDistribution", "TrameInvisible", "CheveuxNaturels"]
    },
    
    # 2. Carousel Comparatif
    {
        "id": "method_comparison",
        "category": "educational",
        "title": "Carousel Comparatif des Méthodes",
        "photo_suggestion": "6 slides : une photo par méthode (Genius Weft, Bande adhésive, I-Tips, Fusion froide, Micro bille, Halo)",
        "caption": """📚 Quelle méthode d'extensions convient le mieux à vos besoins ?

Swipe 👉 pour découvrir les avantages de chacune :
✅ Durée
✅ Confort
✅ Facilité d'application
✅ Prix

On a **tout en stock** à St-Georges ! 📦

Salon ou cliente ? Dites-nous en commentaire quelle méthode vous intéresse !

#ExtensionsCheveuxQuebec #TapeIn #ITips #FusionFroide #GeniusWeft #LuxuraDistribution""",
        "hashtags": ["ExtensionsCheveuxQuebec", "TapeIn", "ITips", "FusionFroide", "GeniusWeft"]
    },
    
    # 3. Reel Déballage
    {
        "id": "unboxing_reel",
        "category": "product",
        "title": "Reel Déballage + Texture",
        "photo_suggestion": "Vidéo : ouverture d'un paquet, texture, douceur, poids, mèches qui glissent",
        "caption": """👀 Ce qui arrive quand tu commandes chez Luxura Distribution...

Cheveux vierges, cuticules intactes, qualité pro directe importateur.

Pas d'intermédiaire = meilleur prix et fraîcheur garantie ✨

Livraison le lendemain au Québec ! 🚚

#Unboxing #ExtensionsPremium #LuxuraDistribution #CheveuxVierges #QualitePro""",
        "hashtags": ["Unboxing", "ExtensionsPremium", "LuxuraDistribution", "CheveuxVierges"]
    },
    
    # 4. Post B2B Salons
    {
        "id": "b2b_salon_partnership",
        "category": "b2b_salon",
        "title": "Post B2B Salons",
        "photo_suggestion": "Photo professionnelle du salon Carouso ou produits en présentation pro",
        "caption": """💼 On ouvre quelques nouveaux partenariats salons au Québec pour 2025-2026.

**Avantages Luxura :**
✅ Inventaire disponible immédiatement
✅ Prix distributeur avantageux
✅ Support technique & formation
✅ Livraison rapide

Intéressé(e) ? Message privé ou appelez au 418-222-3939 📞

On est à St-Georges (salon Carouso). Venez nous voir !

#PartenariatSalon #ExtensionsPro #DistributeurQuebec #LuxuraDistribution #SalonCoiffure""",
        "hashtags": ["PartenariatSalon", "ExtensionsPro", "DistributeurQuebec", "SalonCoiffure"]
    },
    
    # 5. Post Halo
    {
        "id": "halo_easy",
        "category": "product",
        "title": "Post Halo (Facile à vendre)",
        "photo_suggestion": "Photo du Halo posé ou démonstration de pose rapide",
        "caption": """⏱️ Tu veux du volume ou de la longueur en 5 minutes sans colle ni chaleur ?

Le **Halo Luxura** est parfait pour :
✨ Les événements spéciaux
✨ Les mamans occupées
✨ Celles qui veulent juste changer de look

Facile à poser soi-même et réutilisable ! 💫

En stock maintenant 👉 luxuradistribution.com

#HaloExtensions #ExtensionsFaciles #LuxuraDistribution #VolumeInstant #SansColle""",
        "hashtags": ["HaloExtensions", "ExtensionsFaciles", "VolumeInstant", "SansColle"]
    },
    
    # 6. Contenu Éducatif
    {
        "id": "tape_vs_genius",
        "category": "educational",
        "title": "Comparatif Bande vs Genius Weft",
        "photo_suggestion": "Photo côte à côte des deux méthodes",
        "caption": """📚 **Bande adhésive vs Genius Weft : lequel choisir ?**

➡️ **Bande adhésive** : tenue longue, volume important
➡️ **Genius Weft** : plus légère, invisible, pose ultra-rapide

On t'aide à choisir selon ton type de cheveux ! 💁‍♀️

Pose ta question en commentaire ou appelle-nous au 418-222-3939 📞

Tout est en stock à St-Georges !

#TapeIn #GeniusWeft #ConseilsExtensions #LuxuraDistribution #GuideExtensions""",
        "hashtags": ["TapeIn", "GeniusWeft", "ConseilsExtensions", "GuideExtensions"]
    },
    
    # 7. Post Local / Confiance
    {
        "id": "local_pride",
        "category": "local_trust",
        "title": "Post Local Québécois",
        "photo_suggestion": "Photo de l'équipe, du local ou des produits avec drapeau québécois",
        "caption": """🍁 Fier(e) d'être un distributeur 100 % québécois basé à St-Georges.

✅ Inventaire réel
✅ Support en français
✅ Livraison rapide sans douane
✅ Service personnalisé

Merci à toutes les clientes et salons qui nous font confiance depuis le début ! 🙏💛

#MadeInQuebec #DistributeurLocal #LuxuraDistribution #SupportLocal #ExtensionsQuebec""",
        "hashtags": ["MadeInQuebec", "DistributeurLocal", "SupportLocal", "ExtensionsQuebec"]
    },
    
    # 8. Offre Limitée
    {
        "id": "promo_vivian",
        "category": "promo",
        "title": "Offre Spéciale Vivian",
        "photo_suggestion": "Photo produit avec badge -10% ou bannière promo",
        "caption": """🔥 **Offre spéciale cette semaine !**

**-10 %** sur toutes les **Genius Weft Série Vivian** avec le code **VIVIAN10**

Valable jusqu'au {end_date}

Commande en ligne 👉 luxuradistribution.com

Livraison rapide partout au Québec ! 🚚

#Promo #GeniusWeft #LuxuraDistribution #OffreSpeciale #ExtensionsEnRabais""",
        "hashtags": ["Promo", "GeniusWeft", "OffreSpeciale", "ExtensionsEnRabais"],
        "variables": ["end_date"]
    }
]

# ============ GÉNÉRATEUR DE 10 LÉGENDES POUR 7 JOURS ============

def generate_weekly_content_plan(start_date: datetime = None) -> List[Dict]:
    """
    Génère un plan de contenu pour 7 jours avec 10 posts
    Mix optimal: 3 produits, 3 éducatifs, 2 B2B/local, 2 promos
    """
    
    if not start_date:
        start_date = datetime.now()
    
    weekly_plan = []
    
    # Distribution sur 7 jours
    schedule = [
        # Jour 1 - Lundi
        {"day": 0, "category": "product", "template_id": "genius_weft_star"},
        {"day": 0, "category": "educational", "template_id": "method_comparison"},
        # Jour 2 - Mardi  
        {"day": 1, "category": "b2b_salon", "template_id": "b2b_salon_partnership"},
        # Jour 3 - Mercredi
        {"day": 2, "category": "product", "template_id": "halo_easy"},
        {"day": 2, "category": "educational", "template_id": "tape_vs_genius"},
        # Jour 4 - Jeudi
        {"day": 3, "category": "local_trust", "template_id": "local_pride"},
        # Jour 5 - Vendredi
        {"day": 4, "category": "product", "template_id": "unboxing_reel"},
        {"day": 4, "category": "promo", "template_id": "promo_vivian"},
        # Jour 6 - Samedi
        {"day": 5, "category": "educational", "template_id": None},  # Généré dynamiquement
        # Jour 7 - Dimanche
        {"day": 6, "category": "product", "template_id": None}  # Généré dynamiquement
    ]
    
    for item in schedule:
        post_date = start_date + timedelta(days=item["day"])
        
        if item["template_id"]:
            template = next((t for t in READY_TO_USE_POSTS if t["id"] == item["template_id"]), None)
            if template:
                caption = template["caption"]
                # Remplacer les variables si nécessaire
                if "{end_date}" in caption:
                    promo_end = post_date + timedelta(days=7)
                    caption = caption.replace("{end_date}", promo_end.strftime("%d %B"))
                
                weekly_plan.append({
                    "date": post_date.strftime("%Y-%m-%d"),
                    "day_name": ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"][post_date.weekday()],
                    "category": item["category"],
                    "title": template["title"],
                    "photo_suggestion": template["photo_suggestion"],
                    "caption": caption,
                    "hashtags": template["hashtags"]
                })
        else:
            # Générer un post dynamique
            if item["category"] == "educational":
                weekly_plan.append(generate_educational_post(post_date))
            else:
                weekly_plan.append(generate_product_spotlight(post_date))
    
    return weekly_plan


def generate_educational_post(post_date: datetime) -> Dict:
    """Génère un post éducatif dynamique"""
    
    educational_topics = [
        {
            "title": "Comment entretenir ses extensions",
            "caption": """💆‍♀️ **Guide entretien : Comment garder vos extensions magnifiques ?**

1️⃣ Brossez délicatement de bas en haut
2️⃣ Utilisez des produits sans sulfate
3️⃣ Évitez la chaleur excessive
4️⃣ Dormez avec une tresse loose
5️⃣ Faites un masque hydratant 1x/semaine

Vos extensions dureront 2x plus longtemps ! ✨

Questions ? 418-222-3939 ou DM 📩

#EntretienExtensions #ConseilsBeaute #LuxuraDistribution #ExtensionsQuebec"""
        },
        {
            "title": "Différence cheveux Remy vs non-Remy",
            "caption": """🔬 **Remy vs Non-Remy : C'est quoi la différence ?**

**Cheveux Remy :**
✅ Cuticules alignées dans le même sens
✅ Moins d'emmêlement
✅ Brillance naturelle
✅ Durée de vie plus longue

**Non-Remy :**
❌ Cuticules enlevées chimiquement
❌ S'emmêlent plus vite
❌ Moins durables

Chez Luxura, on vend **UNIQUEMENT** du Remy/Vierge ! 💎

#CheveuxRemy #QualitePremium #LuxuraDistribution #ExtensionsPro"""
        }
    ]
    
    topic = random.choice(educational_topics)
    
    return {
        "date": post_date.strftime("%Y-%m-%d"),
        "day_name": ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"][post_date.weekday()],
        "category": "educational",
        "title": topic["title"],
        "photo_suggestion": "Infographie ou photo explicative",
        "caption": topic["caption"],
        "hashtags": ["ConseilsExtensions", "LuxuraDistribution", "ExtensionsQuebec"]
    }


def generate_product_spotlight(post_date: datetime) -> Dict:
    """Génère un spotlight produit dynamique"""
    
    product = random.choice(FEATURED_PRODUCTS)
    
    caption = f"""✨ **Spotlight produit : {product['name']}**

{product['description']}

**Avantages :**
{''.join([f"✅ {b}" + chr(10) for b in product['benefits']])}
👉 Idéal pour : {product['ideal_for']}

En stock à St-Georges ! Livraison rapide partout au Québec 🚚

Commandez : luxuradistribution.com
Questions : 418-222-3939

#LuxuraDistribution #{product['type'].replace('_', '').title()} #ExtensionsQuebec #QualitePro"""
    
    return {
        "date": post_date.strftime("%Y-%m-%d"),
        "day_name": ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"][post_date.weekday()],
        "category": "product",
        "title": f"Spotlight: {product['name']}",
        "photo_suggestion": f"Photo produit {product['name']} - fond blanc ou mannequin",
        "caption": caption,
        "hashtags": ["LuxuraDistribution", product['type'].replace('_', '').title(), "ExtensionsQuebec"]
    }


# ============ MÉTHODES D'EXTENSIONS (POUR PAGE WIX) ============

EXTENSION_METHODS = [
    {
        "name": "Genius Weft (Trame Invisible)",
        "slug": "genius-weft",
        "description": "La méthode la plus moderne et discrète du marché. La trame ultra-fine devient invisible une fois posée.",
        "duration": "4-6 mois avec entretien",
        "pose_time": "45-60 minutes",
        "maintenance": "Remontée toutes les 6-8 semaines",
        "ideal_for": "Cheveux fins à moyens, celles qui cherchent la discrétion absolue",
        "pros": [
            "Trame invisible, indétectable",
            "Ultra-légère et confortable",
            "Pose rapide",
            "Réutilisable plusieurs fois"
        ],
        "cons": [
            "Nécessite une technique de pose maîtrisée",
            "Prix légèrement supérieur"
        ],
        "price_range": "$$$$"
    },
    {
        "name": "Bandes Adhésives (Tape-In)",
        "slug": "tape-in",
        "description": "La méthode la plus populaire. Des bandes de cheveux se collent de part et d'autre de vos mèches naturelles.",
        "duration": "4-8 semaines entre les poses",
        "pose_time": "30-45 minutes",
        "maintenance": "Repose toutes les 6-8 semaines",
        "ideal_for": "Tous types de cheveux, parfait pour volume et longueur",
        "pros": [
            "Pose rapide et facile",
            "Très bon rapport qualité/prix",
            "Réutilisable 2-3 fois",
            "Confortable au quotidien"
        ],
        "cons": [
            "Éviter les produits gras près des racines",
            "Repositionnement régulier nécessaire"
        ],
        "price_range": "$$"
    },
    {
        "name": "I-Tips (Kératine)",
        "slug": "i-tips",
        "description": "Extensions posées mèche par mèche avec une liaison en kératine. Le résultat le plus naturel.",
        "duration": "4-6 mois",
        "pose_time": "2-4 heures",
        "maintenance": "Remontée tous les 3-4 mois",
        "ideal_for": "Celles qui veulent un look ultra-naturel et polyvalent",
        "pros": [
            "Résultat très naturel",
            "Flexibilité de coiffure totale",
            "Longue durée",
            "Personnalisation complète"
        ],
        "cons": [
            "Pose plus longue",
            "Dépose professionnelle requise"
        ],
        "price_range": "$$$"
    },
    {
        "name": "Micro Billes (Micro-Anneaux)",
        "slug": "micro-beads",
        "description": "Extensions fixées avec de petits anneaux métalliques, sans chaleur ni colle.",
        "duration": "3-4 mois",
        "pose_time": "2-3 heures",
        "maintenance": "Ajustement mensuel",
        "ideal_for": "Cheveux fins ou fragiles, celles qui évitent la chaleur",
        "pros": [
            "Aucune chaleur ni colle",
            "Ajustables facilement",
            "Pas de dommage chimique",
            "Idéal cheveux sensibles"
        ],
        "cons": [
            "Anneaux parfois visibles sur cheveux très fins",
            "Ajustements fréquents"
        ],
        "price_range": "$$"
    },
    {
        "name": "Fusion Froide (Ultrason)",
        "slug": "cold-fusion",
        "description": "Technologie ultrason qui crée une liaison invisible sans aucune chaleur. Le plus doux pour vos cheveux.",
        "duration": "4-6 mois",
        "pose_time": "2-3 heures",
        "maintenance": "Remontée tous les 3-4 mois",
        "ideal_for": "Cheveux déjà traités ou fragiles, protection maximale",
        "pros": [
            "Zéro chaleur = zéro dommage",
            "Liaison invisible",
            "Très confortable",
            "Longue durée"
        ],
        "cons": [
            "Équipement spécialisé requis",
            "Prix plus élevé"
        ],
        "price_range": "$$$$"
    },
    {
        "name": "Halo (Fil Invisible)",
        "slug": "halo",
        "description": "Extension sur fil transparent qui se pose sur la tête comme un serre-tête. Aucune fixation permanente.",
        "duration": "Réutilisable indéfiniment",
        "pose_time": "5 minutes",
        "maintenance": "Aucune, retirer chaque soir",
        "ideal_for": "Événements, essais, celles qui ne veulent pas d'engagement",
        "pros": [
            "Pose en 5 minutes soi-même",
            "Aucune colle ni chaleur",
            "Zéro dommage",
            "Réutilisable à l'infini",
            "Parfait pour essayer"
        ],
        "cons": [
            "Doit être retiré chaque soir",
            "Moins adapté au sport intensif"
        ],
        "price_range": "$"
    }
]


def generate_wix_methods_page() -> str:
    """
    Génère le contenu complet pour la page 'Nos méthodes d'extensions' sur Wix
    Format: HTML/Texte riche pour copier-coller dans Wix
    """
    
    content = """# Nos Méthodes d'Extensions Capillaires

**Luxura Distribution** vous offre les 6 meilleures méthodes d'extensions professionnelles, toutes en stock à St-Georges, Québec.

---

"""
    
    for method in EXTENSION_METHODS:
        content += f"""## {method['name']}

{method['description']}

**Durée de vie :** {method['duration']}  
**Temps de pose :** {method['pose_time']}  
**Entretien :** {method['maintenance']}  
**Idéal pour :** {method['ideal_for']}

### Avantages
{''.join([f"- {pro}" + chr(10) for pro in method['pros']])}
### Points à considérer
{''.join([f"- {con}" + chr(10) for con in method['cons']])}
**Gamme de prix :** {method['price_range']}

---

"""
    
    content += """
## Besoin d'aide pour choisir ?

Nos experts sont là pour vous guider vers la méthode parfaite selon votre type de cheveux, votre style de vie et votre budget.

**Appelez-nous :** 418-222-3939  
**Visitez notre showroom :** Salon Carouso, St-Georges, Québec  
**Commandez en ligne :** [luxuradistribution.com](https://www.luxuradistribution.com)

*Livraison rapide 1-2 jours partout au Québec !*
"""
    
    return content


# ============ API HELPER FUNCTIONS ============

def get_all_templates() -> List[Dict]:
    """Retourne tous les templates disponibles"""
    return READY_TO_USE_POSTS


def get_template_by_category(category: str) -> List[Dict]:
    """Retourne les templates d'une catégorie"""
    return [t for t in READY_TO_USE_POSTS if t["category"] == category]


def get_template_by_id(template_id: str) -> Dict:
    """Retourne un template par son ID"""
    return next((t for t in READY_TO_USE_POSTS if t["id"] == template_id), None)


def get_featured_products() -> List[Dict]:
    """Retourne la liste des produits vedettes"""
    return FEATURED_PRODUCTS


def get_extension_methods() -> List[Dict]:
    """Retourne les méthodes d'extensions pour la page Wix"""
    return EXTENSION_METHODS
