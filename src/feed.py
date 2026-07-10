"""Baut den Podcast-RSS-Feed (feed/podcast.xml) aus den Episoden-Metadaten.

Jede Episode liegt als episodes/<datum>.mp3 + episodes/<datum>.json vor.
Apple Podcasts / Overcast / etc. abonnieren die erzeugte podcast.xml.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path

from feedgen.feed import FeedGenerator

from utils import EPISODES_DIR, FEED_DIR


def _load_episodes() -> list[dict]:
    eps = []
    for meta_path in sorted(EPISODES_DIR.glob("*.json")):
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
        mp3 = EPISODES_DIR / f"{meta['date']}.mp3"
        if mp3.exists():
            meta["_bytes"] = mp3.stat().st_size
            eps.append(meta)
    # neueste zuerst
    eps.sort(key=lambda m: m["date"], reverse=True)
    return eps


def _fmt_duration(seconds: int) -> str:
    h, rem = divmod(int(seconds), 3600)
    m, s = divmod(rem, 60)
    return f"{h:d}:{m:02d}:{s:02d}" if h else f"{m:d}:{s:02d}"


def build_feed(cfg: dict) -> Path:
    p = cfg["podcast"]
    base = p["base_url"].rstrip("/")
    episodes = _load_episodes()

    fg = FeedGenerator()
    fg.load_extension("podcast")
    fg.title(p["title"])
    fg.link(href=base, rel="alternate")
    fg.link(href=f"{base}/feed/podcast.xml", rel="self")
    fg.description(p["description"])
    fg.language(p["language"])
    fg.author({"name": p["author"], "email": p["owner_email"]})
    fg.logo(f"{base}/{p['cover_image']}")
    fg.podcast.itunes_author(p["author"])
    fg.podcast.itunes_summary(p["description"])
    fg.podcast.itunes_subtitle(p.get("subtitle", ""))
    fg.podcast.itunes_owner(name=p["author"], email=p["owner_email"])
    fg.podcast.itunes_image(f"{base}/{p['cover_image']}")
    fg.podcast.itunes_category(p["category"])
    fg.podcast.itunes_explicit("yes" if p.get("explicit") else "no")

    for ep in episodes:
        audio_url = f"{base}/episodes/{ep['date']}.mp3"
        fe = fg.add_entry()
        fe.id(audio_url)
        fe.title(ep["title"])
        fe.description(ep.get("description", ""))
        fe.enclosure(audio_url, str(ep["_bytes"]), "audio/mpeg")
        pub = datetime.strptime(ep["date"], "%Y-%m-%d").replace(
            hour=5, minute=0, tzinfo=timezone.utc
        )
        fe.pubDate(format_datetime(pub))
        if ep.get("duration_seconds"):
            fe.podcast.itunes_duration(_fmt_duration(ep["duration_seconds"]))
        if ep.get("subtitle"):
            fe.podcast.itunes_subtitle(ep["subtitle"])
        fe.podcast.itunes_image(f"{base}/{p['cover_image']}")

    FEED_DIR.mkdir(parents=True, exist_ok=True)
    out = FEED_DIR / "podcast.xml"
    fg.rss_file(str(out), pretty=True)
    print(f"  ✓ Feed geschrieben: {out} ({len(episodes)} Folgen)")
    return out


if __name__ == "__main__":
    # Direktaufruf: Feed aus den vorhandenen Episoden neu bauen.
    # Praktisch, nachdem man Episode-Dateien manuell gelöscht hat.
    from utils import load_config

    build_feed(load_config())
