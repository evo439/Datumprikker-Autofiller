import time
import update_dependencies
update_dependencies.update_dependencies()

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import config
from config import DATUMPRIKKER_URL, NAAM, EMAIL
from calendar_integration import get_calendar_events, check_conflict, LOCAL_TZ
from browser_utils import get_driver
import parser


def run_datumprikker(url=None):
    target_url = url or DATUMPRIKKER_URL
    if not target_url or "YOUR_LINK_HERE" in target_url:
        print("\nGeen geldige Datumprikker link gevonden in config.py.")
        entered = input("Voer de Datumprikker URL in (bijv. https://datumprikker.nl/...): ").strip()
        if entered:
            target_url = entered
        else:
            print("Geen URL opgegeven. Bewerking geannuleerd.")
            return

    name = NAAM
    if not name or "YOUR_NAME_HERE" in name:
        name = input("Voer je naam in: ").strip() or "Deelnemer"

    email = EMAIL
    if not email or "YOUR_EMAIL_HERE" in email:
        email = input("Voer je e-mailadres in: ").strip() or "deelnemer@example.com"

    print("\nAgenda-afspraken ophalen uit Google Calendar...")
    events = get_calendar_events()

    browser_pref = getattr(config, "BROWSER", "auto")
    driver = get_driver(browser_pref)
    wait = WebDriverWait(driver, 15)

    try:
        print(f"Navigeren naar {target_url}...")
        driver.get(target_url)

        # 1. Cookies (Desktop selector)
        try:
            cookie_btn = wait.until(EC.element_to_be_clickable((By.ID, "didomi-notice-agree-button")))
            cookie_btn.click()
        except Exception:
            pass

        # 2. Start invullen
        start_btn = wait.until(EC.element_to_be_clickable((By.ID, "nav_next")))
        start_btn.click()

        # 2.5 Taal op NL zetten indien mogelijk
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
        rows = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".eventdate")))
        print(f"{len(rows)} datum/tijd opties gevonden. Beschikbaarheid controleren...")

        # Detecteer of deze poll dagen-alleen is (geen ':' tijd in de teksten)
        row_texts = []
        for r in rows:
            try:
                row_texts.append(r.find_element(By.CSS_SELECTOR, ".date").text)
            except Exception:
                pass

        is_days_only = len(row_texts) > 0 and not any(":" in t for t in row_texts)
        time_window = None
        if is_days_only:
            time_window = parser.ask_custom_time_window()

        available_count = 0
        busy_count = 0

        for row in rows:
            try:
                date_text = row.find_element(By.CSS_SELECTOR, ".date").text
                start_dt, end_dt = parser.parse_dutch_datumprikker_date(date_text, time_window=time_window)

                prikker_start = LOCAL_TZ.localize(start_dt)
                prikker_end = LOCAL_TZ.localize(end_dt)

                bezet = check_conflict(prikker_start, prikker_end, events)

                if bezet:
                    busy_count += 1
                    element = row.find_element(By.CSS_SELECTOR, "li.no")
                    driver.execute_script("arguments[0].click();", element)
                else:
                    available_count += 1
                    element = row.find_element(By.CSS_SELECTOR, "li.yes")
                    driver.execute_script("arguments[0].click();", element)
            except Exception as e:
                print(f"Fout bij verwerken van rij: {e}")
                continue

        print(f"Resultaat: {available_count} beschikbaar, {busy_count} bezet.")

        # 4. Navigatie & Persoonsgegevens
        next_btn = driver.find_element(By.ID, "nav_next")
        next_btn.click()

        naam_veld = wait.until(EC.visibility_of_element_located((By.ID, "eventname")))
        naam_veld.clear()
        naam_veld.send_keys(name)

        email_veld = driver.find_element(By.ID, "eventemail")
        email_veld.clear()
        email_veld.send_keys(email)

        # 5. Volgende (naar overzichtspagina)
        final_next = driver.find_element(By.ID, "nav_next")
        final_next.click()

        print("\nAgent is klaar met invullen van Datumprikker. Controleer de pagina.")

    finally:
        input("\nKlaar? Druk op Enter om de browser te sluiten...")
        try:
            driver.quit()
        except Exception:
            pass


if __name__ == "__main__":
    run_datumprikker()
