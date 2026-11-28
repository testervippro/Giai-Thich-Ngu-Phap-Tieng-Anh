"""4500 English Collocations and Idioms: bảng "| # | Cụm từ | Nghĩa |" trong docs/4500-collocations-idioms.md (OCR từ sách).

OCR hay làm dính chữ ("getdown to business", "beara grudge", "atodds") và để sót chữ rác / tiếng Việt không dấu
ở cuối cụm ("hiton sb tan tinh ai") → fix() tách chữ dính, bỏ đuôi rác, bỏ dòng rác hẳn."""
import re

try:
    from wordfreq import zipf_frequency
except ImportError:                     # không có wordfreq: giữ nguyên như cũ
    zipf_frequency = None

SOURCE = {"code": "c4500", "name": "4500 English Collocations and Idioms", "url": "../#/4500-collocations-idioms"}

_ROW = re.compile(r"^\|\s*(\d+)\s*\|\s*(.+?)\s*\|\s*(.*?)\s*\|\s*$")

# từ thật (ít gặp) — không tách
REAL = set("""breadline pikestaff plughole bargepole ploughshares drabs dribs quids outstay nonsmoking dishwater pigsty
bedpost elbowroom catnap absentminded wiseguy wiseacre sapsucker bullheaded downhearted bellyaching boardinghouse
horsefeathers overcommitted belabor yawner kvetching rooked whatsit counterargument refactor eyelid grapevine abet""".split())
SOLO = {"a", "an", "the", "be", "at", "in", "on", "of", "to", "it", "get", "go", "take", "put", "out", "one's",
        "your", "my", "his", "her", "their", "someone's", "somebody's", "half", "can't", "not", "pick", "pay"}
TYPO = {"familly": "family", "takhe": "take", "lght": "light", "stidk": "stick", "wagping": "wagging",
        "caver": "cover", "idopt": "adopt", "climateacion": "climate action", "sightseel": "sightseeing",
        "bein": "be in", "beinno": "be in no", "beinthe": "be in the", "jabel": "label", "pive": "give", "juck": "luck",
        "inthe": "in the", "atthe": "at the", "onthe": "on the", "tothe": "to the", "ofthe": "of the", "ina": "in a",
        "ona": "on a", "goto": "go to", "offa": "off a", "belike": "be like", "ofa": "of a", "indribs": "in dribs", "schoo": "school", "leaveln": "leave in",
        "hoggle": "boggle", "siturn": "turn", "alotof": "a lot of", "fect": "feet", "binal": "final", "reglons": "regions", "susplelon": "suspicion", "oll": "oil", "alotof": "a lot of"}
KEEP = re.compile(r"(^|/)(sb|sth|sb's|sth's|someone|somebody|something|someone's|somebody's|oneself|one's)\W*($|/)", re.I)
TWO = set("a i an am as at be by do go he if in is it me my no of on or so to up us we".split())
BADPIECE = {"goin", "ina", "ona", "inthe", "atthe", "thewind", "ofa", "toa"}
VI_TAIL = set("""trong di la lam nghe qua khu thuc giang nguy ran rac pap xa ch nay ng tinh mi bi hoa thua nhay quen ngem ma dinh mm
tan ai hau ap mui mau eh hy kinh coi xoay tr nn nhay giao thuc nhin neem khi tin linh hon cha con duy chung sai bira
nh gi th oo""".split())
SHORT_OK = {"up", "in", "on", "of", "to", "it", "me", "us", "go", "do", "be", "so", "no", "by", "at", "an", "a", "i", "sb", "or", "off", "out", "away"}


def z(w):
    return zipf_frequency(w, "en") if zipf_frequency else 9


def segment(lw):
    """'beautyisintheeyeofthebeholder' → 'beauty is in the eye of the beholder' (mỗi mảnh là từ phổ biến, ít mảnh nhất)"""
    n = len(lw)
    best = [None] * (n + 1); best[0] = (0, 0.0, [])
    for i in range(n):
        if best[i] is None:
            continue
        for j in range(i + 1, min(n, i + 15) + 1):
            piece = lw[i:j]
            zp = z(piece)
            if (zp < 3.0 and not (len(piece) >= 5 and zp >= 2.0)) or piece in BADPIECE or (len(piece) <= 2 and piece not in TWO):
                continue
            cand = (best[i][0] + 1 + max(0.0, 5.0 - zp), 0, best[i][2] + [piece])
            if best[j] is None or cand[0] < best[j][0]:
                best[j] = cand
    return (" ".join(best[n][2]) if best[n] and len(best[n][2]) > 1 else "").replace("be holder", "beholder")


