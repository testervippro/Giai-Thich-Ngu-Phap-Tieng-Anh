#!/usr/bin/env python3
"""Video ngắn dọc (9:16, kiểu Shorts/TikTok) cho câu chuyện Kanji, dùng DÀN NHÂN VẬT CỐ ĐỊNH.

Dàn nhân vật (tools/kanji_cast.py -> build/kanji-cast/<id>.png) lấy từ các mảnh hay gặp nhất trong
2.075 câu chuyện: 亻 Nhân (cậu bé khăn đỏ), 女 Nữ, 王 Vua, 士 Binh sĩ, 犬 Chó, 隹 Chim, 羊 Dê, 牛 Trâu.
Mảnh không phải nhân vật (木 cây, 口 miệng …) hiện thành nhãn nổi trên phông cảnh.

Một video (~12 s):
  tiêu đề chữ Hán + âm + nghĩa  ->  phông cảnh AI (sd-turbo, không người)  ->  nhân vật bước vào ĐÚNG LÚC lời kể
  nhắc tới, nhãn mảnh ghép bật lên trên đầu  ->  cuối: các mảnh bay vào giữa ghép thành chữ (亻 + 木 = 休).

    .venv/bin/python tools/kanji_shorts.py            # 3 video thử -> build/kanji-shorts/
"""
from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kanji_video as KV  # noqa: E402
from kanji_cast import CAST as CAST_DEF, SIZE, TEXT_RX  # noqa: E402
from kanji_video import (ACC, BG, F_BOLD, F_TXT, HL, INK, MUTED, duration, ease, font, kfont,  # noqa: E402
                         spoken, title, tts)

ROOT = KV.ROOT
CAST = ROOT / "build/kanji-cast"
OUT = ROOT / "build/kanji-shorts"
BGDIR = OUT / "bg"
W, H, FPS = 720, 1280, 24
SCENE_Y, SCENE = 300, 720          # phông cảnh vuông 720×720
BG_STYLE = (", wide establishing shot, no people, no animals, empty scene, cute flat cartoon background, "
            "children's picture book style, soft pastel colors, clean lines, no text")
LEAD, TAIL = 1.4, 3.4              # giây trước lời kể (tiêu đề) / sau lời kể (ghép chữ)

# Kịch bản thử: phông cảnh + nhân vật (mảnh, id, x giữa 0..1, chân y 0..1, cao 0..1, kiểu vào) + mảnh đạo cụ (x, y)
SHOTS = {
    "休": dict(bg="a single big leafy tree on a green meadow, sunny day, blue sky",
              actors=[("亻", "nhan", 0.30, 0.95, 0.46, "walk")],
              props=[("木", 0.66, 0.16)]),
    "件": dict(bg="a village festival square with colorful flags and paper lanterns, daytime",
              actors=[("亻", "nhan", 0.26, 0.95, 0.42, "walk"), ("牛", "nguu", 0.70, 0.96, 0.38, "walk")],
              props=[]),
    "伏": dict(bg="tall grass and bushes at night under a full moon, quiet countryside",
              actors=[("亻", "nhan", 0.32, 0.96, 0.42, "walk"), ("犬", "khuyen", 0.70, 0.97, 0.30, "walk")],
              props=[]),
}


SCENES = ROOT / "tools/data/kanji_shorts_scenes.jsonl"
PIECE2ID = {c: cid for cid, (chs, _, _) in CAST_DEF.items() for c in chs}
BODY = set("口扌手目心忄足⻊耳罒爫廾舌頁自")


NUMW = {"hai": 2, "ba": 3, "bốn": 4, "năm": 5, "sáu": 6, "bảy": 7, "tám": 8, "chín": 9, "mười": 10}
MANY = {"nhiều", "các", "những", "đàn", "bầy", "lũ", "mấy", "mọi", "đám"}
CLASSIF = {"con", "ông", "bà", "em", "người", "cô", "chị", "anh", "đứa", "cái", "chú", "vị", "được", "cả"}
# chuyện không ghi ai nhưng có người làm việc gì đó -> cậu bé Nhân diễn
DOER = (r"\b(tay|mồm|miệng|mắt|tim|chân|mình|ta|anh ấy|cô ấy|bạn|họ|ai|tôi|nằm|ngồi|đứng|uống|ăn|xem|viết|đè|"
        r"bệnh|dọn|chạy|nói|nhìn|bắt|cầm|mang|mặc|học|đọc|làm|chơi|hát|ngủ|khóc|cười|yêu)\b")


