"""Tách hình minh hoạ khỏi ảnh thẻ Kanji và tính thứ tự "vẽ tay" cho từng điểm ảnh.

Ảnh thẻ: [ô chữ | hình minh hoạ | câu chuyện chữ] ở dải trên, bảng màu ở dưới.
- illustration(img)  -> ảnh RGB chỉ phần hình minh hoạ (hoặc None)
- draw_plan(ill)     -> mảng thời điểm hiện (0..1) cho từng điểm ảnh, theo 3 lớp:
    nét đen/xám (0.00–0.60) -> màu tô (0.45–0.85) -> nét ĐỎ (đánh dấu riêng, hiện theo lời đọc)
"""
from __future__ import annotations

import numpy as np
from PIL import Image
from scipy import ndimage


def _sat_lum(a: np.ndarray):
    a = a.astype(np.float32)
    mx, mn = a.max(2), a.min(2)
    return mx - mn, a.mean(2)


def illustration(path) -> Image.Image | None:
    im = Image.open(path).convert("RGB")
    a = np.asarray(im)
    h, w, _ = a.shape
    sat, lum = _sat_lum(a)
    ink = (lum < 215) | (sat > 50)
    # đáy dải trên: hàng đầu tiên (từ 35% chiều cao) mà phần lớn bề ngang là nền màu của bảng
    colored = ((sat > 25) & (lum > 150)).mean(1)
    top_end = next((y for y in range(int(h * 0.35), h) if colored[y] > 0.45), int(h * 0.6))
    # khung đen bao quanh thẻ: bỏ vài px viền trên
    y0 = 4
    band = ink[y0:top_end]
    dark = (lum[y0:top_end] < 110)
    # mép phải ô chữ: cột tối dài nhất trong khoảng 10%–35% bề ngang
    lo, hi = int(w * 0.10), int(w * 0.35)
    col_dark = dark.mean(0)
    box_r = lo + int(np.argmax(col_dark[lo:hi]))
    if col_dark[box_r] < 0.5:
        return None
    x0 = box_r + 4
    # bỏ các đường kẻ ngang/dọc (khung) và mép trên/dưới của dải
    sub = band[:, x0:].copy()
    bh = sub.shape[0]
    sub[: int(bh * 0.06)] = False
    sub[int(bh * 0.94):] = False
    def thin(flags, maxw=4):
        """chỉ giữ các dải 'đầy mực' hẹp (đường kẻ khung), không phải hình phủ kín nền"""
        out = np.zeros_like(flags)
        i = 0
        while i < len(flags):
            if flags[i]:
                j = i
                while j < len(flags) and flags[j]:
                    j += 1
                if j - i <= maxw:
                    out[i:j] = True
                i = j
            else:
                i += 1
        return out
    sub[:, thin(sub.mean(0) > 0.6)] = False
    sub[thin(sub.mean(1) > 0.3, 6), :] = False
    sw = sub.shape[1]
    cols = sub.sum(0) >= 3
    xs = np.nonzero(cols)[0]
    if len(xs) < 20:
        return None
    # khe trắng rộng nhất (nằm trong 12%–80% bề ngang) = ranh giới hình | chữ câu chuyện
    best, xa = (0, None), xs[0]
    for p0, p1 in zip(xs[:-1], xs[1:]):
        g = p1 - p0
        if g > best[0] and sw * 0.12 < p0 < sw * 0.8:
            best = (g, p0)
    if best[0] < 8:
        return None
    xb = best[1]
    if xb - xa < 40:
        return None
    rows = sub[:, xa:xb + 1].mean(1) > 0.004
    ys = np.nonzero(rows)[0]
    if len(ys) < 20:
        return None
    pad = 3
    box = (x0 + xa - pad, y0 + ys[0] - pad, x0 + xb + pad + 1, y0 + ys[-1] + pad + 1)
    box = (max(0, box[0]), max(0, box[1]), min(w, box[2]), min(h, box[3]))
    return im.crop(box)


