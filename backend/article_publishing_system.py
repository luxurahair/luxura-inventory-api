# Luxura Distribution - Article Publishing System for Quality Backlinks
# Publishes SEO articles on high-authority platforms

import asyncio
import os
import random
from datetime import datetime
from playwright.async_api import async_playwright
from dotenv import load_dotenv

load_dotenv("/app/backend/.env")

BUSINESS = {
    "name": "Luxura Distribution",
    "website": "https://www.luxuradistribution.com",
    "email": os.getenv("LUXURA_EMAIL", "info@luxuradistribution.com"),
    "description": "Premier importer and distributor of professional hair extensions in Quebec, Canada.",
    "author_bio": "Luxura Distribution is Quebec's leading importer of professional hair extensions. Specializing in Genius Weft, Tape-in, and Halo extensions, we partner with over 30 salons across Canada. Visit luxuradistribution.com for premium quality extensions.",
    "author_bio_fr": "Luxura Distribution est le leader québécois des extensions capillaires professionnelles. Spécialisés en Genius Weft, Tape-in et Halo, nous accompagnons plus de 30 salons partenaires au Canada. Visitez luxuradistribution.com pour des extensions de qualité premium."
}

SCREENSHOTS_DIR = "/tmp/backlinks/articles"
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

# ==================== ARTICLE PUBLISHING PLATFORMS ====================

# HIGH QUALITY PLATFORMS - Require quality articles
ARTICLE_PLATFORMS = {
    "high_authority": [
        {
            "name": "Medium",
            "url": "https://medium.com/new-story",
            "type": "blog_platform",
            "da": 95,
            "link_type": "nofollow (but high visibility)",
            "requirements": "Account required, original content",
            "best_for": "Brand awareness, social proof"
        },
        {
            "name": "LinkedIn Articles",
            "url": "https://www.linkedin.com/pulse/",
            "type": "professional",
            "da": 98,
            "link_type": "nofollow (but B2B visibility)",
            "requirements": "LinkedIn account",
            "best_for": "B2B salon partnerships"
        },
    ],
    "beauty_industry": [
        {
            "name": "Beauty Wire Magazine",
            "url": "https://beautywiremagazine.com/submit-an-article/",
            "type": "guest_post",
            "da": 40,
            "link_type": "dofollow",
            "requirements": "Submit via form, original content",
            "best_for": "Beauty industry exposure"
        },
        {
            "name": "Ask Us Beauty Magazine",
            "url": "https://www.askusbeautymagazine.com/submissions",
            "type": "guest_post",
            "da": 35,
            "link_type": "dofollow",
            "requirements": "500 words, $20 editorial fee, $5 per link",
            "best_for": "Targeted beauty audience"
        },
        {
            "name": "Salon Magazine Canada",
            "url": "https://www.salonmagazine.ca/",
            "type": "industry_news",
            "da": 49,
            "link_type": "dofollow",
            "requirements": "Contact editor, industry news angle",
            "best_for": "Canadian salon industry"
        },
    ],
    "canadian_directories": [
        {
            "name": "Canada Business Directory",
            "url": "https://www.canadianbusinessdirectory.ca/",
            "type": "directory",
            "da": 25,
            "link_type": "dofollow",
            "requirements": "Business listing"
        },
        {
            "name": "Canadian Company Capabilities",
            "url": "https://www.ic.gc.ca/eic/site/ccc-rec.nsf/eng/home",
            "type": "government_directory",
            "da": 80,
            "link_type": "dofollow",
            "requirements": "Canadian business registration"
        },
    ],
    "free_article_sites": [
        {
            "name": "EzineArticles",
            "url": "https://ezinearticles.com/",
            "type": "article_directory",
            "da": 70,
            "link_type": "dofollow in author bio",
            "requirements": "Original content, account creation"
        },
        {
            "name": "HubPages",
            "url": "https://hubpages.com/",
            "type": "content_platform",
            "da": 80,
            "link_type": "nofollow (high traffic)",
            "requirements": "Account, quality content"
        },
        {
            "name": "Blogger (Google)",
            "url": "https://www.blogger.com/",
            "type": "blog_platform",
            "da": 95,
            "link_type": "dofollow",
            "requirements": "Google account, create own blog"
        },
    ],
    "press_release": [
        {
            "name": "PRLog",
            "url": "https://www.prlog.org/",
            "type": "press_release",
            "da": 70,
            "link_type": "dofollow",
            "requirements": "Free basic, newsworthy content"
        },
        {
            "name": "OpenPR",
            "url": "https://www.openpr.com/",
            "type": "press_release",
            "da": 65,
            "link_type": "dofollow",
            "requirements": "Free, press release format"
        },
        {
            "name": "1888 Press Release",
            "url": "https://www.1888pressrelease.com/",
            "type": "press_release",
            "da": 60,
            "link_type": "dofollow",
            "requirements": "Free basic tier"
        },
    ],
    "qa_platforms": [
        {
            "name": "Quora",
            "url": "https://www.quora.com/",
            "type": "q_and_a",
            "da": 93,
            "link_type": "nofollow (but high visibility)",
            "requirements": "Answer questions in your niche",
            "best_for": "Authority building, traffic"
        },
        {
            "name": "Reddit r/HairExtensions",
            "url": "https://www.reddit.com/r/HairExtensions/",
            "type": "community",
            "da": 98,
            "link_type": "nofollow",
            "requirements": "Helpful contributions, not spam",
            "best_for": "Community engagement"
        },
    ]
}

