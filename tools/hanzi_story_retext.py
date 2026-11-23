#!/usr/bin/env python3
"""Vẽ lại phần CHỮ câu chuyện trên ảnh thẻ Hán tự docs/hanzi-viewer/story/NNNN.webp (chữ gốc bị mờ):
giữ nguyên phần tranh bên trái, xoá phần chữ thành nền trắng, rồi vẽ lại câu chuyện bằng một font thống nhất.
Câu chuyện lấy từ file 'n|câu chuyện' đã đánh dấu màu: {cụm từ|r} (chữ) — r g b n o p (xem PALETTE).

    python3 tools/hanzi_story_retext.py --stories tools/data/hanzi_story_text.txt --src DIR_ANH_GOC --out DIR 1734 2883
    python3 tools/hanzi_story_retext.py --stories tools/data/hanzi_story_text.txt --src DIR_ANH_GOC --out DIR --all
  DIR_ANH_GOC: ảnh thẻ gốc (chưa vẽ lại), ví dụ lấy từ git:  git archive c5122e73 docs/hanzi-viewer/story | tar -x -C /tmp/goc
"""
import functools, json, os, re, sys
import numpy as np
from fontTools.ttLib import TTCollection, TTFont
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'docs/hanzi-viewer/story/%04d.webp')
SIZE = 44          # cỡ chữ chuẩn; câu dài tự giảm cỡ cho vừa ảnh
FONT_DIR = os.path.join(ROOT, 'tools/fonts')   # HanaMinA/B.otf (Hanazono, miễn phí) cho chữ hiếm Ext-B — không đưa lên git
# chữ Hán: thử lần lượt các font cho tới font có ký tự
_CJK_SRC = [('/System/Library/Fonts/Hiragino Sans GB.ttc', 0), ('/System/Library/Fonts/STHeiti Medium.ttc', 1),
            ('/System/Library/Fonts/ヒラギノ角ゴシック W4.ttc', 0), ('/System/Library/Fonts/Supplemental/Songti.ttc', 7),
            ('/System/Library/Fonts/Supplemental/Arial Unicode.ttf', 0),
            (os.path.join(FONT_DIR, 'HanaMinA.otf'), 0), (os.path.join(FONT_DIR, 'HanaMinB.otf'), 0)]
CJK_FONTS = []   # [(đường dẫn, index, cmap)]
for _p, _i in _CJK_SRC:
    if os.path.exists(_p):
        _f = TTCollection(_p).fonts[_i] if _p.endswith('.ttc') else TTFont(_p)
        CJK_FONTS.append((_p, _i, set(_f.getBestCmap())))


@functools.lru_cache(None)
def vi_font(size):
    return ImageFont.truetype('/System/Library/Fonts/Avenir Next.ttc', size, index=1)   # Bold Italic


@functools.lru_cache(None)
def cjk_font(k, size):
    p, i, _ = CJK_FONTS[k]
    return ImageFont.truetype(p, size, index=i)


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


def cjk_index(c):
    for k, (_, _, cm) in enumerate(CJK_FONTS):
        if ord(c) in cm:
            return k
    return None


def font_for(c, size=SIZE):
    if not is_cjk(c):
        return vi_font(size)
    k = cjk_index(c)
    return None if k is None else cjk_font(k, size)


def renderable(story):
    return all(not is_cjk(c) or cjk_index(c) is not None for c in story)


def adv(c, size=SIZE):
    return size if is_cjk(c) else vi_font(size).getlength(c)


# thẻ chỉ có chữ, không có tranh (đã kiểm tra bằng mắt)
TEXT_ONLY = {105, 129, 373, 453, 542, 558, 613, 684, 692, 700, 707, 715, 721, 729, 737, 745, 752, 760, 768, 775}


