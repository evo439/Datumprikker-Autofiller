import os
import shutil
import sys
from selenium import webdriver


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
