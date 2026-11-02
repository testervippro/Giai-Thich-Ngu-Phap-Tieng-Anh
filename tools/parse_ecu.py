#!/usr/bin/env python3
"""
Chuyển Index của "English Collocations in Use" (bản text 1 cột, sạch)
thành file markdown collocations dạng:

    ## headword
    collocation 1
    collocation 2

Cách dùng:
    python3 tools/parse_ecu.py <input.txt> <output.md> [--keep-pages]

- Bỏ số trang mặc định; dùng --keep-pages để giữ ' (tr. 52)'.
- Ký tự '~' = từ chính, sẽ được thay bằng headword.
- Bỏ dòng header/footer kiểu '160 English Collocations in Use Advanced' và 'Index'.
"""
import re, sys

POS = ("noun", "verb", "adjective", "adverb", "adj", "adv")
# số trang ở cuối dòng: " 52", " 7, 57", " 1, 10, 30"
PAGES_RE = re.compile(r"\s+\d+(?:\s*,\s*\d+)*\s*$")
# header/footer của sách
JUNK_RE = re.compile(r"^\s*(?:\d+\s+)?English Collocations in Use.*$", re.I)


def split_pages(line):
    """Tách phần chữ và phần số trang. Trả (core, pages_str|None)."""
    m = PAGES_RE.search(line)
    if not m:
        return line.strip(), None
    core = line[: m.start()].strip()
    pages = re.sub(r"\s+", " ", m.group().strip())
    return core, pages


def sub_word(headword):
    """Từ dùng để thay '~' (bỏ đuôi POS nếu có)."""
    parts = headword.split()
    if len(parts) >= 2 and parts[-1].lower() in POS:
        return " ".join(parts[:-1])
    return headword


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    inp, outp = sys.argv[1], sys.argv[2]
    keep_pages = "--keep-pages" in sys.argv[3:]

    groups = {}          # headword -> list[str]
    order = []           # giữ thứ tự xuất hiện
    cur = None           # headword hiện tại (dạng hiển thị)
    cur_sub = None       # từ thay cho '~'

    def add(hw, colloc, pages):
        if hw not in groups:
            groups[hw] = []
            order.append(hw)
        if keep_pages and pages:
            colloc = f"{colloc}  (tr. {pages.lstrip()})"
        if colloc not in groups[hw]:
            groups[hw].append(colloc)

    with open(inp, encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or JUNK_RE.match(line) or line.lower() == "index":
                continue

            core, pages = split_pages(line)

            if "~" in line:
                # dòng con của headword hiện tại
                if cur is None:
                    continue
                colloc = re.sub(r"\s+", " ", core.replace("~", cur_sub)).strip()
                add(cur, colloc, pages)
            elif pages:
                # dòng collocation độc lập -> nhóm theo từ đầu
                hw = core.split()[0] if core.split() else core
                add(hw, core, pages)
            else:
                # headword thuần -> mở nhóm mới
                cur = core
                cur_sub = sub_word(core)
                if cur not in groups:
                    groups[cur] = []
                    order.append(cur)

    # xuất markdown (sắp theo alphabet, không phân biệt hoa thường)
    title = "# English Collocations in Use"
    lines_out = [title, ""]
    for hw in sorted(order, key=lambda s: s.lower()):
        cols = groups[hw]
        if not cols:
            continue
        lines_out.append(f"## {hw}")
        lines_out.extend(cols)
        lines_out.append("")

    with open(outp, "w", encoding="utf-8") as f:
        f.write("\n".join(lines_out).rstrip() + "\n")

    n_words = sum(1 for hw in order if groups[hw])
    n_cols = sum(len(groups[hw]) for hw in order)
    print(f"OK: {n_words} từ, {n_cols} collocation -> {outp}")


if __name__ == "__main__":
    main()
