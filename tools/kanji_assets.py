#!/usr/bin/env python3
"""Thư viện tài sản cho video ngắn Kanji, dựng từ tools/data/kanji_assets.tsv (mảnh -> loại -> asset).

Loại (cột 2):
  nv  nhân vật      -> sprite trong build/kanji-cast (tools/kanji_cast.py)
  bc  bối cảnh       -> phông cảnh dùng chung   build/kanji-assets/bc/<slug>.png
  dv  đồ vật         -> sprite trong suốt        build/kanji-assets/dv/<slug>.png
  ct  bộ phận cơ thể -> sprite (bàn tay, cái mồm …) gắn cạnh nhân vật
  tg  thời gian/hướng-> sprite nếu là mô tả (mặt trời, đồng hồ …), còn night/rain/behind… là hiệu ứng code
  hd  động tác, tt tính chất, so số -> hiệu ứng code (không cần ảnh)

    .venv/bin/python tools/kanji_assets.py cand      # vẽ 2 phương án mỗi asset -> build/kanji-assets/cand/
    .venv/bin/python tools/kanji_assets.py pick      # tách nền phương án 0 (hoặc slug=1 để đổi) -> dv/, bc/
    .venv/bin/python tools/kanji_assets.py sheet     # bảng xem nhanh build/kanji-assets/sheet-*.jpg
"""
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kanji_cast import cut_white  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
TSV = ROOT / "tools/data/kanji_assets.tsv"
OUT = ROOT / "build/kanji-assets"
OBJ_STYLE = (", single object, centered, isolated on plain pure white background, cute flat cartoon icon, "
             "children's picture book style, thick clean black outlines, soft pastel colors, no text")
BG_STYLE = (", wide establishing shot, no people, no animals, empty scene, cute flat cartoon background, "
            "children's picture book style, soft pastel colors, clean lines, no text")
BODY = {"mouth": "a cute cartoon open mouth with lips and teeth", "hand": "a cute cartoon open hand palm",
        "eye": "a cute cartoon big eye with eyelashes", "legs": "a pair of cute cartoon legs walking with sandals",
        "head": "a cute cartoon round head with black hair", "ear": "a cute cartoon ear",
        "hair": "a cartoon wig of long black hair", "tongue": "a cartoon face sticking out a long pink tongue",
        "skin": "a cartoon bandage plaster on pink skin", "claw": "a cartoon cat paw with sharp claws",
        "self": "a cute cartoon boy pointing at himself"}
SEEDS = [5, 17]


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:48]


def load():
    rows = []
    for l in TSV.read_text(encoding="utf-8").splitlines():
        if not l.strip() or l.startswith("#"):
            continue
        p, t, vi, a = (l.split("\t") + ["", "", ""])[:4]
        rows.append((p, t, vi, a.strip()))
    return rows


def assets():
    """-> {slug: (kind 'dv'|'bc', prompt, [mảnh], tên Việt)} — mỗi asset vẽ 1 lần dù nhiều mảnh dùng chung."""
    out = {}
    for p, t, vi, a in load():
        if t == "bc":
            kind, prompt = "bc", a
        elif t == "ct" and a in BODY:
            kind, prompt = "dv", BODY[a]
        elif t in ("dv", "ct", "tg") and " " in a:
            kind, prompt = "dv", a
        else:
            continue
        sl = slug(prompt)
        if sl not in out:
            out[sl] = (kind, prompt, [], vi)
        out[sl][2].append(p)
    return out


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "cand"
    A = assets()
    if cmd == "cand":
        import torch
        from diffusers import AutoPipelineForText2Image
        pipe = AutoPipelineForText2Image.from_pretrained("stabilityai/sd-turbo", torch_dtype=torch.float16,
                                                         variant="fp16").to("mps")
        pipe.set_progress_bar_config(disable=True)
        (OUT / "cand").mkdir(parents=True, exist_ok=True)
        for i, (sl, (kind, prompt, ps, vi)) in enumerate(A.items(), 1):
            for j, sd in enumerate(SEEDS):
                f = OUT / "cand" / f"{sl}-{j}.png"
                if f.exists():
                    continue
                pipe(prompt=prompt + (BG_STYLE if kind == "bc" else OBJ_STYLE), num_inference_steps=2,
                     guidance_scale=0.0, height=512, width=512,
                     generator=torch.Generator("cpu").manual_seed(sd)).images[0].save(f)
            if i % 10 == 0:
                print(f"{i}/{len(A)}", flush=True)
    elif cmd == "pick":
        choice = dict(kv.split("=") for kv in sys.argv[2:])
        for sl, (kind, prompt, ps, vi) in A.items():
            src = OUT / "cand" / f"{sl}-{choice.get(sl, '0')}.png"
            (OUT / kind).mkdir(parents=True, exist_ok=True)
            if kind == "bc":
                Image.open(src).convert("RGB").save(OUT / "bc" / f"{sl}.png")
            else:
                cut_white(Image.open(src)).save(OUT / "dv" / f"{sl}.png")
    elif cmd == "sheet":
        fk = ImageFont.truetype("/System/Library/Fonts/ヒラギノ明朝 ProN.ttc", 26, index=1)
        ft = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 15)
        for kind in ("dv", "bc"):
            L = [(sl, v) for sl, v in A.items() if v[0] == kind]
            cols, cw, chh = 10, 170, 230
            sheet = Image.new("RGB", (cols * cw, ((len(L) + cols - 1) // cols) * chh), (250, 247, 242))
            d = ImageDraw.Draw(sheet)
            for i, (sl, (_, prompt, ps, vi)) in enumerate(L):
                f = OUT / kind / f"{sl}.png"
                if not f.exists():
                    continue
                im = Image.open(f)
                im.thumbnail((150, 150))
                x, y = (i % cols) * cw, (i // cols) * chh
                sheet.paste(im, (x + (cw - im.width) // 2, y + 8 + 150 - im.height), im if im.mode == "RGBA" else None)
                d.text((x + cw / 2, y + 190), "".join(ps)[:5], font=fk, fill=(34, 30, 28), anchor="ms")
                d.text((x + cw / 2, y + 215), vi[:20], font=ft, fill=(14, 116, 92), anchor="ms")
            sheet.save(OUT / f"sheet-{kind}.jpg", quality=86)


if __name__ == "__main__":
    main()
