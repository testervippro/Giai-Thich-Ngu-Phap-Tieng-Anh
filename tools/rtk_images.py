#!/usr/bin/env python3
"""Ảnh minh hoạ câu chuyện Heisig RTK (vẽ trên máy, sd-turbo, miễn phí).

Đầu vào:  tools/data/rtk_scenes.jsonl — mỗi dòng {"f": frame, "scene": "mô tả cảnh tiếng Anh"}
Đầu ra:   build/rtk-img/cand/FFFF-k.png (k bản để chọn) và docs/kanji-viewer/rtk_img/FFFF.webp (bản chọn, 384px)
          + docs/kanji-viewer/rtk-img.js (danh sách frame có ảnh, để trang Xem thẻ biết mà hiện).

    .venv/bin/python tools/rtk_images.py                # vẽ các frame chưa có, mỗi frame 3 bản, lấy bản 0
    .venv/bin/python tools/rtk_images.py --pick 18:2    # đổi frame 18 sang bản 2
    .venv/bin/python tools/rtk_images.py --only 18 --force
"""
import argparse
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCENES = ROOT / "tools/data/rtk_scenes.jsonl"
CAND = ROOT / "build/rtk-img/cand"
OUT = ROOT / "docs/kanji-viewer/rtk_img"
LIST = ROOT / "docs/kanji-viewer/rtk-img.js"
PICKS = ROOT / "tools/data/rtk_img_picks.json"
STYLE = (", cute flat cartoon illustration, children's picture book style, bold clean outlines, "
         "bright colors, simple plain background, single scene, no text, no letters")
NEG = "text, letters, words, watermark, signature, blurry, ugly, deformed"


def publish(picks):
    from PIL import Image
    OUT.mkdir(parents=True, exist_ok=True)
    done = []
    for f in sorted({int(p.name[:4]) for p in CAND.glob("*.png")}):
        k = picks.get(str(f), 0)
        src = CAND / f"{f:04d}-{k}.png"
        if not src.exists():
            continue
        dst = OUT / f"{f:04d}.webp"
        if not dst.exists() or dst.stat().st_mtime < src.stat().st_mtime or True:
            Image.open(src).convert("RGB").resize((384, 384), Image.LANCZOS).save(dst, "WEBP", quality=72, method=6)
        done.append(f)
    LIST.write_text("// frame Heisig có ảnh minh hoạ câu chuyện (tools/rtk_images.py)\nwindow.RTK_IMG=new Set(%s);\n" % json.dumps(done), encoding="utf-8")
    kb = sum(p.stat().st_size for p in OUT.glob("*.webp")) // 1024
    print(f"xuất bản {len(done)} ảnh → {OUT.relative_to(ROOT)} ({kb} KB)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--n", type=int, default=3, help="số bản mỗi frame")
    ap.add_argument("--steps", type=int, default=3)
    ap.add_argument("--pick", help="frame:bản, vd 18:2,21:1")
    args = ap.parse_args()
    picks = json.loads(PICKS.read_text()) if PICKS.exists() else {}
    if args.pick:
        for x in args.pick.split(","):
            f, k = x.split(":"); picks[str(int(f))] = int(k)
        PICKS.write_text(json.dumps(picks, indent=0))
        return publish(picks)

    rows = [json.loads(l) for l in SCENES.read_text(encoding="utf-8").splitlines() if l.strip()]
    if args.only:
        want = {int(x) for x in args.only.split(",")}
        rows = [r for r in rows if r["f"] in want]
    CAND.mkdir(parents=True, exist_ok=True)
    todo = [(r["f"], k, r["scene"]) for r in rows for k in range(args.n)
            if args.force or not (CAND / f"{r['f']:04d}-{k}.png").exists()]
    print(f"{len(todo)} ảnh cần vẽ", flush=True)
    if todo:
        import torch
        from diffusers import AutoPipelineForText2Image
        pipe = AutoPipelineForText2Image.from_pretrained(
            "stabilityai/sd-turbo", torch_dtype=torch.float16, variant="fp16").to("mps")
        pipe.set_progress_bar_config(disable=True)
        t0 = time.time()
        for i, (f, k, s) in enumerate(todo, 1):
            im = pipe(prompt=s + STYLE, negative_prompt=NEG, num_inference_steps=args.steps, guidance_scale=0.0,
                      height=512, width=512, generator=torch.Generator("cpu").manual_seed(1000 * k + f)).images[0]
            im.save(CAND / f"{f:04d}-{k}.png", optimize=True)
            if i % 15 == 0 or i == len(todo):
                el = time.time() - t0
                print(f"  {i}/{len(todo)} · {el / i:.1f}s/ảnh · còn ~{el / i * (len(todo) - i) / 60:.1f} phút", flush=True)
    publish(picks)


if __name__ == "__main__":
    main()
