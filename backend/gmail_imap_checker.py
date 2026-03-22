# Luxura Distribution - Gmail IMAP Email Checker
# Direct IMAP connection to check for verification emails

import imaplib
import email
from email.header import decode_header
import os
import re
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv("/app/backend/.env")

# Gmail IMAP settings
IMAP_SERVER = "imap.gmail.com"
IMAP_PORT = 993

EMAIL = os.getenv("LUXURA_EMAIL", "info@luxuradistribution.com")
PASSWORD = os.getenv("LUXURA_PASSWORD", "")
PASSWORD_ALT = os.getenv("LUXURA_PASSWORD_ALT", "")

def decode_mime_header(header):
    """Decode email header"""
    if header is None:
        return ""
    decoded_parts = decode_header(header)
    result = ""
    for part, encoding in decoded_parts:
        if isinstance(part, bytes):
            result += part.decode(encoding or 'utf-8', errors='ignore')
        else:
            result += part
    return result

def extract_links_from_email(msg):
    """Extract all links from email body"""
    links = []
    
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == "text/html":
                try:
                    body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    # Find all href links
                    href_pattern = r'href=["\']([^"\']+)["\']'
                    found_links = re.findall(href_pattern, body, re.IGNORECASE)
                    links.extend(found_links)
                except:
                    pass
            elif content_type == "text/plain":
                try:
                    body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    # Find URLs in plain text
                    url_pattern = r'https?://[^\s<>"\']+' 
                    found_links = re.findall(url_pattern, body)
                    links.extend(found_links)
                except:
                    pass
    else:
        try:
            body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
            url_pattern = r'https?://[^\s<>"\']+' 
            links = re.findall(url_pattern, body)
        except:
            pass
    
    # Filter out common non-verification links
    filtered_links = []
    exclude_domains = ['google.com', 'gstatic.com', 'googleapis.com', 'facebook.com', 'twitter.com', 'linkedin.com']
    verification_keywords = ['verify', 'confirm', 'activate', 'click', 'validate', 'subscribe', 'unsubscribe']
    
    for link in links:
        # Skip excluded domains
        if any(domain in link.lower() for domain in exclude_domains):
            continue
        # Prioritize verification-related links
        if any(keyword in link.lower() for keyword in verification_keywords):
            filtered_links.insert(0, link)  # Add to front
        else:
            filtered_links.append(link)
    
    return list(dict.fromkeys(filtered_links))  # Remove duplicates, keep order

def connect_gmail(email_addr, password):
    """Connect to Gmail via IMAP"""
    print(f"\n📧 Connecting to Gmail IMAP...")
    print(f"   Email: {email_addr}")
    
    try:
        # Connect to Gmail IMAP server
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        
        # Login
        mail.login(email_addr, password)
        print("✅ Gmail IMAP login successful!")
        
        return mail
        
    except imaplib.IMAP4.error as e:
        error_msg = str(e)
        if "Invalid credentials" in error_msg or "AUTHENTICATIONFAILED" in error_msg:
            print(f"❌ Authentication failed. Error: {error_msg}")
            print("\n⚠️ Si tu as 2FA activé sur Gmail, tu dois créer un 'App Password':")
            print("   1. Va sur https://myaccount.google.com/apppasswords")
            print("   2. Sélectionne 'Mail' et 'Other (Custom name)'")
            print("   3. Nomme-le 'Luxura Backlinks'")
            print("   4. Copie le mot de passe généré (16 caractères)")
            print("   5. Donne-moi ce mot de passe")
        else:
            print(f"❌ IMAP Error: {error_msg}")
        return None
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return None

def search_verification_emails(mail):
    """Search for verification emails from directories"""
    print("\n🔍 Searching for verification emails...")
    
    verification_emails = []
    
    # Select inbox
    mail.select("INBOX")
    
    # Search terms for directory verification emails
    search_senders = [
        "hotfrog",
        "cylex", 
        "yelp",
        "canpages",
        "411",
        "iglobal",
        "pages jaunes",
        "yellow pages",
        "noreply",
        "verify",
        "confirm"
    ]
    
    # Search emails from last 7 days
    date_since = (datetime.now() - timedelta(days=7)).strftime("%d-%b-%Y")
    
    # Search for recent unread emails
    try:
        # Search all recent emails
        status, messages = mail.search(None, f'(SINCE "{date_since}")')
        
        if status == "OK":
            email_ids = messages[0].split()
            print(f"   Found {len(email_ids)} emails from last 7 days")
            
            # Check last 50 emails
            for email_id in email_ids[-50:]:
                try:
                    status, msg_data = mail.fetch(email_id, "(RFC822)")
                    
                    if status == "OK":
                        raw_email = msg_data[0][1]
                        msg = email.message_from_bytes(raw_email)
                        
                        subject = decode_mime_header(msg.get("Subject", ""))
                        sender = decode_mime_header(msg.get("From", ""))
                        date = msg.get("Date", "")
                        
                        # Check if it's a verification email
                        combined_text = f"{subject} {sender}".lower()
                        
                        is_verification = any(term in combined_text for term in search_senders)
                        is_verification = is_verification or any(word in combined_text for word in ["verify", "confirm", "activate", "welcome", "registration"])
                        
                        if is_verification:
                            links = extract_links_from_email(msg)
                            
                            verification_emails.append({
                                "id": email_id.decode(),
                                "subject": subject[:80],
                                "from": sender[:50],
                                "date": date,
                                "links": links[:10],  # First 10 links
                                "verification_links": [l for l in links if any(k in l.lower() for k in ["verify", "confirm", "activate", "click"])][:5]
                            })
                            
                            print(f"\n   📬 Found: {subject[:50]}...")
                            print(f"      From: {sender[:40]}")
                            if links:
                                print(f"      Links: {len(links)} found")
                            
                except Exception as e:
                    continue
                    
    except Exception as e:
        print(f"❌ Search error: {e}")
    
    return verification_emails

def main():
    print("=" * 70)
    print("📧 LUXURA - GMAIL IMAP VERIFICATION CHECKER")
    print("=" * 70)
    
    results = {
        "login": False,
        "emails_found": [],
        "verification_links": []
    }
    
    # Try first password
    mail = connect_gmail(EMAIL, PASSWORD)
    
    # If failed, try alternative password
    if mail is None and PASSWORD_ALT:
        print("\n🔄 Trying alternative password...")
        mail = connect_gmail(EMAIL, PASSWORD_ALT)
    
    if mail:
        results["login"] = True
        
        # Search for verification emails
        results["emails_found"] = search_verification_emails(mail)
        
        # Collect all verification links
        for email_info in results["emails_found"]:
            for link in email_info.get("verification_links", []):
                results["verification_links"].append({
                    "subject": email_info["subject"][:40],
                    "link": link
                })
        
        # Logout
        mail.logout()
        print("\n✅ Gmail connection closed")
    
    # Print summary
    print("\n" + "=" * 70)
    print("📊 RÉSUMÉ")
    print("=" * 70)
    print(f"Login IMAP: {'✅ Réussi' if results['login'] else '❌ Échoué'}")
    print(f"Emails de vérification trouvés: {len(results['emails_found'])}")
    print(f"Liens de vérification: {len(results['verification_links'])}")
    
    if results["verification_links"]:
        print("\n🔗 LIENS À CLIQUER:")
        for i, link_info in enumerate(results["verification_links"], 1):
            print(f"\n   {i}. {link_info['subject']}")
            print(f"      {link_info['link'][:80]}...")
    
    return results

if __name__ == "__main__":
    results = main()
