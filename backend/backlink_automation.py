# Luxura Distribution - FULL Backlink Automation with Email Verification
# Handles form submission, CAPTCHA attempts, and email verification

import asyncio
import random
import os
import re
from datetime import datetime
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from dotenv import load_dotenv

load_dotenv("/app/backend/.env")

# ==================== CONFIGURATION ====================

BUSINESS = {
    "name": "Luxura Distribution",
    "name_full": "Luxura Distribution Inc.",
    "description": "Importateur et distributeur direct d'extensions capillaires professionnelles au Québec. Qualité salon haut de gamme. Plus de 30 salons partenaires.",
    "address": "1887, 83e Rue",
    "city": "St-Georges",
    "province": "Québec",
    "province_abbr": "QC", 
    "postal_code": "G6A 1M9",
    "country": "Canada",
    "full_address": "1887, 83e Rue, St-Georges, QC G6A 1M9, Canada",
    "phone": "(418) 222-3939",
    "phone_clean": "4182223939",
    "email": os.getenv("LUXURA_EMAIL", "info@luxuradistribution.com"),
    "password": os.getenv("LUXURA_PASSWORD", ""),
    "password_alt": os.getenv("LUXURA_PASSWORD_ALT", ""),
    "website": "https://www.luxuradistribution.com",
    "category": "Hair Extensions / Extensions capillaires",
}

SCREENSHOTS_DIR = "/tmp/backlinks"
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

# ==================== HELPERS ====================

async def human_delay(min_sec=1.0, max_sec=3.0):
    await asyncio.sleep(random.uniform(min_sec, max_sec))

async def human_type(element, text, delay_range=(30, 80)):
    """Type like a human with variable speed"""
    for char in text:
        await element.type(char, delay=random.randint(*delay_range))
    await human_delay(0.2, 0.5)

async def safe_click(page, selector, timeout=5000):
    """Safely click an element if it exists"""
    try:
        elem = await page.wait_for_selector(selector, timeout=timeout)
        if elem:
            await elem.click()
            return True
    except:
        pass
    return False

async def safe_fill(page, selector, text, timeout=5000):
    """Safely fill a field if it exists"""
    try:
        elem = await page.wait_for_selector(selector, timeout=timeout)
        if elem:
            await elem.click()
            await human_delay(0.2, 0.4)
            await elem.fill("")  # Clear first
            await human_type(elem, text)
            return True
    except:
        pass
    return False

async def save_screenshot(page, name):
    """Save screenshot with timestamp"""
    filename = f"{SCREENSHOTS_DIR}/{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    await page.screenshot(path=filename, full_page=False)
    print(f"📸 {filename}")
    return filename

async def try_solve_checkbox_captcha(page):
    """Try to solve simple checkbox CAPTCHA (reCAPTCHA v2 checkbox)"""
    try:
        # Look for reCAPTCHA iframe
        frames = page.frames
        for frame in frames:
            if "recaptcha" in frame.url:
                # Try to click the checkbox
                checkbox = await frame.query_selector(".recaptcha-checkbox-border")
                if checkbox:
                    await checkbox.click()
                    await human_delay(2, 4)
                    print("✅ Clicked reCAPTCHA checkbox")
                    return True
    except Exception as e:
        print(f"⚠️ CAPTCHA attempt: {e}")
    return False

# ==================== EMAIL VERIFICATION ====================

