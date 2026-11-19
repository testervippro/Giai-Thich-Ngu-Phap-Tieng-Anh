#!/usr/bin/env python3
"""Cụm giao tiếp hay dùng nhất trong từng phim (Friends, The Office, Silicon Valley, Suits LA, phim lẻ).

Cách làm: cắt phụ đề thành từng vế câu (theo . ! ? , ;), đếm các cụm 2–7 từ; cụm được coi là
"cụm giao tiếp" khi hay được nói thành một câu trọn ("I don't know.", "Come on!") hoặc hay mở đầu câu
("I can't believe…", "Why don't you…"). Danh sách ứng viên đã được duyệt tay + dịch nghĩa trong
tools/data/movie_phrases_vi.tsv — chỉ cụm có trong file này mới được liệt kê (lọc tên nhân vật, cụm cụt).

Lên web : docs/movie-viewer/cum-giao-tiep.html — mỗi phim một tab, cụm xếp theo % số tập có cụm đó,
          kèm nghĩa + 1 câu thoại ngắn làm ví dụ.
Trên máy: phụ đề định dạng (movies/_study) gạch chân xanh các cụm này — xem tools/movie_subs_study.py.

    python3 tools/movie_phrases.py           # trang web
    python3 tools/movie_subs_study.py        # phụ đề trên máy (tô từ TOEIC + cụm giao tiếp)
"""
import json
import os
import re
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
GLOSS = os.path.join(HERE, "data", "movie_phrases_vi.tsv")
GROUPS = {"chao": "Chào hỏi / tạm biệt", "camxuc": "Cảm xúc / cảm thán", "phanung": "Phản hồi / đồng ý / từ chối",
          "hoi": "Câu hỏi hay gặp", "yeucau": "Yêu cầu / rủ / khuyên", "noi": "Mở lời / nối ý", "an": "Cảm ơn / xin lỗi / an ủi"}
SENT = re.compile(r"[^.!?…]+[.!?…]*")
TOK = re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)*")
NORM = {"alright": "all right", "ok": "okay", "'kay": "okay"}


def load_gloss():
    """-> {cụm: (nghĩa, nhóm)} theo thứ tự trong file."""
    g = {}
    for l in open(GLOSS, encoding="utf-8"):
        if l.startswith("#") or not l.strip():
            continue
        p = l.rstrip("\n").split("\t")
        g.setdefault(p[0].strip(), (p[1].strip() if len(p) > 1 else "", p[2].strip() if len(p) > 2 else "noi"))
    return g


def display(ph):
    """'oh my god' -> 'Oh my God' ; 'i don't know' -> 'I don't know'."""
    if ph == "my god":
        return "(Oh) my God"
    ws = ph.split()
    ws = [{"i": "I", "i'm": "I'm", "i'll": "I'll", "i've": "I've", "i'd": "I'd", "god": "God", "jesus": "Jesus",
           "christ": "Christ"}.get(w, w) for w in ws]
    return ws[0][:1].upper() + ws[0][1:] + ("" if len(ws) == 1 else " " + " ".join(ws[1:]))


def phrase_rx(ph):
    """Regex tìm cụm trong câu gốc: chịu 'alright'/'all right', 'ok'/'okay', dấu phẩy chen giữa không tính."""
    parts = []
    for w in ph.split():
        if w == "okay":
            parts.append(r"(?:okay|ok)")
        else:
            parts.append(re.escape(w).replace("'", "['’]"))
    body = r"\s+".join(parts).replace(r"all\s+right", r"(?:all\s+right|alright)")
    return re.compile(r"(?<![A-Za-z'])%s(?![A-Za-z'])" % body, re.I)


def chunks(line):
    for s in SENT.findall(line):
        for c in re.split(r"[,;:—]| -- ", s):
            ws = " ".join(NORM.get(w.lower(), w.lower()) for w in TOK.findall(c)).split()
            if ws:
                yield ws


def count(eps, gloss):
    """-> {nhóm phim: {cụm: dict(df, tf, ex=(ep_i, giây, dòng))}}"""
    maxn = max(len(p.split()) for p in gloss)
    groups = defaultdict(list)
    for ei, e in enumerate(eps):
        groups[group_name(e)].append(ei)
    res = {}
    for g, eis in groups.items():
        st = defaultdict(lambda: dict(df=0, tf=0, ex=None, sc=1e9))
        for ei in eis:
            seen = set()
            for t, line in eps[ei]["lines"]:
                for ws in chunks(line):
                    for n in range(3, min(maxn, len(ws)) + 1):
                        for i in range(len(ws) - n + 1):
                            ph = " ".join(ws[i:i + n])
                            if ph not in gloss:
                                continue
                            s = st[ph]
                            s["tf"] += 1
                            seen.add(ph)
                            sc = ex_score(line)
                            if sc < s["sc"]:
                                s["sc"], s["ex"] = sc, (ei, t, line)
            for ph in seen:
                st[ph]["df"] += 1
        res[g] = st
    return res


