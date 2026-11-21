#!/usr/bin/env python3
"""Ngữ pháp trong lời bài hát (LRCLIB): mỗi mẫu ngữ pháp của 19 chương (trang Xem Tất Cả) kèm
câu hát thật có chứa mẫu đó.

Cần chạy trước: tools/song_grammar_pool.py (phân tích spaCy kho lời LRCLIB -> build/song_grammar/).
Danh sách mẫu: tools/song_grammar_patterns.py.

Ra: chèn/thay mục "🎵 NGỮ PHÁP TRONG LỜI BÀI HÁT" ở cuối từng file chương trong docs/
(giữa 2 dấu <!-- song-grammar:start --> … <!-- song-grammar:end -->).

Chạy: ~/Ielts-Reading/.venv-nlp/bin/python tools/song_grammar.py [--dry]
"""
import glob
import gzip
import heapq
import json
import math
import os
import pickle
import re
import sys
import zlib
from collections import Counter, defaultdict
from multiprocessing import Pool
from urllib.parse import quote_plus

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import song_grammar_patterns as SP  # noqa: E402

DOCS = os.path.join(ROOT, "docs")
POOL = os.path.join(ROOT, "build/song_grammar")
CORPUS = os.path.join(HERE, "data/lrclib_corpus.jsonl.gz")
EX = 3          # số câu hát mỗi mẫu
TOPK = 60       # số ứng viên giữ lại mỗi mẫu mỗi khối
SLANG = re.compile(r"\b(finna|tryna|i'ma|ima|imma|yo|ya|u|ur|cuz|da|dat|dem|dis|tek|weh|b-|gat|homie|y'all|ain't no|nothin'|em|'em|wit|thang|lil|ho|gon|gotta|wanna|gonna)\b|\b\w+in'\b", re.I)
START, END = "<!-- song-grammar:start -->", "<!-- song-grammar:end -->"

BAD = re.compile(r"(fuck|shit|bitch|nigg|pussy|\bdick|\bcock|cunt|whore|\bhoes?\b|slut|\bass\b|asshole|"
                 r"\bcum\b|\bsex|\bporn|\bdrugs?\b|cocaine|\bweed\b|\bkill (you|her|him|them)|\bhoe\b|\bthot)", re.I)


# ---------------------------------------------------------------- danh sách mẫu phẳng
def flat_patterns():
    out = []
    for ch in SP.ORDER:
        for gi, (group, items) in enumerate(SP.CHAPTERS[ch]):
            for title, spec in items:
                out.append((ch, gi, group, title, spec))
    return out


# ---------------------------------------------------------------- DSL -> spaCy Matcher
def _vals(s):
    return s.split("|")


def tok_pattern(tok):
    op = None
    if tok[:1] in "?*+" and len(tok) > 1:
        op, tok = tok[0], tok[1:]
    elif tok[-1:] in "?*+" and len(tok) > 1 and not tok.startswith("~") and not tok.startswith("@~"):
        op, tok = tok[-1], tok[:-1]
    d = {}
    if tok != ".":
        for part in tok.split("&"):
            neg = part.startswith("!")
            if neg:
                part = part[1:]
            if part.startswith("@~"):
                key, val = "LEMMA", {"REGEX": "^(%s)$" % part[2:]}
            elif part.startswith("~"):
                rx = part[1:]
                key, val = "LOWER", {"REGEX": ("^(?!(%s)$).*$" % rx) if neg else ("^(%s)$" % rx)}
                neg = False
            elif part.startswith("@"):
                key, val = "LEMMA", _vals(part[1:])
            elif part.startswith("#"):
                key, val = "TAG", _vals(part[1:])
            elif part.startswith("$"):
                key, val = "POS", _vals(part[1:])
            elif part.startswith("%"):
                key, val = "DEP", _vals(part[1:])
            else:
                key, val = "LOWER", _vals(part)
            if isinstance(val, list):
                val = {"NOT_IN" if neg else "IN": val}
            elif neg:
                raise ValueError(part)
            cur = d.setdefault(key, {})
            for k, v in val.items():
                if k == "REGEX" and "REGEX" in cur:      # 2 regex cùng thuộc tính -> ghép bằng lookahead
                    cur["REGEX"] = "(?=%s)%s" % (cur["REGEX"], v)
                else:
                    cur[k] = v
    if op:
        d["OP"] = op
    return d


