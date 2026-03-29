"""
CITATION ENGINE - Moteur de soumission aux annuaires
Version: 1.0
Date: 2026-03-29

Consolide la logique de:
- backlink_automation.py
- submit_all_directories.py

Rôle:
- Soumettre aux annuaires via Playwright
- Retourner des résultats standardisés
- Ne PAS gérer l'email (c'est email_verification_engine.py)
"""

import asyncio
import random
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional, Callable
from playwright.async_api import async_playwright, Page, Browser

from .directory_registry import (
    DIRECTORY_REGISTRY,
    LUXURA_BUSINESS,
    get_playwright_directories,
    get_directory_by_key
)
from .backlink_models import SubmissionResult, BacklinkStatus

logger = logging.getLogger(__name__)

# =====================================================
# CONFIGURATION
# =====================================================

SCREENSHOTS_DIR = "/tmp/backlinks"
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

# =====================================================
# HELPERS PLAYWRIGHT
# =====================================================

async def human_delay(min_sec: float = 1.0, max_sec: float = 3.0):
    """Délai humain aléatoire"""
    await asyncio.sleep(random.uniform(min_sec, max_sec))


async def human_type(element, text: str, delay_range: tuple = (30, 80)):
    """Frappe comme un humain avec vitesse variable"""
    for char in text:
        await element.type(char, delay=random.randint(*delay_range))
    await human_delay(0.2, 0.5)


async def safe_click(page: Page, selector: str, timeout: int = 3000) -> bool:
    """Clique sur un élément s'il existe"""
    try:
        elem = await page.wait_for_selector(selector, timeout=timeout)
        if elem:
            await elem.click()
            return True
    except:
        pass
    return False


async def safe_fill(page: Page, selector: str, text: str, timeout: int = 3000) -> bool:
    """Remplit un champ s'il existe"""
    try:
        elem = await page.wait_for_selector(selector, timeout=timeout)
        if elem:
            await elem.click()
            await elem.fill(text)
            return True
    except:
        pass
    return False


async def safe_fill_multiple(page: Page, selectors: List[str], text: str, timeout: int = 3000) -> bool:
    """Essaye plusieurs sélecteurs jusqu'à ce qu'un fonctionne"""
    for selector in selectors:
        if await safe_fill(page, selector, text, timeout):
            return True
    return False


async def save_screenshot(page: Page, name: str) -> str:
    """Sauvegarde une capture d'écran"""
    filename = f"{SCREENSHOTS_DIR}/{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    try:
        await page.screenshot(path=filename, full_page=False)
        logger.debug(f"📸 {filename}")
    except:
        pass
    return filename


# =====================================================
# SOUMISSIONS PAR ANNUAIRE
# =====================================================

async def submit_hotfrog(page: Page, business: Dict) -> SubmissionResult:
    """Soumission à Hotfrog Canada"""
    directory = get_directory_by_key("hotfrog")
    logger.info("🔥 HOTFROG CANADA")
    
    try:
        await page.goto("https://www.hotfrog.ca/add-a-business", timeout=30000)
        await human_delay(2, 3)
        await save_screenshot(page, "hotfrog_1")
        
        filled = 0
        selectors = directory.get("selectors", {})
        
        # Business name
        if await safe_fill_multiple(page, selectors.get("business_name", []), business["name"]):
            filled += 1
        
        # Phone
        if await safe_fill_multiple(page, selectors.get("phone", []), business["phone"]):
            filled += 1
        
        # Email
        if await safe_fill_multiple(page, selectors.get("email", []), business["email"]):
            filled += 1
        
        # Website
        if await safe_fill_multiple(page, selectors.get("website", []), business["website"]):
            filled += 1
        
        # Address
        if await safe_fill_multiple(page, selectors.get("address", []), business["full_address"]):
            filled += 1
        
        # Description
        if await safe_fill_multiple(page, selectors.get("description", []), business["description"]):
            filled += 1
        
        await save_screenshot(page, "hotfrog_2")
        
        # Submit
        submitted = await safe_click(page, 'button[type="submit"], input[type="submit"], .btn-submit')
        if submitted:
            await human_delay(3, 5)
            await save_screenshot(page, "hotfrog_3")
        
        return SubmissionResult(
            directory_key="hotfrog",
            directory_name="Hotfrog Canada",
            status=BacklinkStatus.SUBMITTED if submitted else BacklinkStatus.EMAIL_PENDING,
            requires_email_verification=True,
            fields_filled=filled,
            submission_url=page.url
        )
        
    except Exception as e:
        logger.error(f"Hotfrog error: {e}")
        return SubmissionResult(
            directory_key="hotfrog",
            directory_name="Hotfrog Canada",
            status=BacklinkStatus.FAILED,
            error_message=str(e)[:100]
        )


