#!/usr/bin/env python3
"""Tìm bài hát có từ TOEIC **trong lời hát** bằng LRCLIB (https://lrclib.net, kho lời bài hát mở).

Hai danh sách từ (lấy từ các trang sẵn có):
  - ETS 2026 Reading + Listening : docs/toeic-vocabulary-songs-real-ets.md (3.268 từ, có số lần xuất hiện)
  - Hackers TOEIC Index đầy đủ    : docs/toeic-vocabulary-index.md        (5.039 mục, có nghĩa)

Với mỗi từ/cụm từ: gọi GET /api/search?q=<từ> (API chỉ tìm theo tên bài/ca sĩ/album), tải lời
các bài trả về, CHỈ giữ bài có lời hát chứa nguyên từ đó (khớp cả từ, không phân biệt hoa thường),
ưu tiên lời tiếng Anh; lấy tối đa 2 bài khác ca sĩ + dòng hát chứa từ.
Kết quả cache ở tools/data/lrclib_cache.json (chạy lại sẽ tiếp tục).

Ra docs/toeic-songs-lyrics.md — gộp 2 danh sách, BỎ TRÙNG (mỗi từ khoá tìm kiếm một dòng)

    python3 tools/toeic_songs_lrclib.py [--jobs 4] [--limit N]
"""
import argparse
import json
import os
import re
import sys
import threading
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, "docs")
CACHE = os.path.join(ROOT, "tools", "data", "lrclib_cache.json")
UA = "toeic-vocab-study/1.0 (personal study notes)"
API = "https://lrclib.net/api/search?q="
lock = threading.Lock()


def load_ets():
    rows = []
    for line in open(os.path.join(DOCS, "toeic-vocabulary-songs-real-ets.md"), encoding="utf-8"):
        m = re.match(r"^\| (\d+) \| \*\*(.+?)\*\* \| (\d+) lần", line)
        if m:
            rows.append(dict(n=int(m.group(1)), term=m.group(2).strip(), info="%s lần trong đề" % m.group(3)))
    return rows


def load_index():
    rows = []
    for line in open(os.path.join(DOCS, "toeic-vocabulary-index.md"), encoding="utf-8"):
        m = re.match(r"^\| (\d+) \| (.+?) \| (.*?) \|\s*$", line)
        if m and m.group(1).isdigit():
            rows.append(dict(n=int(m.group(1)), term=m.group(2).strip(), info=m.group(3).strip()))
    return rows


def query_of(term):
    """'A as well as B' -> 'as well as'; 'be eligible for ~' -> 'eligible for'; bỏ (…), sb/sth/one's."""
    t = re.sub(r"\(.*?\)|\[.*?\]", " ", term)
    t = re.sub(r"[~…/]", " ", t)
    words = [w for w in t.split() if w not in ("A", "B", "sb", "sth", "somebody", "something", "one's", "oneself", "~")]
    if words and words[0].lower() == "be" and len(words) > 1:
        words = words[1:]
    q = " ".join(words).strip(" ,.;:-")
    return q.lower()


def english_score(text):
    w = re.findall(r"[A-Za-z']+", text)
    common = sum(1 for x in w if x.lower() in ("the", "you", "and", "i", "to", "a", "me", "my", "it", "in", "of", "is", "that", "your", "on", "we", "be", "for", "love"))
    return common / max(1, len(w))


def fetch(q):
    url = API + urllib.parse.quote(q)
    for attempt in range(5):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code in (429, 503):
                time.sleep(int(e.headers.get("Retry-After", "2") or 2) + attempt)
                continue
            if e.code == 404:
                return []
            time.sleep(1 + attempt)
        except Exception:
            time.sleep(1 + attempt)
    return None