def compile_dsl(s):
    toks = s.split()
    a_start = toks[0].startswith("<") and len(toks[0]) > 1 or toks[0] == "<"
    if toks[0] == "<":
        toks = toks[1:]
    elif toks[0].startswith("<"):
        toks[0] = toks[0][1:]
    a_end = toks[-1] == ">"
    if a_end:
        toks = toks[:-1]
    return [tok_pattern(t) for t in toks], a_start, a_end


# ---------------------------------------------------------------- worker
G = {}


def label_rx(label):
    if "%s" in label:
        return re.compile("^" + ".+?".join(re.escape(p) for p in label.split("%s")))
    return re.compile("^" + re.escape(label))


def init_worker(pats, pop):
    import spacy
    from spacy.matcher import Matcher
    nlp = spacy.load("en_core_web_sm", disable=["ner"])
    G["nlp"] = nlp
    G["pop"] = pop
    matcher = Matcher(nlp.vocab)
    anchors = {}
    regexes, tagspecs, funcs = [], [], []
    for pid, (ch, gi, group, title, spec) in enumerate(pats):
        specs = spec if isinstance(spec, list) else [spec]
        for si, sp in enumerate(specs):
            key = "%d.%d" % (pid, si)
            filt = None
            if isinstance(sp, tuple):
                _, sp, filt = sp
            entry = (pid, key, filt)
            if sp.startswith("re:"):
                regexes.append((entry, re.compile(sp[3:], re.I)))
            elif sp.startswith("tg:"):
                tagspecs.append((entry, label_rx(sp[3:])))
            elif sp.startswith("fn:"):
                funcs.append((entry, SP.FUNCS[sp[3:]]))
            else:
                p, a1, a2 = compile_dsl(sp)
                matcher.add(key, [p])
                anchors[key] = (a1, a2, entry)
    G.update(matcher=matcher, anchors=anchors, regexes=regexes, tagspecs=tagspecs, funcs=funcs)
    from ielts_ngu_phap import Tagger
    G["tagger"] = Tagger(nlp)
    # bộ lọc phụ (spec2 của "and") — biên dịch riêng
    filt_m = Matcher(nlp.vocab)
    G["filt"] = {}
    for pid, (ch, gi, group, title, spec) in enumerate(pats):
        for sp in (spec if isinstance(spec, list) else [spec]):
            if isinstance(sp, tuple):
                f = sp[2]
                if f.startswith("re:"):
                    G["filt"][f] = ("re", re.compile(f[3:], re.I))
                elif f.startswith("tg:"):
                    G["filt"][f] = ("tg", label_rx(f[3:]))
                else:
                    p, _, _ = compile_dsl(f)
                    filt_m.add(f, [p])
                    G["filt"][f] = ("m", f)
    G["filt_m"] = filt_m


def edge_ok(doc, i, j, a1, a2):
    if a1 and any(not (t.is_punct or t.pos_ == "INTJ") for t in doc[:i]):
        return False
    if a2 and any(not (t.is_punct or t.pos_ == "INTJ") for t in doc[j:]):
        return False
    return True


def score_line(text, s, e, meta):
    w = text.split()
    n = len(w)
    if BAD.search(text) or "[" in text or "(" in text and n < 6:
        return None
    low = [x.lower().strip(",.!?") for x in w]
    if len(set(low)) / n < 0.7:
        return None
    sc = -abs(n - 9) * 0.35
    sc += math.log(G["pop"].get(meta["a"], 1) + 1) * 0.9
    if (e - s) > 0.85 * len(text):
        sc -= 0.8
    if text[:1].isupper():
        sc += 0.3
    if re.search(r"\b(oh|ooh|yeah|la|na|hey|uh|woah|whoa|baby)\b", text, re.I):
        sc -= 0.4
    if SLANG.search(text):
        sc -= 2.5
    if BAD.search(meta.get("t", "")) or re.search(r"\d{2}-\d{2}|[\x00-\x1f]", meta.get("t", "")):
        return None
    sc += (zlib.crc32(text.encode()) % 1000) / 1000 * 1.2
    return sc


