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


BLOCKED = [0]  # số lần liên tiếp bị 403/429 -> dừng hẳn (máy chủ đã chặn, không cố lách)


def get(url, tries=4):
    for a in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as r:
                BLOCKED[0] = 0
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code in (403, 429):
                BLOCKED[0] += 1
                return None
            if e.code in (404, 410):
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
        self.robots = ""

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "title":
            self._t = True
        if tag == "meta" and (a.get("name") or "").lower() == "robots":
            self.robots += (a.get("content") or "").lower()
        if self.depth:
            if tag == "div":
                self.depth += 1
            if tag in ("pre", "code", "script", "style"):
                self.skip += 1
        elif tag == "div" and (a.get("id") == "personal-public-article-body"            # Qiita
                               or "entry-content" in (a.get("class") or "").split()):  # Hatena Blog
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
    if "noai" in p.robots or "noindex" in p.robots:
        return dict(u=url, ok=0, why="robots")  # tác giả không muốn bị máy đọc -> bỏ qua
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


HOUT = os.path.join(DATA, "hatena_kanji.jsonl")
HURLS = os.path.join(DATA, "hatena_urls.txt")
HPORTAL = ["", "ranking", "staff_picks", "kodawari_blogs"] + ["topics/" + t for t in (
    "anime", "board_game", "career", "childcare", "cooking", "cosmetics", "creation", "diy", "fave", "gadget", "game",
    "gourmet", "journal", "learning", "life", "movie", "music", "book", "travel", "sports", "health", "money",
    "fashion", "pet", "outdoor", "photo", "history", "science", "society", "nature", "art", "comic", "idol", "car")]
ENTRY = re.compile(r'https://[a-z0-9-]+\.(?:hatenablog\.(?:com|jp)|hateblo\.jp|hatenadiary\.(?:com|jp|org))/entry/[^"?#<\s]+')


def hatena_urls(per_blog=12, expand=False):
    """Bài từ cổng hatena.blog (xếp hạng, chủ đề); expand=True: thêm vài bài khác của mỗi blog (sitemap của blog)."""
    seen = open(HURLS, encoding="utf-8").read().split() if os.path.exists(HURLS) else []
    if not seen:
        for pth in HPORTAL:
            raw = get("https://hatena.blog/" + pth)
            time.sleep(2)
            if raw:
                seen += ENTRY.findall(raw.decode("utf-8", "replace"))
        seen = list(dict.fromkeys(seen))
        open(HURLS, "w", encoding="utf-8").write("\n".join(seen))
    if not expand:
        return seen
    hosts = list(dict.fromkeys(u.split("/")[2] for u in seen))
    print("  cong: %d bai, %d blog" % (len(seen), len(hosts)), flush=True)
    rnd = random.Random(2136)
    for h in hosts:
        if BLOCKED[0] >= 5:
            break
        raw = get("https://%s/sitemap_index.xml" % h)
        time.sleep(1.5)
        if not raw:
            continue
        sms = re.findall(r"<loc>([^<]+)</loc>", raw.decode("utf-8", "replace"))[:1]
        ents = []
        for sm in sms:
            r2 = get(sm)
            time.sleep(1.5)
            if r2:
                ents += [u for u in re.findall(r"<loc>([^<]+)</loc>", r2.decode("utf-8", "replace")) if "/entry/" in u]
        rnd.shuffle(ents)
        seen += ents[:per_blog]
    seen = list(dict.fromkeys(seen))
    open(HURLS, "w", encoding="utf-8").write("\n".join(seen))
    print("  tong %d bai Hatena" % len(seen), flush=True)
    return seen


