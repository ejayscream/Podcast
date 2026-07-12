"""Recherche + Skript-Erstellung via OpenAI.

Zwei Stufen:
  1) research()      -> tagesaktuelle Recherche (Responses API + web_search)
  2) write_script()  -> daraus ein sendefertiges Solo-Skript (strenges JSON)
"""
from __future__ import annotations

import json

from openai import OpenAI


def research(client: OpenAI, cfg: dict, seed: str, date_iso: str, avoid: str = "") -> str:
    """Lässt das Modell die wichtigsten/viralsten KI-Themen von heute recherchieren."""
    n = cfg["content"]["topics_per_episode"]

    avoid_block = ""
    if avoid.strip():
        avoid_block = f"""

BEREITS BEHANDELT – NICHT WIEDERHOLEN:
Die folgenden Themen kamen in den letzten Folgen schon vor. Wähle sie NICHT
erneut. Ein Thema darf nur dann wieder auftauchen, wenn es eine echte,
substanzielle neue Entwicklung dazu gibt (nicht nur, weil es weiter trending ist) –
und dann mit klarem Fokus auf das Neue.
{avoid}
"""

    prompt = f"""Heutiges Datum: {date_iso}.

Du bist Rechercheur für einen praxisorientierten deutschen KI-Podcast.
Der Hörer ist IT-Systemadmin, IT-Lead und KI-Consultant – Anwender und
Implementierer, KEIN Programmierer/Modellentwickler. Er will am Zahn der Zeit
sein, um zu erkennen, WO er neue KI-Tools/Projekte im Beruf (IT-Betrieb,
Beratung, Team, Automatisierung) und privat einsetzen kann.

Nutze Web-Suche und orientiere dich am Stil und den Themen von tldr.tech
(tldr.tech/ai) – kompakt, praxisnah, tool- und anwendungsgetrieben. Ziehe
außerdem gerade trending Projekte heran (z.B. GitHub Trending, Product Hunt,
neue Tool-/Feature-Launches). Wähle die {n} für heute relevantesten Themen.

Auswahlkriterien (in dieser Priorität):
1. PRAKTISCHER NUTZEN / echter Impact – was machen Leute damit, das wirklich
   etwas verändert? (nicht: technische Neuheit um ihrer selbst willen)
2. Gerade trending / breit diskutiert / frisch gelauncht.
3. Konkret integrierbar für einen IT-Profi & Anwender (Beruf oder privat).
MEIDE: reine Forschungspaper, Modelltraining-/Mathematik-Details, PR-Geblubber.
{avoid_block}
Für JEDES gewählte Thema liefere:
- Worum es geht – verständlich, in einem Satz auf den Punkt
- Warum es JETZT relevant/trending ist
- Was Leute KONKRET damit machen (echte Anwendungsfälle, Beispiele, Impact)
- Wie ein IT-Lead/KI-Consultant ODER Privatanwender es einsetzen/integrieren
  könnte (konkrete Einsatzideen)
- Reifegrad/Aufwand: fertig nutzbar, Beta, Self-Hosting nötig, Kosten? (grob)
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
    max_minutes = cfg["content"].get("max_minutes", minutes + 2)
    wpm = cfg["content"]["words_per_minute"]
    target_words = minutes * wpm
    max_words = max_minutes * wpm
    topics = cfg["content"]["topics_per_episode"]
    style = cfg["content"]["language_style"]
    audience = cfg["content"]["audience"]

    system = f"""Du schreibst das Skript für eine Solo-Folge eines KI-Podcasts (erscheint 2×/Woche).

Stil & Sprache: {style}.
Zielgruppe: {audience}
Länge: ca. {minutes} Minuten Sprechzeit (~{target_words} Wörter).
HARTE OBERGRENZE: NIEMALS länger als {max_minutes} Minuten bzw. {max_words} Wörter.
Lieber je Thema knapper als diese Grenze reißen.

Umfang: {topics} Themen, alle gleichwertig und KOMPAKT behandelt (im Schnitt
rund {round(minutes / topics, 1)} Minuten pro Thema). Bewusst mehr Breite,
weniger Tiefe je Thema – kein einzelnes Thema ausufern lassen.

Redaktioneller Fokus: PRAXIS und ANWENDUNG, nicht Technik-Tiefe. Der Hörer will
wissen, was ein Tool/Projekt kann, was es bringt und wo ER es einsetzen könnte –
nicht, wie es intern funktioniert. Solide Einordnung zum Mitreden und Entscheiden,
aber niemals Forschungs-, Mathematik- oder Coding-Ebene.

Aufbau JEDES Themas (kompakt, Format "Thema + so setzt du's ein"):
1. Was ist es – in einfachen Worten auf den Punkt.
2. Warum es gerade relevant/trending ist.
3. Was Leute konkret damit machen (echte Beispiele, echter Impact).
4. "So könntest du's einsetzen" – konkrete Einsatzideen für einen IT-Lead/
   KI-Consultant im Berufsalltag UND fürs Private/Produktivität.
5. Kurze ehrliche Einordnung: wie reif, wie viel Aufwand, für wen lohnt es sich.

Anforderungen an das Skript (Feld "script"):
- Reiner Sprechtext, den eine TTS-Stimme 1:1 vorliest. KEINE Regieanweisungen,
  keine Zwischenüberschriften, keine Aufzählungszeichen, keine Emojis, keine URLs vorlesen.
- Natürliche gesprochene Sprache, ganze Sätze, sinnvolle Absätze (Absatz = Sprechpause).
- Kurzer Begrüßungs-Opener mit Datum, dann die Themen wie oben, am Ende ein
  knapper Abschluss (z.B. was man heute mal ausprobieren könnte).
- Fachbegriffe im englischen Original, aber sofort auf Deutsch verständlich erklärt.
- Anwendernah und konkret statt abstrakt. Nach dem Hören soll klar sein:
  "Das ist es, das bringt es, DA könnte ich es nutzen."

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
