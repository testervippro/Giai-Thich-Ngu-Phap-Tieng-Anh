#!/usr/bin/env python3
"""OCR một PDF scan (ảnh, không có lớp text thật) ra văn bản.

Viết cho "4500 English Collocations and Idioms" (bản CamScanner): `pdftotext`
chỉ đọc được watermark, phải OCR từng trang. Ảnh scan gốc chỉ ~116 ppi, có
bảng kẻ ô và chữ mặt sau in hằn qua giấy, nên OCR thẳng thì bảng ra rác.
Mỗi trang được xử lý như sau:

  1. PyMuPDF render trang ra ảnh xám ở `--dpi`, cắt bỏ dải quảng cáo ở chân trang.
  2. Xoá đường kẻ bảng: dò trên bản render độ phân giải thấp, chia thành dải để
     chịu được trang scan hơi nghiêng, rồi tô trắng ở bản độ phân giải cao.
     Không xoá thì tesseract đọc lẫn đường kẻ thành ký tự rác và bỏ sót dòng.
  3. Tô trắng mọi điểm ảnh sáng hơn `--threshold` để bỏ chữ in hằn từ mặt sau.
  4. Chạy tesseract (vie+eng, psm 6 để giữ mỗi dòng bảng trên 1 dòng), rồi bỏ
     dòng watermark và ký hiệu rác ở cuối dòng.

Mỗi trang ghi ra 1 file .txt, dùng làm cache: chạy lại chỉ OCR các trang còn
thiếu. Các trang chạy song song nhiều tiến trình.

    python3 tools/pdf_ocr.py "docs/4500 English Collocations and Idioms.pdf" \\
        -o build/4500-ocr --merge build/4500-collocations-ocr.md

    # thử vài trang và xem ảnh đã tiền xử lý
    python3 tools/pdf_ocr.py "docs/…pdf" -f 21 -l 21 --keep-images

Yêu cầu: `brew install tesseract tesseract-lang` và `pip install pymupdf`.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import fitz  # PyMuPDF

# Dòng watermark/quảng cáo lặp lại ở mỗi trang của bản scan.
JUNK_LINE = re.compile(
    r"(?i)t[aà]i li[eệ]u b[oở]i|t[iì]m th[eê]m t[aà]i li[eệ]u|nganhangdethi|qu[eé]t qr"
)
# Cụm cuối dòng toàn ký hiệu (không có chữ/số): rác do bóng mờ hoặc đường kẻ sót lại.
TRAILING_JUNK = re.compile(r"(?:\s+[^\w\s]+)+\s*$")

FOOTER_CROP = 0.925   # giữ 92.5% phía trên trang; phần dưới là banner quảng cáo
DETECT_DPI = 100      # độ phân giải dùng để dò đường kẻ bảng
LINE_DARK = 160       # điểm ảnh tối hơn mức này được tính là mực khi dò đường kẻ
LINE_FILL = 0.8       # tỉ lệ mực tối thiểu trên 1 hàng/cột để coi là đường kẻ
STRIPS = 8            # số dải dò đường kẻ (chịu được trang hơi nghiêng)


def render_gray(page: fitz.Page, dpi: int, clip: fitz.Rect) -> fitz.Pixmap:
    m = fitz.Matrix(dpi / 72, dpi / 72)
    return page.get_pixmap(matrix=m, clip=clip, colorspace=fitz.csGRAY, alpha=False, annots=False)


def find_table_lines(pix: fitz.Pixmap) -> tuple[list[tuple[int, int, int]], list[tuple[int, int, int]]]:
    """Dò đường kẻ dọc/ngang trên ảnh xám độ phân giải thấp.

    Trả về (dọc, ngang): dọc là (y0, y1, x), ngang là (x0, x1, y), theo toạ độ của `pix`.
    Ảnh được chia thành STRIPS dải để 1 đường kẻ hơi nghiêng vẫn nằm gọn trong 1 cột của mỗi dải.
    """
    w, h = pix.width, pix.height
    ink = pix.samples.translate(bytes(1 if i < LINE_DARK else 0 for i in range(256)))
    rows = [ink[y * w:(y + 1) * w] for y in range(h)]

    vertical = []
    for s in range(STRIPS):
        y0, y1 = h * s // STRIPS, h * (s + 1) // STRIPS
        counts = [0] * w
        for y in range(y0, y1):
            for x, v in enumerate(rows[y]):
                if v:
                    counts[x] += 1
        need = LINE_FILL * (y1 - y0)
        vertical += [(y0, y1, x) for x, c in enumerate(counts) if c >= need]

    horizontal = []
    for s in range(STRIPS):
        x0, x1 = w * s // STRIPS, w * (s + 1) // STRIPS
        need = LINE_FILL * (x1 - x0)
        horizontal += [(x0, x1, y) for y in range(h) if sum(rows[y][x0:x1]) >= need]
    return vertical, horizontal


def preprocess(pdf: Path, page_no: int, dpi: int, threshold: int) -> fitz.Pixmap:
    """Render 1 trang thành ảnh xám sạch sẵn sàng cho OCR."""
    with fitz.open(pdf) as doc:
        page = doc[page_no - 1]
        r = page.rect
        clip = fitz.Rect(r.x0, r.y0, r.x1, r.y0 + r.height * FOOTER_CROP)
        vertical, horizontal = find_table_lines(render_gray(page, DETECT_DPI, clip))
        hi = render_gray(page, dpi, clip)

    w, h = hi.width, hi.height
    k = dpi / DETECT_DPI
    pad = int(k * 1.5)
    buf = bytearray(hi.samples)

    for y0, y1, x in vertical:
        xa, xb = max(0, int(x * k) - pad), min(w, int((x + 1) * k) + pad)
        white = b"\xff" * (xb - xa)
        for y in range(int(y0 * k), min(h, int(y1 * k))):
            buf[y * w + xa:y * w + xb] = white
    for x0, x1, y in horizontal:
        xa, xb = int(x0 * k), min(w, int(x1 * k))
        white = b"\xff" * (xb - xa)
        for yy in range(max(0, int(y * k) - pad), min(h, int((y + 1) * k) + pad)):
            buf[yy * w + xa:yy * w + xb] = white

    # Tô trắng vùng xám nhạt (chữ mặt sau in hằn), giữ nguyên độ xám của mực thật.
    lut = bytes(255 if i >= threshold else i for i in range(256))
    return fitz.Pixmap(fitz.csGRAY, w, h, bytes(buf).translate(lut), False)


def clean_text(raw: str) -> str:
    out: list[str] = []
    for ln in raw.split("\n"):
        if JUNK_LINE.search(ln):
            continue
        ln = TRAILING_JUNK.sub("", ln.rstrip()).strip()
        if ln and not re.search(r"\w", ln):  # dòng chỉ toàn ký hiệu
            continue
        if ln == "" and (not out or out[-1] == ""):
            continue
        out.append(ln)
    return "\n".join(out).strip() + "\n"


def ocr_page(pdf: Path, page_no: int, dpi: int, threshold: int, lang: str, psm: int,
             out_dir: Path, keep_image: bool) -> int:
    """OCR 1 trang, ghi ra out_dir/<page>.txt (bỏ qua nếu đã có — cache)."""
    out_file = out_dir / f"{page_no:04d}.txt"
    if out_file.exists():
        return page_no

    img = out_dir / f"{page_no:04d}.png"
    preprocess(pdf, page_no, dpi, threshold).save(img)
    try:
        result = subprocess.run(
            ["tesseract", str(img), "-", "-l", lang, "--psm", str(psm)],
            check=True, capture_output=True, text=True,
        )
    finally:
        if not keep_image:
            img.unlink(missing_ok=True)

    out_file.write_text(clean_text(result.stdout), encoding="utf-8")
    return page_no


def merge(out_dir: Path, pages: list[int], dest: Path, title: str) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("w", encoding="utf-8") as out:
        out.write(f"# {title}\n\n> Văn bản OCR tự động từ bản scan — có thể sai chính tả, đối chiếu với PDF khi cần.\n\n")
        for p in pages:
            f = out_dir / f"{p:04d}.txt"
            if f.exists():
                out.write(f"## Trang {p}\n\n{f.read_text(encoding='utf-8')}\n")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf", type=Path)
    ap.add_argument("-o", "--out", type=Path, default=Path("build/ocr-text"), help="Thư mục chứa 1 file .txt/trang")
    ap.add_argument("-f", "--first", type=int, default=1, help="Trang bắt đầu")
    ap.add_argument("-l", "--last", type=int, default=0, help="Trang cuối (0 = hết file)")
    ap.add_argument("--dpi", type=int, default=300, help="Độ phân giải render trước khi OCR")
    ap.add_argument("--threshold", type=int, default=120,
                    help="Điểm ảnh sáng hơn mức này (0-255) bị tô trắng để bỏ chữ in hằn; 256 = tắt")
    ap.add_argument("--lang", default="vie+eng", help="Ngôn ngữ tesseract, nối bằng +")
    ap.add_argument("--psm", type=int, default=6, help="Tesseract --psm (6 = 1 khối, giữ dòng bảng trên 1 dòng)")
    ap.add_argument("-j", "--jobs", type=int, default=4, help="Số trang OCR song song")
    ap.add_argument("--merge", type=Path, help="Gộp tất cả trang thành 1 file markdown tại đường dẫn này")
    ap.add_argument("--force", action="store_true", help="OCR lại cả trang đã có cache")
    ap.add_argument("--keep-images", action="store_true", help="Giữ ảnh đã tiền xử lý (.png) để kiểm tra")
    args = ap.parse_args()

    if not args.pdf.exists():
        sys.exit(f"Không thấy file: {args.pdf}")

    with fitz.open(args.pdf) as doc:
        total = doc.page_count
        title = doc.metadata.get("title") or args.pdf.stem
    last = min(args.last or total, total)
    pages = list(range(args.first, last + 1))
    args.out.mkdir(parents=True, exist_ok=True)

    if args.force:
        for p in pages:
            (args.out / f"{p:04d}.txt").unlink(missing_ok=True)

    done = failed = 0
    with ProcessPoolExecutor(max_workers=args.jobs) as pool:
        futures = {
            pool.submit(ocr_page, args.pdf, p, args.dpi, args.threshold, args.lang, args.psm,
                        args.out, args.keep_images): p
            for p in pages
        }
        for fut in as_completed(futures):
            try:
                fut.result()
                done += 1
            except Exception as e:  # 1 trang lỗi không làm hỏng cả lượt chạy
                failed += 1
                print(f"\nLỗi trang {futures[fut]}: {e}", file=sys.stderr)
            print(f"\rOCR {done + failed}/{len(pages)} trang", end="", flush=True)
    print(f"\nXong {done} trang, lỗi {failed} trang. Kết quả trong {args.out}/")

    if args.merge:
        merge(args.out, pages, args.merge, title)
        print(f"Đã gộp vào {args.merge}")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
