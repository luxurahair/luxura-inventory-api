# =====================================================
# BLOG AUTOMATION SYSTEM - Luxura Distribution
# Génération automatique + Publication Wix + Images DALL-E
# =====================================================

import os
import random
import uuid
import httpx
import asyncio
import json
import smtplib
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from datetime import datetime, timezone
from typing import Optional, List, Dict, Tuple
import logging

logger = logging.getLogger(__name__)

# Import du module de génération d'images
try:
    from image_generation import (
        generate_blog_image_with_dalle,
        generate_and_upload_blog_images,
        upload_image_bytes_to_wix,
        get_fallback_unsplash_image
    )
    DALLE_AVAILABLE = True
except ImportError:
    logger.warning("Image generation module not available, using Unsplash fallback")
    DALLE_AVAILABLE = False

# Import du module d'overlay de logo
try:
    from logo_overlay import process_image_with_logo, upload_image_with_logo_to_wix
    LOGO_OVERLAY_AVAILABLE = True
    logger.info("Logo overlay module loaded successfully")
except ImportError:
    logger.warning("Logo overlay module not available")
    LOGO_OVERLAY_AVAILABLE = False

# =====================================================
# EMAIL CONFIGURATION
# =====================================================

LUXURA_EMAIL = os.getenv("LUXURA_EMAIL", "info@luxuradistribution.com")
LUXURA_APP_PASSWORD = os.getenv("LUXURA_APP_PASSWORD")


