"""
Système d'approbation par email pour les posts Facebook
========================================================
Envoie un email HTML avec preview du post et boutons Approuver/Rejeter
"""

import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from typing import Optional, Dict, List
import hashlib
import json

logger = logging.getLogger(__name__)

# Configuration email
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
EMAIL_USER = os.getenv("EMAIL_USERNAME") or os.getenv("LUXURA_EMAIL")
EMAIL_PASS = os.getenv("EMAIL_PASSWORD") or os.getenv("LUXURA_APP_PASSWORD")
APPROVAL_EMAIL = os.getenv("APPROVAL_EMAIL", "info@luxuradistribution.com")
API_URL = os.getenv("API_URL", "https://luxura-inventory-api.onrender.com")

# Traduction des jours de la semaine
JOURS_FR = {
    "monday": "lundi",
    "tuesday": "mardi", 
    "wednesday": "mercredi",
    "thursday": "jeudi",
    "friday": "vendredi",
    "saturday": "samedi",
    "sunday": "dimanche",
    "Monday": "Lundi",
    "Tuesday": "Mardi",
    "Wednesday": "Mercredi",
    "Thursday": "Jeudi",
    "Friday": "Vendredi",
    "Saturday": "Samedi",
    "Sunday": "Dimanche"
}

# Traduction des mois
MOIS_FR = {
    "January": "janvier",
    "February": "février",
    "March": "mars",
    "April": "avril",
    "May": "mai",
    "June": "juin",
    "July": "juillet",
    "August": "août",
    "September": "septembre",
    "October": "octobre",
    "November": "novembre",
    "December": "décembre"
}


def traduire_date_fr(text: str) -> str:
    """Traduit les jours et mois anglais en français"""
    result = text
    for en, fr in JOURS_FR.items():
        result = result.replace(en, fr)
    for en, fr in MOIS_FR.items():
        result = result.replace(en, fr)
    return result


def get_date_fr() -> str:
    """Retourne la date actuelle en français"""
    now = datetime.now()
    jour = JOURS_FR.get(now.strftime("%A"), now.strftime("%A"))
    mois = MOIS_FR.get(now.strftime("%B"), now.strftime("%B"))
    return f"{jour} {now.day} {mois} {now.year}"


def generate_post_id(post: Dict) -> str:
    """Génère un ID unique pour un post"""
    content = f"{post.get('text', '')}{post.get('created_at', '')}"
    return hashlib.md5(content.encode()).hexdigest()[:12]


def create_approval_email_html(post: Dict, post_id: str) -> str:
    """
    Crée le HTML de l'email d'approbation
    """
    text = post.get("text", "")
    image_url = post.get("image_url", "")
    source_title = post.get("source_title", "Actualité extensions capillaires")
    source_url = post.get("source_url", "")
    
    # URLs d'action
    approve_url = f"{API_URL}/api/content/approve/{post_id}"
    reject_url = f"{API_URL}/api/content/reject/{post_id}"
    
    # Preview de l'image
    image_html = ""
    if image_url:
        image_html = f'''
        <div style="margin: 20px 0; text-align: center;">
            <img src="{image_url}" alt="Image du post" style="max-width: 100%; max-height: 400px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
        </div>
        '''
    
    # Formater le texte pour l'affichage HTML
    text_html = text.replace("\n", "<br>")
    
    html = f'''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
        .header h1 {{ margin: 0; font-size: 24px; }}
        .content {{ background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; }}
        .post-preview {{ background: white; border-radius: 10px; padding: 20px; margin: 20px 0; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .post-text {{ font-size: 15px; white-space: pre-wrap; }}
        .source {{ font-size: 12px; color: #666; margin-top: 15px; padding-top: 15px; border-top: 1px solid #eee; }}
        .buttons {{ text-align: center; margin-top: 30px; }}
        .btn {{ display: inline-block; padding: 15px 40px; margin: 10px; text-decoration: none; border-radius: 25px; font-weight: bold; font-size: 16px; }}
        .btn-approve {{ background: #28a745; color: white; }}
        .btn-reject {{ background: #dc3545; color: white; }}
        .footer {{ text-align: center; margin-top: 30px; font-size: 12px; color: #666; }}
        .date {{ font-size: 14px; color: #666; margin-top: 10px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📱 Nouveau Post Facebook</h1>
            <p class="date">À publier le {get_date_fr()}</p>
        </div>
        
        <div class="content">
            <h2>📝 Preview du post:</h2>
            
            <div class="post-preview">
                {image_html}
                <div class="post-text">{text_html}</div>
                
                <div class="source">
                    <strong>Source:</strong> <a href="{source_url}">{source_title}</a>
                </div>
            </div>
            
            <div class="buttons">
                <a href="{approve_url}" class="btn btn-approve">✅ Approuver</a>
                <a href="{reject_url}" class="btn btn-reject">❌ Rejeter</a>
            </div>
            
            <p style="text-align: center; font-size: 12px; color: #666; margin-top: 20px;">
                ID du post: {post_id}
            </p>
        </div>
        
        <div class="footer">
            <p>💜 Luxura Distribution - Système de contenu automatisé</p>
            <p>Ce post a été généré automatiquement à partir d'actualités du secteur.</p>
        </div>
    </div>
</body>
</html>
'''
    return html


async def send_approval_email(post: Dict) -> Dict:
    """
    Envoie un email d'approbation pour un post
    
    Args:
        post: Dict contenant text, image_url, source_title, source_url
    
    Returns:
        Dict avec success, post_id, message
    """
    if not EMAIL_USER or not EMAIL_PASS:
        logger.warning("Email non configuré - approbation ignorée")
        return {"success": False, "message": "Email non configuré"}
    
    post_id = generate_post_id(post)
    
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"📱 [Approbation] Nouveau post Facebook - {get_date_fr()}"
        msg["From"] = EMAIL_USER
        msg["To"] = APPROVAL_EMAIL
        
        # Version texte simple
        text_content = f"""
Nouveau post Facebook à approuver

{post.get('text', '')}

---
Source: {post.get('source_title', '')}
URL: {post.get('source_url', '')}

Pour approuver: {API_URL}/api/content/approve/{post_id}
Pour rejeter: {API_URL}/api/content/reject/{post_id}
"""
        
        # Version HTML
        html_content = create_approval_email_html(post, post_id)
        
        msg.attach(MIMEText(text_content, "plain"))
        msg.attach(MIMEText(html_content, "html"))
        
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
            server.login(EMAIL_USER, EMAIL_PASS)
            server.sendmail(EMAIL_USER, APPROVAL_EMAIL, msg.as_string())
        
        logger.info(f"✅ Email d'approbation envoyé pour post {post_id}")
        return {
            "success": True,
            "post_id": post_id,
            "message": f"Email envoyé à {APPROVAL_EMAIL}"
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur envoi email: {e}")
        return {
            "success": False,
            "post_id": post_id,
            "message": str(e)
        }


async def send_batch_approval_email(posts: List[Dict]) -> Dict:
    """
    Envoie un email récapitulatif avec tous les posts à approuver
    """
    if not posts:
        return {"success": False, "message": "Aucun post à envoyer"}
    
    results = []
    for post in posts:
        result = await send_approval_email(post)
        results.append(result)
    
    success_count = sum(1 for r in results if r["success"])
    
    return {
        "success": success_count > 0,
        "total": len(posts),
        "sent": success_count,
        "failed": len(posts) - success_count,
        "details": results
    }
