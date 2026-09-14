import pytz

# --- SCRIPT CONFIGURATIE ---
DATUMPRIKKER_URL = "https://datumprikker.nl/YOUR_LINK_HERE"
NAAM = "YOUR_NAME_HERE"
EMAIL = "YOUR_EMAIL_HERE"

# Kies je gewenste browser: "auto" (detecteert automatisch een beschikbare browser zoals Firefox, Chrome, Edge, etc.),
# of kies specifiek: "firefox", "chrome", "chromium", "edge", "brave", "safari"
BROWSER = "auto"

# --- CALENDAR CONFIGURATIE ---
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
LOCAL_TZ = pytz.timezone("Europe/Amsterdam")
EXCLUDED_CALENDARS = ['Verjaardagen', 'Feestdagen in Nederland', 'Tasks']




