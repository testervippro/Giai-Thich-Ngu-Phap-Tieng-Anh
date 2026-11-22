#!/usr/bin/env python3
"""Thử nghiệm: ảnh câu chuyện Kanji -> clip hoạt hình ngắn (không dùng AI video).

Tranh nhún nhẹ, lấp lánh ở chỗ được nhắc, dòng chữ đang đọc sáng lên, từ khoá chữ Hán khoanh đỏ đúng lúc
giọng đọc tới, phụ đề chạy theo giọng (edge-tts vi-VN-HoaiMyNeural), cuối clip hiện chữ to + âm Hán Việt.

    .venv/bin/python tools/kanji_story_anim.py OUT_DIR
(Hiện cấu hình tay cho thẻ 2095 須 — vị trí đầu nhân vật / dòng chữ / từ khoá đo trên ảnh.)
"""
import math
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(sys.argv[1])
FPS, W, H = 30, 1920, 1080
F_VI = "/System/Library/Fonts/Supplemental/Arial.ttf"
F_VIB = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
F_CJK = "/System/Library/Fonts/Hiragino Sans GB.ttc"
BG, INK, RED, BLUE, GREY = (250, 247, 240), (35, 35, 35), (196, 30, 36), (27, 108, 148), (140, 135, 128)

# ---- cấu hình thẻ (toạ độ trên ảnh story gốc 1148x230)
CARD = dict(
    no=2095, k="須", hv="TU", m="Cần thiết", j="N1",
    pic_w=395,                                   # phần tranh bên trái
    head=(135, 100, 62),                         # tâm + bán kính đầu nhân vật
    lines=[(430, 55, 1005, 100), (455, 110, 965, 150), (605, 160, 815, 200)],
    keys=[("tóc", "彡", (855, 52, 1008, 102), 0), ("giấy", "頁", (568, 108, 716, 152), 1), ("tu", "須", (603, 158, 722, 202), 2)],
    # cụm đọc (theo khoảng lặng của audio) -> các từ
    phrases=[(0.21, 1.66, "Trên đầu không có một cọng tóc"), (2.02, 3.00, "như tờ giấy trắng"), (3.30, 4.30, "là người tu hành.")],
    sparkle_at=[0.35, 1.3],                      # "đầu", "tóc"
)
LEAD, OUTRO = 0.6, 2.6                          # im lặng đầu clip, đoạn kết


def word_times():
    out = []
    for a, b, txt in CARD["phrases"]:
        ws = txt.split()
        n = sum(len(w) for w in ws)
        t = a
        for w in ws:
            d = (b - a) * len(w) / n
            out.append((LEAD + t, LEAD + t + d, w))
            t += d
    return out


WT = word_times()
KEY_T = {}
for kw, ch, box, line in CARD["keys"]:
    KEY_T[ch] = next(t0 for t0, t1, w in WT if w.strip(".,").lower() == kw)
VOICE_END = LEAD + CARD["phrases"][-1][1]
TOTAL = VOICE_END + OUTRO


def ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def star(d, cx, cy, r, a):
    """ngôi sao 4 cánh lấp lánh"""
    if r <= 0.5:
        return
    c = (255, 214, 64, int(255 * a))
    pts = [(cx, cy - r), (cx + r * .22, cy - r * .22), (cx + r, cy), (cx + r * .22, cy + r * .22),
           (cx, cy + r), (cx - r * .22, cy + r * .22), (cx - r, cy), (cx - r * .22, cy - r * .22)]
    d.polygon(pts, fill=c)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    fr = OUT / "frames"
    fr.mkdir(exist_ok=True)
    story = Image.open(ROOT / f"docs/kanji-viewer/kanji_story/{CARD['no']:04d}.webp").convert("RGB")
    S = 1700 / story.width
    sw, sh = round(story.width * S), round(story.height * S)
    big = story.resize((sw, sh), Image.LANCZOS)
    pic_w = round(CARD["pic_w"] * S)
    pic = big.crop((0, 0, pic_w, sh))
    text_part = big.copy()
    ImageDraw.Draw(text_part).rectangle((0, 0, pic_w, sh), fill=(255, 255, 255))
    ox, oy = (W - sw) // 2, 300
    sc = lambda b: (ox + b[0] * S, oy + b[1] * S, ox + b[2] * S, oy + b[3] * S)

    f_cap = ImageFont.truetype(F_VI, 46)
    f_capb = ImageFont.truetype(F_VIB, 46)
    f_tag = ImageFont.truetype(F_VI, 30)
    f_k = ImageFont.truetype(F_CJK, 330)
    f_hv = ImageFont.truetype(F_VIB, 96)
    f_m = ImageFont.truetype(F_VI, 54)
    f_small_k = ImageFont.truetype(F_CJK, 64)
    keywords = {kw for kw, *_ in CARD["keys"]}

    n = int(TOTAL * FPS)
    for i in range(n):
        t = i / FPS
        im = Image.new("RGB", (W, H), BG)
        d = ImageDraw.Draw(im, "RGBA")
        d.text((60, 50), f"Thẻ {CARD['no']} · {CARD['j']}", font=f_tag, fill=GREY)
        # khung ảnh
        d.rounded_rectangle((ox - 14, oy - 14, ox + sw + 14, oy + sh + 14), 28, fill=(255, 255, 255), outline=(228, 222, 210), width=3)
        im.paste(text_part, (ox, oy))
        # dòng đang đọc: nền vàng nhạt
        for li, (a, b, _) in enumerate(CARD["phrases"]):
            a, b = LEAD + a, LEAD + b
            k = ease((t - a + .15) / .25) * (1 - ease((t - b - .1) / .3))
            if k > 0:
                x0, y0, x1, y1 = sc(CARD["lines"][li])
                d.rounded_rectangle((x0 - 12, y0 - 4, x1 + 12, y1 + 4), 14, fill=(255, 226, 120, int(90 * k)))
        # từ khoá: khoanh đỏ + nảy
        for kw, ch, box, line in CARD["keys"]:
            t0 = KEY_T[ch]
            if t >= t0 - .05:
                p = ease((t - t0 + .05) / .25)
                pulse = 1 + .12 * math.sin(min(1, (t - t0) / .45) * math.pi)
                x0, y0, x1, y1 = sc(box)
                cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
                hw, hh = (x1 - x0) / 2 * pulse + 10, (y1 - y0) / 2 * pulse + 6
                d.rounded_rectangle((cx - hw, cy - hh, cx + hw, cy + hh), 16, outline=(196, 30, 36, int(230 * p)), width=5)
        # tranh: nhún nhẹ + lắc rất nhẹ
        bob = 7 * math.sin(2 * math.pi * t / 1.7)
        ang = 1.2 * math.sin(2 * math.pi * t / 3.4)
        pr = pic.rotate(ang, resample=Image.BICUBIC, expand=False, fillcolor=(255, 255, 255))
        im.paste(pr, (ox, oy + round(bob)))
        # lấp lánh quanh đầu (khi đọc "đầu", "tóc") + vệt bóng trên đỉnh đầu
        hx, hy, hr = CARD["head"]
        hx, hy, hr = ox + hx * S, oy + hy * S + bob, hr * S
        for ts_ in CARD["sparkle_at"]:
            u = t - (LEAD + ts_)
            if -0.05 < u < 1.6:
                a = math.sin(min(1, max(0, u / 1.6)) * math.pi)
                for j, (dx, dy, r0) in enumerate([(-.55, -1.15, 34), (.6, -1.05, 26), (1.05, -.35, 20), (-1.05, -.55, 18)]):
                    tw = .6 + .4 * math.sin(u * 9 + j * 1.7)
                    star(d, hx + dx * hr, hy + dy * hr, r0 * tw * a * 1.3, a)
                d.arc((hx - hr * .55, hy - hr * .8, hx + hr * .15, hy - hr * .1), 200, 260, fill=(255, 255, 255, int(220 * a)), width=9)
        # phụ đề karaoke
        spoken = [(w, t0) for t0, t1, w in WT if t >= t0]
        if spoken and t < VOICE_END + .4:
            cur_phrase = None
            for a, b, txt in CARD["phrases"]:
                if t >= LEAD + a - .05:
                    cur_phrase = txt
            ws = cur_phrase.split()
            widths = [(f_capb if w.strip(".,").lower() in keywords else f_cap).getlength(w + " ") for w in ws]
            x = (W - sum(widths)) / 2
            y = 860
            d.rounded_rectangle((x - 30, y - 22, x + sum(widths) + 20, y + 72), 20, fill=(0, 0, 0, 150))
            for w, wd in zip(ws, widths):
                said = any(ww == w and tt0 <= t for tt0, tt1, ww in WT)
                isk = w.strip(".,").lower() in keywords
                col = (255, 214, 64) if isk and said else (255, 255, 255) if said else (150, 150, 150)
                d.text((x, y), w, font=f_capb if isk else f_cap, fill=col)
                x += wd
        # kết: chữ to + âm HV + nghĩa + 2 mảnh ghép
        if t > VOICE_END - .1:
            u = ease((t - VOICE_END + .1) / .4)
            ov = Image.new("RGBA", (W, H), (250, 247, 240, int(250 * u)))
            im.paste(ov, (0, 0), ov)
            d = ImageDraw.Draw(im, "RGBA")
            s = .7 + .3 * u
            kk = Image.new("RGBA", (420, 420), (0, 0, 0, 0))
            ImageDraw.Draw(kk).text((210, 210), CARD["k"], font=f_k, fill=INK + (int(255 * u),), anchor="mm")
            kk = kk.resize((round(420 * s), round(420 * s)), Image.LANCZOS)
            im.paste(kk, (560 - kk.width // 2, 520 - kk.height // 2), kk)
            d.text((820, 380), CARD["hv"], font=f_hv, fill=RED + (int(255 * u),))
            d.text((820, 500), CARD["m"], font=f_m, fill=INK + (int(255 * u),))
            v = ease((t - VOICE_END - .5) / .5)
            x = 820
            for ch, nm in (("彡", "tóc"), ("+", ""), ("頁", "giấy"), ("=", ""), (CARD["k"], "tu")):
                d.text((x, 600), ch, font=f_small_k, fill=(RED if ch == CARD["k"] else INK) + (int(255 * v),))
                if nm:
                    d.text((x + 4, 680), nm, font=f_tag, fill=BLUE + (int(255 * v),))
                x += 95
        im.save(fr / f"{i:05d}.png")
    # audio: im lặng LEAD + giọng + "ting" nhỏ ở mỗi từ khoá
    ting = OUT / "ting.wav"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i",
                    "sine=frequency=1568:duration=0.35", "-af", "afade=t=out:st=0:d=0.35,volume=0.18", str(ting)], check=True)
    inputs = ["-i", str(OUT / "voice.mp3")]
    filt = [f"[1:a]adelay={int(LEAD * 1000)}:all=1[v]"]       # đầu vào 0 là chuỗi ảnh
    mix = ["[v]"]
    for j, ch in enumerate(KEY_T):
        inputs += ["-i", str(ting)]
        filt.append(f"[{j + 2}:a]adelay={int(KEY_T[ch] * 1000)}:all=1[t{j}]")
        mix.append(f"[t{j}]")
    filt.append("".join(mix) + f"amix=inputs={len(mix)}:normalize=0,apad=whole_dur={TOTAL:.2f}[a]")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-framerate", str(FPS), "-i", str(fr / "%05d.png"), *inputs,
                    "-filter_complex", ";".join(filt), "-map", "0:v", "-map", "[a]", "-c:v", "libx264",
                    "-pix_fmt", "yuv420p", "-crf", "20", "-c:a", "aac", "-b:a", "128k", "-shortest",
                    str(OUT / f"{CARD['no']:04d}-{CARD['k']}.mp4")], check=True)
    print(OUT / f"{CARD['no']:04d}-{CARD['k']}.mp4", f"{TOTAL:.1f}s")


if __name__ == "__main__":
    main()
