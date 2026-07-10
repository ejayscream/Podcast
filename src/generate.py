"""Recherche + Skript-Erstellung via OpenAI.

Zwei Stufen:
  1) research()      -> tagesaktuelle Recherche (Responses API + web_search)
  2) write_script()  -> daraus ein sendefertiges Solo-Skript (strenges JSON)
"""
from __future__ import annotations

import json

from openai import OpenAI


def research(client: OpenAI, cfg: dict, seed: str, date_iso: str) -> str:
    """Lässt das Modell die wichtigsten/viralsten KI-Themen von heute recherchieren."""
    n = cfg["content"]["topics_per_episode"]
    prompt = f"""Heutiges Datum: {date_iso}.

Du bist Rechercheur für einen anspruchsvollen deutschen KI-Podcast.
Unten stehen frische Feed-Einträge als Ausgangspunkt. Nutze Web-Suche, um die
{n} lohnendsten Themen für heute zu finden und zu vertiefen.

Auswahlkriterien (in dieser Priorität):
1. Bringt den Hörer technisch weiter (Konzept, Methode, Tool, Technik).
2. Ist gerade viral / stark diskutiert in der KI-Community.
3. Praktischer Anwendungsnutzen – neue Tools, Verbesserungen, Anwendungsbereiche.
Meide reine PR-Meldungen und oberflächliche News.

Für JEDES gewählte Thema liefere:
- Worum es geht (präzise, keine Buzzwords)
- Warum es JETZT relevant ist
- Die technischen Details / das Kernkonzept, das man verstehen sollte
- Konkrete praktische Implikation oder Anwendung
- 2–4 belastbare Quellen (URL)

FEED-EINTRÄGE ALS AUSGANGSPUNKT:
{seed}

Gib strukturierte, faktendichte Recherchenotizen zurück (kein Fließtext-Skript)."""

    resp = client.responses.create(
        model=cfg["openai"]["research_model"],
        tools=[{"type": "web_search"}],
        input=prompt,
    )
    return resp.output_text


def write_script(client: OpenAI, cfg: dict, notes: str, date_iso: str) -> dict:
    """Verwandelt Recherchenotizen in ein sendefertiges Skript (JSON)."""
    minutes = cfg["content"]["target_minutes"]
    wpm = cfg["content"]["words_per_minute"]
    target_words = minutes * wpm
    style = cfg["content"]["language_style"]
    audience = cfg["content"]["audience"]

    system = f"""Du schreibst das Skript für eine Solo-Folge eines täglichen KI-Podcasts.

Stil & Sprache: {style}.
Zielgruppe: {audience}
Länge: ca. {minutes} Minuten Sprechzeit (~{target_words} Wörter).

Anforderungen an das Skript (Feld "script"):
- Reiner Sprechtext, den eine TTS-Stimme 1:1 vorliest. KEINE Regieanweisungen,
  keine Zwischenüberschriften, keine Aufzählungszeichen, keine Emojis, keine URLs vorlesen.
- Natürliche gesprochene Sprache, ganze Sätze, sinnvolle Absätze (Absatz = Sprechpause).
- Kurzer Begrüßungs-Opener mit Datum, dann pro Thema ein echter Deep Dive
  (Konzept erklären, warum es zählt, technisches Detail, praktische Anwendung),
  am Ende ein knapper Ausblick/Abschluss.
- Fachbegriffe im englischen Original, aber auf Deutsch erklärt.
- Substanz statt Hype. Der Hörer soll danach wirklich etwas Neues verstanden haben.

Gib AUSSCHLIESSLICH gültiges JSON zurück, exakt dieses Schema:
{{
  "title": "prägnanter Folgentitel (max ~70 Zeichen)",
  "subtitle": "ein Satz Teaser",
  "description": "2–4 Sätze Shownotes-Beschreibung, nennt die Themen",
  "tags": ["3-6", "schlagworte"],
  "sources": ["https://...", "https://..."],
  "script": "der komplette Sprechtext"
}}"""

    user = f"Datum: {date_iso}\n\nRECHERCHENOTIZEN:\n{notes}"

    resp = client.chat.completions.create(
        model=cfg["openai"]["writer_model"],
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    data = json.loads(resp.choices[0].message.content)

    # Minimalvalidierung
    for field in ("title", "description", "script"):
        if not data.get(field):
            raise ValueError(f"Skript-JSON unvollständig: Feld '{field}' fehlt.")
    data.setdefault("subtitle", "")
    data.setdefault("tags", [])
    data.setdefault("sources", [])
    return data
