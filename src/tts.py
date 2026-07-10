"""Text-to-Speech: Skript -> MP3 via OpenAI.

Lange Skripte werden in Blöcke geteilt (TTS-Limit ~4096 Zeichen) und die
resultierenden MP3-Segmente aneinandergehängt. Byte-Konkatenation von MP3
ist für die Wiedergabe in Podcast-Playern in der Praxis unproblematisch.
"""
from __future__ import annotations

from pathlib import Path

from openai import OpenAI

MAX_CHARS = 3800  # Sicherheitsabstand zum TTS-Limit


def _split_text(text: str, max_chars: int = MAX_CHARS) -> list[str]:
    """Teilt an Absatz-/Satzgrenzen, ohne Wörter zu zerreißen."""
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    chunks: list[str] = []
    current = ""

    def flush():
        nonlocal current
        if current.strip():
            chunks.append(current.strip())
        current = ""

    for para in paragraphs:
        if len(para) > max_chars:
            # zu langer Absatz -> an Sätzen splitten
            sentence = ""
            for part in para.replace("! ", "!|").replace("? ", "?|").replace(". ", ".|").split("|"):
                if len(sentence) + len(part) + 1 > max_chars:
                    if current:
                        flush()
                    current = sentence
                    flush()
                    sentence = part
                else:
                    sentence += (" " if sentence else "") + part
            if sentence:
                if len(current) + len(sentence) + 1 > max_chars:
                    flush()
                current += ("\n" if current else "") + sentence
        elif len(current) + len(para) + 1 > max_chars:
            flush()
            current = para
        else:
            current += ("\n" if current else "") + para
    flush()
    return chunks or [text]


def synthesize(client: OpenAI, cfg: dict, script: str, out_path: Path) -> None:
    chunks = _split_text(script)
    print(f"  TTS: {len(chunks)} Segment(e)")
    model = cfg["openai"]["tts_model"]
    voice = cfg["openai"]["tts_voice"]
    instructions = cfg["openai"].get("tts_instructions", "")

    with open(out_path, "wb") as out:
        for i, chunk in enumerate(chunks, 1):
            kwargs = dict(model=model, voice=voice, input=chunk, response_format="mp3")
            # 'instructions' unterstützen nur die gpt-4o-*-tts-Modelle
            if instructions and "tts" in model and model.startswith("gpt"):
                kwargs["instructions"] = instructions
            with client.audio.speech.with_streaming_response.create(**kwargs) as resp:
                for data in resp.iter_bytes():
                    out.write(data)
            print(f"    ✓ Segment {i}/{len(chunks)} ({len(chunk)} Zeichen)")
