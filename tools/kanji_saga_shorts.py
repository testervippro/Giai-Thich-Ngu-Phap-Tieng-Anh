#!/usr/bin/env python3
"""Series video ngắn (9:16) kể truyện dài "Hành trình của cậu Nhân" (tools/data/kanji_saga/*.txt).

Mỗi tập = vài đoạn liền nhau trong 1 chương (~6–10 chữ Kanji, 30–45 s):
  móc câu (TẬP n + lưới chữ sẽ học)  ->  kể từng câu: phụ đề karaoke ở trên (vùng an toàn), cảnh theo từ khóa,
  cậu Nhân + nhân vật được nhắc tới, thẻ Kanji bật ra đúng lúc được kể rồi bay vào "khay sưu tập" trên cùng,
  đồ vật / cảm xúc từ từ điển lời kể  ->  ôn lại (lưới chữ + âm Hán Việt, có đọc)  ->  "TẬP SAU".

    .venv/bin/python tools/kanji_saga_shorts.py            # mọi tập -> build/kanji-saga-shorts/
    .venv/bin/python tools/kanji_saga_shorts.py 1 2 3      # vài tập
    .venv/bin/python tools/kanji_saga_shorts.py --list     # in danh sách tập
"""
from __future__ import annotations

import math
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kanji_shorts as KS  # noqa: E402
import kanji_video as KV  # noqa: E402
from kanji_video import ACC, BG, F_BOLD, F_TXT, HL, INK, MUTED, duration, ease, font, kfont, title, tts  # noqa: E402

KV.RATE = "+10%"
ROOT = KV.ROOT
SAGA = ROOT / "tools/data/kanji_saga"
OUT = ROOT / "build/kanji-saga-shorts"
W, H, FPS = 720, 1280, 24
SCENE, SX, SY = 600, 60, 440
SUB_Y = 236                     # phụ đề (vùng an toàn, trên cảnh)
TRAY_Y = 84                     # khay sưu tập chữ
MAX_K, MAX_W = 10, 115          # mỗi tập tối đa ~10 chữ / ~115 từ
END_T = 1.6
SERIES = "HÀNH TRÌNH CỦA CẬU NHÂN"


# ------------------------------------------------------------------ chia tập
def chapters():
    out = []
    for f in sorted(SAGA.glob("*.txt")):
        ls = [l.strip() for l in f.read_text(encoding="utf-8").splitlines() if l.strip()]
        out.append((ls[0].lstrip("# ").strip(), ls[1:]))
    return out


def episodes():
    eps = []
    for ci, (ct, paras) in enumerate(chapters(), 1):
        cur, nk, nw = [], 0, 0
        for p in paras:
            k = p.count("【")
            w = len(re.sub(r"\([^)]*\)|【.】", "", p).split())
            if cur and (nk + k > MAX_K or nw + w > MAX_W):
                eps.append(dict(ch=ci, ct=ct, paras=cur))
                cur, nk, nw = [], 0, 0
            cur.append(p)
            nk += k
            nw += w
        if cur:
            eps.append(dict(ch=ci, ct=ct, paras=cur))
    for i, e in enumerate(eps, 1):
        e["n"] = i
        e["kanji"] = [m for p in e["paras"] for m in re.findall(r"【(.)】", p)]
    return eps


# ------------------------------------------------------------------ câu -> lời đọc + vị trí chữ
def sentences(paras):
    out = []
    for p in paras:
        out += [s.strip() for s in re.split(r"(?<=[.!?…])\s+(?=[^\s])", p) if s.strip()]
    return out


def speak(sent: str):
    """'Người (亻) ngồi ... nghỉ ngơi 【休】.' -> ('Người ngồi ... nghỉ ngơi.', [(vị trí, '休', ['亻','木'])])"""
    raw, marks, pcs = "", [], []
    for tok in re.split(r"(【.】|\([^)]*\))", sent):
        if tok.startswith("【"):
            raw += "\x01"
            marks.append((tok[1], pcs))
            pcs = []
        elif tok.startswith("("):
            pcs += [c for c in tok[1:-1] if KV.CJK.match(c)]
        else:
            raw += tok
    raw = re.sub(r"\s+", " ", raw)
    raw = re.sub(r"\s+(\x01*)\s*([,.;:!?…])", r"\1\2", raw).strip()
    pos, clean = [], ""
    for ch in raw:
        if ch == "\x01":
            pos.append(len(clean))
        else:
            clean += ch
    clean = re.sub(r"\s{2,}", " ", clean)
    return clean, [(p, k, pc) for p, (k, pc) in zip(pos, marks)]


