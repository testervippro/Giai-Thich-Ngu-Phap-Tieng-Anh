#!/usr/bin/env python3
"""Bù ảnh câu chuyện cho các Kanji ngoài 2136 (thẻ 2137+) chưa có ảnh trong docs/kanji-viewer/kanji_story.

Lấy phần TRANH từ thẻ Hán tự tương ứng (docs/hanzi-viewer/story/NNNN.webp), đặt bên trái nền trắng,
rồi vẽ câu chuyện (dùng dạng chữ Nhật) bên phải — cùng bố cục với ảnh kanji_story.

    python3 tools/kanji_story_extra.py            # tạo tất cả
    python3 tools/kanji_story_extra.py 2137 2149  # chỉ vài thẻ
"""
import os, re, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'docs/hanzi-viewer/story/%04d.webp')
DST = os.path.join(ROOT, 'docs/kanji-viewer/kanji_story/%04d.webp')

# số thẻ Kanji -> (số thẻ Hán tự, câu chuyện). [từ](chữ): từ màu xanh, chữ đỏ trong ngoặc.
STORIES = {
    2137: (1734, '[Dê](羊) em [công nhân](工) là [sai](差)'),
    2139: (214,  '[Cung](弓) [này](尔) bán [khắp](弥) mọi nơi'),
    2140: (2886, '[Nguyệt](月) leo lên [cây](木) [người](人) vẫn bị ngập [nước](水) đến [đầu gối](膝)'),
    2141: (1654, 'Giống số 4 ngược bị [gãy](寸)'),
    2142: (3108, 'Gà mái giải phóng ra [2](丶) [quả trứng](卵)'),
    2143: (1732, '[Bữa ăn](膳) [Nguyệt](月) nấu mang đi [từ thiện](善)'),
    2145: (264,  '[Tay](扌) [đứng](立) [lôi kéo](拉)'),
    2146: (2791, 'Giống hình [móng chân](爪)'),
    2147: (1132, '[Bột](孛) tăng [lực](力) làm cơ thể [hừng hực](勃)'),
    2149: (2883, 'Bị [bệnh](疒) nên [ông cụ](叟) rất [gầy](痩)'),
    2150: (1490, '[Người](亻) vào dịp tết [Nguyên Đán](旦) [nhưng](但) không làm gì'),
    2153: (206,  '[Nước](氵) uống vài [hạt](曷) vẫn [khát](渇) lắm'),
    2155: (2920, 'Cô [Thảo](艹) có chuyện [tệ](敝) nhất vẫn đang [che giấu](蔽)'),
    2157: (2137, '2 ông [vua](王) bị ép làm [văn](文) đến mức da nổi [lốm đốm](斑) tàn nhang'),
    2160: (627,  '[Điền](塡) thông tin [đất](土) đai đúng [sự thật](眞)'),
    2161: (2788, '[Trúc](⺮) [tàn](戔) dùng làm [giấy viết thư](箋)'),
    2162: (3113, 'Đột ngột [lồi](凸) lên'),
    2163: (3112, 'Ao có chỗ [lõm](凹) hình chữ U'),
}

W, H = 1255, 266
BLACK, TEAL, RED = (35, 35, 35), (30, 140, 175), (180, 35, 35)
F_VI = ImageFont.truetype('/System/Library/Fonts/HelveticaNeue.ttc', 36)
F_CJK = [ImageFont.truetype('/System/Library/Fonts/Hiragino Sans GB.ttc', 36),
         ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Unicode.ttf', 36)]


def font_for(ch):
    if ord(ch) < 0x2E80:
        return F_VI
    for f in F_CJK:
        if f.getmask(ch).getbbox():
            return f
    return F_CJK[0]


def picture(path):
    """Cắt khung tranh bên trái thẻ Hán tự (tới khoảng trắng trước phần chữ)."""
    a = np.asarray(Image.open(path).convert('RGB')).astype(int)
    cols = (a.min(2) < 215).mean(0)
    x0 = int(np.argmax(cols > 0.02)); x1 = x0; gap = 0
    for x in range(x0, a.shape[1]):
        if cols[x] > 0.005:
            x1, gap = x, 0
        else:
            gap += 1
            if gap >= 25 and x - x0 > 100:
                break
    ys = np.where((a[:, x0:x1 + 1].min(2) < 215).mean(1) > 0.02)[0]
    return Image.fromarray(a[ys[0]:ys[-1] + 1, x0:x1 + 1].astype('uint8'))


def tokens(story):
    """Các khối không được ngắt dòng; '[từ](chữ)' giữ liền thành 1 khối. Mỗi khối = [(ký tự, màu)]."""
    out = []
    for m in re.finditer(r'\[([^\]]+)\]\(([^)]+)\)|([^\[]+)', story):
        if m.group(3):
            out += [[(c, BLACK) for c in w] for w in m.group(3).split()]
        else:
            out.append([(c, TEAL) for c in m.group(1)] + [(c, BLACK) for c in ' ('] +
                       [(c, RED) for c in m.group(2)] + [(')', BLACK)])
    return out


def adv(c):
    """Bề rộng 1 ký tự; chữ Hán luôn chiếm đủ 1 ô vuông (tránh bộ thủ hẹp như 亻 bị dính chữ)."""
    return 36 if ord(c) >= 0x2E80 else F_VI.getlength(c)


def width(chars):
    return sum(adv(c) for c, _ in chars)


def draw_story(d, story, x0, x1):
    space = F_VI.getlength(' ')
    lines, cur, cw = [], [], 0
    for t in tokens(story):
        tw = width(t)
        if cur and cw + space + tw > x1 - x0:
            lines.append(cur); cur, cw = [], 0
        cw += (space if cur else 0) + tw
        cur.append(t)
    lines.append(cur)
    lh = 62
    y = (H - lh * len(lines)) // 2 + 6
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
                else:   # căn giữa chữ Hán trong ô 36px
                    l = f.getbbox(c)[0]
                    il, _, ir, _ = f.getmask(c).getbbox()      # phần có mực thật
                    d.text((x + (36 - (ir - il)) / 2 - l - il, y + 3), c, font=f, fill=col)
                x += adv(c)
        y += lh


def build(kn):
    hn, story = STORIES[kn]
    pic = picture(SRC % hn)
    ph = H - 30
    pw = int(pic.width * ph / pic.height)
    if pw > 420:
        pw = 420; ph = int(pic.height * pw / pic.width)
    pic = pic.resize((pw, ph), Image.LANCZOS)
    out = Image.new('RGB', (W, H), 'white')
    out.paste(pic, (30, (H - ph) // 2))
    draw_story(ImageDraw.Draw(out), story, 30 + pw + 50, W - 40)
    out.save(DST % kn, 'WEBP', quality=90)
    print('%04d.webp <- hanzi %04d' % (kn, hn))


if __name__ == '__main__':
    for k in [int(x) for x in sys.argv[1:]] or sorted(STORIES):
        build(k)
