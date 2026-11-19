"""Tests voor de checker. Uitvoeren: docker compose run --rm checker pytest -v"""
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from checker import controleer, lees_websites


class NepServer(BaseHTTPRequestHandler):
    """Kleine webserver voor de tests: /ok geeft 200, /fout geeft 500."""

    def do_GET(self):
        self.send_response(200 if self.path == "/ok" else 500)
        self.end_headers()

    def log_message(self, *args):
        pass  # geen logregels tijdens de tests


@pytest.fixture(scope="module")
def server():
    httpd = HTTPServer(("127.0.0.1", 0), NepServer)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{httpd.server_port}"
    httpd.shutdown()


def test_websites_bestand_lezen(tmp_path):
    bestand = tmp_path / "websites.txt"
    bestand.write_text("# commentaar\nGoogle | https://www.google.com\n\nTest|http://test.local\n")
    assert lees_websites(bestand) == [
        ("Google", "https://www.google.com"),
        ("Test", "http://test.local"),
    ]


def test_bereikbare_website_is_up(server):
    up, code, ms, fout = controleer(server + "/ok")
    assert up is True
    assert code == 200
    assert ms >= 0
    assert fout is None


def test_serverfout_is_down(server):
    up, code, ms, fout = controleer(server + "/fout")
    assert up is False
    assert code == 500


def test_onbereikbare_website_is_down():
    up, code, ms, fout = controleer("http://127.0.0.1:1")
    assert up is False
    assert code is None
    assert fout == "ConnectionError"