def work(path):
    from spacy.tokens import DocBin
    nlp = G["nlp"]
    no = int(re.search(r"pool-(\d+)", path).group(1))
    metas = G["metas_all"][no]
    docs = list(DocBin().from_disk(path).get_docs(nlp.vocab))
    counts = Counter()
    heaps = defaultdict(list)
    matcher, anchors = G["matcher"], G["anchors"]
    tagger = G["tagger"]
    need_tags = bool(G["tagspecs"]) or any(v[0] == "tg" for v in G["filt"].values())
    for li, doc in enumerate(docs):
        text = doc.text
        hits = {}     # pid -> (s, e)

        tags = None

        def get_tags():
            nonlocal tags
            if tags is None:
                try:
                    tags = tagger.tags(doc[:]) if need_tags else []
                except Exception:
                    tags = []
            return tags

        fm = None

        def filt_ok(f):
            nonlocal fm
            if f is None:
                return True
            kind, obj = G["filt"][f]
            if kind == "re":
                return bool(obj.search(text))
            if kind == "tg":
                return any(obj.search(lb) for _, lb, _, _ in get_tags())
            if fm is None:
                fm = {nlp.vocab.strings[m] for m, _, _ in G["filt_m"](doc)}
            return obj in fm

        def put(pid, s, e):
            if pid not in hits or (e - s) > (hits[pid][1] - hits[pid][0]):
                hits[pid] = (s, e)

        for mid, i, j in matcher(doc):
            key = nlp.vocab.strings[mid]
            a1, a2, (pid, _, filt) = anchors[key]
            if edge_ok(doc, i, j, a1, a2) and filt_ok(filt):
                put(pid, doc[i].idx, doc[j - 1].idx + len(doc[j - 1].text))
        for (pid, _, filt), rx in G["regexes"]:
            m = rx.search(text)
            if m and filt_ok(filt):
                put(pid, m.start(), m.end())
        for (pid, _, filt), fn in G["funcs"]:
            r = fn(doc)
            if r and filt_ok(filt):
                put(pid, r[0], r[1])
        if G["tagspecs"]:
            tg = get_tags()
            if tg:
                for (pid, _, filt), rx in G["tagspecs"]:
                    for _, lb, s, e in tg:
                        if rx.search(lb) and filt_ok(filt):
                            put(pid, s, e)
                            break
        if not hits:
            continue
        meta = metas[li]
        for pid, (s, e) in hits.items():
            counts[pid] += 1
            sc = score_line(text, s, e, meta)
            if sc is None:
                continue
            h = heaps[pid]
            item = (sc, li + no * 1_000_000, text, s, e, meta["id"], meta["t"], meta["a"])
            if len(h) < TOPK:
                heapq.heappush(h, item)
            elif item > h[0]:
                heapq.heapreplace(h, item)
    return counts, dict(heaps)


def init_all(pats, pop, metas_all):
    init_worker(pats, pop)
    G["metas_all"] = metas_all


def raw_fallback(pats, counts, cands, pop):
    """Mẫu (dạng regex) còn ít ứng viên: dò thêm trên mọi dòng lời gốc, kể cả dòng ngắn/trùng."""
    G["pop"] = pop
    weak = {}
    for pid, p in enumerate(pats):
        if len(cands.get(pid, [])) >= 2 * EX:
            continue
        specs = p[4] if isinstance(p[4], list) else [p[4]]
        rxs = [re.compile(sp[3:], re.I) for sp in specs if isinstance(sp, str) and sp.startswith("re:")]
        if rxs:
            weak[pid] = rxs
    if not weak:
        return
    print("dò bổ sung", len(weak), "mẫu trên lời gốc", flush=True)
    have = {pid: {it[2].lower() for it in cands.get(pid, [])} for pid in weak}
    key = 50_000_000
    for ln in gzip.open(CORPUS, "rt", encoding="utf-8"):
        d = json.loads(ln)
        for i, l in enumerate(d["l"].split("\n")):
            l = re.sub(r"\s+", " ", l.replace("’", "'")).strip()
            if len(l.split()) < 2 or not l.isascii():
                continue
            for pid, rxs in weak.items():
                for rx in rxs:
                    m = rx.search(l)
                    if m and l.lower() not in have[pid]:
                        have[pid].add(l.lower())
                        sc = score_line(l, m.start(), m.end(), {"a": d["a"], "t": d["t"]})
                        if sc is not None:
                            key += 1
                            cands.setdefault(pid, []).append((sc, key, l, m.start(), m.end(), d["id"], d["t"], d["a"]))
                            counts[pid] += 1
                        break


