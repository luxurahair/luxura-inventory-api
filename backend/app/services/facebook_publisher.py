"""
Service de publication Facebook avec génération d'images
Supporte: Grok (xAI) et DALL-E 3 (OpenAI)
"""

import os
import logging
import httpx
from typing import Optional, Dict, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class FacebookPublisher:
    """
    Publie des posts Facebook avec images générées par Grok ou DALL-E 3
    Priorité: Grok > DALL-E
    """
    
    def __init__(self):
        # Clés API
        self.grok_key = os.getenv("XAI_API_KEY") or os.getenv("GROK_API_KEY")
        self.openai_key = os.getenv("OPENAI_API_KEY")
        
        # Facebook
        self.fb_token = os.getenv("FB_PAGE_ACCESS_TOKEN")
        self.fb_page_id = os.getenv("FB_PAGE_ID", "1838415193042352")
        self.fb_api_version = "v25.0"
        
        # Détecter le provider d'images
        if self.grok_key:
            self.image_provider = "grok"
            logger.info("🎨 Image provider: Grok (xAI)")
        elif self.openai_key:
            self.image_provider = "dalle"
            logger.info("🎨 Image provider: DALL-E 3 (OpenAI)")
        else:
            self.image_provider = None
            logger.warning("⚠️ Aucune clé API pour génération d'images")
    
    # ============================================
    # GÉNÉRATION D'IMAGE - GROK (xAI)
    # ============================================
    
    async def generate_image_grok(self, prompt: str) -> Optional[str]:
        """
        Génère une image avec Grok (xAI) et retourne l'URL.
        
        Args:
            prompt: Le prompt pour l'image
            
        Returns:
            URL de l'image ou None si erreur
        """
        if not self.grok_key:
            return None
        
        logger.info(f"🎨 Génération image Grok (xAI)...")
        logger.info(f"   Prompt: {prompt[:80]}...")
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    "https://api.x.ai/v1/images/generations",
                    headers={
                        "Authorization": f"Bearer {self.grok_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "grok-2-image",
                        "prompt": prompt,
                        "n": 1
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    # Grok retourne les images dans data[].url
                    if data.get("data") and len(data["data"]) > 0:
                        image_url = data["data"][0].get("url")
                        if image_url:
                            logger.info(f"✅ Image Grok générée!")
                            return image_url
                    
                    logger.error(f"❌ Réponse Grok inattendue: {data}")
                    return None
                else:
                    logger.error(f"❌ Erreur Grok: {response.status_code}")
                    logger.error(response.text[:500])
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Erreur Grok: {e}")
            return None
    
    # ============================================
    # GÉNÉRATION D'IMAGE - DALL-E 3 (Fallback)
    # ============================================
    
    async def generate_image_dalle(self, prompt: str) -> Optional[str]:
        """
        Génère une image avec DALL-E 3 et retourne l'URL temporaire.
        """
        if not self.openai_key:
            return None
        
        logger.info(f"🎨 Génération image DALL-E 3...")
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/images/generations",
                    headers={
                        "Authorization": f"Bearer {self.openai_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "dall-e-3",
                        "prompt": prompt,
                        "n": 1,
                        "size": "1792x1024",
                        "quality": "standard"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    image_url = data["data"][0]["url"]
                    logger.info(f"✅ Image DALL-E générée!")
                    return image_url
                else:
                    logger.error(f"❌ Erreur DALL-E: {response.status_code}")
                    logger.error(response.text[:300])
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Erreur DALL-E: {e}")
            return None
    
    # ============================================
    # GÉNÉRATION D'IMAGE - AUTO (Grok > DALL-E)
    # ============================================
    
    async def generate_image(self, prompt: str) -> Optional[str]:
        """
        Génère une image avec le meilleur provider disponible.
        Priorité: Grok > DALL-E
        """
        # Essayer Grok d'abord
        if self.grok_key:
            image_url = await self.generate_image_grok(prompt)
            if image_url:
                return image_url
            logger.warning("⚠️ Grok a échoué, fallback vers DALL-E...")
        
        # Fallback vers DALL-E
        if self.openai_key:
            return await self.generate_image_dalle(prompt)
        
        logger.error("❌ Aucun provider d'images disponible")
        return None
    
    # ============================================
    # PUBLICATION FACEBOOK
    # ============================================
    
    async def publish_post(
        self, 
        message: str, 
        image_url: Optional[str] = None
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Publie un post sur Facebook avec ou sans image.
        
        Args:
            message: Texte du post
            image_url: URL de l'image (optionnel)
            
        Returns:
            Tuple (success, post_id, error_message)
        """
        if not self.fb_token:
            logger.error("FB_PAGE_ACCESS_TOKEN non configuré")
            return False, None, "FB_PAGE_ACCESS_TOKEN non configuré"
        
        logger.info(f"📘 Publication Facebook...")
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                if image_url:
                    # Post avec image (photo)
                    logger.info(f"   Avec image: {image_url[:60]}...")
                    response = await client.post(
                        f"https://graph.facebook.com/{self.fb_api_version}/{self.fb_page_id}/photos",
                        data={
                            "url": image_url,
                            "caption": message,
                            "access_token": self.fb_token
                        }
                    )
                else:
                    # Post texte seul
                    logger.info(f"   Sans image (texte seul)")
                    response = await client.post(
                        f"https://graph.facebook.com/{self.fb_api_version}/{self.fb_page_id}/feed",
                        data={
                            "message": message,
                            "access_token": self.fb_token
                        }
                    )
                
                result = response.json()
                
                if "error" in result:
                    error = result["error"]
                    error_msg = error.get("message", "Erreur inconnue")
                    logger.error(f"❌ Erreur Facebook: {error_msg}")
                    
                    if error.get("code") == 190:
                        error_msg = "Token expiré! Mettez à jour FB_PAGE_ACCESS_TOKEN"
                    
                    return False, None, error_msg
                
                post_id = result.get("id") or result.get("post_id")
                logger.info(f"✅ Publié! Post ID: {post_id}")
                return True, post_id, None
                
        except Exception as e:
            logger.error(f"❌ Erreur publication: {e}")
            return False, None, str(e)
    
    # ============================================
    # WORKFLOW COMPLET
    # ============================================
    
    async def generate_and_publish(
        self, 
        post_text: str, 
        image_prompt: str,
        publish: bool = True
    ) -> Dict:
        """
        Workflow complet: génère l'image puis publie.
        
        Args:
            post_text: Texte du post Facebook
            image_prompt: Prompt DALL-E pour l'image
            publish: Si True, publie sur Facebook. Sinon juste génère l'image.
            
        Returns:
            Dict avec les résultats
        """
        result = {
            "timestamp": datetime.now().isoformat(),
            "post_text": post_text[:200] + "...",
            "image_prompt": image_prompt,
            "image_url": None,
            "published": False,
            "post_id": None,
            "errors": []
        }
        
        # Étape 1: Générer l'image
        image_url = await self.generate_image(image_prompt)
        result["image_url"] = image_url
        
        if not image_url:
            result["errors"].append("Échec génération image DALL-E")
            # On peut quand même publier sans image si demandé
        
        # Étape 2: Publier sur Facebook
        if publish:
            success, post_id, error = await self.publish_post(post_text, image_url)
            result["published"] = success
            result["post_id"] = post_id
            if error:
                result["errors"].append(error)
        
        return result