# ------------------------------------------------------------------ động từ -> nhân vật diễn
ACTS = [(re.compile(rx), a) for rx, a in [
    (r"nhảy múa|\bmúa\b|khiêu vũ|\bnhảy\b", "dance"),
    (r"\bchạy\b|\bđuổi\b|lao tới|\bvội\b|đào tẩu|\btrốn\b", "run"),
    (r"\bbay\b|\btrèo\b|\bleo\b", "fly"),
    (r"\bngã\b|rơi xuống|\bđổ\b", "fall"),
    (r"\bnằm\b|\bngủ\b|\bchết\b|bị bệnh|\bốm\b|mệt", "lie"),
    (r"\bngồi\b|nghỉ ngơi", "sit"),
    (r"\bkhóc\b|nước mắt|\bbuồn\b", "cry"),
    (r"\bđánh\b|công kích|tấn công|\bchém\b|\bbắn\b|\bđấm\b|\bđập\b|ẩu đả|chiến đấu|\bđá\b(?= vào)", "fight"),
    (r"\bsợ\b|hoảng|\brun\b|\bgiận\b|\btức\b|phẫn nộ", "shake"),
    (r"\băn\b|\buống\b|\bnếm\b|\bnướng\b", "eat"),
    (r"suy nghĩ|\bnghĩ\b|\bnhớ\b|\bmơ\b|tưởng|\bhọc\b|\bđọc\b|\bviết\b", "think"),
    (r"\bnói\b|\bhỏi\b|\bkể\b|\bgọi\b|\bhát\b|\bdạy\b|\bkêu\b|\bhét\b|\bbảo\b|trình bày", "talk"),
    (r"\bvui\b|\bcười\b|mừng|\breo\b|hoan hỉ|hạnh phúc", "jump"),
    (r"\bđi\b|\bbước\b|\bdẫn\b|\btới\b|\bvề\b|\bđến\b|lên đường", "walk"),
]]
STAY = {"lie", "sit"}               # giữ tư thế tới hết câu
VERB_COL, NOUN_COL = (124, 58, 237), ACC


def pose(act, dt, j):
    """-> (dx, dy, góc, co ngang, co dọc) của nhân vật đang diễn động tác `act` được dt giây."""
    if act is None or dt < 0:
        return 0, 0, 0, 1, 1
    e = ease(min(1.0, dt / 0.35))
    if act == "dance":
        return math.sin(dt * 9) * 14, -abs(math.sin(dt * 7)) * 50, math.sin(dt * 9) * 12, 1, 1
    if act == "jump":
        return 0, -abs(math.sin(dt * 6)) * 60 * max(0.0, 1 - dt / 1.6), 0, 1, 1
    if act == "run":
        return (1 if j % 2 == 0 else -1) * min(dt, 1.2) * 70, -abs(math.sin(dt * 14)) * 12, -10 * e, 1, 1
    if act == "walk":
        return (1 if j % 2 == 0 else -1) * min(dt, 1.4) * 35, -abs(math.sin(dt * 9)) * 9, 0, 1, 1
    if act == "fly":
        return 0, -min(dt, 1.0) * 110 + math.sin(dt * 5) * 6, math.sin(dt * 4) * 5, 1, 1
    if act == "fall":
        return 0, 0, -85 * e, 1, 1
    if act == "lie":
        return 0, 0, -80 * e, 1, 1
    if act == "sit":
        return 0, 0, 0, 1 + 0.06 * e, 1 - 0.2 * e
    if act == "fight":
        return math.sin(dt * 30) * 16 * max(0.0, 1 - dt / 1.4) + 25 * e * (1 if j % 2 == 0 else -1), 0, 8 * e, 1, 1
    if act == "shake":
        return math.sin(dt * 55) * 7 * max(0.0, 1 - dt / 1.6), 0, 0, 1, 1
    if act == "eat":
        return 0, 0, 0, 1 + 0.05 * abs(math.sin(dt * 16)), 1 - 0.04 * abs(math.sin(dt * 16))
    if act == "talk":
        return 0, -abs(math.sin(dt * 10)) * 5, math.sin(dt * 6) * 3, 1, 1
    return 0, -abs(math.sin(dt * 3)) * 4, 0, 1, 1          # think, cry


