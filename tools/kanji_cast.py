#!/usr/bin/env python3
"""Dàn nhân vật cố định cho video ngắn Kanji (đóng lại ở mọi câu chuyện để người xem quen mặt).

Chọn từ các mảnh hay xuất hiện nhất trong 2.075 câu chuyện: 亻/人/儿 người (~170 chuyện), 女 phụ nữ, 王 vua,
士 binh sĩ, 犬/犭 chó, 隹/鳥 chim, 羊 dê, 牛 trâu …  Mỗi nhân vật vẽ 1 lần bằng sd-turbo (nhiều seed để chọn),
tách nền trắng -> sprite PNG trong suốt dùng lại trong mọi video.

    .venv/bin/python tools/kanji_cast.py cand            # vẽ ứng viên -> build/kanji-cast/cand/<id>-<seed>.png
    .venv/bin/python tools/kanji_cast.py pick nhan=3 ... # chọn seed -> build/kanji-cast/<id>.png (đã tách nền)
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build/kanji-cast"
STYLE = (", full body, single character, centered, isolated on plain pure white background, "
         "cute chibi flat cartoon, children's picture book style, thick clean outlines, soft pastel colors, no text")
CAST = {
    # id: (mảnh, tên tiếng Việt, mô tả)
    "nhan": ("亻", "Nhân", "a cheerful little boy with short black hair, red scarf, blue tunic, brown sandals, standing"),
    "nu": ("女", "Nữ", "a kind young woman with long black hair in a bun, pink kimono, standing"),
    "vuong": ("王", "Vua", "a chubby king with a golden crown, red royal robe, black beard, standing"),
    "si": ("士", "Binh sĩ", "a brave little samurai soldier with a helmet and a wooden sword, green armor, standing"),
    "khuyen": ("犬", "Chó", "a cute brown shiba inu dog with a red collar, standing on four legs, side view"),
    "dieu": ("隹", "Chim", "a cute round blue bird with orange beak, side view"),
    "duong": ("羊", "Dê", "a cute white goat with small curved horns, standing on four legs, side view"),
    "nguu": ("牛", "Trâu", "a cute gray water buffalo with big curved horns, standing on four legs, side view"),
    # 19 vai thêm sau khi quét lại lời kể (tên nhân vật đặt theo mảnh: cô Thảo 艹, chị Nguyệt 月, em Bồ 阝 …)
    "nguyet": ("月", "Chị Nguyệt", "a gentle young woman with a silver crescent moon hairpin, long black hair, light blue kimono, standing"),
    "thao": ("艹", "Cô Thảo", "a cheerful young woman with a crown of green leaves, short brown hair, green dress, standing"),
    "bo": ("阝", "Em Bồ", "a cute teenage girl with two pigtails and a red heart hairclip, yellow dress, standing, shy smile"),
    "chu": ("主官監里", "Ông chủ / quan", "a plump old boss man with mustache in a dark blue mandarin robe and black official hat, holding an abacus, standing"),
    "trung": ("虫豸", "Côn trùng", "a cute green caterpillar insect with big eyes, side view"),
    "tre": ("子曽", "Trẻ con", "a cute toddler baby with one tuft of hair, white diaper, standing, big smile"),
    "xac": ("尸", "Xác chết", "a cute friendly cartoon mummy wrapped in white bandages, arms forward, standing"),
    "than": ("臣辰", "Ông thần", "a wise old god with a long white beard, golden halo, white robe, holding a wooden staff, standing"),
    "ong": ("兄父", "Ông / bố", "a kind grandfather with gray hair and round glasses, brown vest, standing"),
    "thu": ("殳弋", "Kẻ thù", "a funny villain bandit with a black mask and an eye patch, holding a wooden club, standing"),
    "sinh": ("先尚者", "Tiên sinh", "a scholar teacher with round glasses and a small goatee, gray robe, holding a book, standing"),
    "ma": ("鬼麻", "Ma", "a cute little white ghost floating, round body, wavy bottom, big eyes"),
    "chong": ("夫", "Ông chồng", "a tall young husband with short black hair, white shirt and black trousers, standing"),
    "lon": ("豕亥", "Lợn", "a cute pink pig standing on four legs, side view"),
    "ngua": ("馬", "Ngựa", "a cute brown horse with a black mane standing on four legs, side view"),
    "cong": ("工", "Công nhân", "a worker with a yellow hard hat and orange overalls, holding a hammer, standing"),
    "ca": ("魚", "Cá", "a cute orange fish, side view"),
    "ho": ("虎", "Hổ", "a cute orange tiger with black stripes standing on four legs, side view"),
    "rong": ("竜龍", "Rồng", "a cute green chinese dragon with small horns, side view"),
}
SEEDS = [11, 22, 33, 44]


def pipe():
    import torch
    from diffusers import AutoPipelineForText2Image
    p = AutoPipelineForText2Image.from_pretrained("stabilityai/sd-turbo", torch_dtype=torch.float16, variant="fp16").to("mps")
    p.set_progress_bar_config(disable=True)
    return p, torch


def cut_white(im: Image.Image) -> Image.Image:
    """Tách nhân vật: nhân vật có viền đen dày -> nền = vùng nối với mép ảnh mà không vượt qua nét viền.
    (sd-turbo hay cho nền giấy màu/lấm tấm chứ không trắng hẳn, nên không lọc theo màu nền.)"""
    a = np.asarray(im.convert("RGB")).astype(np.int16)
    lum = a.mean(2)
    wall = ndimage.binary_dilation(lum < 95, iterations=2)
    lab, _ = ndimage.label(~wall)
    edge = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    fg = ~np.isin(lab, list(edge))
    fg = ndimage.binary_fill_holes(fg)
    fg = ndimage.binary_erosion(fg, iterations=1)
    lab2, n = ndimage.label(fg)
    if n:
        sizes = ndimage.sum(fg, lab2, range(1, n + 1))
        fg = np.isin(lab2, [i + 1 for i, s in enumerate(sizes) if s > 0.08 * sizes.max()])
    alpha = ndimage.gaussian_filter(fg.astype(np.float32), 0.7)
    rgba = np.dstack([a.astype(np.uint8), (np.clip(alpha, 0, 1) * 255).astype(np.uint8)])
    ys, xs = np.nonzero(fg)
    return Image.fromarray(rgba, "RGBA").crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "cand"
    if cmd == "cand":
        p, torch = pipe()
        only = set(sys.argv[2:])
        for cid, (_, _, desc) in CAST.items():
            if only and cid not in only:
                continue
            for sd in SEEDS:
                im = p(prompt=desc + STYLE, num_inference_steps=2, guidance_scale=0.0, height=512, width=512,
                       generator=torch.Generator("cpu").manual_seed(sd)).images[0]
                im.save(OUT / "cand" / f"{cid}-{sd}.png")
            print(cid, flush=True)
    elif cmd == "pick":
        for kv in sys.argv[2:]:
            cid, sd = kv.split("=")
            cut_white(Image.open(OUT / "cand" / f"{cid}-{sd}.png")).save(OUT / f"{cid}.png")
            print("->", OUT / f"{cid}.png")


if __name__ == "__main__":
    main()