async def check_email_for_verification(page, context):
    """Login to email and look for verification links"""
    print("\n📧 CHECKING EMAIL FOR VERIFICATION LINKS...")
    
    email = BUSINESS["email"]
    passwords = [BUSINESS["password"], BUSINESS["password_alt"]]
    
    verification_links = []
    
    try:
        # Try to login to webmail
        # First try Outlook/Hotmail style
        await page.goto("https://outlook.live.com/owa/", timeout=30000)
        await human_delay(2, 3)
        
        # Check if it's a custom domain email - might use different provider
        if "@luxuradistribution.com" in email:
            # Try common webmail providers for custom domains
            webmail_urls = [
                f"https://mail.luxuradistribution.com",
                f"https://webmail.luxuradistribution.com", 
                "https://mail.google.com",  # If using Google Workspace
            ]
            
            for url in webmail_urls:
                try:
                    await page.goto(url, timeout=10000)
                    await human_delay(1, 2)
                    await save_screenshot(page, "email_login_attempt")
                    
                    # Look for login form
                    email_field = await page.query_selector('input[type="email"], input[name="email"], input[name="username"], #email, #username')
                    if email_field:
                        await email_field.fill(email)
                        await human_delay(0.5, 1)
                        
                        # Look for password field
                        pass_field = await page.query_selector('input[type="password"], input[name="password"], #password')
                        if pass_field:
                            for pwd in passwords:
                                if pwd:
                                    await pass_field.fill(pwd)
                                    await human_delay(0.5, 1)
                                    
                                    # Try to submit
                                    submit = await page.query_selector('button[type="submit"], input[type="submit"], .login-btn, #login')
                                    if submit:
                                        await submit.click()
                                        await human_delay(3, 5)
                                        await save_screenshot(page, "email_after_login")
                                        
                                        # Check if logged in
                                        content = await page.content()
                                        if "inbox" in content.lower() or "boîte" in content.lower():
                                            print("✅ Email login successful!")
                                            
                                            # Look for verification emails
                                            # Search for recent emails with "verify", "confirm", "activation"
                                            links = await page.query_selector_all('a[href*="verify"], a[href*="confirm"], a[href*="activate"]')
                                            for link in links:
                                                href = await link.get_attribute("href")
                                                if href:
                                                    verification_links.append(href)
                                            
                                            break
                        break
                except Exception as e:
                    print(f"⚠️ Webmail {url}: {e}")
                    continue
        
        await save_screenshot(page, "email_final")
        
    except Exception as e:
        print(f"❌ Email check error: {e}")
    
    return verification_links

# ==================== DIRECTORY SUBMISSIONS ====================

async def submit_hotfrog(page):
    """Submit to Hotfrog Canada with full form fill"""
    print("\n🔥 HOTFROG CANADA - Full Submission")
    result = {"directory": "Hotfrog", "status": "started", "fields_filled": []}
    
    try:
        await page.goto("https://www.hotfrog.ca/add-a-business", timeout=30000)
        await human_delay(2, 4)
        await save_screenshot(page, "hotfrog_01_landing")
        
        # Common field selectors to try
        field_mappings = [
            ('input[name="businessName"], input[name="company"], #businessName, #company', BUSINESS["name"]),
            ('input[name="address"], input[name="street"], #address, #street', BUSINESS["full_address"]),
            ('input[name="city"], #city', BUSINESS["city"]),
            ('input[name="state"], input[name="province"], #state, #province', BUSINESS["province"]),
            ('input[name="zip"], input[name="postalCode"], #zip, #postalCode', BUSINESS["postal_code"]),
            ('input[name="phone"], input[name="telephone"], #phone', BUSINESS["phone"]),
            ('input[name="email"], #email', BUSINESS["email"]),
            ('input[name="website"], input[name="url"], #website', BUSINESS["website"]),
            ('textarea[name="description"], #description', BUSINESS["description"]),
        ]
        
        for selectors, value in field_mappings:
            for selector in selectors.split(", "):
                if await safe_fill(page, selector, value, timeout=2000):
                    result["fields_filled"].append(selector)
                    break
        
        await human_delay(1, 2)
        await save_screenshot(page, "hotfrog_02_filled")
        
        # Try to handle CAPTCHA
        await try_solve_checkbox_captcha(page)
        
        # Look for submit button
        submit_clicked = await safe_click(page, 'button[type="submit"], input[type="submit"], .submit-btn, #submit')
        if submit_clicked:
            await human_delay(3, 5)
            await save_screenshot(page, "hotfrog_03_submitted")
            result["status"] = "submitted"
        else:
            result["status"] = "form_filled"
        
        result["url"] = page.url
        
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        print(f"❌ Hotfrog error: {e}")
    
    return result

