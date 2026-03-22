# Luxura Distribution - Automated Backlink Creation System
# Uses Playwright to submit business info to legitimate directories

import asyncio
import random
from datetime import datetime
from playwright.async_api import async_playwright
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== LUXURA BUSINESS INFO ====================

LUXURA_BUSINESS = {
    "company_name": "Luxura Distribution",
    "company_name_full": "Luxura Distribution Inc.",
    "description_short": "Importateur et distributeur d'extensions capillaires professionnelles au Québec",
    "description_long": """Luxura Distribution est un importateur et distributeur direct d'extensions capillaires professionnelles au Québec. Notre mission est d'offrir aux salons un approvisionnement fiable, constant et transparent. Nous sélectionnons nos fournisseurs avec rigueur afin d'assurer une qualité stable, une provenance contrôlée et une performance durable. Chaque mèche est issue d'un processus structuré où la traçabilité et la constance priment. En travaillant directement avec un importateur établi au Québec, les salons partenaires bénéficient d'un inventaire réel, d'une disponibilité immédiate et d'une relation directe sans intermédiaire.""",
    
    # Siège Social
    "address": "1887, 83e Rue",
    "city": "St-Georges",
    "province": "Québec",
    "postal_code": "G6A 1M9",
    "country": "Canada",
    "full_address": "1887, 83e Rue, St-Georges, Québec, Canada G6A 1M9",
    
    # Contact
    "phone": "(418) 222-3939",
    "phone_clean": "4182223939",
    "email": "info@luxuradistribution.com",
    "website": "https://www.luxuradistribution.com",
    
    # Showroom Partner
    "showroom_name": "Salon Carouso",
    "showroom_website": "https://www.saloncarouso.com",
    
    # Social Media
    "instagram": "https://www.instagram.com/luxura_distribution/",
    "facebook": "https://m.me/1838415193042352",
    
    # Categories & Keywords
    "categories": [
        "Extensions capillaires",
        "Produits de coiffure",
        "Distributeur beauté",
        "Grossiste cheveux",
        "Fournisseur salon",
        "Hair Extensions",
        "Beauty Supplies"
    ],
    "keywords": [
        "extensions cheveux québec",
        "extensions capillaires professionnelles",
        "genius weft quebec",
        "tape-in extensions canada",
        "fournisseur extensions salon",
        "grossiste extensions cheveux"
    ],
    
    # Business Info
    "business_type": "Distributeur / Importateur",
    "year_founded": "2023",
    "employees": "1-10",
    "payment_methods": ["Visa", "Mastercard", "Virement bancaire"],
    "languages": ["Français", "English"],
    "hours": "Lundi-Vendredi: 9h-17h"
}

# ==================== TARGET DIRECTORIES ====================

DIRECTORIES = [
    {
        "name": "Pages Jaunes Canada",
        "url": "https://www.pagesjaunes.ca/inscription",
        "priority": "HIGH",
        "type": "business_directory",
        "status": "pending"
    },
    {
        "name": "411.ca",
        "url": "https://www.411.ca/business/add",
        "priority": "HIGH",
        "type": "business_directory",
        "status": "pending"
    },
    {
        "name": "Yelp Canada",
        "url": "https://biz.yelp.ca/signup_business/new",
        "priority": "HIGH",
        "type": "reviews",
        "status": "pending"
    },
    {
        "name": "Canpages",
        "url": "https://www.canpages.ca",
        "priority": "MEDIUM",
        "type": "business_directory",
        "status": "pending"
    },
    {
        "name": "Hotfrog Canada",
        "url": "https://www.hotfrog.ca/add-a-business",
        "priority": "MEDIUM",
        "type": "business_directory",
        "status": "pending"
    },
    {
        "name": "Cylex Canada",
        "url": "https://www.cylex.ca/add-company",
        "priority": "MEDIUM",
        "type": "business_directory",
        "status": "pending"
    },
    {
        "name": "iGlobal.co",
        "url": "https://ca.iglobal.co/register",
        "priority": "LOW",
        "type": "business_directory",
        "status": "pending"
    },
    {
        "name": "IndexBeauté.ca",
        "url": "https://indexbeaute.ca/inscription",
        "priority": "HIGH",
        "type": "industry",
        "status": "pending"
    }
]

# ==================== HUMAN-LIKE BEHAVIORS ====================

async def human_delay(min_seconds=1, max_seconds=3):
    """Random delay to simulate human behavior"""
    delay = random.uniform(min_seconds, max_seconds)
    await asyncio.sleep(delay)

async def human_type(page, selector, text, delay_per_char=0.05):
    """Type like a human with variable speed"""
    await page.click(selector)
    await human_delay(0.3, 0.7)
    for char in text:
        await page.type(selector, char, delay=random.uniform(delay_per_char * 0.5, delay_per_char * 1.5))
    await human_delay(0.2, 0.5)

async def human_scroll(page, amount=300):
    """Scroll like a human"""
    await page.mouse.wheel(0, amount)
    await human_delay(0.5, 1.5)

# ==================== DIRECTORY SUBMISSION FUNCTIONS ====================

