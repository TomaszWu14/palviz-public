"""Generator lektora ElevenLabs dla trybu pokazu (?demo=1).

Czyta scenariusz web/ui/static/ui/demo/demo_script.json i ustawienia głosu config/voice.json,
zapisuje MP3 do web/ui/static/ui/demo/audio/ oraz manifest.json (id kroku → plik), z którego
korzysta odtwarzacz demo.js.

Cache: plik = <id>-<hash>.mp3, hash z tekstu dla lektora (po słowniku wymowy) i ustawień głosu
— generowane są tylko nowe/zmienione kroki. Sąsiednie teksty idą jako previous_text/next_text
(spójna intonacja), ale nie wchodzą do hasha: zmiana jednego kroku = jeden nowy plik.

Użycie (z korzenia repo):
    export ELEVENLABS_API_KEY=...  ELEVENLABS_VOICE_ID=...
    python tools/generate_voiceover.py              # tylko zmienione kroki
    python tools/generate_voiceover.py --dry-run    # pokaż plan, nic nie generuj (bez klucza)
    python tools/generate_voiceover.py --step krok03  # przegeneruj jeden krok
    python tools/generate_voiceover.py --all        # wszystko (np. po zmianie głosu)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "web/ui/static/ui/demo/demo_script.json"
VOICE = ROOT / "config/voice.json"
AUDIO = ROOT / "web/ui/static/ui/demo/audio"
API = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}?output_format={fmt}"


def apply_lexicon(text, lexicon):
    """Podmienia skróty na zapis fonetyczny (całe słowa, najdłuższe klucze najpierw)."""
    for key in sorted(lexicon, key=len, reverse=True):
        text = re.sub(rf"(?<!\w){re.escape(key)}(?!\w)", lexicon[key], text)
    return text


def tts_texts(script):
    lex = script.get("lexicon", {})
    return [apply_lexicon(s["text"], lex) for s in script["steps"]]


def audio_name(step_id, tts_text, voice_cfg):
    payload = json.dumps({"text": tts_text, "voice": voice_cfg}, sort_keys=True, ensure_ascii=False)
    return f"{step_id}-{hashlib.sha256(payload.encode('utf-8')).hexdigest()[:10]}.mp3"


def plan(script, voice_cfg, manifest, existing, only=None, force_all=False):
    """Lista (indeks, nazwa_pliku, powód) kroków do wygenerowania."""
    texts = tts_texts(script)
    out = []
    for i, step in enumerate(script["steps"]):
        sid = step["id"]
        if only and sid != only:
            continue
        name = audio_name(sid, texts[i], voice_cfg)
        if only or force_all:
            out.append((i, name, "wymuszony"))
        elif manifest.get(sid) != name or name not in existing:
            out.append((i, name, "nowy" if sid not in manifest else "zmieniony"))
    return out


def synthesize(text, previous_text, next_text, voice_cfg, api_key, voice_id):
    body = {"text": text, "model_id": voice_cfg["model_id"],
            "voice_settings": voice_cfg["voice_settings"]}
    if previous_text:
        body["previous_text"] = previous_text
    if next_text:
        body["next_text"] = next_text
    req = urllib.request.Request(
        API.format(voice_id=voice_id, fmt=voice_cfg["output_format"]),
        data=json.dumps(body).encode("utf-8"), method="POST",
        headers={"xi-api-key": api_key, "Content-Type": "application/json",
                 "Accept": "audio/mpeg"})
    with urllib.request.urlopen(req, timeout=120) as resp:   # noqa: S310 — stały host https
        return resp.read()


def _load_json(path, default=None):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def run(argv=None, synth=synthesize, script_path=SCRIPT, voice_path=VOICE, audio_dir=AUDIO):
    ap = argparse.ArgumentParser(description="Generuje lektora ElevenLabs dla trybu ?demo=1")
    ap.add_argument("--step", help="przegeneruj tylko ten krok (np. krok03)")
    ap.add_argument("--all", action="store_true", help="przegeneruj wszystkie kroki")
    ap.add_argument("--dry-run", action="store_true", help="pokaż, co by się zmieniło")
    args = ap.parse_args(argv)

    script, voice_cfg = _load_json(script_path), _load_json(voice_path)
    ids = [s["id"] for s in script["steps"]]
    if args.step and args.step not in ids:
        print(f"Nieznany krok {args.step!r}. Dostępne: {', '.join(ids)}", file=sys.stderr)
        return 2
    manifest_path = audio_dir / "manifest.json"
    manifest = _load_json(manifest_path, {})
    existing = {p.name for p in audio_dir.glob("*.mp3")} if audio_dir.exists() else set()
    todo = plan(script, voice_cfg, manifest, existing, only=args.step, force_all=args.all)
    stale = sorted(set(manifest) - set(ids))

    for i, name, why in todo:
        print(f"{ids[i]}: {why} → {name}")
    for sid in stale:
        print(f"{sid}: usunięty ze scenariusza → kasuję {manifest[sid]}")
    if not todo and not stale:
        print("Bez zmian — wszystkie nagrania aktualne.")
    if args.dry_run or (not todo and not stale):
        return 0

    api_key, voice_id = os.environ.get("ELEVENLABS_API_KEY"), os.environ.get("ELEVENLABS_VOICE_ID")
    if todo and not (api_key and voice_id):
        print("Ustaw ELEVENLABS_API_KEY i ELEVENLABS_VOICE_ID (nie zapisuj ich w repo).",
              file=sys.stderr)
        return 2
    audio_dir.mkdir(parents=True, exist_ok=True)
    texts = tts_texts(script)
    for i, name, _why in todo:
        prev_t = texts[i - 1] if i > 0 else None
        next_t = texts[i + 1] if i + 1 < len(texts) else None
        (audio_dir / name).write_bytes(synth(texts[i], prev_t, next_t, voice_cfg, api_key, voice_id))
        old = manifest.get(ids[i])
        if old and old != name and (audio_dir / old).exists():
            (audio_dir / old).unlink()
        manifest[ids[i]] = name
        manifest_path.write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n",
                                 encoding="utf-8")       # po każdym kroku: przerwanie nie gubi pracy
        print(f"{ids[i]}: zapisano")
    for sid in stale:
        (audio_dir / manifest.pop(sid)).unlink(missing_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(run())
