# 🏠 EBM München Wohnungs-Watcher

Schickt dir eine **Push-Benachrichtigung aufs Handy**, sobald auf
<https://ebm-muenchen.de/mietangebote> neue Mietangebote erscheinen.
Läuft kostenlos alle ~10 Minuten auf GitHub – dein Handy/Laptop muss nicht an sein.

## Einrichtung (ca. 5 Minuten)

### 1. ntfy-App installieren
- iPhone: App Store → **ntfy**
- Android: Play Store / F-Droid → **ntfy**

In der App auf **+** tippen und ein Topic abonnieren. Nimm einen **langen,
zufälligen Namen**, den niemand errät, z. B. `ebm-adrian-x7k29qpl`
(jeder, der den Namen kennt, kann mitlesen).

### 2. GitHub-Repo anlegen
1. Auf github.com einloggen → **New repository** → Name z. B. `ebm-watcher`,
   **Public** wählen (bei öffentlichen Repos sind GitHub Actions unbegrenzt kostenlos;
   dein Topic bleibt trotzdem geheim, weil es als Secret gespeichert wird).
2. **Add file → Upload files** → `watcher.py` und `README.md` hochladen → Commit.
3. **Add file → Create new file** → als Dateinamen exakt
   `.github/workflows/watch.yml` eintippen (die Schrägstriche legen die Ordner an)
   und den Inhalt von `watch.yml` aus dem ZIP hineinkopieren → Commit.
   (Der Ordner `.github` ist auf Mac/iPhone versteckt, darum dieser Weg.)

### 4. Topic als Secret hinterlegen
Repo → **Settings → Secrets and variables → Actions → New repository secret**
- Name: `NTFY_TOPIC`
- Wert: dein Topic-Name aus Schritt 1

### 5. Testen
Repo → **Actions** → (falls gefragt: Workflows aktivieren) →
**EBM Wohnungs-Watcher → Run workflow** → Haken bei „Nur Test-Push senden“ → Run.
Nach ~30 Sekunden sollte eine Push kommen. Danach einmal ohne Haken laufen
lassen – dann kommt „EBM-Watcher ist aktiv“. Ab jetzt läuft alles automatisch.

## Mit Freunden teilen
- **Einfachste Variante:** Freund installiert ntfy und abonniert **dasselbe Topic** –
  fertig, keine eigene Einrichtung nötig.
- **Eigene Instanz:** Freund lädt diesen Ordner in ein eigenes Repo und macht
  Schritte 1–5 mit eigenem Topic.

## Wie es funktioniert
`watcher.py` lädt die Seite, merkt sich in `state.json`, ob der Hinweis
„keine aktuellen Angebote“ da ist und welche Angebots-Unterseiten verlinkt sind.
Verschwindet der Hinweis oder taucht ein neuer Link auf → Push (Tippen öffnet die Seite).

## Hinweise
- GitHub-Zeitpläne laufen nicht sekundengenau, meist alle 10–15 Minuten.
- Das Skript macht automatisch alle 30 Tage einen kleinen Commit, damit GitHub
  den Zeitplan nicht wegen Inaktivität pausiert.
- Lokal testen: `NTFY_TOPIC=dein-topic python3 watcher.py --test`
