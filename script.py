import sys
import update_dependencies

# 1. Zorg dat benodigde packages aanwezig zijn
update_dependencies.update_dependencies()

from datumprikker_script import run_datumprikker
from timeful_script import run_timeful


def main_menu():
    print("\n" + "=" * 45)
    print("           POLL AUTOFILLER MENU")
    print("=" * 45)
    print("Voor welke website wil je de beschikbaarheid invullen?")
    print("  1) Datumprikker (datumprikker.nl)")
    print("  2) Timeful (timeful.app)")
    print("  3) Afsluiten")
    print("-" * 45)

    while True:
        try:
            choice = input("Maak een keuze [1, 2 of 3]: ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print("\nAfgesloten.")
            sys.exit(0)

        if choice in ("1", "datumprikker", "datum"):
            print("\n--- Datumprikker Autofiller geselecteerd ---")
            run_datumprikker()
            break
        elif choice in ("2", "timeful", "time"):
            print("\n--- Timeful Autofiller geselecteerd ---")
            run_timeful()
            break
        elif choice in ("3", "q", "quit", "exit", "stop"):
            print("Programma afgesloten.")
            sys.exit(0)
        else:
            print("Ongeldige keuze. Kies 1 voor Datumprikker, 2 voor Timeful, of 3 om af te sluiten.")


if __name__ == "__main__":
    main_menu()
