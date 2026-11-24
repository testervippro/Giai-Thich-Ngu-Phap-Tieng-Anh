#!/usr/bin/env python3
"""Dựng lại ảnh câu chuyện Kanji: CẮT phần tranh (từ ảnh đã làm nét x2) + VẼ LẠI toàn bộ chữ câu chuyện bằng font vector
(giống cách ghép GIF: từ khoá xanh, chữ Hán đỏ, phần còn lại đen). Ra thư mục riêng, không đụng ảnh gốc.

    python3 tools/kanji_story_upscale.py          # bước 1: làm nét x2 -> build/kanji_story_x2/
    python3 tools/kanji_story_redraw.py           # bước 2: cắt tranh + vẽ lại chữ -> build/kanji_story_hd/
    python3 tools/kanji_story_redraw.py 17 542    # vài thẻ để thử
    python3 tools/kanji_story_redraw.py --compare # chỉ dựng trang so sánh build/kanji_story_hd/compare.html

Thẻ chưa có câu chuyện (không có chữ để vẽ lại) -> giữ nguyên ảnh đã làm nét.
Cần: pillow, numpy. Font: Arial Bold Italic (tiếng Việt) + ヒラギノ角ゴシック W6 (chữ Hán dạng Nhật) có sẵn trên macOS.
"""
import argparse
import json
import re
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
UP = ROOT / "build/kanji_story_x2"
OUT = ROOT / "build/kanji_story_hd"
SRC = ROOT / "docs/kanji-viewer/kanji_story"
FV = "/System/Library/Fonts/Supplemental/Arial Bold Italic.ttf"
FC = "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc"
# font chữ Hán theo thứ tự ưu tiên: dạng Nhật trước; ký tự nào thiếu glyph thì lùi sang font sau
FC_CHAIN = [FC, "/System/Library/Fonts/STHeiti Medium.ttc", "/System/Library/Fonts/Hiragino Sans GB.ttc",
            "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"]
INK, TEAL, RED = (35, 35, 35), (30, 125, 175), (185, 35, 40)
_NOTDEF, _HAS, _FONTS = {}, {}, {}


def _bmp(f, c):
    im = Image.new("L", (80, 80), 0)
    ImageDraw.Draw(im).text((8, 4), c, font=f, fill=255)
    return im.tobytes()


def han_font(c, sz):
    """Font đầu tiên trong FC_CHAIN có glyph cho ký tự c (None nếu không font nào có)."""
    for path in FC_CHAIN:
        key = (path, c)
        if key not in _HAS:
            f = _FONTS.setdefault(path, ImageFont.truetype(path, 56))
            nd = _NOTDEF.setdefault(path, _bmp(f, "\uffff"))
            b = _bmp(f, c)
            _HAS[key] = bool(any(b)) and b != nd
        if _HAS[key]:
            return ImageFont.truetype(path, sz)
    return None


def unsupported(story):
    return sorted({c for c in story if cjk(c) and han_font(c, 20) is None})
PUNCT = re.compile(r"^[.,;:!?…]+$")
cjk = lambda c: ord(c) >= 0x2E80


def load_story():
    s = (ROOT / "docs/kanji-viewer/kanji-game-data.js").read_text(encoding="utf-8")
    K = json.JSONDecoder().raw_decode(s[s.index("[", s.index("window.KANJI")):])[0]
    return {r[0]: str(r[5]).strip() for r in K if str(r[5]).strip()}


