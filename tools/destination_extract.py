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
    ws = e['w']; words = [w for w, b in ws]
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
           'lose': 'lose|loses|lost|losing', 'bring': 'bring|brings|brought|bringing', 'pull': 'pull|pulls|pulled|pulling'}
    def piece(w, first):
        w = w.lower()
        if w in ('sb', 'sth', 'sb/sth', 'someone', 'something'): return r"\S+(?: \S+)?"
        if w in ('your', "one's", "sb's"): return r"(?:my|your|his|her|our|their|its|one's|\S+'s)"
        if w in ('yourself', 'oneself'): return r"\S+self|\S+selves"
        if first and w in IRR: return '(?:' + IRR[w] + ')'
        if first and len(w) > 3: return re.escape(w.rstrip('e')) + r"\w*"
        return re.escape(w) + "s?"                       # head → heads
    m = 0
    for j in range(min(10, len(words)), 1, -1):
        cand = norm(' '.join(words[:j]))
        for c in (cand, cand[1:] if cand and cand[0] in ('a', 'an', 'the', 'your', 'be') else None):
            if not c or len(c) < 2: continue
            rx = ' ' + ' '.join(piece(w, i == 0) for i, w in enumerate(c)) + ' '
            if re.search(rx, exn): m = j; break
        if m: break
    k = m if (m >= 2 and k > m + 1) else max(k, m)       # phần đầu khớp câu ví dụ đáng tin hơn chuỗi chữ đậm quá dài
    # ngoặc ngay sau: (saves nine), (away/from)
    while k < len(words) and words[k].startswith('('):
        while k < len(words) and not words[k].endswith(')'): k += 1
        k += 1
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
    return len(re.findall(r'[a-z]{3,}', d)) >= 2


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
        head = re.sub(r"^ake ", "take ", re.sub(r"^top dead", "stop dead", head))           # OCR mất chữ đầu
        while len(head.split()) > 2 and head.split()[-1] in ('someone', 'something', 'used'):   # chữ đầu của định nghĩa dính vào
            rest = head.split()[-1] + ' ' + rest; head = head.rsplit(' ', 1)[0]
        core = [w for w in norm(head) if w not in ('sb', 'sth', 'a', 'an', 'the', 'your', 'on', 'in', 'of', 'to', 'hear', 'give', 'do')]
        if (len(norm(head)) < 2 or not re.match(r"^[A-Za-z(]", head) or head.startswith('(') or not d_ok(rest)
                or norm(head)[-1] in ('a', 'an', 'the') or len(core) < 1): continue
        d, _, ex = rest.partition(':')
        recs.append({'t': 'idiom', 'p': head, 'd': clean(d), 'e': clean(ex).split('. ')[0].strip(' .') + '.' if ex.strip() else ''})
    for e in entries('colloc'):
        words = e['t'].split(' ', 1)
        if len(words) < 2: continue
        hw = clean(words[0])
        for it in split_items(words[1]):
            if len(it.split()) >= 2 and re.search(r'[a-z]{2}', it):
                recs.append({'t': 'collocation', 'p': it})
    return recs


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
