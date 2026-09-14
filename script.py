import update_dependencies
update_dependencies.update_dependencies()

import os
import shutil
import sys
import parser
import time
from calendar_integration import get_calendar_events, check_conflict, LOCAL_TZ

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import config
from config import DATUMPRIKKER_URL, NAAM, EMAIL


def _check_win_paths(relative_paths):
    prefixes = [
        os.environ.get("PROGRAMFILES", r"C:\Program Files"),
        os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)"),
        os.environ.get("LOCALAPPDATA", r"C:\Users\%USERNAME%\AppData\Local")
    ]
    for prefix in prefixes:
        for rel in relative_paths:
            if os.path.isfile(os.path.join(prefix, rel)):
                return True
    return False


def detect_installed_browsers():
    """Detecteer welke browsers op het systeem aanwezig zijn."""
    detected = []

    # Firefox
    if any(shutil.which(cmd) for cmd in ["firefox", "firefox.exe"]) or \
       (sys.platform == "win32" and _check_win_paths([r"Mozilla Firefox\firefox.exe"])) or \
       (sys.platform == "darwin" and os.path.exists("/Applications/Firefox.app")):
        detected.append("firefox")

    # Chrome
    if any(shutil.which(cmd) for cmd in ["google-chrome", "google-chrome-stable", "chrome", "chrome.exe"]) or \
       (sys.platform == "win32" and _check_win_paths([r"Google\Chrome\Application\chrome.exe"])) or \
       (sys.platform == "darwin" and os.path.exists("/Applications/Google Chrome.app")):
        detected.append("chrome")

    # Edge
    if any(shutil.which(cmd) for cmd in ["microsoft-edge", "microsoft-edge-stable", "msedge", "msedge.exe"]) or \
       (sys.platform == "win32" and _check_win_paths([r"Microsoft\Edge\Application\msedge.exe"])) or \
       (sys.platform == "darwin" and os.path.exists("/Applications/Microsoft Edge.app")):
        detected.append("edge")

    # Chromium
    if any(shutil.which(cmd) for cmd in ["chromium", "chromium-browser"]):
        detected.append("chromium")

    # Brave
    if any(shutil.which(cmd) for cmd in ["brave-browser", "brave", "brave.exe"]) or \
       (sys.platform == "win32" and _check_win_paths([r"BraveSoftware\Brave-Browser\Application\brave.exe"])) or \
       (sys.platform == "darwin" and os.path.exists("/Applications/Brave Browser.app")):
        detected.append("brave")

    # Safari (alleen macOS)
    if sys.platform == "darwin" and os.path.exists("/Applications/Safari.app"):
        detected.append("safari")

    return detected


def _maximize_driver(driver):
    """Maximaliseer het venster automatisch naar het schermformaat van de gebruiker."""
    try:
        driver.maximize_window()
    except Exception:
        # Fallback voor omgevingen zonder window manager
        try:
            driver.set_window_size(1280, 800)
        except Exception:
            pass


def _launch_browser(browser_name):
    """Start de geselecteerde browser met passende opties."""
    b = browser_name.lower().strip()

    if b == "firefox":
        from selenium.webdriver.firefox.options import Options as FirefoxOptions
        options = FirefoxOptions()
        try:
            return webdriver.Firefox(options=options)
        except Exception:
            from webdriver_manager.firefox import GeckoDriverManager
            from selenium.webdriver.firefox.service import Service as FirefoxService
            return webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()), options=options)

    elif b in ("chrome", "google-chrome"):
        from selenium.webdriver.chrome.options import Options as ChromeOptions
        options = ChromeOptions()
        try:
            return webdriver.Chrome(options=options)
        except Exception:
            from webdriver_manager.chrome import ChromeDriverManager
            from selenium.webdriver.chrome.service import Service as ChromeService
            return webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)

    elif b == "edge":
        from selenium.webdriver.edge.options import Options as EdgeOptions
        options = EdgeOptions()
        try:
            return webdriver.Edge(options=options)
        except Exception:
            from webdriver_manager.microsoft import EdgeChromiumDriverManager
            from selenium.webdriver.edge.service import Service as EdgeService
            return webdriver.Edge(service=EdgeService(EdgeChromiumDriverManager().install()), options=options)

    elif b == "chromium":
        from selenium.webdriver.chrome.options import Options as ChromeOptions
        options = ChromeOptions()
        chrom_path = shutil.which("chromium") or shutil.which("chromium-browser")
        if chrom_path:
            options.binary_location = chrom_path
        try:
            return webdriver.Chrome(options=options)
        except Exception:
            from webdriver_manager.chrome import ChromeDriverManager
            from webdriver_manager.core.os_manager import ChromeType
            from selenium.webdriver.chrome.service import Service as ChromeService
            return webdriver.Chrome(service=ChromeService(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()), options=options)

    elif b == "brave":
        from selenium.webdriver.chrome.options import Options as ChromeOptions
        options = ChromeOptions()
        brave_path = shutil.which("brave-browser") or shutil.which("brave") or shutil.which("brave.exe")
        if brave_path:
            options.binary_location = brave_path
        try:
            return webdriver.Chrome(options=options)
        except Exception:
            from webdriver_manager.chrome import ChromeDriverManager
            from webdriver_manager.core.os_manager import ChromeType
            from selenium.webdriver.chrome.service import Service as ChromeService
            return webdriver.Chrome(service=ChromeService(ChromeDriverManager(chrome_type=ChromeType.BRAVE).install()), options=options)

    elif b == "safari":
        from selenium.webdriver.safari.options import Options as SafariOptions
        options = SafariOptions()
        return webdriver.Safari(options=options)

    else:
        raise ValueError(
            f"Onbekende browser '{browser_name}'. "
            "Kies uit: 'auto', 'firefox', 'chrome', 'edge', 'chromium', 'brave', 'safari'."
        )


