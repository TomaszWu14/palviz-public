"""Montaż filmu z pokazu ?demo=1 (bez lektora): czyste funkcje bez przeglądarki i sieci (testowalne).

record_demo.py nagrywa klatki i oś czasu kroków, a ten moduł zamienia je na:
- listę klatek dla ffmpeg (concat demuxer z czasami trwania),
- ścieżkę dźwiękową: cisza albo opcjonalny podkład muzyczny (pętla, wyciszenie na końcu,
  głośność wyrównana do -14 LUFS — norma YouTube),
- napisy .srt i opis na YouTube z rozdziałami (rozdziały = pole `chapter` w demo_script.json).

Czasy: sekundy od początku gotowego filmu (plansza tytułowa + nagranie + plansza końcowa)."""
from __future__ import annotations

import math
import re
import textwrap

LEAD_IN = 0.8      # s nagrania przed pierwszym krokiem
TAIL = 1.5         # s po ostatnim kroku, zanim wejdzie plansza końcowa
INTRO = 3.5        # s planszy tytułowej
OUTRO = 7.0        # s planszy końcowej (link do demo + QR)
SRT_CHARS = 84     # maks. znaków w jednym napisie (2 linie po ~42)
READ_MS, MIN_MS = 65, 4500   # jak w demo.js: czas kroku = długość napisu × READ_MS, min. MIN_MS


def read_seconds(text):
    """Szacowany czas kroku pokazu (s) — tylko do etykiety długości na planszy."""
    return max(MIN_MS, len(text) * READ_MS) / 1000


# ── Oś czasu ─────────────────────────────────────────────────────────────────────────
def timeline(steps, plays, durations):
    """Łączy kroki scenariusza z momentami ich startu (epoch s) i czasem trwania (s).

    plays: [(step_id, epoch)] ze zdarzeń `lv-demo-step` odtwarzacza — przy powtórce kroku liczy
    się ostatni start. Zwraca listę dictów {id, text, chapter, start, end} z czasem względem
    startu pierwszego kroku (= 0)."""
    first = {}
    for sid, t in plays:
        first[sid] = t                                    # ostatni start wygrywa (powtórka)
    known = [s for s in steps if s["id"] in first]
    if not known:
        raise ValueError("Brak nagranych kroków — pokaz nie wystartował?")
    t0 = min(first[s["id"]] for s in known)
    out = []
    for s in known:
        start = first[s["id"]] - t0
        out.append({"id": s["id"], "text": s["text"], "chapter": s.get("chapter"),
                    "start": round(start, 3), "end": round(start + durations.get(s["id"], 0.0), 3)})
    out.sort(key=lambda x: x["start"])
    return out


def shift(items, offset):
    return [dict(x, start=round(x["start"] + offset, 3), end=round(x["end"] + offset, 3)) for x in items]


# ── Klatki ───────────────────────────────────────────────────────────────────────────
def frame_list(frames, t_from, t_to):
    """frames: [(epoch, ścieżka)] z screencastu (klatki tylko przy zmianie obrazu).
    Zwraca tekst pliku concat ffmpeg pokrywający dokładnie [t_from, t_to]."""
    frames = sorted(frames)
    if not frames:
        raise ValueError("Brak klatek z nagrania.")
    # Klatka widoczna w chwili t_from = ostatnia sprzed t_from (albo pierwsza w ogóle).
    before = [f for f in frames if f[0] <= t_from]
    seq = ([(t_from, before[-1][1])] if before else [(t_from, frames[0][1])])
    seq += [f for f in frames if t_from < f[0] < t_to]
    lines = ["ffconcat version 1.0"]
    for k, (t, path) in enumerate(seq):
        nxt = seq[k + 1][0] if k + 1 < len(seq) else t_to
        lines.append(f"file '{_esc(path)}'")
        lines.append(f"duration {max(nxt - t, 0.001):.3f}")
    lines.append(f"file '{_esc(seq[-1][1])}'")              # wymóg concat: ostatni plik bez duration
    return "\n".join(lines) + "\n"


def _esc(path):
    return str(path).replace("'", "'\\''")


