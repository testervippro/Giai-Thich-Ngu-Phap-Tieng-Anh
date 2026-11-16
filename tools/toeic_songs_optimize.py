#!/usr/bin/env python3
"""Rút gọn playlist: chọn ÍT bài hát nhất mà vẫn phủ hết các từ TOEIC đã tìm được (bài toán set cover, tham lam).

Một bài hát thường chứa nhiều từ TOEIC, nên thay vì 1–2 bài cho MỖI từ (~8.900 bài), mỗi lượt chọn bài
chứa nhiều từ CHƯA được phủ nhất. Cần lời đầy đủ → dùng kho lời tools/data/lrclib_corpus.jsonl.gz
(tạo bởi toeic_songs_corpus.py) + kết quả vòng 1 (tools/data/lrclib_cache.json) cho từ chỉ có ở đó.

Thứ tự: phủ từ ETS trước (từ hay gặp được ưu tiên), rồi từ chỉ có trong Hackers.
Ra: docs/toeic-songs-playlist.md (mỗi bài kèm các từ TOEIC có trong lời), docs/toeic-songs-playlist/*.txt,
và dựng lại docs/toeic-songs-lyrics*.md với bài trong playlist đứng đầu mỗi từ (ghi 🎧 #số bài).

    python3 tools/toeic_songs_optimize.py
"""
import gzip
import json
import math
import os
import re
import sys
import zlib
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import toeic_songs_lrclib as L  # noqa: E402
import toeic_songs_corpus as C  # noqa: E402

NCORPUS = [0]
TOK = re.compile(r"[a-z][a-z']*")
PLDIR = os.path.join(L.DOCS, "toeic-songs-playlist")


def read_corpus():
    rows, seen = [], set()
    try:
        with gzip.open(C.CORPUS, "rt", encoding="utf-8") as f:
            for line in f:
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                if r["id"] not in seen:
                    seen.add(r["id"])
                    rows.append(r)
    except (EOFError, OSError, zlib.error):
        pass  # kho đang được ghi dở: dùng phần đã đọc được
    return rows


def hit_line(v, q, corpus):
    """v là (dòng, dạng) hoặc chỉ số bài trong kho -> tìm lại dòng hát chứa từ."""
    if not isinstance(v, int):
        return v
    pl = corpus[v]["l"]
    exact = re.compile(r"(?<![A-Za-z'])%s(?![A-Za-z'])" % re.escape(q).replace(r"\ ", r"\s+"), re.I)
    m = exact.search(pl) or C.form_rx(q).search(pl)
    return (line_of(pl, m), m.group(0)) if m else ("", "")


def line_of(pl, m):
    s = pl.rfind("\n", 0, m.start()) + 1
    e = pl.find("\n", m.end())
    return pl[s:e if e >= 0 else len(pl)].strip()[:200]


