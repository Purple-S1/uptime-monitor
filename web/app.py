"""Statuspagina: laat de laatste status van elke website zien."""
import os

import psycopg
from flask import Flask, jsonify, render_template
from psycopg.rows import dict_row

DATABASE_URL = os.environ.get("DATABASE_URL", "")
# Grens voor "traag", net als een alarmgrens bij een temperatuurmeting
DREMPEL_MS = int(os.environ.get("DREMPEL_MS", "1000"))

app = Flask(__name__)

LAATSTE_STATUS = """
    SELECT DISTINCT ON (site)
        site, url, up, status_code, response_ms, error,
        checked_at AT TIME ZONE 'Europe/Amsterdam' AS checked_at
    FROM checks
    ORDER BY site, checked_at DESC
"""


def status_van(rij):
    """Bepaalt de status: down (geen antwoord of fout), traag (boven de drempel) of up."""
    if not rij["up"]:
        return "down"
    if rij["response_ms"] is not None and rij["response_ms"] > DREMPEL_MS:
        return "traag"
    return "up"


def haal_status():
    with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn:
        rijen = conn.execute(LAATSTE_STATUS).fetchall()
    for rij in rijen:
        rij["status"] = status_van(rij)
    return rijen


@app.route("/")
def home():
    rijen = haal_status()
    aantal_up = sum(rij["status"] != "down" for rij in rijen)
    return render_template("index.html", rijen=rijen, aantal_up=aantal_up, drempel=DREMPEL_MS)


@app.route("/api/status")
def api_status():
    rijen = haal_status()
    for rij in rijen:
        rij["checked_at"] = rij["checked_at"].isoformat()
    return jsonify(rijen)


@app.route("/health")
def health():
    """Controleert of de statuspagina én de database werken."""
    try:
        with psycopg.connect(DATABASE_URL, connect_timeout=2) as conn:
            conn.execute("SELECT 1")
        return jsonify(status="ok", database="ok")
    except psycopg.OperationalError:
        return jsonify(status="fout", database="niet bereikbaar"), 503
