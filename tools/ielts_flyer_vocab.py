#!/usr/bin/env python3
"""Gộp "5000 từ vựng IELTS thông dụng" (flyer.vn, 33 chủ đề) vào docs/toeic-vocabulary-index.md.

- Giữ nguyên các mục Hackers TOEIC Index đang có (cột Nguồn = TOEIC, hoặc chưa có cột Nguồn).
- Tải lại danh sách IELTS từ flyer.vn: bảng "Từ vựng | Phiên âm | Dịch nghĩa" dưới mỗi chủ đề.
- Bỏ trùng theo khoá chuẩn hoá (chữ thường, bỏ "(to)"/"to " đầu, bỏ dấu chấm cuối, gộp khoảng trắng):
  trùng thì gộp nghĩa (không lặp lại), phiên âm lấy cái đầu tiên, nguồn ghi đủ.
- Sắp A–Z, đánh số lại. Cột 2–3 giữ là Từ | Nghĩa để các script khác (movie_phrases.py, toeic_songs_*.py) vẫn đọc được.

    python3 tools/ielts_flyer_vocab.py [file_html_đã_tải]
"""
import html
import os
import re
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MD = os.path.join(ROOT, "docs", "toeic-vocabulary-index.md")
URL = "https://flyer.vn/5000-tu-vung-ielts-thong-dung/"


def text(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


def key(term):
    t = term.lower().replace("’", "'").replace("‘", "'")
    t = re.sub(r"^\(to\)\s*", "", t)
    t = re.sub(r"\s+", " ", t).strip(" .;,")
    return t


def fetch_ielts(path=None):
    if path:
        s = open(path, encoding="utf-8").read()
    else:
        req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
        s = urllib.request.urlopen(req, timeout=60).read().decode("utf-8")
    out, topic = [], ""
    # mỗi bảng đứng sau tiêu đề chủ đề "N. English (Tiếng Việt)"
    for m in re.finditer(r"<h[23][^>]*>(.*?)</h[23]>|(<table.*?</table>)", s, flags=re.S):
        if m.group(1) is not None:
            topic = text(m.group(1))
            continue
        tm = re.match(r"\d+\.\s*([^(]+)", topic or "")
        tname = tm.group(1).strip() if tm else ""
        for row in re.findall(r"<tr.*?</tr>", m.group(2), flags=re.S):
            c = [text(x) for x in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, flags=re.S)]
            if len(c) < 3 or c[0] == "Từ vựng" or not c[0]:
                continue
            out.append(dict(term=c[0], ipa=c[1], vi=c[2], src="IELTS · " + tname if tname else "IELTS"))
    return out


def load_md():
    rows, head = [], []
    for line in open(MD, encoding="utf-8"):
        m = re.match(r"^\| (\d+) \| (.+?) \|(.*)\|\s*$", line)
        if not m:
            if not rows:
                head.append(line)
            continue
        cols = [x.strip() for x in m.group(3).split("|")]
        vi = cols[0]
        ipa = cols[1] if len(cols) > 1 else ""
        src = cols[2] if len(cols) > 2 else "TOEIC (Hackers)"
        if "TOEIC" in src:
            rows.append(dict(term=m.group(2).strip(), ipa=ipa, vi=vi, src="TOEIC (Hackers)"))
    return rows


def main():
    toeic = load_md()
    ielts = fetch_ielts(sys.argv[1] if len(sys.argv) > 1 else None)
    merged = {}
    for r in toeic + ielts:
        k = key(r["term"])
        if not k:
            continue
        if k not in merged:
            merged[k] = dict(term=r["term"], ipa=r["ipa"], vis=[], srcs=[])
        e = merged[k]
        if not e["ipa"] and r["ipa"]:
            e["ipa"] = r["ipa"]
        for v in re.split(r"\s*;\s*", r["vi"]):
            if v and v.lower() not in (x.lower() for x in e["vis"]):
                e["vis"].append(v)
        if r["src"] not in e["srcs"]:
            e["srcs"].append(r["src"])
    items = sorted(merged.values(), key=lambda e: (key(e["term"]).lstrip("('\"-0123456789 "), key(e["term"])))
    n_t = sum(1 for e in items if any("TOEIC" in s for s in e["srcs"]))
    n_i = sum(1 for e in items if any("IELTS" in s for s in e["srcs"]))
    both = sum(1 for e in items if any("TOEIC" in s for s in e["srcs"]) and any("IELTS" in s for s in e["srcs"]))
    esc = lambda s: s.replace("|", "/")
    L = ["# Danh sách từ vựng TOEIC + IELTS (Index đầy đủ)\n",
         "> Nguồn: *Hackers TOEIC Vocabulary* (trang 524-559, phần Index — OCR từ bản scan, nghĩa dịch tự động) và "
         "**5000 từ vựng IELTS thông dụng** theo 33 chủ đề của [flyer.vn](%s) (kèm phiên âm). Dùng `Ctrl+F` để tra cứu nhanh.\n" % URL,
         "> Tổng cộng: **%d mục** (đã bỏ trùng), sắp xếp A-Z — %d mục TOEIC, %d mục IELTS, %d mục có ở cả hai "
         "(gộp nghĩa, cột Nguồn ghi đủ).\n" % (len(items), n_t, n_i, both),
         "---\n",
         "| # | Từ / Cụm từ | Nghĩa tiếng Việt | Phiên âm | Nguồn |",
         "|---|---|---|---|---|"]
    for i, e in enumerate(items, 1):
        L.append("| %d | %s | %s | %s | %s |" % (i, esc(e["term"]), esc("; ".join(e["vis"])), esc(e["ipa"]), esc(", ".join(e["srcs"]))))
    open(MD, "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("toeic", len(toeic), "ielts rows", len(ielts), "-> merged", len(items), "| both", both)


if __name__ == "__main__":
    main()