def main():
    ets, idx = L.load_ets(), L.load_index()
    for r in ets + idx:
        r["q"] = L.query_of(r["term"])
    rows, dup = L.merged_rows(ets, idx)
    cache = json.load(open(L.CACHE, encoding="utf-8"))
    corpus = read_corpus()
    NCORPUS[0] = len(corpus)
    print("kho loi: %d bai" % len(corpus), flush=True)

    # ---- bài nào chứa từ nào ----
    songs = []  # dict(key, track, artist, es, hits={row_i: (line, word)})
    key2s = {}

    def song(track, artist, es):
        k = (artist.strip().lower(), re.sub(r"\s*[\(\[].*", "", track).strip().lower())
        if k not in key2s:
            key2s[k] = len(songs)
            songs.append(dict(key=k, track=track, artist=artist, es=es, hits={}))
        return songs[key2s[k]]

    # chỉ đánh chỉ mục các token có trong từ khoá (đỡ tốn RAM: kho 89k bài)
    def forms_of(ws, j, w):
        return C.variants(w) if (j in (0, len(ws) - 1) and len(w) >= 4) else {w}
    plain = lambda ws: all(re.fullmatch(r"[a-z][a-z']*", w) for w in ws)
    need_tok = set()
    for r in rows:
        ws = r["q"].split()
        if plain(ws):
            for j, w in enumerate(ws):
                need_tok |= forms_of(ws, j, w)
    index = defaultdict(list)  # token -> [corpus idx]
    for i, r in enumerate(corpus):
        for w in set(TOK.findall(r["l"].lower())) & need_tok:
            index[w].append(i)
    print("chi muc xong: %d token" % len(index), flush=True)
    es_cache = {}

    def es_of(ci):
        if ci not in es_cache:
            es_cache[ci] = L.english_score(corpus[ci]["l"])
        return es_cache[ci]

    allc = range(len(corpus))
    for ri, r in enumerate(rows):
        q = r["q"]
        ws = q.split()
        if not plain(ws):
            cand = allc
        else:
            cand = None
            for j, w in enumerate(ws):
                st = set()
                for f in forms_of(ws, j, w):
                    st.update(index.get(f, ()))
                cand = st if cand is None else cand & st
                if not cand:
                    break
        if not cand:
            continue
        exact = re.compile(r"(?<![A-Za-z'])%s(?![A-Za-z'])" % re.escape(q).replace(r"\ ", r"\s+"), re.I)
        rx = C.form_rx(q)
        for ci in cand:
            pl = corpus[ci]["l"]
            if exact.search(pl) or rx.search(pl):
                song(corpus[ci]["t"], corpus[ci]["a"], es_of(ci))["hits"][ri] = ci  # dòng hát tính sau
        if ri % 500 == 0:
            print("  do %d/%d tu, %d bai" % (ri, len(rows), len(songs)), flush=True)
    del index
    # bài từ vòng 1 (chỉ biết chứa đúng từ đó)
    for ri, r in enumerate(rows):
        for h in cache.get(r["q"]) or []:
            s = song(h["track"], h["artist"], h.get("es", 0.1))
            s["hits"].setdefault(ri, (h["line"], h.get("word") or ""))
    coverable = {ri for s in songs for ri in s["hits"]}
    print("%d bai ung vien, phu duoc %d/%d muc" % (len(songs), len(coverable), len(rows)), flush=True)

    # ---- tham lam: ETS trước (trọng số theo số lần trong đề), rồi Hackers ----
    def weight(ri):
        r = rows[ri]
        return 1.0 + math.log10(1 + int(r["ets"])) if r["ets"] else 1.0

    sel = min_cover(songs, coverable)
    # xếp thứ tự trong bộ đã chọn: mỗi lượt lấy bài có nhiều từ mới nhất (từ ETS nặng hơn) -> nghe từ hay gặp trước
    chosen, covered, left = [], set(), set(sel)
    while left:
        si = max(left, key=lambda j: (sum(weight(ri) for ri in songs[j]["hits"] if ri not in covered), songs[j]["es"]))
        left.discard(si)
        s = songs[si]
        new = sorted(ri for ri in s["hits"] if ri not in covered)
        covered |= set(new)
        has_ets = any(rows[ri]["ets"] for ri in new)
        chosen.append(dict(song=s, phase="ets" if has_ets else "hackers", new=new, all=sorted(s["hits"])))
    print("playlist toi uu: %d bai phu %d muc" % (len(chosen), len(covered)), flush=True)

    # ---- gán bài cho từng từ: bài trong playlist đứng đầu, rồi 1 bài khác ca sĩ ----
    first = {}
    for k, c in enumerate(chosen, 1):
        for ri in c["new"]:
            first[ri] = (k, c)
    cache2 = {}
    for ri, r in enumerate(rows):
        if ri not in first:
            continue
        k, c = first[ri]
        s = c["song"]
        line, word = hit_line(s["hits"][ri], rows[ri]["q"], corpus)
        hits = [dict(track=s["track"], artist=s["artist"], line=line, word=word, pl=k)]
        for h in cache.get(r["q"]) or []:
            if h["artist"].lower() != s["artist"].lower():
                hits.append(h)
                break
        cache2[r["q"]] = hits

    write_playlist(rows, chosen, len(coverable))
    L.render_merged(rows, cache2, dup, playlist_fn=lambda *_: None)