def crawl_hatena(n, jouyou, delay=1.5, expand=False):
    urls = hatena_urls(expand=expand)
    done = set()
    if os.path.exists(HOUT):
        done = {json.loads(l)["u"] for l in open(HOUT, encoding="utf-8") if l.strip()}
    todo = [u for u in urls if u not in done][:n]
    print("Hatena: %d bai trong danh sach, can tai %d" % (len(urls), len(todo)), flush=True)
    with open(HOUT, "a", encoding="utf-8") as f:
        for k, u in enumerate(todo, 1):
            if BLOCKED[0] >= 5:
                print("  !! may chu tra 403/429 lien tiep -> DUNG (khong co lach)", flush=True)
                break
            f.write(json.dumps(scan(u, jouyou), ensure_ascii=False) + "\n")
            time.sleep(delay)
            if k % 100 == 0:
                f.flush()
                print("  %d/%d" % (k, len(todo)), flush=True)


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
    nq = sum(1 for a in arts if a["src"] == "Qiita")
    L = ["# 📰 Đọc ít bài nhất (Qiita + Hatena Blog) mà gặp nhiều Kanji nhất\n",
         "> Quét **%s bài viết** — %s bài Qiita (IT) + %s bài Hatena Blog (nhật ký, nấu ăn, du lịch, sách, phim…); chỉ tính "
         "phần chữ của bài, **bỏ khối code**, bỏ bài tác giả đặt *noai/noindex* — rồi chọn "
         "**ít bài nhất** mà đọc hết thì gặp nhiều Kanji thường dùng nhất (bài toán set cover: mỗi lượt lấy bài có nhiều chữ "
         "chưa gặp nhất, rồi bỏ bài thừa). Kết quả: **%s bài** phủ **%s/%s chữ** của bộ 2136 Kanji (%d%%). Thứ tự đã xếp để chữ JLPT "
         "N5→N1 (hay gặp) xuất hiện trước.\n>\n"
         "> Qiita là trang kỹ thuật (IT); Hatena Blog là blog đời sống nên bù thêm chữ văn chương, đời thường. Chữ quá "
         "hiếm (cổ văn, địa danh, tên riêng) vẫn có thể không gặp — xem danh sách cuối trang.\n"
         % (fmt(len(arts)), fmt(nq), fmt(len(arts) - nq), fmt(len(sel)), fmt(total), fmt(len(U)), round(100 * total / len(U))),
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
          "| # | Nguồn | Bài viết | Kanji mới gặp | Số chữ mới |", "|---|---|---|---|---|"]
    for k, (j, new) in enumerate(order, 1):
        a = arts[j]
        new_s = sorted(new, key=lambda c: jouyou[c]["n"])
        L.append("| %d | %s | [%s](%s) | %s | %d |" % (k, a["src"], E(a["t"]), a["u"], " ".join(new_s), len(new)))
    miss = sorted(U - seen_any, key=lambda c: jouyou[c]["n"])
    L += ["\n## %s Kanji không gặp trong %s bài đã quét\n" % (fmt(len(miss)), fmt(len(arts))),
          "Bấm chữ để luyện viết. Đây là các chữ hiếm trong bài viết trên mạng — nên học qua [thẻ Kanji](kanji-viewer/write.html).\n",
          " ".join("[%s](kanji-viewer/write.html#%s ':ignore')" % (c, c) for c in miss), ""]
    open(os.path.join(DOCS, "qiita-kanji-2136.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    render_html(jouyou, arts, order, miss, U)
    print("bai chon %d, phu %d/2136, khong gap %d" % (len(sel), total, len(miss)))


def load_arts():
    arts = []
    for path, src in ((OUT, "Qiita"), (HOUT, "Hatena")):
        if os.path.exists(path):
            for l in open(path, encoding="utf-8"):
                try:
                    x = json.loads(l)
                except ValueError:
                    continue  # dòng đang ghi dở (vừa tải vừa xem)
                if x.get("ok") and x.get("k"):
                    x["src"] = src
                    arts.append(x)
    return list({x["u"]: x for x in arts}.values())


def render_html(jouyou, arts, order, miss, U):
    """Trang tương tác docs/kanji-viewer/doc-bao.html: bảng mức đọc (bấm để xem bài) + thẻ học các chữ chưa gặp."""
    n53 = {c for c in U if jouyou[c]["j"] in ("N5", "N4", "N3")}
    marks = [m for m in (5, 10, 30, 50) if m < len(order)] + [len(order)]
    levels, cum, prev = [], set(), 0
    for k, (j, new) in enumerate(order, 1):
        cum |= set(new)
        if k in marks:
            levels.append(dict(n=k, a=prev + 1, seen=len(cum), pct=round(100 * len(cum) / len(U)),
                               n53=100 * len(cum & n53) // max(1, len(n53)), n53n=len(cum & n53)))
            prev = k
    data = dict(
        total=len(U), n53tot=len(n53), scanned=len(arts), nq=sum(1 for a in arts if a["src"] == "Qiita"),
        levels=levels,
        arts=[dict(s=arts[j]["src"], t=arts[j]["t"], u=arts[j]["u"],
                   k="".join(sorted(new, key=lambda c: jouyou[c]["n"]))) for j, new in order],
        miss=[[c, jouyou[c]["hv"], jouyou[c]["m"], jouyou[c]["j"], jouyou[c]["n"]] for c in miss])
    open(os.path.join(DOCS, "kanji-viewer", "kanji-miss.js"), "w", encoding="utf-8").write(
        "// Kanji không gặp trong các bài Qiita + Hatena đã quét (sinh bởi tools/qiita_kanji_cover.py)\n"
        "window.KANJI_MISS = " + json.dumps([m[0] for m in data["miss"]], ensure_ascii=False) + ";\n")
    tpl = open(os.path.join(ROOT, "tools", "doc_bao_template.html"), encoding="utf-8").read()
    open(os.path.join(DOCS, "kanji-viewer", "doc-bao.html"), "w", encoding="utf-8").write(
        tpl.replace("/*DATA*/null", json.dumps(data, ensure_ascii=False)))
    print("html: doc-bao.html,", len(levels), "muc,", len(miss), "chu chua gap")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=("qiita", "hatena", "none"), default="hatena")
    ap.add_argument("--n", type=int, default=3000)
    ap.add_argument("--jobs", type=int, default=1)
    ap.add_argument("--expand", action="store_true", help="Hatena: thêm bài khác của mỗi blog (đọc sitemap, chậm)")
    a = ap.parse_args()
    jouyou = load_kanji()
    print("kanji:", len(jouyou), flush=True)
    if a.source == "qiita":
        crawl(a.n, a.jobs, jouyou)
    elif a.source == "hatena":
        crawl_hatena(a.n, jouyou, expand=a.expand)
    arts = load_arts()
    print("bai co kanji:", len(arts), flush=True)
    sel = cover(arts, set(jouyou))
    render(jouyou, arts, sel)


if __name__ == "__main__":
    sys.exit(main())
