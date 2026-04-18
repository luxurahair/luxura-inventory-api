#!/usr/bin/env python3
"""
Script de scan quotidien de contenu
Point d'entrée pour le cron Render

Usage:
    python scripts/run_content_scan.py
    python scripts/run_content_scan.py --max-posts 5
"""

import os
import sys
import asyncio
import argparse
import logging
from datetime import datetime
from pathlib import Path

# Ajouter le répertoire parent au path
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)

# Charger les variables d'environnement
from dotenv import load_dotenv
load_dotenv(Path(BACKEND_DIR) / '.env')

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main(max_posts: int = 3):
    """
    Exécute le scan quotidien de contenu
    """
    print("=" * 60)
    print(f"[CRON] LUXURA CONTENT SCAN - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Vérifier les variables d'environnement
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        print("[CRON] ⚠️ OPENAI_API_KEY non configurée - Mode dégradé")
    else:
        print("[CRON] ✅ OPENAI_API_KEY configurée")
    
    try:
        from app.services.content_pipeline import ContentPipeline
        
        pipeline = ContentPipeline()
        results = await pipeline.run_daily_scan(max_posts=max_posts)
        
        print("\n" + "=" * 60)
        print("[CRON] RÉSULTATS DU SCAN")
        print("=" * 60)
        print(f"[CRON] Articles trouvés: {results['articles_found']}")
        print(f"[CRON] Articles pertinents: {results['articles_relevant']}")
        print(f"[CRON] Nouveaux articles: {results['articles_new']}")
        print(f"[CRON] Posts générés: {results['posts_generated']}")
        print(f"[CRON] Posts approuvés: {results['posts_approved']}")
        
        if results['errors']:
            print(f"[CRON] Erreurs: {len(results['errors'])}")
            for error in results['errors']:
                print(f"[CRON]   - {error}")
        
        # Afficher les posts générés
        if results['posts']:
            print("\n[CRON] POSTS GÉNÉRÉS:")
            for i, post in enumerate(results['posts'], 1):
                print(f"\n[CRON] --- Post {i} ---")
                print(f"[CRON] Titre: {post.get('post_title', 'N/A')[:60]}...")
                print(f"[CRON] Score: {post.get('confidence_score', 0):.2f}")
                print(f"[CRON] Status: {post.get('status')}")
                print(f"[CRON] Texte: {post.get('post_text', '')[:100]}...")
        
        print("\n" + "=" * 60)
        print("[CRON] ✅ SCAN TERMINÉ AVEC SUCCÈS")
        print("=" * 60)
        
        return 0
        
    except Exception as e:
        print(f"\n[CRON] ❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scan quotidien de contenu Luxura")
    parser.add_argument(
        "--max-posts",
        type=int,
        default=3,
        help="Nombre maximum de posts à générer (défaut: 3)"
    )
    
    args = parser.parse_args()
    
    exit_code = asyncio.run(main(max_posts=args.max_posts))
    sys.exit(exit_code)