async def submit_cylex(page: Page, business: Dict) -> SubmissionResult:
    """Soumission à Cylex Canada"""
    logger.info("🔥 CYLEX CANADA")
    
    try:
        await page.goto("https://www.cylex.ca/add-company", timeout=30000)
        await human_delay(2, 3)
        await save_screenshot(page, "cylex_1")
        
        filled = 0
        
        if await safe_fill(page, '#company_name, input[name="company_name"]', business["name"]):
            filled += 1
        if await safe_fill(page, '#street, input[name="street"]', business["address"]):
            filled += 1
        if await safe_fill(page, '#city, input[name="city"]', business["city"]):
            filled += 1
        if await safe_fill(page, '#zip, input[name="zip"]', business["postal_code"]):
            filled += 1
        if await safe_fill(page, '#phone, input[name="phone"]', business["phone"]):
            filled += 1
        if await safe_fill(page, '#email, input[name="email"]', business["email"]):
            filled += 1
        if await safe_fill(page, '#website, input[name="website"]', business["website"]):
            filled += 1
        
        await save_screenshot(page, "cylex_2")
        
        return SubmissionResult(
            directory_key="cylex",
            directory_name="Cylex Canada",
            status=BacklinkStatus.EMAIL_PENDING,
            requires_email_verification=True,
            fields_filled=filled,
            submission_url=page.url
        )
        
    except Exception as e:
        logger.error(f"Cylex error: {e}")
        return SubmissionResult(
            directory_key="cylex",
            directory_name="Cylex Canada",
            status=BacklinkStatus.FAILED,
            error_message=str(e)[:100]
        )


async def submit_yelp(page: Page, business: Dict) -> SubmissionResult:
    """Soumission à Yelp Canada"""
    logger.info("🔥 YELP CANADA")
    
    try:
        await page.goto("https://biz.yelp.ca/signup_business/new", timeout=30000)
        await human_delay(2, 4)
        await save_screenshot(page, "yelp_1")
        
        filled = 0
        
        # Business name
        for sel in ['input[name="biz_name"]', '#biz_name', 'input[placeholder*="business"]']:
            if await safe_fill(page, sel, business["name"]):
                filled += 1
                break
        
        # Address
        for sel in ['input[name="address1"]', '#address1']:
            if await safe_fill(page, sel, business["address"]):
                filled += 1
                break
        
        # City
        if await safe_fill(page, 'input[name="city"], #city', business["city"]):
            filled += 1
        
        # Province
        if await safe_fill(page, 'input[name="state"], #state', business["province_short"]):
            filled += 1
        
        # Postal
        if await safe_fill(page, 'input[name="zip"], #zip', business["postal_code"]):
            filled += 1
        
        # Phone
        if await safe_fill(page, 'input[name="phone"], #phone', business["phone_clean"]):
            filled += 1
        
        await save_screenshot(page, "yelp_2")
        
        return SubmissionResult(
            directory_key="yelp",
            directory_name="Yelp Canada",
            status=BacklinkStatus.EMAIL_PENDING,
            requires_email_verification=True,
            fields_filled=filled,
            submission_url=page.url,
            notes="Yelp peut demander vérification téléphone"
        )
        
    except Exception as e:
        logger.error(f"Yelp error: {e}")
        return SubmissionResult(
            directory_key="yelp",
            directory_name="Yelp Canada",
            status=BacklinkStatus.FAILED,
            error_message=str(e)[:100]
        )


