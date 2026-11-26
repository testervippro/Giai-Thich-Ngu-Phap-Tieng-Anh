#!/usr/bin/env python3
"""Destination C1 & C2 Grammar and Vocabulary (Mann & Taylore-Knowles, Macmillan) → cụm cho Kho cụm từ.

Sách là bản scan (không có chữ) → OCR (tesseract) phần tra cứu cuối sách:
  Phrasal verbs database · Phrases, patterns and collocations database · Idioms database (trang PDF 246–261)
Sách in 2 cột, cụm in ĐẬM rồi tới định nghĩa → tách cột, đo độ dày nét từng chữ để nhận chữ đậm; với idiom còn đối chiếu
phần đầu mục với câu ví dụ sau dấu ":" (cụm luôn xuất hiện lại trong ví dụ, cho phép sb/sth/your… và động từ chia).

    .venv/bin/python tools/destination_extract.py ["đường dẫn PDF"]     # -> tools/data/destination_c1c2.json
"""
import csv
import io
import json
import re
import statistics
import subprocess
import sys
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import fitz
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
PDF = Path.home() / "Downloads/Destination C1 & C2 Grammar and Vocabulary - Malcolm Mann, Steve Taylore-Knowles.pdf"
OUT = ROOT / "tools/data/destination_c1c2.json"
TMP = ROOT / "build/destination"
L = []