def find_songs(q):
    data = fetch(q)
    if data is None:
        return None
    rx = re.compile(r"(?<![A-Za-z'])%s(?![A-Za-z'])" % re.escape(q).replace(r"\ ", r"\s+"), re.I)
    hits = []
    seen_artist = set()
    for x in data:
        pl = x.get("plainLyrics") or ""
        if not pl or x.get("instrumental"):
            continue
        m = rx.search(pl)
        if not m:
            continue
        es = english_score(pl)
        if es < 0.08:
            continue
        # dòng chứa từ
        s = pl.rfind("\n", 0, m.start()) + 1
        e = pl.find("\n", m.end())
        line = pl[s:e if e >= 0 else len(pl)].strip()
        hits.append(dict(track=x["trackName"], artist=x["artistName"], line=line[:200], es=round(es, 2),
                         in_title=bool(rx.search(x["trackName"] or ""))))
    hits.sort(key=lambda h: (-h["es"]))
    out = []
    for h in hits:
        a = h["artist"].lower()
        if a in seen_artist:
            continue
        seen_artist.add(a)
        out.append(h)
        if len(out) == 2:
            break
    return out


def md_esc(s):
    return (s or "").replace("|", "\\|").replace("*", "\\*")


def link_q(s):
    return urllib.parse.quote(s)


def render(rows, cache, title, intro, out_name, info_col):
    found = sum(1 for r in rows if cache.get(r["q"]))
    L = ["# %s\n" % title,
         "> " + intro + "\n>\n"
         "> **%d/%d mục (%d%%)** tìm được bài hát có từ đó **trong lời hát** (LRCLIB). Cột *Lời hát* trích đúng dòng "
         "chứa từ, từ được **in đậm**. Link Spotify/YouTube là link tìm kiếm theo ca sĩ + tên bài; YouGlish là video "
         "người bản xứ nói từ đó.\n>\n> Cách tìm: API LRCLIB chỉ tìm theo tên bài/ca sĩ/album, nên bài hát được lấy từ "
         "kết quả tìm kiếm rồi **kiểm tra lời hát** có chứa nguyên từ hay không — từ hiếm (reimbursement…) thường "
         "không có bài nào. Lời hát thuộc bản quyền tác giả; chỉ trích 1 dòng để học từ.\n"
         % (found, len(rows), round(100 * found / max(1, len(rows)))),
         "| # | Từ / cụm từ | %s | Bài hát (lời có từ này) | 🎤 Lời hát | Nghe | Người thật nói |" % info_col,
         "|---|---|---|---|---|---|---|"]
    for r in rows:
        hits = cache.get(r["q"]) or []
        yg = "[▶ YouGlish](https://youglish.com/pronounce/%s/english)" % link_q(r["q"] or r["term"])
        if not hits:
            L.append("| %d | **%s** | %s | — | | | %s |" % (r["n"], md_esc(r["term"]), md_esc(r["info"]), yg))
            continue
        songs, lines, listen = [], [], []
        rx = re.compile(r"(?<![A-Za-z'])(%s)(?![A-Za-z'])" % re.escape(r["q"]).replace(r"\ ", r"\s+"), re.I)
        for h in hits:
            songs.append("*%s* – %s" % (md_esc(h["track"]), md_esc(h["artist"])))
            lines.append(rx.sub(lambda m: "**" + m.group(1) + "**", md_esc(h["line"]), count=1))
            qq = link_q("%s %s" % (h["artist"], h["track"]))
            listen.append("[Spotify](https://open.spotify.com/search/%s) · [YouTube](https://www.youtube.com/results?search_query=%s)" % (qq, qq))
        L.append("| %d | **%s** | %s | %s | %s | %s | %s |" % (
            r["n"], md_esc(r["term"]), md_esc(r["info"]), "<br>".join(songs), "<br>".join("“%s”" % l for l in lines),
            "<br>".join(listen), yg))
    open(os.path.join(DOCS, out_name), "w", encoding="utf-8").write("\n".join(L) + "\n")
    print(out_name, found, "/", len(rows))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()
    ets, idx = load_ets(), load_index()
    for r in ets + idx:
        r["q"] = query_of(r["term"])
    cache = json.load(open(CACHE, encoding="utf-8")) if os.path.exists(CACHE) else {}
    todo = sorted({r["q"] for r in ets + idx if r["q"] and len(r["q"]) >= 2} - set(cache))
    if a.limit:
        todo = todo[:a.limit]
    print("ets %d, index %d, can tra %d (da co cache %d)" % (len(ets), len(idx), len(todo), len(cache)), flush=True)
    done = [0]

    def work(q):
        res = find_songs(q)
        with lock:
            if res is not None:
                cache[q] = res
            done[0] += 1
            if done[0] % 100 == 0:
                json.dump(cache, open(CACHE, "w", encoding="utf-8"), ensure_ascii=False)
                print("  %d/%d" % (done[0], len(todo)), flush=True)

    with ThreadPoolExecutor(a.jobs) as ex:
        list(ex.map(work, todo))
    json.dump(cache, open(CACHE, "w", encoding="utf-8"), ensure_ascii=False)

    # gộp 2 danh sách, BỎ TRÙNG theo từ khoá tìm kiếm (vd "A as well as B" == "as well as")
    merged, pos = [], {}
    for r in ets:
        if not r["q"] or r["q"] in pos:
            continue
        pos[r["q"]] = len(merged)
        merged.append(dict(term=r["term"], q=r["q"], ets=r["info"].split()[0], mean="", src="ETS"))
    dup = 0
    for r in sorted(idx, key=lambda r: r["term"].lower()):
        if not r["q"]:
            continue
        if r["q"] in pos:
            m = merged[pos[r["q"]]]
            if not m["mean"]:
                m["mean"] = r["info"]
            m["src"] = "ETS · Hackers"
            dup += 1
            continue
        pos[r["q"]] = len(merged)
        merged.append(dict(term=r["term"], q=r["q"], ets="", mean=r["info"], src="Hackers"))
    print("gop: %d muc (bo %d muc trung)" % (len(merged), len(ets) + len(idx) - len(merged)))
    render_merged(merged, cache, dup)