async def submit_cylex(page):
    """Submit to Cylex Canada"""
    print("\n🔥 CYLEX CANADA - Full Submission")
    result = {"directory": "Cylex", "status": "started", "fields_filled": []}
    
    try:
        await page.goto("https://www.cylex.ca/add-company", timeout=30000)
        await human_delay(2, 4)
        await save_screenshot(page, "cylex_01_landing")
        
        # Try to fill form fields
        field_mappings = [
            ('#company_name, input[name="company_name"]', BUSINESS["name"]),
            ('#street, input[name="street"]', BUSINESS["address"]),
            ('#city, input[name="city"]', BUSINESS["city"]),
            ('#zip, input[name="zip"]', BUSINESS["postal_code"]),
            ('#phone, input[name="phone"]', BUSINESS["phone"]),
            ('#email, input[name="email"]', BUSINESS["email"]),
            ('#website, input[name="website"]', BUSINESS["website"]),
        ]
        
        for selector, value in field_mappings:
            if await safe_fill(page, selector, value, timeout=2000):
                result["fields_filled"].append(selector)
        
        await human_delay(1, 2)
        await save_screenshot(page, "cylex_02_filled")
        
        # Try submit
        if await safe_click(page, 'button[type="submit"], input[type="submit"], .submit'):
            await human_delay(3, 5)
            await save_screenshot(page, "cylex_03_submitted")
            result["status"] = "submitted"
        else:
            result["status"] = "form_filled"
        
        result["url"] = page.url
        
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
    
    return result

async def submit_yelp(page):
    """Submit to Yelp Business"""
    print("\n🔥 YELP BUSINESS - Attempting Submission")
    result = {"directory": "Yelp", "status": "started"}
    
    try:
        await page.goto("https://biz.yelp.ca/signup_business/new", timeout=30000)
        await human_delay(2, 4)
        await save_screenshot(page, "yelp_01_landing")
        
        # Yelp has strong bot detection, try basic fill
        # Look for business name field
        if await safe_fill(page, 'input[name="business_name"], #business-name', BUSINESS["name"]):
            result["fields_filled"] = ["business_name"]
        
        await human_delay(1, 2)
        await save_screenshot(page, "yelp_02_attempt")
        
        # Yelp likely needs manual completion due to strong verification
        result["status"] = "needs_manual"
        result["note"] = "Yelp has strong bot detection - may need manual completion"
        result["url"] = page.url
        
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
    
    return result

async def submit_canpages(page):
    """Submit to Canpages"""
    print("\n🔥 CANPAGES - Submission")
    result = {"directory": "Canpages", "status": "started"}
    
    try:
        await page.goto("https://www.canpages.ca/", timeout=30000)
        await human_delay(2, 4)
        await save_screenshot(page, "canpages_01_landing")
        
        # Look for add business link
        add_links = await page.query_selector_all('a')
        for link in add_links:
            try:
                text = await link.inner_text()
                if any(word in text.lower() for word in ["add", "claim", "business", "list"]):
                    href = await link.get_attribute("href")
                    result["add_business_link"] = href
                    await link.click()
                    await human_delay(2, 3)
                    await save_screenshot(page, "canpages_02_add_page")
                    break
            except:
                continue
        
        result["status"] = "visited"
        result["url"] = page.url
        
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
    
    return result

async def submit_iglobal(page):
    """Submit to iGlobal"""
    print("\n🔥 IGLOBAL - Submission")
    result = {"directory": "iGlobal", "status": "started", "fields_filled": []}
    
    try:
        await page.goto("https://ca.iglobal.co/register", timeout=30000)
        await human_delay(2, 4)
        await save_screenshot(page, "iglobal_01_landing")
        
        # Try to fill registration form
        if await safe_fill(page, 'input[name="company"], #company', BUSINESS["name"]):
            result["fields_filled"].append("company")
        if await safe_fill(page, 'input[name="email"], #email', BUSINESS["email"]):
            result["fields_filled"].append("email")
        if await safe_fill(page, 'input[type="password"], #password', BUSINESS["password"]):
            result["fields_filled"].append("password")
        
        await human_delay(1, 2)
        await save_screenshot(page, "iglobal_02_filled")
        
        result["status"] = "form_filled"
        result["url"] = page.url
        
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
    
    return result

