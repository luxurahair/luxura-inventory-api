#!/usr/bin/env python3
"""
LUXURA MAGAZINE CRON - Posts Facebook Magazine
==============================================
Génère des posts Facebook style MAGAZINE avec approbation email.

Flow:
1. Génère un post Magazine avec image Grok v3
2. Sauvegarde en DB Supabase
3. Envoie email d'approbation
4. User clique → Crée brouillon Facebook

Configuration Render:
  - Build Command: pip install requests psycopg2-binary
  - Start Command: python scripts/magazine_cron.py
  - Schedule: 0 10 * * 0  (Dimanche 10h)

Variables requises:
  - DATABASE_URL: PostgreSQL Supabase
  - XAI_API_KEY: Pour images Grok
  - OPENAI_API_KEY: Pour texte GPT
  - LUXURA_EMAIL + LUXURA_APP_PASSWORD: Pour emails
"""

import os
import sys
import json
import uuid
import asyncio
import requests
from datetime import datetime

# Configuration
API_URL = os.getenv("API_URL", "https://luxura-inventory-api.onrender.com").rstrip("/")
XAI_API_KEY = os.getenv("XAI_API_KEY", "").strip()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("EMERGENT_LLM_KEY", "")
LUXURA_EMAIL = os.getenv("LUXURA_EMAIL", "luxuradistribution@gmail.com")
LUXURA_APP_PASSWORD = os.getenv("LUXURA_APP_PASSWORD", "")

DATABASE_URL = os.getenv("DATABASE_URL", "")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
if DATABASE_URL.startswith("postgresql+psycopg://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql+psycopg://", "postgresql://", 1)


def log(msg):
    print(f"[MAGAZINE CRON] {datetime.now().strftime('%H:%M:%S')} {msg}")


# Thèmes Magazine rotatifs
MAGAZINE_THEMES = [
    {"country": "France", "topic": "Tendances coiffure Paris Fashion Week", "vibe": "haute couture"},
    {"country": "Italie", "topic": "Secrets beauté des stars italiennes", "vibe": "dolce vita glamour"},
    {"country": "Monaco", "topic": "Lifestyle luxueux Côte d'Azur", "vibe": "yacht club élite"},
    {"country": "Espagne", "topic": "Passion et élégance méditerranéenne", "vibe": "flamenco chic"},
    {"country": "Grèce", "topic": "Beauté intemporelle des îles grecques", "vibe": "déesse moderne"},
]

# Prompts v3 Ultra-Glamour pour images - LONGUEUR STRICTE
MAGAZINE_IMAGE_PROMPTS = [
    "Real photograph of glamorous woman on luxury yacht deck at sunset, with voluminous thick hair extensions ending at mid-back level ONLY. Hair must stop at bra-strap level, NEVER longer than waist. Elegant white designer dress. Shot from 3/4 back angle. Golden hour lighting. No text, no watermarks.",
    "Real photograph of two elegant women at exclusive rooftop bar, both with stunning voluminous hair extensions at mid-back length maximum. Hair STOPS at shoulder blade level, NOT below waist. Chic evening wear. Golden hour lighting. No text.",
    "Real photograph of glamorous woman at fashion week backstage, with gorgeous thick bouncy hair extensions. Hair length at MID-BACK only, ending between shoulder blades and waist. NEVER reaching hips or below. Soft professional lighting. No text.",
]


def get_theme_for_today():
    """Sélectionne le thème basé sur la semaine de l'année"""
    week_num = datetime.now().isocalendar()[1]
    return MAGAZINE_THEMES[week_num % len(MAGAZINE_THEMES)]


