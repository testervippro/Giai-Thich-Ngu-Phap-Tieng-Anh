#!/usr/bin/env python3
"""Ảnh câu chuyện Kanji -> GIF động 5 giây để nhớ nhanh (không dùng AI).

  0.0–0.6s  tranh hiện ra (mờ dần + phóng nhẹ)
  0.6–3.4s  câu chuyện hiện lần lượt từng cụm; chữ Hán trong ngoặc "bật" lên màu đỏ
  3.4–5.0s  chữ Kanji to + âm Hán Việt + nghĩa hiện ra, giữ tới cuối (GIF lặp lại)

Tranh lấy từ docs/kanji-viewer/kanji_story/NNNN.webp (phần bên trái), câu chuyện + nghĩa từ kanji-game-data.js.

    python3 tools/kanji_story_gif.py --out DIR 17 23 100
    python3 tools/kanji_story_gif.py --out DIR --all
"""
import json, os, re, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hanzi_story_retext as R   # dùng lại: tách tranh, font chữ Hán

ROOT = R.ROOT
STORY = os.path.join(ROOT, 'docs/kanji-viewer/kanji_story/%04d.webp')
W, H = 800, 220            # khung GIF
FPS, DUR = 12, 5.0
INK, TEAL, RED, MUTED = (35, 35, 35), (30, 125, 175), (185, 35, 40), (120, 120, 120)
F_VI = '/System/Library/Fonts/Avenir Next.ttc'   # index 1 = Bold Italic, 5 = Medium


def load_kanji():
    t = open(os.path.join(ROOT, 'docs/kanji-viewer/kanji-game-data.js'), encoding='utf-8').read()
    arr = json.JSONDecoder().raw_decode(t[t.index('[', t.index('window.KANJI')):])[0]
    return {r[0]: r for r in arr}


def vi(size, idx=1):
    return ImageFont.truetype(F_VI, size, index=idx)


def cjk(c, size):
    return R.font_for(c, size) or R.cjk_font(0, size)


def picture(n):
    im = Image.open(STORY % n).convert('RGB')
    a = np.asarray(im).astype(int)
    x1 = R.split_picture(a)
    if x1 is None:
        return None
    pic = im.crop((0, 0, x1 + 8, im.height))
    # bỏ khoảng trắng thừa quanh tranh
    g = np.asarray(pic.convert('L')) < 235
    # bỏ các hàng chỉ có 1 đường kẻ mảnh (viền ảnh gốc) ở mép trên/dưới
    rows = g.mean(1)
    for _ in range(2):
        r = np.where(rows > 0.01)[0]
        if len(r) > 2:
            top = r[0]; band = r[r < top + 6]
            if len(band) <= 4 and not (rows[top + 6:top + 20] > 0.01).any():
                g[:top + 6] = False; rows = g.mean(1)
            bot = r[-1]; band = r[r > bot - 6]
            if len(band) <= 4 and not (rows[max(bot - 20, 0):bot - 6] > 0.01).any():
                g[bot - 5:] = False; rows = g.mean(1)
    ys, xs = np.where(g)
    if len(xs):
        pic = pic.crop((max(xs.min() - 6, 0), max(ys.min() - 6, 0), min(xs.max() + 7, pic.width), min(ys.max() + 7, pic.height)))
    return pic


def chunks(story):
    """'Bị 1 (一) cái đinh (丁) đè (亻)…' -> các cụm hiện lần lượt: [(văn bản, chữ Hán | None)].
    Mỗi cụm = các từ cho tới hết 1 '(chữ)'."""
    out, buf = [], []
    for m in re.finditer(r'\(([^)]*)\)|[^\s()]+', story):
        if m.group(1) is not None:
            out.append((' '.join(buf), m.group(1).strip())); buf = []
        else:
            buf.append(m.group(0))
    if buf:
        out.append((' '.join(buf), None))
    return out


def text_w(s, size):
    f = vi(size)
    return sum(size if R.is_cjk(c) else f.getlength(c) for c in s)


def layout(ch, maxw, size):
    """Xếp các cụm thành dòng; mỗi phần tử = (dòng, [(x, chữ, kiểu, chỉ số cụm)])."""
    sp = vi(size).getlength(' ')
    items = []   # (từ, kiểu, cụm)
    for i, (txt, k) in enumerate(ch):
        ws = txt.split()
        for j, w in enumerate(ws):
            items.append((w, 'key' if (k and j == len(ws) - 1) else 'txt', i))
        if k:
            items.append(('(' + k + ')', 'han', i))
    lines, cur, cw = [], [], 0
    for it in items:
        w = text_w(it[0], size)
        glue = it[1] == 'han' or re.fullmatch(r'[.,;:!?…]+', it[0])   # '(chữ)' / dấu câu dính vào từ trước
        need = w + (0 if not cur else (sp * 0.5 if glue else sp))
        if cur and cw + need > maxw and not glue:
            lines.append((cur, cw)); cur, cw = [], 0; need = w
        cur.append((it, w, glue)); cw += need
    lines.append((cur, cw))
    return lines, sp


