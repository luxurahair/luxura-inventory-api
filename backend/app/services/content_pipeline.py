"""
Pipeline de contenu automatisé
Orchestre la collecte, le filtrage et la génération de posts
Inclut la génération d'images DALL-E 3 et la publication Facebook
"""

import os
import logging
import json
import hashlib
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from pathlib import Path

from .content_discovery import ContentDiscoveryService
from .facebook_publisher import FacebookPublisher
from .email_approval import send_approval_email, traduire_date_fr

logger = logging.getLogger(__name__)


class ContentPipeline:
    """
    Pipeline complet de génération de contenu Facebook
    
    Flux:
    1. Collecte des actualités (Google News)
    2. Filtrage de pertinence (extensions capillaires)
    3. Dédoublonnage
    4. Traduction en français
    5. Génération du post Facebook
    6. Sauvegarde en brouillon
    """
    
    def __init__(self, db_session=None):
        self.discovery_service = ContentDiscoveryService()
        self.facebook_publisher = FacebookPublisher()
        self.db_session = db_session
        self.history_file = Path("/tmp/luxura_content_history.json")
        self.history = self._load_history()
    
    def _load_history(self) -> Dict:
        """Charge l'historique des contenus traités"""
        try:
            if self.history_file.exists():
                with open(self.history_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Erreur chargement historique: {e}")
        return {"processed_urls": [], "last_run": None}
    
    def _save_history(self):
        """Sauvegarde l'historique"""
        try:
            # Garder seulement les 30 derniers jours
            self.history["last_run"] = datetime.now().isoformat()
            with open(self.history_file, 'w') as f:
                json.dump(self.history, f)
        except Exception as e:
            logger.error(f"Erreur sauvegarde historique: {e}")
    
    async def run_daily_scan(self, max_posts: int = 3, generate_images: bool = True) -> Dict:
        """
        Exécute le scan quotidien complet
        
        Args:
            max_posts: Nombre max de posts à générer
            generate_images: Si True, génère les images DALL-E 3
        
        Returns:
            Dict avec les résultats du scan
        """
        logger.info("=" * 60)
        logger.info("🚀 DÉMARRAGE DU SCAN QUOTIDIEN LUXURA")
        if generate_images:
            logger.info("🎨 Mode: AVEC génération d'images DALL-E 3")
        logger.info("=" * 60)
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "articles_found": 0,
            "articles_relevant": 0,
            "articles_new": 0,
            "posts_generated": 0,
            "posts_approved": 0,
            "images_generated": 0,
            "posts": [],
            "errors": []
        }
        
        try:
            # Étape 1: Collecte
            logger.info("🔍 Étape 1: Collecte des actualités...")
            items = await self.discovery_service.discover_canada_hair_news(max_items=30)
            results["articles_found"] = len(items)
            logger.info(f"   → {len(items)} articles trouvés")
            
            if not items:
                logger.warning("Aucun article trouvé")
                return results
            
            # Étape 2: Filtrage
            logger.info("🎯 Étape 2: Filtrage de pertinence...")
            relevant_items = self.discovery_service.filter_relevant_items(items)
            results["articles_relevant"] = len(relevant_items)
            logger.info(f"   → {len(relevant_items)} articles pertinents")
            
            if not relevant_items:
                logger.warning("Aucun article pertinent")
                return results
            
            # Étape 3: Dédoublonnage
            logger.info("🔄 Étape 3: Dédoublonnage...")
            new_items = self._deduplicate(relevant_items)
            results["articles_new"] = len(new_items)
            logger.info(f"   → {len(new_items)} nouveaux articles")
            
            if not new_items:
                logger.info("Pas de nouveau contenu")
                return results
            
            # Étape 4: Génération des posts (max 3)
            logger.info(f"📝 Étape 4: Génération de {min(len(new_items), max_posts)} posts...")
            
            for item in new_items[:max_posts]:
                try:
                    post = await self.discovery_service.generate_facebook_post(item)
                    
                    # Étape 5: Génération d'image DALL-E 3
                    if generate_images and post.get("image_prompt"):
                        logger.info(f"🎨 Étape 5: Génération image DALL-E 3...")
                        image_url = await self.facebook_publisher.generate_image(
                            post["image_prompt"]
                        )
                        if image_url:
                            post["image_url"] = image_url
                            post["has_image"] = True
                            results["images_generated"] += 1
                            logger.info(f"   ✅ Image générée!")
                        else:
                            post["has_image"] = False
                            logger.warning(f"   ⚠️ Image non générée")
                    
                    # Ajouter l'URL à l'historique
                    self.history["processed_urls"].append(item["source_url"])
                    
                    results["posts"].append(post)
                    results["posts_generated"] += 1
                    
                    if post.get("status") == "approved":
                        results["posts_approved"] += 1
                    
                    # Étape 6: PUBLICATION DIRECTE SUR FACEBOOK
                    logger.info(f"📘 Étape 6: Publication directe sur Facebook...")
                    try:
                        # Publier sur Facebook
                        fb_result = await self.facebook_publisher.publish_post(
                            text=post.get("post_text", ""),
                            image_url=post.get("image_url"),
                            hashtags=post.get("hashtags", [])
                        )
                        
                        if fb_result.get("success"):
                            logger.info(f"   ✅ Publié sur Facebook! ID: {fb_result.get('post_id')}")
                            post["published_to_facebook"] = True
                            post["facebook_post_id"] = fb_result.get("post_id")
                            
                            # Envoyer notification email (pas approbation)
                            await self._send_published_notification(post)
                        else:
                            logger.warning(f"   ⚠️ Publication échouée: {fb_result.get('error')}")
                            post["published_to_facebook"] = False
                    except Exception as fb_error:
                        logger.warning(f"   ⚠️ Erreur publication Facebook: {fb_error}")
                        post["published_to_facebook"] = False
                    
                    logger.info(f"   ✅ Post généré: {post.get('post_title', '')[:50]}...")
                    logger.info(f"      Score: {post.get('confidence_score', 0):.2f} | Status: {post.get('status')} | Image: {'✅' if post.get('has_image') else '❌'}")
                    
                except Exception as e:
                    logger.error(f"Erreur génération post: {e}")
                    results["errors"].append(str(e))
            
            # Sauvegarder l'historique
            self._save_history()
            
            logger.info("=" * 60)
            logger.info(f"✅ SCAN TERMINÉ: {results['posts_generated']} posts générés, {results['images_generated']} images")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"Erreur pipeline: {e}")
            results["errors"].append(str(e))
        
        return results
    
    def _deduplicate(self, items: List[Dict]) -> List[Dict]:
        """
        Dédoublonne les articles
        """
        processed_urls = set(self.history.get("processed_urls", []))
        new_items = []
        
        for item in items:
            url = item["source_url"]
            url_hash = hashlib.md5(url.encode()).hexdigest()
            
            if url not in processed_urls and url_hash not in processed_urls:
                new_items.append(item)
                processed_urls.add(url)
        
        # Nettoyer l'historique (garder max 1000 URLs)
        if len(self.history.get("processed_urls", [])) > 1000:
            self.history["processed_urls"] = self.history["processed_urls"][-500:]
        
        return new_items
    
    async def generate_and_publish_post(
        self, 
        item: Dict, 
        generate_image: bool = True,
        publish: bool = False
    ) -> Dict:
        """
        Génère un post avec image et optionnellement le publie sur Facebook
        
        Args:
            item: Article source
            generate_image: Si True, génère une image DALL-E 3
            publish: Si True, publie directement sur Facebook
            
        Returns:
            Dict avec le post et les infos de publication
        """
        # Générer le post texte
        post = await self.discovery_service.generate_facebook_post(item)
        
        # Générer l'image DALL-E 3
        if generate_image and post.get("image_prompt"):
            logger.info(f"🎨 Génération image DALL-E 3...")
            image_url = await self.facebook_publisher.generate_image(post["image_prompt"])
            if image_url:
                post["image_url"] = image_url
                post["has_image"] = True
                logger.info(f"   ✅ Image générée!")
            else:
                post["has_image"] = False
        
        # Sauvegarder en base si disponible
        if self.db_session:
            await self._save_post_to_db(post)
        
        # Publier si demandé et score suffisant
        if publish and post.get("confidence_score", 0) >= 0.85:
            logger.info(f"📘 Publication Facebook...")
            
            # Construire le texte complet avec hashtags
            full_text = post.get("post_text", "")
            if post.get("hashtags"):
                full_text += "\n\n" + " ".join(post["hashtags"])
            
            success, post_id, error = await self.facebook_publisher.publish_post(
                full_text, 
                post.get("image_url")
            )
            
            post["published"] = success
            post["published_post_id"] = post_id
            if error:
                post["publish_error"] = error
            
            if success:
                post["status"] = "published"
                logger.info(f"   ✅ Publié! Post ID: {post_id}")
        
        return post
    
    async def _save_post_to_db(self, post: Dict):
        """
        Sauvegarde un post en base de données
        """
        # TODO: Implémenter avec SQLAlchemy
        pass
    
    async def _send_published_notification(self, post: Dict):
        """
        Envoie une notification email après publication (pas d'approbation)
        """
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        
        LUXURA_EMAIL = os.getenv("LUXURA_EMAIL", "info@luxuradistribution.com")
        LUXURA_APP_PASSWORD = os.getenv("LUXURA_APP_PASSWORD")
        
        if not LUXURA_APP_PASSWORD:
            logger.warning("⚠️ LUXURA_APP_PASSWORD manquant - notification non envoyée")
            return
        
        try:
            title = post.get("post_title", "Post Facebook")[:100]
            text_preview = post.get("post_text", "")[:200]
            image_url = post.get("image_url", "")
            fb_post_id = post.get("facebook_post_id", "")
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0a0a0a; color: #fff; padding: 20px; }}
                    .container {{ max-width: 600px; margin: 0 auto; background: #1a1a1a; border-radius: 16px; overflow: hidden; }}
                    .header {{ background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%); padding: 24px; text-align: center; }}
                    .header h1 {{ margin: 0; color: #fff; font-size: 24px; }}
                    .content {{ padding: 24px; }}
                    .preview-image {{ width: 100%; border-radius: 12px; margin: 16px 0; }}
                    .text-preview {{ background: #2a2a2a; padding: 16px; border-radius: 8px; color: #ccc; font-size: 14px; }}
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
                        <p style="color: #c9a050; font-size: 16px;">{title}</p>
                        {f'<img src="{image_url}" class="preview-image" alt="Image"/>' if image_url else ''}
                        <div class="text-preview">{text_preview}...</div>
                        <div style="text-align: center;">
                            <a href="https://www.facebook.com/luxuradistribution" class="btn">📱 Voir sur Facebook</a>
                        </div>
                    </div>
                    <div class="footer">Luxura Distribution - Publication automatique</div>
                </div>
            </body>
            </html>
            """
            
            msg = MIMEMultipart('alternative')
            msg['From'] = LUXURA_EMAIL
            msg['To'] = LUXURA_EMAIL
            msg['Subject'] = f"✅ [Publié] {title[:50]}... - Luxura"
            msg.attach(MIMEText(html_content, 'html', 'utf-8'))
            
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(LUXURA_EMAIL, LUXURA_APP_PASSWORD)
                server.send_message(msg)
            
            logger.info("   ✅ Notification email envoyée!")
        except Exception as e:
            logger.warning(f"   ⚠️ Erreur notification email: {e}")