def split_word(w):
    lw = w.lower()
    if lw in TYPO:
        out = TYPO[lw]
        return out[0].upper() + out[1:] if w[0].isupper() else out
    zw = z(lw)
    if zw < 2.0 and "l" in lw:                # OCR đọc i thành l: "achlevement", "rellef", "frultion"
        for k in [i for i, c in enumerate(lw) if c == "l"]:
            cand = lw[:k] + "i" + lw[k + 1:]
            if z(cand) >= 3.0:
                return cand[0].upper() + cand[1:] if w[0].isupper() else cand
    if len(lw) < 4 or lw in REAL or zw >= 2.5 or not re.fullmatch(r"[a-z']+", lw):
        return w
    best = None
    for k in range(1, len(lw)):
        a, b = lw[:k], lw[k:]
        if a.endswith("'") or b.startswith("'") or (len(a) <= 2 and a not in TWO) or (len(b) <= 2 and b not in TWO):
            continue
        za, zb = z(a), z(b)
        if a in SOLO or b in SOLO:            # chữ dính với từ chức năng: "a"+"charm", "bear"+"a", "of"+"life"
            other = zb if a in SOLO else za
            ok = zw < 1.5 or b in SOLO or a in ("a", "an")
            s = min(za, zb) + 3 if ok and (other >= 2.5 if zw < 1.5 else other >= 3.5) else -1
        else:                                 # hai từ nội dung dính nhau: chỉ khi cả cụm gần như không phải từ
            s = min(za, zb) if zw < 1.5 and min(za, zb) >= 3.3 else -1
        if s > 0 and (best is None or s > best[0]):
            best = (s, a + " " + b)
    if not best and zw < 1.0 and len(lw) >= 7:
        seg = segment(lw)
        if seg:
            best = (0, seg)
    if not best:
        return w
    out = best[1]
    return out[0].upper() + out[1:] if w[0].isupper() else out


def junk_word(w):
    if KEEP.search(w):
        return False
    parts = [x for x in re.split(r"[/]", w.lower().strip(".,;:!?()[]=_'\"")) if x]
    def j(x):
        x = x.strip(".,;:!?()[]=_'\"")
        return bool(x) and x not in REAL and x not in SHORT_OK and (z(x) < 2.0 or not re.search(r"[aeiouy]", x))
    return bool(parts) and all(j(x) for x in parts)


def short_junk(t):
    """chữ ngắn sót lại do OCR / tiếng Việt không dấu: 'oe', 'mm', 'bj', 'TA' (không phải từ tiếng Anh phổ biến)"""
    x = t.strip(".,;:!?()[]=_'\"")
    if len(x) <= 3 and x.isupper() and len(x) > 1 and x not in ("OK", "TV", "CV", "UK", "US", "IT", "PR", "HR", "VR", "GM", "AI"):
        return True
    return len(x) <= 3 and x.lower() not in SHORT_OK and not KEEP.search(x) and z(x.lower()) < 3.0


def fix(p):
    if not zipf_frequency:
        return p
    toks = p.split()
    def tail_junk(t, end):
        if end and t.lower().strip(",.") in VI_TAIL:
            return True
        if ")" in t or split_word(t) != t:
            return False
        return (junk_word(t) or short_junk(t) or (end and (t.lower().strip(",.") in VI_TAIL or (t in ("a", "A") and len(toks) > 2)))
                or (end and t.lower() == "an"))
    while len(toks) > 1 and tail_junk(toks[-1], True):
        toks.pop()                            # đuôi rác: chữ tiếng Việt không dấu / ký tự OCR sót
    while len(toks) > 1 and tail_junk(toks[0], False) and len(toks[0]) <= 3 and toks[0] not in ("a", "A", "an", "An"):
        toks.pop(0)
    p = " ".join(toks)
    p = re.sub(r"[A-Za-z][A-Za-z']+", lambda m: TYPO.get(m.group(0).lower(), m.group(0)), p)
    p = re.sub(r"[A-Za-z][A-Za-z']+\b(?!\))", lambda m: split_word(m.group(0)), p)     # "origina)" = original: để nguyên
    p = p.replace("ind ribs", "in dribs")
    if re.fullmatch(r"c[uy]m\b.*|sm\b.*|\w{1,4},?", p, re.I) and not re.search(r"[a-z]{3}.*\s", p):
        return ""                             # tiêu đề mục OCR ("CUM TU CO DINH") / mẩu chữ lẻ
    p = re.sub(r"(?<=\w) [b-hj-zB-HJ-Z] (?=\w)", " ", p)        # chữ cái lẻ lạc giữa cụm: "movable t feast"
    words = re.findall(r"[A-Za-z][A-Za-z']*", re.sub(r"\([^)]*\)", " ", p))   # chữ viết tắt trong ngoặc không tính
    bad = sum(junk_word(w) for w in words)
    bad = bad if bad >= 2 or len(words) <= 1 else 0
    short = sum(short_junk(w) for w in words)
    if (not words or bad / len(words) > 0.25 or (len(words) >= 6 and short / len(words) > 0.5)
            or re.search(r"(?i)\bONE mis|\bONE sis|each of the (following|s)|There is O|Read the pa|\bmis i unc|following sentences", p)
            or sum(junk_word(w) or short_junk(w) for w in words) >= 4 or not re.search(r"[a-z]{3}", p)):
        return ""                             # dòng rác
    return p


def extract(root):
    out, topic, kind = [], "", "collocation"
    for line in (root / "docs/4500-collocations-idioms.md").read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            topic = re.sub(r"^## (Chủ đề \d+:\s*)?", "", line).strip()
        elif line.startswith("### "):
            kind = "idiom" if "Idiom" in line else "collocation"
        else:
            m = _ROW.match(line)
            if m and re.search(r"[A-Za-z]{2}", m.group(2)):
                p = fix(m.group(2))
                if p:
                    out.append({"t": kind, "p": p, "m": m.group(3), "e": "", "ev": "", "g": topic, "x": "", "ref": ""})
    return out