async def send_blog_images_email(blogs: List[Dict], recipient_email: str = None):
    """
    Envoie un email avec les images des blogs générés.
    
    Args:
        blogs: Liste des blogs générés (avec 'title', 'image', 'wix_image_url')
        recipient_email: Email de destination (par défaut LUXURA_EMAIL)
    """
    if not LUXURA_APP_PASSWORD:
        logger.warning("LUXURA_APP_PASSWORD non configuré, email non envoyé")
        return False
    
    recipient = recipient_email or LUXURA_EMAIL
    
    try:
        # Créer le message
        msg = MIMEMultipart('related')
        msg['Subject'] = f"📸 Images Blog Luxura - {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        msg['From'] = LUXURA_EMAIL
        msg['To'] = recipient
        
        # Corps HTML avec les images
        html_content = """
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; padding: 20px; }
                .blog-card { margin-bottom: 30px; border: 1px solid #ddd; padding: 15px; border-radius: 8px; }
                .blog-title { color: #333; font-size: 18px; margin-bottom: 10px; }
                .blog-image { max-width: 600px; width: 100%; border-radius: 4px; }
                .image-urls { font-size: 12px; color: #666; margin-top: 10px; }
                a { color: #C9A66B; }
            </style>
        </head>
        <body>
            <h1>🌟 Blogs Luxura Générés</h1>
            <p>Voici les images des blogs générés automatiquement :</p>
        """
        
        for i, blog in enumerate(blogs):
            title = blog.get('title', 'Sans titre')
            unsplash_url = blog.get('image', '')
            wix_url = blog.get('wix_image_url', '')
            
            html_content += f"""
            <div class="blog-card">
                <h2 class="blog-title">{i+1}. {title}</h2>
                <p><strong>Image Unsplash :</strong></p>
                <img src="{unsplash_url}" class="blog-image" alt="{title}">
                <div class="image-urls">
                    <p>🔗 <strong>Unsplash:</strong> <a href="{unsplash_url}">{unsplash_url[:80]}...</a></p>
                    <p>📁 <strong>Wix Media:</strong> <a href="{wix_url}">{wix_url[:80]}...</a></p>
                </div>
            </div>
            """
        
        html_content += """
            <hr>
            <p style="color: #666; font-size: 12px;">
                Généré automatiquement par Luxura Blog Automation<br>
                Pour ajouter l'image de couverture manuellement sur Wix :<br>
                Dashboard → Blog → Article → Settings → Featured Image
            </p>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(html_content, 'html'))
        
        # Envoyer via Gmail SMTP
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(LUXURA_EMAIL, LUXURA_APP_PASSWORD)
            server.send_message(msg)
        
        logger.info(f"✅ Email envoyé à {recipient} avec {len(blogs)} images")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur envoi email: {e}")
        return False

# FORMAT OPEN GRAPH: 1200x630 px (ratio 1.91:1) pour Wix Blog Cover
# =============================================================================
# IMAGES LUXURA - STYLE SOIRÉE DE FILLES CHIC
# Plusieurs femmes avec cheveux TRÈS LONGS (jusqu'à la taille)
# Scènes sociales: autour d'une table, salon chic, champagne
# =============================================================================

# Images fournies par Luxura (style parfait - soirée de filles)
LUXURA_CUSTOM_IMAGES = [
    # Soirée chic - 4 femmes cheveux longs bruns
    "https://customer-assets.emergentagent.com/job_hair-extensions-shop/artifacts/no4frw3t_vaVsE.jpg",
    # Moment complicité - 3 femmes autour d'une table
    "https://customer-assets.emergentagent.com/job_hair-extensions-shop/artifacts/oyi6y21r_Aq7eZ.jpg",
    # Soirée élégante - 4 femmes cheveux longs ondulés
    "https://customer-assets.emergentagent.com/job_hair-extensions-shop/artifacts/21xcpk05_OdzWP.jpg",
]

# Images de secours - Style similaire sur Unsplash (plusieurs femmes, cheveux longs, ambiance chic)
UNSPLASH_LIFESTYLE_IMAGES = [
    # Groupe de femmes élégantes - brunch/soirée
    "https://images.unsplash.com/photo-1529156069898-49953e39b3ac?w=1200&h=630&fit=crop",  # Groupe amies riant
    "https://images.unsplash.com/photo-1543807535-eceef0bc6599?w=1200&h=630&fit=crop",  # Femmes cheveux longs
    "https://images.unsplash.com/photo-1522202176988-66273c2fd55f?w=1200&h=630&fit=crop",  # Groupe femmes table
    "https://images.unsplash.com/photo-1571508601891-ca5e7a713859?w=1200&h=630&fit=crop",  # Salon coiffure chic
    "https://images.unsplash.com/photo-1600948836101-f9ffda59d250?w=1200&h=630&fit=crop",  # Femme cheveux très longs
    "https://images.unsplash.com/photo-1519699047748-de8e457a634e?w=1200&h=630&fit=crop",  # Femme cheveux longs ondulés
    "https://images.unsplash.com/photo-1562259929-b4e1fd3aef09?w=1200&h=630&fit=crop",  # Groupe femmes élégantes
    "https://images.unsplash.com/photo-1596178060671-7a80dc8059ea?w=1200&h=630&fit=crop",  # Femme cheveux longs bruns
]

# Images par catégorie - Utilise les images Luxura en priorité
UNSPLASH_IMAGES = {
    "halo": [
        # Images Luxura personnalisées (soirée de filles)
        "https://customer-assets.emergentagent.com/job_hair-extensions-shop/artifacts/no4frw3t_vaVsE.jpg",
        "https://customer-assets.emergentagent.com/job_hair-extensions-shop/artifacts/oyi6y21r_Aq7eZ.jpg",
        "https://customer-assets.emergentagent.com/job_hair-extensions-shop/artifacts/21xcpk05_OdzWP.jpg",
        # Backup Unsplash lifestyle
        "https://images.unsplash.com/photo-1529156069898-49953e39b3ac?w=1200&h=630&fit=crop",
        "https://images.unsplash.com/photo-1600948836101-f9ffda59d250?w=1200&h=630&fit=crop",
    ],
    "genius": [
        # Images Luxura personnalisées
        "https://customer-assets.emergentagent.com/job_hair-extensions-shop/artifacts/21xcpk05_OdzWP.jpg",
        "https://customer-assets.emergentagent.com/job_hair-extensions-shop/artifacts/no4frw3t_vaVsE.jpg",
        "https://customer-assets.emergentagent.com/job_hair-extensions-shop/artifacts/oyi6y21r_Aq7eZ.jpg",
        # Backup
        "https://images.unsplash.com/photo-1519699047748-de8e457a634e?w=1200&h=630&fit=crop",
        "https://images.unsplash.com/photo-1596178060671-7a80dc8059ea?w=1200&h=630&fit=crop",
    ],
    "tape": [
        # Images Luxura personnalisées
        "https://customer-assets.emergentagent.com/job_hair-extensions-shop/artifacts/oyi6y21r_Aq7eZ.jpg",
        "https://customer-assets.emergentagent.com/job_hair-extensions-shop/artifacts/no4frw3t_vaVsE.jpg",
        "https://customer-assets.emergentagent.com/job_hair-extensions-shop/artifacts/21xcpk05_OdzWP.jpg",
        # Backup
        "https://images.unsplash.com/photo-1543807535-eceef0bc6599?w=1200&h=630&fit=crop",
        "https://images.unsplash.com/photo-1600948836101-f9ffda59d250?w=1200&h=630&fit=crop",
    ],
    "itip": [
        # Images Luxura personnalisées
        "https://customer-assets.emergentagent.com/job_hair-extensions-shop/artifacts/no4frw3t_vaVsE.jpg",
        "https://customer-assets.emergentagent.com/job_hair-extensions-shop/artifacts/21xcpk05_OdzWP.jpg",
        "https://customer-assets.emergentagent.com/job_hair-extensions-shop/artifacts/oyi6y21r_Aq7eZ.jpg",
        # Backup
        "https://images.unsplash.com/photo-1562259929-b4e1fd3aef09?w=1200&h=630&fit=crop",
        "https://images.unsplash.com/photo-1519699047748-de8e457a634e?w=1200&h=630&fit=crop",
    ],
    "entretien": [
        "https://customer-assets.emergentagent.com/job_hair-extensions-shop/artifacts/oyi6y21r_Aq7eZ.jpg",
        "https://customer-assets.emergentagent.com/job_hair-extensions-shop/artifacts/no4frw3t_vaVsE.jpg",
        "https://images.unsplash.com/photo-1571508601891-ca5e7a713859?w=1200&h=630&fit=crop",
        "https://images.unsplash.com/photo-1596178060671-7a80dc8059ea?w=1200&h=630&fit=crop",
    ],
    "tendances": [
        "https://customer-assets.emergentagent.com/job_hair-extensions-shop/artifacts/21xcpk05_OdzWP.jpg",
        "https://customer-assets.emergentagent.com/job_hair-extensions-shop/artifacts/no4frw3t_vaVsE.jpg",
        "https://images.unsplash.com/photo-1529156069898-49953e39b3ac?w=1200&h=630&fit=crop",
        "https://images.unsplash.com/photo-1562259929-b4e1fd3aef09?w=1200&h=630&fit=crop",
    ],
    "salon": [
        "https://customer-assets.emergentagent.com/job_hair-extensions-shop/artifacts/oyi6y21r_Aq7eZ.jpg",
        "https://customer-assets.emergentagent.com/job_hair-extensions-shop/artifacts/21xcpk05_OdzWP.jpg",
        "https://images.unsplash.com/photo-1571508601891-ca5e7a713859?w=1200&h=630&fit=crop",
        "https://images.unsplash.com/photo-1600948836101-f9ffda59d250?w=1200&h=630&fit=crop",
    ],
    "formation": [
        "https://customer-assets.emergentagent.com/job_hair-extensions-shop/artifacts/no4frw3t_vaVsE.jpg",
        "https://customer-assets.emergentagent.com/job_hair-extensions-shop/artifacts/oyi6y21r_Aq7eZ.jpg",
        "https://images.unsplash.com/photo-1571508601891-ca5e7a713859?w=1200&h=630&fit=crop",
    ],
    "general": [
        # Images Luxura en priorité
        "https://customer-assets.emergentagent.com/job_hair-extensions-shop/artifacts/no4frw3t_vaVsE.jpg",
        "https://customer-assets.emergentagent.com/job_hair-extensions-shop/artifacts/oyi6y21r_Aq7eZ.jpg",
        "https://customer-assets.emergentagent.com/job_hair-extensions-shop/artifacts/21xcpk05_OdzWP.jpg",
        # Backups
        "https://images.unsplash.com/photo-1529156069898-49953e39b3ac?w=1200&h=630&fit=crop",
        "https://images.unsplash.com/photo-1600948836101-f9ffda59d250?w=1200&h=630&fit=crop",
        "https://images.unsplash.com/photo-1519699047748-de8e457a634e?w=1200&h=630&fit=crop",
    ]
}

# =====================================================
# ANECDOTES LUXURA - EXPERTISE TERRAIN RÉELLE
# Pour rendre le contenu plus humain et anti-IA
# =====================================================

LUXURA_ANECDOTES = {
    "general": [
        "Chez Luxura, on voit souvent des clientes qui hésitent entre plusieurs méthodes. On prend toujours le temps de toucher les cheveux naturels, d'évaluer l'épaisseur et la texture avant de recommander quoi que ce soit.",
        "Après 5 ans d'importation directe, on a appris à reconnaître la qualité d'un lot de cheveux Remy dès qu'on le reçoit : la cuticule doit être intacte et alignée dans le même sens.",
        "Nos salons partenaires nous le disent souvent : la constance entre les lots, c'est ce qui fait la différence. Une cliente qui revient veut exactement la même texture qu'avant.",
        "Au Québec, le climat fait une vraie différence. L'humidité de l'été et le froid sec de l'hiver ne traitent pas les extensions de la même façon.",
    ],
    "genius": [
        "La Genius Weft Vivian, c'est notre best-seller chez les coiffeuses qui font beaucoup de volume. La trame de 0.78mm est tellement fine qu'on la sent à peine sous les doigts.",
        "Une coiffeuse de Lévis nous a dit : 'Depuis que je pose des Genius Weft, mes clientes reviennent systématiquement. Le confort est incomparable.'",
        "Ce qu'on aime avec la Genius Weft, c'est qu'on peut la couper sans qu'elle s'effiloche. Ça permet un ajustement parfait à chaque tête.",
        "On a testé plusieurs fournisseurs avant de choisir notre gamme Genius. La différence de qualité entre une trame machine standard et une vraie Genius, ça se voit et ça se sent.",
    ],
    "halo": [
        "Le Halo Everly, c'est souvent le premier choix des clientes qui veulent essayer les extensions sans s'engager. On le recommande beaucoup aux débutantes.",
        "Une cliente de Saint-Georges nous a écrit : 'J'ai porté mon Halo à mon mariage et personne n'a vu la différence avec mes vrais cheveux!'",
        "Ce qu'on adore avec le Halo, c'est qu'il n'abîme pas les cheveux. Pour les femmes avec des cheveux fins ou fragilisés, c'est souvent la meilleure option.",
        "Le fil invisible est ajustable, donc une fois qu'on a trouvé son réglage, ça tient parfaitement toute la journée. Même au vent!",
    ],
    "tape": [
        "Les Tape Aurora, on les appelle nos 'extensions de tous les jours'. La pose sandwich est rapide et le résultat est vraiment plat.",
        "Un salon partenaire de Montréal nous a partagé son astuce : il garde toujours 2-3 paquets de rechange pour les retouches. L'adhésif médical tient vraiment bien.",
        "Ce qu'on remarque après 3-4 lavages avec nos Tape-in, c'est que la texture reste soyeuse. C'est là qu'on voit la qualité du cheveu Remy.",
        "Pour le repositionnement, on recommande toujours de venir en salon. L'adhésif se retire facilement avec le bon solvant, mais il faut le tour de main.",
    ],
    "itip": [
        "Les I-Tip Eleanor, c'est pour les clientes qui veulent un résultat ultra-naturel. La pose mèche par mèche prend plus de temps, mais le rendu est incroyable.",
        "Notre kératine italienne fond parfaitement avec la chaleur de la pince. On a eu des retours de coiffeuses qui ont essayé d'autres marques et qui sont revenues chez nous pour la qualité de fusion.",
        "Ce qu'on aime dire aux salons : 'Avec les I-Tip, vous pouvez vraiment personnaliser la densité.' Certaines clientes veulent juste du volume sur les côtés.",
        "En hiver québécois, on conseille toujours de bien hydrater les pointes. Le froid sec peut assécher les extensions comme les cheveux naturels.",
    ],
    "entretien": [
        "Notre conseil numéro un pour l'entretien : produits sans sulfate et sans alcool. On voit la différence de durée de vie entre les clientes qui suivent nos conseils et celles qui utilisent n'importe quoi.",
        "Une erreur courante qu'on voit : brosser les extensions quand elles sont mouillées. Les cheveux Remy sont solides, mais il faut quand même les traiter avec respect.",
        "Pour les blondes, on recommande un shampoing violet de temps en temps. Les extensions claires peuvent jaunir avec le temps, comme les cheveux naturels.",
        "Le séchoir, c'est correct, mais toujours avec un protecteur thermique. Et jamais à chaleur maximale directement sur les points d'attache.",
    ],
    "pro": [
        "Nos salons partenaires apprécient surtout la constance de nos lots. Quand une cliente commande une couleur, elle veut exactement la même teinte 6 mois plus tard.",
        "On offre des prix de gros intéressants, mais ce qui fidélise vraiment les coiffeuses, c'est notre service. Livraison rapide, stock réel, et on répond toujours au téléphone.",
        "Un conseil qu'on donne souvent aux nouveaux salons : commencez avec 3-4 couleurs populaires (brun naturel, blond miel, noir). C'est 80% de la demande.",
        "Notre salle d'exposition à Saint-Georges permet aux coiffeuses de voir et toucher les produits avant de commander. Ça fait une vraie différence.",
    ]
}

# Fonction pour obtenir une anecdote aléatoire
def get_random_anecdote(category: str) -> str:
    """Retourne une anecdote Luxura aléatoire pour la catégorie donnée."""
    anecdotes = LUXURA_ANECDOTES.get(category, LUXURA_ANECDOTES["general"])
    return random.choice(anecdotes)

def get_luxura_recommendation(category: str) -> str:
    """Retourne une recommandation Luxura basée sur la catégorie."""
    recommendations = {
        "genius": "Pour un résultat optimal avec la Genius Weft, on recommande un repositionnement tous les 2-3 mois. C'est ce qui permet d'atteindre les 12 mois et plus de durée de vie.",
        "halo": "Notre Halo Everly est parfait pour les occasions spéciales ou pour tester les extensions. Aucun engagement, résultat instantané.",
        "tape": "Les Tape Aurora peuvent être réutilisées 3-4 fois avec de nouveaux adhésifs. C'est un excellent rapport qualité-prix pour les clientes régulières.",
        "itip": "Pour les I-Tip Eleanor, on conseille de prévoir 100-150 mèches pour un volume naturel, 150-200 pour une transformation plus visible.",
        "general": "Peu importe la méthode choisie, la qualité du cheveu Remy fait toute la différence. C'est ce qui permet une durée de vie de 12 mois et plus avec un entretien approprié."
    }
    return recommendations.get(category, recommendations["general"])

# =====================================================
# SUJETS DE BLOG - STRATÉGIE SEO LOCALE QUÉBEC
# Ciblage: Montréal, Lévis, Beauce, Saint-Georges, Sainte-Marie, Saint-Romuald
# 4 catégories: Genius Weft, Tape-in, I-Tips, Halo
# =====================================================

# Villes ciblées avec leurs angles spécifiques
CITIES_SEO = {
    "montreal": {
        "name": "Montréal",
        "angle": "haut de gamme, tendance, transformation",
        "suffix": "à Montréal"
    },
    "levis": {
        "name": "Lévis",
        "angle": "proximité, service professionnel local, entretien + installation",
        "suffix": "à Lévis"
    },
    "beauce": {
        "name": "Beauce",
        "angle": "zone régionale forte, service de proximité, confiance, expertise, accessibilité",
        "suffix": "en Beauce"
    },
    "sainte_marie": {
        "name": "Sainte-Marie",
        "angle": "proximité, naturel, entretien facile",
        "suffix": "à Sainte-Marie"
    },
    "saint_georges": {
        "name": "Saint-Georges",
        "angle": "transformation, longueur, volume",
        "suffix": "à Saint-Georges"
    },
    "saint_romuald": {
        "name": "Saint-Romuald",
        "angle": "local, pratique, service haut de gamme rive-sud",
        "suffix": "à Saint-Romuald"
    }
}

BLOG_TOPICS_EXTENDED = [
    # =====================================================
    # GENIUS WEFT - Pages piliers et locales
    # Angle: trame ultra-fine, couture sur base perlée, confort supérieur
    # =====================================================
    
    # Page pilier - Genius Weft
    {
        "topic": "Qu'est-ce qu'une Genius Weft : Guide complet extensions trame invisible",
        "category": "genius",
        "keywords": ["genius weft c'est quoi", "trame invisible extensions", "genius weft Québec", "extensions trame ultra-fine"],
        "focus_product": "Genius Vivian",
        "content_type": "pillar",
        "installation_steps": ["consultation + matching couleur/longueur", "création d'une rangée de microbilles", "mesure et coupe de la trame", "couture de la genius weft sur la rangée perlée", "fondu/blending et coupe de finition"]
    },
    {
        "topic": "Installation Genius Weft étape par étape : Pose professionnelle complète",
        "category": "genius",
        "keywords": ["installation genius weft", "pose genius weft", "tutoriel genius weft", "étapes pose extensions trame"],
        "focus_product": "Genius Vivian",
        "content_type": "guide",
        "installation_steps": ["consultation + matching couleur/longueur", "création d'une rangée de microbilles", "mesure et coupe de la trame", "couture de la genius weft sur la rangée perlée", "fondu/blending et coupe de finition"]
    },
    {
        "topic": "Genius Weft vs trame cousue classique : Comparatif détaillé",
        "category": "genius",
        "keywords": ["genius weft vs hand-tied", "genius weft vs machine weft", "comparatif trames extensions", "différence genius weft"],
        "focus_product": "Genius Vivian",
        "content_type": "comparison"
    },
    {
        "topic": "Entretien et repositionnement Genius Weft : Guide soins professionnels",
        "category": "genius",
        "keywords": ["entretien genius weft", "repositionnement extensions trame", "soins genius weft", "durée vie genius weft"],
        "focus_product": "Genius Vivian",
        "content_type": "maintenance"
    },
    
    # Genius Weft - Pages locales
    {
        "topic": "Extensions Genius Weft à Montréal : Trame invisible haut de gamme",
        "category": "genius",
        "keywords": ["genius weft Montréal", "extensions trame Montréal", "pose genius weft Montréal", "salon extensions Montréal"],
        "focus_product": "Genius Vivian",
        "city": "montreal",
        "content_type": "local"
    },
    {
        "topic": "Extensions Genius Weft à Lévis : Pose professionnelle rive-sud",
        "category": "genius",
        "keywords": ["genius weft Lévis", "extensions Lévis", "pose extensions Lévis", "salon beauté Lévis"],
        "focus_product": "Genius Vivian",
        "city": "levis",
        "content_type": "local"
    },
    {
        "topic": "Extensions Genius Weft en Beauce : Service de proximité haut de gamme",
        "category": "genius",
        "keywords": ["genius weft Beauce", "extensions Beauce", "rallonges capillaires Beauce", "salon extensions Beauce"],
        "focus_product": "Genius Vivian",
        "city": "beauce",
        "content_type": "local"
    },
    {
        "topic": "Extensions Genius Weft à Saint-Georges : Volume et transformation",
        "category": "genius",
        "keywords": ["genius weft Saint-Georges", "extensions Saint-Georges", "rallonges Saint-Georges", "salon beauté Saint-Georges"],
        "focus_product": "Genius Vivian",
        "city": "saint_georges",
        "content_type": "local"
    },
    
    # =====================================================
    # TAPE-IN / BANDE ADHÉSIVE - Pages piliers et locales
    # Angle: pose sandwich, adhésif médical, réutilisable 3-4 fois
    # =====================================================
    
    # Page pilier - Tape-in
    {
        "topic": "Comment installer des extensions bande adhésive : Guide complet Tape-in",
        "category": "tape",
        "keywords": ["installer extensions tape-in", "pose bande adhésive", "tutoriel tape-in", "extensions sandwich"],
        "focus_product": "Tape Aurora",
        "content_type": "pillar",
        "installation_steps": ["sectionner proprement les cheveux", "prendre une fine mèche", "poser un adhésif dessous", "poser un second adhésif dessus en sandwich", "presser et aligner", "répéter en gardant tension et espacement réguliers"]
    },
    {
        "topic": "Extensions Tape-in : Durée, entretien et retrait professionnel",
        "category": "tape",
        "keywords": ["durée tape-in", "entretien tape-in", "retrait extensions tape", "combien temps tape-in"],
        "focus_product": "Tape Aurora",
        "content_type": "guide"
    },
    {
        "topic": "Extensions Tape-in pour cheveux fins : Solution idéale volume discret",
        "category": "tape",
        "keywords": ["tape-in cheveux fins", "extensions fines Québec", "volume cheveux fins", "tape-in discret"],
        "focus_product": "Tape Aurora",
        "content_type": "guide"
    },
    {
        "topic": "Erreurs à éviter avec les extensions Tape-in : Conseils professionnels",
        "category": "tape",
        "keywords": ["erreurs tape-in", "conseils tape-in", "problèmes extensions tape", "éviter erreurs extensions"],
        "focus_product": "Tape Aurora",
        "content_type": "guide"
    },
    
    # Tape-in - Pages locales
    {
        "topic": "Extensions bande adhésive à Montréal : Pose professionnelle Tape-in",
        "category": "tape",
        "keywords": ["tape-in Montréal", "bande adhésive Montréal", "extensions tape Montréal", "salon tape-in Montréal"],
        "focus_product": "Tape Aurora",
        "city": "montreal",
        "content_type": "local"
    },
    {
        "topic": "Extensions bande adhésive à Lévis : Service rapide et professionnel",
        "category": "tape",
        "keywords": ["tape-in Lévis", "extensions Lévis", "bande adhésive Lévis", "pose extensions Lévis"],
        "focus_product": "Tape Aurora",
        "city": "levis",
        "content_type": "local"
    },
    {
        "topic": "Extensions bande adhésive à Saint-Romuald : Haut de gamme rive-sud",
        "category": "tape",
        "keywords": ["tape-in Saint-Romuald", "extensions Saint-Romuald", "bande adhésive rive-sud", "salon Saint-Romuald"],
        "focus_product": "Tape Aurora",
        "city": "saint_romuald",
        "content_type": "local"
    },
    {
        "topic": "Extensions bande adhésive à Sainte-Marie : Service de proximité",
        "category": "tape",
        "keywords": ["tape-in Sainte-Marie", "extensions Sainte-Marie", "bande adhésive Sainte-Marie", "salon Sainte-Marie"],
        "focus_product": "Tape Aurora",
        "city": "sainte_marie",
        "content_type": "local"
    },
    
    # =====================================================
    # I-TIPS - Pages piliers et locales
    # Angle: mèche par mèche, anneaux/microbeads, rendu ultra-discret
    # =====================================================
    
    # Page pilier - I-Tips
    {
        "topic": "Guide complet I-Tips : Extensions kératine mèche par mèche",
        "category": "itip",
        "keywords": ["guide i-tip", "extensions kératine", "mèche par mèche", "i-tip c'est quoi"],
        "focus_product": "I-Tip Eleanor",
        "content_type": "pillar",
        "installation_steps": ["consultation + partition de la tête", "prélever une petite mèche de cheveux naturels", "enfiler un anneau/microbead", "insérer la mèche I-Tip", "rapprocher de la racine", "serrer l'anneau", "répéter rangée par rangée"]
    },
    {
        "topic": "Pose I-Tip étape par étape : Installation professionnelle kératine",
        "category": "itip",
        "keywords": ["pose i-tip", "installation i-tip", "tutoriel i-tip", "étapes i-tip kératine"],
        "focus_product": "I-Tip Eleanor",
        "content_type": "guide",
        "installation_steps": ["consultation + partition de la tête", "prélever une petite mèche de cheveux naturels", "enfiler un anneau/microbead", "insérer la mèche I-Tip", "rapprocher de la racine", "serrer l'anneau", "répéter rangée par rangée"]
    },
    {
        "topic": "I-Tips vs Tape vs Weft : Comparatif complet méthodes extensions",
        "category": "itip",
        "keywords": ["i-tip vs tape", "i-tip vs weft", "comparatif extensions", "quelle méthode choisir"],
        "focus_product": "I-Tip Eleanor",
        "content_type": "comparison"
    },
    {
        "topic": "Entretien I-Tip et remontée : Quand et comment repositionner",
        "category": "itip",
        "keywords": ["entretien i-tip", "remontée extensions", "repositionner i-tip", "soins i-tip kératine"],
        "focus_product": "I-Tip Eleanor",
        "content_type": "maintenance"
    },
    
    # I-Tips - Pages locales
    {
        "topic": "Extensions I-Tip à Montréal : Pose kératine ultra-naturelle",
        "category": "itip",
        "keywords": ["i-tip Montréal", "extensions kératine Montréal", "mèche par mèche Montréal", "salon i-tip Montréal"],
        "focus_product": "I-Tip Eleanor",
        "city": "montreal",
        "content_type": "local"
    },
    {
        "topic": "Extensions I-Tip à Lévis : Service personnalisé kératine",
        "category": "itip",
        "keywords": ["i-tip Lévis", "extensions Lévis", "kératine Lévis", "pose i-tip Lévis"],
        "focus_product": "I-Tip Eleanor",
        "city": "levis",
        "content_type": "local"
    },
    {
        "topic": "Extensions I-Tip en Beauce : Qualité professionnelle locale",
        "category": "itip",
        "keywords": ["i-tip Beauce", "extensions Beauce", "kératine Beauce", "salon extensions Beauce"],
        "focus_product": "I-Tip Eleanor",
        "city": "beauce",
        "content_type": "local"
    },
    {
        "topic": "Extensions I-Tip à Sainte-Marie : Résultat naturel garanti",
        "category": "itip",
        "keywords": ["i-tip Sainte-Marie", "extensions Sainte-Marie", "kératine Sainte-Marie", "salon Sainte-Marie"],
        "focus_product": "I-Tip Eleanor",
        "city": "sainte_marie",
        "content_type": "local"
    },
    
    # =====================================================
    # HALO SUR FIL INVISIBLE - Pages piliers et locales
    # Angle: sans attache directe, rapide, cheveux fins/sensibles
    # =====================================================
    
    # Page pilier - Halo
    {
        "topic": "Comment poser un Halo sur fil invisible : Guide complet débutant",
        "category": "halo",
        "keywords": ["poser halo extensions", "fil invisible extensions", "tutoriel halo", "halo c'est quoi"],
        "focus_product": "Halo Everly",
        "content_type": "pillar",
        "installation_steps": ["brosser les cheveux", "poser le halo sur la tête via le fil invisible", "sortir les cheveux naturels par-dessus avec un peigne", "fondre/blender", "ajuster le fil si besoin"]
    },
    {
        "topic": "Halo vs Clip-in : Pourquoi le fil invisible est supérieur",
        "category": "halo",
        "keywords": ["halo vs clip-in", "comparatif halo clip", "fil invisible vs clips", "avantages halo"],
        "focus_product": "Halo Everly",
        "content_type": "comparison"
    },
    {
        "topic": "Extensions Halo pour cheveux fins : La solution idéale sans dommage",
        "category": "halo",
        "keywords": ["halo cheveux fins", "extensions légères", "cheveux fins solution", "halo sans dommage"],
        "focus_product": "Halo Everly",
        "content_type": "guide"
    },
    {
        "topic": "Entretien du Halo invisible : Conseils durabilité et soins",
        "category": "halo",
        "keywords": ["entretien halo", "soins halo extensions", "durée vie halo", "nettoyer halo"],
        "focus_product": "Halo Everly",
        "content_type": "maintenance"
    },
    {
        "topic": "Erreurs de blending Halo à éviter : Conseils look naturel",
        "category": "halo",
        "keywords": ["erreurs halo", "blending halo", "halo naturel", "cacher fil invisible"],
        "focus_product": "Halo Everly",
        "content_type": "guide"
    },
    
    # Halo - Pages locales
    {
        "topic": "Extensions Halo sur fil invisible à Montréal : Tendance et transformation",
        "category": "halo",
        "keywords": ["halo Montréal", "fil invisible Montréal", "extensions halo Montréal", "salon halo Montréal"],
        "focus_product": "Halo Everly",
        "city": "montreal",
        "content_type": "local"
    },
    {
        "topic": "Extensions Halo sur fil invisible à Saint-Georges : Volume instantané",
        "category": "halo",
        "keywords": ["halo Saint-Georges", "fil invisible Saint-Georges", "extensions Saint-Georges", "volume Saint-Georges"],
        "focus_product": "Halo Everly",
        "city": "saint_georges",
        "content_type": "local"
    },
    {
        "topic": "Extensions Halo sur fil invisible en Beauce : Solution rapide locale",
        "category": "halo",
        "keywords": ["halo Beauce", "fil invisible Beauce", "extensions Beauce", "salon Beauce"],
        "focus_product": "Halo Everly",
        "city": "beauce",
        "content_type": "local"
    },
    {
        "topic": "Extensions Halo sur fil invisible à Sainte-Marie : Naturel et facile",
        "category": "halo",
        "keywords": ["halo Sainte-Marie", "fil invisible Sainte-Marie", "extensions Sainte-Marie", "salon Sainte-Marie"],
        "focus_product": "Halo Everly",
        "city": "sainte_marie",
        "content_type": "local"
    },
    
    # =====================================================
    # PAGES RÉGIONALES GÉNÉRALES
    # =====================================================
    {
        "topic": "Extensions capillaires en Beauce : Guide complet toutes méthodes",
        "category": "general",
        "keywords": ["extensions Beauce", "rallonges capillaires Beauce", "salon extensions Beauce", "cheveux Beauce"],
        "focus_product": None,
        "city": "beauce",
        "content_type": "regional"
    },
    {
        "topic": "Extensions cheveux à Saint-Romuald : Service haut de gamme rive-sud",
        "category": "general",
        "keywords": ["extensions Saint-Romuald", "rallonges Saint-Romuald", "salon Saint-Romuald", "cheveux rive-sud"],
        "focus_product": None,
        "city": "saint_romuald",
        "content_type": "regional"
    },
    {
        "topic": "Extensions cheveux à Lévis : Toutes les méthodes disponibles",
        "category": "general",
        "keywords": ["extensions Lévis", "rallonges Lévis", "salon extensions Lévis", "cheveux Lévis"],
        "focus_product": None,
        "city": "levis",
        "content_type": "regional"
    },
]

# Historique des images utilisées pour éviter les répétitions
_used_images = set()

def get_blog_image_by_category(category: str) -> str:
    """
    Retourne une image libre de droits selon la catégorie.
    Évite de répéter les mêmes images en gardant un historique.
    """
    global _used_images
    
    images = UNSPLASH_IMAGES.get(category, UNSPLASH_IMAGES["general"])
    
    # Filtrer les images déjà utilisées
    available = [img for img in images if img not in _used_images]
    
    # Si toutes utilisées, réinitialiser l'historique
    if not available:
        _used_images.clear()
        available = images
    
    # Choisir une image au hasard
    selected = random.choice(available)
    _used_images.add(selected)
    
    return selected

# =====================================================
# WIX VELO INTEGRATION (Contourne le bug heroImage)
# =====================================================

async def publish_blog_via_velo(
    title: str,
    excerpt: str,
    content: str,
    image_url: str,
    member_id: str = None
) -> Optional[Dict]:
    """
    Publie un blog via Wix Velo HTTP Function (plus fiable que REST API).
    Endpoint: https://www.luxuradistribution.com/_functions/createBlog
    """
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            payload = {
                "title": title,
                "excerpt": excerpt,
                "content": content,
                "imageUrl": image_url,
                "memberId": member_id
            }
            
            logger.info(f"📤 Publishing via Velo: {title[:50]}...")
            
            response = await client.post(
                "https://www.luxuradistribution.com/_functions/createBlog",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    logger.info(f"✅ Blog published via Velo! Draft ID: {result.get('draftId')}")
                    return result
                else:
                    logger.error(f"❌ Velo error: {result.get('error')}")
                    return None
            else:
                logger.error(f"❌ Velo HTTP error: {response.status_code} - {response.text}")
                return None
                
    except Exception as e:
        logger.error(f"❌ Error calling Velo: {e}")
        return None


# =====================================================
# WIX BLOG INTEGRATION (REST API - Fallback)
# =====================================================

async def get_wix_member_id(api_key: str, site_id: str) -> Optional[str]:
    """Récupère le member ID du propriétaire du site pour la publication"""
    try:
        async with httpx.AsyncClient() as client:
            # Try to get the current identity (site owner)
            response = await client.post(
                "https://www.wixapis.com/members/v1/members/query",
                headers={
                    "Authorization": api_key,
                    "wix-site-id": site_id,
                    "Content-Type": "application/json"
                },
                json={
                    "query": {
                        "paging": {"limit": 1}
                    }
                },
                timeout=30
            )
            logger.info(f"Wix members query response: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                members = data.get("members", [])
                if members:
                    member_id = members[0].get("id")
                    logger.info(f"Found Wix member ID: {member_id}")
                    return member_id
            
            # Alternative: Try to get site properties to find owner
            response2 = await client.get(
                "https://www.wixapis.com/site-properties/v4/properties",
                headers={
                    "Authorization": api_key,
                    "wix-site-id": site_id,
                    "Content-Type": "application/json"
                },
                timeout=30
            )
            logger.info(f"Wix site properties response: {response2.status_code}")
            if response2.status_code == 200:
                data = response2.json()
                logger.info(f"Site properties: {data}")
    except Exception as e:
        logger.error(f"Error getting Wix member ID: {e}")
    return None

# =====================================================
# WIX MEDIA MANAGER - Import d'images
# =====================================================

async def import_image_with_retry(
    api_key: str,
    site_id: str,
    category: str,
    max_retries: int = 3,
    add_logo: bool = True
) -> Optional[Dict]:
    """
    Importe une image avec retry automatique.
    Si une image échoue, essaie avec une autre image de la même catégorie.
    
    Args:
        add_logo: Si True, ajoute le logo Luxura sur l'image (coin bas-droit, 15%)
    """
    tried_images = set()
    
    for attempt in range(max_retries):
        # Sélectionner une image pas encore essayée
        image_url = get_blog_image_by_category(category)
        
        # Éviter les doublons
        while image_url in tried_images and len(tried_images) < len(UNSPLASH_IMAGES.get(category, UNSPLASH_IMAGES["general"])):
            image_url = get_blog_image_by_category(category)
        
        tried_images.add(image_url)
        
        logger.info(f"📷 Import image attempt {attempt + 1}/{max_retries}: {image_url[:50]}...")
        
        # Si logo overlay disponible et demandé, utiliser la nouvelle méthode
        if add_logo and LOGO_OVERLAY_AVAILABLE:
            logger.info(f"🖼️ Adding Luxura logo to image (bottom-right, 15%)...")
            result = await import_image_with_logo(
                api_key=api_key,
                site_id=site_id,
                image_url=image_url,
                file_name=f"luxura-cover-{uuid.uuid4().hex[:8]}.jpg"
            )
        else:
            # Fallback: import direct sans logo
            result = await import_image_and_get_wix_uri(
                api_key=api_key,
                site_id=site_id,
                image_url=image_url,
                file_name=f"luxura-cover-{uuid.uuid4().hex[:8]}.jpg"
            )
        
        if result and result.get("file_id"):
            logger.info(f"✅ Image imported successfully on attempt {attempt + 1}")
            result["source_url"] = image_url  # Garder l'URL source
            return result
        
        logger.warning(f"⚠️ Image import failed, trying another image...")
    
    logger.error(f"❌ All {max_retries} image import attempts failed")
    return None


async def import_image_with_logo(
    api_key: str,
    site_id: str,
    image_url: str,
    file_name: str = None
) -> Optional[Dict]:
    """
    Télécharge une image, ajoute le logo Luxura, et l'upload vers Wix Media.
    Position: coin bas-droit, taille: 15%
    
    MÉTHODE: Sauvegarde temporaire + import via URL data
    Note: L'upload direct de bytes nécessite Velo backend ou API v2 avec permissions spéciales.
    En attendant, on utilise l'import standard et on note que le logo devra être ajouté manuellement
    ou via un processus Wix Velo.
    """
    import io
    import tempfile
    import os as local_os
    
    if not file_name:
        file_name = f"luxura-cover-{uuid.uuid4().hex[:8]}.jpg"
    
    try:
        # Créer l'image avec logo
        image_bytes = await process_image_with_logo(
            image_url,
            position="bottom-right",
            size_percent=0.15,
            padding=20
        )
        
        if not image_bytes:
            logger.warning("Logo overlay failed, falling back to direct import")
            return await import_image_and_get_wix_uri(api_key, site_id, image_url, file_name)
        
        logger.info(f"✅ Logo added to image ({len(image_bytes)} bytes)")
        
        # OPTION 1: Essayer l'upload direct via generate-file-upload-url (API v2)
        async with httpx.AsyncClient(timeout=120.0) as client:
            # Étape 1: Générer l'URL d'upload
            generate_payload = {
                "mimeType": "image/jpeg",
                "fileName": file_name,
                "filePath": f"/blog-covers/{file_name}"
            }
            
            response = await client.post(
                "https://www.wixapis.com/site-media/v1/files/generate-file-upload-url",
                headers={
                    "Authorization": api_key,
                    "wix-site-id": site_id,
                    "Content-Type": "application/json"
                },
                json=generate_payload
            )
            
            if response.status_code == 200:
                upload_data = response.json()
                upload_url = upload_data.get("uploadUrl")
                
                if upload_url:
                    # Upload direct des bytes
                    logger.info(f"Uploading image with logo to Wix...")
                    
                    upload_response = await client.put(
                        upload_url,
                        content=image_bytes,
                        headers={"Content-Type": "image/jpeg"}
                    )
                    
                    if upload_response.status_code in (200, 201):
                        # Extraire file_id
                        file_info = upload_data.get("file", {})
                        file_id = file_info.get("id")
                        
                        if file_id:
                            # Attendre que le fichier soit prêt
                            file_desc = await wait_until_wix_file_ready(api_key, site_id, file_id, timeout_sec=90)
                            
                            if file_desc:
                                # Extraire dimensions
                                media = file_desc.get("media", {}) or {}
                                image_wrapper = media.get("image", {}) if isinstance(media, dict) else {}
                                image_data = image_wrapper.get("image", {}) if isinstance(image_wrapper, dict) else {}
                                width = image_data.get("width") or 1200
                                height = image_data.get("height") or 630
                                display_name = file_desc.get("displayName", file_name)
                                
                                # Construire URLs
                                wix_uri = f"wix:image://v1/{file_id}/{display_name}#originWidth={width}&originHeight={height}"
                                static_url = f"https://static.wixstatic.com/media/{file_id}"
                                
                                logger.info(f"✅ Image with logo uploaded - URL: {static_url}")
                                
                                return {
                                    "wix_uri": wix_uri,
                                    "static_url": static_url,
                                    "file_id": file_id,
                                    "width": width,
                                    "height": height,
                                    "display_name": display_name,
                                    "has_logo": True
                                }
        
        # OPTION 2: Si upload direct échoue, utiliser catbox.moe comme hébergeur temporaire (gratuit, pas de clé)
        logger.info("Direct upload not available, trying temporary image hosting...")
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                # Créer un form-data avec les bytes de l'image
                import io
                
                # catbox.moe - hébergeur d'images gratuit sans clé API
                files = {
                    'reqtype': (None, 'fileupload'),
                    'fileToUpload': (file_name, io.BytesIO(image_bytes), 'image/jpeg')
                }
                
                catbox_response = await client.post(
                    "https://catbox.moe/user/api.php",
                    files=files
                )
                
                if catbox_response.status_code == 200:
                    temp_url = catbox_response.text.strip()
                    if temp_url.startswith('https://'):
                        logger.info(f"✅ Image with logo hosted on catbox: {temp_url}")
                        
                        # Maintenant importer cette URL vers Wix
                        result = await import_image_and_get_wix_uri(
                            api_key, site_id, temp_url, file_name
                        )
                        if result:
                            result["has_logo"] = True
                            return result
                else:
                    logger.warning(f"catbox.moe upload failed: {catbox_response.status_code} - {catbox_response.text[:100]}")
                    
        except Exception as catbox_error:
            logger.warning(f"catbox upload failed: {catbox_error}")
        
        # OPTION 3: Fallback final - import sans logo
        logger.warning("All logo upload methods failed, importing original image without logo")
        return await import_image_and_get_wix_uri(api_key, site_id, image_url, file_name)
            
    except Exception as e:
        logger.error(f"Error in import_image_with_logo: {e}")
        import traceback
        traceback.print_exc()
        return await import_image_and_get_wix_uri(api_key, site_id, image_url, file_name)


async def import_image_and_get_wix_uri(
    api_key: str,
    site_id: str,
    image_url: str,
    file_name: str = None
) -> Optional[Dict]:
    """
    Importe l'image et retourne un dict avec plusieurs formats d'URL.
    
    AMÉLIORATION: Retourne aussi l'URL statique (static.wixstatic.com)
    qui fonctionne mieux pour heroImage que le format wix:image://
    
    Returns:
        Dict avec:
        - wix_uri: format wix:image://v1/...
        - static_url: format https://static.wixstatic.com/media/...
        - file_id: ID du fichier Wix
        - width, height: dimensions
    """
    if not file_name:
        file_name = f"blog-cover-{uuid.uuid4().hex[:8]}.jpg"

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            payload = {
                "url": image_url,
                "displayName": file_name,
                "mediaType": "IMAGE",
                "mimeType": "image/jpeg",
                "filePath": f"/blog-covers/{file_name}"
            }

            logger.info(f"Importing image to Wix Media: {image_url[:60]}...")

            response = await client.post(
                "https://www.wixapis.com/site-media/v1/files/import",
                headers={
                    "Authorization": api_key,
                    "wix-site-id": site_id,
                    "Content-Type": "application/json"
                },
                json=payload
            )

            if response.status_code not in (200, 201):
                logger.error(f"Import failed: {response.status_code} - {response.text}")
                return None

            data = response.json()
            file_id = data.get("file", {}).get("id") or data.get("id")

            if not file_id:
                logger.error("No file ID returned from import")
                return None

            # Attendre que le fichier soit READY
            file_desc = await wait_until_wix_file_ready(api_key, site_id, file_id, timeout_sec=90)
            if not file_desc:
                logger.error("File never became READY")
                return None

            # Extraire les informations
            display_name = file_desc.get("displayName", file_name)
            media = file_desc.get("media", {}) or {}
            image_wrapper = media.get("image", {}) if isinstance(media, dict) else {}
            image_data = image_wrapper.get("image", {}) if isinstance(image_wrapper, dict) else {}
            width = image_data.get("width") or 1200
            height = image_data.get("height") or 630

            # Format wix:image:// 
            wix_uri = f"wix:image://v1/{file_id}/{display_name}#originWidth={width}&originHeight={height}"
            
            # Format le plus fiable pour heroImage (forum Wix 2025-2026)
            # Le file_id contient déjà ~mv2.jpg dans son nom
            static_url_mv2 = f"https://static.wixstatic.com/media/{file_id}"
            
            # Format avec dimensions explicites (évite w_NaN / h_NaN)
            static_url_full = f"https://static.wixstatic.com/media/{file_id}/v1/fill/w_{width},h_{height},al_c,q_90/{display_name}"
            
            logger.info(f"✅ Image ready - URL: {static_url_mv2}")
            logger.info(f"   Dimensions: {width}x{height}")
            
            return {
                "wix_uri": wix_uri,
                "static_url": static_url_mv2,      # Utilise celui-ci pour heroImage.id
                "static_url_full": static_url_full,
                "file_id": file_id,
                "width": width,
                "height": height,
                "display_name": display_name
            }

    except Exception as e:
        logger.error(f"Error in import_image_and_get_wix_uri: {e}")
        return None


async def import_image_to_wix_media(
    api_key: str,
    site_id: str,
    image_url: str,
    file_name: str = None
) -> Optional[Dict]:
    """
    Importe une image externe dans le Wix Media Manager.
    IMPORTANT: L'import est asynchrone - il faut attendre operationStatus=READY
    """
    try:
        if not file_name:
            file_name = f"blog-cover-{uuid.uuid4().hex[:8]}.jpg"
        
        async with httpx.AsyncClient() as client:
            payload = {
                "url": image_url,
                "displayName": file_name,
                "mediaType": "IMAGE",
                "mimeType": "image/jpeg",
                "filePath": f"/blog/{file_name}"
            }
            
            logger.info(f"Importing image to Wix Media: {image_url[:50]}...")
            
            response = await client.post(
                "https://www.wixapis.com/site-media/v1/files/import",
                headers={
                    "Authorization": api_key,
                    "wix-site-id": site_id,
                    "Content-Type": "application/json"
                },
                json=payload,
                timeout=60
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                logger.info(f"Wix Media import initiated: {result}")
                return result.get("file", result)
            else:
                logger.error(f"Wix Media import failed: {response.status_code} - {response.text}")
                return None
                
    except Exception as e:
        logger.error(f"Error importing image to Wix Media: {e}")
        return None

async def wait_until_wix_file_ready(
    api_key: str,
    site_id: str,
    file_id: str,
    timeout_sec: int = 90
) -> Optional[Dict]:
    """
    Attend que le fichier Wix soit vraiment prêt (operationStatus=READY).
    Wix traite les imports de façon asynchrone - 200 OK ne veut pas dire prêt!
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            for attempt in range(timeout_sec):
                response = await client.get(
                    f"https://www.wixapis.com/site-media/v1/files/{file_id}",
                    headers={
                        "Authorization": api_key,
                        "wix-site-id": site_id,
                        "Content-Type": "application/json"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    file_desc = data.get("file", data)
                    
                    status = file_desc.get("operationStatus")
                    logger.info(f"File {file_id} status: {status} (attempt {attempt + 1})")
                    
                    if status == "READY":
                        logger.info(f"File {file_id} is READY!")
                        return file_desc
                    
                    if status == "FAILED":
                        logger.error(f"Wix media processing FAILED for file {file_id}")
                        return None
                
                # Attendre avant le prochain check
                await asyncio.sleep(1.5)
            
            logger.error(f"Timeout: File {file_id} was never READY after {timeout_sec}s")
            return None
            
    except Exception as e:
        logger.error(f"Error waiting for Wix file ready: {e}")
        return None

def build_wix_image_uri(file_desc: Dict) -> str:
    """
    Construit la vraie Wix image URI au format:
    wix:image://v1/<mediaId>/<filename>#originWidth=<w>&originHeight=<h>
    
    IMPORTANT: Utilise les vraies dimensions de l'image depuis file_desc.media.image.image
    """
    file_id = file_desc.get("id", "")
    display_name = file_desc.get("displayName", "cover.jpg")
    
    # Récupérer les dimensions depuis media.image.image (structure Wix réelle)
    media = file_desc.get("media", {})
    image_wrapper = media.get("image", {}) if isinstance(media, dict) else {}
    image_data = image_wrapper.get("image", {}) if isinstance(image_wrapper, dict) else {}
    
    # Utiliser les vraies dimensions ou fallback
    width = image_data.get("width") or 1200
    height = image_data.get("height") or 630
    
    wix_uri = f"wix:image://v1/{file_id}/{display_name}#originWidth={width}&originHeight={height}"
    logger.info(f"Built Wix image URI: {wix_uri}")
    return wix_uri


def get_wix_image_object(file_desc: Dict) -> Dict:
    """
    Construit l'objet image complet pour le PATCH du draft.
    Format attendu par media.wixMedia.image
    """
    file_id = file_desc.get("id", "")
    display_name = file_desc.get("displayName", "cover.jpg")
    url = file_desc.get("url", "")
    
    # Récupérer les dimensions depuis media.image.image
    media = file_desc.get("media", {})
    image_wrapper = media.get("image", {}) if isinstance(media, dict) else {}
    image_data = image_wrapper.get("image", {}) if isinstance(image_wrapper, dict) else {}
    
    width = image_data.get("width") or 1200
    height = image_data.get("height") or 630
    
    # Construire la Wix URI
    wix_uri = f"wix:image://v1/{file_id}/{display_name}#originWidth={width}&originHeight={height}"
    
    return {
        "id": wix_uri,
        "url": url,
        "width": width,
        "height": height
    }

async def attach_wix_image_to_draft(
    api_key: str,
    site_id: str,
    draft_id: str,
    file_desc: Dict
) -> bool:
    """
    Attache l'image au draft avec le format minimal recommandé.
    
    Format: media.wixMedia.image.id = "wix:image://v1/..."
    
    Note: Ce format est accepté par l'API (200 OK) et les données sont
    correctement stockées, mais il y a un bug Wix de rendu qui empêche
    parfois l'affichage de la cover dans l'interface.
    """
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Construire la Wix URI
            wix_image_uri = build_wix_image_uri(file_desc)
            logger.info(f"Attaching image to draft {draft_id}")
            logger.info(f"Wix URI: {wix_image_uri}")
            
            # Format minimal recommandé: seulement l'ID
            payload = {
                "draftPost": {
                    "media": {
                        "wixMedia": {
                            "image": {
                                "id": wix_image_uri
                            }
                        }
                    }
                }
            }
            
            response = await client.patch(
                f"https://www.wixapis.com/blog/v3/draft-posts/{draft_id}",
                headers={
                    "Authorization": api_key,
                    "wix-site-id": site_id,
                    "Content-Type": "application/json"
                },
                json=payload
            )
            
            if response.status_code in [200, 204]:
                logger.info(f"Image attached successfully to draft {draft_id}")
                return True
            else:
                logger.error(f"Attach image failed: {response.status_code} - {response.text}")
                return False
                
    except Exception as e:
        logger.error(f"Error attaching image to draft: {e}")
        return False

async def get_wix_blog_categories(api_key: str, site_id: str) -> List[Dict]:
    """Récupère les catégories de blog Wix existantes"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.wixapis.com/blog/v3/categories",
                headers={
                    "Authorization": api_key,
                    "wix-site-id": site_id,
                    "Content-Type": "application/json"
                },
                timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("categories", [])
    except Exception as e:
        logger.error(f"Error getting Wix blog categories: {e}")
    return []

async def create_wix_draft_post(
    api_key: str,
    site_id: str,
    title: str,
    content: str,
    excerpt: str,
    cover_image_data: Optional[Dict] = None,  # Image de couverture pour le feed
    detail_image_data: Optional[Dict] = None,  # Image technique (début du contenu)
    result_image_data: Optional[Dict] = None,  # Image glamour (milieu du contenu)
    video_url: str = None,  # URL de la vidéo générée
    member_id: str = None
) -> Optional[Dict]:
    """
    Crée un brouillon de post sur Wix Blog v3 API.
    
    VERSION V11 avec 3 images + vidéo:
    - cover_image_data: Image de couverture (s'affiche sur le feed/cards)
    - detail_image_data: Image technique close-up (insérée au début du contenu)
    - result_image_data: Image glamour (insérée au milieu du contenu)
    - video_url: URL de la vidéo MP4 (insérée avant la signature)
    - displayed: True pour forcer l'affichage de la cover
    """
    try:
        async with httpx.AsyncClient(timeout=80) as client:
            # URLs statiques pour les 3 images dans le contenu
            cover_static_url = cover_image_data.get("static_url") if cover_image_data else None
            detail_static_url = detail_image_data.get("static_url") if detail_image_data else None
            result_static_url = result_image_data.get("static_url") if result_image_data else None
            
            # Convertir le HTML en Ricos avec les 3 images + vidéo
            rich_content = html_to_ricos(
                content, 
                None,  # hero_image_uri deprecated
                cover_static_url,   # Image 1: Cover au début (installation)
                detail_static_url,  # Image 2: Detail à 1/3 (close-up technique)
                result_static_url,  # Image 3: Result à 2/3 (glamour)
                video_url           # Vidéo avant la signature
            )
            
            logger.info(f"Creating Wix draft post: {title}")
            logger.info(f"  - Image 1 (cover/installation): {cover_static_url[:50] if cover_static_url else 'None'}...")
            logger.info(f"  - Image 2 (detail/close-up): {detail_static_url[:50] if detail_static_url else 'None'}...")
            logger.info(f"  - Image 3 (result/glamour): {result_static_url[:50] if result_static_url else 'None'}...")
            if video_url:
                logger.info(f"  - Video: {video_url[:50]}...")
            
            draft_post = {
                "title": title,
                "excerpt": excerpt,
                "richContent": rich_content,
                "language": "fr"
            }
            
            # Ajouter memberId (obligatoire pour apps tierces)
            if member_id:
                draft_post["memberId"] = member_id
            
            # FORMAT CORRIGÉ POUR IMAGE DE COUVERTURE (affichée sur le feed)
            if cover_image_data and isinstance(cover_image_data, dict):
                file_id = cover_image_data.get("file_id")
                width = cover_image_data.get("width", 1200)
                height = cover_image_data.get("height", 630)
                
                if file_id:
                    logger.info(f"  - Cover image (feed): file_id: {file_id[:50]}...")
                    draft_post["media"] = {
                        "wixMedia": {
                            "image": {
                                "id": file_id,
                                "width": width,
                                "height": height
                            }
                        },
                        "displayed": True,
                        "custom": True
                    }
            
            payload = {"draftPost": draft_post}
            
            response = await client.post(
                "https://www.wixapis.com/blog/v3/draft-posts",
                headers={
                    "Authorization": api_key,
                    "wix-site-id": site_id,
                    "Content-Type": "application/json"
                },
                json=payload
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                draft_id = result.get('draftPost', {}).get('id')
                draft_media = result.get('draftPost', {}).get('media', {})
                displayed = draft_media.get('displayed', False)
                logger.info(f"✅ Wix draft created: {draft_id} | displayed={displayed}")
                return result
            else:
                logger.error(f"Wix draft creation failed: {response.status_code} - {response.text}")
                return None
                
    except Exception as e:
        logger.error(f"Error creating Wix draft: {e}")
        return None

async def publish_wix_draft(api_key: str, site_id: str, draft_id: str) -> bool:
    """Publie un brouillon de post Wix"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://www.wixapis.com/blog/v3/draft-posts/{draft_id}/publish",
                headers={
                    "Authorization": api_key,
                    "wix-site-id": site_id,
                    "Content-Type": "application/json"
                },
                timeout=30
            )
            return response.status_code in [200, 201]
    except Exception as e:
        logger.error(f"Error publishing Wix draft: {e}")
        return False


def generate_seo_meta_description(title: str, category: str = None) -> str:
    """
    Génère une meta description SEO optimisée (150-160 caractères).
    
    Args:
        title: Titre du blog
        category: Catégorie du blog (halo, genius, tape, clips, itip, entretien)
    
    Returns:
        Meta description optimisée pour le SEO
    """
    clean_title = title.lower().replace('💎', '').strip()
    
    # Déterminer la catégorie si non fournie
    if not category:
        if 'halo' in clean_title or 'everly' in clean_title:
            category = 'halo'
        elif 'genius' in clean_title or 'weft' in clean_title:
            category = 'genius'
        elif 'tape' in clean_title or 'bande' in clean_title or 'adhésive' in clean_title:
            category = 'tape'
        elif 'clip' in clean_title or 'sophia' in clean_title:
            category = 'clips'
        elif 'i-tip' in clean_title or 'itip' in clean_title or 'froid' in clean_title or 'eleanor' in clean_title:
            category = 'itip'
        elif 'entretien' in clean_title or 'soin' in clean_title:
            category = 'entretien'
        elif 'cheveux fins' in clean_title or 'fins' in clean_title:
            category = 'fins'
        elif 'académie' in clean_title or 'formation' in clean_title:
            category = 'academie'
    
    # Meta descriptions par catégorie (optimisées SEO)
    meta_descriptions = {
        'halo': 'Extensions Halo Everly - Pose en 30 secondes, sans clips ni colle. Volume naturel pour cheveux fins. Livraison rapide Québec. Luxura Distribution.',
        'genius': 'Genius Weft - Extensions trame ultra-plates et invisibles. Confort optimal, résultat naturel. Professionnels certifiés Québec. Luxura Distribution.',
        'tape': 'Extensions Tape-In Aurora - Adhésives professionnelles, discrètes et légères. Idéal cheveux fins. Livraison Québec. Luxura Distribution.',
        'clips': 'Extensions Clip-In Sophia - Volume instantané amovible. Cheveux 100% Remy, pose en 2 minutes. Sans engagement. Luxura Distribution Québec.',
        'itip': 'Extensions I-Tip Eleanor - Pose à froid sans chaleur. Préserve vos cheveux naturels. Qualité professionnelle Québec. Luxura Distribution.',
        'entretien': 'Guide entretien extensions cheveux - Conseils pros pour prolonger la durée de vie de vos extensions. Luxura Distribution Québec.',
        'fins': 'Extensions pour cheveux fins - Solutions professionnelles pour volume naturel sans abîmer vos cheveux. Luxura Distribution Québec.',
        'academie': 'Académie Luxura - Formation professionnelle extensions cheveux. Devenez certifié Luxura Distribution au Québec.',
    }
    
    # Retourner la meta description correspondante ou une générique
    return meta_descriptions.get(
        category, 
        'Extensions capillaires professionnelles - Halo, Genius, Tape-In, Clip-In. Qualité Remy, livraison rapide Québec. Luxura Distribution.'
    )


async def add_seo_metadata_to_draft(api_key: str, site_id: str, draft_id: str, title: str, category: str = None) -> bool:
    """
    Ajoute les métadonnées SEO à un brouillon de blog Wix.
    
    Args:
        api_key: Clé API Wix
        site_id: ID du site Wix
        draft_id: ID du brouillon
        title: Titre du blog (pour générer la meta description)
        category: Catégorie du blog
    
    Returns:
        True si succès, False sinon
    """
    try:
        meta_description = generate_seo_meta_description(title, category)
        
        # Hashtags SEO par défaut
        seo_hashtags = [
            'luxuradistribution',
            'extensionscheveux', 
            'rallongesquébec',
            'extensionsprofessionnelles',
            'cheveuxremy',
            'beautéquébec'
        ]
        
        async with httpx.AsyncClient(timeout=60) as client:
            # Mettre à jour le draft avec les métadonnées SEO
            response = await client.patch(
                f"https://www.wixapis.com/blog/v3/draft-posts/{draft_id}",
                headers={
                    "Authorization": api_key,
                    "wix-site-id": site_id,
                    "Content-Type": "application/json"
                },
                json={
                    "draftPost": {
                        "excerpt": meta_description,  # L'excerpt sert de description
                        "hashtags": seo_hashtags
                    }
                }
            )
            
            if response.status_code == 200:
                logger.info(f"✅ SEO metadata added to draft {draft_id}")
                logger.info(f"   Meta: {meta_description[:60]}...")
                return True
            else:
                logger.warning(f"⚠️ Could not add SEO metadata: {response.status_code}")
                return False
                
    except Exception as e:
        logger.error(f"Error adding SEO metadata: {e}")
        return False


# URL du logo Luxura Distribution
LUXURA_LOGO_URL = "https://static.wixstatic.com/media/f1b961_e8c5f3e0f0ff4c899c5cf99e2d0c8c4c~mv2.png"
LUXURA_WEBSITE = "https://www.luxuradistribution.com"

def html_to_ricos(html_content: str, hero_image_uri: str = None, image1_url: str = None, image2_url: str = None, image3_url: str = None, video_url: str = None, add_logo: bool = True) -> Dict:
    """
    Convertit le HTML en format Ricos (Wix rich content format) - VERSION V11.
    
    V11: Support de 3 images + 1 vidéo
    - image1_url: Première image (début du contenu) - Installation technique
    - image2_url: Deuxième image (1/3 du contenu) - Close-up technique
    - image3_url: Troisième image (2/3 du contenu) - Résultat glamour
    - video_url: URL de la vidéo (ajoutée avant la dernière image)
    
    Args:
        html_content: Le contenu HTML à convertir
        hero_image_uri: URI Wix de l'image principale (deprecated)
        image1_url: URL de la première image (début)
        image2_url: URL de la deuxième image (1/3)
        image3_url: URL de la troisième image (2/3)
        video_url: URL de la vidéo MP4 (optionnel)
        add_logo: Ajouter le logo Luxura à la fin du contenu
    """
    import re
    import uuid
    
    nodes = []
    
    # =====================================================
    # IMAGE 1: Au début du contenu (technique installation)
    # Chaque image a un ID unique pour éviter les problèmes de galerie
    # =====================================================
    if image1_url:
        nodes.append({
            "type": "IMAGE",
            "id": f"img1_{uuid.uuid4().hex[:8]}",
            "imageData": {
                "image": {
                    "src": {"url": image1_url},
                    "width": 1200,
                    "height": 630
                },
                "altText": "Extensions capillaires Luxura - Installation professionnelle",
                "disableExpand": False,
                "disableDownload": True
            }
        })
    
    # Nettoyer le HTML
    content = html_content.strip()
    
    # =====================================================
    # PARSING SÉQUENTIEL pour conserver l'ordre du contenu
    # =====================================================
    
    # Regex pour trouver tous les éléments avec leur position
    pattern = r'(<h1[^>]*>.*?</h1>|<h2[^>]*>.*?</h2>|<h3[^>]*>.*?</h3>|<p[^>]*>.*?</p>|<ul[^>]*>.*?</ul>|<ol[^>]*>.*?</ol>|<blockquote[^>]*>.*?</blockquote>)'
    
    elements = re.findall(pattern, content, re.DOTALL)
    
    for i, element in enumerate(elements):
        # H1
        if element.startswith('<h1'):
            text = re.sub(r'<[^>]+>', '', element).strip()
            if text:
                nodes.append({
                    "type": "HEADING",
                    "headingData": {"level": 1},
                    "nodes": [{"type": "TEXT", "textData": {"text": text}}]
                })
        
        # H2
        elif element.startswith('<h2'):
            text = re.sub(r'<[^>]+>', '', element).strip()
            if text:
                nodes.append({
                    "type": "HEADING",
                    "headingData": {"level": 2},
                    "nodes": [{"type": "TEXT", "textData": {"text": text}}]
                })
        
        # H3
        elif element.startswith('<h3'):
            text = re.sub(r'<[^>]+>', '', element).strip()
            if text:
                nodes.append({
                    "type": "HEADING", 
                    "headingData": {"level": 3},
                    "nodes": [{"type": "TEXT", "textData": {"text": text}}]
                })
        
        # BLOCKQUOTE - Pour les témoignages
        elif element.startswith('<blockquote'):
            text = re.sub(r'<[^>]+>', '', element).strip()
            if text:
                # Wix utilise le type BLOCKQUOTE pour les citations
                nodes.append({
                    "type": "BLOCKQUOTE",
                    "nodes": [{
                        "type": "PARAGRAPH",
                        "nodes": [{
                            "type": "TEXT", 
                            "textData": {
                                "text": f"« {text} »",
                                "decorations": [{"type": "ITALIC"}]
                            }
                        }]
                    }]
                })
        
        # Paragraphes
        elif element.startswith('<p'):
            text = re.sub(r'<[^>]+>', '', element).strip()
            if text:
                # Vérifier si c'est un texte en gras
                has_strong = '<strong>' in element or '<b>' in element
                
                if has_strong:
                    nodes.append({
                        "type": "PARAGRAPH",
                        "nodes": [{
                            "type": "TEXT", 
                            "textData": {
                                "text": text,
                                "decorations": [{"type": "BOLD"}]
                            }
                        }]
                    })
                else:
                    nodes.append({
                        "type": "PARAGRAPH",
                        "nodes": [{"type": "TEXT", "textData": {"text": text}}]
                    })
        
        # Listes non-ordonnées (ul) - AVEC SUPPORT DES LIENS HYPERTEXTES
        elif element.startswith('<ul'):
            list_items = []
            for li_match in re.finditer(r'<li[^>]*>(.*?)</li>', element, re.DOTALL):
                li_content = li_match.group(1)
                
                # Vérifier s'il y a un lien dans le <li>
                link_match = re.search(r'<a\s+href=["\']([^"\']+)["\'][^>]*>([^<]+)</a>', li_content)
                
                if link_match:
                    # Créer un item de liste avec lien cliquable
                    # IMPORTANT: Wix Ricos exige "BLANK" (pas "_blank") pour target
                    link_url = link_match.group(1)
                    link_text = link_match.group(2).strip()
                    
                    list_items.append({
                        "type": "LIST_ITEM",
                        "nodes": [{
                            "type": "PARAGRAPH", 
                            "nodes": [{
                                "type": "TEXT", 
                                "textData": {
                                    "text": link_text,
                                    "decorations": [{
                                        "type": "LINK",
                                        "linkData": {
                                            "link": {
                                                "url": link_url,
                                                "target": "BLANK"
                                            }
                                        }
                                    }]
                                }
                            }]
                        }]
                    })
                else:
                    # Item de liste sans lien
                    text = re.sub(r'<[^>]+>', '', li_content).strip()
                    if text:
                        list_items.append({
                            "type": "LIST_ITEM",
                            "nodes": [{"type": "PARAGRAPH", "nodes": [{"type": "TEXT", "textData": {"text": text}}]}]
                        })
            
            if list_items:
                nodes.append({
                    "type": "BULLETED_LIST",
                    "nodes": list_items
                })
        
        # Listes ordonnées (ol)
        elif element.startswith('<ol'):
            list_items = []
            for li_match in re.finditer(r'<li[^>]*>(.*?)</li>', element, re.DOTALL):
                text = re.sub(r'<[^>]+>', '', li_match.group(1)).strip()
                if text:
                    list_items.append({
                        "type": "LIST_ITEM",
                        "nodes": [{"type": "PARAGRAPH", "nodes": [{"type": "TEXT", "textData": {"text": text}}]}]
                    })
            if list_items:
                nodes.append({
                    "type": "ORDERED_LIST",
                    "nodes": list_items
                })
    
    # Si aucun node (sauf image), créer un paragraphe avec le contenu brut
    text_nodes = [n for n in nodes if n.get("type") != "IMAGE"]
    if not text_nodes:
        clean_text = re.sub(r'<[^>]+>', '\n', content).strip()
        for para in clean_text.split('\n\n'):
            if para.strip():
                nodes.append({
                    "type": "PARAGRAPH",
                    "nodes": [{"type": "TEXT", "textData": {"text": para.strip()}}]
                })
    
    # =====================================================
    # INSÉRER LES IMAGES 2 ET 3 À DES POSITIONS STRATÉGIQUES
    # =====================================================
    
    # Calculer les points d'insertion
    text_nodes_count = len([n for n in nodes if n.get("type") != "IMAGE"])
    
    # IMAGE 2: À environ 1/3 du contenu (close-up technique)
    if image2_url and text_nodes_count > 3:
        insert_point_2 = max(3, len(nodes) // 3)
        
        image2_node = {
            "type": "IMAGE",
            "id": f"img2_{uuid.uuid4().hex[:8]}",
            "imageData": {
                "image": {
                    "src": {"url": image2_url},
                    "width": 1200,
                    "height": 630
                },
                "altText": "Extensions capillaires - Détail technique close-up",
                "disableExpand": False,
                "disableDownload": True
            }
        }
        
        # Insérer après un H2 si possible
        inserted = False
        for idx in range(insert_point_2, min(insert_point_2 + 5, len(nodes))):
            if idx < len(nodes) and nodes[idx].get("type") == "HEADING":
                nodes.insert(idx + 1, image2_node)
                inserted = True
                break
        
        if not inserted:
            nodes.insert(insert_point_2, image2_node)
    
    # IMAGE 3: À environ 2/3 du contenu (résultat glamour)
    if image3_url and text_nodes_count > 6:
        insert_point_3 = max(6, (len(nodes) * 2) // 3)
        
        image3_node = {
            "type": "IMAGE",
            "id": f"img3_{uuid.uuid4().hex[:8]}",
            "imageData": {
                "image": {
                    "src": {"url": image3_url},
                    "width": 1200,
                    "height": 630
                },
                "altText": "Extensions capillaires - Résultat final glamour",
                "disableExpand": False,
                "disableDownload": True
            }
        }
        
        # Insérer après un H2 si possible
        inserted = False
        for idx in range(insert_point_3, min(insert_point_3 + 5, len(nodes))):
            if idx < len(nodes) and nodes[idx].get("type") == "HEADING":
                nodes.insert(idx + 1, image3_node)
                inserted = True
                break
        
        if not inserted and insert_point_3 < len(nodes):
            nodes.insert(insert_point_3, image3_node)
    
    # =====================================================
    # VIDÉO: DÉSACTIVÉE pour Wix Blog (format Ricos incompatible)
    # La vidéo est générée et sauvegardée pour Instagram/Facebook uniquement
    # =====================================================
    # NOTE: video_url n'est plus utilisée dans le blog Wix
    # Elle reste disponible dans blog_post["video_url"] pour les réseaux sociaux
    
    # Ajouter la signature Luxura à la fin (SANS image logo car il est maintenant dans l'image principale)
    if add_logo:
        # Séparateur
        nodes.append({
            "type": "DIVIDER",
            "dividerData": {
                "lineStyle": "DOUBLE",
                "width": "MEDIUM"
            }
        })
        
        # Note: Le logo Luxura est maintenant intégré directement dans l'image de couverture
        # (coin bas-droit, 15%) pour un rendu plus professionnel
        
        # Signature Luxura avec lien
        # IMPORTANT: Wix Ricos exige "BLANK" (pas "_blank") pour target
        nodes.append({
            "type": "PARAGRAPH",
            "nodes": [{
                "type": "TEXT", 
                "textData": {
                    "text": "Luxura Distribution - Importateur d'extensions capillaires haut de gamme au Québec",
                    "decorations": [
                        {"type": "BOLD"},
                        {
                            "type": "LINK",
                            "linkData": {
                                "link": {
                                    "url": "https://www.luxuradistribution.com",
                                    "target": "BLANK"
                                }
                            }
                        }
                    ]
                }
            }]
        })
        
        # Hashtags - SANS salon car on est un DISTRIBUTEUR
        nodes.append({
            "type": "PARAGRAPH",
            "nodes": [{
                "type": "TEXT", 
                "textData": {
                    "text": "#LuxuraDistribution #ExtensionsCheveux #RallongesQuébec #BeautéMontréal #CheveuxLongs #ExtensionsHautDeGamme"
                }
            }]
        })
    
    return {
        "nodes": nodes,
        "metadata": {
            "version": 1,
            "createdTimestamp": datetime.now(timezone.utc).isoformat(),
            "updatedTimestamp": datetime.now(timezone.utc).isoformat()
        }
    }

# =====================================================
# FACEBOOK PUBLISHING
# =====================================================

def html_to_plain_text(html_content: str) -> str:
    """Convertit le HTML en texte brut pour Facebook"""
    import re
    # Remplacer les balises de titre par des lignes
    text = re.sub(r'<h[1-6][^>]*>(.*?)</h[1-6]>', r'\n\n📌 \1\n', html_content)
    # Remplacer les listes
    text = re.sub(r'<li[^>]*>(.*?)</li>', r'• \1\n', text)
    # Remplacer les paragraphes
    text = re.sub(r'<p[^>]*>(.*?)</p>', r'\1\n\n', text)
    # Supprimer toutes les autres balises
    text = re.sub(r'<[^>]+>', '', text)
    # Nettoyer les espaces multiples
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

async def publish_to_facebook_page(
    fb_access_token: str,
    fb_page_id: str,
    title: str,
    content: str,
    image_url: str = None,
    link: str = None
) -> Optional[Dict]:
    """
    Publie un article sur la page Facebook Luxura Distribution.
    
    Args:
        fb_access_token: Token d'accès de la page Facebook
        fb_page_id: ID de la page Facebook
        title: Titre du post
        content: Contenu HTML (sera converti en texte)
        image_url: URL de l'image (optionnel)
        link: Lien vers l'article complet (optionnel)
    
    Returns:
        Dict avec l'ID du post Facebook si succès, None sinon
    """
    try:
        # Convertir HTML en texte pour Facebook
        plain_text = html_to_plain_text(content)
        
        # Créer le message avec le titre
        message = f"✨ {title}\n\n{plain_text[:1500]}"  # Facebook limite à ~2000 caractères
        
        if link:
            message += f"\n\n🔗 Lire l'article complet: {link}"
        
        message += "\n\n#LuxuraDistribution #ExtensionsCheveux #Québec #Montréal #HairExtensions"
        
        async with httpx.AsyncClient() as client:
            # Si on a une image, on publie un post avec photo
            if image_url:
                response = await client.post(
                    f"https://graph.facebook.com/v19.0/{fb_page_id}/photos",
                    data={
                        "url": image_url,
                        "caption": message,
                        "access_token": fb_access_token
                    },
                    timeout=60
                )
            else:
                # Sinon, on publie un post texte simple
                response = await client.post(
                    f"https://graph.facebook.com/v19.0/{fb_page_id}/feed",
                    data={
                        "message": message,
                        "access_token": fb_access_token
                    },
                    timeout=30
                )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Facebook post published: {result.get('id') or result.get('post_id')}")
                return result
            else:
                logger.error(f"Facebook publish failed: {response.status_code} - {response.text}")
                return None
                
    except Exception as e:
        logger.error(f"Error publishing to Facebook: {e}")
        return None

# =====================================================
# GÉNÉRATION DE BLOG AVEC OPENAI
# =====================================================

async def generate_blog_with_ai(
    topic_data: Dict,
    openai_key: str,
    existing_titles: List[str] = None
) -> Optional[Dict]:
    """Génère un article de blog SEO optimisé avec OpenAI GPT-4 - Version québécoise locale"""
    try:
        import openai
        
        client = openai.AsyncOpenAI(api_key=openai_key)
        
        topic = topic_data["topic"]
        category = topic_data["category"]
        keywords = topic_data["keywords"]
        focus_product = topic_data.get("focus_product")
        content_type = topic_data.get("content_type", "general")
        city = topic_data.get("city")
        installation_steps = topic_data.get("installation_steps", [])
        
        # Obtenir les infos de la ville si c'est un article local
        city_info = CITIES_SEO.get(city, {}) if city else {}
        city_name = city_info.get("name", "")
        city_angle = city_info.get("angle", "")
        city_suffix = city_info.get("suffix", "")
        
        # System message optimisé SEO Québec avec français québécois authentique
        system_message = f"""Tu es un expert SEO francophone spécialisé dans les extensions capillaires au Québec.
Tu écris pour Luxura Distribution, le leader des extensions cheveux haut de gamme au Canada.

IDENTITÉ LUXURA DISTRIBUTION (TRÈS IMPORTANT):
- Luxura Distribution est un IMPORTATEUR et DISTRIBUTEUR de produits d'extensions capillaires haut de gamme
- Luxura n'est PAS un salon de coiffure
- Luxura VEND aux salons professionnels (B2B) ET directement aux consommatrices en ligne (B2C)
- Luxura n'offre PAS de formations ni de services de pose
- NE JAMAIS utiliser le hashtag #SalonProfessionnel - utiliser #LuxuraDistribution

STYLE FRANÇAIS QUÉBÉCOIS:
- Utiliser un français québécois naturel et accessible
- Expressions typiques: "on vous explique", "ben correct", "super pratique", "pas mal populaire"
- Éviter le vouvoiement trop formel, préférer un ton chaleureux
- Termes locaux: "magasinage", "rabais", "pogner", "c'est l'fun"
- Adapter au contexte local québécois

PRODUITS LUXURA (DURÉES DE VIE IMPORTANTES):
- Genius Weft Vivian: Trame ultra-fine 0.78mm, couture sur base perlée, découpable sans effilochage. Durée: 12+ mois.
- Halo Everly: Fil invisible, volume instantané, parfait pour cheveux fins/sensibles. Durée: 12+ mois.
- Tape Aurora: Bande adhésive médicale, pose sandwich, réutilisable 3-4 fois. Durée: 12+ mois.
- I-Tip Eleanor: Kératine italienne, pose mèche par mèche avec anneaux/microbeads. Durée: 12+ mois.

ÉTAPES D'INSTALLATION PAR CATÉGORIE:

GENIUS WEFT:
1. Consultation + matching couleur/longueur
2. Création d'une rangée de microbilles
3. Mesure et coupe de la trame
4. Couture de la genius weft sur la rangée perlée
5. Fondu/blending et coupe de finition

TAPE-IN / BANDE ADHÉSIVE:
1. Sectionner proprement les cheveux
2. Prendre une fine mèche
3. Poser un adhésif dessous
4. Poser un second adhésif dessus en sandwich
5. Presser et aligner
6. Répéter en gardant tension et espacement réguliers

I-TIPS:
1. Consultation + partition de la tête
2. Prélever une petite mèche de cheveux naturels
3. Enfiler un anneau/microbead
4. Insérer la mèche I-Tip
5. Rapprocher de la racine
6. Serrer l'anneau
7. Répéter rangée par rangée

HALO:
1. Brosser les cheveux
2. Poser le halo sur la tête via le fil invisible
3. Sortir les cheveux naturels par-dessus avec un peigne
4. Fondre/blender
5. Ajuster le fil si besoin

VILLES CIBLÉES QUÉBEC:
- Montréal: haut de gamme, tendance, transformation
- Lévis: proximité, service professionnel local
- Beauce: zone régionale forte, confiance, accessibilité
- Sainte-Marie: proximité, naturel, entretien facile
- Saint-Georges: transformation, longueur, volume
- Saint-Romuald: local, pratique, service haut de gamme rive-sud

⚠️ DURÉE DE VIE CRITIQUE:
- Toutes les extensions Luxura durent PLUS DE 12 MOIS avec des soins appropriés
- NE JAMAIS écrire "6 mois" - C'est TOUJOURS "12 mois et plus"
- Les couleurs BLONDES nécessitent plus de soins
- Recommander des produits sans sulfate et sans alcool

LOCALISATION: Québec, Montréal, Lévis, Beauce, Saint-Georges, Sainte-Marie, Saint-Romuald, Canada
LANGUE: Français québécois UNIQUEMENT"""

        product_mention = f"\nMentionne particulièrement le produit: {focus_product}" if focus_product else ""
        
        # Instructions spécifiques selon le type de contenu
        content_instructions = ""
        if content_type == "pillar":
            content_instructions = """
CONTENU PILIER (PAGE PRINCIPALE):
- Article de référence complet sur le sujet
- Expliquer c'est quoi, pour qui, avantages
- Inclure les étapes d'installation détaillées
- Couvrir entretien et durabilité
- Inclure une FAQ avec 3-4 questions fréquentes
"""
        elif content_type == "guide":
            content_instructions = """
GUIDE PRATIQUE:
- Focus sur le "comment faire"
- Étapes claires et numérotées
- Conseils pratiques et erreurs à éviter
- Ton accessible et pédagogique
"""
        elif content_type == "comparison":
            content_instructions = """
ARTICLE COMPARATIF:
- Comparer objectivement les méthodes
- Tableau ou liste des différences
- Pour qui chaque méthode est idéale
- Conclusion avec recommandation
"""
        elif content_type == "maintenance":
            content_instructions = """
ARTICLE ENTRETIEN:
- Focus sur les soins et la durabilité
- Produits recommandés (sans sulfate, sans alcool)
- Fréquence d'entretien
- Signes qu'il faut repositionner
"""
        elif content_type == "local":
            content_instructions = f"""
ARTICLE LOCAL - {city_name}:
- Angle: {city_angle}
- Adapter le contenu au contexte local
- Mentionner la ville et les environs
- Inclure "secteur desservi: {city_name} et environs"
- Ton de proximité et confiance locale
"""
        
        # Instructions pour les étapes d'installation
        installation_instructions = ""
        if installation_steps:
            steps_text = "\n".join([f"{i+1}. {step}" for i, step in enumerate(installation_steps)])
            installation_instructions = f"""
ÉTAPES D'INSTALLATION À INCLURE:
{steps_text}

Intégrer ces étapes dans une section dédiée avec un H2 comme "Comment se fait l'installation ?" ou "Pose étape par étape"
"""
        
        # Obtenir une anecdote et une recommandation Luxura pour rendre le contenu plus humain
        luxura_anecdote = get_random_anecdote(category)
        luxura_recommendation = get_luxura_recommendation(category)
        
        prompt = f"""Écris un article de blog SEO complet sur le sujet suivant:

SUJET: {topic}
CATÉGORIE: {category}
MOTS-CLÉS À INTÉGRER: {', '.join(keywords)}
TYPE DE CONTENU: {content_type}
{product_mention}
{content_instructions}
{installation_instructions}

STRUCTURE IMPORTANTE (ANTI-IA - Obligatoire):
1. Introduction engageante (100-150 mots) - SANS TITRE H1 car Wix l'affiche automatiquement
2. Section "Pour qui c'est fait ?" avec H2 + contenu détaillé
3. Section "Comment installer..." avec H2 + étapes numérotées (<ol>)
4. **OBLIGATOIRE - Témoignage en BLOCKQUOTE** - Utilise cette citation:
   <blockquote>{luxura_anecdote}</blockquote>
5. Section "Avantages" avec H2 + liste à puces (<ul>)
6. Section "Entretien" avec H2 + conseils pratiques
7. **OBLIGATOIRE - Section "Luxura recommande"** avec H3:
   "{luxura_recommendation}"
8. Conclusion avec CTA vers Luxura Distribution
9. OBLIGATOIRE: Section "Découvrez nos collections" avec liens

STYLE ANTI-IA (TRÈS IMPORTANT):
- Varier la longueur des phrases (courtes ET longues)
- Questions rhétoriques: "Tu te demandes si..." "Pourquoi c'est important?"
- Contractions québécoises: "c'est pas mal", "ben correct", "ça l'fait vraiment"
- Ton conversationnel et authentique, comme si tu parlais à une cliente
- Éviter les listes trop parfaites et les transitions génériques
- UTILISER <blockquote> pour le témoignage

LIENS CATÉGORIES À INCLURE (OBLIGATOIRE dans la conclusion):
<p><strong>Découvrez nos collections Luxura :</strong></p>
<ul>
<li><a href="https://www.luxuradistribution.com/genius-weft">Extensions Genius Weft</a></li>
<li><a href="https://www.luxuradistribution.com/halo-extensions">Extensions Halo</a></li>
<li><a href="https://www.luxuradistribution.com/tape-in-extensions">Extensions Tape-in</a></li>
<li><a href="https://www.luxuradistribution.com/i-tip-extensions">Extensions I-Tip</a></li>
<li><a href="https://www.luxuradistribution.com/boutique">Tous nos produits</a></li>
</ul>

CONSIGNES CRITIQUES:
- 1200-1800 mots total
- NE PAS inclure de balise <h1>
- Commencer par <p>introduction</p>
- Intégrer chaque mot-clé 2-3 fois naturellement
- Utiliser: <h2>, <h3>, <p>, <ul>, <ol>, <li>, <strong>, <a>, <blockquote>
- Luxura = distributeur (PAS un salon)
- Ton québécois AUTHENTIQUE
- INCLURE <blockquote> pour le témoignage

FORMAT JSON STRICT:
{{
  "title": "Titre SEO optimisé",
  "excerpt": "Résumé accrocheur de 140 caractères max",
  "content": "Contenu HTML avec <blockquote> pour témoignage",
  "meta_description": "Description meta de 155 caractères max",
  "tags": ["extensions cheveux Québec", "rallonges capillaires", "{category}", "Luxura Distribution"],
  "hashtags": "#LuxuraDistribution #ExtensionsCheveux #RallongesQuébec"
}}"""

        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            temperature=0.75,
            max_tokens=4000
        )
        
        response_text = response.choices[0].message.content.strip()
        
        # Nettoyer les balises markdown
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        try:
            blog_data = json.loads(response_text.strip())
        except json.JSONDecodeError:
            import re
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                blog_data = json.loads(json_match.group())
            else:
                return None
        
        # Ajouter l'image et les métadonnées
        blog_data["image"] = get_blog_image_by_category(category)
        blog_data["category"] = category
        blog_data["keywords"] = keywords
        blog_data["focus_product"] = focus_product
        
        return blog_data
        
    except Exception as e:
        logger.error(f"Error generating blog with OpenAI: {e}")
        return None

# =====================================================
# GÉNÉRATION AUTOMATIQUE 2x PAR JOUR
# =====================================================

async def generate_daily_blogs(
    db,
    openai_key: str,
    wix_api_key: str = None,
    wix_site_id: str = None,
    publish_to_wix: bool = True,
    count: int = 2,
    fb_access_token: str = None,
    fb_page_id: str = None,
    publish_to_facebook: bool = False,
    send_email: bool = True,
    force_category: str = None,
    custom_topic: str = None
) -> List[Dict]:
    """
    Génère automatiquement les blogs quotidiens avec OpenAI.
    
    Args:
        force_category: Forcer une catégorie (halo, itip, tape, genius)
        custom_topic: Sujet personnalisé à utiliser
    """
    results = []
    
    # Récupérer le member ID pour Wix si on veut publier
    wix_member_id = None
    if publish_to_wix and wix_api_key and wix_site_id:
        wix_member_id = await get_wix_member_id(wix_api_key, wix_site_id)
        if not wix_member_id:
            logger.warning("Could not get Wix member ID - will try publishing without it")
    
    # Récupérer les titres existants pour éviter les doublons
    existing_posts = await db.blog_posts.find({}, {"title": 1}).to_list(1000)
    existing_titles = [p.get("title", "").lower() for p in existing_posts]
    
    # Si un sujet personnalisé est fourni, l'utiliser directement
    if custom_topic:
        category = force_category or "halo"
        selected_topics = [{
            "topic": custom_topic,
            "category": category,
            "keywords": [category, "extensions cheveux", "Luxura Distribution"],
            "focus_product": f"Extensions {category.title()} Luxura"
        }]
        count = 1
        logger.info(f"📝 Using custom topic: {custom_topic}")
    
    # Si une catégorie est forcée, filtrer les topics
    elif force_category:
        available_topics = [
            t for t in BLOG_TOPICS_EXTENDED 
            if t["category"].lower() == force_category.lower()
            and t["topic"].lower() not in existing_titles
        ]
        if not available_topics:
            # Prendre tous les topics de cette catégorie si aucun nouveau
            available_topics = [t for t in BLOG_TOPICS_EXTENDED if t["category"].lower() == force_category.lower()]
            random.shuffle(available_topics)
        
        selected_topics = available_topics[:count]
        logger.info(f"📝 Forced category: {force_category} - Found {len(selected_topics)} topics")
    
    else:
        # Sélection normale - sujets non couverts
        available_topics = [
            t for t in BLOG_TOPICS_EXTENDED 
            if t["topic"].lower() not in existing_titles
        ]
        
        # Si tous les sujets sont couverts, réutiliser avec rotation
        if len(available_topics) < count:
            available_topics = BLOG_TOPICS_EXTENDED.copy()
            random.shuffle(available_topics)
        
        # Sélectionner les sujets pour aujourd'hui (diversifier les catégories)
        categories_used = []
        selected_topics = []
        
        for topic in available_topics:
            if len(selected_topics) >= count:
                break
            if topic["category"] not in categories_used or len(categories_used) >= 4:
                selected_topics.append(topic)
                categories_used.append(topic["category"])
    
    # Générer chaque blog
    for topic_data in selected_topics:
        blog_data = await generate_blog_with_ai(topic_data, openai_key, existing_titles)
        
        if not blog_data:
            continue
        
        # Créer l'entrée dans la base locale
        post_id = f"auto-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:4]}"
        
        blog_post = {
            "id": post_id,
            "title": blog_data.get("title", topic_data["topic"]),
            "excerpt": blog_data.get("excerpt", ""),
            "content": blog_data.get("content", ""),
            "meta_description": blog_data.get("meta_description", ""),
            "tags": blog_data.get("tags", topic_data["keywords"]),
            "image": blog_data.get("image"),
            "category": topic_data["category"],
            "author": "Luxura Distribution",
            "created_at": datetime.now(timezone.utc),
            "auto_generated": True,
            "needs_human_review": True,  # NOUVEAU: Flag pour relecture humaine obligatoire
            "human_reviewed": False,      # NOUVEAU: Sera mis à True après relecture
            "published_to_wix": False,
            "published_to_facebook": False
        }
        
        await db.blog_posts.insert_one(blog_post)
        
        # ============================================
        # PUBLIER SUR WIX - DALL-E DÉSACTIVÉ DÉFINITIVEMENT
        # Utiliser UNIQUEMENT Unsplash vérifiées (femmes cheveux longs)
        # ============================================
        if publish_to_wix:
            category = topic_data.get("category", "general")
            blog_title = blog_post['title']
            blog_content = blog_post['content']
            focus_product = topic_data.get("focus_product", "")
            
            logger.info(f"🚀 Publishing to Wix: {blog_title[:50]}...")
            
            if wix_api_key and wix_site_id:
                cover_image_data = None
                content_image_data = None
                
                # ============================================
                # V4: ARCHITECTURE INTELLIGENTE
                # Brief Generator analyse le contenu et décide du style
                # ============================================
                if DALLE_AVAILABLE:
                    logger.info(f"🎨 V4: Smart image generation based on blog content analysis...")
                    
                    # Construire blog_data complet pour le brief generator
                    blog_data_for_images = {
                        "title": blog_title,
                        "content": blog_content,
                        "excerpt": blog_post.get("excerpt", ""),
                        "category": category,
                        "focus_product": focus_product,
                        "tags": blog_post.get("tags", [])
                    }
                    
                    try:
                        cover_image_data, detail_image_data, result_image_data = await generate_and_upload_blog_images(
                            api_key=wix_api_key,
                            site_id=wix_site_id,
                            category=category,
                            blog_title=blog_title,
                            keywords=blog_post.get("tags", []),
                            focus_product=focus_product,
                            blog_content=blog_content,
                            blog_data=blog_data_for_images  # V9: Passe tout le blog
                        )
                    except Exception as dalle_error:
                        logger.warning(f"⚠️ DALL-E V9 generation failed: {dalle_error}")
                        import traceback
                        traceback.print_exc()
                        cover_image_data = None
                        detail_image_data = None
                        result_image_data = None
                
                # FALLBACK: Si DALL-E échoue, utiliser Unsplash
                if not cover_image_data:
                    logger.info(f"📷 Fallback: Using Unsplash images")
                    
                    cover_image_data = await import_image_with_retry(
                        api_key=wix_api_key,
                        site_id=wix_site_id,
                        category=category,
                        max_retries=3
                    )
                
                # Fallback pour detail et result
                if not detail_image_data:
                    detail_image_data = await import_image_with_retry(
                        api_key=wix_api_key,
                        site_id=wix_site_id,
                        category=category,
                        max_retries=2
                    )
                
                if not result_image_data:
                    result_image_data = await import_image_with_retry(
                        api_key=wix_api_key,
                        site_id=wix_site_id,
                        category=category,
                        max_retries=2
                    )
                
                # Mettre à jour l'image principale dans blog_post
                if cover_image_data:
                    blog_post["image"] = cover_image_data.get("static_url", blog_post.get("image"))
                
                # =====================================================
                # GÉNÉRATION VIDÉO avec FAL.AI/Kling (optionnel)
                # =====================================================
                video_url = None
                try:
                    from services.video_brief_generator import generate_video_brief, should_generate_video
                    from services.video_generator import generate_short_video, FAL_ENABLED
                    
                    if FAL_ENABLED and cover_image_data:
                        video_brief = generate_video_brief(blog_data_for_images)
                        if should_generate_video(video_brief):
                            logger.info(f"🎥 Generating video for: {blog_post['title'][:40]}...")
                            video_url = await generate_short_video(
                                video_brief=video_brief,
                                image_url=cover_image_data.get("static_url")
                            )
                            if video_url:
                                blog_post["video_url"] = video_url
                                logger.info(f"✅ Video generated: {video_url[:60]}...")
                except ImportError:
                    logger.info("🎥 Video generation not available (services not configured)")
                except Exception as video_error:
                    logger.warning(f"⚠️ Video generation failed (non-blocking): {video_error}")
                
                # Créer le draft Wix avec les 3 images + vidéo V11
                wix_result = await create_wix_draft_post(
                    api_key=wix_api_key,
                    site_id=wix_site_id,
                    title=blog_post["title"],
                    content=blog_post["content"],
                    excerpt=blog_post["excerpt"],
                    cover_image_data=cover_image_data,      # Feed/Card cover
                    detail_image_data=detail_image_data,    # Technique close-up (début contenu)
                    result_image_data=result_image_data,    # Glamour (milieu contenu)
                    video_url=video_url,                    # Vidéo (avant signature)
                    member_id=wix_member_id
                )
                
                if wix_result:
                    draft_id = wix_result.get("draftPost", {}).get("id")
                    if draft_id:
                        # NOUVEAU: Ajouter les métadonnées SEO avant publication
                        await add_seo_metadata_to_draft(
                            wix_api_key, 
                            wix_site_id, 
                            draft_id, 
                            blog_post["title"],
                            force_category  # Passer la catégorie pour une meilleure meta description
                        )
                        
                        published = await publish_wix_draft(wix_api_key, wix_site_id, draft_id)
                        if published:
                            logger.info(f"✅ Blog published successfully with 3 unique images + SEO metadata!")
                            await db.blog_posts.update_one(
                                {"id": post_id},
                                {"$set": {"published_to_wix": True, "wix_post_id": draft_id}}
                            )
                            blog_post["published_to_wix"] = True
                            
                            # V9: Ajouter les URLs des 3 images pour l'email
                            if cover_image_data:
                                blog_post["wix_image_url"] = cover_image_data.get("static_url", "")
                            if detail_image_data:
                                blog_post["wix_detail_image_url"] = detail_image_data.get("static_url", "")
                            if result_image_data:
                                blog_post["wix_result_image_url"] = result_image_data.get("static_url", "")
                else:
                    logger.error(f"❌ Failed to create Wix draft")
        
        # Publier sur Facebook si configuré
        if publish_to_facebook and fb_access_token and fb_page_id:
            fb_result = await publish_to_facebook_page(
                fb_access_token=fb_access_token,
                fb_page_id=fb_page_id,
                title=blog_post["title"],
                content=blog_post["content"],
                image_url=blog_post["image"],
                link=None  # Ajouter le lien vers l'article Wix si disponible
            )
            
            if fb_result:
                fb_post_id = fb_result.get("id") or fb_result.get("post_id")
                await db.blog_posts.update_one(
                    {"id": post_id},
                    {"$set": {"published_to_facebook": True, "facebook_post_id": fb_post_id}}
                )
                blog_post["published_to_facebook"] = True
        
        # Nettoyer pour la réponse
        blog_post.pop("_id", None)
        if isinstance(blog_post.get("created_at"), datetime):
            blog_post["created_at"] = blog_post["created_at"].isoformat()
        
        results.append(blog_post)
        existing_titles.append(blog_post["title"].lower())
    
    # Envoyer email avec les images après génération
    if results and send_email:
        await send_blog_images_email(results)
    
    return results