# ==================== SAMPLE ARTICLES FOR PUBLISHING ====================

ARTICLES = [
    {
        "title": "Professional Hair Extensions in Quebec: A Complete Guide for Salons",
        "title_fr": "Extensions capillaires professionnelles au Québec : Guide complet pour les salons",
        "excerpt": "Discover how Quebec salons are transforming their business with premium hair extensions. Learn about Genius Weft, Tape-in, and Halo extensions.",
        "content": """
# Professional Hair Extensions in Quebec: A Complete Guide for Salons

The hair extension industry in Quebec has experienced remarkable growth over the past few years. More and more women are seeking natural-looking, long-lasting solutions for added volume and length.

## Why Genius Weft Extensions Are Leading the Market

Genius Weft extensions represent a revolutionary advancement in hair extension technology. Unlike traditional wefts, Genius Weft features:

- **Ultra-thin weft base** - Lies completely flat against the scalp
- **No shedding** - Superior hand-tied construction
- **Reusable** - Can be reinstalled multiple times
- **Invisible blend** - Perfect for fine hair

## Choosing the Right Extension Method

### Tape-in Extensions
Perfect for clients seeking a semi-permanent solution. These extensions last 6-8 weeks between adjustments and are ideal for adding volume throughout the hair.

### Halo Extensions
A no-damage solution for clients who want instant transformation without commitment. The invisible wire sits comfortably on the crown.

### I-Tip/Fusion Extensions
The most permanent option, lasting 4-6 months. Ideal for clients wanting maximum styling flexibility.

## Partner with a Professional Distributor

Working with an established distributor ensures consistent quality and reliable supply. Look for:

- 100% Remy human hair products
- Multiple color and length options
- Professional training and support
- Competitive wholesale pricing

*For salon partnerships and wholesale inquiries, visit [Luxura Distribution](https://www.luxuradistribution.com) - Quebec's premier hair extension importer.*
        """,
        "tags": ["hair extensions", "Quebec", "salon business", "Genius Weft", "professional hair"],
        "category": "beauty_industry"
    },
    {
        "title": "5 Hair Extension Trends Dominating Quebec Salons in 2025",
        "excerpt": "From balayage blends to invisible wefts, discover the hottest hair extension trends transforming Quebec's beauty scene.",
        "content": """
# 5 Hair Extension Trends Dominating Quebec Salons in 2025

Quebec's salon industry is embracing innovative hair extension techniques that deliver stunning, natural results. Here are the top trends:

## 1. Balayage Extensions
Pre-colored extensions that perfectly match balayage and ombre hairstyles. No more mismatched colors!

## 2. Invisible Genius Weft
The ultra-thin weft technology has made extensions virtually undetectable, even in thin or fine hair.

## 3. Volume-Only Applications
Many clients now choose extensions purely for volume, not length - creating fuller, more luxurious looks.

## 4. Low-Maintenance Halo Extensions
The rise of DIY-friendly halo extensions for special occasions and everyday glamour.

## 5. Sustainable Hair Sourcing
Ethically sourced, 100% Remy human hair is now the standard for premium salons.

## The Business Opportunity

Salons adding extension services see an average 40% increase in client spending. The key is partnering with a reliable supplier who offers:

- Consistent quality
- Fast delivery
- Professional training
- Competitive pricing

*Quebec salons trust [Luxura Distribution](https://www.luxuradistribution.com) for premium hair extensions and expert support.*
        """,
        "tags": ["hair trends 2025", "Quebec beauty", "salon trends", "hair extensions"],
        "category": "beauty_industry"
    },
    {
        "title": "PRESS RELEASE: Luxura Distribution Expands Partnership Program for Quebec Salons",
        "type": "press_release",
        "content": """
FOR IMMEDIATE RELEASE

**Luxura Distribution Expands Partnership Program for Quebec Salons**

ST-GEORGES, QUEBEC - Luxura Distribution, Quebec's leading importer of professional hair extensions, announces the expansion of its salon partnership program.

**What's New:**
- Dedicated account managers for partner salons
- Free professional training workshops
- Exclusive access to new products
- Preferred wholesale pricing

**About the Program:**
"Our goal is to help Quebec salons build thriving extension services," says the Luxura Distribution team. "We provide everything from premium products to hands-on training."

**Products Available:**
- Genius Weft extensions (60+ colors)
- Tape-in extensions
- Halo extensions
- I-Tip/Fusion extensions

**Contact:**
Luxura Distribution
1887, 83e Rue, St-Georges, QC G6A 1M9
Phone: (418) 222-3939
Email: info@luxuradistribution.com
Website: https://www.luxuradistribution.com

###
        """,
        "tags": ["press release", "hair extensions", "Quebec business", "salon partnership"],
        "category": "press_release"
    }
]