ASSETS = ROOT / "build/kanji-assets"
EMOJI = "/System/Library/Fonts/Apple Color Emoji.ttc"
HOLD = r"cầm|dùng|mang|giơ|tay|nắm|chống|quàng|đội|mặc|đeo|ôm|bê|xách"
# động tác / tính chất của mảnh (cột asset trong kanji_assets.tsv) -> hiệu ứng
FX_PIECE = {"speak": "💬", "eat": "😋", "hit": "💥", "look": "👀", "pray": "🙏", "cut": "✂️", "stop": "🛑",
            "run": "💨", "sing": "🎵", "use": "👉", "meet": "🤝", "grab": "✊", "release": "🕊️", "struggle": "😵",
            "squeeze": "💢", "point": "👉", "cross": "➡️", "big": "big", "small": "small", "sparkle": "✨",
            "good": "✅", "no": "❌", "bad": "❌", "sick": "🤒", "ouch": "💥", "love": "❤️", "laugh": "😂",
            "dead": "💀", "heavy": "💦", "spicy": "🌶️", "dry": "☀️", "dark": "night", "night": "night",
            "rain": "rain", "missing": "❓", "strange": "❓", "angry": "💢", "old": "🕰️", "born": "👶", "match": "🤝"}
# động từ / tính từ trong LỜI KỂ -> hiệu ứng (theo thứ tự ưu tiên)
FX_TEXT = [(r"không tốt|\bxấu\b", "❌"), (r"\btốt\b", "✅"), (r"\bnói\b|lời nói|hội thoại", "💬"), (r"\băn\b", "😋"),
           (r"\buống\b", "🥤"), (r"\bđánh\b", "💥"), (r"\bnhìn\b|\bxem\b", "👀"), (r"\byêu\b|\bthích\b", "❤️"),
           (r"\bcười\b", "😂"), (r"\bkhóc\b", "😭"), (r"\bngủ\b", "💤"), (r"\bchết\b", "💀"), (r"bệnh", "🤒"),
           (r"\bchạy\b", "💨"), (r"cháy|\bđốt\b", "🔥"), (r"t[ỏo]a sáng|\bsáng\b|\bđẹp\b", "✨"),
           (r"\bto\b|\blớn\b", "big"), (r"\bnhỏ\b", "small"), (r"\bmưa\b", "rain"), (r"\bđêm\b|tối", "night"),
           (r"\bcay\b", "🌶️"), (r"\bnặng\b", "💦"), (r"\bsợ\b", "😱"), (r"\bhát\b", "🎵"), (r"\bnằm\b|\bngã\b", "lie"),
           (r"tiền|giàu", "💰"), (r"\bbay\b", "🕊️"), (r"\bnóng\b", "🥵"), (r"\blạnh\b|\bbăng\b", "🥶"),
           (r"\bvui\b", "😄"), (r"\bbuồn\b", "😢"), (r"\bđau\b|thốn", "😣"), (r"\bngồi\b", "sit")]
_LIB = {}


def lib() -> dict:
    """mảnh -> (loại, tên Việt, asset) từ tools/data/kanji_assets.tsv"""
    if not _LIB:
        import kanji_assets as KA
        for p, t, vi, a in KA.load():
            _LIB[p] = (t, vi, a)
    return _LIB


def sprite_path(t: str, a: str):
    import kanji_assets as KA
    if t == "ct" and a in KA.BODY:
        return ASSETS / "dv" / f"{KA.slug(KA.BODY[a])}.png"
    if t in ("dv", "ct", "tg") and " " in a:
        return ASSETS / "dv" / f"{KA.slug(a)}.png"
    return None


