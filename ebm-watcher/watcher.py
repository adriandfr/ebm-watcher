#!/usr/bin/env python3
"""EBM München Wohnungs-Watcher.

Prüft https://ebm-muenchen.de/mietangebote und schickt per ntfy.sh eine
Push-Benachrichtigung, sobald neue Mietangebote erscheinen.
Nur Python-Standardbibliothek, keine Installation nötig.
"""
import datetime as dt
import hashlib
import json
import os
import sys
import urllib.request
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

URL = os.environ.get("WATCH_URL", "https://ebm-muenchen.de/mietangebote")
TOPIC = os.environ.get("NTFY_TOPIC", "").strip()
NTFY_SERVER = os.environ.get("NTFY_SERVER", "https://ntfy.sh").rstrip("/")
STATE_FILE = os.environ.get("STATE_FILE", "state.json")
NO_OFFERS_PHRASE = "keine aktuellen angebote"
KEEPALIVE_DAYS = 30  # verhindert, dass GitHub den Zeitplan nach 60 Tagen pausiert


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = {}  # href -> Linktext
        self.text = []
        self._skip = 0
        self._href = None
        self._link_text = []

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript"):
            self._skip += 1
        elif tag == "a":
            self._href = dict(attrs).get("href")
            self._link_text = []

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript") and self._skip:
            self._skip -= 1
        elif tag == "a" and self._href:
            self.links[self._href] = " ".join("".join(self._link_text).split())
            self._href = None

    def handle_data(self, data):
        if self._skip:
            return
        self.text.append(data)
        if self._href is not None:
            self._link_text.append(data)


def fetch(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (EBM-Wohnungs-Watcher; privat)",
        "Accept-Language": "de-DE,de;q=0.9",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode(r.headers.get_content_charset() or "utf-8", "replace")


def analyse(html, base_url):
    p = PageParser()
    p.feed(html)
    text = " ".join(" ".join(p.text).split())
    base_path = urlparse(base_url).path.rstrip("/")
    offers = {}
    for href, label in p.links.items():
        full = urljoin(base_url, href).split("#")[0]
        u = urlparse(full)
        # Unterseiten wie /mietangebote/irgendwas = einzelne Angebote
        if u.netloc.endswith("ebm-muenchen.de") and u.path.rstrip("/").startswith(base_path + "/"):
            offers[full] = label or u.path.rsplit("/", 1)[-1]
    return {
        "no_offers_notice": NO_OFFERS_PHRASE in text.lower(),
        "offers": offers,
        "text_hash": hashlib.sha256(text.encode()).hexdigest()[:16],
    }


def notify(title, message, click=URL, tags="house"):
    if not TOPIC:
        print("WARN: NTFY_TOPIC fehlt – keine Push gesendet.")
        return
    body = json.dumps({"topic": TOPIC, "title": title, "message": message,
                       "click": click, "tags": [tags], "priority": 4}).encode()
    req = urllib.request.Request(NTFY_SERVER, data=body,
                                 headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req, timeout=20).read()
    print(f"Push gesendet: {title}")


def load_state():
    try:
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


def main():
    if "--test" in sys.argv:
        notify("Test: EBM-Watcher", "Wenn du das siehst, funktionieren die Pushs. 🎉")
        return
    try:
        cur = analyse(fetch(URL), URL)
    except Exception as e:  # Seite kurz down → einfach beim nächsten Lauf nochmal
        print(f"Abruf fehlgeschlagen: {e}")
        return

    old = load_state()
    today = dt.date.today().isoformat()
    print(f"Hinweis 'keine Angebote': {cur['no_offers_notice']} | Angebots-Links: {len(cur['offers'])}")

    if old is None:
        notify("EBM-Watcher ist aktiv",
               "Du bekommst ab jetzt eine Push, sobald auf ebm-muenchen.de neue Mietangebote erscheinen.")
        if cur["offers"] or not cur["no_offers_notice"]:
            notify("EBM: Es gibt gerade Angebote!", "Schau direkt nach – die Bewerbung läuft übers Formular.")
    else:
        new = {u: l for u, l in cur["offers"].items() if u not in old.get("offers", {})}
        if new:
            for u, label in list(new.items())[:5]:
                notify("🏠 Neue Wohnung bei EBM!", label or "Neues Mietangebot", click=u)
        elif old.get("no_offers_notice") and not cur["no_offers_notice"]:
            notify("🏠 EBM hat neue Mietangebote!",
                   "Der Hinweis 'keine Angebote' ist verschwunden – schnell nachschauen!")

    alive = (old or {}).get("alive", today)
    if (dt.date.today() - dt.date.fromisoformat(alive)).days >= KEEPALIVE_DAYS:
        alive = today
    save_state({**cur, "alive": alive if old else today})


if __name__ == "__main__":
    main()
