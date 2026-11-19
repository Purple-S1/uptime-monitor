# Uptime Monitor 📡

Gevorderd project (VS09) voor het keuzedeel *Verdieping software* van Sven Teuben.

Een monitoringapplicatie die elke 30 seconden controleert of een aantal websites bereikbaar is en hoe snel ze reageren. De resultaten worden opgeslagen in een database en getoond in een Grafana-dashboard en op een eenvoudige statuspagina. Is een website trager dan 1000 ms, dan wordt hij oranje ("TRAAG"); reageert hij niet, dan rood ("DOWN").

Het idee is hetzelfde als bij professionele monitoringsystemen, zoals BlueRaven van Purple Q dat temperatuur en luchtvochtigheid bewaakt: regelmatig meten, opslaan, tonen en waarschuwen bij een grenswaarde.

## Hoe het werkt

```
                 ┌──────────────┐  elke 30 s   ┌──────────────────┐
  websites  ◄────┤   checker    │─────────────►│  db (PostgreSQL) │
  (internet)     │   (Python)   │   INSERT     │  volume: db-data │
                 └──────────────┘              └────────┬─────────┘
                                                        │ SELECT
                              ┌─────────────────────────┼─────────────────┐
                              ▼                                           ▼
                     ┌──────────────────┐                      ┌────────────────────┐
  browser ──8000──►  │ web (Flask +     │      browser ─3000─► │ grafana (dashboard)│
                     │ Gunicorn)        │                      │ volume: grafana-data│
                     └──────────────────┘                      └────────────────────┘
```

| Container | Wat doet hij? | Poort |
|---|---|---|
| `db` | PostgreSQL-database met alle metingen | geen (alleen intern) |
| `checker` | Python-programma dat de websites controleert | geen |
| `web` | Statuspagina met de laatste status per website | 8000 |
| `grafana` | Dashboard met grafieken | 3000 |

## Starten

Je hebt alleen Docker Desktop nodig.

```bash
cp .env.example .env        # daarna eigen wachtwoorden invullen in .env
docker compose up -d --build
```

- Statuspagina: <http://localhost:8000>
- Grafana-dashboard: <http://localhost:3000> (bekijken kan zonder inloggen)

## Handige commando's

```bash
docker compose ps                         # welke containers draaien er?
docker compose logs -f checker            # live meekijken met de checker
docker compose run --rm checker pytest -v # de tests uitvoeren
docker compose down                       # alles stoppen (data blijft bewaard)
docker compose down -v                    # alles stoppen én de data wissen
```

## Websites aanpassen

De lijst staat in `config/websites.txt` (één per regel: `naam | adres`). Na het aanpassen:

```bash
docker compose restart checker
```

`host.docker.internal` betekent: de Mac zelf, gezien vanuit een container. Zo kan de checker ook het voorbeeldproject [hallo-docker](https://github.com/Purple-S1/hallo-docker) op poort 8080 controleren.

## Belangrijke keuzes

- **Wachtwoorden in `.env`**, en dat bestand staat in `.gitignore`. Op GitHub staat alleen `.env.example`.
- **Volumes** (`db-data`, `grafana-data`) zodat metingen bewaard blijven na `docker compose down`.
- **Healthchecks**: de checker, web en Grafana starten pas als de database echt klaar is.
- **Twee netwerken**: de database zit alleen in het `backend`-netwerk en heeft geen poort naar buiten.
- **`restart: unless-stopped`** en opnieuw verbinden in de checker, zodat het systeem een herstart van de database overleeft.
- **Gunicorn** in plaats van de testserver van Flask.
- **Geen root**: de eigen containers draaien als gewone gebruiker.

## Mappenstructuur

```
uptime-monitor/
├── docker-compose.yml         # alle diensten, netwerken en volumes
├── .env.example               # voorbeeld van de instellingen
├── config/websites.txt        # welke websites gecontroleerd worden
├── db/init.sql                # maakt de tabel 'checks' aan
├── checker/                   # Python-checker + tests (pytest)
├── web/                       # statuspagina (Flask + Gunicorn)
└── grafana/provisioning/      # datasource en dashboard, automatisch geladen
```