def group_name(e):
    return e["show"] if not e["show"].startswith("Phim") else e["title"]


def ex_score(line):
    """Câu ví dụ tốt: câu trọn (viết hoa đầu, dấu câu cuối), dài 25–70 ký tự. Nhỏ hơn = tốt hơn."""
    sc = abs(len(line) - 45) / 10
    if not (line[:1].isupper() and line.rstrip('"\'')[-1:] in ".!?"):
        sc += 5
    if len(line) > 110:
        sc += 10
    return sc


# ---------------- toàn bộ từ của từng phim ----------------
def load_vi():
    """Nghĩa tiếng Việt: file tự soạn > DK Illustrated Dictionary > TOEIC index. -> ({từ: nghĩa}, {tên riêng})"""
    vi, names = {}, set()
    for l in open(os.path.join(HERE, "data", "en_vi_movie_words.tsv"), encoding="utf-8"):
        if l.startswith("#") or "\t" not in l:
            continue
        w, m = l.rstrip("\n").split("\t", 1)
        if m == "=tên":
            names.add(w)
        else:
            vi.setdefault(w, m)
    s = open(os.path.join(ROOT, "docs", "tools", "vocab-3d-data.js"), encoding="utf-8").read()
    for r in json.JSONDecoder().raw_decode(s[s.index("{"):])[0]["words"]:
        for w in r[0].split(","):
            vi.setdefault(w.strip().lower(), r[2])
    for l in open(os.path.join(ROOT, "docs", "toeic-vocabulary-index.md"), encoding="utf-8"):
        m = re.match(r"\| \d+ \| ([^|]+) \| ([^|]+) \|", l)
        if m:
            vi.setdefault(m.group(1).strip().lower(), "; ".join(m.group(2).strip().split(";")[:2]))
    return vi, names


_LEM = {}
IRREG = {"is": "be", "am": "be", "are": "be", "was": "be", "were": "be", "been": "be", "being": "be", "saw": "see", "has": "have", "had": "have", "does": "do", "did": "do", "went": "go", "gone": "go",
         "men": "man", "women": "woman", "children": "child", "people": "people", "better": "better", "best": "best"}
KEEP = set("""as its us his this yes always perhaps sometimes news means clothes glasses pants thanks guys
species series physics politics jeans scissors"""
           .split()) | {"morning", "evening", "nothing", "something", "anything", "everything", "wedding", "building",
                        "feeling", "meeting", "during", "excited", "interested", "married", "tired", "bored", "boring",
                        "scared", "surprised", "worried", "confused", "embarrassed", "amazing", "interesting", "exciting",
                        "missing", "darling", "ceiling", "beginning", "kidding", "fucking", "freaking", "supposed",
                        "used", "red", "bed", "need", "speed", "seed", "feed", "weed", "bring", "king", "ring",
                        "sing", "thing", "spring", "string", "swing", "wing", "ceiling", "sibling", "pudding"}


def lemma(w, vi):
    """went -> go, apologizing -> apologize, clothes -> clothes (WordNet; giữ nguyên dạng có trong từ điển)."""
    if w in _LEM:
        return _LEM[w]
    r = IRREG.get(w, w)
    if r == w and "'" not in w and w not in KEEP and not w.endswith(("ss", "us", "is")) and (w not in vi or w.endswith(("s", "ed", "ing"))):
        from nltk.stem import WordNetLemmatizer
        from nltk.corpus import wordnet as wn
        L = _LEM.setdefault("__L", WordNetLemmatizer())
        order = "nva" if w.endswith("s") else "vna"
        cands = [L.lemmatize(w, p) for p in order]
        cands = [c for c in cands if c != w]
        good = [c for c in cands if c in vi] or [c for c in cands if wn.synsets(c)]
        if w in vi and w.endswith("s") and not w.endswith(("ed", "ing")):
            good = [c for c in good if c in vi]  # danh từ số nhiều: chỉ gộp khi số ít cũng có trong từ điển
        if good:
            r = good[0]
    _LEM[w] = r
    return r