def draw_word(d, x, y, word, kind, size, alpha, pop):
    col = {'txt': INK, 'key': TEAL, 'han': RED}[kind]
    col = tuple(int(255 - (255 - c) * alpha) for c in col)
    f = vi(size)
    for c in word:
        if R.is_cjk(c):                       # chữ Hán: căn giữa nét chữ trong ô vuông rộng = size
            s = int(size * pop)
            fc = cjk(c, s)
            l = fc.getbbox(c)[0]
            il, _, ir, _ = fc.getmask(c).getbbox()
            d.text((x + (size - (ir - il)) / 2 - l - il, y + size * 0.1 - (s - size) / 2), c, font=fc, fill=col)
            x += size
        else:
            d.text((x, y), c, font=f, fill=col)
            x += f.getlength(c)


def ease(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def frames(n, card):
    _, k, hv, m, jlpt, story = card[:6]
    pic = picture(n)
    ch = chunks(story) if story.strip() else []
    px0, pw = 14, 0
    if pic:
        ph = H - 28
        pic = pic.resize((int(pic.width * ph / pic.height), ph), Image.LANCZOS)
        if pic.width > 330:
            pic = pic.resize((330, int(pic.height * 330 / pic.width)), Image.LANCZOS)
        pw = pic.width
    tx0, tx1 = px0 + pw + 26, W - 18
    size = 30
    for size in (30, 27, 24, 22, 20):
        lines, sp = layout(ch, tx1 - tx0, size)
        if len(lines) * size * 1.55 <= H - 30:
            break
    lh = size * 1.55
    nch = max(len(ch), 1)
    t_text0, t_text1, t_big = 0.6, 3.4, 3.55
    out = []
    for fi in range(int(FPS * DUR)):
        t = fi / FPS
        im = Image.new('RGB', (W, H), 'white')
        d = ImageDraw.Draw(im)
        # tranh: hiện dần + phóng nhẹ, cuối clip nhún nhẹ
        if pic:
            a = ease(t / 0.6)
            sc = 0.92 + 0.08 * a + (0.025 * np.sin((t - 3.4) * 9) * max(0, 1 - (t - 3.4) / 1.2) if t > 3.4 else 0)
            p = pic.resize((max(1, int(pic.width * sc)), max(1, int(pic.height * sc))), Image.LANCZOS)
            if a < 1:
                p = Image.blend(Image.new('RGB', p.size, 'white'), p, a)
            im.paste(p, (px0 + (pic.width - p.width) // 2, (H - p.height) // 2))
        # pha 2: câu chuyện hiện từng cụm
        fade_out = 1 - ease((t - t_big) / 0.35) if t > t_big else 1
        if fade_out > 0 and ch:
            y = (H - lh * len(lines)) / 2
            for words, lw in lines:
                x = tx0 + (tx1 - tx0 - lw) / 2
                for i, ((w, kind, ci), ww, glue) in enumerate(words):
                    if i:
                        x += (0 if re.fullmatch(r'[.,;:!?…]+', w) else sp * 0.5) if glue else sp
                    ts = t_text0 + (t_text1 - t_text0) * ci / nch
                    a = ease((t - ts) / 0.3) * fade_out
                    if a > 0:
                        pop = 1 + 0.45 * max(0, 1 - (t - ts - 0.15) / 0.3) if kind == 'han' and t > ts + 0.15 else 1
                        draw_word(d, x, y, w, kind, size, a, pop if kind == 'han' else 1)
                    x += ww
                y += lh
        # pha 3: chữ Kanji to + Hán Việt + nghĩa
        if t > t_big:
            a = ease((t - t_big) / 0.45)
            big = int(120 * (0.6 + 0.4 * a))
            fk = cjk(k, big)
            cx = (tx0 + tx1) / 2
            col = tuple(int(255 - (255 - c) * a) for c in RED)
            bb = fk.getbbox(k)
            d.text((cx - 150 - (bb[0] + bb[2]) / 2, H / 2 - (bb[1] + bb[3]) / 2), k, font=fk, fill=col)
            fh, fm = vi(40), vi(24, 5)
            colh = tuple(int(255 - (255 - c) * a) for c in TEAL)
            colm = tuple(int(255 - (255 - c) * a) for c in INK)
            d.text((cx - 60, H / 2 - 44), hv, font=fh, fill=colh)
            mm = m if fm.getlength(m) < tx1 - cx + 50 else m[:28] + '…'
            d.text((cx - 60, H / 2 + 8), mm, font=fm, fill=colm)
            if jlpt:
                d.text((cx - 60, H / 2 + 40), jlpt, font=vi(18, 5), fill=tuple(int(255 - (255 - c) * a) for c in MUTED))
        out.append(im)
    return out


def save_gif(fr, path):
    # bảng màu chung cho cả clip -> GIF nhẹ, không nhấp nháy màu
    pal = fr[-1].quantize(colors=96, method=Image.MEDIANCUT)
    q = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in fr]
    q[0].save(path, save_all=True, append_images=q[1:], duration=int(1000 / FPS), loop=0, optimize=True)


if __name__ == '__main__':
    args = sys.argv[1:]
    out = args[args.index('--out') + 1]; os.makedirs(out, exist_ok=True)
    K = load_kanji()
    # chỉ các thẻ có câu chuyện (cột câu chuyện không rỗng) và có ảnh
    ids = sorted(n for n in K if K[n][5].strip() and os.path.exists(STORY % n)) if '--all' in args else [int(x) for x in args if x.isdigit()]
    for n in ids:
        save_gif(frames(n, K[n]), os.path.join(out, '%04d.gif' % n))
        print('%04d.gif' % n, K[n][1])