def how_many(body: str, start: int) -> int:
    """'8 con lợn' -> 4 (vẽ tối đa 4), 'nhiều lợn' -> 3, '2 ông chồng' -> 2, còn lại 1."""
    ws = re.findall(r"[0-9]+|[^\W\d_]+", body[max(0, start - 30):start])
    while ws and ws[-1] in CLASSIF:
        ws.pop()
    if not ws:
        return 1
    w = ws[-1]
    n = int(w) if w.isdigit() else NUMW.get(w, 3 if w in MANY else 1)
    return max(1, min(4, n))


def auto_shot(k: str, info: dict, bg: str) -> dict:
    """Tự dàn cảnh:
    - mảnh có chữ gọi tên nhân vật đứng trước ('Ông vua (主)', 'Nguyệt (月)') -> vai theo chữ đó, không có thì theo mảnh;
    - nhân vật chỉ có trong lời kể -> vào đúng lúc được nhắc;
    - số lượng ('8 con lợn', 'nhiều lợn', '2 ông chồng') -> vẽ nhiều con/người (tối đa 4);
    - chuyện không ghi ai nhưng có người làm gì đó (tay, mồm, nằm, uống…) -> cậu bé Nhân diễn;
    - mảnh còn lại -> nhãn nổi."""
    s = info[k]["s"]
    say, _ = spoken(s, info)
    low = say.lower()
    body = re.sub(r"\s*\([^)]*\)", "", s).lower()
    actors, seen = [], set()
    prev = 0
    for m in re.finditer(r"\(([^)]+)\)", s):
        c, gloss = m.group(1), s[prev:m.start()].lower()
        prev = m.end()
        if c == k or not KV.CJK.fullmatch(c[:1]):
            continue
        cid = next((r for r, rx in TEXT_RX.items() if re.search(rx, gloss)), None) or PIECE2ID.get(c)
        if cid and cid not in seen:
            seen.add(cid)
            actors.append([c[:1], cid, None])
    for cid, rx in TEXT_RX.items():
        m = re.search(rx, low)
        if m and cid not in seen:
            seen.add(cid)
            actors.append([None, cid, m.start()])
    if not actors and (set(KV.parts_of(k, s)) & BODY or re.search(DOER, body)):
        actors.append([None, "nhan", 0])
    actors = actors[:3]
    for a in actors:
        m = re.search(TEXT_RX[a[1]], body)
        a.append(how_many(body, m.start()) if m else 1)
    xs = {1: [0.5], 2: [0.28, 0.72], 3: [0.18, 0.5, 0.82]}.get(len(actors), [])
    out = [(c, cid, x, 0.95, SIZE.get(cid, 0.44 if len(actors) < 3 else 0.38), "walk", pos, n)
           for (c, cid, pos, n), x in zip(actors, xs)]
    # --- thư viện: bối cảnh / đồ vật / hiệu ứng
    import kanji_assets as KA
    L = lib()
    used = {a[0] for a in actors}
    bgfile, objs, chipl, fx = None, [], [], []
    prev = 0
    for m in re.finditer(r"\(([^)]+)\)", s):
        c, gloss = m.group(1)[:1], s[prev:m.start()].lower()
        prev = m.end()
        if c == k or c in used or not KV.CJK.fullmatch(c):
            continue
        used.add(c)
        t, vi, a = L.get(c, (None, "", ""))
        if t == "bc":
            f = ASSETS / "bc" / f"{KA.slug(a)}.png"
            if not bgfile and f.exists():
                bgfile = f
            chipl.append(c)
            continue
        sp = sprite_path(t, a) if t else None
        if sp and sp.exists():
            objs.append((c, str(sp), bool(re.search(HOLD, gloss)) and bool(out), t))
            continue
        chipl.append(c)
        e = FX_PIECE.get(a)
        if e:
            if e == "✅" and "không" in gloss:
                e = "❌"
            fx.append((c, e))
    for rx, e in FX_TEXT:
        mm = re.search(rx, low)
        if mm and e not in {x[1] for x in fx} and not (e == "✅" and "❌" in {x[1] for x in fx}):
            fx.append((mm.start(), e))
    if "💀" in {x[1] for x in fx} and out:
        fx.append((next(x[0] for x in fx if x[1] == "💀"), "lie"))
    fx = fx[:5]
    pp = [(c, (i + 1) / (len(chipl) + 1), 0.11) for i, c in enumerate(chipl)]
    return dict(bg=bg, bgfile=str(bgfile) if bgfile else None, actors=out, props=pp, objs=objs, fx=fx)


