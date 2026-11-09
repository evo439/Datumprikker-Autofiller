import datetime
import re


def parse_time_input(input_str):
    """
    Parseert tijd-invoer zoals '19:00 - 21:00', '1900-2100', '19-21', '19:30 - 22:00', '1900 - 2100'.
    Geeft een tuple (datetime.time, datetime.time) terug, of None als het niet herkend is.
    """
    if not input_str:
        return None

    cleaned = input_str.strip().lower()
    # Zoekt naar: (\d{1,2}) optioneel (:\d{2} of \d{2}) [scheidingsteken] (\d{1,2}) optioneel (:\d{2} of \d{2})
    match = re.search(r'(\d{1,2})(?::?(\d{2}))?\s*(?:-|tot|to)\s*(\d{1,2})(?::?(\d{2}))?', cleaned)
    if not match:
        return None

    h1 = int(match.group(1))
    m1 = int(match.group(2) or 0)
    h2 = int(match.group(3))
    m2 = int(match.group(4) or 0)

    if not (0 <= h1 <= 23 and 0 <= m1 <= 59 and 0 <= h2 <= 24 and 0 <= m2 <= 59):
        return None

    if h2 == 24 and m2 == 0:
        h2 = 23
        m2 = 59

    return datetime.time(h1, m1), datetime.time(h2, m2)


def ask_custom_time_window():
    """
    Vraagt de gebruiker of er voor een dagen-alleen poll een specifiek tijdvenster moet worden gebruikt.
    Geeft (start_time, end_time) terug of None (hele dag).
    """
    print("\n" + "=" * 55)
    print("ℹ Dit is een poll voor HELE DAGEN (days only).")
    print("Wil je je beschikbaarheid controleren op:")
    print("  1) De hele dag (00:00 - 23:59)")
    print("  2) Een specifiek tijdvenster (bijv. 's avonds 19:00 - 21:00)")
    print("=" * 55)

    while True:
        try:
            choice = input("Maak een keuze [1 of 2, standaard 1]: ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print("\nStandaard gekozen: hele dag.")
            return None

        if choice in ("", "1", "dag", "hele dag"):
            print("Controleren op de hele dag.")
            return None
        elif choice in ("2", "tijd", "tijdvenster", "custom"):
            while True:
                try:
                    time_inp = input("Voer het gewenste tijdvenster in (bijv. 19:00 - 21:00 of 1900-2100): ").strip()
                except (KeyboardInterrupt, EOFError):
                    print("\nStandaard gekozen: hele dag.")
                    return None

                parsed = parse_time_input(time_inp)
                if parsed:
                    t_start, t_end = parsed
                    print(f"Gekozen tijdvenster: {t_start.strftime('%H:%M')} tot {t_end.strftime('%H:%M')}")
                    return (t_start, t_end)
                else:
                    print("Ongeldig formaat. Voorbeelden: '19:00 - 21:00', '1900-2100', '19 - 21'.")
        else:
            print("Kies 1 voor de hele dag of 2 voor een specifiek tijdvenster.")


def parse_dutch_datumprikker_date(date_str, time_window=None):
    """
    Converteert een Datumprikker string naar een start- en eind-datetime object.
    Input format voorbeeld: "ma 12 mei 10:00 - 11:00", "maandag 12 mei 2026 14:00" of "maandag 12 mei 2026" (zonder tijd).
    Als time_window gegeven is en de datum heeft geen tijd, wordt dat tijdvenster toegepast.
    """
    # Mappings voor Nederlandse termen
    maanden = {
        'jan': 1, 'januari': 1,
        'feb': 2, 'februari': 2,
        'mrt': 3, 'maart': 3,
        'apr': 4, 'april': 4,
        'mei': 5,
        'jun': 6, 'juni': 6,
        'jul': 7, 'juli': 7,
        'aug': 8, 'augustus': 8,
        'sep': 9, 'september': 9,
        'okt': 10, 'oktober': 10,
        'nov': 11, 'november': 11,
        'dec': 12, 'december': 12
    }

    # Opschonen van de string
    date_str = date_str.lower().strip().replace(',', ' ')

    # Regex met optionele tijd:
    # [dagnummer] [maandnaam] [optioneel jaar] [optioneel starttijd] [optioneel eindtijd]
    pattern = r'(?P<dagnum>\d{1,2})\s+(?P<maand>\w+)\s*(?P<jaar>\d{4})?(?:\s+(?P<start>\d{1,2}:\d{2})\s*(?:-\s*(?P<eind>\d{1,2}:\d{2}))?)?'

    match = re.search(pattern, date_str)
    if not match:
        raise ValueError(f"Kon datum format niet herkennen: {date_str}")

    day = int(match.group('dagnum'))
    month_str = match.group('maand')
    month = maanden.get(month_str)

    if not month:
        raise ValueError(f"Onbekende maand: {month_str}")

    now = datetime.datetime.now()
    if match.group('jaar'):
        year = int(match.group('jaar'))
    else:
        year = now.year
        if month < now.month:
            year += 1

    start_time_str = match.group('start')
    if start_time_str:
        # Er is een specifieke tijd in de tekst
        start_dt = datetime.datetime.strptime(f"{year}-{month}-{day} {start_time_str}", "%Y-%m-%d %H:%M")
        if match.group('eind'):
            end_time_str = match.group('eind')
            end_dt = datetime.datetime.strptime(f"{year}-{month}-{day} {end_time_str}", "%Y-%m-%d %H:%M")
        else:
            end_dt = start_dt + datetime.timedelta(hours=1)
    else:
        # Dagen-alleen (geen tijdstip vermeld)
        if time_window:
            t_start, t_end = time_window
            start_dt = datetime.datetime(year, month, day, t_start.hour, t_start.minute, 0)
            end_dt = datetime.datetime(year, month, day, t_end.hour, t_end.minute, 0)
        else:
            start_dt = datetime.datetime(year, month, day, 0, 0, 0)
            end_dt = datetime.datetime(year, month, day, 23, 59, 59)

    return start_dt, end_dt
