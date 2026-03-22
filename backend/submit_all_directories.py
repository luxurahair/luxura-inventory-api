# Luxura Distribution - COMPLETE Directory Submission
# Submits to ALL directories, not just Hotfrog and Cylex

import asyncio
import random
import os
from datetime import datetime
from playwright.async_api import async_playwright
from dotenv import load_dotenv

load_dotenv("/app/backend/.env")

BUSINESS = {
    "name": "Luxura Distribution",
    "description": "Importateur et distributeur direct d'extensions capillaires professionnelles au Québec. Qualité salon haut de gamme.",
    "description_long": "Luxura Distribution est le leader québécois des extensions capillaires professionnelles. Nous offrons des extensions Genius Weft, Tape-in, Halo et I-Tip de qualité supérieure. Plus de 30 salons partenaires au Québec. Livraison rapide partout au Canada.",
    "address": "1887, 83e Rue",
    "city": "St-Georges",
    "province": "Québec",
    "province_short": "QC",
    "postal_code": "G6A 1M9",
    "country": "Canada",
    "full_address": "1887, 83e Rue, St-Georges, QC G6A 1M9, Canada",
    "phone": "(418) 222-3939",
    "phone_clean": "4182223939",
    "email": os.getenv("LUXURA_EMAIL", "info@luxuradistribution.com"),
    "website": "https://www.luxuradistribution.com",
    "categories": ["Hair Extensions", "Beauty Supplies", "Salon Supplies", "Extensions capillaires"],
}

SCREENSHOTS_DIR = "/tmp/backlinks"
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

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

async def safe_fill(page, selector, text, timeout=3000):
    try:
        elem = await page.wait_for_selector(selector, timeout=timeout)
        if elem:
            await elem.click()
            await elem.fill(text)
            return True
    except:
        pass
    return False

async def safe_click(page, selector, timeout=3000):
    try:
        elem = await page.wait_for_selector(selector, timeout=timeout)
        if elem:
            await elem.click()
            return True
    except:
        pass
    return False

# ==================== DIRECTORY SUBMISSIONS ====================

async def submit_hotfrog(page):
    """Submit to Hotfrog Canada"""
    print("\n🔥 HOTFROG CANADA")
    try:
        await page.goto("https://www.hotfrog.ca/add-a-business", timeout=30000)
        await human_delay(2, 3)
        await save_screenshot(page, "dir_hotfrog_1")
        
        filled = 0
        for sel in ['input[name="businessName"]', '#businessName', 'input[placeholder*="business"]', 'input[placeholder*="Business"]']:
            if await safe_fill(page, sel, BUSINESS["name"]):
                filled += 1
                break
        
        for sel in ['input[name="phone"]', '#phone', 'input[type="tel"]']:
            if await safe_fill(page, sel, BUSINESS["phone"]):
                filled += 1
                break
        
        for sel in ['input[name="email"]', '#email', 'input[type="email"]']:
            if await safe_fill(page, sel, BUSINESS["email"]):
                filled += 1
                break
                
        for sel in ['input[name="website"]', '#website', 'input[type="url"]']:
            if await safe_fill(page, sel, BUSINESS["website"]):
                filled += 1
                break
        
        for sel in ['input[name="address"]', '#address', 'input[placeholder*="address"]']:
            if await safe_fill(page, sel, BUSINESS["full_address"]):
                filled += 1
                break
        
        for sel in ['textarea[name="description"]', '#description', 'textarea']:
            if await safe_fill(page, sel, BUSINESS["description"]):
                filled += 1
                break
        
        await save_screenshot(page, "dir_hotfrog_2")
        
        # Try submit
        submitted = await safe_click(page, 'button[type="submit"], input[type="submit"], .btn-submit')
        if submitted:
            await human_delay(3, 5)
            await save_screenshot(page, "dir_hotfrog_3")
        
        return {"name": "Hotfrog", "status": "submitted" if submitted else "filled", "fields": filled}
    except Exception as e:
        return {"name": "Hotfrog", "status": "error", "error": str(e)[:50]}

async def submit_cylex(page):
    """Submit to Cylex Canada"""
    print("\n🔥 CYLEX CANADA")
    try:
        await page.goto("https://www.cylex.ca/add-company", timeout=30000)
        await human_delay(2, 3)
        await save_screenshot(page, "dir_cylex_1")
        
        filled = 0
        if await safe_fill(page, '#company_name, input[name="company_name"], input[name="company"]', BUSINESS["name"]):
            filled += 1
        if await safe_fill(page, '#street, input[name="street"], input[name="address"]', BUSINESS["address"]):
            filled += 1
        if await safe_fill(page, '#city, input[name="city"]', BUSINESS["city"]):
            filled += 1
        if await safe_fill(page, '#zip, input[name="zip"], input[name="postal"]', BUSINESS["postal_code"]):
            filled += 1
        if await safe_fill(page, '#phone, input[name="phone"]', BUSINESS["phone"]):
            filled += 1
        if await safe_fill(page, '#email, input[name="email"]', BUSINESS["email"]):
            filled += 1
        if await safe_fill(page, '#website, input[name="website"]', BUSINESS["website"]):
            filled += 1
        
        await save_screenshot(page, "dir_cylex_2")
        
        return {"name": "Cylex", "status": "filled", "fields": filled}
    except Exception as e:
        return {"name": "Cylex", "status": "error", "error": str(e)[:50]}

