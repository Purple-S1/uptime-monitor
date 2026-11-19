"""Uptime-checker: controleert websites en slaat het resultaat op in PostgreSQL."""
import os
import time

import psycopg
import requests

DATABASE_URL = os.environ.get("DATABASE_URL", "")
INTERVAL = int(os.environ.get("CHECK_INTERVAL", "60"))
TIMEOUT = float(os.environ.get("CHECK_TIMEOUT", "5"))
WEBSITES_FILE = os.environ.get("WEBSITES_FILE", "/config/websites.txt")


def lees_websites(pad):
    """Leest het bestand met websites. Elke regel: naam | adres. Regels met # zijn commentaar."""
    websites = []
    with open(pad, encoding="utf-8") as f:
        for regel in f:
            regel = regel.strip()
            if not regel or regel.startswith("#"):
                continue
            naam, url = (deel.strip() for deel in regel.split("|", 1))
            websites.append((naam, url))
    return websites


def controleer(url):
    """Doet één controle en geeft (up, statuscode, reactietijd_ms, fout) terug."""
    start = time.perf_counter()
    try:
        antwoord = requests.get(url, timeout=TIMEOUT)
        ms = round((time.perf_counter() - start) * 1000)
        return antwoord.status_code < 400, antwoord.status_code, ms, None
    except requests.RequestException as fout:
        # Geen antwoord: bijvoorbeeld ConnectionError of ReadTimeout
        return False, None, None, type(fout).__name__


def sla_op(conn, naam, url, resultaat):
    up, code, ms, fout = resultaat
    conn.execute(
        "INSERT INTO checks (site, url, up, status_code, response_ms, error) "
        "VALUES (%s, %s, %s, %s, %s, %s)",
        (naam, url, up, code, ms, fout),
    )
    conn.commit()


def verbind():
    """Maakt verbinding met de database en probeert het opnieuw zolang dat niet lukt."""
    while True:
        try:
            return psycopg.connect(DATABASE_URL, connect_timeout=5)
        except psycopg.OperationalError:
            print("Database niet bereikbaar, over 5 seconden opnieuw proberen...", flush=True)
            time.sleep(5)


def main():
    websites = lees_websites(WEBSITES_FILE)
    print(f"Checker gestart: {len(websites)} websites, elke {INTERVAL} seconden", flush=True)
    conn = verbind()
    while True:
        for naam, url in websites:
            resultaat = controleer(url)
            try:
                sla_op(conn, naam, url, resultaat)
            except psycopg.OperationalError:
                # Verbinding verbroken (bijv. database herstart): opnieuw verbinden
                # en deze meting nog een keer opslaan, zodat er niets verloren gaat.
                print("Verbinding met de database verbroken, opnieuw verbinden...", flush=True)
                conn.close()
                conn = verbind()
                sla_op(conn, naam, url, resultaat)
            status = "UP  " if resultaat[0] else "DOWN"
            ms = resultaat[2] if resultaat[2] is not None else "-"
            print(f"{status} {naam:<14} {ms:>5} ms  {resultaat[3] or ''}", flush=True)
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
