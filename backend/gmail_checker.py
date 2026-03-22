# Luxura Distribution - Gmail Email Verification Script
# Checks Gmail for directory verification links

import asyncio
import random
import os
from datetime import datetime
from playwright.async_api import async_playwright
from dotenv import load_dotenv

load_dotenv("/app/backend/.env")

EMAIL = os.getenv("LUXURA_EMAIL", "info@luxuradistribution.com")
PASSWORD = os.getenv("LUXURA_PASSWORD", "")
PASSWORD_ALT = os.getenv("LUXURA_PASSWORD_ALT", "")

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
        print(f"⚠️ Could not save screenshot {name}")
    return filename

async def login_gmail(page, email, password):
    """Login to Gmail account"""
    print(f"\n📧 Attempting Gmail login for: {email}")
    
    try:
        # Go to Gmail
        await page.goto("https://accounts.google.com/signin/v2/identifier?service=mail", timeout=30000)
        await human_delay(2, 4)
        await save_screenshot(page, "gmail_01_login_page")
        
        # Enter email
        email_input = await page.wait_for_selector('input[type="email"]', timeout=10000)
        if email_input:
            await email_input.fill(email)
            await human_delay(0.5, 1)
            print(f"✅ Email entered: {email}")
            
            # Click Next
            next_btn = await page.query_selector('#identifierNext, button[type="submit"]')
            if next_btn:
                await next_btn.click()
                await human_delay(3, 5)
                await save_screenshot(page, "gmail_02_after_email")
        
        # Enter password
        try:
            pass_input = await page.wait_for_selector('input[type="password"]', timeout=10000)
            if pass_input:
                await pass_input.fill(password)
                await human_delay(0.5, 1)
                print("✅ Password entered")
                
                # Click Next
                next_btn = await page.query_selector('#passwordNext, button[type="submit"]')
                if next_btn:
                    await next_btn.click()
                    await human_delay(5, 8)
                    await save_screenshot(page, "gmail_03_after_password")
        except Exception as e:
            print(f"⚠️ Password step issue: {e}")
        
        # Check if we're logged in or need 2FA
        current_url = page.url
        page_content = await page.content()
        
        if "myaccount.google.com" in current_url or "mail.google.com" in current_url:
            print("✅ Gmail login successful!")
            return True
        elif "challenge" in current_url or "2-Step" in page_content or "vérification" in page_content.lower():
            print("⚠️ 2FA/Security challenge detected - needs manual intervention")
            await save_screenshot(page, "gmail_04_2fa_required")
            return "2fa_required"
        elif "incorrect" in page_content.lower() or "wrong" in page_content.lower() or "incorrect" in page_content.lower():
            print("❌ Wrong password")
            return False
        else:
            await save_screenshot(page, "gmail_04_unknown_state")
            return "unknown"
            
    except Exception as e:
        print(f"❌ Gmail login error: {e}")
        await save_screenshot(page, "gmail_error")
        return False

async def check_verification_emails(page):
    """Look for verification emails in Gmail inbox"""
    print("\n📬 Checking for verification emails...")
    
    verification_links = []
    
    try:
        # Go to Gmail inbox
        await page.goto("https://mail.google.com/mail/u/0/#inbox", timeout=30000)
        await human_delay(3, 5)
        await save_screenshot(page, "gmail_inbox_01")
        
        # Search for verification emails
        search_terms = ["verify", "confirm", "activation", "welcome", "hotfrog", "cylex", "yelp", "canpages"]
        
        for term in search_terms[:3]:  # Try first 3 terms
            try:
                # Find search box
                search_box = await page.query_selector('input[name="q"], input[aria-label*="Search"]')
                if search_box:
                    await search_box.fill(f"is:unread {term}")
                    await page.keyboard.press("Enter")
                    await human_delay(2, 3)
                    await save_screenshot(page, f"gmail_search_{term}")
                    
                    # Look for email rows
                    emails = await page.query_selector_all('tr.zA')
                    print(f"   Found {len(emails)} emails for '{term}'")
                    
                    # Click first unread email if found
                    if emails:
                        await emails[0].click()
                        await human_delay(2, 3)
                        await save_screenshot(page, f"gmail_email_{term}")
                        
                        # Look for verification links in email
                        links = await page.query_selector_all('a[href*="verify"], a[href*="confirm"], a[href*="activate"], a[href*="click"]')
                        for link in links:
                            href = await link.get_attribute("href")
                            if href and "google" not in href and "mailto:" not in href:
                                verification_links.append({
                                    "term": term,
                                    "url": href[:100]
                                })
                                print(f"   🔗 Found link: {href[:60]}...")
                        
                        # Go back to inbox
                        await page.goto("https://mail.google.com/mail/u/0/#inbox", timeout=15000)
                        await human_delay(1, 2)
                        
            except Exception as e:
                print(f"   ⚠️ Search error for '{term}': {e}")
        
        await save_screenshot(page, "gmail_inbox_final")
        
    except Exception as e:
        print(f"❌ Email check error: {e}")
    
    return verification_links