async def submit_yelp(page):
    """Submit to Yelp Business"""
    print("\n🔥 YELP CANADA")
    try:
        await page.goto("https://biz.yelp.ca/signup_business/new", timeout=30000)
        await human_delay(2, 4)
        await save_screenshot(page, "dir_yelp_1")
        
        # Yelp usually asks for business name first
        filled = 0
        for sel in ['input[name="biz_name"]', '#biz_name', 'input[placeholder*="business"]', 'input[aria-label*="business"]']:
            if await safe_fill(page, sel, BUSINESS["name"]):
                filled += 1
                break
        
        # Address
        for sel in ['input[name="address1"]', '#address1', 'input[placeholder*="address"]']:
            if await safe_fill(page, sel, BUSINESS["address"]):
                filled += 1
                break
        
        # City
        for sel in ['input[name="city"]', '#city']:
            if await safe_fill(page, sel, BUSINESS["city"]):
                filled += 1
                break
        
        # Province
        for sel in ['input[name="state"]', '#state', 'select[name="state"]']:
            if await safe_fill(page, sel, BUSINESS["province_short"]):
                filled += 1
                break
        
        # Postal
        for sel in ['input[name="zip"]', '#zip']:
            if await safe_fill(page, sel, BUSINESS["postal_code"]):
                filled += 1
                break
        
        # Phone
        for sel in ['input[name="phone"]', '#phone', 'input[type="tel"]']:
            if await safe_fill(page, sel, BUSINESS["phone_clean"]):
                filled += 1
                break
        
        await save_screenshot(page, "dir_yelp_2")
        
        return {"name": "Yelp", "status": "filled", "fields": filled, "note": "Yelp requires manual verification"}
    except Exception as e:
        return {"name": "Yelp", "status": "error", "error": str(e)[:50]}

async def submit_pagesjaunes(page):
    """Submit to Pages Jaunes Canada"""
    print("\n🔥 PAGES JAUNES CANADA")
    try:
        # Try to find the add business page
        await page.goto("https://www.pagesjaunes.ca/", timeout=30000)
        await human_delay(2, 3)
        await save_screenshot(page, "dir_pagesjaunes_1")
        
        # Search for add business link
        content = await page.content()
        
        # Try common URLs for adding business
        add_urls = [
            "https://www.pagesjaunes.ca/add-business",
            "https://www.pagesjaunes.ca/claim",
            "https://www.yellowpages.ca/add-business"
        ]
        
        for url in add_urls:
            try:
                await page.goto(url, timeout=10000)
                await human_delay(1, 2)
                current = page.url
                if "add" in current or "claim" in current or "business" in current:
                    await save_screenshot(page, "dir_pagesjaunes_2")
                    return {"name": "Pages Jaunes", "status": "found_add_page", "url": current}
            except:
                continue
        
        await save_screenshot(page, "dir_pagesjaunes_2")
        return {"name": "Pages Jaunes", "status": "visited", "note": "Need to find add business page manually"}
    except Exception as e:
        return {"name": "Pages Jaunes", "status": "error", "error": str(e)[:50]}

async def submit_411(page):
    """Submit to 411.ca"""
    print("\n🔥 411.CA")
    try:
        await page.goto("https://www.411.ca/", timeout=30000)
        await human_delay(2, 3)
        await save_screenshot(page, "dir_411_1")
        
        # First search for the business
        search_box = await page.query_selector('input[type="search"], input[name="q"], #what, input[placeholder*="Search"]')
        if search_box:
            await search_box.fill(BUSINESS["name"])
            await human_delay(0.5, 1)
            await page.keyboard.press("Enter")
            await human_delay(2, 3)
        
        await save_screenshot(page, "dir_411_2")
        
        # Look for "Add your business" or "Claim" link
        add_link = await page.query_selector('a[href*="add"], a[href*="claim"], a[href*="business"]')
        if add_link:
            await add_link.click()
            await human_delay(2, 3)
            await save_screenshot(page, "dir_411_3")
            return {"name": "411.ca", "status": "found_add_page"}
        
        return {"name": "411.ca", "status": "searched"}
    except Exception as e:
        return {"name": "411.ca", "status": "error", "error": str(e)[:50]}

