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
                    for n in range(2, min(maxn, len(ws)) + 1):
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


def main():
    sys.path.insert(0, HERE)
    import movie_subs_study as M
    gloss = load_gloss()
    eps = M.load_episodes()
    res = count(eps, gloss)
    shows = sorted(res, key=lambda g: (g not in M.SHOW_NAMES.values(), -sum(1 for e in eps if group_name(e) == g)))
    data = dict(groups=GROUPS, shows=[])
    for g in shows:
        n_eps = sum(1 for e in eps if group_name(e) == g)
        series = n_eps >= 5
        rows = []
        for ph, s in res[g].items():
            if (series and s["df"] < 2) or (not series and s["tf"] < 2):
                continue
            ei, t, line = s["ex"]
            rows.append([display(ph), gloss[ph][0], gloss[ph][1], s["df"], s["tf"], line[:140],
                         "%s · %d:%02d" % (M.code(eps[ei]) if series else "lúc", t // 60, t % 60)])
        rows.sort(key=lambda r: (-r[3], -r[4]) if series else (-r[4],))
        data["shows"].append(dict(name=g, eps=n_eps, series=series, rows=rows))
        print("%-45s %3d tap  %4d cum" % (g[:45], n_eps, len(rows)))
    tpl = open(os.path.join(HERE, "movie_phrases_template.html"), encoding="utf-8").read()
    out = os.path.join(ROOT, "docs", "movie-viewer", "cum-giao-tiep.html")
    open(out, "w", encoding="utf-8").write(tpl.replace("/*DATA*/null", json.dumps(data, ensure_ascii=False, separators=(",", ":"))))
    print("web:", out, os.path.getsize(out) // 1024, "KB")


if __name__ == "__main__":
    sys.exit(main())