def _bfs_order(mask: np.ndarray, t0: float, t1: float, out: np.ndarray):
    """Mỗi cụm nét: hiện dần từ điểm trái-trên ra xa (giống ngòi bút chạy theo nét)."""
    lab, n = ndimage.label(mask, structure=np.ones((3, 3)))
    if not n:
        return
    sizes = ndimage.sum(mask, lab, range(1, n + 1))
    cents = ndimage.center_of_mass(mask, lab, range(1, n + 1))
    # cụm to trước, rồi trái -> phải; cụm li ti dồn chung
    order = sorted(range(n), key=lambda i: (sizes[i] < 25, cents[i][1]))
    total = float(sizes.sum())
    acc = 0.0
    for i in order:
        comp = lab == i + 1
        ys, xs = np.nonzero(comp)
        k = int(np.argmin(xs + ys))
        seed = np.zeros_like(comp)
        seed[ys[k], xs[k]] = True
        # khoảng cách trắc địa trong cụm (lan dần)
        dist = np.full(comp.shape, -1, np.int32)
        frontier, d = seed, 0
        dist[frontier] = 0
        while frontier.any():
            d += 1
            nxt = ndimage.binary_dilation(frontier, structure=np.ones((3, 3))) & comp & (dist < 0)
            dist[nxt] = d
            frontier = nxt
            if d > 4000:
                break
        dist[comp & (dist < 0)] = d
        a = t0 + (t1 - t0) * acc / total
        b = t0 + (t1 - t0) * (acc + sizes[i]) / total
        out[comp] = a + (b - a) * dist[comp] / max(1, d)
        acc += sizes[i]


def draw_plan(ill: Image.Image):
    """-> (T, red) : T thời điểm hiện 0..1 cho lớp đen + lớp màu (inf = nền trắng),
    red = mảng thời điểm 0..1 trong lớp đỏ (nan nếu không phải điểm đỏ)."""
    a = np.asarray(ill.convert("RGB")).astype(np.int16)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    sat, lum = _sat_lum(a)
    # đỏ / đỏ sẫm (dấu đánh riêng như 2 dấu X), không lấy màu da (đỏ nhạt)
    redm = (r > 90) & (r - g > 35) & (r - b > 25) & ((r - g) > 0.3 * r)
    redm = ndimage.binary_dilation(redm, iterations=1) & ((r - g > 40) | (lum < 200))
    # đường kẻ khung thẳng dài (viền thẻ lọt vào khi cắt) -> bỏ hẳn, không vẽ
    dark = lum < 170
    frame_rows = ndimage.binary_dilation(dark.mean(1) > 0.5, iterations=1)
    frame_cols = ndimage.binary_dilation(dark.mean(0) > 0.5, iterations=1)
    keep = ~(frame_rows[:, None] | frame_cols[None, :])
    redm &= keep
    if not (15 < redm.sum() < 0.12 * redm.size):
        redm = np.zeros_like(redm)
    line = (lum < 140) & (sat < 90) & ~redm & keep
    fill = ((lum < 245) | (sat > 25)) & ~line & ~redm & keep
    T = np.full(lum.shape, np.inf, np.float32)
    _bfs_order(line, 0.0, 0.60, T)
    _bfs_order(fill, 0.40, 0.85, T)
    R = np.full(lum.shape, np.nan, np.float32)
    if 15 < redm.sum() < 0.12 * redm.size:     # mảng đỏ quá lớn = áo/nền đỏ, không phải dấu đánh riêng
        tmp = np.full(lum.shape, np.inf, np.float32)
        _bfs_order(redm, 0.0, 1.0, tmp)
        R[redm] = tmp[redm]
    return T, R


def frame(ill_arr: np.ndarray, T: np.ndarray, R: np.ndarray, p: float, pr: float):
    """Ảnh hình minh hoạ tại tiến độ p (lớp đen+màu) và pr (lớp đỏ); trả (ảnh, vị trí ngòi bút)."""
    show = T <= p
    if pr > 0:
        show |= (R <= pr)
    out = np.full_like(ill_arr, 255)
    out[show] = ill_arr[show]
    pen = None
    act = (R <= pr) & (R > pr - 0.08) if 0 < pr < 1 else (T <= p) & (T > p - 0.03) if p < 0.86 else None
    if act is not None and act.any():
        ys, xs = np.nonzero(act)
        pen = (float(xs.mean()), float(ys.mean()))
    return Image.fromarray(out), pen