def show_words(eps_g, vi, names):
    """-> rows [từ gốc, 'dạng khác', số lần, số tập, nghĩa, loại] ; loại: '' | 'ten' (tên riêng)"""
    tf, df, forms, cap = defaultdict(int), defaultdict(int), defaultdict(lambda: defaultdict(int)), defaultdict(int)
    for e in eps_g:
        seen = set()
        for _, line in e["lines"]:
            for m in TOK.finditer(line):
                raw = m.group(0)
                w = raw.lower().replace("’", "'")
                if len(w) == 1 and w not in "ai":
                    continue
                lm = lemma(w, vi)
                tf[lm] += 1
                forms[lm][w] += 1
                seen.add(lm)
                if raw[0].isupper() and w != "i" and m.start() > 0 and not re.search(r"[.!?\"\-♪]\s*$", line[:m.start()]):
                    cap[lm] += 1
        for lm in seen:
            df[lm] += 1
    rows = []
    for lm, n in tf.items():
        name = lm in names or (lm not in vi and cap[lm] >= max(1, 0.6 * n))
        fs = [f for f, _ in sorted(forms[lm].items(), key=lambda x: -x[1]) if f != lm][:5]
        rows.append([lm, ", ".join(fs), n, df[lm], "" if name else vi.get(lm, ""), "ten" if name else ""])
    rows.sort(key=lambda r: (-r[2], r[0]))
    return rows


# ---------------- 700 câu nói hàng ngày (docs/daily-native-expressions.md) dò qua mọi phim ----------------
DAILY_MD = os.path.join(ROOT, "docs", "daily-native-expressions.md")


def daily_norm(text):
    """'brb (be right back)' -> 'be right back' ; 'Would you mind...?' -> 'would you mind' ; 'Wow, really?' -> 'wow really'."""
    m = re.match(r"^\s*[a-z]{2,5}\s*\(([^)]+)\)\s*$", text)
    if m:
        text = m.group(1)
    text = re.sub(r"\([^)]*\)", " ", text)
    return " ".join(NORM.get(w, w) for w in (x.lower().replace("’", "'") for x in TOK.findall(text)))


def daily_rows(eps, shows):
    """-> rows [số thứ tự, câu, nghĩa, [nhóm], tổng số lần, [[phim, số lần]], câu ví dụ, nguồn] — đã gộp câu trùng."""
    items, by = [], {}
    sec = ""
    for l in open(DAILY_MD, encoding="utf-8"):
        m = re.match(r"## \d+\. (.*)", l)
        if m:
            sec = m.group(1).strip()
            continue
        m = re.match(r"\| (\d+) \| ([^|]+) \| ([^|]+) \|", l)
        if not m:
            continue
        key = daily_norm(m.group(2))
        if not key:
            continue
        if key in by:  # câu trùng (cùng chữ, khác dấu câu/nhóm) -> gộp
            it = by[key]
            if sec not in it["secs"]:
                it["secs"].append(sec)
            continue
        it = by[key] = dict(n=int(m.group(1)), text=m.group(2).strip(), mean=m.group(3).strip(), secs=[sec],
                            tf=defaultdict(int), ex=None, sc=1e9)
        items.append(it)
    multi = {k for k in by if len(k.split()) >= 3}
    short = {k for k in by if len(k.split()) <= 2}
    filler = {"oh", "well", "yeah", "okay", "uh", "um", "so", "and", "but", "hey", "no", "yes", "ah", "oh"}
    maxn = max(len(k.split()) for k in by)
    for ei, e in enumerate(eps):
        g = group_name(e)
        for t, line in e["lines"]:
            ws = [NORM.get(w, w) for w in (x.lower().replace("’", "'") for x in TOK.findall(line))]
            ws = " ".join(ws).split()
            hit = set()
            for n in range(3, min(maxn, len(ws)) + 1):
                for i in range(len(ws) - n + 1):
                    k = " ".join(ws[i:i + n])
                    if k in multi:
                        hit.add(k)
            # câu 1–2 từ ("Deal", "Got it", "Hold on"): chỉ tính khi được nói thành nguyên một vế câu
            # (bỏ qua "oh/well/yeah…" đứng trước) — tránh đếm nhầm "Ross got it for me", "hold on to it"
            for c in chunks(line):
                while len(c) > 1 and c[0] in filler and " ".join(c) not in short:
                    c = c[1:]
                if len(c) <= 2 and " ".join(c) in short:
                    hit.add(" ".join(c))
            for k in hit:
                it = by[k]
                it["tf"][g] += 1
                sc = ex_score(line)
                if sc < it["sc"]:
                    it["sc"], it["ex"] = sc, (ei, t, line)
    order = {g: i for i, g in enumerate(shows)}
    rows = []
    for it in items:
        per = sorted(([order[g], n] for g, n in it["tf"].items()), key=lambda x: -x[1])
        ex, src = "", ""
        if it["ex"]:
            ei, t, line = it["ex"]
            e = eps[ei]
            ex = line[:140]
            src = "%s %s · %d:%02d" % (group_name(e), "S%02dE%02d" % (e["s"], e["e"]) if e["s"] else "", t // 60, t % 60)
            src = re.sub(r"\s+", " ", src)
        rows.append([it["n"], it["text"], it["mean"], it["secs"], sum(it["tf"].values()), per, ex, src])
    return rows


def all_rows(data):
    """Gộp cụm giao tiếp của mọi phim + 700 câu hàng ngày, bỏ trùng.
    -> rows [thứ tự, cụm, nghĩa, [nhóm], tổng số lần, [[phim, số lần]], câu ví dụ, nguồn, 'p'|'d'|'pd']"""
    by, order = {}, []
    for si, sh in enumerate(data["shows"]):
        for ph, mean, grp, df, tf, line, src in sh["rows"]:
            k = daily_norm(ph)
            it = by.get(k)
            if not it:
                it = by[k] = dict(ph=ph, mean=mean, secs=[data["groups"].get(grp, "")], per={}, ex="", src="", best=-1, tag="p")
                order.append(k)
            it["per"][si] = it["per"].get(si, 0) + tf
            if tf > it["best"]:
                it["best"], it["ex"] = tf, line
                it["src"] = sh["name"] + " " + src if sh["series"] else sh["name"] + " " + src.replace("lúc ", "")
    for no, ph, mean, secs, tf, per, line, src in data["daily"]:
        k = daily_norm(ph)
        it = by.get(k)
        if it:
            it["tag"] = "pd"
            it["secs"] += [x for x in secs if x not in it["secs"]]
            continue
        by[k] = dict(ph=ph, mean=mean, secs=list(secs), per=dict(per), ex=line, src=src, tag="d")
        order.append(k)
    rows = []
    for k in order:
        it = by[k]
        per = sorted(([i, n] for i, n in it["per"].items()), key=lambda x: -x[1])
        rows.append([0, it["ph"], it["mean"], it["secs"], sum(n for _, n in per), per, it["ex"], it["src"], it["tag"]])
    rows.sort(key=lambda r: -r[4])
    for i, r in enumerate(rows, 1):
        r[0] = i
    return rows


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:40]