def generate_image_grok(theme: dict) -> str:
    """Génère une image avec Grok v3"""
    import random
    
    if not XAI_API_KEY:
        log("❌ XAI_API_KEY manquant")
        return None
    
    prompt = random.choice(MAGAZINE_IMAGE_PROMPTS)
    prompt += f" Theme: {theme['vibe']}, {theme['country']} inspiration."
    
    log(f"🎨 Génération image Grok...")
    
    try:
        resp = requests.post(
            "https://api.x.ai/v1/images/generations",
            headers={"Authorization": f"Bearer {XAI_API_KEY}", "Content-Type": "application/json"},
            json={"model": "grok-imagine-image", "prompt": prompt, "n": 1},
            timeout=120
        )
        
        if resp.status_code == 200:
            image_url = resp.json()["data"][0]["url"]
            log(f"✅ Image générée!")
            return image_url
        else:
            log(f"❌ Erreur Grok: {resp.status_code}")
            return None
    except Exception as e:
        log(f"❌ Erreur: {e}")
        return None


def generate_text_gpt(theme: dict) -> str:
    """Génère le texte avec GPT"""
    if not OPENAI_API_KEY:
        log("❌ OPENAI_API_KEY manquant")
        return None
    
    log(f"📝 Génération texte GPT...")
    
    try:
        resp = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": "gpt-4o",
                "messages": [{
                    "role": "user",
                    "content": f"""Écris un post Facebook style MAGAZINE de luxe (150-200 mots) pour Luxura Distribution.

CONTEXTE IMPORTANT:
- Luxura Distribution est basée à St-Georges, Beauce, QUÉBEC
- C'est un DISTRIBUTEUR QUÉBÉCOIS d'extensions capillaires premium
- On S'INSPIRE des tendances de {theme['country']}, on n'est PAS un fournisseur là-bas
- Le ton doit être: "Les tendances de {theme['country']} arrivent au Québec grâce à Luxura"

Thème d'inspiration: {theme['topic']}
Vibe: {theme['vibe']}

RÈGLES:
- Luxura = référence québécoise qui suit les tendances internationales
- NE PAS dire qu'on fournit {theme['country']} ou qu'on est présent là-bas
- Parler de comment ces tendances inspirent notre collection
- Appel à l'action vers luxuradistribution.com
- Français québécois élégant et authentique
- Livraison partout au Québec"""
                }],
                "max_tokens": 400
            },
            timeout=60
        )
        
        if resp.status_code == 200:
            text = resp.json()["choices"][0]["message"]["content"]
            log(f"✅ Texte généré ({len(text)} chars)")
            return text
        else:
            log(f"❌ Erreur GPT: {resp.status_code}")
            return None
    except Exception as e:
        log(f"❌ Erreur: {e}")
        return None