def bg_image(k: str, prompt: str, seed: int) -> Image.Image:
    BGDIR.mkdir(parents=True, exist_ok=True)
    p = BGDIR / f"{ord(k):05x}.png"
    if not p.exists():
        import torch
        from diffusers import AutoPipelineForText2Image
        global _PIPE
        if "_PIPE" not in globals():
            _PIPE = AutoPipelineForText2Image.from_pretrained(
                "stabilityai/sd-turbo", torch_dtype=torch.float16, variant="fp16").to("mps")
            _PIPE.set_progress_bar_config(disable=True)
        _PIPE(prompt=prompt + BG_STYLE, num_inference_steps=2, guidance_scale=0.0, height=512, width=512,
              generator=torch.Generator("cpu").manual_seed(seed)).images[0].save(p)
    return Image.open(p).convert("RGB").resize((SCENE + 80, SCENE + 80), Image.LANCZOS)


_MISS = {}


def kf(ch: str, size: int):
    """Font chữ Hán; Hiragino Mincho thiếu chữ giản thể (兑…) -> dùng Songti."""
    if ch not in _MISS:
        f = kfont(60)
        def sig(c):
            m = f.getmask(c)
            return m.size, bytes(m)
        _MISS[ch] = sig(ch) == sig("\U000F0000")
    return font("/System/Library/Fonts/Supplemental/Songti.ttc", size, 0) if _MISS[ch] else kfont(size)


