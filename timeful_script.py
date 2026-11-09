import datetime
import time
from urllib.parse import urlparse
import update_dependencies
update_dependencies.update_dependencies()

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import config
from config import NAAM, EMAIL
from calendar_integration import get_calendar_events, check_conflict, LOCAL_TZ
from browser_utils import get_driver
from parser import ask_custom_time_window


def check_day_conflict(day_date, events, local_tz, time_window=None):
    """
    Controleert of een specifieke dag (day_date) een conflict heeft in Google Calendar.
    day_date: datetime.date of datetime.datetime object.
    events: lijst met Google Calendar events.
    local_tz: pytz timezone.
    time_window: optionele tuple (datetime.time, datetime.time) voor een specifiek tijdvenster (bijv. 19:00 - 21:00).
    """
    if isinstance(day_date, datetime.datetime):
        day_date = day_date.date()

    if time_window:
        t_start, t_end = time_window
        day_start = local_tz.localize(datetime.datetime(day_date.year, day_date.month, day_date.day, t_start.hour, t_start.minute, 0))
        day_end = local_tz.localize(datetime.datetime(day_date.year, day_date.month, day_date.day, t_end.hour, t_end.minute, 0))
    else:
        day_start = local_tz.localize(datetime.datetime(day_date.year, day_date.month, day_date.day, 0, 0, 0))
        day_end = local_tz.localize(datetime.datetime(day_date.year, day_date.month, day_date.day, 23, 59, 59))

    date_str = day_date.strftime("%Y-%m-%d")

    for event in events:
        start_dict = event.get('start', {})
        end_dict = event.get('end', {})

        # 1. Hele dag afspraak ('date' veld, bijv. '2026-10-22')
        if 'date' in start_dict:
            ev_start_date = start_dict.get('date')
            ev_end_date = end_dict.get('date', ev_start_date)
            # Google Calendar all-day afspraken hebben end.date als de dag erna (exclusief)
            if ev_start_date <= date_str < ev_end_date:
                return True

        # 2. Afspraak met specifieke tijden ('dateTime' veld)
        elif 'dateTime' in start_dict:
            ev_start_str = start_dict.get('dateTime')
            ev_end_str = end_dict.get('dateTime')
            if ev_start_str and ev_end_str:
                try:
                    ev_start = datetime.datetime.fromisoformat(ev_start_str.replace('Z', '+00:00'))
                    ev_end = datetime.datetime.fromisoformat(ev_end_str.replace('Z', '+00:00'))
                    if ev_start.tzinfo is None:
                        ev_start = local_tz.localize(ev_start)
                    if ev_end.tzinfo is None:
                        ev_end = local_tz.localize(ev_end)

                    # Overlap met de dag
                    if (day_start < ev_end) and (day_end > ev_start):
                        return True
                except Exception:
                    continue

    return False


def _extract_timeful_event_info(driver):
    """
    Haalt de event-gegevens (naam, datums, type, tijden) op vanuit de Timeful pagina.
    """
    js_code = """
    var callback = arguments[arguments.length - 1];

    async function loadInfo() {
        try {
            var pathParts = window.location.pathname.split('/').filter(Boolean);
            var eventId = pathParts[pathParts.length - 1] || "";
            var sanitizedId = eventId.replace(/\\./g, '');

            var event = null;

            // 1. Probeer de Timeful REST API aan te roepen (altijd up-to-date en compleet)
            if (sanitizedId) {
                try {
                    var resp = await fetch('/api/events/' + sanitizedId, { credentials: 'include' });
                    if (resp.ok) {
                        event = await resp.json();
                    }
                } catch (e) {
                    console.log("Fetch API error:", e);
                }
            }

            // 2. Fallback: Zoek in Vue componenten op de pagina
            if (!event) {
                var rootEl = document.querySelector('#app') || document.querySelector('.v-application') || document.body;
                var rootVue = rootEl ? rootEl.__vue__ : null;

                function findComp(vm, predicate) {
                    if (!vm) return null;
                    if (predicate(vm)) return vm;
                    if (vm.$children) {
                        for (var i = 0; i < vm.$children.length; i++) {
                            var r = findComp(vm.$children[i], predicate);
                            if (r) return r;
                        }
                    }
                    return null;
                }

                var eventComp = rootVue ? findComp(rootVue, function(vm) { return vm.event && vm.event.dates; }) : null;
                if (eventComp && eventComp.event) {
                    event = eventComp.event;
                }
            }

            if (!event) {
                callback({ error: "Kon Timeful event niet vinden op de pagina." });
                return;
            }

            callback({
                success: true,
                eventId: event._id || sanitizedId,
                shortId: event.shortId || sanitizedId,
                name: event.name || "Timeful Poll",
                daysOnly: !!event.daysOnly,
                dates: event.dates || [],
                hasSpecificTimes: !!event.hasSpecificTimes,
                times: event.times || null,
                timeIncrement: event.timeIncrement || 15,
                duration: event.duration || 0,
                type: event.type || "specific_dates"
            });
        } catch (err) {
            callback({ error: err.toString() });
        }
    }

    loadInfo();
    """
    return driver.execute_async_script(js_code)


