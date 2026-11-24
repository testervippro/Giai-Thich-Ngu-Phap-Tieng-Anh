# Kho cụm từ & mẫu câu — nguồn dữ liệu

Mỗi file `tools/phrase_src/<tên>.py` là MỘT nguồn, có dạng:

```python
SOURCE = {"code": "e650", "name": "650+ English Phrases", "url": "../650-english-phrases-everyday-speaking.md"}   # url tính từ docs/tools/
def extract(root):            # root = thư mục gốc repo (pathlib.Path); trả về list[dict]
    return [{"t": "topic", "p": "I'm running late", "m": "Tôi sắp trễ", "e": "...", "ev": "...", "g": "Thời gian", "x": "", "ref": ""}, ...]
```

Bản ghi: `t` loại · `p` cụm/mẫu câu tiếng Anh (bắt buộc) · `m` nghĩa/giải thích tiếng Việt · `e` 1 câu ví dụ tiếng Anh ·
`ev` bản dịch câu ví dụ · `g` nhóm (chủ đề/tình huống/danh mục) · `x` ghi chú ngắn · `ref` mỏ neo/URL con trỏ về trang gốc.

Loại `t`: idiom · phrasal · collocation · fixed · pattern · structure · topic · daily · movie · situation · it
`tools/phrase_bank_build.py` gộp mọi nguồn -> `docs/tools/phrase-bank-data.js`.
