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
import re
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCENES = ROOT / "tools/data/rtk_scenes.jsonl"
CAND = ROOT / "build/rtk-img/cand2"     # kiểu nét vẽ đơn giản (giống thẻ kanji_story); cand/ = bản thử hoạt hình cũ
OUT = ROOT / "docs/kanji-viewer/rtk_img"
LIST = ROOT / "docs/kanji-viewer/rtk-img.js"
PICKS = ROOT / "tools/data/rtk_img_picks2.json"
LIVE = ROOT / "docs/kanji-viewer/rtk-live.json"
LIVE_DIR = ROOT / "build/rtk-img/live"
USED = CAND / "used.json"               # tên ảnh -> mô tả đã dùng; mô tả đổi thì vẽ lại
LEGACY_OK = set()                       # ảnh vẽ trước khi có used.json mà vẫn giữ (để trống = vẽ lại hết)
STYLE = (", simple flat vector cartoon clipart, solid flat colors, clean outlines, minimal details, "
         "isolated on plain white background, no text")
NEG = "text, letters, words, watermark, signature, blurry, ugly, deformed"


# ---- thẻ ngang kiểu kanji_story: hình bên trái, câu chuyện bên phải (từ khoá xanh, chữ Hán đỏ trong ngoặc) ----
W, H, PIC = 1440, 360, 360
MIN_FONT = 26
BLUE, RED, INK = (41, 128, 185), (200, 40, 40), (34, 34, 34)
FONT_LAT = "/System/Library/Fonts/Supplemental/Arial Bold Italic.ttf"
FONT_JP = "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc"


def load_rtk():
    import subprocess
    js = "global.window={};require(process.argv[1]);process.stdout.write(JSON.stringify(window.RTK))"
    return {r[1]: r for r in json.loads(subprocess.check_output(["node", "-e", js, str(ROOT / "docs/kanji-viewer/rtk-data.js")])) if r[1]}


def segments(r):
    """Câu chuyện Heisig nguyên văn (html: <b> keyword, <i> thành phần) -> [(chữ, màu)]."""
    import html as H_
    import re
    # chữ nghiêng ngay trước chữ Hán / "(frame N)" là chữ KHÁC được nhắc để so sánh, không phải thành phần
    story = re.sub(r"<i>([^<]*)</i>(\s*[\u3000-\u9fff]|\s*\(frame)", r"\1\2", r[5] or "")
    story = re.sub(r"\s*\((see )?frames? [\d, and]+\)", "", story)
    st = re.sub(r"\s*\[\d+\]\s*$", "", story).strip()
    st = re.sub(r"(-[a-z]+)<([ib])>", r"\1-<\2>", st)                # bản trích mất gạch nối: "shell-to<i>shell" (frame 63)
    st = re.sub(r"(\w)-(</[ib]>)?\s+(?=[a-z])", r"\1\2", st)       # gạch nối ngắt dòng của bản scan: "sun- flower"
    if not H_.unescape(re.sub(r"<[^>]+>", "", st)).strip():
        st = f"<b>{r[2]}</b>"
    out, kj = [], False
    for m in re.finditer(r"<(b|i)>(.*?)</\1>|([^<]+)", st, flags=re.S):
        tag = m.group(1) or ""
        txt = H_.unescape(re.sub(r"<[^>]+>", "", (m.group(2) if tag else m.group(3)) or ""))
        if tag and txt.strip() != txt:            # "<b>one </b>is" -> khoảng trắng ra ngoài
            lead, core, trail = re.match(r"^(\s*)(.*?)(\s*)$", txt, re.S).groups()
            if lead: out.append((lead, INK))
            out.append((core, BLUE))
            if tag == "b" and not kj: out.append(("(" + r[0] + ")", RED)); kj = True
            if trail: out.append((trail, INK))
            continue
        out.append((txt, BLUE if tag else INK))
        if tag == "b" and not kj:
            out.append(("(" + r[0] + ")", RED)); kj = True
    if not kj:
        out = [(r[2], BLUE), ("(" + r[0] + ")", RED), (" — ", INK)] + out
    return out


def words_of(segs):
    """[(chữ, màu)] -> danh sách từ; mỗi từ là các đoạn liền nhau (để '(字)' dính vào keyword, dấu chấm dính vào chữ)."""
    words, cur, gap = [], [], True
    for t, c in segs:
        for piece in re.split(r"(\s+)", t):
            if not piece:
                continue
            if piece.isspace():
                gap = True; continue
            if gap or not cur:
                if cur: words.append(cur)
                cur = []
            cur.append((piece, c)); gap = False
    if cur:
        words.append(cur)
    return words


