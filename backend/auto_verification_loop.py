# Luxura Distribution - Auto Verification Loop
# Checks Gmail every 10 minutes until all directories are verified

import asyncio
import imaplib
import email
from email.header import decode_header
import os
import re
import json
from datetime import datetime, timedelta
from playwright.async_api import async_playwright
from dotenv import load_dotenv

load_dotenv("/app/backend/.env")

EMAIL = os.getenv("LUXURA_EMAIL", "info@luxuradistribution.com")
APP_PASSWORD = os.getenv("LUXURA_APP_PASSWORD", "")

SCREENSHOTS_DIR = "/tmp/backlinks"
STATUS_FILE = "/tmp/backlinks/verification_status.json"
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

# Directories to track
DIRECTORIES = {
    "hotfrog": {"verified": False, "keywords": ["hotfrog"], "submitted": True},
    "cylex": {"verified": False, "keywords": ["cylex"], "submitted": True},
    "yelp": {"verified": False, "keywords": ["yelp"], "submitted": False},
    "canpages": {"verified": False, "keywords": ["canpages", "canpage"], "submitted": False},
    "411": {"verified": False, "keywords": ["411"], "submitted": False},
    "iglobal": {"verified": False, "keywords": ["iglobal"], "submitted": False},
    "pagesjaunes": {"verified": False, "keywords": ["pages jaunes", "yellow pages", "pagesjaunes"], "submitted": False},
}

def load_status():
    """Load verification status from file"""
    try:
        if os.path.exists(STATUS_FILE):
            with open(STATUS_FILE, 'r') as f:
                return json.load(f)
    except:
        pass
    return DIRECTORIES.copy()

def save_status(status):
    """Save verification status to file"""
    try:
        with open(STATUS_FILE, 'w') as f:
            json.dump(status, f, indent=2, default=str)
    except Exception as e:
        print(f"⚠️ Could not save status: {e}")

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

def extract_verification_links(msg):
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
    
    # Filter for verification links only
    verification_links = []
    skip_domains = ['google.com', 'facebook.com', 'twitter.com', 'linkedin.com', 'unsubscribe', 'mailto:']
    verify_keywords = ['verify', 'confirm', 'activate', 'validate', 'click', 'registration', 'account']
    
    for link in links:
        link_lower = link.lower()
        if any(d in link_lower for d in skip_domains):
            continue
        if any(k in link_lower for k in verify_keywords):
            verification_links.append(link)
    
    return list(set(verification_links))

def check_gmail_for_verifications(status):
    """Check Gmail for verification emails"""
    print(f"\n📧 [{datetime.now().strftime('%H:%M:%S')}] Checking Gmail...")
    
    found_emails = []
    
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
        mail.login(EMAIL, APP_PASSWORD)
        mail.select("INBOX")
        
        # Search last 7 days
        date_since = (datetime.now() - timedelta(days=7)).strftime("%d-%b-%Y")
        result, messages = mail.search(None, f'(SINCE "{date_since}")')
        
        if result == "OK":
            email_ids = messages[0].split()
            print(f"   Scanning {len(email_ids)} emails...")
            
            for eid in email_ids[-150:]:  # Last 150 emails
                try:
                    result, data = mail.fetch(eid, "(RFC822)")
                    if result == "OK":
                        msg = email.message_from_bytes(data[0][1])
                        subject = decode_header_str(msg.get("Subject", ""))
                        sender = decode_header_str(msg.get("From", ""))
                        
                        combined = f"{subject} {sender}".lower()
                        
                        # Check which directory this email is from
                        for dir_name, dir_info in status.items():
                            if dir_info.get("verified"):
                                continue  # Already verified
                            
                            # Check if email matches this directory
                            if any(kw in combined for kw in dir_info["keywords"]):
                                links = extract_verification_links(msg)
                                if links:
                                    print(f"\n   🎯 Found email for {dir_name.upper()}!")
                                    print(f"      Subject: {subject[:50]}...")
                                    print(f"      Links: {len(links)} verification links")
                                    
                                    found_emails.append({
                                        "directory": dir_name,
                                        "subject": subject,
                                        "from": sender,
                                        "links": links
                                    })
                except:
                    continue
        
        mail.logout()
        
    except Exception as e:
        print(f"   ❌ Gmail error: {e}")
    
    return found_emails

