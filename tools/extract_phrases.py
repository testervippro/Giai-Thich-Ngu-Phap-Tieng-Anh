#!/usr/bin/env python3
"""Trích danh sách cụm từ / thành ngữ từ bảng của sách "4500 English Collocations and Idioms".

OCR cả trang (tools/pdf_ocr.py) trộn các cột của bảng vào nhau nên khó đọc. Script này
dò đường kẻ bảng, cắt riêng từng ô của cột cụm từ (cột rộng 15–40% trang, sau cột STT)
và cột nghĩa ngay bên phải, rồi OCR từng ô: cụm từ bằng `eng`, nghĩa bằng `vie` (chỉ
giữ dòng đầu, vì bảng chi tiết có thêm câu ví dụ bên dưới).

Kết quả từng trang được cache trong file JSON. Chủ đề xác định theo trang bắt đầu
trong mục lục (bảng TOPICS); mục A/B theo ô tiêu đề của bảng ("CỤM TỪ CỐ ĐỊNH" / "THÀNH NGỮ").

    python3 tools/extract_phrases.py "docs/4500 English Collocations and Idioms.pdf" \\
        -o build/4500-phrases.md
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import tempfile
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import fitz  # PyMuPDF

DPI = 250             # độ phân giải dò bảng
OCR_DPI = 300         # độ phân giải render ô để OCR
FOOTER_CROP = 0.925   # bỏ banner quảng cáo ở chân trang
V_DARK = 150          # mực của đường kẻ dọc
H_DARK = 170          # mực của đường kẻ ngang (nhạt hơn ở mép bảng)
H_FRAC = 0.7          # đoạn mực liền dài tối thiểu (theo bề ngang cột) để coi là đường kẻ ngang
STRIPS = 16           # số dải dò đường kẻ dọc; mỗi dải < 256 hàng (cộng dồn theo byte)
INK_KEEP = 125        # điểm ảnh sáng hơn mức này bị tô trắng khi OCR (bỏ chữ in hằn, watermark)


def runs(flags: list[bool], min_gap: int = 1) -> list[tuple[int, int]]:
    """Gom các vị trí True liền nhau (cho phép hở <= min_gap) thành đoạn (a, b)."""
    out, start = [], None
    for i, f in enumerate(flags + [False]):
        if f and start is None:
            start = i
        elif not f and start is not None:
            if out and start - out[-1][1] <= min_gap:
                out[-1] = (out[-1][0], i)
            else:
                out.append((start, i))
            start = None
    return out


def render(page: fitz.Page, dpi: int, clip: fitz.Rect | None = None) -> fitz.Pixmap:
    if clip is None:
        r = page.rect
        clip = fitz.Rect(r.x0, r.y0, r.x1, r.y0 + r.height * FOOTER_CROP)
    return page.get_pixmap(matrix=fitz.Matrix(dpi / 72, dpi / 72), clip=clip,
                           colorspace=fitz.csGRAY, alpha=False, annots=False)


def table_rows(page: fitz.Page) -> list[tuple[tuple[int, int, int, int], tuple[int, int, int, int]]]:
    """Các hàng của bảng cụm từ: (ô cụm từ, ô nghĩa), toạ độ pixel ở DPI, trên xuống dưới."""
    pix = render(page, DPI)
    data, w, h = pix.samples, pix.width, pix.height
    ink = data.translate(bytes(1 if i < V_DARK else 0 for i in range(256)))
    light = data.translate(bytes(1 if i < H_DARK else 0 for i in range(256)))
    rows = [ink[y * w:(y + 1) * w] for y in range(h)]
    lrows = [light[y * w:(y + 1) * w] for y in range(h)]

    # 1. Đường kẻ dọc theo từng dải ngang (chịu được trang nghiêng/cong).
    #    Mỗi hàng ảnh là 1 số nguyên lớn, mỗi byte 1 điểm ảnh (0/1): nở ±3px bằng dịch bit,
    #    cộng các hàng trong dải là ra số điểm mực của từng cột.
    strips = []  # (y0, y1, phrase_x0, phrase_x1, meaning_x1)
    weak = []
    mask = (1 << 8 * w) - 1
    for s in range(STRIPS):
        y0, y1 = h * s // STRIPS, h * (s + 1) // STRIPS
        total = 0
        for row in rows[y0:y1]:
            r = int.from_bytes(row, "big")
            d = r
            for k in (1, 2, 3):
                d |= (r << 8 * k) | (r >> 8 * k)
            total += d & mask
        counts = total.to_bytes(w, "big")
        v = [(a + b) // 2 for a, b in runs([c >= 0.85 * (y1 - y0) for c in counts], 2)]
        # Cột cụm từ: khoảng rộng 15–50% trang, bên phải là cột nghĩa (rộng >= 25%), hoặc
        # bên trái là cột STT hẹp khi viền phải bị mất (trang scan bị cắt).
        gaps = list(zip(v, v[1:]))
        for i, (a, b) in enumerate(gaps):
            if not 0.15 * w <= b - a <= 0.50 * w:
                continue
            if i + 1 < len(gaps) and gaps[i + 1][1] - gaps[i + 1][0] >= 0.25 * w:
                strips.append((y0, y1, a, b, gaps[i + 1][1]))
                break
            if i + 1 == len(gaps) and i > 0 and gaps[i - 1][1] - gaps[i - 1][0] < 0.1 * w \
                    and b + 0.25 * w < w:
                strips.append((y0, y1, a, b, min(w, b + int(0.5 * w))))
                break
        else:
            weak.append((y0, y1, v))
    if not strips:
        return []
    # Dải mà đường kẻ giữa cột STT và cột cụm từ bị mờ/đứt: mượn toạ độ cột của dải tốt
    # gần nhất nếu đường kẻ phải của cột cụm từ vẫn khớp.
    for y0, y1, v in weak:
        near = min(strips, key=lambda t: abs(t[0] - y0))
        if any(abs(x - near[3]) < 20 for x in v):
            strips.append((y0, y1, *near[2:]))
    strips.sort()

    reach = h // 12

    def cols_at(y: int):
        y0, y1, *c = min(strips, key=lambda t: 0 if t[0] <= y < t[1] else min(abs(y - t[0]), abs(y - t[1])))
        return c if y0 - reach <= y < y1 + reach else None

    # 2. Đường kẻ ngang: chỉ xét trong cột cụm từ (hẹp nên độ nghiêng không đáng kể).
    hflags = []
    for y in range(h):
        c = cols_at(y)
        if not c:
            hflags.append(False)
            continue
        a, b = c[0] + 12, c[1] - 12
        # gộp ±4 hàng để đường kẻ hơi nghiêng vẫn liền một đoạn
        acc = 0
        for yy in range(max(0, y - 4), min(h, y + 5)):
            acc |= int.from_bytes(lrows[yy][a:b], "big")
        seg = acc.to_bytes(b - a, "big")
        # đường kẻ = 1 đoạn mực gần liền mạch (chữ đậm cũng nhiều mực nhưng có khoảng trắng giữa các từ)
        hflags.append(max((y - x for x, y in runs([bool(v) for v in seg], 4)), default=0) >= H_FRAC * (b - a))
    bounds = [(a + b) // 2 for a, b in runs(hflags, 4)]

    out = []
    for top, bot in zip(bounds, bounds[1:]):
        c = cols_at((top + bot) // 2)
        if not c or bot - top < 60:
            continue
        px0, px1, mx1 = c
        out.append(((px0 + 10, top + 5, px1 - 10, bot - 5), (px1 + 10, top + 5, mx1 - 10, bot - 5)))
    return out


def ocr_box(page: fitz.Page, box: tuple[int, int, int, int], lang: str, tmp: Path) -> list[str]:
    k = 72 / DPI
    x0, y0, x1, y1 = box
    if x1 - x0 < 20 or y1 - y0 < 20:
        return []
    r = page.rect
    pix = render(page, OCR_DPI, fitz.Rect(r.x0 + x0 * k, r.y0 + y0 * k, r.x0 + x1 * k, r.y0 + y1 * k))
    lut = bytes(255 if i >= INK_KEEP else i for i in range(256))
    img = fitz.Pixmap(fitz.csGRAY, pix.width, pix.height, pix.samples.translate(lut), False)
    f = tmp / "cell.png"
    img.save(f)
    out = subprocess.run(["tesseract", str(f), "-", "-l", lang, "--psm", "6"],
                         capture_output=True, text=True).stdout
    return [" ".join(ln.split()) for ln in out.splitlines() if ln.strip()]


def do_page(args: tuple[str, int]) -> tuple[int, list[list[str]]]:
    try:
        return _do_page(*args)
    except Exception as e:  # lỗi 1 trang (ảnh lạ, ô rỗng...) không làm hỏng cả lượt chạy
        raise RuntimeError(f"trang {args[1]}: {e!r}") from None


def _do_page(pdf: str, p: int) -> tuple[int, list[list[str]]]:
    items = []
    with fitz.open(pdf) as doc, tempfile.TemporaryDirectory() as t:
        page = doc[p - 1]
        for pbox, mbox in table_rows(page):
            phrase = " ".join(ocr_box(page, pbox, "eng", Path(t)))
            if not re.search(r"[A-Za-z]{2}", phrase):
                continue
            meaning = ocr_box(page, mbox, "vie", Path(t))
            items.append([phrase, meaning[0] if meaning else ""])
    return p, items


# ---------------------------------------------------------------- dựng file markdown

# (trang PDF bắt đầu, tên) của 46 chủ đề, theo mục lục (trang sách = trang PDF + 4).
TOPICS = [
    (34, "Giáo dục"), (74, "Công việc và kinh doanh"), (104, "Bắt đầu và kết thúc"),
    (113, "Thành công và thất bại"), (126, "Nguyên nhân và tác động"), (139, "Nỗ lực"),
    (147, "Gia đình"), (168, "Mối quan hệ"), (192, "Vấn đề xã hội"),
    (200, "Đồng ý và không đồng ý"), (206, "Khen ngợi và chỉ trích"),
    (216, "Lời khuyên và cảnh báo"), (222, "Ngoại hình, tính cách và hành vi"),
    (234, "Các bộ phận cơ thể"), (295, "Cảm xúc"), (308, "Môi trường"), (343, "Động vật"),
    (362, "Thời tiết"), (371, "Nguy hiểm"), (377, "Cuộc sống hằng ngày"), (382, "Trải nghiệm"),
    (388, "Nhà ở và căn hộ"), (396, "Thức ăn và đồ uống"), (403, "Du lịch"),
    (412, "Thị trấn và quê"), (421, "Văn hóa"), (427, "Lễ hội và tổ chức"), (432, "Giải trí"),
    (439, "Game và thể thao"), (450, "Quần áo và thời trang"), (458, "Màu sắc"),
    (471, "Sức khỏe"), (484, "Tiền bạc và tài chính"), (497, "Số lượng và lượng"),
    (502, "Tính cần thiết và tính đáng mong muốn"), (508, "Khoa học và công nghệ"),
    (515, "Tin tức"), (523, "Lịch sử"), (528, "Tội phạm và pháp luật"),
    (540, "Chiến tranh và xung đột"), (552, "Thời gian"), (562, "So sánh và tương phản"),
    (567, "Kích thước và vị trí"), (573, "Xác suất và may mắn"), (579, "Binomials"),
    (591, "Quảng cáo"),
]
# Trang sách bắt đầu mục B (thành ngữ) của từng chủ đề theo mục lục; None = chủ đề không
# chia A/B trong mục lục (17, 31, 45) thì nhận theo tiêu đề bảng. 11 và 12 bị cắt mất số
# trên bản scan, lấy theo trang có tiêu đề bảng "THÀNH NGỮ".
B_START_BOOK = [61, 91, 112, 123, 137, 145, 163, 181, 201, 207, 217, 223, 234, 245, 307, 332, None,
                370, 378, 383, 389, 397, 405, 414, 422, 428, 434, 440, 449, 456, None, 483, 496,
                503, 509, 516, 524, 530, 541, 552, 560, 568, 573, 580, None, 597]
BOOK_OFFSET = 4  # trang sách = trang PDF + 4
SECTION_TITLES = {"A": ("A. Cụm từ cố định (Collocations)", "Cụm từ"),
                  "B": ("B. Thành ngữ (Idioms)", "Thành ngữ")}
VI_CHARS = re.compile(r"[àáâãèéêìíòóôõùúýăđĩũơưạ-ỹ]", re.I)  # dấu tiếng Việt
LOANWORDS = {"café", "cafe", "résumé", "cliché", "fiancé", "fiancée", "naïve", "déjà", "vu", "entrée"}


def topic_of(page: int) -> int | None:
    n = None
    for i, (start, _) in enumerate(TOPICS, 1):
        if page >= start:
            n = i
    return n


def header_section(cell: str) -> str | None:
    """Ô tiêu đề bảng ("CỤM TỪ CỐ ĐỊNH" / "THÀNH NGỮ", OCR bằng eng nên mất dấu)."""
    letters = re.sub(r"[^A-Za-z]", "", cell)
    if not letters or letters.upper() != letters or len(letters) > 20:
        return None
    if re.search(r"TH?AN|NG[UOY]", letters):
        return "B"
    if re.search(r"C[UO]M|DINH|BINH", letters):
        return "A"
    return None


def clean_phrase(s: str) -> str:
    s = s.split(" — ")[0].replace("|", " ").replace("’", "'").replace("{", "(").replace("}", ")")
    toks = s.split()
    # nghĩa tiếng Việt dính sang cột cụm từ: cắt từ từ đầu tiên có dấu tiếng Việt
    cut = next((i for i, t in enumerate(toks)
                if VI_CHARS.search(t) and t.lower().strip(".,;:()") not in LOANWORDS), len(toks))
    s = " ".join(toks[:cut])
    s = re.sub(r"^[^A-Za-z(]+", "", s)               # số thứ tự / ký hiệu rác ở đầu
    s = re.sub(r"[^A-Za-z)/'éè]+$", "", s)           # rác ở cuối
    return " ".join(s.replace(" ,", ",").split())


def clean_meaning(s: str) -> str:
    s = re.sub(r"^[^\wÀ-ỹ(]+", "", s)
    s = re.sub(r"[\s|_\-—~.,;:'\"“”*•¬]+$", "", s.replace("|", " "))
    return " ".join(s.split())


PAGE_B = re.compile(r"\(IDIOMS\)|TH[AÀ]NH ?NG\S*\s*[|—_\-:’']*\s*NGH")
PAGE_A = re.compile(r"\(COLLOCATIONS\)|C[UỤ]M ?T[UỪ] ?C[OỐỔÕỖ] ?[ĐD][IỊ]NH\s*[|—_\-:’']*\s*NGH")


def page_section(text: str) -> str | None:
    """Mục A/B theo tiêu đề bảng in trên trang (dự phòng khi ô tiêu đề OCR hỏng)."""
    for ln in text.splitlines():
        if PAGE_B.search(ln):
            return "B"
        if PAGE_A.search(ln):
            return "A"
    return None


def text_rows(text: str) -> list[list[str]]:
    """Dự phòng khi không dò được bảng: đọc từ OCR toàn trang các dòng dạng
    "<STT> <cụm từ tiếng Anh> <nghĩa tiếng Việt>" (bảng tóm tắt 1 dòng/hàng)."""
    out = []
    for ln in text.splitlines():
        if "Question" in ln or ln.lstrip().startswith("("):
            continue
        toks = ln.replace("|", " ").split()
        cut = next((i for i, t in enumerate(toks) if VI_CHARS.search(t)), None)
        if not cut:
            continue
        en = clean_phrase(" ".join(toks[:cut]))
        if len(re.findall(r"[A-Za-z]{2,}", en)) >= 2:
            out.append([en, " ".join(toks[cut:])])
    return out


def suspicious(items: list[list[str]]) -> bool:
    """Kết quả dò bảng của trang có vẻ sai (lấy nhầm cột): quá nửa ô nghĩa rỗng."""
    return not items or sum(1 for _, m in items if not m.strip()) > 0.4 * len(items)


def build(cache: dict[str, list[list[str]]], dest: Path, page_text: Path) -> int:
    sections: dict[int, dict[str, list[tuple[str, str]]]] = {}
    seen: set[tuple[int, str]] = set()
    topic, section = None, "A"
    for p in sorted(cache, key=int):
        t = topic_of(int(p))
        if t is None:
            continue
        if t != topic:
            topic, section = t, "A"
        f = page_text / f"{int(p):04d}.txt"
        text = f.read_text(encoding="utf-8") if f.exists() else ""
        b_book = B_START_BOOK[topic - 1]
        if b_book is None:
            section = page_section(text) or section
        elif int(p) + BOOK_OFFSET < b_book:
            section = "A"
        elif int(p) + BOOK_OFFSET > b_book:
            section = "B"
        else:  # trang chuyển mục: theo tiêu đề bảng; không thấy tiêu đề A nào thì coi là B
            has_a = any(header_section(ph) == "A" for ph, _ in cache[p]) or PAGE_A.search(text)
            section = page_section(text) or ("A" if has_a else "B")
        items = cache[p]
        fallback = text_rows(text)
        if suspicious(items) or len(fallback) >= 2 * len(items) + 3:  # dò bảng hỏng / gộp nhầm ô
            items = fallback or items
        for phrase, meaning in items:
            sec = header_section(phrase)
            if sec:
                if b_book is None or int(p) + BOOK_OFFSET == b_book:
                    section = sec
                continue
            phrase = clean_phrase(phrase)
            if len(phrase) < 3 or not re.search(r"[a-z]{2}", phrase) or "__" in phrase \
                    or (phrase[0].isupper() and len(phrase.split()) > 7) \
                    or re.search(r"\[\d|\bquestion\b|\bsentence\b|\bSTT\b|THANH|LESSON", phrase, re.I) \
                    or len(re.findall(r"[^A-Za-z /'(),=\-]", phrase)) > 0.08 * len(phrase):
                continue  # ô tiếng Việt / rác / câu bài tập
            key = (topic, phrase.lower())
            if key in seen:
                continue
            seen.add(key)
            sections.setdefault(topic, {}).setdefault(section, []).append((phrase, clean_meaning(meaning)))

    lines = ["# 4500 English Collocations and Idioms — danh sách cụm từ", "",
             "> Trích tự động (OCR) từ cột cụm từ / thành ngữ trong các bảng của sách; có thể còn",
             "> lỗi chính tả, đối chiếu với PDF khi cần. Cột nghĩa lấy dòng đầu của ô nghĩa.", ""]
    count = 0
    for t in sorted(sections):
        lines += [f"## Chủ đề {t:02d}: {TOPICS[t - 1][1]}", ""]
        for sec in ("A", "B"):
            rows = sections[t].get(sec)
            if not rows:
                continue
            title, col = SECTION_TITLES[sec]
            lines += [f"### {title}", "", f"| # | {col} | Nghĩa |", "|---:|---|---|"]
            for i, (ph, me) in enumerate(rows, 1):
                lines.append(f"| {i} | {ph.replace('|', '/')} | {me.replace('|', '/')} |")
            lines.append("")
            count += len(rows)
    dest.write_text("\n".join(lines), encoding="utf-8")
    return count


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf")
    ap.add_argument("-f", "--first", type=int, default=1)
    ap.add_argument("-l", "--last", type=int, default=0)
    ap.add_argument("-j", "--jobs", type=int, default=8)
    ap.add_argument("--cache", type=Path, default=Path("build/4500-phrases.json"))
    ap.add_argument("--page-text", type=Path, default=Path("build/4500-ocr"),
                    help="Văn bản OCR toàn trang (tools/pdf_ocr.py), dùng để nhận tiêu đề mục A/B")
    ap.add_argument("-o", "--out", type=Path, default=Path("build/4500-phrases.md"))
    args = ap.parse_args()

    with fitz.open(args.pdf) as doc:
        last = min(args.last or doc.page_count, doc.page_count)
    cache = json.loads(args.cache.read_text()) if args.cache.exists() else {}
    todo = [(args.pdf, p) for p in range(args.first, last + 1) if str(p) not in cache]
    with ProcessPoolExecutor(args.jobs) as pool:
        for i, (p, items) in enumerate(pool.map(do_page, todo), 1):
            cache[str(p)] = items
            print(f"\rOCR {i}/{len(todo)} trang", end="", flush=True)
            if i % 20 == 0:
                args.cache.write_text(json.dumps(cache, ensure_ascii=False, indent=0))
    args.cache.write_text(json.dumps(cache, ensure_ascii=False, indent=0))
    print()

    n = build(cache, args.out, args.page_text)
    print(f"Đã ghi {n} cụm từ vào {args.out}")


if __name__ == "__main__":
    main()