async def submit_to_hotfrog(page, business):
    """Submit business to Hotfrog Canada"""
    try:
        await page.goto("https://www.hotfrog.ca/add-a-business")
        await human_delay(2, 4)
        
        # Fill business name
        if await page.is_visible('input[name="businessName"]'):
            await human_type(page, 'input[name="businessName"]', business["company_name"])
        
        # Fill address
        if await page.is_visible('input[name="address"]'):
            await human_type(page, 'input[name="address"]', business["full_address"])
        
        # Fill phone
        if await page.is_visible('input[name="phone"]'):
            await human_type(page, 'input[name="phone"]', business["phone"])
        
        # Fill website
        if await page.is_visible('input[name="website"]'):
            await human_type(page, 'input[name="website"]', business["website"])
        
        # Fill email
        if await page.is_visible('input[name="email"]'):
            await human_type(page, 'input[name="email"]', business["email"])
        
        # Fill description
        if await page.is_visible('textarea[name="description"]'):
            await human_type(page, 'textarea[name="description"]', business["description_short"])
        
        await human_delay(1, 2)
        
        # Take screenshot before submit
        await page.screenshot(path=f"/tmp/backlink_hotfrog_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        
        return {"status": "form_filled", "message": "Form filled, ready for manual captcha/submit"}
        
    except Exception as e:
        logger.error(f"Hotfrog submission error: {e}")
        return {"status": "error", "message": str(e)}

async def submit_to_cylex(page, business):
    """Submit business to Cylex Canada"""
    try:
        await page.goto("https://www.cylex.ca/add-company")
        await human_delay(2, 4)
        
        # Fill company name
        if await page.is_visible('input#company_name'):
            await human_type(page, 'input#company_name', business["company_name"])
        
        # Fill street
        if await page.is_visible('input#street'):
            await human_type(page, 'input#street', business["address"])
        
        # Fill city
        if await page.is_visible('input#city'):
            await human_type(page, 'input#city', business["city"])
        
        # Fill postal code
        if await page.is_visible('input#zip'):
            await human_type(page, 'input#zip', business["postal_code"])
        
        # Fill phone
        if await page.is_visible('input#phone'):
            await human_type(page, 'input#phone', business["phone"])
        
        # Fill website
        if await page.is_visible('input#website'):
            await human_type(page, 'input#website', business["website"])
        
        # Fill email
        if await page.is_visible('input#email'):
            await human_type(page, 'input#email', business["email"])
        
        await human_delay(1, 2)
        
        # Take screenshot
        await page.screenshot(path=f"/tmp/backlink_cylex_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        
        return {"status": "form_filled", "message": "Form filled, ready for manual verification"}
        
    except Exception as e:
        logger.error(f"Cylex submission error: {e}")
        return {"status": "error", "message": str(e)}

async def create_pinterest_pins(page, business, products):
    """Create Pinterest pins with backlinks to products"""
    try:
        # Note: Pinterest requires login
        # This is a template for creating product pins
        
        pin_templates = [
            {
                "title": f"Extensions Genius Weft - {business['company_name']}",
                "description": f"Extensions cheveux trame invisible professionnelles. Qualité salon haut de gamme. {business['website']}",
                "link": f"{business['website']}/category/all-products"
            },
            {
                "title": "Rallonges capillaires naturelles Québec",
                "description": f"Extensions cheveux 100% naturels Remy Hair. Livraison rapide au Québec. {business['website']}",
                "link": f"{business['website']}/category/all-products"
            },
            {
                "title": "Extensions cheveux balayage blond",
                "description": f"Extensions balayage blond naturel. Volume et longueur instantanés. {business['website']}",
                "link": f"{business['website']}/category/all-products"
            }
        ]
        
        return {
            "status": "templates_ready",
            "pins": pin_templates,
            "message": "Pinterest requires manual login. Use these templates to create pins."
        }
        
    except Exception as e:
        logger.error(f"Pinterest error: {e}")
        return {"status": "error", "message": str(e)}

# ==================== MAIN RUNNER ====================

async def run_backlink_automation(target_directories=None):
    """Run the backlink automation for specified directories"""
    
    results = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        # Filter directories if specified
        dirs_to_process = target_directories or DIRECTORIES
        
        for directory in dirs_to_process:
            logger.info(f"Processing: {directory['name']}")
            
            try:
                if directory["name"] == "Hotfrog Canada":
                    result = await submit_to_hotfrog(page, LUXURA_BUSINESS)
                elif directory["name"] == "Cylex Canada":
                    result = await submit_to_cylex(page, LUXURA_BUSINESS)
                else:
                    # Generic visit and screenshot
                    await page.goto(directory["url"])
                    await human_delay(2, 4)
                    screenshot_path = f"/tmp/backlink_{directory['name'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    await page.screenshot(path=screenshot_path)
                    result = {
                        "status": "visited",
                        "screenshot": screenshot_path,
                        "message": f"Page visited. Manual submission required at {directory['url']}"
                    }
                
                results.append({
                    "directory": directory["name"],
                    "url": directory["url"],
                    "priority": directory["priority"],
                    **result
                })
                
            except Exception as e:
                results.append({
                    "directory": directory["name"],
                    "url": directory["url"],
                    "status": "error",
                    "message": str(e)
                })
            
            # Random delay between directories
            await human_delay(3, 7)
        
        await browser.close()
    
    return results

def get_business_info():
    """Return business info for manual submissions"""
    return LUXURA_BUSINESS

def get_directories_list():
    """Return list of target directories"""
    return DIRECTORIES

# ==================== API INTEGRATION ====================

if __name__ == "__main__":
    # Test run
    results = asyncio.run(run_backlink_automation())
    for r in results:
        print(f"{r['directory']}: {r['status']} - {r.get('message', '')}")
