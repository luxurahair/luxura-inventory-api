# Luxura Distribution - COMPLETE Backlink System
# 1. Submit to directories
# 2. Check email for verification links
# 3. Click verification links

import asyncio
import imaplib
import email
from email.header import decode_header
import random
import os
import re
from datetime import datetime, timedelta
from playwright.async_api import async_playwright
from dotenv import load_dotenv

load_dotenv("/app/backend/.env")

# ==================== CONFIGURATION ====================

BUSINESS = {
    "name": "Luxura Distribution",
    "description": "Importateur et distributeur direct d'extensions capillaires professionnelles au Québec.",
    "address": "1887, 83e Rue",
    "city": "St-Georges",
    "province": "Québec",
    "postal_code": "G6A 1M9",
    "full_address": "1887, 83e Rue, St-Georges, QC G6A 1M9, Canada",
    "phone": "(418) 222-3939",
    "email": os.getenv("LUXURA_EMAIL", "info@luxuradistribution.com"),
    "website": "https://www.luxuradistribution.com",
}

EMAIL = os.getenv("LUXURA_EMAIL")
APP_PASSWORD = os.getenv("LUXURA_APP_PASSWORD")

SCREENSHOTS_DIR = "/tmp/backlinks"
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

# ==================== HELPERS ====================

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

# ==================== EMAIL FUNCTIONS ====================

def decode_header_str(header):
    if not header:
        return ""
    parts = decode_header(header)
    result = ""
    for part, enc in parts:
        if isinstance(part, bytes):
            result += part.decode(enc or 'utf-8', errors='ignore')
        else:
            result += str(part)
    return result

def extract_links(msg):
    """Extract verification links from email"""
    links = []
    
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            if ctype in ["text/html", "text/plain"]:
                try:
                    body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    found = re.findall(r'https?://[^\s<>"\']+', body)
                    links.extend(found)
                except:
                    pass
    else:
        try:
            body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
            links = re.findall(r'https?://[^\s<>"\']+', body)
        except:
            pass
    
    # Filter for verification links
    verification_links = []
    for link in links:
        link_lower = link.lower()
        # Skip common non-verification domains
        if any(d in link_lower for d in ['google.com', 'facebook.com', 'twitter.com', 'unsubscribe']):
            continue
        # Prioritize verification keywords
        if any(k in link_lower for k in ['verify', 'confirm', 'activate', 'validate', 'click']):
            verification_links.append(link)
    
    return list(set(verification_links))

def check_gmail_for_verification():
    """Check Gmail for directory verification emails"""
    print("\n📧 Checking Gmail for verification emails...")
    
    verification_data = []
    
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
        mail.login(EMAIL, APP_PASSWORD)
        print("✅ Gmail connected")
        
        mail.select("INBOX")
        
        # Search recent emails
        date_since = (datetime.now() - timedelta(days=3)).strftime("%d-%b-%Y")
        status, messages = mail.search(None, f'(SINCE "{date_since}")')
        
        if status == "OK":
            email_ids = messages[0].split()
            print(f"   Checking {len(email_ids)} recent emails...")
            
            # Directory keywords
            keywords = ['hotfrog', 'cylex', 'yelp', 'canpages', '411', 'iglobal', 'yellow', 'verify', 'confirm', 'welcome', 'registration']
            
            for eid in email_ids[-100:]:  # Last 100
                try:
                    status, data = mail.fetch(eid, "(RFC822)")
                    if status == "OK":
                        msg = email.message_from_bytes(data[0][1])
                        subject = decode_header_str(msg.get("Subject", ""))
                        sender = decode_header_str(msg.get("From", ""))
                        
                        combined = f"{subject} {sender}".lower()
                        
                        if any(k in combined for k in keywords):
                            links = extract_links(msg)
                            if links:
                                print(f"\n   📬 {subject[:50]}...")
                                print(f"      From: {sender[:40]}")
                                print(f"      🔗 {len(links)} verification links found!")
                                
                                verification_data.append({
                                    "subject": subject,
                                    "from": sender,
                                    "links": links
                                })
                except:
                    continue
        
        mail.logout()
        
    except Exception as e:
        print(f"❌ Gmail error: {e}")
    
    return verification_data

# ==================== DIRECTORY SUBMISSIONS ====================

async def submit_hotfrog(page):
    print("\n🔥 HOTFROG - Submitting...")
    try:
        await page.goto("https://www.hotfrog.ca/add-a-business", timeout=30000)
        await human_delay(2, 3)
        await save_screenshot(page, "submit_hotfrog_1")
        
        # Try various selectors
        filled = 0
        for sel in ['input[name="businessName"]', '#businessName', 'input[placeholder*="business"]']:
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
        
        await human_delay(1, 2)
        await save_screenshot(page, "submit_hotfrog_2")
        
        # Try to submit
        submitted = await safe_click(page, 'button[type="submit"], input[type="submit"]')
        if submitted:
            await human_delay(3, 5)
            await save_screenshot(page, "submit_hotfrog_3")
        
        return {"status": "submitted" if submitted else "filled", "fields": filled}
    except Exception as e:
        return {"status": "error", "error": str(e)}

