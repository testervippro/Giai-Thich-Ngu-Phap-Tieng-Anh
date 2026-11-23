#!/usr/bin/env python3
"""Vẽ lại phần CHỮ câu chuyện trên ảnh thẻ Hán tự docs/hanzi-viewer/story/NNNN.webp (chữ gốc bị mờ):
giữ nguyên phần tranh bên trái, xoá phần chữ thành nền trắng, rồi vẽ lại câu chuyện bằng một font thống nhất.
Câu chuyện lấy từ file 'n|câu chuyện' đã đánh dấu màu: {cụm từ|r} (chữ) — r g b n o p (xem PALETTE).

    python3 tools/hanzi_story_retext.py --stories FILE --out DIR 1734 2883   # vài thẻ
    python3 tools/hanzi_story_retext.py --stories FILE --out DIR --all
"""
import json, os, re, sys
import numpy as np
from fontTools.ttLib import TTCollection, TTFont
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'docs/hanzi-viewer/story/%04d.webp')
SIZE = 44
F_VI = ImageFont.truetype('/System/Library/Fonts/Avenir Next.ttc', SIZE, index=1)   # Bold Italic
# chữ Hán: thử lần lượt các font cho tới font có ký tự (bộ thủ hiếm như 𧾷 𦍌 𠃊 cần Heiti / Songti)
_CJK_SRC = [('/System/Library/Fonts/Hiragino Sans GB.ttc', 0), ('/System/Library/Fonts/STHeiti Medium.ttc', 1),
            ('/System/Library/Fonts/ヒラギノ角ゴシック W4.ttc', 0), ('/System/Library/Fonts/Supplemental/Songti.ttc', 7),
            ('/System/Library/Fonts/Supplemental/Arial Unicode.ttf', 0)]
F_CJK, CMAPS = [], []
for _p, _i in _CJK_SRC:
    if os.path.exists(_p):
        F_CJK.append(ImageFont.truetype(_p, SIZE, index=_i))
        _f = TTCollection(_p).fonts[_i] if _p.endswith('.ttc') else TTFont(_p)
        CMAPS.append(set(_f.getBestCmap()))
INK = (25, 25, 25)
# bảng màu cố định (giống màu hay gặp trên thẻ cũ): r đỏ đậm, g xanh lá, b xanh dương, n xanh tím than, o cam, p tím
PALETTE = {'r': (160, 30, 40), 'g': (55, 125, 35), 'b': (30, 125, 175), 'n': (35, 45, 120),
           'o': (205, 105, 25), 'p': (140, 50, 130)}


def load_cards():
    txt = open(os.path.join(ROOT, 'docs/hanzi-viewer/hanzi-cards.js'), encoding='utf-8').read()
    s = txt[txt.index('[', txt.index('window.HANZI')):]
    arr = json.JSONDecoder().raw_decode(s)[0]
    return {r[0]: r for r in arr}


def is_cjk(c):
    return ord(c) >= 0x2E80


def font_for(c):
    if not is_cjk(c):
        return F_VI
    for f, cm in zip(F_CJK, CMAPS):
        if ord(c) in cm:
            return f
    return None


def renderable(story):
    return all(not is_cjk(c) or font_for(c) for c in story)


def adv(c):
    return SIZE if is_cjk(c) else F_VI.getlength(c)


def split_picture(a):
    """Cột kết thúc phần tranh (khoảng trắng >= 25 cột sau tranh)."""
    cols = (a.min(2) < 215).mean(0)
    x0 = int(np.argmax(cols > 0.02)); x1 = x0; gap = 0
    for x in range(x0, a.shape[1]):
        if cols[x] > 0.005:
            x1, gap = x, 0
        else:
            gap += 1
            if gap >= 25 and x - x0 > 100:
                break
    return x1


