#!/usr/bin/env python3
"""Mỗi chữ Kanji một video MP4 (1280×720) khớp với câu chuyện của thẻ.

Cảnh trong mỗi video (giọng đọc tiếng Việt, độ dài cảnh theo độ dài lời đọc):
  1. Giới thiệu: chữ to + âm Hán Việt + nghĩa.
  2. Câu chuyện: ảnh thẻ (lia chậm) + các mảnh ghép hiện lên ĐÚNG LÚC lời đọc nhắc tới
     (木 + 幺 + 白 → 楽) + phụ đề, mảnh đã nhắc được tô màu.
  3. (tắt) Câu chuyện con của từng mảnh — bật bằng SUBSTORIES = True.
  4. Cách viết: vẽ từng nét theo KanjiVG.

Bỏ qua chữ đơn giản: chưa có câu chuyện, chính là mảnh bộ nền, hoặc câu chuyện ghép < 2 mảnh.

    .venv/bin/python tools/kanji_video.py --only 楽          # làm mẫu 1 chữ
    .venv/bin/python tools/kanji_video.py -j 4               # cả bộ -> build/kanji-video/
Cần: pip install pillow edge-tts; ffmpeg.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from kanji_audio_text import js_value, title  # noqa: E402
import numpy as np  # noqa: E402
import kanji_draw  # noqa: E402

KV = ROOT / "docs/kanji-viewer"
OUT = ROOT / "build/kanji-video"
CACHE = ROOT / "build/kanji-video-cache"
FFMPEG = "/opt/homebrew/bin/ffmpeg"
FFPROBE = "/opt/homebrew/bin/ffprobe"
W, H, FPS = 1280, 720, 24
VOICE = "vi-VN-HoaiMyNeural"
SUBSTORIES = False      # True = thêm cảnh câu chuyện con của từng mảnh ghép

BG, INK, MUTED, ACC, HL, CARD = (250, 247, 242), (34, 30, 28), (120, 112, 104), (14, 116, 92), (217, 119, 6), (255, 255, 255)
CJK = re.compile(r"[⺀-⿟々゠-ヿ㐀-鿿豈-﫿]")
F_MIN = "/System/Library/Fonts/ヒラギノ明朝 ProN.ttc"
F_TXT = "/System/Library/Fonts/Supplemental/Arial.ttf"
F_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
_fonts: dict = {}


def font(path: str, size: int, index: int = 0):
    key = (path, size, index)
    if key not in _fonts:
        _fonts[key] = ImageFont.truetype(path, size, index=index)
    return _fonts[key]


def kfont(size):            # chữ Hán: Hiragino Mincho W6
    return font(F_MIN, size, 1)


# ------------------------------------------------------------------ dữ liệu
def load_data():
    kanji = js_value(KV / "kanji-game-data.js", "KANJI")
    road = js_value(KV / "kanji-roadmap.js", "ROADMAP")
    info = {}
    for n, k, hv, m, j, s, img in kanji:
        d = info.setdefault(k, {"hv": hv, "m": m, "s": "", "img": None, "n": n})
        if s and not d["s"]:
            d.update(s=s, img=img, n=n)
    for k, hv, m, _t in road["radw"]:
        info.setdefault(k, {"hv": hv, "m": m, "s": "", "img": None, "n": None})
    radk = {r["k"] for r in road["rad"]} | {r[0] for r in road["radw"]}
    return kanji, info, radk


def parts_of(k: str, s: str) -> list[str]:
    out = []
    for c in CJK.findall(s):
        if c != k and c not in out:
            out.append(c)
    return out


def eligible(kanji, radk):
    rows = []
    for n, k, hv, m, j, s, img in kanji:
        if s and k not in radk and len(parts_of(k, s)) >= 2:
            rows.append((n, k, hv, m, j, s, img))
    return rows


def spoken(text: str, info) -> tuple[str, dict[str, int]]:
    """Chữ Hán -> âm Hán Việt; trả về câu đọc + vị trí (ký tự) lần đầu nhắc mỗi chữ."""
    out, pos = "", {}
    for ch in text:
        if CJK.match(ch):
            pos.setdefault(ch, len(out))
            out += title(info[ch]["hv"]) if ch in info and info[ch]["hv"] else ""
        else:
            out += ch
    out = re.sub(r"\(\s*\)", "", out)
    out = re.sub(r"\s+([,.;:!?])", r"\1", out)
    return re.sub(r"\s{2,}", " ", out).strip(), pos


def end(t: str) -> str:
    t = t.strip()
    return t if not t or t[-1] in ".!?…" else t + "."


# ------------------------------------------------------------------ giọng đọc
async def _edge(text: str, dest: Path) -> bool:
    import edge_tts
    for attempt in range(12):
        try:
            data = bytearray()
            comm = edge_tts.Communicate(text, VOICE)
            async for msg in comm.stream():
                if msg["type"] == "audio":
                    data += msg["data"]
            if len(data) > 512:
                dest.write_bytes(bytes(data))
                return True
        except Exception:                                   # noqa: BLE001
            pass
        await asyncio.sleep(0.7 * (attempt + 1))
    return False


def tts(text: str) -> Path:
    CACHE.mkdir(parents=True, exist_ok=True)
    dest = CACHE / (hashlib.sha1(f"{VOICE}|{text}".encode()).hexdigest()[:16] + ".mp3")
    if dest.exists() and dest.stat().st_size > 512:
        return dest
    if not asyncio.run(_edge(text, dest)):
        # dịch vụ edge hỏng hẳn -> giọng Linh có sẵn của macOS (offline)
        with tempfile.NamedTemporaryFile(suffix=".aiff", delete=False) as t:
            aiff = Path(t.name)
        subprocess.run(["say", "-v", "Linh", "-o", str(aiff), text], check=True)
        subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", str(aiff), "-b:a", "64k", str(dest)], check=True)
        aiff.unlink(missing_ok=True)
    return dest


def duration(p: Path) -> float:
    out = subprocess.run([FFPROBE, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                         capture_output=True, text=True).stdout.strip()
    return float(out or 0)


# ------------------------------------------------------------------ vẽ chữ
def runs(text: str):
    """Tách đoạn chữ Latin / chữ Hán để vẽ bằng 2 font khác nhau."""
    cur, cjk = "", None
    for ch in text:
        c = bool(CJK.match(ch))
        if cjk is not None and c != cjk:
            yield cur, cjk
            cur = ""
        cur += ch
        cjk = c
    if cur:
        yield cur, cjk


def wrap_rich(text: str, size: int, width: int) -> list[list[tuple[str, bool]]]:
    words = re.findall(r"\S+\s*", text)
    lines, line, lw = [], [], 0.0
    for w in words:
        ww = sum((kfont(size) if c else font(F_TXT, size)).getlength(t) for t, c in runs(w))
        if line and lw + ww > width:
            lines.append(line)
            line, lw = [], 0.0
        line.append(w)
        lw += ww
    if line:
        lines.append(line)
    return [list(runs("".join(l).rstrip())) for l in lines]


def draw_rich(d: ImageDraw.ImageDraw, x0: int, y: int, text: str, size: int, width: int,
              hl: set[str] = frozenset(), color=INK, center=False, line_h=1.45) -> int:
    for line in wrap_rich(text, size, width):
        lw = sum((kfont(size) if c else font(F_TXT, size)).getlength(t) for t, c in line)
        x = x0 + (width - lw) / 2 if center else x0
        for t, c in line:
            if c:
                for ch in t:
                    f = kfont(size)
                    d.text((x, y + size * 0.82), ch, font=f, fill=HL if ch in hl else ACC, anchor="ls")
                    x += f.getlength(ch)
            else:
                f = font(F_TXT, size)
                d.text((x, y + size * 0.82), t, font=f, fill=color, anchor="ls")
                x += f.getlength(t)
        y += int(size * line_h)
    return y


def mix(col, q):
    return tuple(int(BG[i] + (col[i] - BG[i]) * q) for i in range(3))


def ease(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def paste_alpha(base: Image.Image, im: Image.Image, xy, alpha: float):
    if alpha <= 0:
        return
    if alpha < 1:
        im = im.copy()
        a = im.getchannel("A").point(lambda v: int(v * alpha))
        im.putalpha(a)
    base.alpha_composite(im, (int(xy[0]), int(xy[1])))


def glyph_tile(ch: str, size: int, color=INK, sub: str = "", sub_size=26) -> Image.Image:
    w = int(size * 1.15)
    im = Image.new("RGBA", (max(w, int(font(F_BOLD, sub_size).getlength(sub)) + 10), int(size * 1.2 + sub_size * 1.6)), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.text((im.width / 2, size * 0.98), ch, font=kfont(size), fill=color, anchor="ms")
    if sub:
        d.text((im.width / 2, size * 1.2 + sub_size), sub, font=font(F_BOLD, sub_size), fill=ACC, anchor="ms")
    return im


# ------------------------------------------------------------------ nét chữ KanjiVG
def svg_path_points(dstr: str, steps: int = 14) -> list[tuple[float, float]]:
    toks = re.findall(r"[MmCcSsLlHhVvZz]|-?\d*\.?\d+(?:e-?\d+)?", dstr)
    pts, i, cmd = [], 0, None
    cx = cy = 0.0
    last_c2 = None

    def num():
        nonlocal i
        v = float(toks[i]); i += 1
        return v

    def bez(p0, p1, p2, p3):
        for s in range(1, steps + 1):
            t = s / steps
            mt = 1 - t
            pts.append((mt**3 * p0[0] + 3 * mt * mt * t * p1[0] + 3 * mt * t * t * p2[0] + t**3 * p3[0],
                        mt**3 * p0[1] + 3 * mt * mt * t * p1[1] + 3 * mt * t * t * p2[1] + t**3 * p3[1]))

    while i < len(toks):
        if re.match(r"[A-Za-z]", toks[i]):
            cmd = toks[i]; i += 1
            if cmd in "Zz":
                continue
        rel = cmd.islower()
        ox, oy = (cx, cy) if rel else (0.0, 0.0)
        C = cmd.upper()
        if C == "M":
            cx, cy = num() + ox, num() + oy
            pts.append((cx, cy)); last_c2 = None
            cmd = "l" if rel else "L"
        elif C == "L":
            cx, cy = num() + ox, num() + oy
            pts.append((cx, cy)); last_c2 = None
        elif C == "H":
            cx = num() + ox; pts.append((cx, cy)); last_c2 = None
        elif C == "V":
            cy = num() + oy; pts.append((cx, cy)); last_c2 = None
        elif C == "C":
            p1 = (num() + ox, num() + oy); p2 = (num() + ox, num() + oy); p3 = (num() + ox, num() + oy)
            bez((cx, cy), p1, p2, p3); last_c2 = p2; cx, cy = p3
        elif C == "S":
            p1 = (2 * cx - last_c2[0], 2 * cy - last_c2[1]) if last_c2 else (cx, cy)
            p2 = (num() + ox, num() + oy); p3 = (num() + ox, num() + oy)
            bez((cx, cy), p1, p2, p3); last_c2 = p2; cx, cy = p3
        else:
            i += 1
    return pts


def strokes_of(ch: str) -> list[list[tuple[float, float]]]:
    p = KV / "kvg" / f"{ord(ch):05x}.json"
    if not p.exists():
        return []
    return [svg_path_points(d) for d in json.loads(p.read_text())["paths"]]


def partial(pts, frac):
    if frac >= 1:
        return pts
    seg = [((pts[k][0] - pts[k - 1][0]) ** 2 + (pts[k][1] - pts[k - 1][1]) ** 2) ** 0.5 for k in range(1, len(pts))]
    total, target, acc = sum(seg), sum(seg) * frac, 0.0
    out = [pts[0]]
    for k, L in enumerate(seg):
        if acc + L >= target:
            r = (target - acc) / L if L else 0
            out.append((pts[k][0] + (pts[k + 1][0] - pts[k][0]) * r, pts[k][1] + (pts[k + 1][1] - pts[k][1]) * r))
            return out
        out.append(pts[k + 1]); acc += L
    return out


# ------------------------------------------------------------------ cảnh
def base() -> Image.Image:
    im = Image.new("RGBA", (W, H), BG + (255,))
    d = ImageDraw.Draw(im)
    d.rectangle([0, H - 6, W, H], fill=ACC)
    return im


def card_img(rel: str | None, max_w: int, max_h: int) -> Image.Image | None:
    if not rel:
        return None
    p = KV / rel
    if not p.exists():
        return None
    im = Image.open(p).convert("RGBA")
    s = min(max_w / im.width, max_h / im.height)
    return im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)


class Drawer:
    """Hình minh hoạ của thẻ được 'vẽ tay' dần: nét đen -> tô màu -> nét đỏ (theo lời đọc)."""
    def __init__(self, rel, max_w, max_h):
        self.ok = False
        if not rel or not (KV / rel).exists():
            return
        ill = kanji_draw.illustration(KV / rel)
        if ill is None:
            return
        self.arr = np.asarray(ill.convert("RGB"))
        self.T, self.R = kanji_draw.draw_plan(ill)
        self.has_red = bool(np.isfinite(self.R).any() and (~np.isnan(self.R)).any())
        s = min(max_w / ill.width, max_h / ill.height)
        self.size = (int(ill.width * s), int(ill.height * s))
        self.scale = s
        self.ok = True

    def image(self, p, pr):
        im, pen = kanji_draw.frame(self.arr, self.T, self.R, p, pr)
        im = im.resize(self.size, Image.LANCZOS).convert("RGBA")
        if pen:
            d = ImageDraw.Draw(im)
            x, y = pen[0] * self.scale, pen[1] * self.scale
            d.line([(x, y), (x + 34, y - 46)], fill=(60, 60, 60), width=7)          # cây bút
            d.line([(x + 34, y - 46), (x + 44, y - 60)], fill=HL, width=7)
            d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=HL)
        return im


class Video:
    def __init__(self):
        self.scenes = []          # (dur, fn(t)->Image, audio path|None)

    def add(self, dur, fn, audio=None):
        self.scenes.append((dur, fn, audio))

    def render(self, dest: Path):
        dest.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            wavs = []
            for k, (dur, fn, audio) in enumerate(self.scenes):
                w = td / f"a{k:03d}.wav"
                src = ["-i", str(audio)] if audio else ["-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono"]
                subprocess.run([FFMPEG, "-y", "-loglevel", "error", *src, "-af", f"apad=whole_dur={dur:.3f}",
                                "-t", f"{dur:.3f}", "-ar", "24000", "-ac", "1", str(w)], check=True)
                wavs.append(w)
            lst = td / "a.txt"
            lst.write_text("".join(f"file '{w}'\n" for w in wavs))
            audio = td / "a.wav"
            subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst),
                            "-c", "copy", str(audio)], check=True)
            proc = subprocess.Popen([FFMPEG, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                                     "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", str(audio),
                                     "-c:v", "libx264", "-preset", "medium", "-crf", "26", "-pix_fmt", "yuv420p",
                                     "-c:a", "aac", "-b:a", "96k", "-shortest", "-movflags", "+faststart", str(dest)],
                                    stdin=subprocess.PIPE)
            for dur, fn, _ in self.scenes:
                n = max(1, round(dur * FPS))
                for f in range(n):
                    proc.stdin.write(fn(f / FPS).convert("RGB").tobytes())
            proc.stdin.close()
            proc.wait()


def make_video(row, info, dest: Path):
    n, k, hv, m, j, s, img = row
    v = Video()
    PAD = 0.45

    # 1. Giới thiệu
    a = tts(f"{title(hv)}. Nghĩa: {end(m)}")
    d1 = duration(a) + PAD + 0.4
    intro = base()
    dd = ImageDraw.Draw(intro)
    dd.text((W - 40, 44), f"Thẻ {n}" + (f" · {j}" if j else ""), font=font(F_TXT, 26), fill=MUTED, anchor="rs")
    big = glyph_tile(k, 400)

    def f_intro(t, big=big):
        im = intro.copy()
        paste_alpha(im, big, (110, 120 - 30 * (1 - ease(t / 0.6))), ease(t / 0.5))
        d = ImageDraw.Draw(im)
        al = ease((t - 0.3) / 0.5)
        if al > 0:
            col = tuple(int(BG[c] + (ACC[c] - BG[c]) * al) for c in range(3))
            d.text((640, 300), title(hv), font=font(F_BOLD, 84), fill=col, anchor="ls")
            col2 = tuple(int(BG[c] + (INK[c] - BG[c]) * al) for c in range(3))
            draw_rich(d, 640, 340, m[:1].upper() + m[1:], 48, 600, color=col2)
        return im
    v.add(d1, f_intro, a)

    # 2. Câu chuyện: ảnh thẻ + mảnh ghép hiện đúng lúc lời đọc nhắc tới
    say, pos = spoken(s, info)
    a = tts("Câu chuyện: " + end(say))
    lead = len("Câu chuyện: ")
    total_chars = lead + len(end(say))
    d2 = duration(a) + PAD + 0.8
    speech = d2 - PAD - 0.8
    pieces = parts_of(k, s)[:6]
    when = {c: (lead + pos.get(c, 0)) / total_chars * speech for c in pieces + [k]}
    when[k] = max(when.get(k, 0), max(when[c] for c in pieces) + 0.4) if pieces else when.get(k, 0)
    tiles = [glyph_tile(c, 92, INK, title(info[c]["hv"]) if c in info else "") for c in pieces]
    res = glyph_tile(k, 92, HL, title(hv))
    plus = font(F_BOLD, 54)
    gap = 26
    widths = [t.width for t in tiles] + [res.width]
    row_w = sum(widths) + gap * 2 * len(tiles) + 40
    scale = min(1.0, (W - 80) / row_w)
    if scale < 1:
        tiles = [t.resize((int(t.width * scale), int(t.height * scale)), Image.LANCZOS) for t in tiles]
        res = res.resize((int(res.width * scale), int(res.height * scale)), Image.LANCZOS)
        gap = int(gap * scale)
        row_w = sum(t.width for t in tiles) + res.width + gap * 2 * len(tiles) + 40
    # Ảnh AI vẽ theo câu chuyện (build/kanji-ai/NNNN-0.png, -1.png …, tạo bằng tools/kanji_ai_images.py)
    ai = [Image.open(q).convert("RGBA").resize((470, 470), Image.LANCZOS)
          for q in sorted((ROOT / "build/kanji-ai").glob(f"{n:04d}-*.png"))]
    drw = Drawer(img, 700, 470) if not ai else type("NoDraw", (), {"ok": False})()
    card = None if drw.ok else card_img(img, 1000, 330)
    t_draw0, t_draw1 = 0.15, max(1.5, speech * 0.72)
    t_red = min((when[c] for c in pieces), default=speech * 0.5)
    hv_f, row_h = font(F_BOLD, 30), 74
    st_base = base()
    if drw.ok:
        sd = ImageDraw.Draw(st_base)
        px, py = 40 + (720 - drw.size[0]) // 2, 30 + (490 - drw.size[1]) // 2
        sd.rounded_rectangle([40, 30, 760, 520], 18, fill=CARD, outline=(225, 215, 205), width=2)

    def f_story(t):
        im = st_base.copy()
        d = ImageDraw.Draw(im)
        if ai:
            # mỗi ảnh một đoạn của lời kể, lia/zoom chậm, chuyển cảnh mờ dần
            seg = speech / len(ai)
            k_ = min(len(ai) - 1, int(t / seg)) if seg > 0 else 0
            for idx in ([k_ - 1, k_] if k_ > 0 and t - k_ * seg < 0.5 else [k_]):
                lt = t - idx * seg
                z = 1 + 0.08 * min(1, lt / max(seg, 0.1))
                sz = int(470 * z)
                img_ = ai[idx].resize((sz, sz), Image.BILINEAR).crop(((sz - 470) // 2, (sz - 470) // 2 + (idx % 2) * (sz - 470) // 3, (sz - 470) // 2 + 470, (sz - 470) // 2 + (idx % 2) * (sz - 470) // 3 + 470))
                al = 1.0 if idx < k_ or k_ == 0 or t - k_ * seg >= 0.5 or idx != k_ else (t - k_ * seg) / 0.5
                paste_alpha(im, img_, (165, 40), al)
            ImageDraw.Draw(im).rounded_rectangle([163, 38, 637, 512], 16, outline=(225, 215, 205), width=3)
        if ai or drw.ok:
            y = 40
            for c in pieces:
                q = ease((t - when[c]) / 0.35)
                if q > 0:
                    tile = glyph_tile(c, 62, INK)
                    paste_alpha(im, tile, (800 + 20 * (1 - q), y - 8), q)
                    d.text((890, y + 44), title(info[c]["hv"]) if c in info else "", font=hv_f, fill=mix(ACC, q), anchor="ls")
                y += row_h
            q = ease((t - when[k]) / 0.4)
            if q > 0:
                d.line([(800, y + 6), (1230, y + 6)], fill=(210, 200, 190), width=2)
                paste_alpha(im, glyph_tile(k, 70, HL), (800, y + 10 - 20 * (1 - q)), q)
                d.text((895, y + 66), title(hv), font=font(F_BOLD, 36), fill=mix(HL, q), anchor="ls")
        if drw.ok:
            p = 0.86 * ease((t - t_draw0) / (t_draw1 - t_draw0)) if t < t_draw1 else 1.0
            pr = (t - t_red) / 1.4 if drw.has_red else 0
            im.alpha_composite(drw.image(p, max(0.0, min(1.0, pr))), (px, py))
        elif not ai:
            if card:
                z = 1 + 0.05 * (t / d2)
                c2 = card.resize((int(card.width * z), int(card.height * z)), Image.BILINEAR)
                im.alpha_composite(c2, ((W - c2.width) // 2, 22 - (c2.height - card.height) // 2))
            y0 = 372
            x = (W - row_w) / 2
            for idx, (c, tile) in enumerate(zip(pieces, tiles)):
                p = ease((t - when[c]) / 0.35)
                paste_alpha(im, tile, (x, y0 + 26 * (1 - p)), p)
                x += tile.width + gap
                if p > 0:
                    d.text((x, y0 + 70 * scale), "+" if idx < len(pieces) - 1 else "→", font=plus, fill=MUTED, anchor="lm")
                x += gap + (20 if idx == len(pieces) - 1 else 0)
            p = ease((t - when[k]) / 0.4)
            paste_alpha(im, res, (x, y0 + 26 * (1 - p)), p)
        said = {c for c in pieces + [k] if t >= when[c]}
        draw_rich(d, 70, 548, s, 30, W - 140, hl=said, center=True, line_h=1.4)
        return im
    v.add(d2, f_story, a)

    # 3. Câu chuyện con của từng mảnh: TẮT (chỉ giữ câu chuyện chính cho video gọn)
    for c in (parts_of(k, s) if SUBSTORIES else []):
        if c not in info:
            continue
        ci = info[c]
        if ci["s"]:
            text = f"{title(ci['hv'])}, {ci['m'].lower()}: " + end(spoken(ci["s"], info)[0])
        else:
            text = f"{title(ci['hv'])}, {spoken(ci['m'], info)[0].lower()}, là mảnh ghép."
        a = tts(text)
        dur = duration(a) + PAD
        sb = base()
        d = ImageDraw.Draw(sb)
        draw_rich(d, 40, 30, f"Câu chuyện con · mảnh của {k} ({title(hv)})", 26, 900, color=MUTED)
        tile = glyph_tile(c, 260)
        cdrw = Drawer(ci["img"], 520, 250) if ci["s"] else None
        cimg = None if (cdrw and cdrw.ok) else (card_img(ci["img"], 780, 260) if ci["s"] else None)
        d.text((440, 140), title(ci["hv"]), font=font(F_BOLD, 60), fill=ACC, anchor="ls")
        draw_rich(d, 440, 166, ci["m"][:1].upper() + ci["m"][1:], 36, 780)
        if cimg:
            sb.alpha_composite(cimg, (440, 230))
        if cdrw and cdrw.ok:
            ImageDraw.Draw(sb).rounded_rectangle([440, 222, 440 + cdrw.size[0] + 16, 222 + cdrw.size[1] + 16], 14, fill=CARD, outline=(225, 215, 205), width=2)
        story_y = 230 + (cimg.height + 30 if cimg else cdrw.size[1] + 36 if (cdrw and cdrw.ok) else 20)
        draw_rich(d, 440, story_y, ci["s"] or "(mảnh ghép, không có câu chuyện riêng)", 32, 800, hl=set(), color=INK if ci["s"] else MUTED)

        def f_sub(t, sb=sb, tile=tile, cdrw=cdrw, dur=dur):
            im = sb.copy()
            if cdrw and cdrw.ok:
                p = 0.86 * ease((t - 0.1) / max(0.8, dur * 0.6)) if t < dur * 0.6 + 0.1 else 1.0
                pr = (t - dur * 0.45) / 1.0 if cdrw.has_red else 0
                im.alpha_composite(cdrw.image(p, max(0.0, min(1.0, pr))), (448, 230))
            paste_alpha(im, tile, (60, 130 + 20 * (1 - ease(t / 0.4))), ease(t / 0.35))
            return im
        v.add(dur, f_sub, a)

    # 4. Cách viết
    strokes = strokes_of(k)
    if strokes:
        a = tts(f"Cách viết chữ {title(hv).split(',')[0]}: {len(strokes)} nét.")
        per = 0.55
        dur = max(duration(a) + 0.3, len(strokes) * per + 1.6)
        wb = base()
        d = ImageDraw.Draw(wb)
        S, ox, oy = 560, 120, 70
        d.rectangle([ox, oy, ox + S, oy + S], outline=(220, 200, 190), width=3, fill=CARD)
        for a1, b1 in (((ox + S / 2, oy), (ox + S / 2, oy + S)), ((ox, oy + S / 2), (ox + S, oy + S / 2))):
            d.line([a1, b1], fill=(235, 215, 205), width=2)
        d.text((760, 260), k, font=kfont(150), fill=INK, anchor="ls")
        d.text((760, 330), title(hv), font=font(F_BOLD, 48), fill=ACC, anchor="ls")
        d.text((760, 390), f"{len(strokes)} nét", font=font(F_TXT, 40), fill=MUTED, anchor="ls")
        sc = S / 109

        def f_write(t, wb=wb):
            im = wb.copy()
            dr = ImageDraw.Draw(im)
            for idx, pts in enumerate(strokes):
                fr = (t - 0.3 - idx * per) / (per * 0.85)
                if fr <= 0:
                    break
                q = [(ox + x * sc, oy + y * sc) for x, y in partial(pts, min(1, fr))]
                col = HL if fr < 1 else INK
                if len(q) > 1:
                    dr.line(q, fill=col, width=int(3.4 * sc), joint="curve")
                    for px, py in (q[0], q[-1]):
                        r = 3.4 * sc / 2
                        dr.ellipse([px - r, py - r, px + r, py + r], fill=col)
            return im
        v.add(dur, f_write, a)

    v.render(dest)
    return dest


def job(args):
    row, out = args
    _, info, _ = load_data()
    try:
        make_video(row, info, out)
        return f"✓ {out.name}"
    except Exception as exc:                                # noqa: BLE001
        return f"✗ {out.name}: {exc}"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", help="Chỉ làm các chữ này (vd 楽 or 楽休) hoặc số thẻ, cách nhau dấu phẩy")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("-j", "--jobs", type=int, default=3)
    ap.add_argument("-o", "--out", type=Path, default=OUT)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    kanji, info, radk = load_data()
    rows = eligible(kanji, radk)
    if args.only:
        want = set(re.split(r"[,\s]+", args.only)) | set(CJK.findall(args.only))
        rows = [r for r in kanji if r[1] in want or str(r[0]) in want]
    if args.limit:
        rows = rows[: args.limit]
    todo = [(r, args.out / f"{r[0]:04d}-{r[1]}.mp4") for r in rows]
    todo = [(r, o) for r, o in todo if args.force or not o.exists()]
    print(f"{len(todo)} video cần làm (đủ điều kiện: {len(eligible(kanji, radk))})", flush=True)
    with ProcessPoolExecutor(args.jobs) as ex:
        for i, msg in enumerate(ex.map(job, todo), 1):
            print(f"[{i}/{len(todo)}] {msg}", flush=True)


if __name__ == "__main__":
    main()