async def submit_cylex(page):
    print("\n🔥 CYLEX - Submitting...")
    try:
        await page.goto("https://www.cylex.ca/add-company", timeout=30000)
        await human_delay(2, 3)
        await save_screenshot(page, "submit_cylex_1")
        
        filled = 0
        if await safe_fill(page, '#company_name, input[name="company"]', BUSINESS["name"]):
            filled += 1
        if await safe_fill(page, '#street, input[name="street"]', BUSINESS["address"]):
            filled += 1
        if await safe_fill(page, '#city, input[name="city"]', BUSINESS["city"]):
            filled += 1
        if await safe_fill(page, '#phone, input[name="phone"]', BUSINESS["phone"]):
            filled += 1
        if await safe_fill(page, '#email, input[name="email"]', BUSINESS["email"]):
            filled += 1
        if await safe_fill(page, '#website, input[name="website"]', BUSINESS["website"]):
            filled += 1
        
        await save_screenshot(page, "submit_cylex_2")
        
        return {"status": "filled", "fields": filled}
    except Exception as e:
        return {"status": "error", "error": str(e)}

async def click_verification_links(page, links):
    """Click verification links with Playwright"""
    clicked = []
    
    for i, link_data in enumerate(links[:5]):
        for link in link_data.get("links", [])[:2]:  # Max 2 links per email
            try:
                print(f"\n🔗 Clicking: {link[:60]}...")
                await page.goto(link, timeout=30000)
                await human_delay(3, 5)
                await save_screenshot(page, f"verify_click_{i}")
                
                content = await page.content()
                success = any(w in content.lower() for w in ['success', 'verified', 'confirmed', 'thank', 'merci'])
                
                clicked.append({
                    "link": link[:60],
                    "status": "✅ SUCCESS" if success else "⚠️ Clicked"
                })
                
                if success:
                    print(f"   ✅ Verification SUCCESS!")
                    
            except Exception as e:
                clicked.append({"link": link[:60], "status": f"❌ Error: {str(e)[:30]}"})
    
    return clicked

# ==================== MAIN ====================

async def main():
    print("=" * 70)
    print("🚀 LUXURA - COMPLETE BACKLINK AUTOMATION")
    print("=" * 70)
    print(f"Business: {BUSINESS['name']}")
    print(f"Email: {EMAIL}")
    print("=" * 70)
    
    results = {
        "submissions": {},
        "email_verifications": [],
        "clicks": []
    }
    
    # Step 1: Check email first for any pending verifications
    print("\n" + "=" * 50)
    print("STEP 1: CHECK EMAIL FOR PENDING VERIFICATIONS")
    print("=" * 50)
    
    verification_emails = check_gmail_for_verification()
    results["email_verifications"] = verification_emails
    
    # Step 2: Submit to directories
    print("\n" + "=" * 50)
    print("STEP 2: SUBMIT TO DIRECTORIES")
    print("=" * 50)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()
        
        # Submit to directories
        results["submissions"]["Hotfrog"] = await submit_hotfrog(page)
        await human_delay(3, 5)
        
        results["submissions"]["Cylex"] = await submit_cylex(page)
        await human_delay(3, 5)
        
        # Step 3: Click verification links
        if verification_emails:
            print("\n" + "=" * 50)
            print("STEP 3: CLICKING VERIFICATION LINKS")
            print("=" * 50)
            
            results["clicks"] = await click_verification_links(page, verification_emails)
        
        await browser.close()
    
    # Print summary
    print("\n" + "=" * 70)
    print("📊 FINAL SUMMARY")
    print("=" * 70)
    
    print("\n📁 DIRECTORY SUBMISSIONS:")
    for name, data in results["submissions"].items():
        status = data.get("status", "unknown")
        icon = "✅" if status in ["submitted", "filled"] else "❌"
        print(f"   {icon} {name}: {status}")
    
    print(f"\n📧 VERIFICATION EMAILS FOUND: {len(results['email_verifications'])}")
    for v in results["email_verifications"]:
        print(f"   📬 {v['subject'][:50]}...")
    
    print(f"\n🔗 VERIFICATION LINKS CLICKED: {len(results['clicks'])}")
    for c in results["clicks"]:
        print(f"   {c['status']} - {c['link']}")
    
    # List screenshots
    print(f"\n📸 SCREENSHOTS:")
    for f in sorted(os.listdir(SCREENSHOTS_DIR))[-10:]:
        print(f"   - {f}")
    
    return results

if __name__ == "__main__":
    results = asyncio.run(main())
    print("\n✅ Complete!")
