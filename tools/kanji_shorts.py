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

import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kanji_video as KV  # noqa: E402
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


def chip(ch: str, hv: str, size=54) -> Image.Image:
    """Nhãn mảnh ghép: ô tròn trắng viền xanh, chữ Hán + âm Hán Việt."""
    f2 = font(F_BOLD, 24)
    w = int(max(size * 1.25, f2.getlength(hv) + 28))
    h = int(size * 1.25 + 34)
    im = Image.new("RGBA", (w + 8, h + 8), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([4, 6, w + 4, h + 6], 18, fill=(0, 0, 0, 60))
    d.rounded_rectangle([0, 0, w, h], 18, fill=(255, 255, 255, 245), outline=ACC, width=4)
    d.text((w / 2, size * 1.08), ch, font=kfont(size), fill=INK, anchor="ms")
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

    bg = bg_image(k, shot["bg"], 7 + (d0["n"] or 0))
    sprites = {}
    for ch, cid, x, y, h, how in shot["actors"]:
        sp = Image.open(CAST / f"{cid}.png").convert("RGBA")
        hh = int(SCENE * h)
        sprites[cid] = sp.resize((max(1, int(sp.width * hh / sp.height)), hh), Image.LANCZOS)
    pieces = [c for c in KV.parts_of(k, d0["s"])]
    chips = {c: chip(c, title(info[c]["hv"]) if c in info and info[c]["hv"] else "") for c in pieces}
    f_hv, f_m, f_sub = font(F_BOLD, 44), font(F_TXT, 34), font(F_BOLD, 40)
    sub_lines = wrap(say, f_sub, W - 90)

    def anchor_of(ch):
        for c, cid, x, y, h, how in shot["actors"]:
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
        for ch, cid, x, y, h, how in shot["actors"]:
            t0 = at.get(ch, lead) - 0.35
            p = (t - t0) / 0.9
            if p <= 0:
                continue
            sp = sprites[cid]
            side = -1 if x < 0.5 else 1
            cx = x * SCENE + side * (1 - ease(p)) * (SCENE * 0.6)
            walking = p < 1
            bob = abs(math.sin(t * 9)) * 14 if walking else math.sin(t * 2.2) * 3
            fy = y * SCENE - sp.height - bob
            sh_w = sp.width * 0.7
            sd.ellipse([cx - sh_w / 2, y * SCENE - 12, cx + sh_w / 2, y * SCENE + 8], fill=(0, 0, 0, 55))
            spr = sp.rotate(math.sin(t * 9) * 4, resample=Image.BICUBIC, expand=False) if walking else sp
            scene.alpha_composite(spr, (int(cx - sp.width / 2), int(fy)))
        # --- nhãn mảnh ghép bật lên lúc được nhắc
        for c in pieces:
            if c not in at:
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
            x = (SCENE - sum(ws)) / 2
            for (kind, c), w_ in zip(items, ws):
                cx = x + w_ / 2
                x += w_
                if kind == "p":
                    q = ease(te / 0.5)
                    sd.text((cx, SCENE / 2 + 40), c, font=kfont(int(100 * q) or 1), fill=INK, anchor="ms")
                elif kind in "+=":
                    if te > 0.6:
                        sd.text((cx, SCENE / 2 + 20), c, font=font(F_BOLD, 56), fill=MUTED, anchor="ms")
                else:
                    q = pop((te - 0.9) / 0.5)
                    if q > 0:
                        sd.text((cx, SCENE / 2 + 45), c, font=kfont(max(1, int(130 * q))), fill=HL, anchor="ms")
            if te > 1.2:
                sd.text((SCENE / 2, SCENE / 2 + 140), " + ".join(title(info[c]["hv"]) for c in pieces) + " = " + title(d0["hv"]),
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
    only = sys.argv[1:] or list(SHOTS)
    for k in only:
        dest = OUT / f"{info[k]['n']:04d}-{k}.mp4"
        make_short(k, info, SHOTS[k], dest)
        print("->", dest.relative_to(ROOT), f"{duration(dest):.1f}s", flush=True)


if __name__ == "__main__":
    main()