# ==================== PLATFORM SUBMISSION FUNCTIONS ====================

async def human_delay(min_sec=1.0, max_sec=3.0):
    await asyncio.sleep(random.uniform(min_sec, max_sec))

async def save_screenshot(page, name):
    filename = f"{SCREENSHOTS_DIR}/{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    try:
        await page.screenshot(path=filename, full_page=False)
        print(f"📸 {filename}")
    except:
        pass
    return filename

async def visit_platform(page, platform):
    """Visit a platform and take screenshots"""
    print(f"\n🌐 Visiting: {platform['name']}")
    try:
        await page.goto(platform['url'], timeout=30000)
        await human_delay(2, 4)
        await save_screenshot(page, f"platform_{platform['name'].lower().replace(' ', '_')}")
        
        return {
            "name": platform['name'],
            "url": platform['url'],
            "da": platform.get('da'),
            "link_type": platform.get('link_type'),
            "status": "visited",
            "requirements": platform.get('requirements')
        }
    except Exception as e:
        return {
            "name": platform['name'],
            "status": "error",
            "error": str(e)[:50]
        }

async def explore_all_platforms():
    """Visit all article publishing platforms"""
    print("=" * 70)
    print("📝 LUXURA - ARTICLE PUBLISHING PLATFORMS EXPLORER")
    print("=" * 70)
    
    results = {
        "high_authority": [],
        "beauty_industry": [],
        "free_sites": [],
        "press_release": [],
        "qa_platforms": []
    }
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--no-sandbox'])
        context = await browser.new_context(viewport={"width": 1920, "height": 1080})
        page = await context.new_page()
        
        # Visit high authority platforms
        print("\n" + "=" * 50)
        print("🏆 HIGH AUTHORITY PLATFORMS")
        print("=" * 50)
        for platform in ARTICLE_PLATFORMS["high_authority"]:
            result = await visit_platform(page, platform)
            results["high_authority"].append(result)
            await human_delay(2, 4)
        
        # Visit beauty industry platforms
        print("\n" + "=" * 50)
        print("💄 BEAUTY INDUSTRY PLATFORMS")
        print("=" * 50)
        for platform in ARTICLE_PLATFORMS["beauty_industry"]:
            result = await visit_platform(page, platform)
            results["beauty_industry"].append(result)
            await human_delay(2, 4)
        
        # Visit free article sites
        print("\n" + "=" * 50)
        print("📰 FREE ARTICLE SITES")
        print("=" * 50)
        for platform in ARTICLE_PLATFORMS["free_article_sites"]:
            result = await visit_platform(page, platform)
            results["free_sites"].append(result)
            await human_delay(2, 4)
        
        # Visit press release sites
        print("\n" + "=" * 50)
        print("📢 PRESS RELEASE PLATFORMS")
        print("=" * 50)
        for platform in ARTICLE_PLATFORMS["press_release"]:
            result = await visit_platform(page, platform)
            results["press_release"].append(result)
            await human_delay(2, 4)
        
        await browser.close()
    
    return results

def get_article_content(article_type="general"):
    """Get article content for publishing"""
    for article in ARTICLES:
        if article.get("category") == article_type or article.get("type") == article_type:
            return article
    return ARTICLES[0]

def get_all_platforms():
    """Get all available platforms with details"""
    return ARTICLE_PLATFORMS

def print_platform_summary():
    """Print summary of all platforms"""
    print("\n" + "=" * 70)
    print("📋 ARTICLE PUBLISHING PLATFORMS SUMMARY")
    print("=" * 70)
    
    total_platforms = 0
    
    for category, platforms in ARTICLE_PLATFORMS.items():
        print(f"\n📁 {category.upper().replace('_', ' ')}")
        print("-" * 40)
        for p in platforms:
            da = p.get('da', '?')
            link = p.get('link_type', 'unknown')
            print(f"   • {p['name']:25} DA:{da:3} | {link}")
            total_platforms += 1
    
    print("\n" + "=" * 70)
    print(f"   TOTAL: {total_platforms} platforms identified")
    print("=" * 70)

# ==================== MAIN ====================

if __name__ == "__main__":
    print_platform_summary()
    
    print("\n\n🚀 Exploring platforms...")
    results = asyncio.run(explore_all_platforms())
    
    print("\n" + "=" * 70)
    print("📊 EXPLORATION RESULTS")
    print("=" * 70)
    
    for category, platforms in results.items():
        print(f"\n{category.upper()}:")
        for p in platforms:
            status = p.get('status', 'unknown')
            icon = "✅" if status == "visited" else "❌"
            print(f"   {icon} {p['name']}: {status}")