async def submit_411(page):
    """Submit to 411.ca"""
    print("\n🔥 411.CA - Submission")
    result = {"directory": "411.ca", "status": "started"}
    
    try:
        await page.goto("https://www.411.ca/", timeout=30000)
        await human_delay(2, 4)
        await save_screenshot(page, "411_01_landing")
        
        # Search for existing listing first
        search_box = await page.query_selector('input[type="search"], input[name="q"], #search')
        if search_box:
            await search_box.fill(BUSINESS["name"])
            await human_delay(1, 2)
            
            # Submit search
            await page.keyboard.press("Enter")
            await human_delay(2, 3)
            await save_screenshot(page, "411_02_search_results")
        
        result["status"] = "searched"
        result["url"] = page.url
        
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
    
    return result

# ==================== MAIN RUNNER ====================

async def run_full_automation():
    """Run complete backlink automation with email verification"""
    print("=" * 70)
    print("🚀 LUXURA DISTRIBUTION - FULL BACKLINK AUTOMATION")
    print("=" * 70)
    print(f"Business: {BUSINESS['name']}")
    print(f"Email: {BUSINESS['email']}")
    print(f"Website: {BUSINESS['website']}")
    print("=" * 70)
    
    all_results = {}
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-dev-shm-usage', '--disable-blink-features=AutomationControlled']
        )
        
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            locale="fr-CA",
            timezone_id="America/Toronto"
        )
        
        # Add some cookies to look more human
        await context.add_cookies([
            {"name": "visited", "value": "true", "domain": ".hotfrog.ca", "path": "/"},
            {"name": "visited", "value": "true", "domain": ".cylex.ca", "path": "/"},
        ])
        
        page = await context.new_page()
        
        # Run all submissions
        submissions = [
            ("Hotfrog", submit_hotfrog),
            ("Cylex", submit_cylex),
            ("iGlobal", submit_iglobal),
            ("411", submit_411),
            ("Canpages", submit_canpages),
            ("Yelp", submit_yelp),
        ]
        
        for name, func in submissions:
            try:
                print(f"\n{'='*50}")
                all_results[name] = await func(page)
                await human_delay(3, 6)  # Longer delay between sites
            except Exception as e:
                all_results[name] = {"status": "error", "error": str(e)}
        
        # Check email for verification links
        print(f"\n{'='*50}")
        verification_links = await check_email_for_verification(page, context)
        all_results["email_verification"] = {
            "links_found": len(verification_links),
            "links": verification_links[:5]  # First 5 links
        }
        
        await browser.close()
    
    # Print final summary
    print("\n" + "=" * 70)
    print("📊 RÉSUMÉ FINAL - SOUMISSIONS BACKLINKS")
    print("=" * 70)
    
    for name, result in all_results.items():
        status = result.get("status", "unknown")
        fields = len(result.get("fields_filled", []))
        icon = "✅" if status in ["submitted", "form_filled"] else "⚠️" if status == "visited" else "❌"
        print(f"{icon} {name}: {status}" + (f" ({fields} fields)" if fields else ""))
        if result.get("error"):
            print(f"   └── Error: {result['error'][:60]}")
    
    # List all screenshots
    print(f"\n📸 SCREENSHOTS ({len(os.listdir(SCREENSHOTS_DIR))} files):")
    for f in sorted(os.listdir(SCREENSHOTS_DIR))[-10:]:  # Last 10
        print(f"   - {f}")
    
    return all_results

if __name__ == "__main__":
    results = asyncio.run(run_full_automation())
    print("\n✅ Full automation complete!")