def tokens(story):
    """Câu chuyện đã đánh dấu màu: '{cụm từ|r} (亥) dùng đao (刂) {điêu khắc|n} (刻)'.
    Trả về các khối không ngắt dòng [(ký tự, màu)]; '(chữ)' luôn dính vào từ đứng trước."""
    story = re.sub(r'\s*⟨\?⟩', '', story).strip()
    # chuỗi ký tự kèm màu; dấu cách trong cụm tô màu là "không ngắt" (NB), dấu cách thường là chỗ được ngắt
    NB = '\u00a0'
    chars = []
    for m in re.finditer(r'\{([^}|]+)\|(\w)\}|([^{]+)', story):
        if m.group(1):
            col = PALETTE.get(m.group(2), INK)
            chars += [(NB if c.isspace() else c, col) for c in ' '.join(m.group(1).split())]
        else:
            chars += [(c, INK) for c in m.group(3)]
    words, cur = [], []
    for c, col in chars:
        if c.isspace() and c != NB:
            if cur: words.append(cur); cur = []
        else:
            cur.append((' ' if c == NB else c, col))
    if cur: words.append(cur)
    out = []
    for w in words:
        if w[0][0] == '(' and out:   # '(chữ)' dính vào từ đứng trước
            out[-1] += [(' ', INK)] + [(c, INK) for c, _ in w]
        else:
            out.append(w)
    return out


def width(t):
    return sum(adv(c) for c, _ in t)


def draw_story(d, toks, x0, x1, H):
    space = F_VI.getlength(' ')

    def wrap(maxw):
        lines, cur, cw = [], [], 0
        for t in toks:
            tw = width(t)
            if cur and cw + space + tw > maxw:
                lines.append(cur); cur, cw = [], 0
            cw += (space if cur else 0) + tw
            cur.append(t)
        return lines + [cur]
    lines = wrap(x1 - x0)
    if len(lines) == 1 and width([c for t in toks for c in t]) > (x1 - x0) * 0.6:
        lines = wrap(x1 - x0 - 1)   # câu dài vừa -> vẫn chia 2 dòng như thẻ cũ
        total = sum(width(t) for t in toks) + space * (len(toks) - 1)
        lines = wrap(total / 2 + SIZE)
    elif len(lines) > 1:
        # chia đều các dòng (giống thẻ cũ), không để dòng cuối quá ngắn
        n = len(lines)
        total = sum(width(t) for t in toks) + space * (len(toks) - 1)
        w = total / n
        while w < x1 - x0:
            cand = wrap(w)
            if len(cand) <= n:
                lines = cand; break
            w += 10
    lh = int(SIZE * 1.75)
    y = (H - lh * len(lines)) // 2 - 4
    for ln in lines:
        lw = sum(width(t) for t in ln) + space * (len(ln) - 1)
        x = x0 + (x1 - x0 - lw) / 2
        for i, t in enumerate(ln):
            if i:
                x += space
            for c, col in t:
                f = font_for(c)
                if f is F_VI:
                    d.text((x, y), c, font=f, fill=col)
                else:
                    l = f.getbbox(c)[0]
                    il, _, ir, _ = f.getmask(c).getbbox()
                    d.text((x + (SIZE - (ir - il)) / 2 - l - il, y + 6), c, font=f, fill=col)
                x += adv(c)
        y += lh


def build(n, story, out_dir):
    im = Image.open(SRC % n).convert('RGB')
    a = np.asarray(im).astype(int)
    H, W, _ = a.shape
    x1 = split_picture(a)
    out = Image.new('RGB', (W, H), 'white')
    out.paste(im.crop((0, 0, x1 + 12, H)), (0, 0))
    draw_story(ImageDraw.Draw(out), tokens(story), x1 + 50, W - 30, H)
    out.save(os.path.join(out_dir, '%04d.webp' % n), 'WEBP', quality=90)


def load_marked(path):
    """File 'n|câu chuyện có đánh dấu màu' (mỗi dòng 1 thẻ)."""
    d = {}
    for ln in open(path, encoding='utf-8'):
        if '|' in ln:
            n, s = ln.rstrip('\n').split('|', 1)
            if n.strip().isdigit():
                d[int(n)] = s
    return d


if __name__ == '__main__':
    args = sys.argv[1:]
    out_dir = args[args.index('--out') + 1]; os.makedirs(out_dir, exist_ok=True)
    stories = load_marked(args[args.index('--stories') + 1])
    ids = sorted(stories) if '--all' in args else [int(x) for x in args if x.isdigit()]
    k = 0
    for n in ids:
        s = stories.get(n, '')
        if not s.strip():
            continue
        if not renderable(s):
            print('bỏ qua (thiếu font):', n, [c for c in s if is_cjk(c) and not font_for(c)]); continue
        build(n, s, out_dir); k += 1
    print('xong', k)
