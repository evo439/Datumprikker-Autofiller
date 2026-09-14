import subprocess
import sys

def update_dependencies():
    packages = [
        "pytz",
        "selenium",
        "webdriver-manager",
        "google-auth",
        "google-auth-oauthlib",
        "google-api-python-client"
    ]
    print("Checking and updating dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "--break-system-packages"] + packages)
        print("Dependencies updated successfully.")
    except Exception as e:
        print(f"Waarschuwing: Kon afhankelijkheden niet automatisch bijwerken via pip: {e}")

if __name__ == "__main__":
    update_dependencies()
