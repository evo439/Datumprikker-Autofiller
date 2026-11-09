# Poll Autofiller (Datumprikker & Timeful)

Dit script vult automatisch polls in op zowel [Datumprikker](https://datumprikker.nl/) als [Timeful](https://timeful.app/) op basis van je beschikbaarheid in Google Calendar. Het maakt gebruik van Selenium voor browserinteractie en de Google Calendar API om overlappende afspraken te detecteren.

## Vereisten

- Een ondersteunde browser geïnstalleerd op je systeem (bijv. Google Chrome, Mozilla Firefox, Microsoft Edge, Chromium of Brave).
- Python 3.x geïnstalleerd.

## Installatie & Configuratie

1. **Repository clonen of downloaden**:
   Zorg dat alle bestanden in dezelfde map staan.
2. **Instellingen configureren** in `config.py`:
   - Open `config.py`.
   - Stel `DATUMPRIKKER_URL` in voor Datumprikker polls.
   - Stel `TIMEFUL_URL` in voor Timeful polls.
   - Vul je naam (`NAAM`) en e-mailadres (`EMAIL`) in.
   - (Optioneel) Pas `BROWSER` aan: `"auto"` (standaard, detecteert automatisch een geïnstalleerde browser) of kies specifiek `"chrome"`, `"firefox"`, `"edge"`, etc.
   - Pas `EXCLUDED_CALENDARS` aan als je bepaalde agenda's wilt negeren (zoals feestdagen).
3. **Google Calendar API Credentials**:
   - Ga naar de [Google Cloud Console](https://console.cloud.google.com/).
   - Maak een project aan en schakel de **Google Calendar API** in.
   - Maak OAuth 2.0 Client ID inloggegevens aan (Desktop App).
   - Download het JSON-bestand, noem het `credentials.json`, en plaats dit in de hoofdmap van het project.

## Het script gebruiken

1. Open je terminal in de projectmap.
2. Start het hoofdscript:
   ```bash
   python script.py
   ```
3. Kies in het terminalmenu welke website je wilt invullen:
   - **1) Datumprikker (datumprikker.nl)**
   - **2) Timeful (timeful.app)**
   - **3) Afsluiten**

Je kunt de afzonderlijke scripts desgewenst ook direct uitvoeren:
- Alleen Datumprikker: `python datumprikker-script.py` (of `python datumprikker_script.py`)
- Alleen Timeful: `python timeful-script.py` (of `python timeful_script.py`)

4. **Eerste keer inloggen**: De eerste keer opent een browserscherm om in te loggen bij Google en leestoegang te verlenen tot je agenda. Dit genereert een `token.json` bestand zodat je niet telkens opnieuw hoeft in te loggen.
5. Het script start de browser, leest de voorgestelde datums/tijdsloten uit, checkt je Google Calendar op conflicten en vult je beschikbaarheid in.
6. De browser blijft openstaan zodat je de ingevulde gegevens kunt controleren. Druk op **Enter** in de terminal om af te ronden en de browser te sluiten.

## Structuur van de bestanden

- **`script.py`**: Het centrale startpunt met het interactieve terminal keuzemenu.
- **`datumprikker-script.py` / `datumprikker_script.py`**: Bevat de specifieke logica voor het invullen van Datumprikker.
- **`timeful-script.py` / `timeful_script.py`**: Bevat de specifieke logica voor het invullen van Timeful (via Timeful Plugin API en DOM).
- **`browser_utils.py`**: Gedeelde browserdetectie en WebDriver configuratie voor Chrome, Firefox, Edge, Brave, Chromium en Safari.
- **`calendar_integration.py`**: Beheert authenticatie met Google Calendar en detecteert tijdconflicten (`check_conflict`).
- **`parser.py`**: Converteert Nederlandse datumaanduidingen naar datetime-objecten.
- **`config.py`**: Centrale configuratie voor URL's, persoonlijke gegevens en kalender-instellingen.
- **`update_dependencies.py`**: Controleert en installeert automatisch eventuele ontbrekende Python packages.