async def click_verification_links(page, links):
    """Click on verification links found in emails"""
    clicked = []
    
    for link_info in links[:5]:  # Max 5 links
        try:
            url = link_info.get("url", "")
            if url and url.startswith("http"):
                print(f"\n🔗 Clicking verification link: {url[:60]}...")
                await page.goto(url, timeout=30000)
                await human_delay(3, 5)
                await save_screenshot(page, f"verify_{link_info['term']}")
                
                # Check if verification succeeded
                content = await page.content()
                if any(word in content.lower() for word in ["success", "verified", "confirmed", "thank you", "merci"]):
                    print(f"   ✅ Verification successful for {link_info['term']}!")
                    clicked.append({"url": url, "status": "success"})
                else:
                    clicked.append({"url": url, "status": "clicked"})
                    
        except Exception as e:
            print(f"   ❌ Error clicking link: {e}")
            clicked.append({"url": link_info.get("url", ""), "status": "error", "error": str(e)})
    
    return clicked

async def main():
    print("=" * 70)
    print("📧 LUXURA - GMAIL VERIFICATION CHECK")
    print("=" * 70)
    print(f"Email: {EMAIL}")
    print("=" * 70)
    
    results = {
        "login_status": None,
        "verification_links": [],
        "clicked_links": []
    }
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-dev-shm-usage', '--disable-blink-features=AutomationControlled']
        )
        
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            locale="fr-CA"
        )
        
        page = await context.new_page()
        
        # Try login with first password
        login_result = await login_gmail(page, EMAIL, PASSWORD)
        
        # If first password fails, try alternative
        if login_result == False and PASSWORD_ALT:
            print("\n🔄 Trying alternative password...")
            login_result = await login_gmail(page, EMAIL, PASSWORD_ALT)
        
        results["login_status"] = login_result
        
        if login_result == True:
            # Check for verification emails
            results["verification_links"] = await check_verification_emails(page)
            
            # Click verification links if found
            if results["verification_links"]:
                results["clicked_links"] = await click_verification_links(page, results["verification_links"])
        
        await browser.close()
    
    # Print summary
    print("\n" + "=" * 70)
    print("📊 RÉSUMÉ VÉRIFICATION EMAIL")
    print("=" * 70)
    print(f"Login: {'✅ Réussi' if results['login_status'] == True else '⚠️ ' + str(results['login_status'])}")
    print(f"Liens trouvés: {len(results['verification_links'])}")
    print(f"Liens cliqués: {len(results['clicked_links'])}")
    
    if results["verification_links"]:
        print("\n🔗 Liens de vérification:")
        for link in results["verification_links"]:
            print(f"   - [{link['term']}] {link['url'][:50]}...")
    
    # List screenshots
    print(f"\n📸 Screenshots:")
    for f in sorted(os.listdir(SCREENSHOTS_DIR)):
        if "gmail" in f:
            print(f"   - {f}")
    
    return results

if __name__ == "__main__":
    results = asyncio.run(main())
