#!/usr/bin/env python3
"""Vẽ ảnh minh hoạ câu chuyện Kanji bằng Stable Diffusion chạy trên máy (sd-turbo, miễn phí).

Đầu vào: tools/data/kanji_ai_prompts.jsonl, mỗi dòng {"n": 28, "scenes": ["a world map ...", "a hand drawing two red X ..."]}
  (mô tả tiếng Anh cho từng cảnh của câu chuyện, theo đúng thứ tự lời kể)
Đầu ra:  build/kanji-ai/0028-0.png, 0028-1.png …  -> tools/kanji_video.py tự dùng cho cảnh câu chuyện.

    .venv/bin/python tools/kanji_ai_images.py            # bỏ qua ảnh đã có
    .venv/bin/python tools/kanji_ai_images.py --only 28,600 --force
Cần: pip install torch diffusers transformers accelerate (mô hình ~2,5 GB tải lần đầu vào ~/.cache/huggingface).
"""
import argparse
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROMPTS = ROOT / "tools/data/kanji_ai_prompts.jsonl"
OUT = ROOT / "build/kanji-ai"
STYLE = (", cute flat cartoon illustration, children's picture book style, clean lines, "
         "soft pastel colors, simple background, no text")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="số thẻ, cách nhau dấu phẩy")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--steps", type=int, default=2)
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()

    rows = [json.loads(l) for l in PROMPTS.read_text(encoding="utf-8").splitlines() if l.strip()]
    if args.only:
        want = {int(x) for x in args.only.split(",")}
        rows = [r for r in rows if r["n"] in want]
    OUT.mkdir(parents=True, exist_ok=True)
    todo = [(r["n"], i, p) for r in rows for i, p in enumerate(r["scenes"])
            if args.force or not (OUT / f"{r['n']:04d}-{i}.png").exists()]
    print(f"{len(todo)} ảnh cần vẽ", flush=True)
    if not todo:
        return

    import torch
    from diffusers import AutoPipelineForText2Image
    pipe = AutoPipelineForText2Image.from_pretrained(
        "stabilityai/sd-turbo", torch_dtype=torch.float16, variant="fp16").to("mps")
    pipe.set_progress_bar_config(disable=True)
    t0 = time.time()
    for k, (n, i, p) in enumerate(todo, 1):
        im = pipe(prompt=p + STYLE, num_inference_steps=args.steps, guidance_scale=0.0, height=512, width=512,
                  generator=torch.Generator("cpu").manual_seed(args.seed + n)).images[0]
        # PNG 512px ~400 KB; lưu PNG tối ưu cho nhẹ (ổ đĩa ít chỗ)
        im.save(OUT / f"{n:04d}-{i}.png", optimize=True)
        if k % 20 == 0 or k == len(todo):
            el = time.time() - t0
            print(f"  {k}/{len(todo)} ảnh · còn ~{el / k * (len(todo) - k) / 60:.0f} phút", flush=True)


if __name__ == "__main__":
    main()