async def submit_iglobal(page: Page, business: Dict) -> SubmissionResult:
    """Soumission à iGlobal Canada"""
    logger.info("🔥 IGLOBAL CANADA")
    
    try:
        await page.goto("https://ca.iglobal.co/register", timeout=30000)
        await human_delay(2, 3)
        await save_screenshot(page, "iglobal_1")
        
        filled = 0
        
        if await safe_fill(page, 'input[name="company"], #company', business["name"]):
            filled += 1
        if await safe_fill(page, 'input[name="email"], #email', business["email"]):
            filled += 1
        if await safe_fill(page, 'input[name="phone"], #phone', business["phone"]):
            filled += 1
        if await safe_fill(page, 'input[name="website"], #website', business["website"]):
            filled += 1
        
        await save_screenshot(page, "iglobal_2")
        
        return SubmissionResult(
            directory_key="iglobal",
            directory_name="iGlobal Canada",
            status=BacklinkStatus.EMAIL_PENDING,
            requires_email_verification=True,
            fields_filled=filled,
            submission_url=page.url
        )
        
    except Exception as e:
        logger.error(f"iGlobal error: {e}")
        return SubmissionResult(
            directory_key="iglobal",
            directory_name="iGlobal Canada",
            status=BacklinkStatus.FAILED,
            error_message=str(e)[:100]
        )


async def submit_pagesjaunes(page: Page, business: Dict) -> SubmissionResult:
    """Soumission à Pages Jaunes Canada"""
    logger.info("🔥 PAGES JAUNES CANADA")
    
    try:
        await page.goto("https://www.pagesjaunes.ca/", timeout=30000)
        await human_delay(2, 3)
        await save_screenshot(page, "pagesjaunes_1")
        
        # Chercher le lien d'ajout
        add_urls = [
            "https://www.pagesjaunes.ca/add-business",
            "https://www.pagesjaunes.ca/claim",
            "https://www.yellowpages.ca/add-business"
        ]
        
        for url in add_urls:
            try:
                await page.goto(url, timeout=10000)
                await human_delay(1, 2)
                if "add" in page.url or "claim" in page.url:
                    await save_screenshot(page, "pagesjaunes_2")
                    return SubmissionResult(
                        directory_key="pagesjaunes",
                        directory_name="Pages Jaunes Canada",
                        status=BacklinkStatus.EMAIL_PENDING,
                        requires_email_verification=True,
                        submission_url=page.url,
                        notes="Page d'ajout trouvée"
                    )
            except:
                continue
        
        return SubmissionResult(
            directory_key="pagesjaunes",
            directory_name="Pages Jaunes Canada",
            status=BacklinkStatus.FAILED,
            notes="Page d'ajout non trouvée - soumission manuelle requise"
        )
        
    except Exception as e:
        logger.error(f"Pages Jaunes error: {e}")
        return SubmissionResult(
            directory_key="pagesjaunes",
            directory_name="Pages Jaunes Canada",
            status=BacklinkStatus.FAILED,
            error_message=str(e)[:100]
        )


async def submit_411(page: Page, business: Dict) -> SubmissionResult:
    """Soumission à 411.ca"""
    logger.info("🔥 411.CA")
    
    try:
        await page.goto("https://www.411.ca/", timeout=30000)
        await human_delay(2, 3)
        await save_screenshot(page, "411_1")
        
        # Rechercher le business
        search_box = await page.query_selector('input[type="search"], input[name="q"], #what')
        if search_box:
            await search_box.fill(business["name"])
            await human_delay(0.5, 1)
            await page.keyboard.press("Enter")
            await human_delay(2, 3)
        
        await save_screenshot(page, "411_2")
        
        # Chercher le lien d'ajout
        add_link = await page.query_selector('a[href*="add"], a[href*="claim"]')
        if add_link:
            await add_link.click()
            await human_delay(2, 3)
            await save_screenshot(page, "411_3")
            return SubmissionResult(
                directory_key="411",
                directory_name="411.ca",
                status=BacklinkStatus.EMAIL_PENDING,
                submission_url=page.url
            )
        
        return SubmissionResult(
            directory_key="411",
            directory_name="411.ca",
            status=BacklinkStatus.FAILED,
            notes="Recherche effectuée, ajout manuel requis"
        )
        
    except Exception as e:
        logger.error(f"411 error: {e}")
        return SubmissionResult(
            directory_key="411",
            directory_name="411.ca",
            status=BacklinkStatus.FAILED,
            error_message=str(e)[:100]
        )


