def top_cut(im):
    """Đường kẻ ngang dưới ô câu chuyện (bản scan: mảnh, hơi nghiêng -> xét cửa sổ 3 hàng)."""
    g = im.convert("L"); w, h = g.size; px = g.load()
    xs = range(int(w * .3), int(w * .98), 2)
    def score(y):
        return sum(1 for x in xs if min(px[x, y - 1], px[x, y], px[x, y + 1]) < 150) / len(xs)
    ys = range(int(h * .45), int(h * .75))
    y = max(ys, key=score)
    if score(y) > .6:
        return y - 1
    # dự phòng: chỗ nền đổi từ trắng (ô câu chuyện) sang màu (bảng bên dưới)
    def mean(yy):
        return sum(px[x, yy] for x in xs) / len(xs)
    m = {yy: mean(yy) for yy in range(int(h * .4), int(h * .8))}
    def drop(yy):
        return (m[yy - 4] + m[yy - 3] + m[yy - 2]) / 3 - (m[yy + 2] + m[yy + 3] + m[yy + 4]) / 3
    y2 = max(range(int(h * .45), int(h * .75)), key=drop)
    return (y2 - 2) if drop(y2) > 18 and m[y2 - 4] > 200 else None


def story_box(im):
    """Ô câu chuyện: phải đường kẻ dọc (chạy suốt chiều cao thẻ), trên đường kẻ ngang. None nếu không chắc."""
    y = top_cut(im)
    if not y:
        return None
    g = im.convert("L"); w, h = g.size; px = g.load()
    def col(x, y0, y1):
        ys = range(y0, y1)
        return sum(1 for yy in ys if min(px[x - 1, yy], px[x, yy], px[x + 1, yy]) < 150) / len(ys)
    xs = range(int(w * .12), int(w * .34))
    sc = {x: (col(x, int(h * .06), y - 3), col(x, y + 4, int(h * .94))) for x in xs}
    good = [x for x, (a, b) in sc.items() if a > .7 and b > .7]
    if not good:
        return None
    x = min(good)
    while x + 1 in sc and sc[x + 1][0] > .7 and sc[x + 1][1] > .7:
        x += 1                                         # qua hết bề dày đường kẻ
    # đường kẻ trên của ô (ảnh có dính dải thẻ trước): hàng tối dài nhất, thấp nhất trong 0–35% chiều cao
    xs2 = range(x + 4, w - 4)
    def row(yy):                                       # đoạn tối liền mạch dài nhất (đường kẻ thật, không phải dòng chữ)
        best = cur = 0
        for xx in xs2:
            if min(px[xx, yy - 1], px[xx, yy], px[xx, yy + 1]) < 150:
                cur += 1; best = max(best, cur)
            else:
                cur = 0
        return best / len(xs2)
    tops = [yy for yy in range(1, int(h * .35)) if row(yy) > .6]
    t = (max(tops) + 2) if tops else 0
    return (x + 2, t, w, y)
