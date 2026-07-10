"""Seed-Themen aus RSS-Feeds ziehen (arXiv, HN, HF ...).

Diese Einträge dienen NICHT als fertiger Inhalt, sondern als Startpunkt,
damit die anschließende Web-Recherche weiß, was gerade frisch/relevant ist.
"""
from __future__ import annotations

import time
from dataclasses import dataclass

import feedparser


@dataclass
class SeedItem:
    source: str
    title: str
    summary: str
    link: str
    published: str

    def as_line(self) -> str:
        s = self.summary.strip().replace("\n", " ")
        if len(s) > 300:
            s = s[:300] + "…"
        return f"- [{self.source}] {self.title.strip()} — {s} ({self.link})"


def _clean(html: str) -> str:
    import re
    return re.sub(r"<[^>]+>", "", html or "").strip()


def fetch_seed_items(cfg: dict) -> list[SeedItem]:
    feeds = cfg["sources"]["feeds"]
    max_items = cfg["sources"]["max_seed_items"]
    items: list[SeedItem] = []

    for feed in feeds:
        try:
            parsed = feedparser.parse(feed["url"])
        except Exception as exc:  # Feed darf ausfallen, Podcast läuft weiter
            print(f"  ! Feed-Fehler {feed['name']}: {exc}")
            continue

        for entry in parsed.entries[:10]:
            items.append(
                SeedItem(
                    source=feed["name"],
                    title=getattr(entry, "title", "(kein Titel)"),
                    summary=_clean(getattr(entry, "summary", "")),
                    link=getattr(entry, "link", ""),
                    published=getattr(entry, "published", ""),
                )
            )
        print(f"  ✓ {feed['name']}: {len(parsed.entries)} Einträge")
        time.sleep(0.3)  # höflich zu den Servern

    # simple Dedup nach Titel
    seen: set[str] = set()
    unique: list[SeedItem] = []
    for it in items:
        key = it.title.lower().strip()
        if key not in seen:
            seen.add(key)
            unique.append(it)

    return unique[:max_items]


def seed_block(items: list[SeedItem]) -> str:
    if not items:
        return "(Keine Feed-Einträge verfügbar – recherchiere frei die wichtigsten KI-News von heute.)"
    return "\n".join(it.as_line() for it in items)