def _submit_timeful_availability(driver, sanitized_id, name, email, available_timestamps):
    """
    Slaat de beschikbaarheid direct op via de Timeful backend response API,
    werkt localStorage bij en triggert een pagina/Vue refresh.
    """
    js_code = """
    var callback = arguments[arguments.length - 1];
    var sanitizedId = arguments[0];
    var name = arguments[1];
    var email = arguments[2];
    var availableTimestamps = arguments[3];

    async function submit() {
        try {
            // 1. Haal event info op om event._id te hebben
            var eventResp = await fetch('/api/events/' + sanitizedId, { credentials: 'include' });
            var eventData = eventResp.ok ? await eventResp.json() : null;
            var longId = (eventData && eventData._id) ? eventData._id : sanitizedId;

            // 2. Sla guestName op in localStorage zodat Timeful direct weet wie de gebruiker is
            if (longId) {
                localStorage[longId + '.guestName'] = name;
            }
            localStorage[sanitizedId + '.guestName'] = name;

            // 3. Verstuur beschikbaarheid naar de backend response endpoint
            var payload = {
                guest: true,
                name: name,
                email: email,
                availability: availableTimestamps,
                ifNeeded: []
            };

            var postResp = await fetch('/api/events/' + sanitizedId + '/response', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include',
                body: JSON.stringify(payload)
            });

            if (!postResp.ok) {
                var errText = await postResp.text();
                callback({ ok: false, error: "HTTP " + postResp.status + ": " + errText });
                return;
            }

            // 4. Update Vue component of herlaad de pagina zodat de ingevulde gegevens direct zichtbaar zijn
            var rootEl = document.querySelector('#app') || document.querySelector('.v-application') || document.body;
            function findCompWithRefresh(vm) {
                if (!vm) return null;
                if (typeof vm.refreshEvent === 'function') return vm;
                if (vm.$children) {
                    for (var i = 0; i < vm.$children.length; i++) {
                        var r = findCompWithRefresh(vm.$children[i]);
                        if (r) return r;
                    }
                }
                return null;
            }

            var evComp = rootEl && rootEl.__vue__ ? findCompWithRefresh(rootEl.__vue__) : null;
            if (evComp && evComp.refreshEvent) {
                await evComp.refreshEvent();
                if (evComp.scheduleOverlapComponent && evComp.scheduleOverlapComponent.stopEditing) {
                    evComp.scheduleOverlapComponent.stopEditing();
                }
            } else {
                window.location.reload();
            }

            callback({ ok: true });
        } catch (err) {
            callback({ ok: false, error: err.toString() });
        }
    }

    submit();
    """
    return driver.execute_async_script(js_code, sanitized_id, name, email, available_timestamps)


