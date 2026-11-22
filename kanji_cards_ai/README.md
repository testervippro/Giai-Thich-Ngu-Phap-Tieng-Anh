# Ảnh thẻ Kanji đã làm nét (AI) — bản lưu để cập nhật lại

Bộ ảnh đang dùng trên web nằm ở `docs/kanji-viewer/` (`kanji_p1`, `kanji_p2`, `kanji_jlpt`, `kanji_story`).
Thư mục này giữ một bản để lần sau sửa/thay lại cho tiện. Các ảnh ở đây là **liên kết cứng (hard link)** tới đúng file trong `docs/`
nên trên máy không tốn thêm dung lượng, git cũng chỉ lưu một lần.

| Thư mục | Nội dung |
|---|---|
| `cards/kanji_p1`, `cards/kanji_p2` | 2.097 thẻ đầy đủ, cỡ ×2 so với bản scan. **Nửa trên** (chữ Hán + tranh + câu chuyện) làm nét bằng Real-ESRGAN `x4plus-anime`, nửa dưới (cách đọc, bảng từ) chỉ phóng to thường. 51 thẻ (tranh chạm đường kẻ) làm nét cả thẻ. |
| `story/` | 2.097 ảnh **chỉ ô câu chuyện** (tranh + câu gợi nhớ), đã bỏ viền đen khung/góc bo. |
| `scripts/` | Script đã dùng (đường dẫn bên trong trỏ tới thư mục tạm lúc chạy — sửa lại `SRC`/`C` trước khi chạy). |
| `data/` | `story_meta.json` (khung ô câu chuyện từng thẻ), `ghost_scan2.json` (thẻ mặt sau khớp nhất), `deghosted.json` / `ghost_cards.json` (các thẻ bị hằn mặt sau). |

Ảnh thẻ **cũ** (trước khi làm nét) để ở `/kanji_cards_old/` — chỉ trên máy, đã cho vào `.gitignore` (bản cũ vẫn còn trong lịch sử git).

## Quy trình đã làm

1. **Làm nét** (`scripts/run.sh`, `run2.sh` + `prep2.py`, `conv2.py`): Real-ESRGAN `realesrgan-x4plus-anime` ×4 rồi thu về ×2, lưu WebP q84.
   Nửa trên cắt ở đường kẻ ngang dưới ô câu chuyện (`topcut.top_cut`); `redo_top.py` ghép nửa trên AI + nửa dưới phóng to thường.
2. **Cắt ô câu chuyện** (`story_final.py`): khung dò bằng `topcut.story_box` (đường kẻ dọc chạy suốt thẻ + đường kẻ ngang;
   mép trên = đoạn tối liền mạch dài nhất); 29 thẻ không dò được lấy tỉ lệ của ~30 thẻ gần nhất.
   Bỏ viền đen: `trim` (đường kẻ sát mép, cả hơi nghiêng), `clean_corners` (góc bo), `erase_edge_lines` (nét kẻ mảnh còn sót dọc mép).
3. **Hằn mặt sau trang** (25 thẻ 1421–1479): `find_ghost2.py` tìm thẻ in ở mặt sau (lật ngang, dò độ lệch);
   `gh_prep.py` xoá hằn trên ảnh gốc **trước** khi chạy AI, `gh_full.py` dựng lại thẻ đầy đủ, `clean_text.py` xoá vệt xám ở vùng chữ.
4. **Gemini**: 11 ảnh câu chuyện (1421, 1433–1437, 1446, 1447, 1450, 1451, 1458) thay bằng bản người dùng nhờ Gemini vẽ lại sạch hơn
   (10 ảnh từ ảnh ghép nhỏ được làm nét thêm bằng Real-ESRGAN). Lưu ý: bản Gemini của 1446 thiếu chữ “để” trong câu.

## Chạy lại AI

```
realesrgan-ncnn-vulkan -i <thư mục png vào> -o <thư mục ra> -n realesrgan-x4plus-anime -m <models> -f png
```
(Bản macOS: https://github.com/xinntao/Real-ESRGAN/releases — `realesrgan-ncnn-vulkan-20220424-macos.zip`.)
