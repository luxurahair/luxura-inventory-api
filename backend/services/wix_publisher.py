# services/wix_publisher.py
"""
Publication des blogs vers Wix
Utilise les fonctions existantes de blog_automation
"""

import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


async def publish_to_wix(
    wix_api_key: str,
    wix_site_id: str,
    blog_post: Dict,
    cover_data: Dict = None,
    content_data: Dict = None
) -> bool:
    """
    Publie un blog vers Wix en utilisant le système existant.
    
    Args:
        wix_api_key: Clé API Wix
        wix_site_id: ID du site Wix
        blog_post: Données du blog (title, excerpt, content)
        cover_data: Données de l'image de couverture (optionnel)
        content_data: Données de l'image de contenu (optionnel)
    
    Returns:
        True si publication réussie, False sinon
    """
    try:
        # Importer les fonctions Wix existantes
        from blog_automation import create_wix_draft_post, publish_wix_draft
        
        logger.info(f"📤 Publishing to Wix: {blog_post.get('title', 'No title')[:50]}...")
        
        # Créer le brouillon
        draft_result = await create_wix_draft_post(
            api_key=wix_api_key,
            site_id=wix_site_id,
            title=blog_post.get('title', 'Article Luxura'),
            content=blog_post.get('content', ''),
            excerpt=blog_post.get('excerpt', ''),
            cover_image_data=cover_data,
            content_image_data=content_data
        )
        
        if not draft_result:
            logger.error("Draft creation failed")
            return False
        
        draft_id = draft_result.get('draftPost', {}).get('id')
        if not draft_id:
            logger.error("No draft ID returned")
            return False
        
        logger.info(f"   Draft created: {draft_id}")
        
        # Publier le brouillon
        published = await publish_wix_draft(wix_api_key, wix_site_id, draft_id)
        
        if published:
            logger.info(f"✅ Published to Wix successfully!")
            return True
        else:
            logger.warning(f"⚠️ Draft created but publication failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Wix publication error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def update_wix_post_image(
    wix_api_key: str,
    wix_site_id: str,
    post_id: str,
    cover_data: Dict
) -> bool:
    """
    Met à jour l'image d'un post Wix existant.
    """
    try:
        from blog_automation import attach_wix_image_to_draft
        
        return await attach_wix_image_to_draft(
            api_key=wix_api_key,
            site_id=wix_site_id,
            draft_id=post_id,
            file_desc=cover_data
        )
    except Exception as e:
        logger.error(f"Update image error: {e}")
        return False