def fmt(n):
    return "{:,}".format(n).replace(",", ".")


def min_cover(songs, U):
    """Set cover: tham lam (không chia pha) -> bỏ bài thừa -> đổi 2 bài lấy 1 bài phủ đủ, lặp tới khi hết cải thiện."""
    import heapq
    S = [set(s["hits"]) & U for s in songs]
    inv = defaultdict(set)
    for j, st in enumerate(S):
        for w in st:
            inv[w].add(j)
    # 1) tham lam lười
    need, sel = set(U), set()
    heap = [(-len(st), -songs[j]["es"], j) for j, st in enumerate(S) if st]
    heapq.heapify(heap)
    while need and heap:
        sc, es, j = heapq.heappop(heap)
        cur = len(S[j] & need)
        if cur == 0:
            continue
        if heap and -cur > heap[0][0]:
            heapq.heappush(heap, (-cur, es, j))
            continue
        sel.add(j)
        need -= S[j]
    print("  tham lam: %d bai" % len(sel), flush=True)
    cnt = defaultdict(int)
    for j in sel:
        for w in S[j]:
            cnt[w] += 1

    def prune():
        for j in sorted(sel, key=lambda j: len(S[j])):
            if all(cnt[w] >= 2 for w in S[j]):
                sel.discard(j)
                for w in S[j]:
                    cnt[w] -= 1

    prune()
    print("  bo bai thua: %d bai" % len(sel), flush=True)
    # 2) đổi 2 -> 1
    improved = True
    while improved:
        improved = False
        owner = {}
        for j in sel:
            for w in S[j]:
                if cnt[w] == 1:
                    owner[w] = j
        uniq = defaultdict(set)
        for w, j in owner.items():
            uniq[j].add(w)
        for a in sorted(sel, key=lambda j: len(uniq[j])):
            if a not in sel or not uniq[a]:
                continue
            w0 = next(iter(uniq[a]))
            done = False
            for k in inv[w0]:
                if k in sel or not uniq[a] <= S[k]:
                    continue
                for b in {owner[w] for w in S[k] if w in owner} - {a}:
                    if b in sel and uniq[b] <= S[k]:
                        for j in (a, b):
                            sel.discard(j)
                            for w in S[j]:
                                cnt[w] -= 1
                        sel.add(k)
                        for w in S[k]:
                            cnt[w] += 1
                        done = improved = True
                        break
                if done:
                    break
            if done:
                break  # tính lại owner/uniq
        if improved:
            prune()
            if len(sel) % 10 == 0:
                print("  doi 2->1: %d bai" % len(sel), flush=True)
    assert all(cnt[w] >= 1 for w in U)
    print("  ket qua: %d bai" % len(sel), flush=True)
    return sel


def tiers(rows, chosen, total):
    n_ets_all = sum(1 for c in chosen for ri in c["new"] if rows[ri]["ets"])
    out, cum, ce = [], 0, 0
    marks = [m for m in (25, 50, 100, 200, 300, 500, 750, 1000, 1500, 2000) if m < len(chosen)] + [len(chosen)]
    for k, c in enumerate(chosen, 1):
        cum += len(c["new"])
        ce += sum(1 for ri in c["new"] if rows[ri]["ets"])
        if k in marks:
            out.append("| **%s bài** | %s | %d%% | %s/%s (%d%%) |" % (fmt(k), fmt(cum), round(100 * cum / max(1, total)),
                                                                  fmt(ce), fmt(n_ets_all), round(100 * ce / max(1, n_ets_all))))
    return out