# ---------- tìm ranh giới tranh | chữ ----------
def picture_right_edge(im):
    """Cột cuối của khối tranh (bên trái): khoảng trống dọc dài nhất ở nửa giữa, bên phải còn khối chữ."""
    a = np.asarray(im.convert("L")).astype(np.int16)
    H, W = a.shape
    e = np.zeros(a.shape, bool)
    e[:, :-1] |= np.abs(np.diff(a, axis=1)) > 40
    e[:-1, :] |= np.abs(np.diff(a, axis=0)) > 40
    ink = e.sum(0) > max(3, 0.01 * H)
    runs, x = [], 0
    while x < W:
        if not ink[x]:
            y = x
            while y < W and not ink[y]:
                y += 1
            runs.append((x, y - x)); x = y
        else:
            x += 1
    best = None
    for st, ln in runs:
        if st < 0.12 * W or st + ln > 0.78 * W or ln < 0.02 * W:
            continue
        if ink[st + ln:].sum() < 0.12 * W:        # bên phải phải còn khối chữ đủ rộng
            continue
        if best is None or ln > best[1]:
            best = (st, ln)
    return (best[0] + min(best[1] // 3, 16)) if best else int(0.40 * W)


# ---------- vẽ chữ ----------
def chunks(story):
    out, buf = [], []
    for m in re.finditer(r"\(([^)]*)\)|[^\s()]+", story):
        if m.group(1) is not None:
            out.append((" ".join(buf), m.group(1).strip())); buf = []
        else:
            buf.append(m.group(0))
    if buf:
        out.append((" ".join(buf), None))
    return out


def words(ch):
    it = []
    for i, (txt, k) in enumerate(ch):
        ws = txt.split()
        for j, w in enumerate(ws):
            it.append((w, TEAL if k and j == len(ws) - 1 else INK, bool(PUNCT.match(w))))
        if k:
            it.append(("(" + k + ")", RED, True))
    return it


def draw_story(canvas, story, x0, x1, H):
    d = ImageDraw.Draw(canvas)
    items = words(chunks(story))
    wlen = lambda w, fv, sz: sum(sz if cjk(c) else fv.getlength(c) for c in w)
    cache = {}
    area = x1 - x0
    for sz in range(int(H * 0.215), int(H * 0.09), -2):
        fv = ImageFont.truetype(FV, sz)
        sp = fv.getlength(" ")
        lines, cur, cw = [], [], 0
        for w, col, glue in items:
            L = wlen(w, fv, sz)
            gap = 0 if not cur else sp * 0.4 if glue else sp
            if cur and cw + gap + L > area and not glue:
                lines.append((cur, cw)); cur, cw, gap = [], 0, 0
            cur.append((w, col, glue, L, gap)); cw += gap + L
        lines.append((cur, cw))
        if len(lines) * sz * 1.55 <= H * 0.92 and all(w <= area for _, w in lines):
            break
    y = (H - sz * 1.55 * len(lines)) / 2
    for ln, lw in lines:
        x = x0 + (area - lw) / 2
        for w, col, glue, L, gap in ln:
            x += gap
            for c in w:
                if cjk(c):
                    if (c, sz) not in cache:
                        cache[(c, sz)] = han_font(c, sz)
                    fc = cache[(c, sz)]
                    bb = fc.getmask(c).getbbox() if fc else None
                    if bb:
                        il, _, ir, _ = bb
                        d.text((x + (sz - (ir - il)) / 2 - fc.getbbox(c)[0] - il, y + sz * 0.02), c, font=fc, fill=col)
                    x += sz
                else:
                    d.text((x, y), c, font=fv, fill=col)
                    x += fv.getlength(c)
        y += sz * 1.55


def render(n, story):
    src = UP / f"{n:04d}.webp"
    im = Image.open(src).convert("RGB")
    W, H = im.size
    if not story:
        return im, "giữ nguyên (chưa có câu chuyện)"
    if unsupported(story):
        return im, "giữ nguyên (có ký tự không font nào vẽ được)"
    px1 = picture_right_edge(im)
    canvas = Image.new("RGB", (W, H), "white")
    canvas.paste(im.crop((0, 0, px1, H)), (0, 0))
    draw_story(canvas, story, px1 + int(0.03 * W), W - int(0.025 * W), H)
    return canvas, f"tranh {px1}/{W}px"


def work(args):
    n, story, quality = args
    try:
        img, note = render(n, story)
        tmp = OUT / f"{n:04d}.tmp.webp"
        img.save(tmp, quality=quality, method=4)
        tmp.rename(OUT / f"{n:04d}.webp")
        return n, None
    except Exception as e:  # noqa: BLE001
        return n, str(e)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cards", nargs="*", type=int)
    ap.add_argument("--quality", type=int, default=90)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--force", action="store_true", help="làm lại cả ảnh đã có")
    ap.add_argument("--compare", action="store_true")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    story = load_story()
    names = sorted(int(f.stem) for f in UP.glob("*.webp") if f.stem.isdigit())
    if a.cards:
        names = [n for n in names if n in set(a.cards)]
    if not a.compare:
        todo = [(n, story.get(n, ""), a.quality) for n in names if a.force or not (OUT / f"{n:04d}.webp").exists()]
        print(f"{len(names)} ảnh, cần làm {len(todo)} -> {OUT}", flush=True)
        errs, done = [], 0
        with ProcessPoolExecutor(a.workers) as ex:
            for n, err in ex.map(work, todo, chunksize=8):
                done += 1
                if err:
                    errs.append((n, err)); print("⚠️", n, err, flush=True)
                if done % 200 == 0:
                    print(f"{done}/{len(todo)}", flush=True)
        print("lỗi:", len(errs))
    sys.path.insert(0, str(ROOT / "tools"))
    import kanji_story_upscale as U
    U.OUT = OUT
    have = [f"{n:04d}.webp" for n in names if (OUT / f"{n:04d}.webp").exists()]
    print("so sánh:", U.compare_page(have))


if __name__ == "__main__":
    main()