# ---------------------------------------------------------------- render
def esc(s):
    return re.sub(r"([\\*_\[\]<>|`#])", r"\\\1", s)


def render_line(text, s, e):
    while s > 0 and (text[s - 1].isalnum() or text[s - 1] == "'" and s > 1 and text[s - 2].isalnum()):
        s -= 1
    while e < len(text) and (text[e].isalnum() or text[e] == "'" and e + 1 < len(text) and text[e + 1].isalnum()):
        e += 1
    a, b, c = text[:s], text[s:e], text[e:]
    if not b.strip():
        return esc(text)
    lead = len(b) - len(b.lstrip())
    trail = len(b) - len(b.rstrip())
    a += b[:lead]
    c = b[len(b) - trail:] + c if trail else c
    b = b.strip()
    return esc(a) + "**" + esc(b) + "**" + esc(c)


def clean_title(t, a):
    t = re.sub(r"[\x00-\x1f]+", " ", t)
    for _ in range(2):
        if t.lower().startswith(a.lower() + " - "):
            t = t[len(a) + 3:]
        t = re.sub(r"^\d{1,2}(-\d{1,2})?\s+", "", t.strip())
    t = re.sub(r"\s*[\(\[][^\)\]]*(live|remaster|version|mix|video|demo|edit|mono|stereo|take|acoustic|bonus|session|instrumental)[^\)\]]*[\)\]]", "", t, flags=re.I)
    t = re.sub(r"\s+-\s+.*(live|remaster|version|mix|edit|mono|stereo|take|acoustic|bonus).*$", "", t, flags=re.I)
    return re.sub(r"\s+", " ", t).strip(" ;-")


def yt(t, a):
    return "https://www.youtube.com/results?search_query=" + quote_plus("%s %s" % (a, t))


