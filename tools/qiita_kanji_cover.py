#!/usr/bin/env python3
"""Tìm ÍT bài Qiita nhất mà đọc hết thì gặp đủ (nhiều nhất) 2136 Kanji thường dùng.

1. Lấy danh sách bài từ sitemap công khai của Qiita (cdn.qiita.com/sitemap-https), chọn ngẫu nhiên N bài.
2. Tải từng bài (trang bài viết; robots.txt của Qiita cho phép, chỉ chặn /api, /search…), lấy phần
   nội dung bài, BỎ khối code, rồi chỉ ghi lại TẬP KANJI có trong bài (không lưu nội dung bài).
   Lưu ở tools/data/qiita_kanji.jsonl (chạy lại sẽ tiếp tục).
3. Set cover: chọn ít bài nhất phủ nhiều kanji nhất (tham lam -> bỏ bài thừa), xếp thứ tự
   bài có nhiều chữ mới (chữ hay gặp/ JLPT thấp trước) lên đầu.
Ra docs/qiita-kanji-2136.md.

    python3 tools/qiita_kanji_cover.py --n 6000 --jobs 3
"""
import argparse
import gzip
import json
import os
import random
import re
import sys
import threading
import time
import urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, "docs")
DATA = os.path.join(ROOT, "tools", "data")
OUT = os.path.join(DATA, "qiita_kanji.jsonl")
URLS = os.path.join(DATA, "qiita_item_urls.txt")
UA = "Mozilla/5.0 (kanji-study personal notes)"
lock = threading.Lock()


def get(url, tries=4):
    for a in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code in (404, 410, 403):
                return None
            time.sleep(3 + 3 * a)
        except Exception:
            time.sleep(2 + 2 * a)
    return None


def load_kanji():
    s = open(os.path.join(DOCS, "kanji-viewer", "kanji-game-data.js"), encoding="utf-8").read()
    a = s.index("window.KANJI=") + len("window.KANJI=")
    rows = json.loads(s[a:s.index("]];", a) + 2])
    return {r[1]: dict(n=r[0], hv=r[2], m=r[3], j=r[4]) for r in rows}


def item_urls():
    if os.path.exists(URLS):
        return open(URLS, encoding="utf-8").read().split()
    idx = gzip.decompress(get("https://cdn.qiita.com/sitemap-https/sitemap.xml.gz")).decode()
    out = []
    for sm in re.findall(r"<loc>([^<]+)</loc>", idx):
        raw = get(sm)
        if not raw:
            continue
        locs = re.findall(r"<loc>([^<]+)</loc>", gzip.decompress(raw).decode())
        out += [u for u in locs if "/items/" in u]
        print("  sitemap", sm.rsplit("/", 1)[-1], len(out), flush=True)
    open(URLS, "w", encoding="utf-8").write("\n".join(out))
    return out


class Body(HTMLParser):
    """Lấy chữ trong <div id="personal-public-article-body">, bỏ <pre>/<code>."""

    def __init__(self):
        super().__init__()
        self.depth = 0
        self.skip = 0
        self.text = []
        self.title = ""
        self._t = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "title":
            self._t = True
        if self.depth:
            if tag == "div":
                self.depth += 1
            if tag in ("pre", "code", "script", "style"):
                self.skip += 1
        elif tag == "div" and a.get("id") == "personal-public-article-body":
            self.depth = 1

    def handle_endtag(self, tag):
        if tag == "title":
            self._t = False
        if not self.depth:
            return
        if tag in ("pre", "code", "script", "style") and self.skip:
            self.skip -= 1
        if tag == "div":
            self.depth -= 1

    def handle_data(self, d):
        if self._t:
            self.title += d
        if self.depth and not self.skip:
            self.text.append(d)


def scan(url, jouyou):
    raw = get(url)
    if raw is None:
        return dict(u=url, ok=0)
    p = Body()
    p.feed(raw.decode("utf-8", "replace"))
    txt = "".join(p.text)
    ks = sorted({c for c in txt if c in jouyou})
    jp = len(re.findall(r"[぀-ヿ一-鿿]", txt))
    title = re.sub(r"\s*-\s*Qiita\s*$", "", p.title.strip())
    return dict(u=url, ok=1, t=title[:150], jp=jp, k="".join(ks))


def crawl(n, jobs, jouyou, seed=2136):
    urls = item_urls()
    random.Random(seed).shuffle(urls)
    done = set()
    if os.path.exists(OUT):
        for line in open(OUT, encoding="utf-8"):
            try:
                done.add(json.loads(line)["u"])
            except ValueError:
                pass
    todo = [u for u in urls[:n] if u not in done]
    print("tong %d bai trong sitemap, lay mau %d, can tai %d" % (len(urls), n, len(todo)), flush=True)
    f = open(OUT, "a", encoding="utf-8")
    cnt = [0]

    def work(u):
        r = scan(u, jouyou)
        time.sleep(0.6)  # lịch sự với máy chủ
        with lock:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
            cnt[0] += 1
            if cnt[0] % 200 == 0:
                f.flush()
                print("  %d/%d" % (cnt[0], len(todo)), flush=True)

    with ThreadPoolExecutor(jobs) as ex:
        list(ex.map(work, todo))
    f.close()