# ── Audio ────────────────────────────────────────────────────────────────────────────
def audio_filter(total, music_input=None):
    """Filtr ffmpeg ścieżki dźwiękowej o długości `total` s, wyjście [aout].

    Bez muzyki: cisza (wejście 1 = anullsrc) — YouTube i odtwarzacze lepiej znoszą film z cichą
    ścieżką niż bez niej. Z muzyką (wejście music_input): pętla, łagodne wejście i wyciszenie
    na końcu, głośność wyrównana do -14 LUFS."""
    if music_input is None:
        return f"[1:a]atrim=0:{total:.3f},asetpts=PTS-STARTPTS[aout]"
    return (f"[{music_input}:a]aresample=48000,aformat=channel_layouts=stereo,aloop=-1:2e9,"
            f"atrim=0:{total:.3f},asetpts=PTS-STARTPTS,afade=t=in:st=0:d=1.5,"
            f"afade=t=out:st={max(total - 3, 0):.3f}:d=3,loudnorm=I=-14:TP=-1.5:LRA=11,"
            f"aresample=48000[aout]")


# ── Napisy ───────────────────────────────────────────────────────────────────────────
def _ts(sec):
    ms = int(round(sec * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _chunks(text, limit=SRT_CHARS):
    """Dzieli tekst na napisy: najpierw po zdaniach, za długie zdania po słowach."""
    out = []
    for sent in re.split(r"(?<=[.!?])\s+", text.strip()):
        out.extend(textwrap.wrap(sent, limit) if len(sent) > limit else [sent])
    return [c for c in out if c]


def srt(items):
    """Napisy .srt: czas kroku dzielony między fragmenty proporcjonalnie do liczby znaków."""
    blocks, n = [], 0
    for it in items:
        chunks = _chunks(it["text"])
        span = max(it["end"] - it["start"], 0.5)
        total = sum(len(c) for c in chunks)
        t = it["start"]
        for c in chunks:
            d = span * len(c) / total
            n += 1
            body = "\n".join(textwrap.wrap(c, math.ceil(len(c) / 2) + 6)) if len(c) > 42 else c
            blocks.append(f"{n}\n{_ts(t)} --> {_ts(t + d - 0.05)}\n{body}\n")
            t += d
    return "\n".join(blocks)


# ── YouTube ──────────────────────────────────────────────────────────────────────────
def _mmss(sec):
    sec = int(sec)
    return f"{sec // 60}:{sec % 60:02d}"


def chapters(items, intro_title="Wstęp"):
    """Rozdziały YouTube: pierwszy musi być 0:00, każdy ≥10 s, co najmniej 3 — krótsze
    sklejamy z poprzednim, żeby YouTube ich nie odrzucił."""
    marks = [(0.0, intro_title)] + [(it["start"], it["chapter"]) for it in items if it.get("chapter")]
    if len(marks) > 1 and marks[1][0] < 10:            # pierwszy rozdział tuż po planszy → jako 0:00
        marks = [(0.0, marks[1][1])] + marks[2:]
    kept = []
    for t, title in marks:
        if kept and t - kept[-1][0] < 10:
            continue
        kept.append((t, title))
    return [f"{_mmss(t)} {title}" for t, title in kept]


def youtube_description(chap, demo_url, repo_url, duration):
    lines = [
        "LogViz — jedna aplikacja webowa dla magazynu, transportu i obsługi klienta: dane podstawowe, "
        "paletyzacja na palecie EU 120×80 w 3D, wysyłki z załadunkiem 3D oraz kontrola palet (HU) "
        "na skanerze z panelem lidera. SAP zostaje źródłem danych tylko do odczytu.",
        "",
        f"▶ Wypróbuj bez logowania: {demo_url}",
        f"▶ Kod i dokumentacja: {repo_url}",
        "",
        "Rozdziały:",
        *chap,
        "",
        "Dane w filmie i w wersji demo są fikcyjne (ACME, DOMEX, PACZKI / PALETY / BUS / EXPORT).",
        f"Długość: {_mmss(duration)}. Bez lektora — opis każdego kroku w napisach.",
        "",
        "#logistyka #magazyn #paletyzacja #WMS #Django #portfolio",
    ]
    return "\n".join(lines) + "\n"