async def submit_canpages(page):
    """Submit to Canpages"""
    print("\n🔥 CANPAGES")
    try:
        await page.goto("https://www.canpages.ca/", timeout=30000)
        await human_delay(2, 3)
        await save_screenshot(page, "dir_canpages_1")
        
        # Look for add business option
        links = await page.query_selector_all('a')
        for link in links[:30]:
            try:
                text = await link.inner_text()
                if any(word in text.lower() for word in ["add", "claim", "business", "list your"]):
                    href = await link.get_attribute("href")
                    await link.click()
                    await human_delay(2, 3)
                    await save_screenshot(page, "dir_canpages_2")
                    return {"name": "Canpages", "status": "found_add_page", "url": page.url}
            except:
                continue
        
        await save_screenshot(page, "dir_canpages_2")
        return {"name": "Canpages", "status": "visited"}
    except Exception as e:
        return {"name": "Canpages", "status": "error", "error": str(e)[:50]}

async def submit_iglobal(page):
    """Submit to iGlobal"""
    print("\n🔥 IGLOBAL")
    try:
        await page.goto("https://ca.iglobal.co/register", timeout=30000)
        await human_delay(2, 3)
        await save_screenshot(page, "dir_iglobal_1")
        
        filled = 0
        if await safe_fill(page, 'input[name="company"], #company, input[placeholder*="company"]', BUSINESS["name"]):
            filled += 1
        if await safe_fill(page, 'input[name="email"], #email, input[type="email"]', BUSINESS["email"]):
            filled += 1
        if await safe_fill(page, 'input[name="phone"], #phone', BUSINESS["phone"]):
            filled += 1
        if await safe_fill(page, 'input[name="website"], #website', BUSINESS["website"]):
            filled += 1
        
        await save_screenshot(page, "dir_iglobal_2")
        
        return {"name": "iGlobal", "status": "filled", "fields": filled}
    except Exception as e:
        return {"name": "iGlobal", "status": "error", "error": str(e)[:50]}

async def submit_indexbeaute(page):
    """Submit to IndexBeauté.ca (Beauty Industry Directory)"""
    print("\n🔥 INDEX BEAUTÉ")
    try:
        await page.goto("https://www.indexbeaute.ca/", timeout=30000)
        await human_delay(2, 3)
        await save_screenshot(page, "dir_indexbeaute_1")
        
        # Look for registration or add business
        links = await page.query_selector_all('a')
        for link in links[:40]:
            try:
                text = await link.inner_text()
                href = await link.get_attribute("href") or ""
                if any(word in (text + href).lower() for word in ["inscri", "register", "ajouter", "add", "entreprise"]):
                    await link.click()
                    await human_delay(2, 3)
                    await save_screenshot(page, "dir_indexbeaute_2")
                    return {"name": "IndexBeauté", "status": "found_register", "url": page.url}
            except:
                continue
        
        await save_screenshot(page, "dir_indexbeaute_2")
        return {"name": "IndexBeauté", "status": "visited"}
    except Exception as e:
        return {"name": "IndexBeauté", "status": "error", "error": str(e)[:50]}

# ==================== MAIN ====================

async def submit_to_all_directories():
    """Submit to ALL directories"""
    print("=" * 70)
    print("🚀 LUXURA - COMPLETE DIRECTORY SUBMISSION")
    print("=" * 70)
    print(f"Business: {BUSINESS['name']}")
    print(f"Website: {BUSINESS['website']}")
    print("=" * 70)
    
    results = []
    
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
        
        # Submit to all directories
        submissions = [
            submit_hotfrog,
            submit_cylex,
            submit_yelp,
            submit_pagesjaunes,
            submit_411,
            submit_canpages,
            submit_iglobal,
            submit_indexbeaute,
        ]
        
        for func in submissions:
            try:
                result = await func(page)
                results.append(result)
                await human_delay(3, 6)
            except Exception as e:
                results.append({"name": func.__name__, "status": "error", "error": str(e)[:50]})
        
        await browser.close()
    
    # Print summary
    print("\n" + "=" * 70)
    print("📊 SUBMISSION SUMMARY")
    print("=" * 70)
    
    for r in results:
        status = r.get("status", "unknown")
        name = r.get("name", "Unknown")
        icon = "✅" if status in ["submitted", "filled", "found_add_page", "found_register"] else "⚠️" if status == "visited" else "❌"
        fields = r.get("fields", 0)
        extra = f" ({fields} fields)" if fields else ""
        print(f"   {icon} {name:15} : {status}{extra}")
    
    # Screenshots
    print(f"\n📸 Screenshots saved to {SCREENSHOTS_DIR}/")
    
    return results

if __name__ == "__main__":
    results = asyncio.run(submit_to_all_directories())