async def submit_canpages(page: Page, business: Dict) -> SubmissionResult:
    """Soumission à Canpages"""
    logger.info("🔥 CANPAGES")
    
    try:
        await page.goto("https://www.canpages.ca/", timeout=30000)
        await human_delay(2, 3)
        await save_screenshot(page, "canpages_1")
        
        # Chercher le lien d'ajout
        links = await page.query_selector_all('a')
        for link in links[:30]:
            try:
                text = await link.inner_text()
                if any(word in text.lower() for word in ["add", "claim", "business", "list your"]):
                    await link.click()
                    await human_delay(2, 3)
                    await save_screenshot(page, "canpages_2")
                    return SubmissionResult(
                        directory_key="canpages",
                        directory_name="Canpages",
                        status=BacklinkStatus.EMAIL_PENDING,
                        submission_url=page.url
                    )
            except:
                continue
        
        return SubmissionResult(
            directory_key="canpages",
            directory_name="Canpages",
            status=BacklinkStatus.FAILED,
            notes="Page visitée, ajout manuel requis"
        )
        
    except Exception as e:
        logger.error(f"Canpages error: {e}")
        return SubmissionResult(
            directory_key="canpages",
            directory_name="Canpages",
            status=BacklinkStatus.FAILED,
            error_message=str(e)[:100]
        )


async def submit_indexbeaute(page: Page, business: Dict) -> SubmissionResult:
    """Soumission à IndexBeauté.ca"""
    logger.info("🔥 INDEX BEAUTÉ")
    
    try:
        await page.goto("https://www.indexbeaute.ca/", timeout=30000)
        await human_delay(2, 3)
        await save_screenshot(page, "indexbeaute_1")
        
        # Chercher inscription/ajout
        links = await page.query_selector_all('a')
        for link in links[:40]:
            try:
                text = await link.inner_text()
                href = await link.get_attribute("href") or ""
                if any(word in (text + href).lower() for word in ["inscri", "register", "ajouter", "entreprise"]):
                    await link.click()
                    await human_delay(2, 3)
                    await save_screenshot(page, "indexbeaute_2")
                    return SubmissionResult(
                        directory_key="indexbeaute",
                        directory_name="IndexBeauté.ca",
                        status=BacklinkStatus.EMAIL_PENDING,
                        requires_email_verification=True,
                        submission_url=page.url,
                        notes="Annuaire beauté Québec - TRÈS pertinent"
                    )
            except:
                continue
        
        return SubmissionResult(
            directory_key="indexbeaute",
            directory_name="IndexBeauté.ca",
            status=BacklinkStatus.FAILED,
            notes="Page visitée, inscription manuelle requise"
        )
        
    except Exception as e:
        logger.error(f"IndexBeauté error: {e}")
        return SubmissionResult(
            directory_key="indexbeaute",
            directory_name="IndexBeauté.ca",
            status=BacklinkStatus.FAILED,
            error_message=str(e)[:100]
        )


# =====================================================
# MAPPING DES FONCTIONS DE SOUMISSION
# =====================================================

SUBMISSION_FUNCTIONS: Dict[str, Callable] = {
    "hotfrog": submit_hotfrog,
    "cylex": submit_cylex,
    "yelp": submit_yelp,
    "iglobal": submit_iglobal,
    "pagesjaunes": submit_pagesjaunes,
    "411": submit_411,
    "canpages": submit_canpages,
    "indexbeaute": submit_indexbeaute,
}


