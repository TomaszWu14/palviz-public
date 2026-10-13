"""Nagrywa pokaz aplikacji (?demo=1, napisy bez lektora) i składa gotowy film na YouTube.

Przeglądarka (Playwright + Chromium) wchodzi na /demo/?pokaz=1, uruchamia pokaz i nagrywa ekran
przez CDP screencast (JPEG, 1920×1080). Odtwarzacz demo.js sam przechodzi przez kroki i przy
każdym wysyła zdarzenie `lv-demo-step`; skrypt zapisuje, kiedy który krok ruszył (rozdziały,
.srt). Potem ffmpeg skleja: plansza tytułowa → nagranie → plansza końcowa (link do demo + QR),
z cichą ścieżką albo podkładem muzycznym (--music).

Wymaga: instancji z DEMO_MODE (lokalnie albo publicznej), `pip install playwright segno`,
ffmpeg/ffprobe w PATH. Przeglądarka: PLAYWRIGHT_CHROMIUM albo `playwright install chromium`.

Użycie (z korzenia repo, serwer demo działa na :8080 — patrz README „Wersja demo lokalnie”):
    python tools/record_demo.py                                  # → output/video/
    python tools/record_demo.py --base-url https://logviz.twapp.pl
    python tools/record_demo.py --music podklad.mp3
    python tools/record_demo.py --srt-captions                   # napisy tylko w .srt, nie w obrazie
    python tools/record_demo.py --cards-only                     # same plansze + miniatura

Wynik w --out: logviz-demo.mp4, logviz-demo.pl.srt, youtube.md (tytuł, opis
z rozdziałami), miniatura.png, timeline.json."""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import demo_video as dv  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DEMO = ROOT / "web/ui/static/ui/demo"
CARD = ROOT / "tools/video/card.html"
FONT = ROOT / "web/ui/static/ui/fonts/inter-latin-ext-wght.woff2"
SHOTS = ROOT / "docs/screenshots"
NAME = "logviz-demo"
TITLE = "LogViz — paletyzacja 3D, wysyłki i kontrola HU w jednej aplikacji (demo 2 min)"

# W nagraniu chowamy panel sterowania pokazem. Napisy (opis kroku) zostają w obrazie — film jest
# bez lektora; z --srt-captions chowamy je i zostaje sam plik .srt (napisy CC na YouTube).
HIDE_PANEL = ".lv-demo__panel{display:none!important}"
HIDE_CAPTIONS = ".lv-demo__cap{display:none!important}"
INIT_JS = """
(() => {
  const css = %s;
  const add = () => { const s = document.createElement('style'); s.textContent = css;
                      (document.head || document.documentElement).appendChild(s); };
  document.readyState === 'loading' ? document.addEventListener('DOMContentLoaded', add) : add();
  document.addEventListener('lv-demo-step', (e) => {
    try { window.__lvRec(e.detail.id, e.detail.ms, Date.now() / 1000); } catch (err) {}
  });
})();
"""


def run(cmd):
    print("  $", " ".join(str(c) for c in cmd[:6]), "…" if len(cmd) > 6 else "")
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def browser(pw):
    exe = os.environ.get("PLAYWRIGHT_CHROMIUM") or ("/opt/pw-browsers/chromium"
                                                    if Path("/opt/pw-browsers/chromium").exists() else None)
    return pw.chromium.launch(executable_path=exe, args=["--hide-scrollbars"])


