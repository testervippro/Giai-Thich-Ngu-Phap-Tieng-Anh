#!/usr/bin/env python3
"""Ngân hàng mẫu câu IELTS 9.0 — một danh sách duy nhất, dò từng mẫu qua phụ đề phim.

Đầu vào : tools/data/pattern_bank/*.tsv  (mẫu câu | nghĩa | ví dụ tự soạn | band | kỹ năng; dòng "# cat:" mở nhóm)
          phụ đề ~/remind voca/movies (Friends, The Office, Silicon Valley, Suits LA, phim lẻ) — xem movie_subs_study.py
Đầu ra  : docs/tools/pattern-bank-data.js  (trang docs/tools/pattern-bank.html đọc file này)

Mỗi mẫu được dò bằng phần chữ cố định dài nhất (bỏ chỗ trống …, V-ing, sb, (that)…); mẫu chỉ có 1 từ
("Absolutely.") chỉ tính khi được nói thành nguyên một vế câu. Trích 1 câu thoại ngắn làm ví dụ thật.

    python3 tools/pattern_bank.py
"""
import glob
import json
import os
import re
import sys
from collections import defaultdict, Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(HERE, "data", "pattern_bank")
OUT = os.path.join(ROOT, "docs", "tools", "pattern-bank-data.js")
sys.path.insert(0, HERE)

SLOT = re.compile(r"…|\.\.\.|\+|\b(?:V-ing|V3|V|sb|sth|S|X|Y|N|adj|adv|Adjective|comparative)\b")
ANY1 = re.compile(r"\b(?:one's|someone's|sb's|oneself)\b")  # một từ bất kỳ (his/her/my…)
WORD = re.compile(r"[a-z]+(?:'[a-z]+)*")


def load():
    cats, rows, seen = [], [], set()
    cur = None
    for f in sorted(glob.glob(os.path.join(SRC, "*.tsv"))):
        for line in open(f, encoding="utf-8"):
            line = line.rstrip("\n")
            if line.startswith("# cat:"):
                code, vi, en, block = [x.strip() for x in line[6:].split("|")]
                cur = code
                if code not in [c["id"] for c in cats]:
                    cats.append(dict(id=code, vi=vi, en=en, block=block))
                continue
            if not line.strip() or line.startswith("#"):
                continue
            p = line.split("\t")
            if len(p) != 5:
                print("bỏ dòng lỗi:", f, line[:60], file=sys.stderr)
                continue
            key = re.sub(r"[^a-z]+", " ", p[0].lower()).strip()
            if key in seen:
                continue
            seen.add(key)
            rows.append(dict(c=cur, p=p[0].strip(), vi=p[1].strip(), ex=p[2].strip(), b=int(p[3]), s=p[4].strip()))
    return cats, rows


def norm(s):
    s = s.lower().replace("’", "'").replace("‘", "'")
    s = re.sub(r"(?<=[a-z])-(?=[a-z])", "", s)  # mind-body → mindbody (không khớp nhầm "to my mind")
    s = re.sub(r"\bgonna\b", "going to", s)
    s = re.sub(r"\bwanna\b", "want to", s)
    s = re.sub(r"\balright\b", "all right", s)
    s = re.sub(r"\bok\b", "okay", s)
    return s


COMMON = set()  # ~150 từ phổ biến nhất trong phụ đề (điền trong main)


def pattern_rx(pat):
    """-> [(regex trên chuỗi từ đã chuẩn hóa, các từ cố định, chế độ)].
    'sub'   : các từ cố định theo đúng thứ tự, chỗ trống giữa câu = 1–6 từ bất kỳ, (từ tùy chọn) có/không đều được
    'whole' : mẫu ngắn không chỗ trống (≤3 từ) — phải là nguyên một vế câu
    'start' : 1 từ + dấu phẩy đứng đầu câu ("Honestly, …")"""
    out = []
    pat = re.sub(r"\b([A-Za-z']+) / ([A-Za-z']+)\b(?! [A-Za-z'])", r"\1|\2", pat)  # doubled / tripled → 1 vị trí 2 lựa chọn
    for alt in re.split(r"\s+/\s+", pat):
        alt = re.sub(r"[\"“”]", " ", alt)
        alt = re.sub(r"\((?:[^)]*\b(?:imperative|emphasis|formal plan)\b[^)]*)\)", " ", alt)
        toks = re.findall(r"\([^)]*\)|…|\.\.\.|\+|[A-Za-z']+(?:\|[A-Za-z']+)+|[A-Za-z][A-Za-z'’-]*|[,.;:!?]", alt)
        parts, lits, gaps, nalt = [], [], False, 0
        for t in toks:
            if "|" in t:
                parts.append(" (?:%s)" % "|".join(re.escape(norm(x)) for x in t.split("|")))
                nalt += 1
            elif t.startswith("("):
                inner = WORD.findall(norm(t[1:-1]))
                if inner and not SLOT.search(t):
                    parts.append("(?: %s)?" % " ".join(map(re.escape, inner)))
                else:
                    parts.append("GAP")
            elif SLOT.fullmatch(t) or t in ("…", "...", "+"):
                parts.append("GAP")
            elif ANY1.fullmatch(t.lower().replace("’", "'")):
                parts.append(" \\S+")
            elif re.fullmatch(r"[,.;:!?]", t):
                continue
            else:
                for w in WORD.findall(norm(t)):
                    parts.append(" " + re.escape(w))
                    lits.append(w)
        if not lits:
            continue
        if nalt:
            lits = lits + ["\0"] * nalt  # vị trí có lựa chọn: tính là từ cố định, không dùng để lọc ứng viên
        # bỏ chỗ trống ở đầu / cuối
        while parts and parts[0] == "GAP":
            parts.pop(0)
        while parts and parts[-1] == "GAP":
            parts.pop()
            gaps = True
        gaps = gaps or "GAP" in parts or bool(SLOT.search(alt))
        body = "".join("(?: \\S+){1,6}" if x == "GAP" else x for x in parts)
        lead = bool(re.match(r"^\s*(?:…|\.\.\.)", alt))
        inner = "GAP" in parts
        if len(lits) == 1:
            if gaps and re.search(r"^\s*[A-Za-z']+\s*,", alt):
                out.append((lits[0], lits, "start"))
            elif not gaps:
                out.append((lits[0], lits, "whole"))
            elif nalt:
                out.append((re.compile(body + " "), [w for w in lits if w != "\0"], "sub"))
            elif not lead and re.match(r"^\s*[A-Za-z']+\s*(?:…|\(that\))", alt) and not re.search(r"\bV(?:-ing|3)?\b|\+", alt):
                out.append((lits[0], lits, "begin"))   # Although …, Unless …
            elif len(lits[0]) >= 8:
                out.append((re.compile(" %s " % re.escape(lits[0])), lits, "sub"))  # … deforestation …
            continue
        if len(lits) <= 3 and all(w in COMMON or w == "\0" for w in lits) and (inner or lead or "+" in alt):
            continue  # khung ngữ pháp toàn từ quá phổ biến (So … that …) — đếm sẽ sai, bỏ qua
        if not gaps and len(lits) <= 3:
            if nalt:
                out.append((re.compile("^" + body + " $"), [w for w in lits if w != "\0"], "sub"))
            else:
                out.append((" ".join(lits), lits, "whole"))
        else:
            out.append((re.compile(body + " "), [w for w in lits if w != "\0"], "sub"))
    return out