def write_playlist(rows, chosen, total, size=200):
    os.makedirs(PLDIR, exist_ok=True)
    for f in os.listdir(PLDIR):
        if f.endswith(".txt"):
            os.remove(os.path.join(PLDIR, f))
    files = []
    for a in range(0, len(chosen), size):
        part = chosen[a:a + size]
        name = "toeic-playlist-%03d-%03d.txt" % (a + 1, a + len(part))
        open(os.path.join(PLDIR, name), "w", encoding="utf-8").write(
            "\n".join("%s - %s" % (c["song"]["artist"], c["song"]["track"]) for c in part) + "\n")
        files.append((a + 1, a + len(part), name, sum(len(c["new"]) for c in part)))
    n_ets = sum(1 for c in chosen if c["phase"] == "ets")
    E = L.md_esc
    out = ["# 🎧 Playlist TOEIC tối ưu — ít bài nhất, phủ hết từ\n",
           "> Một bài hát thường chứa nhiều từ TOEIC, nên playlist được tối ưu để có **ít bài nhất mà vẫn phủ mọi từ đã tìm được**: "
           "chọn bài phủ nhiều từ nhất, bỏ bài thừa, rồi thử đổi 2 bài lấy 1 bài phủ đủ cả hai (dò trong kho %s bài hát có lời). "
           "Kết quả **%s bài** phủ **%s mục** từ vựng (lúc đầu là ~8.900 bài). Thứ tự đã xếp để **từ hay gặp trong đề ETS được nghe trước**.\n>\n"
           "> Mỗi bài ghi **từ mới** (lần đầu gặp trong playlist, in đậm) và các từ TOEIC khác có trong lời. "
           "Xem câu hát chứa từ ở trang [🎤 Từ vựng TOEIC trong lời bài hát](toeic-songs-lyrics.md).\n"
           % (fmt(NCORPUS[0]), fmt(len(chosen)), fmt(total)),
           "## Nghe bao nhiêu bài thì phủ bao nhiêu từ?\n",
           "Danh sách đã xếp theo hiệu quả: các bài đầu chứa nhiều từ nhất. Không cần nghe hết — chọn một mức:\n",
           "| Nghe bài 1 → | Phủ (mục) | Tỉ lệ | Trong đó từ ETS |", "|---|---|---|---|"] + tiers(rows, chosen, total) + [
           "\n## Cách tạo playlist (Spotify / YouTube Music / Apple Music)\n",
           "1. Mở một file bên dưới, **chọn hết và copy** (mỗi dòng: `Ca sĩ - Tên bài`).",
           "2. Vào [tunemymusic.com](https://www.tunemymusic.com/) → nguồn **Free text** → dán vào "
           "(hoặc [Soundiiz](https://soundiiz.com/) → *Import playlist* → *From text*).",
           "3. Chọn đích **Spotify / YouTube Music / Apple Music**, đăng nhập, bấm chuyển — công cụ tự tìm từng bài.",
           "\n> Bản miễn phí thường giới hạn ~500 bài mỗi lần nên chia file %d bài. Vài bài ít phổ biến có thể không tìm thấy.\n" % size,
           "## Các file\n", "| Bài | Số từ mới phủ | File |", "|---|---|---|"]
    for a, b, name, nw in files:
        out.append("| %d–%d | %s | [%s](toeic-songs-playlist/%s ':ignore') |" % (a, b, fmt(nw), name, name))
    out += ["\n## Danh sách bài\n", "| # | Bài hát | Từ mới | Từ TOEIC khác trong lời | Nghe |", "|---|---|---|---|---|"]
    for k, c in enumerate(chosen, 1):
        s = c["song"]
        new = set(c["new"])
        nw = ", ".join("**%s**" % E(rows[ri]["term"]) for ri in c["new"])
        other = [rows[ri]["term"] for ri in c["all"] if ri not in new]
        ot = ", ".join(E(t) for t in other[:25]) + (" … (+%d)" % (len(other) - 25) if len(other) > 25 else "")
        qq = L.link_q("%s %s" % (s["artist"], s["track"]))
        out.append('| <a id="b%d"></a>%d | *%s* – %s | %s | %s | [Spotify](https://open.spotify.com/search/%s) · [YouTube](https://www.youtube.com/results?search_query=%s) |'
                   % (k, k, E(s["track"]), E(s["artist"]), nw, ot, qq, qq))
    open(os.path.join(L.DOCS, "toeic-songs-playlist.md"), "w", encoding="utf-8").write("\n".join(out) + "\n")
    print("playlist:", len(chosen), "bai,", len(files), "file")


if __name__ == "__main__":
    sys.exit(main())
