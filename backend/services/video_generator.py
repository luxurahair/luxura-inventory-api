# services/video_generator.py
"""
Génération de vidéos courtes avec FAL.AI (Kling 2.0)
Version V2 - FAL.AI Integration

FAL.AI donne accès à Kling 2.0 qui est aussi bon que Runway Gen-3
Prix: ~$0.10 par vidéo de 5 secondes
"""

import os
import logging
import asyncio
import httpx
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# Configuration FAL.AI
# Supporte les deux noms de variable: FAL_KEY et FLA_AI_API_KEY
FAL_KEY = os.getenv("FAL_KEY") or os.getenv("FLA_AI_API_KEY")
FAL_ENABLED = bool(FAL_KEY)

if FAL_ENABLED:
    logger.info("✅ FAL.AI video generation enabled")
else:
    logger.info("⚠️ FAL.AI not configured (FAL_KEY missing)")


async def generate_short_video(
    video_brief: Dict,
    image_url: Optional[str] = None
) -> Optional[str]:
    """
    Génère une vidéo courte avec FAL.AI (Kling 2.0).
    
    Args:
        video_brief: Brief de la vidéo (scene, motion, duration, etc.)
        image_url: URL de l'image source pour image-to-video
    
    Returns:
        URL de la vidéo générée ou None si échec
    """
    if not FAL_ENABLED:
        logger.info("🎥 Video generation skipped (FAL_KEY not configured)")
        return None
    
    if not image_url:
        logger.warning("🎥 Video generation skipped (no source image)")
        return None
    
    try:
        # Construire le prompt pour la vidéo
        scene = video_brief.get("scene", "")
        motion = video_brief.get("motion", "Beautiful woman with very long flowing hair")
        
        # Prompt optimisé pour Kling
        prompt = f"{scene}. {motion}. Cinematic quality, smooth camera movement, natural hair flow, professional lighting."
        
        # Règles de sécurité
        negative_prompt = "short hair, bob cut, men, masculine, cartoon, animation, text, watermark, low quality"
        
        logger.info(f"🎥 Generating video with FAL.AI/Kling...")
        logger.info(f"   Source image: {image_url[:60]}...")
        logger.info(f"   Duration: {video_brief.get('duration_seconds', 5)}s")
        
        async with httpx.AsyncClient(timeout=300.0) as client:
            # Appel à FAL.AI - Kling Image-to-Video
            response = await client.post(
                "https://queue.fal.run/fal-ai/kling-video/v1.5/pro/image-to-video",
                headers={
                    "Authorization": f"Key {FAL_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "prompt": prompt,
                    "negative_prompt": negative_prompt,
                    "image_url": image_url,
                    "duration": str(video_brief.get("duration_seconds", 5)),
                    "aspect_ratio": video_brief.get("aspect_ratio", "16:9")
                }
            )
            
            if response.status_code not in (200, 201, 202):
                logger.error(f"FAL.AI error: {response.status_code} - {response.text}")
                return None
            
            result = response.json()
            
            # FAL.AI utilise un système de queue
            request_id = result.get("request_id")
            if not request_id:
                # Résultat direct
                video_url = result.get("video", {}).get("url")
                if video_url:
                    logger.info(f"✅ Video generated: {video_url[:60]}...")
                    return video_url
                return None
            
            logger.info(f"   Queue ID: {request_id}")
            
            # Polling pour attendre le résultat
            for attempt in range(60):  # Max 5 minutes
                await asyncio.sleep(5)
                
                status_response = await client.get(
                    f"https://queue.fal.run/fal-ai/kling-video/requests/{request_id}/status",
                    headers={"Authorization": f"Key {FAL_KEY}"}
                )
                
                if status_response.status_code != 200:
                    continue
                
                status_data = status_response.json()
                status = status_data.get("status")
                
                if status == "COMPLETED":
                    # Récupérer le résultat
                    result_response = await client.get(
                        f"https://queue.fal.run/fal-ai/kling-video/requests/{request_id}",
                        headers={"Authorization": f"Key {FAL_KEY}"}
                    )
                    
                    if result_response.status_code == 200:
                        final_result = result_response.json()
                        video_url = final_result.get("video", {}).get("url")
                        if video_url:
                            logger.info(f"✅ Video generated: {video_url[:60]}...")
                            return video_url
                    return None
                
                elif status == "FAILED":
                    error = status_data.get("error", "Unknown error")
                    logger.error(f"Video generation failed: {error}")
                    return None
                
                elif status in ("IN_QUEUE", "IN_PROGRESS"):
                    if attempt % 6 == 0:  # Log every 30 seconds
                        logger.info(f"   Still processing... ({attempt * 5}s)")
                    continue
            
            logger.error("Video generation timed out")
            return None
            
    except Exception as e:
        logger.error(f"Video generation error: {e}")
        import traceback
        traceback.print_exc()
        return None


async def generate_text_to_video(
    prompt: str,
    duration: int = 5,
    aspect_ratio: str = "16:9"
) -> Optional[str]:
    """
    Génère une vidéo à partir d'un prompt texte uniquement (sans image source).
    """
    if not FAL_ENABLED:
        return None
    
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                "https://queue.fal.run/fal-ai/kling-video/v1.5/pro/text-to-video",
                headers={
                    "Authorization": f"Key {FAL_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "prompt": prompt,
                    "negative_prompt": "short hair, men, cartoon, low quality",
                    "duration": str(duration),
                    "aspect_ratio": aspect_ratio
                }
            )
            
            if response.status_code not in (200, 201, 202):
                return None
            
            result = response.json()
            video_url = result.get("video", {}).get("url")
            return video_url
            
    except Exception as e:
        logger.error(f"Text-to-video error: {e}")
        return None
