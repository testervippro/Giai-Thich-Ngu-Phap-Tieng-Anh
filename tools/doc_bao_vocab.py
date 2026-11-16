#!/usr/bin/env python3
"""Từ vựng + ngữ pháp của từng bài trong lộ trình "Đọc ít bài nhất mà gặp đủ Kanji" (doc-bao.html).

1. Lấy danh sách bài (theo thứ tự lộ trình) từ docs/kanji-viewer/doc-bao.html.
2. Tải lại từng bài (Qiita / Hatena Blog), chỉ lấy phần chữ, bỏ khối code; bỏ bài tác giả đặt noai/noindex.
   Bản chữ chỉ lưu trên máy: private/doc_bao_texts.jsonl (private/ không push).
3. Từ vựng: dò từ có Kanji theo từ điển docs/kanji-viewer/kic-words.json (9.279 từ: cách đọc, nghĩa, Hán Việt),
   khớp cả dạng chia của động từ / tính từ (使う → 使われ…). Từ ghép Kanji không có trong từ điển vẫn liệt kê,
   kèm âm Hán Việt + nghĩa từng chữ.
4. Ngữ pháp: dò theo tools/data/jp_grammar_vi.tsv (mẫu N5 → N1, nghĩa tiếng Việt).
Ra docs/kanji-viewer/bai/NNN.json (chỉ danh sách từ + mẫu ngữ pháp + 1 câu ngắn minh hoạ mỗi mẫu)
và trang xem docs/kanji-viewer/bai.html?n=NNN.

    python3 tools/doc_bao_vocab.py
"""
import json
import os
import re
import sys
import time
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
KV = os.path.join(ROOT, "docs", "kanji-viewer")
CACHE = os.path.join(ROOT, "private", "doc_bao_texts.jsonl")
OUTDIR = os.path.join(KV, "bai")
sys.path.insert(0, HERE)
import qiita_kanji_cover as Q  # noqa: E402

KANJI = r"[一-鿿々〆ヶ]"
HIRA = "ぁ-ゖ"
SENT = re.compile(r"[^。！？!?\n]+[。！？!?]?")


def routes():
    s = open(os.path.join(KV, "doc-bao.html"), encoding="utf-8").read()
    i = s.index("const D = ") + len("const D = ")
    return json.JSONDecoder().raw_decode(s[i:])[0]["arts"]


def fetch_all(arts):
    have = {}
    if os.path.exists(CACHE):
        for l in open(CACHE, encoding="utf-8"):
            x = json.loads(l)
            have[x["u"]] = x
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    with open(CACHE, "a", encoding="utf-8") as f:
        for k, a in enumerate(arts, 1):
            if a["u"] in have:
                continue
            if Q.BLOCKED[0] >= 5:
                print("!! may chu chan (403/429) -> dung, khong lach", flush=True)
                break
            raw = Q.get(a["u"])
            x = dict(u=a["u"], ok=0)
            if raw:
                p = Q.Body()
                p.feed(raw.decode("utf-8", "replace"))
                if not ("noai" in p.robots or "noindex" in p.robots):
                    x = dict(u=a["u"], ok=1, text="".join(p.text))
            have[a["u"]] = x
            f.write(json.dumps(x, ensure_ascii=False) + "\n")
            f.flush()
            print("  tai %d/%d %s" % (k, len(arts), "ok" if x["ok"] else "BO"), flush=True)
            time.sleep(1.5)
    return have


# ---------------- từ điển ----------------
def load_dict():
    words = json.load(open(os.path.join(KV, "kic-words.json"), encoding="utf-8"))
    s = open(os.path.join(KV, "kanji-game-data.js"), encoding="utf-8").read()
    a = s.index("window.KANJI=") + len("window.KANJI=")
    kj = {r[1]: (r[2], r[3], r[4]) for r in json.loads(s[a:s.index("]];", a) + 2])}
    exact, stems = {}, {}
    for w, rd, en, hv in words:
        if not re.search(KANJI, w):
            continue
        exact.setdefault(w, (w, rd, en, hv))
        verb = en.startswith("to ") and w[-1] in "うくすつぬふむゆるぐぶ"
        iadj = w.endswith("い") and not en.startswith("to ") and re.search(KANJI, w[:-1]) is not None
        if verb or iadj:
            st = w[:-1]
            if re.search(KANJI, st):
                stems.setdefault(st, []).append((w, rd, en, hv, "v" if verb else "a"))
    return exact, stems, kj


def starts_word(text, i, exact):
    """Có từ điển >= 2 chữ bắt đầu ở vị trí i không."""
    return any(text[i:i + L] in exact for L in range(2, 9))


VERB_NEXT = set("わいうえおかきくけこさしすせそたちつてとなにぬねのまみむめもらりるれろがぎぐげごばびぶべぼっんよ")
ADJ_NEXT = set("くかけさすいそ")