def get_driver(browser_preference="auto"):
    """Vind en start een werkende WebDriver voor de gewenste browser."""
    pref = (browser_preference or "auto").lower().strip()

    if pref != "auto":
        print(f"Browser gekozen in configuratie: {pref}")
        driver = _launch_browser(pref)
        _maximize_driver(driver)
        return driver

    # Automatische detectie
    installed = detect_installed_browsers()
    candidates = installed if installed else ["firefox", "chrome", "edge", "chromium", "safari"]

    print(f"Gedetecteerde browser(s): {', '.join(installed) if installed else 'geen specifiek gedetecteerd, probeer standaardlijst'}")

    errors = []
    for browser in candidates:
        try:
            print(f"Poging om '{browser}' op te starten...")
            driver = _launch_browser(browser)
            _maximize_driver(driver)
            print(f"Browser succesvol gestart ({browser})!")
            return driver
        except Exception as e:
            print(f"Kon '{browser}' niet starten: {e}")
            errors.append(f"{browser}: {e}")
            continue

    raise RuntimeError(
        "Geen geschikte browser kunnen opstarten. "
        "Zorg dat minstens één browser (Firefox, Chrome, Edge, Chromium, Brave) geïnstalleerd is, "
        "of pas BROWSER aan in config.py.\n"
        f"Gevonden fouten: {'; '.join(errors)}"
    )


def run_agent():
    events = get_calendar_events()

    browser_pref = getattr(config, "BROWSER", "auto")
    driver = get_driver(browser_pref)
    wait = WebDriverWait(driver, 15)
    
    try:
        driver.get(DATUMPRIKKER_URL)

        # 1. Cookies (Desktop selector)
        try:
            cookie_btn = wait.until(EC.element_to_be_clickable((By.ID, "didomi-notice-agree-button")))
            cookie_btn.click()
        except:
            pass
        

        # 2. Start invullen
        start_btn = wait.until(EC.element_to_be_clickable((By.ID, "nav_next")))
        start_btn.click()

        #2.5 Taal op NL zetten
        try:
            menu_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".toggle-popupmenu")))
            menu_btn.click()

            language_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".select_language a")))
            language_btn.click()

            nederlands_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a[href='?hl=nl']")))
            nederlands_btn.click()
        except Exception as e:
            print(f"Taal switch overgeslagen: {e}")

        time.sleep(1)

        # 3. Grid uitlezen en vergelijken
        # Datumprikker gebruikt vaak een tabel of grid voor de opties
        rows = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".eventdate")))

        for row in rows:
            try:
                # Hier moet je de parsing aanpassen aan het exacte Datumprikker format
                # Voorbeeld: "maandag 12 mei 2026 14:00 - 15:00"
                date_text = row.find_element(By.CSS_SELECTOR, ".date").text
                
                # Parse de datumtekst naar start en eind datetime objecten
                start_dt, end_dt = parser.parse_dutch_datumprikker_date(date_text)
                
                # Voorzie de tijden van de juiste tijdzone (nodig voor check_conflict)
                prikker_start = LOCAL_TZ.localize(start_dt)
                prikker_end = LOCAL_TZ.localize(end_dt)
                
                # Check op conflicten met Google Calendar
                bezet = check_conflict(prikker_start, prikker_end, events)
                
                if bezet:
                    element = row.find_element(By.CSS_SELECTOR, "li.no")
                    driver.execute_script("arguments[0].click();", element)
                else:
                    element = row.find_element(By.CSS_SELECTOR, "li.yes")
                    driver.execute_script("arguments[0].click();", element)
            except Exception as e:
                print(f"Fout bij verwerken van rij: {e}")
                continue

        # 4. Navigatie & Persoonsgegevens
        next_btn = driver.find_element(By.ID, "nav_next")
        next_btn.click()

        naam_veld = wait.until(EC.visibility_of_element_located((By.ID, "eventname")))
        naam_veld.send_keys(NAAM)
        
        email_veld = driver.find_element(By.ID, "eventemail")
        email_veld.send_keys(EMAIL)

        # 5. Volgende (naar overzichtspagina)
        final_next = driver.find_element(By.ID, "nav_next")
        final_next.click()

        print("Agent is klaar met invullen. Controleer de pagina.")

    finally:
        input("Klaar? Druk op Enter...")
        driver.quit()

if __name__ == "__main__":
    run_agent()
