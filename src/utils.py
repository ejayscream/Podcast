"""Gemeinsame Helfer: Config laden, Pfade, Datum/Slug."""
from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

import yaml

# Projekt-Wurzel = eine Ebene über src/
ROOT = Path(__file__).resolve().parent.parent
EPISODES_DIR = ROOT / "episodes"
FEED_DIR = ROOT / "feed"


def load_config() -> dict:
    with open(ROOT / "config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def today_iso() -> str:
    """UTC-Datum als YYYY-MM-DD. (In CI ist Zeit ohnehin UTC.)"""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")[:80] or "episode"


def ensure_dirs() -> None:
    EPISODES_DIR.mkdir(parents=True, exist_ok=True)
    FEED_DIR.mkdir(parents=True, exist_ok=True)


def recent_topics_block(n: int, exclude_date: str | None = None) -> str:
    """Titel + Tags der letzten n Folgen als 'nicht wiederholen'-Liste.

    Liest die episodes/*.json (neueste zuerst). Gibt "" zurück, wenn es
    noch keine früheren Folgen gibt.
    """
    metas = sorted(EPISODES_DIR.glob("*.json"), reverse=True)
    lines: list[str] = []
    for meta_path in metas:
        if exclude_date and meta_path.stem == exclude_date:
            continue  # eine evtl. schon existierende Folge von heute nicht mitzählen
        try:
            data = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        title = (data.get("title") or "").strip()
        tags = ", ".join(t for t in data.get("tags", []) if t)
        if title:
            lines.append(f"- {title}" + (f"  [Tags: {tags}]" if tags else ""))
        if len(lines) >= n:
            break
    return "\n".join(lines)


def _load_dotenv() -> None:
    """Minimaler .env-Loader für lokale Läufe (keine Extra-Abhängigkeit)."""
    env_file = ROOT / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def require_api_key() -> str:
    _load_dotenv()
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise SystemExit(
            "FEHLER: Umgebungsvariable OPENAI_API_KEY ist nicht gesetzt.\n"
            "Lokal:  setze sie via .env / PowerShell ($env:OPENAI_API_KEY='sk-...').\n"
            "In CI:  hinterlege sie als GitHub-Secret OPENAI_API_KEY."
        )
    return key