def vocab(text, exact, stems, kj):
    """-> Counter{từ gốc: lần}, info{từ gốc: (từ, đọc, nghĩa, Hán Việt, loại)}"""
    cnt, info = Counter(), {}
    maxlen = 10
    i, n = 0, len(text)
    while i < n:
        if not re.match(KANJI, text[i]):
            i += 1
            continue
        best = None
        for L in range(min(maxlen, n - i), 0, -1):
            seg = text[i:i + L]
            if seg in exact:
                best = (L, exact[seg], "")
                break
        for L in range(min(maxlen, n - i), 0, -1):
            seg = text[i:i + L]
            if seg in stems and i + L < n:
                nx = text[i + L]
                for w, rd, en, hv, kind in stems[seg]:
                    ok = nx in (VERB_NEXT if kind == "v" else ADJ_NEXT) or (kind == "v" and w.endswith("る") and nx in HIRA)
                    if ok and (best is None or L + 1 > best[0]):
                        best = (L + 1, (w, rd, en, hv), "")
                        break
                if best and best[0] == L + 1:
                    break
        run = re.match(KANJI + "+", text[i:]).group(0)
        if best and best[0] == 1 and len(run) >= 2 and not starts_word(text, i + 1, exact):
            best = None  # chữ lẻ trong cụm Kanji dài mà sau nó không bắt đầu từ nào -> coi cả cụm là từ ghép
        if best:
            L, (w, rd, en, hv), _ = best
            cnt[w] += 1
            info[w] = (w, rd, en, hv, "")
            i += L
            continue
        j = 1
        while j < len(run) and not starts_word(text, i + j, exact):
            j += 1
        run = run[:j] if j < len(run) and j >= 2 else run
        if len(run) >= 2:
            hv = " ".join(kj.get(c, ("?",))[0] for c in run)
            mean = " + ".join("%s (%s)" % (kj[c][0].lower(), kj[c][1]) for c in run if c in kj)
            cnt[run] += 1
            info[run] = (run, "", mean, hv, "ghep")
        i += len(run)
    return cnt, info


# ---------------- ngữ pháp ----------------
def load_grammar():
    out = []
    for l in open(os.path.join(HERE, "data", "jp_grammar_vi.tsv"), encoding="utf-8"):
        if l.startswith("#") or not l.strip():
            continue
        lv, pat, rx, mean = l.rstrip("\n").split("\t")
        out.append((lv, pat, re.compile(rx), mean))
    return out


def grammar(text, gram):
    sents = [s.strip() for s in SENT.findall(text) if s.strip()]
    res = []
    for lv, pat, rx, mean in gram:
        hits = [s for s in sents if rx.search(s)]
        if not hits:
            continue
        ex = min(hits, key=lambda s: (abs(len(s) - 30), s))  # câu ngắn vừa phải
        m = rx.search(ex)
        ex = ex if len(ex) <= 80 else ex[max(0, m.start() - 35):m.end() + 35]
        m = rx.search(ex)
        res.append([lv, pat, mean, len(hits), ex, [m.start(), m.end()] if m else None])
    order = {"N5": 0, "N4": 1, "N3": 2, "N2": 3, "N1": 4}
    res.sort(key=lambda r: (order[r[0]], -r[3]))
    return res


def main():
    arts = routes()
    print("bai trong lo trinh:", len(arts), flush=True)
    texts = fetch_all(arts)
    exact, stems, kj = load_dict()
    gram = load_grammar()
    os.makedirs(OUTDIR, exist_ok=True)
    seen = set()
    index = []
    for k, a in enumerate(arts, 1):
        x = texts.get(a["u"]) or {}
        if not x.get("ok"):
            index.append(dict(n=k, t=a.get("t"), ok=0))
            continue
        text = x["text"]
        cnt, info = vocab(text, exact, stems, kj)
        words = []
        for w, c in cnt.most_common():
            ww, rd, en, hv, kind = info[w]
            words.append([ww, rd, en, hv, c, 0 if w in seen else 1, kind])
        seen |= set(cnt)
        g = grammar(text, gram)
        d = dict(n=k, t=a.get("t"), u=a["u"], s=a.get("s"), k=a.get("k"),
                 chars=len(re.findall(r"[぀-ヿ一-鿿]", text)), words=words, grammar=g)
        json.dump(d, open(os.path.join(OUTDIR, "%03d.json" % k), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
        index.append(dict(n=k, t=a.get("t"), ok=1, nw=len(words), nnew=sum(w[5] for w in words), ng=len(g)))
    json.dump(index, open(os.path.join(OUTDIR, "index.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    ok = [r for r in index if r["ok"]]
    print("xong: %d/%d bai, tb %d tu, %d mau ngu phap / bai" % (
        len(ok), len(index), sum(r["nw"] for r in ok) // max(1, len(ok)), sum(r["ng"] for r in ok) // max(1, len(ok))))


if __name__ == "__main__":
    sys.exit(main())
