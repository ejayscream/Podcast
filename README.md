# KI Daily – vollautomatischer täglicher KI-Podcast

Erzeugt jeden Morgen automatisch eine 8–12-minütige Podcast-Folge über die
relevantesten KI-Themen und stellt sie als privaten Podcast-Feed bereit –
abonnierbar in Apple Podcasts. Kein manueller Eingriff nötig.

## Wie es funktioniert

```
Feeds (arXiv, HN, HF)            OpenAI Responses API + web_search
        │  Seed-Themen                    │ tagesaktuelle Recherche
        ▼                                 ▼
   src/sources.py ───────────────►  src/generate.py ──► Skript (Deutsch)
                                          │
                                          ▼
                                     src/tts.py  ──► MP3 (OpenAI TTS)
                                          │
                                          ▼
                                     src/feed.py ──► feed/podcast.xml
                                          │
                          GitHub Actions (03:00 UTC, täglich)
                                          │
                                     GitHub Pages
                                          │
                              Apple Podcasts (Abo per RSS)
                                          ▼
                              📱 morgens um 7 auf dem iPhone
```

## Projektstruktur

| Pfad | Zweck |
|------|-------|
| `config.yaml` | Alle Einstellungen (Titel, Stimme, Länge, Feeds, base_url) |
| `src/sources.py` | Seed-Themen aus RSS-Feeds |
| `src/generate.py` | Web-Recherche + Skript-Erstellung |
| `src/tts.py` | Text-to-Speech (MP3) |
| `src/feed.py` | Podcast-RSS-Feed bauen |
| `src/main.py` | Orchestrator (eine Folge erzeugen) |
| `.github/workflows/daily.yml` | Täglicher Cron-Job in der Cloud |
| `episodes/` | Erzeugte MP3s + Metadaten (committet) |
| `feed/podcast.xml` | Der abonnierbare Feed |
| `assets/cover.png` | Podcast-Cover (selbst hinzufügen) |

## Lokal testen (Windows / PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Key setzen (oder .env aus .env.example anlegen)
$env:OPENAI_API_KEY = "sk-..."

python src/main.py            # erzeugt die heutige Folge
python src/main.py --force    # überschreibt eine schon vorhandene Folge
```

Danach liegt `episodes/<datum>.mp3` und ein aktualisiertes `feed/podcast.xml` vor.

## Live schalten (4 Handgriffe)

1. **GitHub-Repo** anlegen (z. B. `ki-podcast`), diesen Ordner pushen.
2. In `config.yaml` `podcast.base_url` auf
   `https://<dein-user>.github.io/ki-podcast` setzen.
3. **Secret** `OPENAI_API_KEY` in GitHub hinterlegen
   (Settings → Secrets and variables → Actions).
4. **GitHub Pages** aktivieren (Settings → Pages → Source: „GitHub Actions").
5. **Cover** `assets/cover.png` (1400²–3000² px) hinzufügen.

Dann in Apple Podcasts:
**Mediathek → oben rechts (…) → „Sendung per URL hinzufügen"** →
`https://<dein-user>.github.io/ki-podcast/feed/podcast.xml`

## Kosten (grob)

- GitHub Actions + Pages: kostenlos (öffentliches Repo).
- OpenAI pro Folge: wenige Cent bis ~20–40 ct (Recherche + Skript + TTS),
  je nach gewählten Modellen. TTS ist der Hauptkostenpunkt.