# ------------------------------------------------------------------ hình
_IMG = {}


def sprite(cid: str, h: int):
    key = ("c", cid, h)
    if key not in _IMG:
        sp = Image.open(KS.CAST / f"{cid}.png").convert("RGBA")
        _IMG[key] = sp.resize((max(1, int(sp.width * h / sp.height)), h), Image.LANCZOS)
    return _IMG[key]


def emoji(e: str, s: int):
    key = ("e", e, s)
    if key not in _IMG:
        im = Image.open(KS.emoji_png(e)).convert("RGBA")
        sc = s / max(im.size)
        _IMG[key] = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))), Image.LANCZOS)
    return _IMG[key]


def bg_img(path: Path):
    key = ("b", str(path))
    if key not in _IMG:
        _IMG[key] = Image.open(path).convert("RGB").resize((SCENE + 60, SCENE + 60), Image.LANCZOS).convert("RGBA")
    return _IMG[key]


def card(k: str, info, pcs):
    """Thẻ Kanji: chữ to + ÂM HÁN VIỆT + nghĩa + mảnh ghép."""
    key = ("k", k)
    if key in _IMG:
        return _IMG[key]
    x = info.get(k, {})
    w, h = 330, 300
    im = Image.new("RGBA", (w + 10, h + 12), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([5, 10, w + 5, h + 10], 26, fill=(0, 0, 0, 60))
    d.rounded_rectangle([0, 0, w, h], 26, fill=(255, 255, 255, 250), outline=ACC, width=5)
    d.text((w / 2, 150), k, font=KS.kf(k, 150), fill=INK, anchor="ms")
    d.text((w / 2, 200), title(x.get("hv", "")).upper(), font=font(F_BOLD, 36), fill=ACC, anchor="ms")
    m = x.get("m", "").split(";")[0]
    f = font(F_TXT, 26)
    while f.getlength(m) > w - 30 and len(m) > 4:
        m = m[:-2].rstrip() + "…"
    d.text((w / 2, 238), m, font=f, fill=MUTED, anchor="ms")
    if pcs:
        eq = " + ".join(pcs[:4]) + " = " + k
        fk = KS.kf(pcs[0], 30)
        d.text((w / 2, 282), eq, font=fk, fill=INK, anchor="ms")
    _IMG[key] = im
    return im


def slot(k: str, info, s: int, filled: bool):
    key = ("s", k, s, filled)
    if key not in _IMG:
        im = Image.new("RGBA", (s, s + 18), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        if filled:
            d.rounded_rectangle([0, 0, s - 1, s - 1], 12, fill=(255, 255, 255, 255), outline=ACC, width=3)
            d.text((s / 2, s * 0.8), k, font=KS.kf(k, int(s * 0.7)), fill=INK, anchor="ms")
            hv = title(info.get(k, {}).get("hv", "")).split(",")[0].split("/")[0]
            d.text((s / 2, s + 16), hv, font=font(F_BOLD, 15), fill=ACC, anchor="ms")
        else:
            d.rounded_rectangle([0, 0, s - 1, s - 1], 12, outline=(200, 190, 180, 255), width=2)
            d.text((s / 2, s * 0.68), "?", font=font(F_BOLD, int(s * 0.45)), fill=(200, 190, 180, 255), anchor="ms")
        _IMG[key] = im
    return _IMG[key]


# ------------------------------------------------------------------ dựng 1 tập
def make_episode(ep, nxt, info, dest: Path):
    sents = []
    for s in sentences(ep["paras"]):
        say, marks = speak(s)
        if not say:
            continue
        low = say.lower()
        actors, apos = ["nhan"], [0]
        for cid, rx in KS.TEXT_RX.items():
            m = re.search(rx, low)
            if cid != "nhan" and m and len(actors) < 3:
                actors.append(cid)
                apos.append(m.start())
        def subj(p):                            # chủ thể = nhân vật được nhắc gần nhất phía trước động từ
            c = [j for j, a in enumerate(apos) if a <= p]
            return max(c, key=lambda j: apos[j]) if c else 0
        objs, fxs, taken, nouns, verbs = [], [], [], [], []
        for rx, e, kind in KS.LEX:
            m = rx.search(low)
            if not m or any(m.start() < b and a < m.end() for a, b in taken):
                continue
            taken.append(m.span())
            if kind == "V":
                verbs.append(m.span())
                if e not in ("big", "small", "lie", "sit", "night", "rain") and len(fxs) < 2:
                    fxs.append((m.start(), e, subj(m.start())))
            elif kind in "GF" and len(objs) < 3:
                objs.append((m.start(), e, say[m.start():m.end()]))
                nouns.append(m.span())
        acts, at_ = [], []
        for rx, a in ACTS:
            for m in rx.finditer(low):
                if len(acts) < 4 and not any(m.start() < y and x < m.end() for x, y in at_):
                    at_.append(m.span())
                    acts.append((m.start(), subj(m.start()), a))
                    if not any(m.start() < y and x < m.end() for x, y in verbs):
                        verbs.append(m.span())
        acts.sort()
        bgp, _ = KS.keyword_bg(ep["kanji"][0] if ep["kanji"] else "人", low)
        sents.append(dict(say=say, marks=marks, actors=actors, objs=objs, fxs=fxs, acts=acts, bg=bgp,
                          nouns=nouns, verbs=verbs))
    n_k = len(ep["kanji"])
    intro = f"Tập {ep['n']}. {n_k} chữ Kanji trong một câu chuyện." if n_k else f"Tập {ep['n']}."
    recap_say = "Ôn lại: " + ", ".join(title(info[k]["hv"]).split(",")[0].split("/")[0] for k in ep["kanji"]) + "." if n_k else ""
    a_intro = tts(intro)
    t_intro = duration(a_intro) + 0.35
    for s_ in sents:
        s_["a"] = tts(s_["say"])
        s_["d"] = duration(s_["a"]) + 0.25
    a_rec = tts(recap_say) if recap_say else None
    t_rec = (duration(a_rec) + 0.6) if a_rec else 0.0
    # mốc thời gian
    t0 = t_intro
    learn = []                                  # (thời điểm, chữ, mảnh)
    for s_ in sents:
        s_["t0"] = t0
        L = max(1, len(s_["say"]))
        dur = s_["d"] - 0.25
        for p, k, pc in s_["marks"]:
            learn.append((t0 + dur * min(1.0, p / L) - 0.15, k, pc))
        t0 += s_["d"]
    t_story_end = t0
    show, prev = [], -9.0                       # lịch hiện thẻ: (bắt đầu, kết thúc, chữ, mảnh)
    for tt, k, pc in learn:
        st_ = max(tt, prev + 1.1)
        show.append([st_, 0, k, pc])
        prev = st_
    for i, x in enumerate(show):
        x[1] = max(x[0] + 1.1, show[i + 1][0]) if i + 1 < len(show) else min(x[0] + 2.2, t_story_end + 0.4)
    learn = [(x[0], x[2], x[3]) for x in show]
    total = t0 + t_rec + END_T
    order = [k for _, k, _ in learn]

    f_hdr, f_sub = font(F_BOLD, 22), font(F_BOLD, 36)
    hooks = font(F_BOLD, 40)
    slot_s = min(64, int((W - 40) / max(1, n_k)) - 8)

    def sub_layout(say):
        f, lh = f_sub, 46
        lines = KS.wrap(say, f, W - 60)
        if len(lines) > 4:
            f, lh = font(F_BOLD, 30), 38
            lines = KS.wrap(say, f, W - 50)
        return f, lh, lines
    for s_ in sents:
        s_["sub"] = sub_layout(s_["say"])

    def cur_sent(t):
        for s_ in reversed(sents):
            if t >= s_["t0"]:
                return s_
        return None

    def frame(t):
        im = Image.new("RGBA", (W, H), BG + (255,))
        d = ImageDraw.Draw(im)
        # header
        d.text((22, 44), f"{SERIES} · TẬP {ep['n']}", font=f_hdr, fill=MUTED, anchor="ls")
        got = sum(1 for tt, _, _ in learn if t >= tt + 0.6)
        d.text((W - 22, 44), f"{got}/{n_k} chữ", font=f_hdr, fill=ACC, anchor="rs")
        # khay sưu tập
        if n_k:
            x0 = (W - n_k * (slot_s + 8) + 8) / 2
            for i, k in enumerate(order):
                filled = t >= learn[i][0] + 0.6
                sl = slot(k, info, slot_s, filled)
                im.alpha_composite(sl, (int(x0 + i * (slot_s + 8)), TRAY_Y))
        # cảnh
        scene = Image.new("RGBA", (SCENE, SCENE), (255, 255, 255, 255))
        s_ = cur_sent(t)
        if t < t_intro or s_ is None or t >= t_story_end:
            scene.alpha_composite(bg_img(sents[0]["bg"]).crop((30, 30, 30 + SCENE, 30 + SCENE)) if sents else scene)
        else:
            idx = sents.index(s_)
            z = (t - s_["t0"]) / max(0.1, s_["d"])
            b = bg_img(s_["bg"])
            ox = int(10 + 40 * z)
            scene.alpha_composite(b.crop((ox, 30, ox + SCENE, 30 + SCENE)))
            if idx and sents[idx - 1]["bg"] != s_["bg"] and t - s_["t0"] < 0.35:
                pb = bg_img(sents[idx - 1]["bg"]).crop((50, 30, 50 + SCENE, 30 + SCENE))
                pb.putalpha(pb.getchannel("A").point(lambda v: int(v * (1 - (t - s_["t0"]) / 0.35))))
                scene.alpha_composite(pb)
            sd = ImageDraw.Draw(scene)
            L = max(1, len(s_["say"]))
            dur = s_["d"] - 0.25
            # nhân vật: diễn động tác của động từ trong câu
            xs = {1: [0.3], 2: [0.24, 0.7], 3: [0.2, 0.52, 0.82]}[len(s_["actors"])]
            heads = []
            for j, (cid, xx) in enumerate(zip(s_["actors"], xs)):
                h_ = int(SCENE * KS.SIZE.get(cid, 0.4) * (0.95 if len(s_["actors"]) > 2 else 1))
                sp = sprite(cid, h_)
                p = 1.0 if (j == 0 and idx) else ease((t - s_["t0"] - 0.1 * j) / 0.6)
                if p <= 0:
                    heads.append((xx * SCENE, SCENE * 0.5))
                    continue
                act, adt = None, 0.0
                for ap, aj, an in s_["acts"]:
                    tt = s_["t0"] + dur * min(1.0, ap / L) - 0.1
                    if aj == j and t >= tt and (an in STAY or t - tt < 1.8):
                        act, adt = an, t - tt
                dx, dy, rot, kx, ky = pose(act, adt, j)
                if kx != 1 or ky != 1:
                    sp = sp.resize((max(1, int(sp.width * kx)), max(1, int(sp.height * ky))), Image.LANCZOS)
                if rot:
                    sp = sp.rotate(rot, resample=Image.BICUBIC, expand=True)
                cx = xx * SCENE + (1 - p) * SCENE * (0.5 if xx > 0.5 else -0.5) + dx
                cx = min(SCENE - sp.width * 0.35, max(sp.width * 0.35, cx))
                gy = SCENE * 0.96
                bob = abs(math.sin(t * 8 + j)) * 10 if p < 1 else (math.sin(t * 2 + j) * 3 if act is None else 0)
                sw = sp.width * 0.35 * (1 + dy / 200)
                sd.ellipse([cx - sw, gy - 10, cx + sw, gy + 8], fill=(0, 0, 0, 50))
                top = gy - sp.height - bob + dy
                scene.alpha_composite(sp, (int(cx - sp.width / 2), int(top)))
                heads.append((cx, top))
                # hiệu ứng đi kèm động tác
                if act == "run" and adt < 1.6:
                    for q_ in range(3):
                        r_ = 8 + q_ * 5 + (adt * 30) % 10
                        sd.ellipse([cx - sp.width / 2 - 20 - q_ * 22 - r_, gy - 14 - r_, cx - sp.width / 2 - 20 - q_ * 22 + r_, gy - 14 + r_],
                                   fill=(190, 180, 170, int(150 * max(0.0, 1 - adt / 1.6))))
                if act == "cry":
                    for q_ in range(2):
                        ty = top + sp.height * 0.3 + ((adt * 120 + q_ * 40) % 90)
                        tx = cx + (q_ * 2 - 1) * sp.width * 0.12
                        sd.ellipse([tx - 5, ty - 8, tx + 5, ty + 8], fill=(90, 160, 240, 220))
                if act == "think" and adt < 1.8:
                    bx, by = cx + sp.width * 0.45, top - 10
                    for q_, r_ in enumerate((7, 11, 30)):
                        oy = by - q_ * 22 - (22 if q_ == 2 else 0)
                        sd.ellipse([bx + q_ * 14 - r_, oy - r_ * 0.8, bx + q_ * 14 + r_, oy + r_ * 0.8], fill=(255, 255, 255, 235), outline=(180, 170, 160, 255))
                if act == "talk" and adt < 1.6 and int(adt * 6) % 2 == 0:
                    bx, by = cx + sp.width * 0.42, top + 10
                    sd.rounded_rectangle([bx, by - 34, bx + 62, by], 14, fill=(255, 255, 255, 240), outline=(180, 170, 160, 255))
                    sd.text((bx + 31, by - 10), "...", font=font(F_BOLD, 26), fill=INK, anchor="ms")
                if act == "fight" and 0.15 < adt < 1.2:
                    ei = emoji("💥", 64)
                    fx_ = cx + (1 if j % 2 == 0 else -1) * sp.width * 0.6
                    scene.alpha_composite(ei, (int(fx_ - 32), int(top + sp.height * 0.3)))
            # đồ vật từ lời kể (danh từ) + nhãn chữ
            spots = [(0.86, 0.28), (0.14, 0.28), (0.86, 0.56)]
            for j, (p, e, word) in enumerate(s_["objs"]):
                tt = s_["t0"] + dur * min(1.0, p / L)
                q = KS.pop((t - tt) / 0.4)
                if q <= 0:
                    continue
                ei = emoji(e, max(1, int(96 * q)))
                x_, y_ = SCENE * spots[j][0], SCENE * spots[j][1]
                fl = math.sin(t * 2.5 + j) * 4
                scene.alpha_composite(ei, (int(x_ - ei.width / 2), int(y_ - ei.height / 2 + fl)))
                tg = KS.word_tag(word)
                scene.alpha_composite(tg, (int(min(SCENE - tg.width - 4, max(4, x_ - tg.width / 2))), int(y_ + 52 + fl)))
            # cảm xúc / động tác cạnh đầu nhân vật làm việc đó
            for j, (p, e, aj) in enumerate(s_["fxs"]):
                tt = s_["t0"] + dur * min(1.0, p / L)
                dt = t - tt
                if dt < 0 or dt > 2.0:
                    continue
                hx, hy = heads[aj] if aj < len(heads) else heads[0]
                ei = emoji(e, int(70 * KS.pop(dt / 0.35)) or 1)
                fade = 1 - max(0.0, (dt - 1.5) / 0.5)
                if fade < 1:
                    ei = ei.copy()
                    ei.putalpha(ei.getchannel("A").point(lambda v: int(v * fade)))
                scene.alpha_composite(ei, (int(min(SCENE - ei.width, hx + 30 + 60 * j)), int(max(0, hy - ei.height - dt * 20))))
        # thẻ Kanji đang học: bật ra lúc được kể, giữ >= 1,1 s (tràn sang câu sau được), rồi bay lên khay
        if t_intro <= t < t_story_end + 0.4:
            cur = [x for x in show if x[0] <= t < x[1]]
            if cur:
                s0, e0, k, pc = cur[-1]
                c = card(k, info, pc)
                q = KS.pop((t - s0) / 0.35)
                fly = ease((t - (e0 - 0.35)) / 0.35) if t > e0 - 0.35 else 0.0
                sc = q * (1 - 0.8 * fly)
                if sc > 0.02:
                    ci = c.resize((max(1, int(c.width * sc)), max(1, int(c.height * sc))), Image.LANCZOS)
                    cx, cy = SCENE / 2, 24 + c.height / 2 - fly * 280
                    scene.alpha_composite(ci, (int(cx - ci.width / 2), int(cy - ci.height / 2)))
        # móc câu: TẬP n + lưới chữ
        if t < t_intro + 0.3:
            a_ = 1 - ease((t - t_intro) / 0.3) if t > t_intro else 1.0
            scene.alpha_composite(Image.new("RGBA", scene.size, (250, 247, 242, int(240 * a_))))
            sd2 = ImageDraw.Draw(scene)
            sd2.text((SCENE / 2, 80), f"TẬP {ep['n']}", font=font(F_BOLD, 52), fill=tuple(ACC) + (int(255 * a_),), anchor="ms")
            sd2.text((SCENE / 2, 126), ep["ct"].split(". ", 1)[-1], font=font(F_BOLD, 26), fill=tuple(MUTED) + (int(255 * a_),), anchor="ms")
            cols = min(5, max(1, n_k))
            cs = min(108, int((SCENE - 40) / cols))
            for i, k in enumerate(order):
                r_, c_ = divmod(i, cols)
                q = KS.pop((t - 0.08 * i) / 0.35)
                if q <= 0:
                    continue
                sd2.text((SCENE / 2 + (c_ - (min(cols, n_k - r_ * cols) - 1) / 2) * cs, 250 + r_ * (cs + 10)), k,
                         font=KS.kf(k, max(1, int(cs * 0.82 * q))), fill=tuple(INK) + (int(255 * a_),), anchor="ms")
            sd2.rounded_rectangle([SCENE * 0.08, SCENE * 0.84, SCENE * 0.92, SCENE * 0.95], 20, fill=tuple(ACC) + (int(255 * a_),))
            sd2.text((SCENE / 2, SCENE * 0.915), f"NHỚ {n_k} CHỮ BẰNG 1 CÂU CHUYỆN", font=font(F_BOLD, 30),
                     fill=(255, 255, 255, int(255 * a_)), anchor="ms")
        # ôn lại
        if t_story_end <= t < t_story_end + t_rec:
            tr = t - t_story_end
            scene.alpha_composite(Image.new("RGBA", scene.size, (250, 247, 242, int(250 * ease(tr / 0.3)))))
            sd2 = ImageDraw.Draw(scene)
            sd2.text((SCENE / 2, 70), "ÔN LẠI", font=font(F_BOLD, 46), fill=ACC, anchor="ms")
            cols = min(4, max(1, n_k))
            cs = min(140, int((SCENE - 30) / cols))
            per = max(0.2, (t_rec - 0.6) / max(1, n_k))
            for i, k in enumerate(order):
                r_, c_ = divmod(i, cols)
                q = KS.pop((tr - 0.9 - per * i) / 0.3)
                if q <= 0:
                    continue
                x_ = SCENE / 2 + (c_ - (min(cols, n_k - r_ * cols) - 1) / 2) * cs
                y_ = 170 + r_ * (cs + 22)
                sd2.text((x_, y_), k, font=KS.kf(k, max(1, int(cs * 0.6 * q))), fill=INK, anchor="ms")
                hv = title(info[k]["hv"]).split(",")[0].split("/")[0].upper()
                sd2.text((x_, y_ + 34), hv, font=font(F_BOLD, 22), fill=ACC, anchor="ms")
        # tập sau
        if t >= total - END_T:
            te = t - (total - END_T)
            scene.alpha_composite(Image.new("RGBA", scene.size, (250, 247, 242, int(255 * ease(te / 0.3)))))
            sd2 = ImageDraw.Draw(scene)
            sd2.text((SCENE / 2, 120), "TẬP SAU", font=font(F_BOLD, 50), fill=ACC, anchor="ms")
            if nxt:
                ks = "".join(nxt["kanji"][:4])
                q = KS.pop((te - 0.15) / 0.4)
                if q > 0 and ks:
                    sd2.text((SCENE / 2, 330), ks, font=kfont(max(1, int(min(150, 520 / max(1, len(ks))) * q))), fill=HL, anchor="ms")
                sd2.text((SCENE / 2, 410), f"Tập {nxt['n']}: {nxt['ct'].split('. ', 1)[-1]}", font=font(F_BOLD, 26), fill=INK, anchor="ms")
            sd2.text((SCENE / 2, 500), "Theo dõi để học đủ 2.136 chữ", font=font(F_BOLD, 28), fill=MUTED, anchor="ms")
        # bo góc + dán cảnh
        mask = Image.new("L", (SCENE, SCENE), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, SCENE - 1, SCENE - 1], 34, fill=255)
        scene.putalpha(mask)
        im.alpha_composite(scene, (SX, SY))
        # phụ đề karaoke
        if s_ is not None and t_intro <= t < t_story_end:
            f, lh, lines = s_["sub"]
            prog = min(1.0, (t - s_["t0"]) / max(0.1, s_["d"] - 0.25)) * len(s_["say"])
            y = SUB_Y + (4 - len(lines)) * lh / 2
            done = 0
            for line in lines:
                x = (W - f.getlength(line)) / 2
                for wd in line.split(" "):
                    said = done + len(wd) / 2 <= prog
                    a_, b_ = done, done + len(wd)
                    kind = ("n" if any(a_ < q2 and p2 < b_ for p2, q2 in s_["nouns"]) else
                            "v" if any(a_ < q2 and p2 < b_ for p2, q2 in s_["verbs"]) else "")
                    col = NOUN_COL if kind == "n" else VERB_COL if kind == "v" else (HL if said else INK)
                    d.text((x, y), wd, font=f, fill=col, anchor="ls")
                    if kind and said:
                        d.line([x, y + 7, x + f.getlength(wd.rstrip(".,!?;:")), y + 7], fill=col, width=4)
                    x += f.getlength(wd + " ")
                    done += len(wd) + 1
                y += lh
        elif t < t_intro:
            d.text((W / 2, SUB_Y + 60), ep["ct"].split(". ", 1)[0].upper(), font=font(F_BOLD, 30), fill=MUTED, anchor="ms")
        # thanh tiến độ
        d.rectangle([0, H - 8, int(W * min(1.0, t / total)), H], fill=ACC)
        return im

    v = KV.Video()
    KV.W, KV.H, KV.FPS = W, H, FPS
    v.add(t_intro, frame, a_intro)
    for s_ in sents:
        v.add(s_["d"], (lambda t0_: (lambda tt: frame(t0_ + tt)))(s_["t0"]), s_["a"])
    if a_rec:
        v.add(t_rec, lambda tt: frame(t_story_end + tt), a_rec)
    v.add(END_T, lambda tt: frame(total - END_T + tt))
    v.render(dest)
    return total


def _job(args):
    i, eps = args
    ep = eps[i]
    dest = OUT / f"tap-{ep['n']:03d}.mp4"
    try:
        if dest.exists() and "--force" not in sys.argv:
            return ep["n"], "skip", 0
        info = _info()
        tot = make_episode(ep, eps[i + 1] if i + 1 < len(eps) else None, info, dest)
        return ep["n"], "ok", tot
    except Exception as e:  # noqa: BLE001
        return ep["n"], "ERR " + repr(e)[:200], 0


_INFO = None


def _info():
    global _INFO
    if _INFO is None:
        _, _INFO, _ = KV.load_data()
    return _INFO


def main():
    import multiprocessing as mp
    eps = episodes()
    argv = sys.argv[1:]
    jobs = 6
    if "-j" in argv:
        jobs = int(argv[argv.index("-j") + 1])
        del argv[argv.index("-j"):argv.index("-j") + 2]
    args = [a for a in argv if not a.startswith("--")]
    if "--list" in sys.argv:
        for e in eps:
            print(f"Tập {e['n']:3d} · chương {e['ch']:2d} · {len(e['kanji']):2d} chữ · {''.join(e['kanji'])}")
        print(len(eps), "tập")
        return
    want = [int(a) - 1 for a in args] if args else list(range(len(eps)))
    OUT.mkdir(parents=True, exist_ok=True)
    with mp.get_context("spawn").Pool(jobs) as pool:
        for k, (n, st, tot) in enumerate(pool.imap_unordered(_job, [(i, eps) for i in want]), 1):
            print(f"[{k}/{len(want)}] tập {n} {st} {tot:.0f}s", flush=True)


if __name__ == "__main__":
    main()
