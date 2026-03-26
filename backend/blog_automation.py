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
# IMAGES LUXURA - UNIQUEMENT CHEVEUX LONGS, LUXUEUX ET VOLUMINEUX
# Images représentant le résultat des extensions capillaires professionnelles
# =============================================================================
UNSPLASH_IMAGES = {
    "halo": [
        # FEMMES avec cheveux TRÈS LONGS (style Pinterest/produit Luxura)
        # Cheveux jusqu'à la taille ou plus - LONGS, LISSES, SOYEUX
        "https://images.unsplash.com/photo-1580489944761-15a19d654956?w=1200&h=630&fit=crop",  # Femme cheveux très longs
        "https://images.unsplash.com/photo-1524504388940-b1c1722653e1?w=1200&h=630&fit=crop",  # Femme cheveux longs lisses
        "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=1200&h=630&fit=crop",  # Portrait cheveux longs
        "https://images.unsplash.com/photo-1517841905240-472988babdf9?w=1200&h=630&fit=crop",  # Cheveux longs bruns
        "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=1200&h=630&fit=crop",  # Portrait élégant
        "https://images.unsplash.com/photo-1488716820095-cbe80883c496?w=1200&h=630&fit=crop",  # Femme cheveux longs naturels
    ],
    "genius": [
        "https://images.unsplash.com/photo-1524504388940-b1c1722653e1?w=1200&h=630&fit=crop",
        "https://images.unsplash.com/photo-1580489944761-15a19d654956?w=1200&h=630&fit=crop",
        "https://images.unsplash.com/photo-1517841905240-472988babdf9?w=1200&h=630&fit=crop",
        "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=1200&h=630&fit=crop",
        "https://images.unsplash.com/photo-1488716820095-cbe80883c496?w=1200&h=630&fit=crop",
        "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=1200&h=630&fit=crop",
    ],
    "tape": [
        "https://images.unsplash.com/photo-1517841905240-472988babdf9?w=1200&h=630&fit=crop",
        "https://images.unsplash.com/photo-1524504388940-b1c1722653e1?w=1200&h=630&fit=crop",
        "https://images.unsplash.com/photo-1580489944761-15a19d654956?w=1200&h=630&fit=crop",
        "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=1200&h=630&fit=crop",
        "https://images.unsplash.com/photo-1488716820095-cbe80883c496?w=1200&h=630&fit=crop",
        "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=1200&h=630&fit=crop",
    ],
    "itip": [
        "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=1200&h=630&fit=crop",
        "https://images.unsplash.com/photo-1524504388940-b1c1722653e1?w=1200&h=630&fit=crop",
        "https://images.unsplash.com/photo-1517841905240-472988babdf9?w=1200&h=630&fit=crop",
        "https://images.unsplash.com/photo-1580489944761-15a19d654956?w=1200&h=630&fit=crop",
        "https://images.unsplash.com/photo-1488716820095-cbe80883c496?w=1200&h=630&fit=crop",
        "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=1200&h=630&fit=crop",
    ],
    "entretien": [
        "https://images.unsplash.com/photo-1488716820095-cbe80883c496?w=1200&h=630&fit=crop",
        "https://images.unsplash.com/photo-1524504388940-b1c1722653e1?w=1200&h=630&fit=crop",
        "https://images.unsplash.com/photo-1517841905240-472988babdf9?w=1200&h=630&fit=crop",
        "https://images.unsplash.com/photo-1580489944761-15a19d654956?w=1200&h=630&fit=crop",
        "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=1200&h=630&fit=crop",
    ],
    "tendances": [
        "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=1200&h=630&fit=crop",
        "https://images.unsplash.com/photo-1524504388940-b1c1722653e1?w=1200&h=630&fit=crop",
        "https://images.unsplash.com/photo-1517841905240-472988babdf9?w=1200&h=630&fit=crop",
        "https://images.unsplash.com/photo-1580489944761-15a19d654956?w=1200&h=630&fit=crop",
        "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=1200&h=630&fit=crop",
    ],
    "salon": [
        "https://images.unsplash.com/photo-1524504388940-b1c1722653e1?w=1200&h=630&fit=crop",
        "https://images.unsplash.com/photo-1517841905240-472988babdf9?w=1200&h=630&fit=crop",
        "https://images.unsplash.com/photo-1580489944761-15a19d654956?w=1200&h=630&fit=crop",
        "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=1200&h=630&fit=crop",
        "https://images.unsplash.com/photo-1488716820095-cbe80883c496?w=1200&h=630&fit=crop",
    ],
    "formation": [
        "https://images.unsplash.com/photo-1517841905240-472988babdf9?w=1200&h=630&fit=crop",
        "https://images.unsplash.com/photo-1524504388940-b1c1722653e1?w=1200&h=630&fit=crop",
        "https://images.unsplash.com/photo-1580489944761-15a19d654956?w=1200&h=630&fit=crop",
        "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=1200&h=630&fit=crop",
    ],
    "general": [
        "https://images.unsplash.com/photo-1524504388940-b1c1722653e1?w=1200&h=630&fit=crop",
        "https://images.unsplash.com/photo-1580489944761-15a19d654956?w=1200&h=630&fit=crop",
        "https://images.unsplash.com/photo-1517841905240-472988babdf9?w=1200&h=630&fit=crop",
        "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=1200&h=630&fit=crop",
        "https://images.unsplash.com/photo-1488716820095-cbe80883c496?w=1200&h=630&fit=crop",
        "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=1200&h=630&fit=crop",
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
    max_retries: int = 3
) -> Optional[Dict]:
    """
    Importe une image avec retry automatique.
    Si une image échoue, essaie avec une autre image de la même catégorie.
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
    content_image_data: Optional[Dict] = None,  # 2ème image à insérer dans le contenu
    member_id: str = None
) -> Optional[Dict]:
    """
    Crée un brouillon de post sur Wix Blog v3 API.
    
    VERSION 2026 avec DALL-E:
    - cover_image_data: Image de couverture (s'affiche sur le feed/cards)
    - content_image_data: 2ème image différente insérée au milieu de l'article
    - displayed: True pour forcer l'affichage de la cover
    """
    try:
        async with httpx.AsyncClient(timeout=80) as client:
            # URLs statiques pour les images dans le contenu
            cover_static_url = cover_image_data.get("static_url") if cover_image_data else None
            content_static_url = content_image_data.get("static_url") if content_image_data else None
            
            # Convertir le HTML en Ricos avec les 2 images
            rich_content = html_to_ricos(
                content, 
                None,  # hero_image_uri deprecated
                cover_static_url,  # Image en haut du contenu
                content_static_url  # 2ème image au milieu
            )
            
            logger.info(f"Creating Wix draft post: {title}")
            if cover_static_url:
                logger.info(f"  - Cover image: {cover_static_url[:50]}...")
            if content_static_url:
                logger.info(f"  - Content image: {content_static_url[:50]}...")
            
            draft_post = {
                "title": title,
                "excerpt": excerpt,
                "richContent": rich_content,
                "language": "fr"
            }
            
            # Ajouter memberId (obligatoire pour apps tierces)
            if member_id:
                draft_post["memberId"] = member_id
            
            # FORMAT CORRIGÉ POUR IMAGE DE COUVERTURE
            if cover_image_data and isinstance(cover_image_data, dict):
                file_id = cover_image_data.get("file_id")
                width = cover_image_data.get("width", 1200)
                height = cover_image_data.get("height", 630)
                
                if file_id:
                    logger.info(f"Adding cover image with displayed:True - file_id: {file_id[:50]}...")
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

# URL du logo Luxura Distribution
LUXURA_LOGO_URL = "https://static.wixstatic.com/media/f1b961_e8c5f3e0f0ff4c899c5cf99e2d0c8c4c~mv2.png"
LUXURA_WEBSITE = "https://www.luxuradistribution.com"

def html_to_ricos(html_content: str, hero_image_uri: str = None, static_image_url: str = None, content_image_url: str = None, add_logo: bool = True) -> Dict:
    """
    Convertit le HTML en format Ricos (Wix rich content format).
    
    Args:
        html_content: Le contenu HTML à convertir
        hero_image_uri: URI Wix de l'image principale (deprecated)
        static_image_url: URL statique de l'image de couverture (premier élément)
        content_image_url: URL de la 2ème image à insérer au milieu du contenu
        add_logo: Ajouter le logo Luxura à la fin du contenu
    """
    import re
    import uuid
    
    nodes = []
    
    # Insérer l'image de couverture comme premier élément
    image_src = static_image_url or hero_image_uri
    if image_src:
        image_node = {
            "type": "IMAGE",  # MAJUSCULE requis par Wix API
            "imageData": {
                "image": {
                    "src": {
                        "url": image_src
                    },
                    "width": 1200,
                    "height": 630
                },
                "altText": "Extensions capillaires Luxura Distribution"
            }
        }
        nodes.append(image_node)
    
    # Nettoyer le HTML
    content = html_content.strip()
    
    # Parser les balises principales
    # H1
    for match in re.finditer(r'<h1[^>]*>(.*?)</h1>', content, re.DOTALL):
        nodes.append({
            "type": "HEADING",
            "headingData": {"level": 1},
            "nodes": [{"type": "TEXT", "textData": {"text": match.group(1).strip()}}]
        })
    
    # H2
    for match in re.finditer(r'<h2[^>]*>(.*?)</h2>', content, re.DOTALL):
        nodes.append({
            "type": "HEADING",
            "headingData": {"level": 2},
            "nodes": [{"type": "TEXT", "textData": {"text": match.group(1).strip()}}]
        })
    
    # H3
    for match in re.finditer(r'<h3[^>]*>(.*?)</h3>', content, re.DOTALL):
        nodes.append({
            "type": "HEADING", 
            "headingData": {"level": 3},
            "nodes": [{"type": "TEXT", "textData": {"text": match.group(1).strip()}}]
        })
    
    # Paragraphes
    for match in re.finditer(r'<p[^>]*>(.*?)</p>', content, re.DOTALL):
        text = re.sub(r'<[^>]+>', '', match.group(1)).strip()
        if text:
            nodes.append({
                "type": "PARAGRAPH",
                "nodes": [{"type": "TEXT", "textData": {"text": text}}]
            })
    
    # Listes
    for ul_match in re.finditer(r'<ul[^>]*>(.*?)</ul>', content, re.DOTALL):
        list_items = []
        for li_match in re.finditer(r'<li[^>]*>(.*?)</li>', ul_match.group(1), re.DOTALL):
            text = re.sub(r'<[^>]+>', '', li_match.group(1)).strip()
            list_items.append({
                "type": "LIST_ITEM",
                "nodes": [{"type": "PARAGRAPH", "nodes": [{"type": "TEXT", "textData": {"text": text}}]}]
            })
        if list_items:
            nodes.append({
                "type": "BULLETED_LIST",
                "nodes": list_items
            })
    
    # Si aucun node (sauf image), créer un paragraphe avec le contenu brut
    text_nodes = [n for n in nodes if n.get("type") != "IMAGE" and n.get("type") != "image"]
    if not text_nodes:
        clean_text = re.sub(r'<[^>]+>', '\n', content).strip()
        for para in clean_text.split('\n\n'):
            if para.strip():
                nodes.append({
                    "type": "PARAGRAPH",
                    "nodes": [{"type": "TEXT", "textData": {"text": para.strip()}}]
                })
    
    # Insérer la 2ème image (content_image) AU MILIEU du contenu
    if content_image_url and len(nodes) > 3:
        # Trouver le point d'insertion (environ au milieu)
        mid_point = len(nodes) // 2
        
        content_image_node = {
            "type": "IMAGE",  # MAJUSCULE requis par Wix API
            "imageData": {
                "image": {
                    "src": {
                        "url": content_image_url
                    },
                    "width": 1200,
                    "height": 630
                },
                "altText": "Extensions capillaires professionnelles"
            }
        }
        
        # Insérer au milieu
        nodes.insert(mid_point, content_image_node)
    
    # Ajouter la signature Luxura à la fin
    if add_logo:
        # Séparateur
        nodes.append({
            "type": "DIVIDER",
            "dividerData": {
                "lineStyle": "DOUBLE",
                "width": "MEDIUM"
            }
        })
        
        # Signature Luxura
        nodes.append({
            "type": "PARAGRAPH",
            "nodes": [{
                "type": "TEXT", 
                "textData": {
                    "text": "📍 Luxura Distribution - Importateur d'extensions capillaires haut de gamme au Québec",
                    "decorations": [{"type": "BOLD"}]
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
2. Section 1 avec H2 + contenu détaillé (c'est quoi / pour qui)
3. Section 2 avec H2 + étapes d'installation si applicable
4. **OBLIGATOIRE - Section "Ce qu'on voit chez Luxura"** avec H2 incluant cette anecdote réelle:
   "{luxura_anecdote}"
5. Section 3 avec H2 + avantages / entretien
6. **OBLIGATOIRE - Section "Luxura recommande"** avec H3 incluant ce conseil:
   "{luxura_recommendation}"
7. Conclusion avec appel à l'action vers Luxura Distribution
8. OBLIGATOIRE: Section "Découvrez nos collections" avec liens

STYLE ANTI-IA (TRÈS IMPORTANT):
- Varier la longueur des phrases (courtes ET longues)
- Utiliser des questions rhétoriques: "Tu te demandes si..." "Pourquoi c'est important?"
- Inclure des contractions québécoises: "c'est pas mal", "ben oui", "ça l'fait"
- Une anecdote ou observation concrète par section principale
- Ton conversationnel et authentique, comme si tu parlais à une amie
- Éviter les listes trop parfaites et les transitions génériques

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
- 1200-1800 mots total (articles plus longs pour éviter la détection IA)
- NE PAS inclure de balise <h1> dans le contenu
- Commencer directement par un paragraphe <p> d'introduction
- Intégrer chaque mot-clé 2-3 fois naturellement
- Utiliser des balises HTML: <h2>, <h3>, <p>, <ul>, <li>, <strong>, <a>
- Mentionner Luxura Distribution comme expert distributeur (PAS un salon)
- Ton professionnel mais chaleureux, style québécois AUTHENTIQUE
- INCLURE les liens vers les catégories dans la conclusion
- INCLURE les sections "Ce qu'on voit chez Luxura" et "Luxura recommande"

FORMAT JSON STRICT:
{{
  "title": "Titre SEO optimisé (affiché par Wix automatiquement)",
  "excerpt": "Résumé accrocheur de 150 caractères max",
  "content": "Contenu HTML SANS h1 - commencer par <p>introduction</p>... AVEC sections Luxura + liens catégories",
  "meta_description": "Description meta de 155 caractères max",
  "tags": ["extensions cheveux Québec", "rallonges capillaires", "{category}", "Luxura Distribution", "tag-local-si-applicable"],
  "hashtags": "#LuxuraDistribution #ExtensionsCheveux #RallongesQuébec #CheveuxLongs"
}}

RÈGLES TAGS SEO (TRÈS IMPORTANT):
- TOUJOURS inclure "extensions cheveux Québec" ou "rallonges capillaires Québec"
- NE JAMAIS utiliser #SalonProfessionnel (Luxura n'est pas un salon)
- TOUJOURS inclure le nom du produit (Genius Vivian, Halo Everly, Tape Aurora, I-Tip Eleanor)
- Ajouter des mots-clés locaux: Montréal, Québec, Canada
- Ajouter des mots-clés beauté: salon, coiffure, cheveux longs, volume
- Minimum 5 tags, maximum 8 tags par article

HASHTAGS LUXURA (pour réseaux sociaux):
- #LuxuraDistribution
- #ExtensionsCheveux
- #RallongesQuébec
- #ExtensionsProfessionnelles
- #BeautéMontréal
- #CheveuxLongs
- #SalonBeauté
- #GeniusWeft / #HaloExtensions / #TapeIn / #ITipExtensions (selon le sujet)"""

        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=3000
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
    send_email: bool = True  # NOUVEAU: Envoyer email avec images
) -> List[Dict]:
    """Génère automatiquement les blogs quotidiens avec OpenAI"""
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
    
    # Sélectionner des sujets non couverts
    available_topics = [
        t for t in BLOG_TOPICS_EXTENDED 
        if t["topic"].lower() not in existing_titles
    ]
    
    # Si tous les sujets sont couverts, réutiliser avec rotation
    if len(available_topics) < count:
        # Ajouter des variations aux sujets existants
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
        # PUBLIER SUR WIX AVEC IMAGES DALL-E (PROMPTS GROK V3)
        # ============================================
        if publish_to_wix:
            category = topic_data.get("category", "general")
            blog_title = blog_post['title']
            blog_keywords = topic_data.get("keywords", [])
            focus_product = topic_data.get("focus_product")
            
            logger.info(f"🚀 Publishing to Wix: {blog_title[:50]}...")
            
            if wix_api_key and wix_site_id:
                cover_image_data = None
                content_image_data = None
                
                # RÉACTIVÉ: DALL-E avec prompts Grok V3 optimisés
                if DALLE_AVAILABLE:
                    try:
                        logger.info(f"🎨 Generating images with DALL-E (Grok V3 prompts)")
                        logger.info(f"   Title: {blog_title[:50]}...")
                        logger.info(f"   Category: {category}, Product: {focus_product}")
                        
                        # Générer image de couverture avec prompts Grok
                        cover_bytes = await generate_blog_image_with_dalle(
                            category=category,
                            blog_title=blog_title,
                            keywords=blog_keywords,
                            focus_product=focus_product,
                            image_type="cover"
                        )
                        if cover_bytes:
                            cover_image_data = await upload_image_bytes_to_wix(
                                api_key=wix_api_key,
                                site_id=wix_site_id,
                                image_bytes=cover_bytes,
                                file_name=f"cover-dalle-{uuid.uuid4().hex[:8]}.png"
                            )
                            if cover_image_data:
                                logger.info(f"✅ DALL-E cover image uploaded")
                        
                        # Générer 2ème image pour le contenu
                        content_bytes = await generate_blog_image_with_dalle(
                            category=category,
                            blog_title=blog_title,
                            keywords=blog_keywords,
                            focus_product=focus_product,
                            image_type="content"
                        )
                        if content_bytes:
                            content_image_data = await upload_image_bytes_to_wix(
                                api_key=wix_api_key,
                                site_id=wix_site_id,
                                image_bytes=content_bytes,
                                file_name=f"content-dalle-{uuid.uuid4().hex[:8]}.png"
                            )
                            if content_image_data:
                                logger.info(f"✅ DALL-E content image uploaded")
                                
                    except Exception as e:
                        logger.error(f"⚠️ DALL-E generation failed: {e}, falling back to Unsplash")
                
                # Fallback vers Unsplash si DALL-E échoue
                if not cover_image_data:
                    logger.info(f"📷 Using Unsplash fallback for cover image")
                    cover_image_data = await import_image_with_retry(
                        api_key=wix_api_key,
                        site_id=wix_site_id,
                        category=category,
                        max_retries=3
                    )
                
                # Fallback pour l'image de contenu aussi
                if not content_image_data:
                    logger.info(f"📷 Using Unsplash fallback for content image")
                    content_image_data = await import_image_with_retry(
                        api_key=wix_api_key,
                        site_id=wix_site_id,
                        category=category,
                        max_retries=2
                    )
                
                # Mettre à jour l'image principale dans blog_post
                if cover_image_data:
                    blog_post["image"] = cover_image_data.get("static_url", blog_post.get("image"))
                
                # Créer le draft Wix avec les 2 images
                wix_result = await create_wix_draft_post(
                    api_key=wix_api_key,
                    site_id=wix_site_id,
                    title=blog_post["title"],
                    content=blog_post["content"],
                    excerpt=blog_post["excerpt"],
                    cover_image_data=cover_image_data,
                    content_image_data=content_image_data,
                    member_id=wix_member_id
                )
                
                if wix_result:
                    draft_id = wix_result.get("draftPost", {}).get("id")
                    if draft_id:
                        published = await publish_wix_draft(wix_api_key, wix_site_id, draft_id)
                        if published:
                            logger.info(f"✅ Blog published successfully with 2 unique images!")
                            await db.blog_posts.update_one(
                                {"id": post_id},
                                {"$set": {"published_to_wix": True, "wix_post_id": draft_id}}
                            )
                            blog_post["published_to_wix"] = True
                            
                            # Ajouter les URLs des images pour l'email
                            if cover_image_data:
                                blog_post["wix_image_url"] = cover_image_data.get("static_url", "")
                            if content_image_data:
                                blog_post["wix_content_image_url"] = content_image_data.get("static_url", "")
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