def render_merged(rows, cache, dup):
    found = sum(1 for r in rows if cache.get(r["q"]))
    n_ets = sum(1 for r in rows if r["ets"])
    L = ["# 🎤 Từ vựng TOEIC trong LỜI BÀI HÁT — ETS 2026 + Hackers Index (đã bỏ trùng)\n",
         "> Gộp [3.268 từ trong đề ETS 2026](toeic-vocabulary-songs-real-ets.md) (Reading + Listening) và "
         "[5.039 mục Hackers TOEIC Index](toeic-vocabulary-index.md), **mỗi từ chỉ một dòng** (%d từ có trong cả hai "
         "danh sách được gộp lại, cột *Nguồn* ghi rõ). Tổng **%s mục**: phần 1 là %s từ có trong đề ETS (xếp theo số lần "
         "xuất hiện), phần 2 là các mục chỉ có trong Hackers (A–Z).\n>\n"
         "> **%s/%s mục (%d%%)** tìm được bài hát có từ đó **trong lời hát** (kho lời bài hát mở [LRCLIB](https://lrclib.net)). "
         "Cột *Lời hát* trích đúng dòng chứa từ, từ được **in đậm**. Spotify/YouTube là link tìm kiếm theo ca sĩ + tên bài; "
         "YouGlish là video người bản xứ nói từ đó.\n>\n"
         "> Cách tìm: (1) API LRCLIB chỉ tìm theo tên bài/ca sĩ/album, nên bài hát lấy từ kết quả tìm kiếm rồi **kiểm tra lời "
         "hát** có chứa nguyên từ; (2) với từ còn thiếu, tải một kho lời bài hát tiếng Anh về máy và tìm thẳng trong lời, "
         "chấp nhận cả **dạng chia** của từ (ghi *(dạng: …)* sau câu hát, vd reimburse → reimbursed). Từ quá chuyên ngành "
         "vẫn có thể không có bài nào. Cụm có A/B/sb/sth được bỏ phần giữ chỗ khi tìm. Lời hát thuộc bản quyền tác giả; chỉ trích 1 dòng để học từ.\n"
         % (dup, "{:,}".format(len(rows)), "{:,}".format(n_ets), "{:,}".format(found), "{:,}".format(len(rows)),
            round(100 * found / max(1, len(rows)))),
         "**Đi nhanh:** [Phần 1 — từ trong đề ETS](#p1) · [Phần 2 — chỉ có trong Hackers](#p2)\n"]
    head = ("| # | Từ / cụm từ | Nguồn | Số lần trong đề ETS | Nghĩa | Bài hát (lời có từ này) | 🎤 Lời hát | Nghe | Người thật nói |\n"
            "|---|---|---|---|---|---|---|---|---|")
    k = 0
    for part, title, sel in (("p1", "Phần 1 — Từ có trong đề ETS 2026 (xếp theo số lần xuất hiện)", lambda r: r["ets"]),
                             ("p2", "Phần 2 — Chỉ có trong Hackers TOEIC Index (A–Z)", lambda r: not r["ets"])):
        L.append('\n<a id="%s"></a>\n\n## %s\n\n%s' % (part, title, head))
        for r in rows:
            if not sel(r):
                continue
            k += 1
            hits = cache.get(r["q"]) or []
            yg = "[▶ YouGlish](https://youglish.com/pronounce/%s/english)" % link_q(r["q"])
            base = "| %d | **%s** | %s | %s | %s |" % (k, md_esc(r["term"]), r["src"], r["ets"], md_esc(r["mean"]))
            if not hits:
                L.append(base + " — | | | %s |" % yg)
                continue
            rx = re.compile(r"(?<![A-Za-z'])(%s)(?![A-Za-z'])" % re.escape(r["q"]).replace(r"\ ", r"\s+"), re.I)
            songs = "<br>".join("*%s* – %s" % (md_esc(h["track"]), md_esc(h["artist"])) for h in hits)
            def bold(h):
                r2 = re.compile(r"(?<![A-Za-z'])(%s)(?![A-Za-z'])" % re.escape(h["word"]).replace(r"\ ", r"\s+"), re.I) if h.get("word") else rx
                t = r2.sub(lambda m: "**" + m.group(1) + "**", md_esc(h["line"]), count=1)
                if h.get("word") and h["word"].lower() != r["q"]:
                    t += " *(dạng: %s)*" % md_esc(h["word"].lower())
                return "“%s”" % t if not t.endswith(")*") else "“%s”%s" % (t[:t.rindex(" *(")], t[t.rindex(" *("):])
            lines = "<br>".join(bold(h) for h in hits)
            listen = "<br>".join("[Spotify](https://open.spotify.com/search/{0}) · [YouTube](https://www.youtube.com/results?search_query={0})"
                                 .format(link_q("%s %s" % (h["artist"], h["track"]))) for h in hits)
            L.append(base + " %s | %s | %s | %s |" % (songs, lines, listen, yg))
    text = "\n".join(L) + "\n"
    i2 = text.index('\n<a id="p2"></a>')
    intro, p1 = text[:text.index('\n<a id="p1"></a>')], text[text.index('\n<a id="p1"></a>'):i2]
    nav = intro.replace("[Phần 2 — chỉ có trong Hackers](#p2)", "[Phần 2 — chỉ có trong Hackers](toeic-songs-lyrics-hackers.md)") \
        + "\n**🎧 Tạo playlist:** [danh sách bài hát để nhập vào TuneMyMusic / Soundiiz](toeic-songs-playlist.md)\n"
    open(os.path.join(DOCS, "toeic-songs-lyrics.md"), "w", encoding="utf-8").write(nav + p1)
    open(os.path.join(DOCS, "toeic-songs-lyrics-hackers.md"), "w", encoding="utf-8").write(
        "# 🎤 Phần 2 — mục chỉ có trong Hackers TOEIC Index: bài hát có từ trong LỜI HÁT\n\n"
        "> Tiếp theo [Phần 1 — từ trong đề ETS 2026](toeic-songs-lyrics.md) (đã bỏ trùng: từ có ở cả hai danh sách "
        "chỉ nằm ở Phần 1). Cách tìm và chú thích: xem đầu Phần 1.\n" + text[i2:])
    export_playlists(rows, cache)
    print("toeic-songs-lyrics.md (+ -hackers)", found, "/", len(rows))


