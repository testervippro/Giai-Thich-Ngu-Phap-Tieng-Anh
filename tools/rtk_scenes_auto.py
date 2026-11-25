#!/usr/bin/env python3
"""Mô tả cảnh cho ảnh minh hoạ Heisig RTK, lấy từ chính câu chuyện trong sách (tools/data/rtk_scenes.jsonl).

Nguồn ưu tiên (xem quy tắc trong docstring dưới):
  1. Sách Heisig (câu chuyện + ghi chú thành phần trong docs/kanji-viewer/rtk-data.js) — chuẩn.
  2. Cảnh viết tay đã có trong rtk_scenes.jsonl (dòng không có "auto") — giữ nguyên, chỉ kiểm tra.
  3. Keyword + thành phần — để dựng hình.

Mỗi frame tự động: keyword + thành phần Heisig in nghiêng + câu "hình ảnh" rõ nhất của câu chuyện
(câu có imagine/picture/think of…, bỏ các câu hướng dẫn viết nét). Không bịa thêm thành phần/quan hệ.
Không tìm được câu gợi nhớ đáng tin → ghi "review": lý do, để người xem lại chứ không đoán.

    python3 tools/rtk_scenes_auto.py            # viết lại mọi dòng "auto", giữ dòng viết tay
    python3 tools/rtk_scenes_auto.py --report   # chỉ in thống kê + danh sách cần xem lại
    .venv/bin/python tools/rtk_images.py --n 1
"""
import argparse
import html
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SC = ROOT / "tools/data/rtk_scenes.jsonl"
MAX_WORDS = 40          # sd-turbo (CLIP) chỉ đọc ~77 token

POSTPONED = re.compile(r"pass over|postpone|glide over (them|it)|until later", re.I)
IMAGERY = re.compile(r"\b(imagine|picture|think of|see|image|story|scene|visualize|just as|like a)\b", re.I)
WRITING = re.compile(r"\b(stroke|strokes|write|writing|written|frame|key ?word|kanji|character|primitive|"
                     r"element|elements|lesson|chapter|book|radical|pronounc)\w*", re.I)


def load_rtk():
    js = "global.window={};require(process.argv[1]);process.stdout.write(JSON.stringify(window.RTK))"
    return json.loads(subprocess.check_output(["node", "-e", js, str(ROOT / "docs/kanji-viewer/rtk-data.js")]))


def clean(s):
    s = html.unescape(re.sub(r"<[^>]+>", "", s or "")).replace("’", "'")
    s = re.sub(r"(-\w+-) (\w)", r"\1\2", s)                      # "birth- and-death" giữ gạch nối
    s = re.sub(r"(\w)- (\w)", r"\1\2", s)                       # "divin- ing" (gạch nối ngắt dòng của bản scan)
    s = re.sub(r"\s*\[\d+\]", "", s)                              # số nét
    s = re.sub(r"\((see )?frames? [\d, and]+\)", "", s)
    s = re.sub(r"[　-鿿\U00020000-\U0002ffff]+", "", s)  # chữ Hán trong câu chuyện
    return re.sub(r"\s+", " ", s).strip()


def prims(story, kw):
    out = []
    # chữ nghiêng ngay trước chữ Hán / "(frame N)" là chữ khác được nhắc để so sánh, không phải thành phần
    story = re.sub(r"<i>([^<]*)</i>(\s*[\u3000-\u9fff]|\s*\(frame)", r"\1\2", story or "")
    for m in re.findall(r"<i>(.*?)</i>", story, flags=re.S):
        for p in re.split(r"\.{2,}|…|,|;|\band\b", clean(m)):
            p = re.sub(r"[^A-Za-z' -]", " ", p).strip(" -'").lower()
            p = re.sub(r"\s+", " ", p)
            if 2 < len(p) < 30 and p != kw.lower() and p not in out and not re.fullmatch(r"(the|a|an|of|to|in|on)", p):
                out.append(p)
    return out[:4]


def best_sentence(story, kw, ps):
    """Câu mang hình ảnh gợi nhớ: chứa keyword/thành phần, có động từ hình ảnh, ít chữ về cách viết nét."""
    best, score = None, 0
    for s in re.split(r"(?<=[.!?])\s+|(?<=[.!?]”)\s+", clean(story)):
        low = s.lower()
        hits = sum(p in low for p in ps) + (kw.lower() in low)
        if not hits or len(s.split()) < 7 or not s[:1].isupper() or s.rstrip().endswith(("...", "…")):
            continue
        sc = 2 * hits + 2 * len(IMAGERY.findall(s)) - 3 * len(WRITING.findall(s))
        if sc > score:
            best, score = s, sc
    return best


def trim(s, n):
    w = s.split()
    return " ".join(w[:n]).rstrip(",;:") if len(w) > n else s


def scene(r):
    """-> (mô tả cảnh, lý do cần xem lại hoặc None)"""
    kw, story = re.sub(r"\s+", " ", r[2]).strip(), r[5]
    picto = re.search(r"pictograph|picture of", clean(story), re.I)
    if not story or not clean(story):
        return f"a simple picture of '{kw}'", "không có câu chuyện Heisig"
    if POSTPONED.search(clean(story)):
        return None, "sách hoãn câu chuyện tới bài sau"
    ps = prims(story, kw)
    sent = best_sentence(story, kw, ps)
    head = f"'{kw}'" + (f": {', '.join(ps)}" if ps else "")
    if sent:
        return trim(f"{head}. {sent}", MAX_WORDS), None
    if ps:
        return trim(head, MAX_WORDS), "primitives"   # sách chỉ cho thành phần (người học tự dựng chuyện) — vẫn đúng sách
    if picto:                                     # chữ tượng hình: vẽ đúng vật theo keyword
        return f"a simple clear picture of '{kw}' (pictograph)", None
    return f"a simple picture of '{kw}'", "câu chuyện không nêu thành phần/hình ảnh"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", action="store_true")
    args = ap.parse_args()
    rows = [json.loads(l) for l in SC.read_text(encoding="utf-8").splitlines() if l.strip()]
    hand = {o["f"]: o for o in rows if not o.get("auto")}
    out, flagged = [], []
    for r in load_rtk():
        f = r[1]
        if not f or not r[2] or not r[3]:
            continue
        if f in hand:
            o = hand[f]
        else:
            sc, why = scene(r)
            o = {"f": f, "scene": sc, "auto": 1}
            if why == "primitives":
                o["basis"] = "primitives"
            elif why:
                o["review"] = why
                if sc is None:                    # sách chưa kể chuyện: chỉ dựng từ keyword, chờ xem lại
                    o["scene"] = f"a simple picture of '{r[2]}'"
        if o.get("review"):
            flagged.append((f, r[0], r[2], o["review"]))
        out.append(o)
    out.sort(key=lambda o: o["f"])
    nb = sum(o.get("basis") == "primitives" for o in out)
    print(f"{len(out)} frame · {len(hand)} viết tay · {len(out) - len(hand)} tự động "
          f"({nb} chỉ có thành phần) · {len(flagged)} cần xem lại")
    for f, k, kw, why in flagged:
        print(f"  #{f} {k} {kw}: {why}")
    if not args.report:
        SC.write_text("".join(json.dumps(o, ensure_ascii=False) + "\n" for o in out), encoding="utf-8")


if __name__ == "__main__":
    main()