# ── Nagranie ─────────────────────────────────────────────────────────────────────────
def capture(pw, base_url, frames_dir, width, height, css_width, burn_captions, timeout):
    """Zwraca (frames [(epoch, path)], plays [(step_id, epoch)], durations {step_id: s}, t_end)."""
    scale = width / css_width
    b = browser(pw)
    ctx = b.new_context(viewport={"width": css_width, "height": round(height / scale)},
                        device_scale_factor=scale, locale="pl-PL", timezone_id="Europe/Warsaw")
    plays, frames, durations = [], [], {}

    def on_step(_src, sid, ms, t):
        plays.append((sid, t))
        durations[sid] = ms / 1000

    ctx.expose_binding("__lvRec", on_step)
    css = HIDE_PANEL + ("" if burn_captions else HIDE_CAPTIONS)
    ctx.add_init_script(INIT_JS % json.dumps(css))
    page = ctx.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    cdp = ctx.new_cdp_session(page)

    def on_frame(ev):
        path = frames_dir / f"{len(frames):06d}.jpg"
        path.write_bytes(base64.b64decode(ev["data"]))
        frames.append((ev["metadata"].get("timestamp") or time.time(), path))
        try:
            cdp.send("Page.screencastFrameAck", {"sessionId": ev["sessionId"]})
        except Exception:  # noqa: BLE001 — strona w trakcie nawigacji
            pass

    def start_cast():
        cdp.send("Page.startScreencast", {"format": "jpeg", "quality": 92,
                                          "maxWidth": width, "maxHeight": height})

    cdp.on("Page.screencastFrame", on_frame)
    page.goto(base_url.rstrip("/") + "/demo/?pokaz=1", wait_until="networkidle")
    if "/login" in page.url:
        sys.exit(f"Nie wpuściło na konto demo ({page.url}) — czy instancja ma DEMO_MODE i seed_demo?")
    page.wait_for_selector(".lv-demo__panel", state="attached", timeout=15000)
    start_cast()
    page.wait_for_timeout(600)
    page.evaluate("document.querySelector('.lv-demo__btn--primary').click()")

    deadline = time.time() + timeout
    last_url, done = page.url, False
    while time.time() < deadline and not done:
        page.wait_for_timeout(250)
        if page.url != last_url:                 # pełne przeładowanie — screencast od nowa
            last_url = page.url
            try:
                page.wait_for_load_state("domcontentloaded")
                start_cast()
            except Exception:  # noqa: BLE001
                pass
        try:
            cap = page.evaluate("(document.querySelector('.lv-demo__cap')||{}).textContent||''")
        except Exception:  # noqa: BLE001 — kontekst zniszczony nawigacją
            continue
        done = cap.startswith("Koniec prezentacji")
    if not done:
        sys.exit("Pokaz nie dobiegł końca w limicie czasu — sprawdź scenariusz / serwer.")
    page.wait_for_timeout(int(dv.TAIL * 1000) + 500)
    t_end = time.time()
    cdp.send("Page.stopScreencast")
    b.close()
    if errors:
        print("  ! błędy JS na stronach:", *errors[:5], sep="\n    ")
    return frames, plays, durations, t_end


# ── Plansze ──────────────────────────────────────────────────────────────────────────
def qr_svg(url):
    import segno
    import io
    buf = io.BytesIO()
    segno.make(url, error="m").save(buf, kind="svg", scale=10, border=0, dark="#0f172a", xmldecl=False,
                                     svgns=True, nl=False)
    svg = buf.getvalue().decode()
    # segno podaje stałe width/height bez viewBox — zamień na viewBox, żeby kod wypełnił ramkę.
    return re.sub(r'width="(\d+)" height="(\d+)"', r'viewBox="0 0 \1 \2"', svg, count=1)


def short(url):
    return re.sub(r"^https?://", "", url).rstrip("/")


def render_cards(pw, out, demo_url, repo_url, duration_label):
    tpl = CARD.read_text(encoding="utf-8")
    fills = {"FONT": FONT.as_uri(), "SHOT_INTRO": (SHOTS / "hub.png").as_uri(),
             "SHOT_THUMB": (SHOTS / "paletyzacja-3d.png").as_uri(), "DURATION": duration_label,
             "DEMO_URL_SHORT": short(demo_url), "REPO_URL_SHORT": short(repo_url), "QR_SVG": qr_svg(demo_url)}
    b = browser(pw)
    paths = {}
    for card, (w, h) in {"intro": (1920, 1080), "outro": (1920, 1080), "thumb": (1280, 720)}.items():
        html = tpl
        for k, v in dict(fills, CARD=card, W=str(w), H=str(h)).items():
            html = html.replace("{{%s}}" % k, v)
        src = out / f"_card-{card}.html"
        src.write_text(html, encoding="utf-8")
        page = b.new_page(viewport={"width": w, "height": h})
        page.goto(src.as_uri(), wait_until="networkidle")
        page.evaluate("document.fonts.ready")
        paths[card] = out / ("miniatura.png" if card == "thumb" else f"_card-{card}.png")
        page.screenshot(path=str(paths[card]))
        page.close()
        src.unlink()
    b.close()
    return paths


