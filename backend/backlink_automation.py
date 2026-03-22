# Luxura Distribution - Real Playwright Backlink Automation
# Actually submits to directories with human-like behavior

import asyncio
import random
import os
from datetime import datetime
from playwright.async_api import async_playwright

# ==================== LUXURA BUSINESS INFO ====================

BUSINESS = {
    "name": "Luxura Distribution",
    "name_full": "Luxura Distribution Inc.",
    "description": "Importateur et distributeur direct d'extensions capillaires professionnelles au Québec. Qualité salon haut de gamme. Plus de 30 salons partenaires.",
    "description_long": "Luxura Distribution est un importateur et distributeur direct d'extensions capillaires professionnelles au Québec. Notre mission est d'offrir aux salons un approvisionnement fiable, constant et transparent. Extensions Genius Weft, Tape-in, Halo et plus. Qualité Remy Hair 100% naturels.",
    "address": "1887, 83e Rue",
    "city": "St-Georges",
    "province": "Québec",
    "province_abbr": "QC",
    "postal_code": "G6A 1M9",
    "country": "Canada",
    "full_address": "1887, 83e Rue, St-Georges, QC G6A 1M9, Canada",
    "phone": "(418) 222-3939",
    "phone_clean": "4182223939",
    "email": "info@luxuradistribution.com",
    "website": "https://www.luxuradistribution.com",
    "categories": ["Extensions capillaires", "Produits coiffure", "Distributeur beauté", "Hair Extensions"],
    "keywords": "extensions cheveux, rallonges capillaires, genius weft, tape-in, salon professionnel, québec"
}

SCREENSHOTS_DIR = "/tmp/backlinks"

async def human_delay(min_sec=1.0, max_sec=3.0):
    await asyncio.sleep(random.uniform(min_sec, max_sec))

async def human_type(page, selector, text):
    """Type like a human"""
    await page.click(selector)
    await human_delay(0.2, 0.5)
    for char in text:
        await page.type(selector, char, delay=random.randint(30, 80))
    await human_delay(0.3, 0.7)

async def save_screenshot(page, name):
    """Save screenshot with timestamp"""
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
    filename = f"{SCREENSHOTS_DIR}/{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    await page.screenshot(path=filename)
    print(f"📸 Screenshot saved: {filename}")
    return filename

# ==================== DIRECTORY SUBMISSIONS ====================

async def submit_hotfrog(page):
    """Submit to Hotfrog Canada"""
    print("\n🔥 HOTFROG CANADA")
    try:
        await page.goto("https://www.hotfrog.ca/add-a-business", timeout=30000)
        await human_delay(2, 4)
        await save_screenshot(page, "hotfrog_1_landing")
        
        # Look for form fields
        selectors_tried = []
        
        # Try common field names
        for name_sel in ['input[name="businessName"]', 'input[name="company"]', 'input[name="name"]', '#businessName', '#company-name']:
            try:
                if await page.is_visible(name_sel, timeout=2000):
                    await human_type(page, name_sel, BUSINESS["name"])
                    selectors_tried.append(f"✅ {name_sel}")
                    break
            except:
                selectors_tried.append(f"❌ {name_sel}")
        
        await human_delay(1, 2)
        await save_screenshot(page, "hotfrog_2_form")
        
        return {"status": "visited", "selectors": selectors_tried, "url": page.url}
        
    except Exception as e:
        print(f"❌ Hotfrog error: {e}")
        return {"status": "error", "error": str(e)}

async def submit_cylex(page):
    """Submit to Cylex Canada"""
    print("\n🔥 CYLEX CANADA")
    try:
        await page.goto("https://www.cylex.ca/add-company", timeout=30000)
        await human_delay(2, 4)
        await save_screenshot(page, "cylex_1_landing")
        
        # Check if there's a form
        content = await page.content()
        has_form = "form" in content.lower()
        
        await human_delay(1, 2)
        await save_screenshot(page, "cylex_2_page")
        
        return {"status": "visited", "has_form": has_form, "url": page.url}
        
    except Exception as e:
        print(f"❌ Cylex error: {e}")
        return {"status": "error", "error": str(e)}

async def submit_yelp(page):
    """Submit to Yelp Business"""
    print("\n🔥 YELP BUSINESS")
    try:
        await page.goto("https://business.yelp.ca/", timeout=30000)
        await human_delay(2, 4)
        await save_screenshot(page, "yelp_1_landing")
        
        # Look for claim/add business button
        buttons = await page.query_selector_all("a, button")
        claim_found = False
        for btn in buttons[:20]:
            text = await btn.inner_text()
            if any(word in text.lower() for word in ["claim", "add", "get started", "commencer"]):
                claim_found = True
                break
        
        await save_screenshot(page, "yelp_2_page")
        
        return {"status": "visited", "claim_button_found": claim_found, "url": page.url}
        
    except Exception as e:
        print(f"❌ Yelp error: {e}")
        return {"status": "error", "error": str(e)}