def main():
    sys.path.insert(0, HERE)
    import movie_subs_study as M
    gloss = load_gloss()
    eps = M.load_episodes()
    res = count(eps, gloss)
    shows = sorted(res, key=lambda g: (g not in M.SHOW_NAMES.values(), -sum(1 for e in eps if group_name(e) == g)))
    data = dict(groups=GROUPS, shows=[])
    vi, names = load_vi()
    wdir = os.path.join(ROOT, "docs", "movie-viewer", "tu")
    os.makedirs(wdir, exist_ok=True)
    for g in shows:
        n_eps = sum(1 for e in eps if group_name(e) == g)
        series = n_eps >= 5
        wrows = show_words([e for e in eps if group_name(e) == g], vi, names)
        wfile = slug(g) + ".json"
        json.dump(wrows, open(os.path.join(wdir, wfile), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
        nw = sum(1 for r in wrows if r[5] != "ten")
        nvi = sum(1 for r in wrows if r[5] != "ten" and r[4])
        rows = []
        for ph, s in res[g].items():
            if series and s["df"] < 2:  # phim bộ: cụm có từ 2 tập; phim lẻ: mọi cụm có trong phim
                continue
            ei, t, line = s["ex"]
            rows.append([display(ph), gloss[ph][0], gloss[ph][1], s["df"], s["tf"], line[:140],
                         "%s · %d:%02d" % (M.code(eps[ei]) if series else "lúc", t // 60, t % 60)])
        rows.sort(key=lambda r: (-r[3], -r[4]) if series else (-r[4],))
        data["shows"].append(dict(name=g, eps=n_eps, series=series, rows=rows, words=wfile, nw=nw, nvi=nvi))
        print("%-45s %3d tap  %4d cum  %5d tu (%d co nghia)" % (g[:45], n_eps, len(rows), nw, nvi))
    data["daily"] = daily_rows(eps, shows)
    nd = sum(1 for r in data["daily"] if r[4])
    print("700 cau hang ngay: %d cau (sau khi bo trung), %d cau co trong phim" % (len(data["daily"]), nd))
    data["all"] = all_rows(data)
    print("tat ca cum (phim + 700 cau, bo trung): %d" % len(data["all"]))
    tpl = open(os.path.join(HERE, "movie_phrases_template.html"), encoding="utf-8").read()
    out = os.path.join(ROOT, "docs", "movie-viewer", "cum-giao-tiep.html")
    open(out, "w", encoding="utf-8").write(tpl.replace("/*DATA*/null", json.dumps(data, ensure_ascii=False, separators=(",", ":"))))
    print("web:", out, os.path.getsize(out) // 1024, "KB")


if __name__ == "__main__":
    sys.exit(main())