def chip(ch: str, hv: str, size=54) -> Image.Image:
    """Nhãn mảnh ghép: ô tròn trắng viền xanh, chữ Hán + âm Hán Việt."""
    f2 = font(F_BOLD, 24)
    w = int(max(size * 1.25, f2.getlength(hv) + 28))
    h = int(size * 1.25 + 34)
    im = Image.new("RGBA", (w + 8, h + 8), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([4, 6, w + 4, h + 6], 18, fill=(0, 0, 0, 60))
    d.rounded_rectangle([0, 0, w, h], 18, fill=(255, 255, 255, 245), outline=ACC, width=4)
    d.text((w / 2, size * 1.08), ch, font=kf(ch, size), fill=INK, anchor="ms")
    d.text((w / 2, h - 12), hv, font=f2, fill=ACC, anchor="ms")
    return im


def pop(t: float) -> float:
    """0 -> phóng to vượt 1 rồi về 1 (bật lên)."""
    if t <= 0:
        return 0.0
    if t >= 1:
        return 1.0
    return 1 + 0.25 * math.sin(t * math.pi) * (1 - t) + (ease(t) - 1)


def wrap(text: str, f, width: int) -> list[str]:
    lines, cur = [], ""
    for w in text.split():
        if cur and f.getlength(cur + " " + w) > width:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    return lines + ([cur] if cur else [])


def make_short(k: str, info: dict, shot: dict, dest: Path):
    d0 = info[k]
    say, pos = spoken(d0["s"], info)
    intro = f"{title(d0['hv'])}. {KV.end(d0['m'].split(';')[0])}"
    a_intro, a_story = tts(intro), tts(say)
    t_intro = duration(a_intro)
    lead = max(LEAD, t_intro + 0.3)
    dur_s = duration(a_story)
    total = lead + dur_s + TAIL
    L = max(1, len(say))
    at = {c: lead + dur_s * min(1.0, p / L) for c, p in pos.items()}   # lúc lời kể nhắc tới mảnh
    acts = []
    for a in shot["actors"]:
        ch, cid, x, y, h, how = a[:6]
        tp = a[6] if len(a) > 6 else None
        cnt = a[7] if len(a) > 7 else 1
        t_in = at.get(ch) if ch else (lead + dur_s * min(1.0, tp / L) if tp is not None else lead)
        acts.append((ch, cid, x, y, h * (1, 1, 0.8, 0.7, 0.62)[cnt], how, t_in if t_in is not None else lead, cnt))

    if shot.get("bgfile"):
        bg = Image.open(shot["bgfile"]).convert("RGB").resize((SCENE + 80, SCENE + 80), Image.LANCZOS)
    else:
        bg = bg_image(k, shot["bg"], 7 + (d0["n"] or 0))
    # đồ vật: đồ to (cây, xe, nhà…) đứng trên mặt đất bên phải; đồ nhỏ lơ lửng; cầm tay / bộ phận cơ thể -> cạnh nhân vật.
    # Có đồ vật thì dồn nhân vật sang trái cho đỡ chồng lên nhau.
    BIGW = ("tree", "car", "boat", "well", "wall", "door", "bamboo", "gate", "cabinet", "kimono", "stool", "house",
            "rock", "campfire", "television", "basket", "pile", "stack", "chain", "jacket")
    free = [o for o in shot.get("objs", []) if not o[2] and o[3] != "ct"]
    near = [o for o in shot.get("objs", []) if o[2] or o[3] == "ct"]
    if not acts:
        free, near = free + near, []
    if free and acts:
        n = len(acts)
        xs_ = {1: [0.3], 2: [0.18, 0.44], 3: [0.14, 0.33, 0.52]}[n]
        acts = [(a_[0], a_[1], x_, a_[3], a_[4] * (0.9 if n > 1 else 1), *a_[5:]) for a_, x_ in zip(acts, xs_)]
    objs = []
    for i, (c, f, hold, t) in enumerate(free):
        big = any(w_ in Path(f).stem for w_ in BIGW)
        n = len(free)
        lo, hi = (0.6, 0.92) if acts else (0.08, 0.92)
        x = SCENE * (lo + (hi - lo) * (i + 0.5) / n)
        sz = SCENE * min((0.46 if big else 0.3) * (1 if acts else 1.25), (hi - lo) / n * 1.05)
        yb = SCENE * (0.93 if big else (0.62 if acts else 0.7))
        objs.append((c, f, x, yb, sz))
    for i, (c, f, hold, t) in enumerate(near):
        a0 = acts[0]
        sz = SCENE * 0.17
        x = a0[2] * SCENE + SCENE * a0[4] * 0.45 + i * sz * 0.9
        yb = SCENE * (a0[3] - a0[4] * (0.25 if hold else 0.55))
        objs.append((c, f, x, yb, sz))
    oimg = {}
    for c, f, x, yb, sz in objs:
        im_ = Image.open(f).convert("RGBA")
        sc = sz / max(im_.width, im_.height)
        oimg[c] = im_.resize((max(1, int(im_.width * sc)), max(1, int(im_.height * sc))), Image.LANCZOS)
    small_chip = {c: chip(c, title(info[c]["hv"]) if c in info and info[c]["hv"] else "", size=34) for c, *_ in objs}
    # hiệu ứng: thời điểm + loại
    fxs = []
    for trig, e in shot.get("fx", []):
        tt = at.get(trig) if isinstance(trig, str) else lead + dur_s * min(1.0, trig / L)
        fxs.append((tt if tt is not None else lead, e))
    efont = ImageFont.truetype(EMOJI, 160)
    emo = {}
    for _, e in fxs:
        if e not in ("big", "small", "night", "rain", "lie", "sit"):
            ei = Image.new("RGBA", (200, 200), (0, 0, 0, 0))
            ImageDraw.Draw(ei).text((100, 100), e, font=efont, embedded_color=True, anchor="mm")
            bb = ei.getbbox()
            emo[e] = ei.crop(bb).resize((84, int(84 * (bb[3] - bb[1]) / max(1, bb[2] - bb[0]))), Image.LANCZOS) if bb else None
    moon = Image.new("RGBA", (200, 200), (0, 0, 0, 0))
    ImageDraw.Draw(moon).text((100, 100), "🌙", font=efont, embedded_color=True, anchor="mm")
    moon = moon.crop(moon.getbbox() or (0, 0, 200, 200)).resize((70, 70), Image.LANCZOS)

    def fx_val(kind):
        """mức 0..1 của hiệu ứng kéo dài (to/nhỏ/đêm/mưa/nằm/ngồi) tại thời điểm t"""
        return [tt for tt, e in fxs if e == kind]
    sprites = {}
    for ch, cid, x, y, h, how, _, _ in acts:
        sp = Image.open(CAST / f"{cid}.png").convert("RGBA")
        hh = int(SCENE * h)
        sprites[cid] = sp.resize((max(1, int(sp.width * hh / sp.height)), hh), Image.LANCZOS)
    pieces = [c for c in KV.parts_of(k, d0["s"])]
    obj_pieces = {o[0] for o in objs}
    chips = {c: chip(c, title(info[c]["hv"]) if c in info and info[c]["hv"] else "") for c in pieces}
    f_hv, f_m, f_sub = font(F_BOLD, 44), font(F_TXT, 34), font(F_BOLD, 40)
    sub_lines = wrap(say, f_sub, W - 90)

    def anchor_of(ch):
        for c, cid, x, y, h, how, _, _ in acts:
            if c == ch:
                sp = sprites[cid]
                return x * SCENE, y * SCENE - sp.height - 60
        for c, x, y in shot["props"]:
            if c == ch:
                return x * SCENE, y * SCENE
        return None

    def frame(t: float) -> Image.Image:
        im = Image.new("RGBA", (W, H), BG + (255,))
        d = ImageDraw.Draw(im)
        # --- tiêu đề
        a = ease(t / 0.6)
        d.text((W / 2, 150), k, font=kfont(int(150 * (0.8 + 0.2 * a))), fill=INK, anchor="ms")
        d.text((W / 2, 212), title(d0["hv"]).upper(), font=f_hv, fill=ACC, anchor="ms")
        d.text((W / 2, 262), d0["m"].split(";")[0], font=f_m, fill=MUTED, anchor="ms")
        # --- phông cảnh: Ken Burns chậm
        z = t / total
        ox, oy = int(40 * z), int(40 * (1 - z))
        scene = bg.crop((ox, oy, ox + SCENE, oy + SCENE)).convert("RGBA")
        sd = ImageDraw.Draw(scene)
        # --- nhân vật
        zoom = 1.0
        for tt in fx_val("big"):
            zoom *= 1 + 0.28 * ease((t - tt) / 0.5)
        for tt in fx_val("small"):
            zoom *= 1 - 0.25 * ease((t - tt) / 0.5)
        lie = max([ease((t - tt) / 0.6) for tt in fx_val("lie")] + [0])
        sit = max([ease((t - tt) / 0.4) for tt in fx_val("sit")] + [0])
        for ai, (ch, cid, x, y, h, how, t_in, cnt) in enumerate(acts):
            sp = sprites[cid]
            if ai == 0 and (zoom != 1 or sit):
                sp = sp.resize((max(1, int(sp.width * zoom)), max(1, int(sp.height * zoom * (1 - 0.18 * sit)))), Image.LANCZOS)
            if ai == 0 and lie > 0:
                sp = sp.rotate(-80 * lie, resample=Image.BICUBIC, expand=True)
            spread = sp.width * 0.62
            # nhiều con: hàng sau (lẻ) vẽ trước, cao hơn chút; vào lần lượt
            for j in sorted(range(cnt), key=lambda j: -(j % 2)):
                t0 = t_in - 0.35 + 0.18 * j
                p = (t - t0) / 0.9
                if p <= 0:
                    continue
                side = -1 if x < 0.5 else 1
                gx = x * SCENE + (j - (cnt - 1) / 2) * spread
                gx = min(SCENE - sp.width / 2, max(sp.width / 2, gx)) if cnt > 1 else gx
                gy = y * SCENE - (SCENE * 0.05 if j % 2 else 0)
                cx = gx + side * (1 - ease(p)) * (SCENE * 0.6)
                walking = p < 1
                bob = abs(math.sin(t * 9 + j)) * 14 if walking else math.sin(t * 2.2 + j) * 3
                fy = gy - sp.height - bob
                sh_w = sp.width * 0.7
                sd.ellipse([cx - sh_w / 2, gy - 12, cx + sh_w / 2, gy + 8], fill=(0, 0, 0, 55))
                spr = sp.rotate(math.sin(t * 9 + j) * 4, resample=Image.BICUBIC, expand=False) if walking else sp
                scene.alpha_composite(spr, (int(cx - sp.width / 2), int(fy)))
        # --- đồ vật hiện đúng lúc được nhắc (bật lên, lơ lửng nhẹ) + nhãn nhỏ bên dưới
        for c, f, x, yb, sz in objs:
            q = pop((t - at.get(c, lead)) / 0.45)
            if q <= 0:
                continue
            oi = oimg[c]
            ow, oh = max(1, int(oi.width * q)), max(1, int(oi.height * q))
            fl = math.sin(t * 2.5 + x) * 4
            scene.alpha_composite(oi.resize((ow, oh), Image.LANCZOS),
                                  (int(min(SCENE - ow, max(0, x - ow / 2))), int(yb - oh + fl)))
            if t <= total - TAIL + 0.2:
                cp = small_chip[c]
                scene.alpha_composite(cp, (int(min(SCENE - cp.width, max(0, x - cp.width / 2))), int(min(SCENE - cp.height, yb + 4 + fl))))
        # --- đêm / mưa
        for tt in fx_val("night"):
            a_ = ease((t - tt) / 0.8)
            if a_ > 0:
                scene.alpha_composite(Image.new("RGBA", scene.size, (20, 30, 80, int(110 * a_))))
                mo = moon.copy()
                mo.putalpha(mo.getchannel("A").point(lambda v: int(v * a_)))
                scene.alpha_composite(mo, (SCENE - 100, 24))
        for tt in fx_val("rain"):
            if t > tt:
                rd = ImageDraw.Draw(scene)
                for i in range(46):
                    rx_ = (i * 97 + 13) % SCENE
                    ry_ = (i * 53 + t * 900) % (SCENE + 60) - 30
                    rd.line([rx_, ry_, rx_ - 6, ry_ + 22], fill=(120, 160, 230, 200), width=3)
        # --- biểu tượng cảm xúc / động tác cạnh đầu nhân vật chính
        for tt, e in fxs:
            if e not in emo or emo[e] is None:
                continue
            dt = t - tt
            if dt < 0 or dt > 2.2:
                continue
            q = pop(dt / 0.4)
            fade = 1 - max(0.0, (dt - 1.7) / 0.5)
            ei = emo[e]
            ew, eh = max(1, int(ei.width * q)), max(1, int(ei.height * q))
            ei = ei.resize((ew, eh), Image.LANCZOS)
            if fade < 1:
                ei.putalpha(ei.getchannel("A").point(lambda v: int(v * fade)))
            if acts:
                a0 = acts[0]
                hx = a0[2] * SCENE + SCENE * a0[4] * 0.32
                hy = a0[3] * SCENE - SCENE * a0[4] - 20
            else:
                hx, hy = SCENE * 0.5, SCENE * 0.3
            k_ = [x_[1] for x_ in fxs if x_[1] in emo].index(e)
            hx += (k_ % 2) * 60 - 20
            scene.alpha_composite(ei, (int(min(SCENE - ew, max(0, hx - ew / 2))), int(max(0, hy - eh - dt * 30 - (k_ // 2) * 40))))
        # --- nhãn mảnh ghép (mảnh không có hình) bật lên lúc được nhắc
        for c in pieces:
            if c not in at or c in obj_pieces:
                continue
            q = pop((t - at[c]) / 0.45)
            if q <= 0 or t > total - TAIL + 0.2:
                continue
            ap = anchor_of(c) or (SCENE * (0.2 + 0.6 * pieces.index(c) / max(1, len(pieces) - 1)), SCENE * 0.12)
            cp = chips[c]
            cw, ch_ = max(1, int(cp.width * q)), max(1, int(cp.height * q))
            cpz = cp.resize((cw, ch_), Image.LANCZOS)
            float_y = math.sin(t * 3 + pieces.index(c)) * 5
            scene.alpha_composite(cpz, (int(min(SCENE - cw - 6, max(6, ap[0] - cw / 2))), int(max(6, ap[1] - ch_ / 2 + float_y))))
        # --- đoạn cuối: tối phông, các mảnh ghép thành chữ
        te = t - (total - TAIL)
        if te > 0:
            dim = Image.new("RGBA", scene.size, (250, 247, 242, int(215 * ease(te / 0.5))))
            scene.alpha_composite(dim)
            sd = ImageDraw.Draw(scene)
            n = len(pieces)
            items = []
            for c in pieces:
                items += [("p", c), ("+", "+")]
            items[-1] = ("=", "=")
            items.append(("k", k))
            ws = [120 if kind in "pk" else 50 for kind, _ in items]
            zf = min(1.0, (SCENE - 40) / sum(ws))
            ws = [w_ * zf for w_ in ws]
            x = (SCENE - sum(ws)) / 2
            for (kind, c), w_ in zip(items, ws):
                cx = x + w_ / 2
                x += w_
                if kind == "p":
                    q = ease(te / 0.5)
                    sd.text((cx, SCENE / 2 + 40), c, font=kf(c, int(100 * q * zf) or 1), fill=INK, anchor="ms")
                elif kind in "+=":
                    if te > 0.6:
                        sd.text((cx, SCENE / 2 + 20), c, font=font(F_BOLD, 56), fill=MUTED, anchor="ms")
                else:
                    q = pop((te - 0.9) / 0.5)
                    if q > 0:
                        sd.text((cx, SCENE / 2 + 45), c, font=kfont(max(1, int(130 * q * zf))), fill=HL, anchor="ms")
            if te > 1.2:
                sd.text((SCENE / 2, SCENE / 2 + 140), " + ".join(title(info[c]["hv"]) if c in info and info[c]["hv"] else c for c in pieces) + " = " + title(d0["hv"]),
                        font=font(F_BOLD, 34), fill=ACC, anchor="ms")
        # bo góc phông cảnh
        mask = Image.new("L", (SCENE, SCENE), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, SCENE - 1, SCENE - 1], 36, fill=255)
        scene.putalpha(mask)
        im.alpha_composite(scene, (0, SCENE_Y))
        # --- phụ đề: chữ đã đọc tới đổi màu cam
        if lead - 0.1 <= t:
            prog = min(1.0, (t - lead) / max(0.1, dur_s))
            spoken_n = prog * L
            y = SCENE_Y + SCENE + 64
            done = 0
            for line in sub_lines:
                lw = f_sub.getlength(line)
                x = (W - lw) / 2
                for wd in line.split(" "):
                    col = HL if done + len(wd) / 2 <= spoken_n else INK
                    d.text((x, y), wd, font=f_sub, fill=col, anchor="ls")
                    x += f_sub.getlength(wd + " ")
                    done += len(wd) + 1
                y += 54
        d.rectangle([0, H - 8, W, H], fill=ACC)
        return im

    v = KV.Video()
    KV.W, KV.H, KV.FPS = W, H, FPS          # Video.render dùng kích thước của module
    # cảnh 1: tiêu đề (đọc âm + nghĩa), cảnh 2: lời kể + phần ghép chữ
    v.add(lead, frame, a_intro)
    v.add(dur_s + TAIL, lambda tt: frame(lead + tt), a_story)
    v.render(dest)


def main():
    _, info, _ = KV.load_data()
    OUT.mkdir(parents=True, exist_ok=True)
    scenes = {}
    if SCENES.exists():
        for l in SCENES.read_text(encoding="utf-8").splitlines():
            if l.strip():
                r = json.loads(l)
                scenes[r["k"]] = r
    args = sys.argv[1:]
    force = "--force" in args
    args = [a for a in args if a != "--force"]
    only = [c for a in args for c in a] if args else list(scenes)
    for i, k in enumerate(only, 1):
        dest = OUT / f"{info[k]['n']:04d}-{k}.mp4"
        if dest.exists() and not force:
            continue
        shot = auto_shot(k, info, scenes.get(k, {}).get("bg", "a simple sunny park"))
        make_short(k, info, shot, dest)
        print(f"[{i}/{len(only)}]", dest.relative_to(ROOT), f"{duration(dest):.1f}s",
              " ".join(a[1] for a in shot["actors"]), flush=True)


if __name__ == "__main__":
    main()
