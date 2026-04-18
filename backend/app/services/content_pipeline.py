"""
Pipeline de contenu automatisé
Orchestre la collecte, le filtrage et la génération de posts
"""

import os
import logging
import json
import hashlib
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from pathlib import Path

from .content_discovery import ContentDiscoveryService

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
    
    async def run_daily_scan(self, max_posts: int = 3) -> Dict:
        """
        Exécute le scan quotidien complet
        
        Returns:
            Dict avec les résultats du scan
        """
        logger.info("=" * 60)
        logger.info("🚀 DÉMARRAGE DU SCAN QUOTIDIEN LUXURA")
        logger.info("=" * 60)
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "articles_found": 0,
            "articles_relevant": 0,
            "articles_new": 0,
            "posts_generated": 0,
            "posts_approved": 0,
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
                    
                    # Ajouter l'URL à l'historique
                    self.history["processed_urls"].append(item["source_url"])
                    
                    results["posts"].append(post)
                    results["posts_generated"] += 1
                    
                    if post.get("status") == "approved":
                        results["posts_approved"] += 1
                    
                    logger.info(f"   ✅ Post généré: {post.get('post_title', '')[:50]}...")
                    logger.info(f"      Score: {post.get('confidence_score', 0):.2f} | Status: {post.get('status')}")
                    
                except Exception as e:
                    logger.error(f"Erreur génération post: {e}")
                    results["errors"].append(str(e))
            
            # Sauvegarder l'historique
            self._save_history()
            
            logger.info("=" * 60)
            logger.info(f"✅ SCAN TERMINÉ: {results['posts_generated']} posts générés")
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
    
    async def generate_and_publish_post(self, item: Dict, publish: bool = False) -> Dict:
        """
        Génère un post et optionnellement le publie
        """
        # Générer le post
        post = await self.discovery_service.generate_facebook_post(item)
        
        # Sauvegarder en base si disponible
        if self.db_session:
            await self._save_post_to_db(post)
        
        # Publier si demandé et score suffisant
        if publish and post.get("confidence_score", 0) >= 0.85:
            # TODO: Intégrer facebook_publisher.py
            pass
        
        return post
    
    async def _save_post_to_db(self, post: Dict):
        """
        Sauvegarde un post en base de données
        """
        # TODO: Implémenter avec SQLAlchemy
        pass
