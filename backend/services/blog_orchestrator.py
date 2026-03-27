# services/blog_orchestrator.py
"""
Orchestrateur principal - Version V8 propre et robuste
Utilise le nouveau système de briefs techniques réalistes
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

# Flags de disponibilité des pipelines
HAS_IMAGE_PIPELINE = False
HAS_VIDEO_PIPELINE = False

# Import du pipeline d'images
try:
    from image_generation import generate_and_upload_blog_images
    HAS_IMAGE_PIPELINE = True
    logger.info("✅ Image pipeline loaded")
except ImportError as e:
    logger.warning(f"Image pipeline unavailable: {e}")
    async def generate_and_upload_blog_images(**kwargs):
        return None, None

# Import du pipeline vidéo (optionnel)
try:
    from services.video_brief_generator import generate_video_brief, should_generate_video
    from services.video_generator import generate_short_video
    HAS_VIDEO_PIPELINE = True
    logger.info("✅ Video pipeline loaded")
except ImportError as e:
    logger.warning(f"Video pipeline unavailable: {e}")
    def generate_video_brief(x): return {"video_mode": "none"}
    async def generate_short_video(**kwargs): return None
    def should_generate_video(x): return False


async def generate_daily_blogs(
    db,
    openai_key: str,
    wix_api_key: str = None,
    wix_site_id: str = None,
    count: int = 2,
    publish_to_wix: bool = True,
    send_email: bool = True
) -> List[Dict]:
    """
    V8: Génère les blogs quotidiens de façon robuste.
    
    Cette version utilise le nouveau système de briefs V8 avec prompts techniques réalistes:
    - Halo = fil invisible, pose simple à la maison
    - I-Tip = microbilles + pince (close-up précis)
    - Tape-in = méthode sandwich adhésif
    - Genius Weft = couture sur rangée perlée
    """
    results = []

    # Récupération des titres existants pour éviter doublons
    try:
        existing_titles = []
        async for p in db.blog_posts.find({}, {"title": 1}):
            existing_titles.append(p.get("title", "").lower())
    except Exception as e:
        logger.warning(f"Could not fetch existing titles: {e}")
        existing_titles = []

    # Import des fonctions existantes de blog_automation
    try:
        from blog_automation import (
            BLOG_TOPICS_EXTENDED,
            generate_blog_with_ai,
            create_wix_draft_post,
            publish_wix_draft,
            send_blog_images_email
        )
        from image_brief_generator import generate_image_brief
    except ImportError as e:
        logger.error(f"Failed to import blog_automation: {e}")
        return []

    # Sélection des topics
    import random
    available_topics = [t for t in BLOG_TOPICS_EXTENDED if t["topic"].lower() not in existing_titles]
    
    if len(available_topics) < count:
        available_topics = BLOG_TOPICS_EXTENDED.copy()
        random.shuffle(available_topics)
    
    # Diversifier les catégories
    selected_topics = []
    categories_used = []
    for topic in available_topics:
        if len(selected_topics) >= count:
            break
        if topic["category"] not in categories_used or len(categories_used) >= 4:
            selected_topics.append(topic)
            categories_used.append(topic["category"])
    
    logger.info(f"📝 V8 Selected {len(selected_topics)} topics")

    for topic_data in selected_topics:
        topic = topic_data.get('topic', 'Article Luxura')
        category = topic_data.get('category', 'general')
        
        logger.info(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        logger.info(f"📝 Processing: {topic[:60]}...")

        # 1. Génération du contenu texte avec GPT-4o
        try:
            blog_data = await generate_blog_with_ai(topic_data, openai_key)
            if not blog_data:
                logger.warning(f"Content generation failed for: {topic}")
                continue
            logger.info(f"   ✅ Text content generated")
        except Exception as e:
            logger.error(f"Content generation error: {e}")
            continue

        # 2. Générer le brief V8 pour décider du mode visuel
        brief = generate_image_brief(blog_data)
        logger.info(f"   📸 V8 Brief: mode={brief['visual_mode']}, is_technical={brief.get('is_technical', False)}")

        # 3. Génération des images (utilise le système V7/V8 existant)
        cover_data = None
        content_data = None
        if publish_to_wix and HAS_IMAGE_PIPELINE and wix_api_key and wix_site_id:
            try:
                cover_data, content_data = await generate_and_upload_blog_images(
                    api_key=wix_api_key,
                    site_id=wix_site_id,
                    category=category,
                    blog_title=blog_data.get('title', topic),
                    focus_product=topic_data.get('focus_product'),
                    blog_data=blog_data
                )
                logger.info(f"   ✅ Images: cover={bool(cover_data)}, content={bool(content_data)}")
            except Exception as e:
                logger.error(f"Image generation failed: {e}")

        # 4. Vidéo (optionnel, non-bloquant)
        video_url = None
        if publish_to_wix and cover_data and HAS_VIDEO_PIPELINE:
            try:
                video_brief = generate_video_brief(blog_data)
                if should_generate_video(video_brief):
                    logger.info(f"   🎥 Generating video: {video_brief['video_mode']}")
                    video_url = await generate_short_video(
                        video_brief=video_brief,
                        image_url=cover_data.get("static_url")
                    )
                    if video_url:
                        logger.info(f"   ✅ Video generated")
            except Exception as e:
                logger.warning(f"Video skipped (non-blocking): {e}")

        # 5. Sauvegarde en base locale
        post_id = f"auto-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}"
        
        blog_post = {
            "id": post_id,
            "title": blog_data.get("title"),
            "excerpt": blog_data.get("excerpt"),
            "content": blog_data.get("content"),
            "image": cover_data.get("static_url") if cover_data else None,
            "wix_image_url": cover_data.get("static_url") if cover_data else None,
            "video_url": video_url,
            "category": category,
            "focus_product": topic_data.get("focus_product"),
            "author": "Luxura Distribution",
            "created_at": datetime.now(timezone.utc),
            "auto_generated": True,
            "needs_human_review": True,
            "published_to_wix": False,
            "visual_mode": brief['visual_mode'],
            "is_technical": brief.get('is_technical', False),
        }

        try:
            await db.blog_posts.insert_one(blog_post)
            logger.info(f"   💾 Saved to DB: {post_id}")
        except Exception as e:
            logger.error(f"DB save failed: {e}")
            continue

        # 6. Publication vers Wix
        if publish_to_wix and wix_api_key and wix_site_id:
            try:
                draft_result = await create_wix_draft_post(
                    api_key=wix_api_key,
                    site_id=wix_site_id,
                    title=blog_data.get('title'),
                    content=blog_data.get('content'),
                    excerpt=blog_data.get('excerpt'),
                    cover_image_data=cover_data,
                    content_image_data=content_data
                )
                
                if draft_result:
                    draft_id = draft_result.get('draftPost', {}).get('id')
                    if draft_id:
                        published = await publish_wix_draft(wix_api_key, wix_site_id, draft_id)
                        if published:
                            blog_post["published_to_wix"] = True
                            blog_post["wix_draft_id"] = draft_id
                            await db.blog_posts.update_one(
                                {"id": post_id}, 
                                {"$set": {"published_to_wix": True, "wix_draft_id": draft_id}}
                            )
                            logger.info(f"   ✅ Published to Wix: {draft_id}")
                        else:
                            logger.warning(f"   ⚠️ Draft created but publish failed")
            except Exception as e:
                logger.error(f"Wix publication failed: {e}")

        results.append(blog_post)
        logger.info(f"✅ Blog completed: {blog_post['title'][:50]}...")

    # Envoi email récap (non bloquant)
    if send_email and results:
        try:
            await send_blog_images_email(results)
            logger.info(f"📧 Summary email sent")
        except Exception as e:
            logger.warning(f"Summary email skipped: {e}")

    logger.info(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    logger.info(f"🎉 V8 Batch completed: {len(results)} blogs generated")
    return results