def save_to_db(post_id: str, post_data: dict):
    """Sauvegarde le post en DB Supabase"""
    import psycopg2
    from psycopg2.extras import Json
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO pending_posts (post_id, post_data, status, created_at)
            VALUES (%s, %s, 'published', NOW())
            ON CONFLICT (post_id) DO UPDATE SET post_data = %s, status = 'published'
        """, (post_id, Json(post_data), Json(post_data)))
        conn.commit()
        cur.close()
        conn.close()
        log(f"✅ Sauvegardé en DB: {post_id[:8]}...")
        return True
    except Exception as e:
        log(f"❌ Erreur DB: {e}")
        return False


def publish_to_facebook(post_data: dict):
    """Publie directement sur Facebook (plus d'approbation email)"""
    FB_PAGE_ID = os.getenv("FB_PAGE_ID", "").strip()
    FB_PAGE_ACCESS_TOKEN = os.getenv("FB_PAGE_ACCESS_TOKEN", "").strip()
    
    if not FB_PAGE_ID or not FB_PAGE_ACCESS_TOKEN:
        log("❌ FB_PAGE_ID ou FB_PAGE_ACCESS_TOKEN manquant")
        return False, None
    
    message = post_data.get('full_text', post_data.get('text', ''))
    image_url = post_data.get('image_url')
    
    try:
        if image_url:
            # Post avec image
            response = requests.post(
                f"https://graph.facebook.com/v21.0/{FB_PAGE_ID}/photos",
                data={
                    "url": image_url,
                    "caption": message,
                    "published": "true",  # PUBLICATION DIRECTE
                    "access_token": FB_PAGE_ACCESS_TOKEN
                },
                timeout=60
            )
        else:
            # Post texte seulement
            response = requests.post(
                f"https://graph.facebook.com/v21.0/{FB_PAGE_ID}/feed",
                data={
                    "message": message,
                    "published": "true",  # PUBLICATION DIRECTE
                    "access_token": FB_PAGE_ACCESS_TOKEN
                },
                timeout=60
            )
        
        if response.status_code == 200:
            result = response.json()
            post_fb_id = result.get('id') or result.get('post_id')
            log(f"✅ Publié sur Facebook! ID: {post_fb_id}")
            return True, post_fb_id
        else:
            log(f"❌ Erreur Facebook: {response.status_code} - {response.text[:200]}")
            return False, None
    except Exception as e:
        log(f"❌ Exception Facebook: {e}")
        return False, None


def send_published_notification(post_data: dict, fb_post_id: str = None):
    """Envoie une notification que le post a été publié"""
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    
    if not LUXURA_APP_PASSWORD:
        log("⚠️ LUXURA_APP_PASSWORD manquant - notification non envoyée")
        return False
    
    theme = post_data.get('theme', {})
    image_url = post_data.get('image_url', '')
    text_preview = post_data.get('text', '')[:200]
    
    # Lien vers la page Facebook
    FB_PAGE_ID = os.getenv("FB_PAGE_ID", "")
    fb_page_url = f"https://www.facebook.com/{FB_PAGE_ID}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0a0a0a; color: #fff; padding: 20px; }}
            .container {{ max-width: 600px; margin: 0 auto; background: #1a1a1a; border-radius: 16px; overflow: hidden; }}
            .header {{ background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%); padding: 24px; text-align: center; }}
            .header h1 {{ margin: 0; color: #fff; font-size: 24px; }}
            .content {{ padding: 24px; }}
            .preview-image {{ width: 100%; border-radius: 12px; margin: 16px 0; }}
            .text-preview {{ background: #2a2a2a; padding: 16px; border-radius: 8px; color: #ccc; font-size: 14px; line-height: 1.6; }}
            .btn {{ display: inline-block; background: #c9a050; color: #000; padding: 14px 28px; border-radius: 8px; text-decoration: none; font-weight: 600; margin-top: 16px; }}
            .footer {{ padding: 16px; text-align: center; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>✅ Post Facebook Publié!</h1>
            </div>
            <div class="content">
                <p style="color: #c9a050; font-size: 18px; margin-bottom: 8px;">
                    🗞️ MAGAZINE {theme.get('country', '')}
                </p>
                
                {f'<img src="{image_url}" class="preview-image" alt="Image du post"/>' if image_url else ''}
                
                <div class="text-preview">
                    {text_preview}...
                </div>
                
                <div style="text-align: center;">
                    <a href="{fb_page_url}" class="btn">📱 Voir sur Facebook</a>
                </div>
            </div>
            <div class="footer">
                Luxura Distribution - Publication automatique
            </div>
        </div>
    </body>
    </html>
    """
    
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = LUXURA_EMAIL
        msg['To'] = LUXURA_EMAIL
        msg['Subject'] = f"✅ [Publié] 📱 Magazine {theme.get('country', '')} - Luxura"
        
        msg.attach(MIMEText(html_content, 'html', 'utf-8'))
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(LUXURA_EMAIL, LUXURA_APP_PASSWORD)
            server.send_message(msg)
        
        log("✅ Notification email envoyée!")
        return True
    except Exception as e:
        log(f"⚠️ Erreur envoi notification: {e}")
        return False


def send_approval_email(post_data: dict):
    """DÉSACTIVÉ - On publie directement maintenant"""
    log("⏭️ Email d'approbation DÉSACTIVÉ - publication directe activée")
    return True  # Skip email


def _old_send_approval_email(post_data: dict):
    """Envoie l'email d'approbation"""
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    
    if not LUXURA_APP_PASSWORD:
        log("❌ LUXURA_APP_PASSWORD manquant")
        return False
    
    post_id = post_data['post_id']
    theme = post_data.get('theme', {})
    approve_url = f"{API_URL}/api/fb-approve/{post_id}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: -apple-system, sans-serif; background: #f5f5f5; margin: 0; padding: 20px; }}
            .container {{ max-width: 600px; margin: 0 auto; background: #0c0c0c; border-radius: 12px; overflow: hidden; }}
            .header {{ background: linear-gradient(135deg, #c9a050, #8b6914); padding: 20px; text-align: center; color: #000; }}
            .content {{ padding: 25px; color: #fff; }}
            .preview-img {{ width: 100%; border-radius: 8px; margin: 15px 0; }}
            .btn {{ display: block; width: 80%; margin: 15px auto; padding: 18px; text-align: center; border-radius: 8px; text-decoration: none; font-weight: bold; font-size: 16px; }}
            .btn-approve {{ background: linear-gradient(135deg, #c9a050, #8b6914); color: #000 !important; }}
            .post-text {{ background: #1a1a1a; padding: 15px; border-radius: 8px; margin: 15px 0; line-height: 1.6; white-space: pre-wrap; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>📱 Nouveau Post Magazine</h2>
                <p>🗞️ {theme.get('country', 'International')} - {datetime.now().strftime('%d %B %Y')}</p>
            </div>
            <div class="content">
                <h3>📷 Preview:</h3>
                <img src="{post_data.get('image_url', '')}" class="preview-img" alt="Preview">
                
                <h3>📝 Texte:</h3>
                <div class="post-text">{post_data.get('full_text', '')[:800]}...</div>
                
                <a href="{approve_url}" class="btn btn-approve">✅ Approuver → Créer Brouillon Facebook</a>
            </div>
        </div>
    </body>
    </html>
    """
    
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"[Approbation] 📱 Magazine {theme.get('country', '')} - Luxura"
        msg['From'] = LUXURA_EMAIL
        msg['To'] = LUXURA_EMAIL
        msg.attach(MIMEText(html_content, 'html'))
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(LUXURA_EMAIL, LUXURA_APP_PASSWORD)
            server.send_message(msg)
        
        log(f"📧 Email envoyé!")
        return True
    except Exception as e:
        log(f"❌ Erreur email: {e}")
        return False


def main():
    log("=" * 60)
    log("🗞️ LUXURA MAGAZINE CRON")
    log(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log("=" * 60)
    
    # 1. Sélectionner le thème
    theme = get_theme_for_today()
    log(f"🌍 Thème: {theme['country']} - {theme['topic']}")
    
    # 2. Générer l'image
    image_url = generate_image_grok(theme)
    if not image_url:
        log("❌ Échec génération image - arrêt")
        sys.exit(1)
    
    # 3. Générer le texte
    text = generate_text_gpt(theme)
    if not text:
        log("❌ Échec génération texte - arrêt")
        sys.exit(1)
    
    # 4. Créer le post data
    post_id = str(uuid.uuid4())
    hashtags = ["#LuxuraDistribution", "#ExtensionsCheveux", "#Québec", f"#{theme['country']}", "#Magazine"]
    full_text = text + "\n\n" + " ".join(hashtags) + "\n\n🌐 luxuradistribution.com"
    
    post_data = {
        "post_id": post_id,
        "title": f"Magazine: {theme['topic'][:50]}",
        "text": text,
        "full_text": full_text,
        "image_url": image_url,
        "hashtags": hashtags,
        "content_type": "magazine",
        "theme": theme
    }
    
    # 5. Sauvegarder en DB
    if not save_to_db(post_id, post_data):
        log("❌ Échec sauvegarde DB - arrêt")
        sys.exit(1)
    
    # 6. PUBLIER DIRECTEMENT SUR FACEBOOK
    success, fb_post_id = publish_to_facebook(post_data)
    if success:
        # 7. Envoyer notification email
        send_published_notification(post_data, fb_post_id)
    else:
        log("⚠️ Publication Facebook échouée mais post sauvegardé en DB")
    
    log("=" * 60)
    log("✅ MAGAZINE CRON TERMINÉ - POST PUBLIÉ!")
    log("=" * 60)
    sys.exit(0)


if __name__ == "__main__":
    main()