def ocr_col(img):
    b = io.BytesIO(); img.save(b, 'PNG')
    out = subprocess.run(['tesseract', '-', '-', '--psm', '6', 'tsv'], input=b.getvalue(), capture_output=True).stdout.decode()
    rows = [r for r in csv.DictReader(io.StringIO(out), delimiter='\t', quoting=csv.QUOTE_NONE) if r['text'] and r['text'].strip() and r['conf'] != '-1']
    g = img.convert('L')
    for r in rows:
        x, y, w, h = (int(r[k]) for k in ('left', 'top', 'width', 'height'))
        crop = g.crop((x, y, x + w, y + h)); W2, H2 = crop.size; px = crop.load()
        runs = []
        for yy in range(H2):
            n = 0
            for xx in range(W2):
                if px[xx, yy] < 120: n += 1
                elif n: runs.append(n); n = 0
            if n: runs.append(n)
        runs.sort()
        r['dens'] = runs[len(runs) // 2] if runs else 0      # độ dày nét (trung vị độ dài các đoạn tối theo hàng ngang)
    return rows
def page(path):
    im = Image.open(path); W, H = im.size
    cols = []
    for (a, b) in ((0, W // 2), (W // 2, W)):
        cols.append(ocr_col(im.crop((a, 0, b, H))))
    return cols


def one(i):
    cols = page(str(TMP / f'r{i:03d}.png')); out = []
    for ci, col in enumerate(cols):
        med = statistics.median([r['dens'] for r in col]) if col else 0
        line, cur, x0 = None, [], 0
        for r in col:
            k = (r['block_num'], r['par_num'], r['line_num'])
            if k != line and cur:
                out.append({'p': i, 'c': ci, 'x': x0, 'w': cur}); cur = []
            if k != line: x0 = int(r['left'])
            line = k; cur.append([r['text'], int(r['dens'] >= med + 2)])
        if cur: out.append({'p': i, 'c': ci, 'x': x0, 'w': cur})
    return out


SECT = {'phrasal': range(246, 252), 'colloc': range(252, 258), 'idiom': range(258, 262)}
PART = r"(?:up|down|out|off|on|in|into|over|back|away|about|around|round|through|together|along|across|by|for|after|with|to|apart|ahead|forward|under|behind|onto|upon|without|against|from|at|of|aside|before|past|like)"
PV = re.compile(r"^([a-z]+(?:\s+(?:%s(?:/%s)*|\(%s\)|sb|sth|yourself|oneself|it)){1,4})\s+(.*)$" % (PART, PART, PART))
def clean(t):
    t = t.replace('’', "'").replace('‘', "'").replace('|', 'I').replace('“', '"').replace('”', '"')
    return re.sub(r"\s+", " ", t).strip()
def lines(sec):
    out = []
    for p in SECT[sec]:
        for c in (0, 1):
            ls = [l for l in L if l['p'] == p and l['c'] == c]
            if not ls: continue
            xs = sorted(l['x'] for l in ls); m = xs[len(xs) // 5]
            for l in ls:
                txt = ' '.join(w for w, b in l['w'])
                if 'database' in txt.lower() or len(re.findall(r'[a-z]', txt)) < len(txt) * 0.5: continue
                l['margin'] = abs(l['x'] - m) < 25
                out.append(l)
    return out
def entries(sec):
    ents, cur = [], None
    for l in lines(sec):
        txt = ' '.join(w for w, b in l['w'])
        prev_end = cur is None or re.search(r"[.!?'\")]$", cur['t'].rstrip())
        b0 = l['w'][0][1]; b1 = len(l['w']) > 1 and l['w'][1][1]
        if sec == 'phrasal':
            start = l['margin'] and PV.match(clean(txt)) and (b0 or prev_end)
        elif sec == 'idiom':
            start = l['margin'] and ((b0 and (prev_end or b1)) or (prev_end and ':' not in txt[:25] and cur is not None and ':' in cur['t']))
        else:
            start = b0 and l['margin']
        if start:
            cur = {'t': txt, 'w': list(l['w'])}; ents.append(cur)
        elif cur:
            cur['t'] += ' ' + txt; cur['w'] += l['w']
    return ents
def norm(s): return re.findall(r"[a-z0-9']+", s.lower().replace('’', "'"))
def idiom_head(e):
    ws = e['w']
    JUNK = r"[0-9]+|e{2,}|a{2,}|[A-Z]{1,2}[a-z]?|aE|DT"
    while ws and re.fullmatch(JUNK, ws[0][0]): ws = ws[1:]                                   # rác OCR đầu dòng
    J2 = r"e{2,}|aE|a{3,}"
    ws = [x for i, x in enumerate(ws) if not (i < 10 and (re.fullmatch(J2, x[0]) or
          (x[0] == 'a' and i + 1 < len(ws) and re.fullmatch(J2, ws[i + 1][0]))))]          # rác lẫn giữa cụm
    FIX = {"'ake": "take", "ake": "take", "ell": "tell"}
    if ws and ws[0][0] in FIX: ws = [[FIX[ws[0][0]], ws[0][1]]] + ws[1:]                   # OCR mất chữ đầu
    if len(ws) > 1 and ws[0][0] == 'top' and ws[1][0] == 'dead': ws = [['stop', ws[0][1]]] + ws[1:]
    e = dict(e, w=ws, t=' '.join(w for w, b in ws)); words = [w for w, b in ws]
    # 1) chuỗi chữ đậm ở đầu (cho phép 1 chữ thường lẫn giữa)
    k, gap = 0, 0
    for i, (w, b) in enumerate(ws[:12]):
        generic = w.lower().strip("(),") in ('sb', 'sth', "sb's", 'your', "one's", 'oneself', 'yourself', 'sb/sth', 'a', 'the')
        if b: k, gap = i + 1, 0
        elif i == 0: break
        else:
            gap += 1
            if gap > (2 if generic else 1): break
    # 2) phần đầu xuất hiện lại trong câu ví dụ
    t = clean(e['t']); ex = t.split(':', 1)[1] if ':' in t else ''
    exn = ' ' + ' '.join(norm(ex)) + ' '
    IRR = {'get': 'get|gets|got|getting|gotten', 'stick': 'stick|sticks|stuck|sticking', 'keep': 'keep|keeps|kept|keeping',
           'take': 'take|takes|took|taken|taking', 'make': 'make|makes|made|making', 'give': 'give|gives|gave|given|giving',
           'go': 'go|goes|went|gone|going', 'come': 'come|comes|came|coming', 'be': 'be|is|are|was|were|been|being|am',
           'have': 'have|has|had|having', 'do': 'do|does|did|done|doing', 'put': 'put|puts|putting', 'set': 'set|sets|setting',
           'let': 'let|lets|letting', 'hit': 'hit|hits|hitting', 'cut': 'cut|cuts|cutting', 'run': 'run|runs|ran|running',
           'break': 'break|breaks|broke|broken|breaking', 'bite': 'bite|bites|bit|bitten|biting', 'hold': 'hold|holds|held|holding',
           'see': 'see|sees|saw|seen|seeing', 'tell': 'tell|tells|told|telling', 'feel': 'feel|feels|felt|feeling',
           'lose': 'lose|loses|lost|losing', 'fall': 'fall|falls|fell|fallen|falling', 'tell': 'tell|tells|told|telling',
           'hear': 'hear|hears|heard|hearing', 'catch': 'catch|catches|caught|catching', 'pay': 'pay|pays|paid|paying', 'bring': 'bring|brings|brought|bringing', 'pull': 'pull|pulls|pulled|pulling'}
    def piece(w, first):
        w = w.lower()
        if w in ('sb', 'sth', 'sb/sth', 'someone', 'something'): return r"\S+(?: \S+){0,3}"
        if w in ('your', "one's", "sb's", 'their', 'his', 'her'): return r"(?:my|your|his|her|our|their|its|one's|\S+'s)"
        if w in ('yourself', 'oneself'): return r"(?:\S+self|\S+selves)"
        if first and w in IRR: return '(?:' + IRR[w] + ')'
        if first: return re.escape(w.rstrip('e') if len(w) > 3 else w) + r"\w*"
        return re.escape(w) + "s?"                       # head → heads
    def strip_paren(ts):                     # bỏ nhóm "(hear sth)" (có thể trải nhiều token) khi so với câu ví dụ
        out, d = [], 0
        for t in ts:
            if t.startswith('('): d += 1
            if not d: out.append(t)
            if t.endswith(')'): d = max(0, d - 1)
        return out
    def tok_rx(t, first):
        t = t.lower().replace('’', "'").strip('.,;:!?"')
        if t.startswith('(') and t.endswith(')'): return None            # phần tuỳ chọn trong ngoặc → bỏ khi so
        alts = [re.sub(r"[^a-z0-9'-]", "", a) for a in t.split('/')]
        ps = [piece(a, first) for a in alts if a]
        return None if not ps else (ps[0] if len(ps) == 1 else '(?:' + '|'.join(ps) + ')')
    m = 0
    for j in range(min(10, len(words)), 0, -1):
        toks = words[:j]
        for drop in (0, 1):
            if drop and not (toks and toks[0].lower() in ('a', 'an', 'the', 'your', 'be')): continue
            hit = False
            for ts in (strip_paren(toks[drop:]), [t.strip('()') for t in toks[drop:]]):    # ngoặc: có hoặc không đều được
                pcs = [p for p in (tok_rx(t, i == 0) for i, t in enumerate(ts)) if p]
                if len(pcs) < 2 and not (len(pcs) == 1 and '-' in ts[-1]): continue
                if re.search(' ' + ' '.join(pcs) + ' ', ' ' + ' '.join(re.findall(r"[a-z0-9'-]+", ex.lower().replace('’', "'"))) + ' '):
                    hit = True; break
            if hit: m = j; break
        if m: break
    k = m if (m >= 2 and k > m + 1) else max(k, m)
    if k == 0:                                          # không có chữ đậm, không khớp ví dụ → định nghĩa thường lặp lại động từ đầu / bắt đầu bằng "used"
        low = [w.lower() for w in words[:10]]
        for i in range(2, len(low)):
            if low[i] == low[0].split('/')[0] or low[i] in ('used',) or low[i].startswith(low[0].split('/')[0] + '/'):
                k = i; break       # phần đầu khớp câu ví dụ đáng tin hơn chuỗi chữ đậm quá dài
    # cụm xuống dòng giữa chừng: kết thúc bằng từ chức năng / chỉ 1 từ → lấy thêm tới từ có nghĩa
    FN = ('a', 'an', 'the', 'your', 'own', 'sb', 'sth', 'of', 'on', 'in', 'to', "sb's", 'their', 'his', 'her', 'my', 'our')
    while m < k and 0 < k < len(words) and k < 9 and (words[k - 1].lower() in FN or (k == 1 and '-' not in words[0])) and not words[k - 1].endswith((':', ',')):
        k += 1
    # ngoặc ngay sau: (saves nine), (away/from)
    while k < len(words) and words[k].startswith('('):
        while k < len(words) and not words[k].endswith(')'): k += 1
        k += 1
    if m < k and k > 2 and words[k - 1].lower() == words[0].lower():      # "not have a leg to stand on | not have any way…" → chữ đầu định nghĩa
        k -= 1
    return clean(' '.join(words[:k])), clean(' '.join(words[k:]))
def split_items(s):
    out, d, cur = [], 0, ''
    for ch in s:
        if ch == '(': d += 1
        if ch == ')': d = max(0, d - 1)
        if ch in ',;' and d == 0: out.append(cur); cur = ''
        else: cur += ch
    out.append(cur); return [clean(x) for x in out if clean(x)]


def d_ok(rest):
    d = rest.partition(':')[0]
    return len(re.findall(r'[a-z]{3,}', d)) >= 1


def extract():
    recs = []
    for e in entries('phrasal'):
        m = PV.match(clean(e['t']))
        if not m: continue
        head, rest = m.group(1), m.group(2)
        d, _, ex = rest.partition(':')
        recs.append({'t': 'phrasal', 'p': head, 'd': clean(d), 'e': clean(ex).split('. ')[0].strip(' .') + '.' if ex.strip() else ''})
    for e in entries('idiom'):
        head, rest = idiom_head(e)
        head = re.sub(r"^'?ake ", "take ", re.sub(r"^top dead", "stop dead", re.sub(r"^ell tales", "tell tales", head)))           # OCR mất chữ đầu
        while len(head.split()) > 2 and head.split()[-1] in ('someone', 'something', 'used'):   # chữ đầu của định nghĩa dính vào
            rest = head.split()[-1] + ' ' + rest; head = head.rsplit(' ', 1)[0]
        core = [w for w in norm(head) if w not in ('sb', 'sth', 'a', 'an', 'the', 'your', 'on', 'in', 'of', 'to', 'hear', 'give', 'do')]
        if (len(norm(head)) < 2 or not re.match(r"^[A-Za-z(]", head) or re.fullmatch(r"\([^)]*\)", head) or not d_ok(rest)
                or norm(head)[-1] in ('a', 'an', 'the') or len(core) < 1): continue
        d, _, ex = rest.partition(':')
        recs.append({'t': 'idiom', 'p': head, 'd': clean(d), 'e': clean(ex).split('. ')[0].strip(' .') + '.' if ex.strip() else ''})
    for e in entries('colloc'):
        words = e['t'].split(' ', 1)
        if len(words) < 2: continue
        hw = clean(words[0])
        for it in split_items(words[1]):
            it = ' '.join(w for w in it.split() if not re.fullmatch(r"e{2,}|aE|a{3,}|[A-Z][a-z]?E?", w))      # chữ rác OCR
            for bad, good in (('takhe', 'take'), ('lght', 'light'), ('alljust', 'all/just')):
                it = re.sub(r"\b%s\b" % bad, good, it)
            if re.search(r"[«»—=_<>\[\]{}|]", it) or any(len(x) > 3 and not re.search(r"[aeiouy]", x) for x in (re.sub(r"sb|sth|[^a-z]", "", w.lower()) for w in it.split())):
                continue                                                                         # dòng toàn ký hiệu / rác
            for part in split_dup(clean_colloc(it)):
                if len(part.split()) >= 2 and re.search(r'[a-z]{2}', part) and part.lower() != 'patterns and':
                    recs.append({'t': 'collocation', 'p': part})
    return recs


KEEP2 = {'a', 'i', 'an', 'to', 'of', 'in', 'on', 'at', 'by', 'do', 'go', 'up', 'be', 'me', 'my', 'us', 'it', 'is', 'so', 'no', 'or',
         'as', 'if', 'we', 'he', 'sb', 'tv', 'pm', 'am', 'ok', 'oh', 'eg', 'ie'}


def clean_colloc(it):
    """Bỏ chữ cái lạc của OCR ("take into t account", "in kt the act", "on : balance", "' arms control")."""
    ws = [w for w in it.split() if not (re.fullmatch(r"[A-Za-z]{1,2}", w) and w.lower() not in KEEP2) and not re.fullmatch(r"[^A-Za-z(]+", w)]
    return ' '.join(ws).strip(" '")


def split_dup(it):
    """Hai mục dính nhau ở chỗ đổi đầu mục: "decide on delight delight in doing" → "decide on" + "delight in doing"."""
    ws = it.split()
    for i in range(1, len(ws)):
        if ws[i].lower() == ws[i - 1].lower() and ws[i].isalpha() and ws[i].lower() not in ('very', 'so', 'had', 'that'):
            return [' '.join(ws[:i - 1]), ' '.join(ws[i:])]
    return [it]

def main():
    global L
    pdf = Path(sys.argv[1]).expanduser() if len(sys.argv) > 1 else PDF
    TMP.mkdir(parents=True, exist_ok=True)
    d = fitz.open(pdf)
    for i in range(246, 262):
        f = TMP / f"r{i:03d}.png"
        if not f.exists():
            d[i].get_pixmap(dpi=200).save(str(f))
    with ProcessPoolExecutor(8) as ex:
        L = [l for pg in ex.map(one, range(246, 262)) for l in pg]
    recs = extract()
    OUT.write_text(json.dumps(recs, ensure_ascii=False, indent=0), encoding="utf-8")
    c = defaultdict(int)
    for r in recs:
        c[r["t"]] += 1
    print(dict(c), "->", OUT.relative_to(ROOT))


if __name__ == "__main__":
    main()