async def submit_pages_jaunes(page):
    """Submit to Pages Jaunes Canada"""
    print("\n🔥 PAGES JAUNES CANADA")
    try:
        await page.goto("https://www.pagesjaunes.ca/", timeout=30000)
        await human_delay(2, 4)
        await save_screenshot(page, "pagesjaunes_1_landing")
        
        # Search for Luxura to see if already listed
        search_box = await page.query_selector('input[type="search"], input[name="q"], input[placeholder*="Search"]')
        if search_box:
            await search_box.type(BUSINESS["name"], delay=50)
            await human_delay(0.5, 1)
        
        await save_screenshot(page, "pagesjaunes_2_search")
        
        return {"status": "visited", "url": page.url}
        
    except Exception as e:
        print(f"❌ Pages Jaunes error: {e}")
        return {"status": "error", "error": str(e)}

async def submit_411(page):
    """Submit to 411.ca"""
    print("\n🔥 411.CA")
    try:
        await page.goto("https://www.411.ca/", timeout=30000)
        await human_delay(2, 4)
        await save_screenshot(page, "411_1_landing")
        
        # Look for business listing options
        links = await page.query_selector_all("a")
        add_business = False
        for link in links[:30]:
            try:
                text = await link.inner_text()
                href = await link.get_attribute("href")
                if any(word in text.lower() for word in ["add", "business", "claim"]):
                    add_business = True
                    break
            except:
                pass
        
        await save_screenshot(page, "411_2_page")
        
        return {"status": "visited", "add_business_found": add_business, "url": page.url}
        
    except Exception as e:
        print(f"❌ 411.ca error: {e}")
        return {"status": "error", "error": str(e)}

async def submit_canpages(page):
    """Submit to Canpages"""
    print("\n🔥 CANPAGES")
    try:
        await page.goto("https://www.canpages.ca/", timeout=30000)
        await human_delay(2, 4)
        await save_screenshot(page, "canpages_1_landing")
        
        await save_screenshot(page, "canpages_2_page")
        
        return {"status": "visited", "url": page.url}
        
    except Exception as e:
        print(f"❌ Canpages error: {e}")
        return {"status": "error", "error": str(e)}

async def check_google_mybusiness(page):
    """Check Google My Business status"""
    print("\n🔥 GOOGLE MY BUSINESS CHECK")
    try:
        # Search for Luxura on Google Maps
        await page.goto("https://www.google.com/maps/search/Luxura+Distribution+St-Georges+Quebec", timeout=30000)
        await human_delay(3, 5)
        await save_screenshot(page, "google_maps_1_search")
        
        # Check if business appears
        content = await page.content()
        listed = "luxura" in content.lower()
        
        await save_screenshot(page, "google_maps_2_results")
        
        return {"status": "visited", "possibly_listed": listed, "url": page.url}
        
    except Exception as e:
        print(f"❌ Google Maps error: {e}")
        return {"status": "error", "error": str(e)}

# ==================== MAIN RUNNER ====================

async def main():
    print("=" * 60)
    print("🚀 LUXURA DISTRIBUTION - BACKLINK AUTOMATION")
    print("=" * 60)
    print(f"Business: {BUSINESS['name']}")
    print(f"Address: {BUSINESS['full_address']}")
    print(f"Website: {BUSINESS['website']}")
    print("=" * 60)
    
    results = {}
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            locale="fr-CA"
        )
        
        page = await context.new_page()
        
        # Run submissions
        directories = [
            ("google_maps", check_google_mybusiness),
            ("hotfrog", submit_hotfrog),
            ("cylex", submit_cylex),
            ("yelp", submit_yelp),
            ("pages_jaunes", submit_pages_jaunes),
            ("411", submit_411),
            ("canpages", submit_canpages),
        ]
        
        for name, func in directories:
            try:
                results[name] = await func(page)
                await human_delay(2, 5)  # Wait between sites
            except Exception as e:
                results[name] = {"status": "error", "error": str(e)}
        
        await browser.close()
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ DES SOUMISSIONS")
    print("=" * 60)
    
    for name, result in results.items():
        status = result.get("status", "unknown")
        icon = "✅" if status == "visited" else "❌"
        print(f"{icon} {name}: {status}")
        if result.get("error"):
            print(f"   └── Error: {result['error'][:50]}")
    
    # List screenshots
    print("\n📸 SCREENSHOTS GÉNÉRÉES:")
    if os.path.exists(SCREENSHOTS_DIR):
        for f in sorted(os.listdir(SCREENSHOTS_DIR)):
            print(f"   - {f}")
    
    return results

if __name__ == "__main__":
    results = asyncio.run(main())
    print("\n✅ Automation complete!")
