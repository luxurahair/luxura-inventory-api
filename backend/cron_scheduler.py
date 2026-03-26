#!/usr/bin/env python3
"""
CRON Scheduler pour Luxura Blog Automation
Génère automatiquement des blogs 2x par jour (08:00 et 16:00 EST)
"""

import os
import asyncio
import logging
import httpx
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv

load_dotenv()

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
BLOG_COUNT_PER_RUN = 2  # Nombre de blogs à générer par exécution
API_URL = "http://localhost:8001/api/blog/auto-generate"


async def generate_blogs():
    """Appelle l'API pour générer des blogs."""
    try:
        logger.info(f"🚀 Starting scheduled blog generation at {datetime.now()}")
        
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                API_URL,
                json={"count": BLOG_COUNT_PER_RUN},
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                posts = result.get("posts", [])
                logger.info(f"✅ Successfully generated {len(posts)} blog(s)")
                for post in posts:
                    logger.info(f"   - {post.get('title', 'No title')[:60]}...")
            else:
                logger.error(f"❌ Blog generation failed: {response.status_code} - {response.text[:200]}")
                
    except Exception as e:
        logger.error(f"❌ Error in scheduled blog generation: {e}")


def start_scheduler():
    """Démarre le planificateur CRON."""
    scheduler = AsyncIOScheduler(timezone="America/Montreal")
    
    # Génération à 08:00 EST
    scheduler.add_job(
        generate_blogs,
        CronTrigger(hour=8, minute=0),
        id="morning_blog_generation",
        name="Morning Blog Generation (08:00)"
    )
    
    # Génération à 16:00 EST
    scheduler.add_job(
        generate_blogs,
        CronTrigger(hour=16, minute=0),
        id="afternoon_blog_generation",
        name="Afternoon Blog Generation (16:00)"
    )
    
    scheduler.start()
    logger.info("=" * 60)
    logger.info("🕐 LUXURA BLOG CRON SCHEDULER STARTED")
    logger.info("=" * 60)
    logger.info(f"📅 Schedule: 2x per day")
    logger.info(f"   - 08:00 EST: Generate {BLOG_COUNT_PER_RUN} blogs")
    logger.info(f"   - 16:00 EST: Generate {BLOG_COUNT_PER_RUN} blogs")
    logger.info(f"📝 Total: {BLOG_COUNT_PER_RUN * 2} blogs/day")
    logger.info("=" * 60)
    
    return scheduler


async def main():
    """Point d'entrée principal."""
    scheduler = start_scheduler()
    
    # Garder le scheduler actif
    try:
        while True:
            await asyncio.sleep(3600)  # Check every hour
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logger.info("Scheduler stopped")


if __name__ == "__main__":
    # Pour tester manuellement
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        logger.info("🧪 Running test generation...")
        asyncio.run(generate_blogs())
    else:
        asyncio.run(main())
