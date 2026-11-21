#!/usr/bin/env python3
"""Truyện dài Kanji -> 1 video dài: ảnh minh hoạ + chữ chạy theo giọng đọc.

Cần chạy trước:
    python3 tools/kanji_saga_audio.py
    .venv/bin/python tools/audio/tts.py build/kanji-saga-audio-text -o build/kanji-saga-audio --rate +25%
Rồi:
    .venv/bin/python tools/kanji_saga_video.py      # -> build/kanji-saga-video/truyen-kanji.mp4 (+ .srt, chapters.txt)

Canh giờ: tts.py cắt mỗi chương thành các đoạn (~1200 ký tự) và lưu từng đoạn
trong build/audio-cache. Lấy thời lượng thật của từng đoạn, rồi trong một đoạn
chia theo số ký tự -> mỗi câu lệch cùng lắm vài giây.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent / "audio"))
from kanji_saga_audio import clean  # noqa: E402
from tts import cache_key, cap, chunks  # noqa: E402

sys.argv = sys.argv[:1]
import kanji_saga_shorts as S  # noqa: E402  (thẻ Kanji giống video ngắn)

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "docs/kanji-viewer/truyen-data.js"
IMG = ROOT / "docs/kanji-viewer/truyen-img"
TEXT = ROOT / "build/kanji-saga-audio-text"
AUDIO = ROOT / "build/kanji-saga-audio"
CACHE = ROOT / "build/audio-cache"
OUT = ROOT / "build/kanji-saga-video"
VOICE, RATE, MAX_CHARS, REQ_CHARS = "vi-VN-HoaiMyNeural", "+25%", 2000, 1200
W, H = 1280, 720
FONT = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
F_HEAD = ImageFont.truetype(FONT, 26)
F_SUB = ImageFont.truetype(FONT, 36)
SUB_MAX = 170          # ký tự tối đa mỗi màn chữ (~3 dòng)


def duration(p: Path) -> float:
    return float(subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)]))


def pieces(par: str) -> list[str]:
    """Đoạn văn -> các màn chữ ngắn (theo câu, câu dài cắt ở dấu phẩy/khoảng trắng)."""
    out = []
    for s in re.split(r"(?<=[.!?…:])\s+", par):
        stack = [s.strip()]
        while stack:
            t = stack.pop(0)
            if len(t) <= SUB_MAX:
                if t:
                    out.append(t)
                continue
            mid = len(t) // 2
            cuts = [m.end() for m in re.finditer(r"[,;–]\s+", t)] or [m.end() for m in re.finditer(r"\s+", t)]
            c = min(cuts, key=lambda x: abs(x - mid))
            stack[:0] = [t[:c].strip(), t[c:].strip()]
    return out


def pauses(mp3: Path) -> list[float]:
    """Thời điểm hết mỗi khoảng lặng (= lúc câu/vế tiếp theo bắt đầu nói)."""
    err = subprocess.run(["ffmpeg", "-i", str(mp3), "-af", "silencedetect=noise=-35dB:d=0.1", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    return [float(x) for x in re.findall(r"silence_end: ([\d.]+)", err)]


def snap(pred: list[float], sil: list[float], miss: float = 2.5) -> list[float]:
    """Ghép từng mốc dự đoán với một khoảng lặng (giữ thứ tự, DP); không ghép được thì giữ dự đoán."""
    n, m = len(pred), len(sil)
    INF = float("inf")
    # dp[i][j]: chi phí tốt nhất cho i mốc đầu, đã dùng tới khoảng lặng thứ j (j = số khoảng lặng đã qua)
    dp = [[INF] * (m + 1) for _ in range(n + 1)]
    back = [[None] * (m + 1) for _ in range(n + 1)]
    for j in range(m + 1):
        dp[0][j] = 0.0
    for i in range(1, n + 1):
        for j in range(m + 1):
            best, arg = dp[i - 1][j] + miss, ("skip", j)       # mốc i không có khoảng lặng
            if j > 0 and dp[i - 1][j - 1] + abs(pred[i - 1] - sil[j - 1]) < best:
                best, arg = dp[i - 1][j - 1] + abs(pred[i - 1] - sil[j - 1]), ("match", j - 1)
            if j > 0 and dp[i][j - 1] < best:                  # bỏ qua khoảng lặng j
                best, arg = dp[i][j - 1], ("pass", j - 1)
            dp[i][j], back[i][j] = best, arg
    out, i, j = list(pred), n, m
    while i > 0:
        kind, jj = back[i][j]
        if kind == "pass":
            j = jj
            continue
        if kind == "match":
            out[i - 1] = sil[jj]
        i, j = i - 1, jj
    return out


def with_kanji(raw: str, cps: list[str]) -> list[str]:
    """Bản hiện trên màn hình của từng màn chữ: giữ chữ Hán trong ngoặc, 【雨】 -> (雨).

    Ghép theo từ: mỗi màn chữ (bản đã bỏ chữ Hán) có n từ -> lấy n từ của câu gốc,
    cộng các mảnh chú thích chữ Hán đi ngay sau."""
    toks = re.sub(r"【(.)】", r"(\1)", raw).split()
    has_word = lambda t: bool(re.search(r"[^\W\d_]|\d", clean(t)))
    out, i = [], 0
    for c in cps:
        need, buf = len(c.split()), []
        while i < len(toks) and (need > 0 or not has_word(toks[i])):
            if has_word(toks[i]):
                need -= 1
            buf.append(toks[i])
            i += 1
        out.append(" ".join(buf) or c)
    if i < len(toks) and out:
        out[-1] += " " + " ".join(toks[i:])
    return out


def chapter_timeline(n: int):
    """-> (văn bản chương, align(vị trí các màn chữ) -> hàm vị trí ký tự -> giây, tổng giây).

    Mỗi đoạn audio (~1 phút) có khoảng lặng thật ở cuối câu/dấu phẩy: đầu mỗi màn chữ
    được ghép vào khoảng lặng gần nhất, giữa các mốc thì nội suy theo ký tự."""
    text = (TEXT / f"{n:02d}.txt").read_text(encoding="utf-8")
    jobs = [c for c in chunks(text, MAX_CHARS) if re.search(r"[^\W_]", c)]
    jobs = [p for c in jobs for p in cap(c, REQ_CHARS)]
    spans, cur, t = [], 0, 0.0
    for j in jobs:
        a = text.find(j.split("\n")[0][:40], cur)
        a = cur if a < 0 else a
        mp3 = CACHE / f"{cache_key(j, VOICE, RATE)}.mp3"
        d = duration(mp3)
        spans.append([a, 0, t, d, pauses(mp3)])
        cur, t = a + len(j), t + d
    for i, sp in enumerate(spans):
        sp[1] = spans[i + 1][0] if i + 1 < len(spans) else len(text)
    scale = duration(AUDIO / f"{n:02d}.mp3") / t     # bù phần lệch do encode lại
    total = scale * t

    def align(starts: list[int]):
        anchors = []
        for a, b, t0, d, sil in spans:
            inside = sorted(p for p in set(starts) if a + 3 < p < b)
            pred = [d * (p - a) / max(1, b - a) for p in inside]
            anchors.append((a, t0))
            anchors += [(p, t0 + x) for p, x in zip(inside, snap(pred, sil))]
        anchors.append((len(text), t))
        anchors.sort()

        def at(pos: int) -> float:
            for (p0, x0), (p1, x1) in zip(anchors, anchors[1:]):
                if pos < p1:
                    return scale * (x0 + (x1 - x0) * max(0, pos - p0) / max(1, p1 - p0))
            return total
        return at
    return text, align, total


def wrap(d: ImageDraw.ImageDraw, s: str, font, width: int) -> list[str]:
    lines, cur = [], ""
    for w in s.split():
        nxt = f"{cur} {w}".strip()
        if d.textlength(nxt, font=font) <= width or not cur:
            cur = nxt
        else:
            lines.append(cur)
            cur = w
    return lines + [cur] if cur else lines


_base: dict = {}


PX, PY, PW, PH = 560, 50, 700, 404             # khung thẻ Kanji (bên phải)


def base(img: str, head: str) -> Image.Image:
    key = (img, head)
    if key not in _base:
        pic = Image.open(IMG / f"{img}.webp").convert("RGB")
        r = max(W / pic.width, H / pic.height)
        bg = pic.resize((int(pic.width * r) + 1, int(pic.height * r) + 1)).crop((0, 0, W, H))
        bg = bg.filter(ImageFilter.GaussianBlur(28)).point(lambda v: int(v * 0.3))
        fw = PX - 40
        fg = pic.resize((fw, int(fw * pic.height / pic.width)), Image.LANCZOS)
        bg.paste(fg, (20, PY + (PH - fg.height) // 2))
        d = ImageDraw.Draw(bg)
        size = 26                                   # tiêu đề dài -> thu nhỏ, chừa chỗ cho bộ đếm chữ
        while size > 16 and d.textlength(head, font=ImageFont.truetype(FONT, size)) > W - 320:
            size -= 1
        d.text((W // 2, 27), head, font=ImageFont.truetype(FONT, size), fill=(255, 214, 120), anchor="mm")
        _base.clear()
        _base[key] = bg
    return _base[key]


def frame(img: str, head: str, sub: str, dest: Path, card=None, got: int = 0) -> None:
    im = base(img, head).copy()
    d = ImageDraw.Draw(im)
    d.text((W - 20, 27), f"{got} chữ", font=F_HEAD, fill=(120, 220, 170), anchor="rm")
    if card is not None:                        # thẻ Kanji bên phải ảnh
        im.paste(card, (PX, PY), card)
    draw_sub(d, sub)
    im.save(dest, compress_level=1)


def _runs(tok: str):
    out, buf, cj = [], "", None
    for c in tok:
        isc = bool(CJK_RX.match(c))
        if cj is not None and isc != cj:
            out.append((buf, cj))
            buf = ""
        buf, cj = buf + c, isc
    if buf:
        out.append((buf, cj))
    return out


def draw_sub(d, sub: str, size: int = 36, lh: int = 48) -> None:
    """Phụ đề có cả chữ Hán, vd "trời mưa (雨) suốt 24 giờ" — chữ Việt Arial Bold, chữ Hán font Nhật."""
    fv = ImageFont.truetype(FONT, size)
    tw = lambda t: sum((S.KS.kf(r[0], size).getlength(r) if c else fv.getlength(r)) for r, c in _runs(t))
    sp, maxw = fv.getlength(" "), W - 90
    lines, cur, cw = [], [], 0.0
    for tok in sub.split():
        w = tw(tok)
        if cur and cw + sp + w > maxw:
            lines.append((cur, cw))
            cur, cw = [], 0.0
        cw += (sp if cur else 0) + w
        cur.append(tok)
    if cur:
        lines.append((cur, cw))
    if len(lines) > 5:
        return draw_sub(d, sub, size - 4, lh - 6)
    y0 = 462 + (254 - lh * len(lines)) // 2
    for i, (toks, w) in enumerate(lines):
        x, y = (W - w) / 2, y0 + i * lh + lh // 2 + size * 0.36
        for j, tok in enumerate(toks):
            if j:
                x += sp
            for r, c in _runs(tok):
                f = S.KS.kf(r[0], size) if c else fv
                d.text((x, y), r, font=f, fill=(255, 225, 140) if c else (255, 255, 255), anchor="ls",
                       stroke_width=2, stroke_fill=(0, 0, 0))
                x += f.getlength(r)


CARD_MIN, CARD_MIN_SAME, CARD_LEAD = 0.8, 0.4, 0.5   # thẻ ở ít nhất 0.8 s (0.4 s nếu cùng câu); hiện sớm 0.5 s
_cards: dict = {}
_DATA: dict = {}
CJK_RX = re.compile(r"[⺀-⿟々〆㐀-鿿豈-﫿\U00020000-\U0003FFFF]")
GREEN, GREY, INK_ = (14, 116, 92), (120, 112, 104), (34, 30, 28)
F_TXT = "/System/Library/Fonts/Supplemental/Arial.ttf"
KIMG = ROOT / "docs/kanji-viewer"                # x["img"] = "kanji_p2/1056.webp"


def kdata() -> dict:
    """chữ -> {hv, m, s, n, j}: thẻ học (kanji-game-data.js) + mảnh ghép (kanji-roadmap.js)."""
    if not _DATA:
        kanji = S.KV.js_value(S.KV.KV / "kanji-game-data.js", "KANJI")
        road = S.KV.js_value(S.KV.KV / "kanji-roadmap.js", "ROADMAP")
        for n, k, hv, m, j, st, img in kanji:
            d = _DATA.setdefault(k, {"hv": hv, "m": m, "s": "", "n": n, "j": j, "img": img})
            if st and not d["s"]:
                d.update(s=st, n=n, j=j, img=img)
        for k, hv, m, _t in road["radw"]:
            _DATA.setdefault(k, {"hv": hv, "m": m, "s": "", "n": None, "j": ""})
    return _DATA


def mixed(d, xy, text, size, fill, maxw, max_lines=2, lh=None):
    """Vẽ chữ Việt lẫn chữ Hán (mỗi loại một font), tự xuống dòng; trả y cuối."""
    fv = ImageFont.truetype(F_TXT, size)
    lh = lh or int(size * 1.35)

    def runs(tok):
        out, buf, cj = [], "", None
        for c in tok:
            isc = bool(CJK_RX.match(c))
            if cj is not None and isc != cj:
                out.append((buf, cj)); buf = ""
            buf, cj = buf + c, isc
        if buf:
            out.append((buf, cj))
        return out

    def width(tok):
        return sum((S.KS.kf(t[0], size).getlength(t) if c else fv.getlength(t)) for t, c in runs(tok))

    x0, y = xy
    lines, cur, cw = [], [], 0.0
    sp = fv.getlength(" ")
    for tok in text.split():
        w = width(tok)
        if cur and cw + sp + w > maxw:
            lines.append(cur); cur, cw = [], 0.0
        cur.append(tok); cw += (sp if len(cur) > 1 else 0) + w
    if cur:
        lines.append(cur)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1] + ["…"]
    for ln in lines:
        x = x0
        for i, tok in enumerate(ln):
            if i:
                x += sp
            for t, c in runs(tok):
                f = S.KS.kf(t[0], size) if c else fv
                d.text((x, y + size), t, font=f, fill=fill, anchor="ls")
                x += f.getlength(t)
        y += lh
    return y


def cap1(t: str) -> str:
    return t[:1].upper() + t[1:] if t else t


def kcard(k: str, pcs=None):
    """Thẻ Kanji như trang Luyện viết: chữ to, ÂM HÁN VIỆT, nghĩa, Thẻ · N, câu chuyện, các mảnh ghép."""
    if k in _cards:
        return _cards[k]
    D = kdata()
    x = D.get(k, {"hv": "", "m": "", "s": "", "n": None, "j": ""})
    im = Image.new("RGBA", (PW, PH), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, PW - 1, PH - 1], 22, fill=(250, 248, 244, 248))
    kimg = KIMG / x["img"] if x.get("img") else None
    if kimg and kimg.exists():
        # ảnh thẻ trong sách (đã có chữ, thứ tự nét, âm HV, nghĩa, câu chuyện, âm On/Kun, từ ví dụ) + các mảnh ghép
        pic = Image.open(kimg).convert("RGB")
        pw = PW - 16
        pic = pic.resize((pw, int(pw * pic.height / pic.width)), Image.LANCZOS)
        im.paste(pic, (8, 8))
        parts_y = 8 + pic.height + 8
    else:
        parts_y = None
    if parts_y is not None:
        y = parts_y
    else:
        y = draw_head(d, k, x)
    return finish(im, d, k, x, y)


def draw_head(d, k, x):
    d.text((22, 132), k, font=S.KS.kf(k, 128), fill=INK_, anchor="ls")
    tx = 175
    d.text((tx, 58), x["hv"].upper(), font=ImageFont.truetype(FONT, 44), fill=GREEN, anchor="ls")
    mixed(d, (tx, 70), cap1(x["m"].split(";")[0]), 28, INK_, PW - tx - 20, max_lines=1)
    meta = " · ".join(b for b in [f"Thẻ {x['n']}" if x["n"] else "Mảnh ghép", x["j"]] if b)
    d.text((tx, 138), meta, font=ImageFont.truetype(F_TXT, 22), fill=GREY, anchor="ls")
    y = 156
    if x["s"]:
        y = mixed(d, (18, y), x["s"], 22, INK_, PW - 36, max_lines=2, lh=29) + 4
    return y


def finish(im, d, k, x, y):
    D = kdata()
    parts = []
    for c in CJK_RX.findall(x["s"]):
        if c != k and c not in parts:
            parts.append(c)
    row_h = 33
    for c in parts[: max(0, (PH - y - 6) // row_h)]:
        p = D.get(c, {"hv": "", "m": "", "s": ""})
        d.rectangle([14, y + 2, PW - 14, y + row_h - 4], fill=(255, 255, 255, 255))
        d.rectangle([14, y + 2, 18, y + row_h - 4], fill=GREEN)
        d.text((28, y + row_h - 8), c, font=S.KS.kf(c, 25), fill=INK_, anchor="ls")
        xx = 66
        hv = p["hv"].split(",")[0].upper() or "—"
        f = ImageFont.truetype(FONT, 19)
        d.text((xx, y + row_h - 10), hv, font=f, fill=GREEN, anchor="ls")
        xx += f.getlength(hv) + 8
        desc = "– " + (f"{cap1(p['m'])}: {p['s']}" if p.get("s") else f"{p['m']} (mảnh ghép)")
        mixed(d, (xx, y + 4), desc, 19, GREY, PW - xx - 24, max_lines=1)
        y += row_h
    _cards[k] = im
    return im


_multi: dict = {}


def multicard(keys: tuple):
    """Một câu có nhiều chữ: xếp ảnh thẻ của tất cả các chữ (đã được kể tới) trong cùng khung."""
    if keys in _multi:
        return _multi[keys]
    D = kdata()
    pics = []
    for k in keys:
        x = D.get(k, {})
        f = KIMG / x["img"] if x.get("img") else None
        if f and f.exists():
            pics.append(Image.open(f).convert("RGB"))
        else:                                   # không có ảnh sách -> dùng thẻ vẽ (cắt phần đầu)
            pics.append(kcard(k).crop((0, 0, PW, 200)).convert("RGB"))
    n, pad = len(pics), 8
    ratio = sum(p.width / p.height for p in pics) / n
    best = None
    for cols in (1, 2):
        rows = -(-n // cols)
        w = min((PW - pad * (cols + 1)) / cols, (PH - pad * (rows + 1)) / rows * ratio)
        if best is None or w > best[0]:
            best = (w, cols, rows)
    w, cols, rows = best
    im = Image.new("RGBA", (PW, PH), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, PW - 1, PH - 1], 22, fill=(250, 248, 244, 248))
    cell_h = (PH - pad * (rows + 1)) / rows
    for i, p in enumerate(pics):
        r_, c_ = divmod(i, cols)
        pw = int(min(w, cell_h * p.width / p.height))
        ph = int(pw * p.height / p.width)
        q = p.resize((pw, ph), Image.LANCZOS)
        cw = (PW - pad * (cols + 1)) / cols
        x0 = int(pad + c_ * (cw + pad) + (cw - pw) / 2)
        y0 = int(pad + r_ * (cell_h + pad) + (cell_h - ph) / 2)
        im.paste(q, (x0, y0))
        if i == n - 1:                          # chữ vừa được kể: viền xanh
            d.rectangle([x0 - 3, y0 - 3, x0 + pw + 2, y0 + ph + 2], outline=GREEN, width=4)
    _multi[keys] = im
    return im


def ts(t: float, sep=",") -> str:
    return f"{int(t // 3600):02d}:{int(t % 3600 // 60):02d}:{int(t % 60):02d}{sep}{int(t * 1000 % 1000):03d}"


END_IMG = 3.0                                    # cuối mỗi đề mục: ảnh minh hoạ toàn màn hình 3 s


def full_frame(img: str, title_: str, dest: Path) -> None:
    """Ảnh minh hoạ của đề mục, to hết màn hình (nền mờ), tên đề mục ở dưới."""
    pic = Image.open(IMG / f"{img}.webp").convert("RGB")
    r = max(W / pic.width, H / pic.height)
    im = pic.resize((int(pic.width * r) + 1, int(pic.height * r) + 1)).crop((0, 0, W, H))
    im = im.filter(ImageFilter.GaussianBlur(30)).point(lambda v: int(v * 0.3))
    fg = pic.resize((W, int(W * pic.height / pic.width)), Image.LANCZOS)
    if fg.height > H - 80:
        fg = pic.resize((int((H - 80) * pic.width / pic.height), H - 80), Image.LANCZOS)
    im.paste(fg, ((W - fg.width) // 2, (H - 60 - fg.height) // 2))
    d = ImageDraw.Draw(im)
    d.text((W // 2, H - 34), title_, font=ImageFont.truetype(FONT, 30), fill=(255, 214, 120), anchor="mm",
           stroke_width=2, stroke_fill=(0, 0, 0))
    im.save(dest, compress_level=1)


def hms(t: float) -> str:
    return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{int(t % 60):02d}"


def main() -> None:
    raw = SRC.read_text(encoding="utf-8")
    saga = json.JSONDecoder().raw_decode(raw, re.search(r"window\.SAGA\s*=\s*", raw).end())[0]
    frames = OUT / "frames"
    frames.mkdir(parents=True, exist_ok=True)
    for old in frames.glob("*.png"):
        old.unlink()
    wav = OUT / "wav"
    wav.mkdir(exist_ok=True)
    silence = wav / "silence.wav"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", "600",
                    str(silence)], check=True)
    concat, aparts, srt, chap = [], [], [], []      # aparts: (file wav, từ giây, tới giây)
    gt, k_, learned = 0.0, 0, 0                     # gt = đồng hồ chung của video

    def emit(png: Path, dur: float):
        nonlocal gt
        concat.extend([f"file '{png}'", f"duration {dur:.3f}"])
        gt += dur

    for n, ch in enumerate(saga, 1):
        text, align, total = chapter_timeline(n)
        cw_ = wav / f"{n:02d}.wav"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(AUDIO / f"{n:02d}.mp3"), "-ar", "24000", "-ac", "1",
                        str(cw_)], check=True)
        chap.append((gt, ch["t"]))
        # màn chữ: (vị trí trong text, ảnh, tiêu đề, chữ, số đề mục); thẻ: (vị trí, chữ, mảnh, câu, đề mục)
        items, marks_k, cur, sid = [], [], 0, 0

        def put(img, stitle, txt, sec_i, shown_txt=None):
            nonlocal cur
            pos = text.find(txt[:30], cur)
            pos = cur if pos < 0 else pos
            items.append((pos, img, f"{ch['t']}  ·  {stitle}", shown_txt or txt, sec_i))
            cur = pos + len(txt)
            return pos

        put(ch["s"][0]["img"], ch["s"][0]["t"], ch["t"].rstrip(".") + ".", 0)
        for sec_i, sec in enumerate(ch["s"]):
            put(sec["img"], sec["t"], sec["t"].rstrip(".") + ".", sec_i)
            for p in sec["p"]:
                for rs in re.split(r"(?<=[.!?…:])\s+", p):
                    if not rs.strip():
                        continue
                    say, mk = S.speak(rs)
                    cl = clean(rs)
                    if not cl:
                        continue
                    starts_ = []
                    cps = pieces(cl)
                    for piece, shown_txt in zip(cps, with_kanji(rs, cps)):
                        starts_.append((put(sec["img"], sec["t"], piece, sec_i, shown_txt), len(piece)))
                    sid += 1                   # các chữ cùng một câu -> hiện chung một khung
                    for mp, k, pcs in mk:      # vị trí trong câu -> vị trí trong text chương
                        r = mp / max(1, len(say)) * sum(ln for _, ln in starts_)
                        for sp_, ln in starts_:
                            if r <= ln:
                                marks_k.append((sp_ + int(r), k, pcs, sid, sec_i))
                                break
                            r -= ln
                        else:
                            marks_k.append((starts_[-1][0] + starts_[-1][1], k, pcs, sid, sec_i))
        # mốc canh giờ: đầu mỗi màn chữ + mỗi dấu phẩy (đều có khoảng lặng thật trong audio)
        at = align([p for p, *_ in items] + [m.end() for m in re.finditer(r"[,;]\s+", text)])
        show, prev, prev_sid = [], -9.0, None
        for pos, k, pcs, sid_, sec_i in marks_k:
            gap = CARD_MIN_SAME if sid_ == prev_sid else CARD_MIN
            st_ = max(at(pos) - CARD_LEAD, prev + gap)
            show.append([st_, 0.0, k, pcs, sid_, sec_i])
            prev, prev_sid = st_, sid_
        for i, x in enumerate(show):
            x[1] = show[i + 1][0] if i + 1 < len(show) else total    # giữ tới khi thẻ sau hiện
        sub_t = [at(p) for p, *_ in items]
        sub_t[0] = 0.0
        # ranh giới đề mục (thời điểm đọc tên đề mục kế tiếp) -> chèn màn ôn lại đề mục trước đó
        sec_start = {}
        for i, it in enumerate(items[1:], 1):
            sec_start.setdefault(it[4], sub_t[i])
        bounds = [(sec_start[j], j - 1) for j in sorted(sec_start) if j > 0] + [(total, len(ch["s"]) - 1)]
        cuts = sorted(set(sub_t + [x[0] for x in show] + [x[1] for x in show] + [b for b, _ in bounds]))
        cuts = [c for c in cuts if 0 <= c <= total]
        seg_from, si, bi = 0.0, 0, 0
        gmap = []                                   # (giờ trong chương, giờ chung) ở đầu mỗi đoạn audio

        def review(sec_i: int, at_local: float):
            nonlocal seg_from, k_
            aparts.append((cw_, seg_from, at_local))
            seg_from = at_local
            sec = ch["s"][sec_i]
            png = frames / f"{k_:06d}.png"
            full_frame(sec["img"], sec["t"], png)
            emit(png, END_IMG)
            k_ += 1
            dur = END_IMG
            aparts.append((silence, 0.0, dur))
            gmap.append((at_local, gt))

        gmap.append((0.0, gt))
        for i in range(len(cuts) - 1):
            t0_, t1_ = cuts[i], cuts[i + 1]
            while bi < len(bounds) - 1 and bounds[bi][0] <= t0_ + 1e-6:
                review(bounds[bi][1], bounds[bi][0])
                bi += 1
            if t1_ - t0_ < 0.02:
                continue
            while si + 1 < len(items) and sub_t[si + 1] <= t0_ + 1e-6:
                si += 1
            card = next((x for x in show if x[0] <= t0_ + 1e-6 < x[1]), None)
            group = [x for x in show if card and x[4] == card[4] and x[0] <= t0_ + 1e-6]
            got = learned + sum(1 for x in show if x[0] <= t0_ + 1e-6)
            _, img, head, txt_, _ = items[si]
            png = frames / f"{k_:06d}.png"
            panel = None
            if card:
                panel = kcard(card[2], card[3]) if len(group) < 2 else multicard(tuple(x[2] for x in group))
            frame(img, head, txt_, png, panel, got)
            emit(png, t1_ - t0_)
            k_ += 1
        while bi < len(bounds):                     # ôn lại đề mục cuối chương
            review(bounds[bi][1], total)
            bi += 1
        aparts.append((cw_, seg_from, total))

        def g(t):                                   # giờ trong chương -> giờ chung (sau các màn ôn lại chèn vào)
            base = max((x for x in gmap if x[0] <= t + 1e-6), key=lambda x: x[0])
            return base[1] + (t - base[0])
        for i, it in enumerate(items):
            end_ = sub_t[i + 1] if i + 1 < len(items) else total
            srt.append(f"{len(srt) + 1}\n{ts(g(sub_t[i]))} --> {ts(g(end_) if i + 1 < len(items) else g(end_ - 1e-3))}\n{it[3]}\n")
        learned += len(show)
        print(f"chương {n}: {len(items)} màn chữ, {len(show)} thẻ Kanji, hết lúc {hms(gt)}", flush=True)
    concat.append(concat[-2])                       # concat demuxer bỏ qua duration của ảnh cuối
    (OUT / "frames.txt").write_text("\n".join(concat) + "\n")
    (OUT / "audio.txt").write_text("".join(f"file '{f}'\ninpoint {a:.4f}\noutpoint {b:.4f}\n" for f, a, b in aparts))
    (OUT / "truyen-kanji.srt").write_text("\n".join(srt), encoding="utf-8")
    (OUT / "chapters.txt").write_text("".join(f"{hms(t)} {name}\n" for t, name in chap), encoding="utf-8")
    meta = [";FFMETADATA1", "title=Hành trình của cậu Nhân — Truyện dài Kanji"]
    ends = [t for t, _ in chap[1:]] + [gt]
    for (t, name), e in zip(chap, ends):
        meta += ["[CHAPTER]", "TIMEBASE=1/1000", f"START={int(t * 1000)}", f"END={int(e * 1000)}", f"title={name}"]
    (OUT / "meta.txt").write_text("\n".join(meta) + "\n", encoding="utf-8")
    full = OUT / "truyen-kanji.m4a"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(OUT / "audio.txt"),
                    "-c:a", "aac", "-b:a", "96k", str(full)], check=True)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(full), "-c:a", "libmp3lame", "-b:a", "64k",
                    str(OUT / "truyen-kanji.mp3")], check=True)
    tmp = OUT / "truyen-kanji.tmp.mp4"              # ghi ra file tạm rồi đổi tên: mở file lúc đang render không bị hỏng
    keys = ",".join(f"{t:.3f}" for t, _ in chap)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(OUT / "frames.txt"),
                    "-i", str(full), "-i", str(OUT / "meta.txt"), "-map", "0:v", "-map", "1:a",
                    "-map_metadata", "2", "-map_chapters", "2", "-force_key_frames", keys,
                    "-vf", "fps=10,format=yuv420p", "-c:v", "libx264", "-tune", "stillimage",
                    "-preset", "veryfast", "-crf", "23", "-c:a", "copy", "-shortest",
                    "-movflags", "+faststart", str(tmp)], check=True)
    mp4 = OUT / "truyen-kanji.mp4"
    tmp.replace(mp4)
    print(f"{mp4}  ({duration(mp4) / 60:.1f} phút, {mp4.stat().st_size / 1e6:.0f} MB)")
    # 12 video theo chương (cắt đúng keyframe đầu chương, không encode lại)
    sub = OUT / "chuong"
    sub.mkdir(exist_ok=True)
    for i, ((t, name), e) in enumerate(zip(chap, ends), 1):
        dst = sub / f"{i:02d} - {name.split('. ', 1)[-1]}.mp4"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{t:.3f}", "-to", f"{e:.3f}", "-i", str(mp4),
                        "-map", "0:v", "-map", "0:a", "-c", "copy", "-map_chapters", "-1",
                        "-metadata", f"title={name}", "-movflags", "+faststart", str(dst)], check=True)
        print(f"  {dst.name}  ({duration(dst) / 60:.1f} phút)")


if __name__ == "__main__":
    main()