def run_timeful(url=None):
    target_url = url or getattr(config, "TIMEFUL_URL", None)
    if not target_url or "YOUR_LINK_HERE" in target_url:
        print("\nGeen geldige Timeful link gevonden in config.py.")
        entered = input("Voer de Timeful URL in (bijv. https://timeful.app/e/...): ").strip()
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

    # Haal ID uit URL
    parsed_path = urlparse(target_url).path.strip('/')
    parts = parsed_path.split('/')
    raw_event_id = parts[-1] if parts else ""
    sanitized_id = raw_event_id.replace('.', '')

    print("\nAgenda-afspraken ophalen uit Google Calendar...")
    events = get_calendar_events()

    browser_pref = getattr(config, "BROWSER", "auto")
    driver = get_driver(browser_pref)
    wait = WebDriverWait(driver, 20)

    try:
        print(f"Navigeren naar {target_url}...")
        driver.get(target_url)

        # 1. Wachten tot applicatie geladen is
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#app, .v-application")))
        time.sleep(2)

        # 2. Cookies banner wegklikken indien aanwezig
        try:
            close_buttons = driver.find_elements(By.CSS_SELECTOR, "button[class*='tw-text-gray-400'], button.close")
            for btn in close_buttons:
                if btn.is_displayed():
                    btn.click()
                    break
        except Exception:
            pass

        # 3. Event info ophalen
        print("Timeful event details ophalen...")
        info = _extract_timeful_event_info(driver)

        if not info or not info.get("success"):
            err = info.get("error", "Onbekende fout") if info else "Geen respons van pagina"
            print(f"Wachten op laden van pagina: {err}...")
            time.sleep(3)
            info = _extract_timeful_event_info(driver)

        if not info or not info.get("success"):
            raise RuntimeError(f"Kon event-opties niet laden: {info.get('error') if info else 'Onbekend'}")

        poll_name = info.get("name", "Timeful Poll")
        is_days_only = info.get("daysOnly", False)
        event_dates = info.get("dates", [])
        time_increment = info.get("timeIncrement", 15)

        print(f"\nPoll gevonden: '{poll_name}'")
        print(f"Type: {'Dagen-alleen (daysOnly)' if is_days_only else 'Datum en tijd sloten'}")
        print(f"Aantal voorgestelde datums: {len(event_dates)}")

        available_timestamps = []
        busy_count = 0
        available_count = 0

        # --- A. Dagen-alleen event (bijv. Ketmania) ---
        if is_days_only:
            time_window = ask_custom_time_window()
            if time_window:
                w_str = f"{time_window[0].strftime('%H:%M')} tot {time_window[1].strftime('%H:%M')}"
                print(f"\nBeschikbaarheid controleren per dag binnen tijdvenster ({w_str})...")
            else:
                print("\nBeschikbaarheid controleren per dag (gehele dag 00:00 - 23:59)...")

            for date_iso in event_dates:
                # date_iso is bijv. "2026-10-22T00:00:00Z"
                try:
                    dt = datetime.datetime.fromisoformat(date_iso.replace('Z', '+00:00'))
                    local_dt = dt.astimezone(LOCAL_TZ)

                    is_busy = check_day_conflict(local_dt.date(), events, LOCAL_TZ, time_window=time_window)
                    day_formatted = local_dt.strftime("%A %d-%m-%Y")

                    if is_busy:
                        busy_count += 1
                        print(f"  [X] {day_formatted}: Bezet")
                    else:
                        available_count += 1
                        print(f"  [V] {day_formatted}: Beschikbaar")
                        available_timestamps.append(date_iso)
                except Exception as e:
                    print(f"Fout bij verwerken van datum {date_iso}: {e}")

        # --- B. Tijd-gebaseerd event ---
        else:
            print(f"\nTijdsloten controleren (stappen van {time_increment} min)...")
            start_hour = 9
            end_hour = 17

            # Indien specifieke tijden zijn ingesteld in het event
            times_list = info.get("times")
            if times_list and len(times_list) >= 2:
                try:
                    t0 = times_list[0]
                    t1 = times_list[1]
                    if isinstance(t0, str):
                        t_start = datetime.datetime.fromisoformat(t0.replace('Z', '+00:00'))
                        start_hour = t_start.hour
                    if isinstance(t1, str):
                        t_end = datetime.datetime.fromisoformat(t1.replace('Z', '+00:00'))
                        end_hour = t_end.hour
                    if end_hour <= start_hour:
                        end_hour = 24
                except Exception:
                    pass

            for date_iso in event_dates:
                dt_day = datetime.datetime.fromisoformat(date_iso.replace('Z', '+00:00')).astimezone(LOCAL_TZ)
                year, month, day = dt_day.year, dt_day.month, dt_day.day

                curr_dt = LOCAL_TZ.localize(datetime.datetime(year, month, day, start_hour, 0, 0))
                end_dt_day = LOCAL_TZ.localize(datetime.datetime(year, month, day, end_hour, 0, 0))

                delta = datetime.timedelta(minutes=time_increment)
                while curr_dt < end_dt_day:
                    slot_end = curr_dt + delta
                    is_busy = check_conflict(curr_dt, slot_end, events)

                    slot_utc = curr_dt.astimezone(datetime.timezone.utc)
                    slot_iso = slot_utc.strftime("%Y-%m-%dT%H:%M:%S.000Z")

                    if is_busy:
                        busy_count += 1
                    else:
                        available_count += 1
                        available_timestamps.append(slot_iso)

                    curr_dt = slot_end

        print(f"\nResultaat: {available_count} beschikbaar, {busy_count} bezet.")

        # 4. Opslaan in Timeful
        print(f"Beschikbaarheid insturen voor {name} ({email})...")
        save_result = _submit_timeful_availability(
            driver,
            sanitized_id=sanitized_id,
            name=name,
            email=email,
            available_timestamps=available_timestamps
        )

        if save_result.get("ok"):
            print("Beschikbaarheid succesvol opgeslagen in Timeful!")
            # Pagina herladen zodat de wijzigingen fris op het scherm staan
            time.sleep(1)
            driver.refresh()
            print("Pagina vernieuwd: controleer je ingevulde beschikbaarheid.")
        else:
            err_msg = save_result.get("error", "Onbekende fout")
            print(f"Let op bij opslaan: {err_msg}")

        print("\nAgent is klaar met invullen van Timeful. Controleer de pagina.")

    finally:
        input("\nKlaar? Druk op Enter om de browser te sluiten...")
        try:
            driver.quit()
        except Exception:
            pass


if __name__ == "__main__":
    run_timeful()