def export_playlists(rows, cache, size=200):
    """Danh sách 'Ca sĩ - Tên bài' (bỏ trùng bài) theo thứ tự trang, chia file 200 bài cho TuneMyMusic."""
    d = os.path.join(DOCS, "toeic-songs-playlist")
    os.makedirs(d, exist_ok=True)
    for f in os.listdir(d):
        if f.endswith(".txt"):
            os.remove(os.path.join(d, f))
    seen, songs = set(), []
    for part in ("ets", "hackers"):
        for r in rows:
            if (part == "ets") != bool(r["ets"]):
                continue
            for h in cache.get(r["q"]) or []:
                key = (h["artist"].lower(), h["track"].lower())
                if key not in seen:
                    seen.add(key)
                    songs.append((part, r["term"], "%s - %s" % (h["artist"], h["track"])))
    files = []
    for part, label in (("ets", "ETS 2026"), ("hackers", "Hackers Index")):
        lst = [x for x in songs if x[0] == part]
        for k in range(0, len(lst), size):
            name = "toeic-%s-%03d-%03d.txt" % (part, k + 1, min(k + size, len(lst)))
            open(os.path.join(d, name), "w", encoding="utf-8").write("\n".join(x[2] for x in lst[k:k + size]) + "\n")
            files.append((label, k + 1, min(k + size, len(lst)), name, lst[k][1], lst[min(k + size, len(lst)) - 1][1]))
    L = ["# 🎧 Tạo playlist từ các bài hát chứa từ TOEIC\n",
         "> %d bài hát (đã bỏ trùng) từ trang [🎤 Từ vựng TOEIC trong lời bài hát](toeic-songs-lyrics.md), chia mỗi file %d bài, "
         "theo đúng thứ tự từ vựng trên trang (phần ETS: từ hay gặp trước).\n" % (len(songs), size),
         "## Cách tạo playlist (Spotify / YouTube Music / Apple Music)\n",
         "1. Mở một file bên dưới, **chọn hết và copy** (mỗi dòng: `Ca sĩ - Tên bài`).",
         "2. Vào [tunemymusic.com](https://www.tunemymusic.com/) → chọn nguồn **Free text** → dán vào "
         "(hoặc [Soundiiz](https://soundiiz.com/) → *Import playlist* → *From text*).",
         "3. Chọn đích **Spotify / YouTube Music / Apple Music**, đăng nhập, bấm chuyển — công cụ tự tìm từng bài và tạo playlist.",
         "\n> Bản miễn phí thường giới hạn ~500 bài mỗi lần nên chia file 200 bài. Vài bài ít phổ biến có thể không tìm thấy.\n",
         "## Các file\n", "| Danh sách | Bài | Từ vựng (từ … đến) | File |", "|---|---|---|---|"]
    for label, a, b, name, t1, t2 in files:
        L.append("| %s | %d–%d | %s … %s | [%s](toeic-songs-playlist/%s ':ignore') |" % (label, a, b, md_esc(t1), md_esc(t2), name, name))
    open(os.path.join(DOCS, "toeic-songs-playlist.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("playlist:", len(songs), "bai,", len(files), "file")


if __name__ == "__main__":
    sys.exit(main())