def split_picture(a):
    """Cột kết thúc phần tranh bên trái; None nếu thẻ không có tranh (chỉ có chữ).
    Mực = điểm tối hoặc có màu (kể cả viền khung màu nhạt)."""
    H, W, _ = a.shape
    mx, mn = a.max(2), a.min(2)
    ink = (mn < 225) | (((mx - mn) > 35) & (mn < 245))
    cols = ink.mean(0)
    # các khối cột có mực, cách nhau bởi khoảng trắng >= 25 cột
    segs, x, start, gap = [], 0, None, 0
    for x in range(W):
        if cols[x] > 0.005:
            if start is None:
                start = x
            end, gap = x, 0
        elif start is not None:
            gap += 1
            if gap >= 25:
                segs.append((start, end)); start, gap = None, 0
    if start is not None:
        segs.append((start, end))
    segs = [s for s in segs if not (s[0] < 10 and s[1] - s[0] < 60)]   # mẩu viền thẻ bên cạnh dính ở mép trái
    if not segs:
        return None
    x0, x1 = segs[0]
    # viền khung mảnh (màu nhạt) cách tranh > 25 cột: gộp các khối hẹp, cao gần hết ảnh ngay sau tranh
    for sx, ex in segs[1:]:
        if sx - x1 > 160 or ex - sx > 20:
            break
        if (ink[:, sx:ex + 1].any(1)).mean() > 0.5:
            x1 = ex
    if x1 > 0.75 * W:
        return None
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


def width(t, size=SIZE):
    return sum(adv(c, size) for c, _ in t)


def layout(toks, maxw, size):
    """Chia dòng đều nhau (giống thẻ cũ): số dòng ít nhất có thể, rồi cân độ dài các dòng."""
    space = vi_font(size).getlength(' ')

    def wrap(w):
        lines, cur, cw = [], [], 0
        for t in toks:
            tw = width(t, size)
            if cur and cw + space + tw > w:
                lines.append(cur); cur, cw = [], 0
            cw += (space if cur else 0) + tw
            cur.append(t)
        return lines + [cur]
    total = sum(width(t, size) for t in toks) + space * (len(toks) - 1)
    lines = wrap(maxw)
    n = len(lines)
    if n == 1 and total > maxw * 0.6 and len(toks) > 1:
        n = 2                                    # câu vừa dài -> 2 dòng như thẻ cũ
    w = total / n
    while w < maxw:
        cand = wrap(w)
        if len(cand) <= n:
            return cand
        w += 8
    return lines


def draw_story(d, toks, x0, x1, H):
    for size in (SIZE, 40, 36, 33, 30, 27):
        lines = layout(toks, x1 - x0, size)
        lh = int(size * 1.7)
        if lh * len(lines) <= H - 24:
            break
    space = vi_font(size).getlength(' ')
    y = (H - lh * len(lines)) // 2 - 4
    for ln in lines:
        lw = sum(width(t, size) for t in ln) + space * (len(ln) - 1)
        x = x0 + (x1 - x0 - lw) / 2
        for i, t in enumerate(ln):
            if i:
                x += space
            for c, col in t:
                f = font_for(c, size)
                if not is_cjk(c):
                    d.text((x, y), c, font=f, fill=col)
                else:
                    l = f.getbbox(c)[0]
                    il, _, ir, _ = f.getmask(c).getbbox()
                    d.text((x + (size - (ir - il)) / 2 - l - il, y + size * 0.14), c, font=f, fill=col)
                x += adv(c, size)
        y += lh


def build(n, story, out_dir, src=SRC):
    im = Image.open(src % n).convert('RGB')
    a = np.asarray(im).astype(int)
    H, W, _ = a.shape
    x1 = None if n in TEXT_ONLY else split_picture(a)
    out = Image.new('RGB', (W, H), 'white')
    if x1 is None:                                   # thẻ chỉ có chữ
        draw_story(ImageDraw.Draw(out), tokens(story), 60, W - 60, H)
    else:
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
    src = os.path.join(args[args.index('--src') + 1], '%04d.webp') if '--src' in args else SRC   # thư mục ảnh GỐC
    ids = sorted(stories) if '--all' in args else [int(x) for x in args if x.isdigit()]
    k = 0
    for n in ids:
        s = stories.get(n, '')
        if not s.strip():
            continue
        if not renderable(s):
            print('bỏ qua (thiếu font):', n, [c for c in s if is_cjk(c) and cjk_index(c) is None]); continue
        build(n, s, out_dir, src); k += 1
    print('xong', k)
