"""Orchestrator: eine Folge erzeugen und den Feed aktualisieren.

Ablauf:
  1) Seed-Themen aus Feeds
  2) Web-Recherche (OpenAI Responses + web_search)
  3) Skript schreiben (JSON)
  4) TTS -> MP3
  5) Metadaten speichern, Feed neu bauen, altes Archiv beschneiden
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from openai import OpenAI

import generate
import sources
from feed import build_feed
from tts import synthesize
from utils import (
    EPISODES_DIR,
    ensure_dirs,
    load_config,
    recent_topics_block,
    require_api_key,
    slugify,
    today_iso,
)


def prune_archive(cfg: dict) -> None:
    keep = cfg["archive"]["keep_last_episodes"]
    mp3s = sorted(EPISODES_DIR.glob("*.mp3"))
    for old in mp3s[:-keep] if len(mp3s) > keep else []:
        old.unlink(missing_ok=True)
        print(f"  ↳ Archiv beschnitten: {old.name} entfernt")


def run() -> int:
    cfg = load_config()
    ensure_dirs()
    api_key = require_api_key()
    client = OpenAI(api_key=api_key)

    date_iso = today_iso()
    mp3_path = EPISODES_DIR / f"{date_iso}.mp3"
    meta_path = EPISODES_DIR / f"{date_iso}.json"

    if mp3_path.exists() and "--force" not in sys.argv:
        print(f"Folge für {date_iso} existiert bereits. Nutze --force zum Überschreiben.")
        build_feed(cfg)
        return 0

    print(f"== KI-Podcast: Folge {date_iso} ==")

    print("[1/5] Seed-Themen aus Feeds ...")
    seed_items = sources.fetch_seed_items(cfg)
    seed = sources.seed_block(seed_items)

    print("[2/5] Web-Recherche ...")
    avoid = recent_topics_block(cfg["content"]["avoid_recent_episodes"], exclude_date=date_iso)
    if avoid:
        print(f"  ↳ meide Themen der letzten {len(avoid.splitlines())} Folge(n)")
    notes = generate.research(client, cfg, seed, date_iso, avoid=avoid)

    print("[3/5] Skript schreiben ...")
    script_data = generate.write_script(client, cfg, notes, date_iso)
    print(f"  Titel: {script_data['title']}")
    word_count = len(script_data["script"].split())
    duration = int(word_count / cfg["content"]["words_per_minute"] * 60)
    print(f"  ~{word_count} Wörter ≈ {duration // 60}:{duration % 60:02d} min")

    print("[4/5] Audio erzeugen (TTS) ...")
    synthesize(client, cfg, script_data["script"], mp3_path)

    print("[5/5] Metadaten + Feed ...")
    meta = {
        "date": date_iso,
        "title": script_data["title"],
        "subtitle": script_data.get("subtitle", ""),
        "description": script_data.get("description", ""),
        "tags": script_data.get("tags", []),
        "sources": script_data.get("sources", []),
        "slug": slugify(script_data["title"]),
        "duration_seconds": duration,
        "word_count": word_count,
    }
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    # Skript zum Nachlesen mit ablegen
    (EPISODES_DIR / f"{date_iso}.txt").write_text(script_data["script"], encoding="utf-8")

    prune_archive(cfg)
    build_feed(cfg)

    print(f"\n✅ Fertig: {mp3_path.name} ({mp3_path.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