# ── Montaż ───────────────────────────────────────────────────────────────────────────
def assemble(work, out, frames, t_first, t_end, cards, music, fps):
    t_from = t_first - dv.LEAD_IN
    main_len = t_end - t_from
    total = dv.INTRO + main_len + dv.OUTRO
    concat = work / "frames.ffconcat"
    concat.write_text(dv.frame_list(frames, t_from, t_end), encoding="utf-8")
    fit = (f"scale=1920:1080:force_original_aspect_ratio=decrease,"
           f"pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=0x0b1220,setsar=1,fps={fps},format=yuv420p")
    silent = work / "video.mp4"
    vf = (f"[0:v]{fit},fade=t=out:st={dv.INTRO - 0.4}:d=0.4[a];"
          f"[1:v]{fit},trim=0:{main_len:.3f},setpts=PTS-STARTPTS,fade=t=in:st=0:d=0.4[b];"
          f"[2:v]{fit},fade=t=in:st=0:d=0.5,fade=t=out:st={dv.OUTRO - 0.6}:d=0.6[c];"
          f"[a][b][c]concat=n=3:v=1:a=0[v]")
    run(["ffmpeg", "-y", "-loop", "1", "-framerate", str(fps), "-t", str(dv.INTRO), "-i", cards["intro"],
         "-f", "concat", "-safe", "0", "-i", concat,
         "-loop", "1", "-framerate", str(fps), "-t", str(dv.OUTRO), "-i", cards["outro"],
         "-filter_complex", vf, "-map", "[v]", "-c:v", "libx264", "-preset", "slow", "-crf", "18",
         "-movflags", "+faststart", silent])
    cmd = ["ffmpeg", "-y", "-i", silent]
    cmd += ["-i", music] if music else ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo"]
    final = out / f"{NAME}.mp4"
    cmd += ["-filter_complex", dv.audio_filter(total, 1 if music else None), "-map", "0:v", "-map", "[aout]",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest",
            "-movflags", "+faststart", final]
    run(cmd)
    return final, total


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--base-url", default="http://127.0.0.1:8080", help="instancja z DEMO_MODE")
    ap.add_argument("--public-url", default="https://logviz.twapp.pl", help="adres demo na planszy i w opisie")
    ap.add_argument("--repo-url", default="https://github.com/TomaszWu14/palviz-public")
    ap.add_argument("--out", type=Path, default=ROOT / "output/video")
    ap.add_argument("--music", type=Path, help="podkład (mp3/wav) — tylko z prawem do użycia")
    ap.add_argument("--srt-captions", action="store_true", help="napisy tylko w .srt (bez napisów w obrazie)")
    ap.add_argument("--css-width", type=int, default=1440, help="szerokość widoku w px CSS (1440 = czytelny UI)")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--timeout", type=int, default=600, help="maks. czas pokazu w s")
    ap.add_argument("--cards-only", action="store_true", help="tylko plansze i miniatura (bez nagrania)")
    args = ap.parse_args(argv)
    if not shutil.which("ffmpeg"):
        sys.exit("Brak ffmpeg w PATH.")
    from playwright.sync_api import sync_playwright

    script = json.loads((DEMO / "demo_script.json").read_text(encoding="utf-8"))
    est = sum(dv.read_seconds(s["text"]) for s in script["steps"]) + dv.INTRO + dv.OUTRO
    label = f"{round(est / 30) / 2:g} min".replace(".", ",")      # do pół minuty: „2,5 min”
    args.out.mkdir(parents=True, exist_ok=True)
    demo_url = args.public_url.rstrip("/") + "/demo/"

    with sync_playwright() as pw:
        print("1/3 Plansze i miniatura")
        cards = render_cards(pw, args.out, demo_url, args.repo_url, label)
        if args.cards_only:
            print(f"Gotowe: {args.out}")
            return 0
        with tempfile.TemporaryDirectory(prefix="lv-rec-") as tmp:
            work = Path(tmp)
            (work / "frames").mkdir()
            print(f"2/3 Nagrywanie pokazu z {args.base_url} (ok. {round(est)} s)")
            frames, plays, durations, t_end = capture(pw, args.base_url, work / "frames", 1920, 1080,
                                                      args.css_width, not args.srt_captions, args.timeout)
            items = dv.timeline(script["steps"], plays, durations)
            if len(items) != len(script["steps"]):
                print(f"  ! nagrano {len(items)} z {len(script['steps'])} kroków")
            t_first = min(t for _, t in plays)
            offset = dv.INTRO + dv.LEAD_IN
            items_abs = dv.shift(items, offset)
            print(f"3/3 Montaż ({len(frames)} klatek)")
            final, total = assemble(work, args.out, frames, t_first, t_end, cards, args.music, args.fps)
    for c in ("intro", "outro"):
        cards[c].unlink(missing_ok=True)
    (args.out / f"{NAME}.pl.srt").write_text(dv.srt(items_abs), encoding="utf-8")
    chap = dv.chapters(items_abs)
    subs = (f"{NAME}.pl.srt — wgraj jako napisy PL (w obrazie ich nie ma)." if args.srt_captions else
            f"Napisy są w obrazie. {NAME}.pl.srt nie wgrywaj jako CC (dublowałyby się).")
    (args.out / "youtube.md").write_text(
        f"# Tytuł\n\n{TITLE}\n\n# Opis\n\n```\n"
        f"{dv.youtube_description(chap, demo_url, args.repo_url, total)}```\n\n"
        f"# Napisy\n\n{subs}\n\nMiniatura: miniatura.png (1280×720).\n",
        encoding="utf-8")
    (args.out / "timeline.json").write_text(json.dumps(items_abs, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Gotowe: {final} ({total:.1f} s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