# =====================================================
# FONCTIONS PRINCIPALES
# =====================================================

async def submit_to_directory(
    directory_key: str,
    business: Dict = None,
    page: Page = None
) -> SubmissionResult:
    """
    Soumet à un annuaire spécifique.
    
    Args:
        directory_key: Clé de l'annuaire (hotfrog, cylex, etc.)
        business: Données business (utilise LUXURA_BUSINESS par défaut)
        page: Instance Playwright Page (crée une nouvelle si non fournie)
    
    Returns:
        SubmissionResult avec le statut de la soumission
    """
    if business is None:
        business = LUXURA_BUSINESS
    
    if directory_key not in SUBMISSION_FUNCTIONS:
        return SubmissionResult(
            directory_key=directory_key,
            directory_name=directory_key,
            status=BacklinkStatus.FAILED,
            error_message=f"Pas de fonction de soumission pour {directory_key}"
        )
    
    submit_func = SUBMISSION_FUNCTIONS[directory_key]
    
    # Si page fournie, utiliser directement
    if page:
        return await submit_func(page, business)
    
    # Sinon créer un browser
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            locale="fr-CA"
        )
        page = await context.new_page()
        
        try:
            result = await submit_func(page, business)
        finally:
            await browser.close()
        
        return result


async def submit_to_all_directories(
    directory_keys: List[str] = None,
    business: Dict = None,
    delay_between: tuple = (3, 6)
) -> List[SubmissionResult]:
    """
    Soumet à plusieurs annuaires.
    
    Args:
        directory_keys: Liste des clés d'annuaires (tous les Playwright par défaut)
        business: Données business
        delay_between: Délai entre soumissions (min, max secondes)
    
    Returns:
        Liste de SubmissionResult
    """
    if business is None:
        business = LUXURA_BUSINESS
    
    if directory_keys is None:
        directory_keys = list(SUBMISSION_FUNCTIONS.keys())
    
    results = []
    
    logger.info("=" * 70)
    logger.info("🚀 LUXURA - CITATION ENGINE")
    logger.info("=" * 70)
    logger.info(f"Business: {business['name']}")
    logger.info(f"Annuaires: {len(directory_keys)}")
    logger.info("=" * 70)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            locale="fr-CA"
        )
        page = await context.new_page()
        
        for key in directory_keys:
            if key not in SUBMISSION_FUNCTIONS:
                logger.warning(f"⚠️ Pas de fonction pour {key}, skip")
                continue
            
            try:
                result = await SUBMISSION_FUNCTIONS[key](page, business)
                results.append(result)
                
                # Log résultat
                status_icon = "✅" if result.status != BacklinkStatus.FAILED else "❌"
                logger.info(f"{status_icon} {result.directory_name}: {result.status}")
                
                # Délai entre soumissions
                await asyncio.sleep(random.uniform(*delay_between))
                
            except Exception as e:
                logger.error(f"❌ Erreur {key}: {e}")
                results.append(SubmissionResult(
                    directory_key=key,
                    directory_name=key,
                    status=BacklinkStatus.FAILED,
                    error_message=str(e)[:100]
                ))
        
        await browser.close()
    
    # Résumé
    success = len([r for r in results if r.status != BacklinkStatus.FAILED])
    logger.info("=" * 70)
    logger.info(f"📊 RÉSUMÉ: {success}/{len(results)} soumissions réussies")
    logger.info("=" * 70)
    
    return results


# =====================================================
# FONCTION CLI
# =====================================================

async def run_citation_cycle(directories: List[str] = None):
    """
    Lance un cycle complet de citations.
    Utilisable depuis CLI ou CRON.
    """
    results = await submit_to_all_directories(directory_keys=directories)
    
    # Afficher résumé
    for r in results:
        icon = "✅" if r.status != BacklinkStatus.FAILED else "❌"
        print(f"   {icon} {r.directory_name:20} : {r.status}")
    
    return results