def card(pic, r):
    """Thẻ ngang: hình 360px bên trái, câu chuyện nguyên văn bên phải; chuyện dài thì thẻ cao thêm (chữ ≥ MIN_FONT)."""
    from PIL import Image, ImageDraw, ImageFont
    d = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    words = words_of(segments(r))
    box_w, x0 = W - PIC - 70, PIC + 40

    def layout(size):
        fl, fj = ImageFont.truetype(FONT_LAT, size), ImageFont.truetype(FONT_JP, size)
        f = lambda t: fj if re.search(r"[\u3000-\u9fff\U00020000-\U0002ffff]", t) else fl
        sp = d.textlength(" ", font=fl)
        wlen = lambda w: sum(d.textlength(t, font=f(t)) for t, _ in w)
        lines, cur, cw = [], [], 0
        for w in words:
            ww = wlen(w)
            if cur and cw + sp + ww > box_w:
                lines.append((cur, cw)); cur, cw = [], 0
            cw += (sp if cur else 0) + ww; cur.append((w, ww))
        if cur:
            lines.append((cur, cw))
        return lines, int(size * 1.4), f, sp

    for size in range(48, MIN_FONT - 1, -2):
        lines, lh, f, sp = layout(size)
        if len(lines) * lh <= H - 40 and max(lw for _, lw in lines) <= box_w:
            break
    h = max(H, len(lines) * lh + 40)
    im = Image.new("RGB", (W, h), "white")
    im.paste(Image.open(pic).convert("RGB").resize((PIC - 24, PIC - 24), Image.LANCZOS), (12, (h - PIC) // 2 + 12))
    d = ImageDraw.Draw(im)
    y = (h - len(lines) * lh) // 2
    for ln, lw in lines:
        x = x0 + (box_w - lw) / 2 if h == H else x0      # chuyện dài: căn trái cho dễ đọc
        for w, ww in ln:
            for t, c in w:
                d.text((x, y), t, font=f(t), fill=c)
                x += d.textlength(t, font=f(t))
            x += sp
        y += lh
    return im


def merge_used():
    used = json.loads(USED.read_text()) if USED.exists() else {}
    for p in sorted(LIVE_DIR.glob("used-*.jsonl")):
        for l in p.read_text().splitlines():
            if l.strip():
                name, sc = json.loads(l); used[name] = sc
        p.unlink()
    USED.write_text(json.dumps(used, ensure_ascii=False, indent=0))
    return used


def publish(picks):
    merge_used()
    OUT.mkdir(parents=True, exist_ok=True)
    R = load_rtk()
    done = []
    for f in sorted({int(p.name[:4]) for p in CAND.glob("*.png")}):
        k = picks.get(str(f), 0)
        src = CAND / f"{f:04d}-{k}.png"
        if not src.exists() or f not in R:
            continue
        card(src, R[f]).save(OUT / f"{f:04d}.webp", "WEBP", quality=70, method=6)
        done.append(f)
    LIST.write_text("// frame Heisig có ảnh minh hoạ câu chuyện (tools/rtk_images.py)\nwindow.RTK_IMG=new Set(%s);\n" % json.dumps(done), encoding="utf-8")
    kb = sum(p.stat().st_size for p in OUT.glob("*.webp")) // 1024
    print(f"xuất bản {len(done)} ảnh → {OUT.relative_to(ROOT)} ({kb} KB)")


def prompt_of(scene):
    # phong cách đặt TRƯỚC: CLIP chỉ đọc ~77 token, mô tả dài bị cắt đuôi chứ không mất phong cách
    return STYLE.lstrip(", ") + ". " + scene


def run_workers(args, n_todo):
    """Chia việc cho N tiến trình (--shard i/N), gộp tiến độ từng tiến trình vào rtk-live.json cho trang rtk-live.html."""
    import subprocess
    import sys
    base = [sys.executable, __file__, "--n", str(args.n), "--steps", str(args.steps)] + \
           (["--only", args.only] if args.only else []) + (["--force"] if args.force else [])
    for p in LIVE_DIR.glob("live-*.json"):
        p.unlink()
    procs = [subprocess.Popen(base + ["--shard", f"{i}/{args.workers}"]) for i in range(args.workers)]
    t0 = time.time()
    while True:
        alive = [p.poll() is None for p in procs]
        ws = []
        for i in range(args.workers):
            try:
                ws.append(json.loads((LIVE_DIR / f"live-{i}.json").read_text()))
            except (OSError, ValueError):
                ws.append({})
        n = sum(w.get("n", 0) for w in ws)
        el = time.time() - t0
        rate = el / n if n else 0
        done = sorted((d for w in ws for d in w.get("done", [])), key=lambda d: d[3])
        LIVE.write_text(json.dumps({
            "total": n_todo, "n": n, "started": t0, "rate": round(rate, 2),
            "eta_min": round(rate * (n_todo - n) / 60, 1), "done": done[-400:],
            "workers": [{"n": w.get("n", 0), "total": w.get("total", 0), "rate": w.get("rate"), "alive": a}
                        for w, a in zip(ws, alive)]}, ensure_ascii=False))
        if not any(alive):
            break
        time.sleep(2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--n", type=int, default=3, help="số bản mỗi frame")
    ap.add_argument("--steps", type=int, default=3)
    ap.add_argument("--pick", help="frame:bản, vd 18:2,21:1")
    ap.add_argument("--workers", type=int, default=1, help="số tiến trình vẽ song song (M2 16GB: 2)")
    ap.add_argument("--publish", action="store_true", help="chỉ dựng lại thẻ từ ảnh đã vẽ")
    ap.add_argument("--shard", help="i/N — dùng nội bộ khi chạy --workers")
    args = ap.parse_args()
    picks = json.loads(PICKS.read_text()) if PICKS.exists() else {}
    if args.publish:
        return publish(picks)
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
    LIVE_DIR.mkdir(parents=True, exist_ok=True)
    used = json.loads(USED.read_text()) if args.shard and USED.exists() else merge_used()  # ảnh nào vẽ từ mô tả nào

    def stale(f, k, sc):
        p = CAND / f"{f:04d}-{k}.png"
        return args.force or not p.exists() or used.get(p.name) not in (None, sc) or \
            (p.name not in used and f not in LEGACY_OK)

    flag = {r["f"]: r.get("review") or ("chỉ có thành phần" if r.get("basis") == "primitives" else "") for r in rows}
    todo = [(r["f"], k, r["scene"]) for r in rows for k in range(args.n) if stale(r["f"], k, r["scene"])]
    if args.workers > 1 and not args.shard:
        print(f"{len(todo)} ảnh cần vẽ · {args.workers} tiến trình song song", flush=True)
        if todo:
            run_workers(args, len(todo))
        return publish(picks)
    me, N = (int(x) for x in args.shard.split("/")) if args.shard else (0, 1)
    todo = todo[me::N]
    live_path = LIVE_DIR / f"live-{me}.json" if args.shard else LIVE
    print(f"[{me}/{N}] {len(todo)} ảnh cần vẽ", flush=True)
    if todo:
        import torch
        from diffusers import AutoPipelineForText2Image
        pipe = AutoPipelineForText2Image.from_pretrained(
            "stabilityai/sd-turbo", torch_dtype=torch.float16, variant="fp16").to("mps")
        pipe.set_progress_bar_config(disable=True)
        R = load_rtk(); OUT.mkdir(parents=True, exist_ok=True)
        live = {"total": len(todo), "done": [], "started": time.time()}
        t0 = time.time()
        for i, (f, k, s) in enumerate(todo, 1):
            im = pipe(prompt=prompt_of(s), negative_prompt=NEG, num_inference_steps=args.steps, guidance_scale=0.0,
                      height=512, width=512, generator=torch.Generator("cpu").manual_seed(1000 * k + f)).images[0]
            name = f"{f:04d}-{k}.png"
            im.save(CAND / name, optimize=True)
            (LIVE_DIR / f"used-{me}.jsonl").open("a").write(json.dumps([name, s]) + "\n")
            if k == picks.get(str(f), 0) and f in R:      # thẻ xuất bản ngay để trang rtk-live.html thấy
                card(CAND / name, R[f]).save(OUT / f"{f:04d}.webp", "WEBP", quality=70, method=6)
                live["done"].append([f, R[f][0], R[f][2], round(time.time(), 1), me, s,
                                     flag.get(f, "")])
            el = time.time() - t0
            live.update(n=i, rate=round(el / i, 2), eta_min=round(el / i * (len(todo) - i) / 60, 1))
            live_path.write_text(json.dumps(live, ensure_ascii=False))
            if i % 15 == 0 or i == len(todo):
                print(f"  [{me}] {i}/{len(todo)} · {el / i:.1f}s/ảnh · còn ~{el / i * (len(todo) - i) / 60:.1f} phút", flush=True)
    if not args.shard:
        publish(picks)


if __name__ == "__main__":
    main()
