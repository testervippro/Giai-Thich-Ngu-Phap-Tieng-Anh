"""Thẻ bị hằn mặt sau: ở vùng chữ/nền trắng (không phải tranh) xoá mọi điểm xám chưa đủ đậm."""
import numpy as np
from PIL import Image, ImageFilter

def picture_mask(a, blk=24):
    """Vùng tranh = các ô có nhiều điểm không trắng (mảng màu), nới rộng ra."""
    h, w, _ = a.shape
    nonwhite = a.min(axis=2) < 225
    sat = (a.max(axis=2) - a.min(axis=2)) / 255.
    m = np.zeros((h, w), bool)
    for y in range(0, h, blk):
        for x in range(0, w, blk):
            nb = nonwhite[y:y + blk, x:x + blk]
            if nb.mean() > .35: m[y:y + blk, x:x + blk] = True
    im = Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(blk // 2 * 2 + 1))
    return np.asarray(im) > 0

def clean(a):
    a = a.astype(np.float32)
    ink = 1 - a.min(axis=2) / 255.
    sat = (a.max(axis=2) - a.min(axis=2)) / 255.
    pic = picture_mask(a)
    ghost = (~pic) & (sat < .16) & (ink < .72)
    out = a.copy(); out[ghost] = 255
    return out.astype(np.uint8)
