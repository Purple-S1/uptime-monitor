-- Wordt één keer uitgevoerd als de database voor het eerst start (lege volume).
-- Tabel met het resultaat van elke controle van een website.
CREATE TABLE IF NOT EXISTS checks (
    id          SERIAL PRIMARY KEY,
    site        TEXT        NOT NULL,              -- naam van de website, bijv. 'GitHub'
    url         TEXT        NOT NULL,              -- adres dat is gecontroleerd
    checked_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    up          BOOLEAN     NOT NULL,              -- bereikbaar ja/nee
    status_code INTEGER,                           -- HTTP-statuscode, leeg als er geen antwoord kwam
    response_ms INTEGER,                           -- reactietijd in milliseconden
    error       TEXT                               -- soort fout als de website niet bereikbaar was
);

-- Index zodat "laatste status per website" snel opgezocht kan worden
CREATE INDEX IF NOT EXISTS idx_checks_site_time ON checks (site, checked_at DESC);