def cover(arts, U):
    """Ít bài nhất, phủ nhiều kanji nhất: dùng lại min_cover của playlist TOEIC
    (tham lam -> bỏ bài thừa -> đổi 2 bài lấy 1 bài phủ đủ cả hai)."""
    from toeic_songs_optimize import min_cover
    items = [dict(hits={c: 1 for c in a["k"]}, es=-a["jp"]) for a in arts]  # hoà thì ưu tiên bài ngắn
    reach = set().union(*(set(a["k"]) for a in arts)) & U
    return list(min_cover(items, reach))


def render(jouyou, arts, sel):
    E = lambda s: (s or "").replace("|", "\\|").replace("[", "\\[").replace("]", "\\]")
    fmt = lambda n: "{:,}".format(n).replace(",", ".")
    jw = {"N5": 5, "N4": 4, "N3": 3, "N2": 2, "N1": 1}
    w = lambda c: 1 + jw.get(jouyou[c]["j"], 0)  # chữ JLPT thấp (hay gặp) nặng hơn -> đọc trước
    U = set(jouyou)
    seen_any = set().union(*(set(a["k"]) for a in arts))
    # xếp thứ tự bài đã chọn
    order, cov, left = [], set(), list(sel)
    while left:
        j = max(left, key=lambda j: sum(w(c) for c in set(arts[j]["k"]) - cov))
        left.remove(j)
        new = [c for c in arts[j]["k"] if c not in cov]
        cov |= set(new)
        order.append((j, new))
    total = len(cov)
    L = ["# 📰 Đọc ít bài Qiita nhất mà gặp đủ 2136 Kanji\n",
         "> Quét **%s bài viết Qiita** (chọn ngẫu nhiên từ sitemap công khai; chỉ tính phần chữ, **bỏ khối code**), rồi chọn "
         "**ít bài nhất** mà đọc hết thì gặp nhiều Kanji thường dùng nhất (bài toán set cover: mỗi lượt lấy bài có nhiều chữ "
         "chưa gặp nhất, rồi bỏ bài thừa). Kết quả: **%s bài** phủ **%s/%s chữ** của bộ 2136 Kanji (%d%%). Thứ tự đã xếp để chữ JLPT "
         "N5→N1 (hay gặp) xuất hiện trước.\n>\n"
         "> Qiita là trang kỹ thuật (IT) nên rất hợp với [1800 từ vựng IT](kanji-viewer/write.html), nhưng một số chữ ít "
         "dùng trong văn kỹ thuật (thường gặp trong văn học, địa danh, cổ văn) sẽ không có — xem danh sách cuối trang.\n"
         % (fmt(len(arts)), fmt(len(sel)), fmt(total), fmt(len(U)), round(100 * total / len(U))),
         "## Đọc bao nhiêu bài thì gặp bao nhiêu Kanji?\n",
         "| Đọc bài 1 → | Số Kanji khác nhau đã gặp | %% cả bộ (%s chữ) | Riêng chữ N5–N3 đã gặp |" % fmt(len(U)), "|---|---|---|---|"]
    n53 = {c for c in U if jouyou[c]["j"] in ("N5", "N4", "N3")}
    cum, c53 = set(), set()
    marks = [m for m in (5, 10, 20, 30, 50, 75, 100, 150, 200, 300) if m < len(order)] + [len(order)]
    for k, (j, new) in enumerate(order, 1):
        cum |= set(new)
        if k in marks:
            L.append("| **%s bài** | %s | %d%% | %s/%s (%d%%) |" % (fmt(k), fmt(len(cum)), round(100 * len(cum) / len(U)),
                     fmt(len(cum & n53)), fmt(len(n53)), round(100 * len(cum & n53) / max(1, len(n53)))))
    L += ["\n## Danh sách bài (đọc theo thứ tự)\n",
          "| # | Bài viết | Kanji mới gặp | Số chữ mới |", "|---|---|---|---|"]
    for k, (j, new) in enumerate(order, 1):
        a = arts[j]
        new_s = sorted(new, key=lambda c: jouyou[c]["n"])
        L.append("| %d | [%s](%s) | %s | %d |" % (k, E(a["t"]), a["u"], " ".join(new_s), len(new)))
    miss = sorted(U - seen_any, key=lambda c: jouyou[c]["n"])
    L += ["\n## %s Kanji không gặp trong %s bài đã quét\n" % (fmt(len(miss)), fmt(len(arts))),
          "Bấm chữ để luyện viết. Đây là các chữ hiếm trong văn kỹ thuật — nên học qua [thẻ Kanji](kanji-viewer/write.html).\n",
          " ".join("[%s](kanji-viewer/write.html#%s ':ignore')" % (c, c) for c in miss), ""]
    open(os.path.join(DOCS, "qiita-kanji-2136.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("bai chon %d, phu %d/2136, khong gap %d" % (len(sel), total, len(miss)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=6000)
    ap.add_argument("--jobs", type=int, default=3)
    ap.add_argument("--no-fetch", action="store_true")
    a = ap.parse_args()
    jouyou = load_kanji()
    print("kanji:", len(jouyou), flush=True)
    if not a.no_fetch:
        crawl(a.n, a.jobs, jouyou)
    arts = [json.loads(l) for l in open(OUT, encoding="utf-8")]
    arts = [x for x in {x["u"]: x for x in arts if x.get("ok") and x.get("k")}.values()]
    print("bai co kanji:", len(arts), flush=True)
    sel = cover(arts, set(jouyou))
    render(jouyou, arts, sel)


if __name__ == "__main__":
    sys.exit(main())