def main():
    import movie_subs_study as M
    cats, rows = load()
    print("mẫu câu:", len(rows), "nhóm:", len(cats))
    eps = M.load_episodes()
    shows = []
    ep_count = Counter()
    lines = []  # (show_i, code, text, norm_words_str, chunks)
    for e in eps:
        show = e["show"] if not e["show"].startswith("Phim") else e["title"].split(" 20")[0]
        if len(show) > 28:  # video YouTube: tiêu đề dài → rút gọn
            show = "Video: " + show.split("'")[0].split(" ")[0]
        if show not in shows:
            shows.append(show)
        si = shows.index(show)
        ep_count[show] += 1
        code = "S%02dE%02d" % (e["s"], e["e"]) if e["s"] else ""
        for _, t in e["lines"]:
            ws = " " + " ".join(WORD.findall(norm(t))) + " "
            lines.append((si, code, t, ws))
    print("lượt thoại:", len(lines))

    # chỉ mục: từ → các dòng; vế câu (≤5 từ) → các dòng; từ đầu câu + dấu phẩy → các dòng
    uni = defaultdict(list)
    whole = defaultdict(set)
    start = defaultdict(set)
    begin = defaultdict(set)
    for li, (_, _, t, ws) in enumerate(lines):
        for w in set(ws.split()):
            uni[w].append(li)
        nt = norm(t)
        for sent in re.split(r"[.!?…]+|\s-\s", nt):
            sw = WORD.findall(sent)
            if 0 < len(sw) <= 5:
                whole[" ".join(sw)].add(li)
            for cl in re.split(r"[,;:—]", sent):
                cw = WORD.findall(cl)
                if 0 < len(cw) <= 5:
                    whole[" ".join(cw)].add(li)
            if sw:
                begin[sw[0]].add(li)
            m = re.match(r"\s*([a-z']+)\s*,", sent)
            if m:
                start[m.group(1)].add(li)

    COMMON.update(w for w, _ in sorted(uni.items(), key=lambda kv: -len(kv[1]))[:150])

    def ex_score(t):
        sc = abs(len(t) - 50) / 10
        if not (t[:1].isupper() and t.rstrip('"\'')[-1:] in ".!?"):
            sc += 4
        if len(t) > 110:
            sc += 20
        if re.search(r"\b(fuck|shit|bitch|dick|cock|pussy|asshole)", t, re.I):
            sc += 50
        return sc

    found = 0
    for r in rows:
        hits = set()
        for rx, lits, mode in pattern_rx(r["p"]):
            if mode == "whole":
                hits.update(whole.get(rx, ()))
                continue
            if mode == "begin":
                hits.update(begin.get(rx, ()))
                continue
            if mode == "start":
                hits.update(start.get(rx, ()))
                continue
            cand = min((uni.get(w, []) for w in set(lits)), key=len)
            if len(cand) > 60000:
                cand = set(cand).intersection(*[uni.get(w, []) for w in set(lits)])
            hits.update(li for li in cand if rx.search(lines[li][3]))
        per = Counter(lines[li][0] for li in hits)
        r["n"] = len(hits)
        r["by"] = {str(si): n for si, n in per.items()}
        if hits:
            found += 1
            li = min(hits, key=lambda i: (ex_score(lines[i][2]), i))
            si, code, t, _ = lines[li]
            r["m"] = [t, si, code]
        r["k"] = bool(pattern_rx(r["p"]))
    print("mẫu gặp trong phim: %d/%d" % (found, len(rows)))
    data = dict(cats=cats, shows=shows, eps=[ep_count[s] for s in shows], rows=rows)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("window.PB=" + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n")
    print("ghi", OUT, os.path.getsize(OUT) // 1024, "KB")


if __name__ == "__main__":
    main()