def main():
    dry = "--dry" in sys.argv
    pats = flat_patterns()
    print(len(pats), "mẫu", flush=True)
    pop = Counter()
    for ln in gzip.open(CORPUS, "rt", encoding="utf-8"):
        a = json.loads(ln)["a"]
        if not re.search(r"various|unknown|soundtrack|cast|karaoke", a, re.I):
            pop[a] += 1
    metas = [json.loads(l) for l in open(os.path.join(POOL, "meta.jsonl"), encoding="utf-8")]
    files = sorted(glob.glob(os.path.join(POOL, "pool-*.spacy")))
    metas_all = {}
    for f in files:
        no = int(re.search(r"pool-(\d+)", f).group(1))
        metas_all[no] = metas[no * 100_000:(no + 1) * 100_000]
    cache = os.path.join(POOL, "scan.pkl")
    if "--render" in sys.argv:
        counts, cands = pickle.load(open(cache, "rb"))
    else:
        with Pool(min(7, len(files)), initializer=init_all, initargs=(pats, dict(pop), metas_all)) as pool:
            res = pool.map(work, files)
        counts = Counter()
        cands = defaultdict(list)
        for c, h in res:
            counts.update(c)
            for pid, items in h.items():
                cands[pid].extend(items)
        raw_fallback(pats, counts, cands, pop)
        pickle.dump((counts, cands), open(cache, "wb"))

    # ---- chọn câu: khác bài, khác ca sĩ, ưu tiên câu chưa dùng ở mẫu khác
    used = Counter()
    chosen = {}
    order = sorted(range(len(pats)), key=lambda p: counts[p])     # mẫu hiếm chọn trước
    for pid in order:
        items = sorted(cands.get(pid, []), reverse=True)
        pick, songs, arts = [], set(), set()
        for rnd in (0, 1):
            for it in items:
                if len(pick) >= EX:
                    break
                sc, key, text, s, e, sid, t, a = it
                if sid in songs or (rnd == 0 and (a in arts or used[key])):
                    continue
                if any(p[1] == key for p in pick):
                    continue
                pick.append(it)
                songs.add(sid)
                arts.add(a)
        for it in pick:
            used[it[1]] += 1
        chosen[pid] = pick

    # ---- link YouTube phát đúng đoạn (song_grammar_yt.py); --no-yt: chỉ link tìm kiếm
    ytl = {}
    if "--no-yt" not in sys.argv:
        import song_grammar_yt as SY
        yitems = [(it[5], clean_title(it[6], it[7]), it[7], it[2]) for pk in chosen.values() for it in pk]
        SY.links(yitems)
        SY.retry(yitems)
        ytl = SY.links(yitems)
        print("có mốc thời gian: %d/%d câu" % (len(ytl), sum(len(v) for v in chosen.values())), flush=True)

    # ---- ghi file
    stats = []
    by_ch = defaultdict(list)
    for pid, p in enumerate(pats):
        by_ch[p[0]].append(pid)
    for ch in SP.ORDER:
        fn = next(c[4] for c in CHAPTERS_META if c[0] == ch)
        name = next(c[1] for c in CHAPTERS_META if c[0] == ch)
        out = ["# 🎵 %s — ngữ pháp trong lời bài hát" % name, "",
               "> 📘 Lý thuyết: [%s](%s) · 🎵 [Tất cả chương (1 trang)](%s)" % (name, quote(fn), quote(ALL_FN)), ">",
               "> Mỗi mẫu ngữ pháp của chương (theo đúng thứ tự phần lý thuyết) kèm **câu hát thật** "
               "có chứa mẫu đó, lấy từ kho lời bài hát [LRCLIB](https://lrclib.net/) (~89.000 bài, 1,07 triệu dòng lời). "
               "Phần ngữ pháp được **in đậm**; con số cạnh mỗi mẫu là số dòng lời có mẫu đó. "
               "Bấm **▶ tên bài · phút:giây** để mở YouTube phát ngay đúng câu đó; bài không có ▶ là link tìm trên YouTube.",
               ">",
               "> ⚠️ Câu được máy dò tự động (spaCy + mẫu từ khóa) nên có thể sai khoảng 5–10%.", ""]
        cur_g = None
        gno = 0
        n_ok = n_all = 0
        for pid in by_ch[ch]:
            _, gi, group, title, _ = pats[pid]
            if gi != cur_g:
                cur_g = gi
                gno += 1
                out += ["", "## %d. %s" % (gno, group), ""]
            n_all += 1
            pick = chosen.get(pid, [])
            if pick:
                n_ok += 1
            out.append("**▸ %s** · %s dòng lời" % (esc(title), "{:,}".format(counts[pid]).replace(",", ".")))
            out.append("")
            if not pick:
                out.append("- _(chưa tìm thấy câu hát phù hợp trong kho lời)_")
            for sc, key, text, s, e, sid, t, a in pick:
                tt = clean_title(t, a)
                u = ytl.get((sid, text))
                if u:
                    sec = int(u.rsplit("=", 1)[1][:-1]) + 1
                    out.append("- 🎵 “%s” — [▶ %s · %s · %d:%02d](%s)" % (
                        render_line(text, s, e), esc(tt), esc(a), sec // 60, sec % 60, u))
                else:
                    out.append("- 🎵 “%s” — [%s · %s](%s)" % (render_line(text, s, e), esc(tt), esc(a), yt(tt, a)))
            out.append("")
        stats.append((ch, n_ok, n_all))
        sfn = song_fn(fn)
        if not dry:
            open(os.path.join(DOCS, sfn), "w", encoding="utf-8").write("\n".join(out).rstrip("\n") + "\n")
            # bỏ khối cũ (nếu có) khỏi file lý thuyết — mục bài hát giờ là trang riêng
            path = os.path.join(DOCS, fn)
            src = open(path, encoding="utf-8").read()
            if START in src:
                src = re.sub(r"\n*" + re.escape(START) + r".*?" + re.escape(END) + r"\n?", "\n", src, flags=re.S)
                open(path, "w", encoding="utf-8").write(src.rstrip("\n") + "\n")
    if not dry:
        all_md = ["# 🎵 NGỮ PHÁP TRONG LỜI BÀI HÁT — TẤT CẢ", "",
                  "> 19 chương, %d mẫu ngữ pháp, mỗi mẫu tối đa %d câu hát thật từ [LRCLIB](https://lrclib.net/). "
                  "Ctrl+F để tìm nhanh." % (len(pats), EX), ""]
        for ch in SP.ORDER:
            name, fn = next((c[1], c[4]) for c in CHAPTERS_META if c[0] == ch)
            all_md += ["[%s](%s ':include')" % (name.upper(), quote(song_fn(fn))), ""]
        open(os.path.join(DOCS, ALL_FN), "w", encoding="utf-8").write("\n".join(all_md))
    tot_ok = sum(s[1] for s in stats)
    tot = sum(s[2] for s in stats)
    for ch, a, b in stats:
        print("%-7s %3d/%3d mẫu có câu hát" % (ch, a, b))
    print("TỔNG %d/%d" % (tot_ok, tot))
    weak = [(pats[p][0], pats[p][3], counts[p], len(chosen.get(p, []))) for p in range(len(pats)) if len(chosen.get(p, [])) < EX]
    for w in weak:
        print("  THIẾU", w)
    json.dump({"%s|%s" % (pats[p][0], pats[p][3]): counts[p] for p in range(len(pats))},
              open(os.path.join(POOL, "counts.json"), "w"), ensure_ascii=False, indent=0)


CHAPTERS_META = [
    ("noun", "Danh Từ.md"), ("pron", "Đại Từ.md"), ("sva", "Sự Tương Tự Giữa Chủ Ngữ Và Động Từ.md"),
    ("adj", "Tính Từ.md"), ("adv", "Trạng Từ.md"), ("comp", "Các Phép So Sánh Của Tính Từ Và Trạng Từ.md"),
    ("verb", "Động Từ.md"), ("phr", "Cụm Động Từ.md"), ("pass", "Câu Bị Động.md"),
    ("inf", "Động Từ Nguyên Mẫu Và Danh Động Từ.md"), ("prep", "Giới Từ.md"), ("conj", "Liên Từ.md"),
    ("art", "Mạo Từ.md"), ("quant", "Lượng Từ.md"), ("tense", "TENSES.md"), ("clause", "Menh De.md"),
    ("sent", "SENTENCES.md"), ("seq", "SEQUENCE OF TENSES.md"), ("inv", "Đảo Ngữ.md"),
]
NAMES = {"noun": "Danh từ", "pron": "Đại từ", "sva": "Sự tương hợp giữa chủ ngữ và động từ", "adj": "Tính từ",
         "adv": "Trạng từ", "comp": "So sánh của tính từ và trạng từ", "verb": "Động từ", "phr": "Cụm động từ",
         "pass": "Câu bị động", "inf": "Động từ nguyên mẫu và danh động từ", "prep": "Giới từ", "conj": "Liên từ",
         "art": "Mạo từ", "quant": "Lượng từ", "tense": "Các thì", "clause": "Mệnh đề", "sent": "Câu",
         "seq": "Phối hợp thì", "inv": "Đảo ngữ"}
CHAPTERS_META = [(k, NAMES[k], None, None, f) for k, f in CHAPTERS_META]
ALL_FN = "song-grammar-all.md"


def song_fn(fn):
    return fn[:-3] + " (Bài hát).md"


def quote(fn):
    from urllib.parse import quote as q
    return q(fn)

if __name__ == "__main__":
    main()