async def click_verification_link(page, link, directory):
    """Click a verification link and check if successful"""
    try:
        print(f"   🔗 Clicking link for {directory}...")
        await page.goto(link, timeout=30000)
        await asyncio.sleep(3)
        
        # Take screenshot
        screenshot = f"{SCREENSHOTS_DIR}/verified_{directory}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        await page.screenshot(path=screenshot)
        print(f"   📸 {screenshot}")
        
        # Check for success indicators
        content = await page.content()
        content_lower = content.lower()
        
        success_indicators = ['success', 'verified', 'confirmed', 'thank you', 'merci', 
                            'congratulations', 'félicitations', 'compte activé', 'account activated',
                            'email verified', 'verification complete']
        
        if any(ind in content_lower for ind in success_indicators):
            print(f"   ✅ {directory.upper()} VERIFIED!")
            return True
        else:
            print(f"   ⚠️ Link clicked, verification status unclear")
            return "clicked"
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

async def process_verifications(found_emails, status):
    """Process all found verification emails"""
    if not found_emails:
        return status
    
    print(f"\n🔄 Processing {len(found_emails)} verification emails...")
    
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
        
        for email_data in found_emails:
            directory = email_data["directory"]
            links = email_data["links"]
            
            if status.get(directory, {}).get("verified"):
                continue
            
            # Try each link until one works
            for link in links[:3]:  # Max 3 attempts per directory
                result = await click_verification_link(page, link, directory)
                
                if result == True:
                    status[directory]["verified"] = True
                    status[directory]["verified_at"] = datetime.now().isoformat()
                    status[directory]["link_used"] = link[:100]
                    break
                elif result == "clicked":
                    # Mark as potentially verified, will confirm next check
                    status[directory]["clicked"] = True
                    status[directory]["last_click"] = datetime.now().isoformat()
                
                await asyncio.sleep(2)
        
        await browser.close()
    
    return status

def print_status(status):
    """Print current verification status"""
    print("\n" + "=" * 60)
    print("📊 VERIFICATION STATUS")
    print("=" * 60)
    
    verified_count = 0
    total_submitted = 0
    
    for name, info in status.items():
        if info.get("submitted"):
            total_submitted += 1
            if info.get("verified"):
                verified_count += 1
                icon = "✅"
                state = "VERIFIED"
            elif info.get("clicked"):
                icon = "🔄"
                state = "CLICKED (pending)"
            else:
                icon = "⏳"
                state = "WAITING"
        else:
            icon = "⬜"
            state = "Not submitted"
        
        print(f"   {icon} {name.upper():12} : {state}")
    
    print("-" * 60)
    print(f"   VERIFIED: {verified_count}/{total_submitted} submitted directories")
    
    return verified_count, total_submitted

async def run_verification_loop(max_iterations=30, interval_minutes=10):
    """
    Run verification loop until all directories are verified
    - max_iterations: Maximum number of checks (default 30 = 5 hours)
    - interval_minutes: Minutes between checks (default 10)
    """
    print("=" * 70)
    print("🔄 LUXURA - AUTO VERIFICATION LOOP STARTED")
    print("=" * 70)
    print(f"   Email: {EMAIL}")
    print(f"   Check interval: {interval_minutes} minutes")
    print(f"   Max iterations: {max_iterations}")
    print("=" * 70)
    
    status = load_status()
    
    for iteration in range(1, max_iterations + 1):
        print(f"\n{'='*60}")
        print(f"🔁 ITERATION {iteration}/{max_iterations} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # Check Gmail for verification emails
        found_emails = check_gmail_for_verifications(status)
        
        # Process any found verifications
        if found_emails:
            status = await process_verifications(found_emails, status)
        else:
            print("   📭 No new verification emails found")
        
        # Save status
        save_status(status)
        
        # Print current status
        verified_count, total_submitted = print_status(status)
        
        # Check if all verified
        if verified_count >= total_submitted and total_submitted > 0:
            print("\n" + "🎉" * 20)
            print("🎉 ALL DIRECTORIES VERIFIED! 🎉")
            print("🎉" * 20)
            break
        
        # Wait for next iteration (unless last iteration)
        if iteration < max_iterations:
            print(f"\n⏳ Next check in {interval_minutes} minutes...")
            print(f"   (Press Ctrl+C to stop)")
            await asyncio.sleep(interval_minutes * 60)
    
    # Final summary
    print("\n" + "=" * 70)
    print("📋 FINAL SUMMARY")
    print("=" * 70)
    print_status(status)
    
    # List all verification screenshots
    print("\n📸 Verification Screenshots:")
    for f in sorted(os.listdir(SCREENSHOTS_DIR)):
        if "verified_" in f:
            print(f"   - {f}")
    
    return status

# For running as a script
if __name__ == "__main__":
    import sys
    
    # Default: 30 iterations, 10 minute intervals = 5 hours max
    max_iter = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    interval = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    
    final_status = asyncio.run(run_verification_loop(max_iter, interval))
