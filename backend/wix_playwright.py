# =====================================================
# WIX PLAYWRIGHT AUTOMATION
# Ajoute automatiquement l'image de couverture via le Dashboard
# =====================================================

import os
import asyncio
import logging
from typing import Optional
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

logger = logging.getLogger(__name__)

# Credentials from .env
WIX_EMAIL = os.getenv("WIX_EMAIL", "info@luxuradistribution.com")
WIX_PASSWORD = os.getenv("WIX_PASSWORD", "Liana2018$")


async def add_cover_image_via_playwright(
    post_title: str,
    image_filename: str,
    wix_site_url: str = "https://manage.wix.com"
) -> bool:
    """
    Utilise Playwright pour ajouter l'image de couverture via le Dashboard Wix.
    
    Args:
        post_title: Titre du blog post (pour le trouver dans la liste)
        image_filename: Nom du fichier image dans Wix Media Manager
        wix_site_url: URL du dashboard Wix
    
    Returns:
        True si succès, False sinon
    """
    logger.info(f"🎭 Playwright: Adding cover image to '{post_title[:50]}...'")
    
    async with async_playwright() as p:
        # Lancer le navigateur en mode headless
        browser = await p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )
        
        page = await context.new_page()
        
        try:
            # === ÉTAPE 1: Se connecter à Wix ===
            logger.info("Step 1: Logging into Wix...")
            await page.goto("https://users.wix.com/signin", wait_until="networkidle", timeout=30000)
            
            # Attendre le formulaire de login
            await page.wait_for_selector('input[type="email"], input[name="email"]', timeout=10000)
            
            # Remplir email
            email_input = page.locator('input[type="email"], input[name="email"]').first
            await email_input.fill(WIX_EMAIL)
            
            # Cliquer sur continuer/suivant
            continue_btn = page.locator('button:has-text("Continue"), button:has-text("Continuer"), button[type="submit"]').first
            await continue_btn.click()
            
            await page.wait_for_timeout(2000)
            
            # Remplir mot de passe
            await page.wait_for_selector('input[type="password"]', timeout=10000)
            password_input = page.locator('input[type="password"]').first
            await password_input.fill(WIX_PASSWORD)
            
            # Cliquer sur login
            login_btn = page.locator('button:has-text("Log In"), button:has-text("Se connecter"), button[type="submit"]').first
            await login_btn.click()
            
            # Attendre la redirection vers le dashboard
            await page.wait_for_url("**/dashboard/**", timeout=30000)
            logger.info("✅ Logged into Wix successfully!")
            
            # === ÉTAPE 2: Aller au Blog Manager ===
            logger.info("Step 2: Navigating to Blog Manager...")
            
            # Chercher le lien Blog dans le menu
            await page.goto("https://manage.wix.com/dashboard", wait_until="networkidle", timeout=30000)
            
            # Cliquer sur Blog dans le menu latéral
            blog_menu = page.locator('text=Blog, a:has-text("Blog")').first
            await blog_menu.click()
            await page.wait_for_timeout(3000)
            
            # === ÉTAPE 3: Trouver l'article ===
            logger.info(f"Step 3: Finding post '{post_title[:30]}...'")
            
            # Chercher l'article par son titre
            post_link = page.locator(f'text="{post_title[:50]}"').first
            await post_link.click()
            await page.wait_for_timeout(3000)
            
            # === ÉTAPE 4: Ouvrir les paramètres ===
            logger.info("Step 4: Opening post settings...")
            
            # Cliquer sur Settings ou l'icône engrenage
            settings_btn = page.locator('button:has-text("Settings"), [aria-label="Settings"], button:has-text("Paramètres")').first
            await settings_btn.click()
            await page.wait_for_timeout(2000)
            
            # === ÉTAPE 5: Ajouter l'image de couverture ===
            logger.info("Step 5: Adding cover image...")
            
            # Chercher le bouton Featured Image / Image de couverture
            featured_btn = page.locator('text=Featured Image, text=Image de couverture, text=Cover Image').first
            await featured_btn.click()
            await page.wait_for_timeout(2000)
            
            # Ouvrir le Media Manager
            media_btn = page.locator('text=Choose from Media, text=Choisir dans les médias, button:has-text("Media")').first
            await media_btn.click()
            await page.wait_for_timeout(3000)
            
            # Chercher l'image par son nom
            image_element = page.locator(f'[alt*="{image_filename}"], img[src*="{image_filename}"], text="{image_filename}"').first
            await image_element.click()
            await page.wait_for_timeout(1000)
            
            # Confirmer la sélection
            add_btn = page.locator('button:has-text("Add"), button:has-text("Ajouter"), button:has-text("Select")').first
            await add_btn.click()
            await page.wait_for_timeout(2000)
            
            # === ÉTAPE 6: Sauvegarder ===
            logger.info("Step 6: Saving changes...")
            
            save_btn = page.locator('button:has-text("Save"), button:has-text("Enregistrer"), button:has-text("Done")').first
            await save_btn.click()
            await page.wait_for_timeout(3000)
            
            logger.info(f"✅ Cover image added successfully to '{post_title[:30]}...'!")
            return True
            
        except PlaywrightTimeout as e:
            logger.error(f"❌ Playwright timeout: {e}")
            # Prendre une capture d'écran pour debug
            await page.screenshot(path="/app/backend/playwright_error.png")
            return False
            
        except Exception as e:
            logger.error(f"❌ Playwright error: {e}")
            await page.screenshot(path="/app/backend/playwright_error.png")
            return False
            
        finally:
            await browser.close()


async def test_wix_login() -> bool:
    """Test la connexion à Wix pour vérifier les credentials"""
    logger.info("🧪 Testing Wix login...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        
        page = await browser.new_page()
        
        try:
            await page.goto("https://users.wix.com/signin", wait_until="networkidle", timeout=30000)
            
            # Remplir email
            await page.wait_for_selector('input[type="email"], input[name="email"]', timeout=10000)
            email_input = page.locator('input[type="email"], input[name="email"]').first
            await email_input.fill(WIX_EMAIL)
            
            # Continuer
            continue_btn = page.locator('button:has-text("Continue"), button:has-text("Continuer"), button[type="submit"]').first
            await continue_btn.click()
            await page.wait_for_timeout(2000)
            
            # Mot de passe
            await page.wait_for_selector('input[type="password"]', timeout=10000)
            password_input = page.locator('input[type="password"]').first
            await password_input.fill(WIX_PASSWORD)
            
            # Login
            login_btn = page.locator('button:has-text("Log In"), button:has-text("Se connecter"), button[type="submit"]').first
            await login_btn.click()
            
            # Attendre le dashboard
            await page.wait_for_url("**/dashboard/**", timeout=30000)
            
            logger.info("✅ Wix login test successful!")
            await page.screenshot(path="/app/backend/wix_login_success.png")
            return True
            
        except Exception as e:
            logger.error(f"❌ Wix login test failed: {e}")
            await page.screenshot(path="/app/backend/wix_login_error.png")
            return False
            
        finally:
            await browser.close()


if __name__ == "__main__":
    # Test la connexion
    asyncio.run(test_wix_login())
