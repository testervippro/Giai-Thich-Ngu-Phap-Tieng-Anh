# Chuyển tài liệu Markdown thành audio

Biến `docs/MindMap-Full.md` (616k ký tự, 198 bảng HTML) thành MP3 nghe được —
khoảng **8,7 giờ**, cắt sẵn thành 7 track ~1 giờ.

Gồm hai bước tách rời, để bước nào sai thì sửa lại bước đó mà không phải render lại từ đầu:

| Bước | Script | Việc |
|---|---|---|
| 1 | `md_to_speech.py` | Markdown + bảng HTML → văn bản thuần đọc được, cắt thành track |
| 2 | `tts.py` | Văn bản → MP3 |

## Cài đặt

`edge-tts` đã được cài trong `.venv/` của repo (không commit). Nếu cần dựng lại:

```bash
python3 -m venv .venv && .venv/bin/pip install edge-tts
brew install ffmpeg          # đã có sẵn
```

Không muốn cài gì thì dùng `--engine say` với `python3` hệ thống (giọng Linh có sẵn trong macOS, chạy offline).

## Chạy

```bash
# 1. Markdown -> text
python3 tools/audio/md_to_speech.py docs/MindMap-Full.md -o build/audio-text

# 2. Text -> MP3
.venv/bin/python tools/audio/tts.py build/audio-text --mode bilingual -o build/audio -j 6
```

Đây đúng là lệnh đã dùng để tạo bộ 8,76 giờ trong `build/audio/`.

Đọc trước `build/audio-text/*.txt` rồi hãy render — sửa text rẻ hơn rất nhiều so với render lại vài giờ audio.

## Tuỳ chọn hay dùng

```bash
# Câu tiếng Anh đọc bằng giọng Anh, câu tiếng Việt bằng giọng Việt
python3 tools/audio/tts.py build/audio-text --mode bilingual

# Nghe nhanh hơn
python3 tools/audio/tts.py build/audio-text --rate "+20%"

# Offline, không cần mạng, không cần cài gì
python3 tools/audio/tts.py build/audio-text --engine say

# Chỉ đếm số đoạn / ước tính, không gọi TTS
python3 tools/audio/tts.py build/audio-text --dry-run

# Track dài hơn (mặc định ~45k ký tự ≈ 1 giờ)
python3 tools/audio/md_to_speech.py docs/MindMap-Full.md --max-chars 90000
# hoặc gộp tất cả vào một file
python3 tools/audio/md_to_speech.py docs/MindMap-Full.md --single
```

## Giọng

```bash
edge-tts --list-voices | grep vi-VN     # vi-VN-HoaiMyNeural (nữ), vi-VN-NamMinhNeural (nam)
say -v '?' | grep vi_VN                 # Linh
```

Đổi giọng bằng `--voice`, giọng tiếng Anh cho chế độ bilingual bằng `--en-voice`.

## Ghi chú kỹ thuật

- **Bảng chiếm 62% tài liệu.** Đọc thẳng bảng ra sẽ thành một chuỗi ô rời rạc không hiểu
  được, nên mỗi hàng được đổi thành câu có nhãn: `Giới từ: during. Ý nghĩa: … Ví dụ: …`
- **Cache theo nội dung.** Mỗi đoạn được lưu trong `build/audio-cache/` theo hash của
  (nội dung + giọng + tốc độ). Sửa một mục rồi chạy lại chỉ render đúng đoạn đã đổi.
- **Chống lỗi mạng.** Mỗi đoạn thử lại 4 lần; đứt giữa chừng thì chạy lại lệnh cũ, phần
  đã render nằm trong cache nên không mất.
- **`--mode bilingual` tách theo câu**, mảnh ngắn dưới 40 ký tự được gộp vào đoạn trước —
  đổi giọng vì vài chữ nghe rất vụn.
- **Nối file bằng cách encode lại** thay vì `-c copy`: nối thô nhiều MP3 hay sinh timestamp
  lệch, một số máy nghe nhạc sẽ nhảy hoặc hiện sai tổng thời lượng.
- **Timeout cho từng request là bắt buộc.** Websocket của dịch vụ thỉnh thoảng mở được nhưng
  không bao giờ gửi dữ liệu; không có `--timeout` thì cả mẻ render đứng vô hạn.
- **Đoạn dài hay bị trả về rỗng một cách ổn định** (retry vô ích). Mỗi request bị chặn ở
  1200 ký tự (`--req-chars`), và nếu vẫn hỏng thì tự cắt đôi ở ranh giới câu rồi thử lại
  từng nửa.
- **Đường dẫn ffmpeg tuyệt đối.** Tiến trình chạy nền có PATH tối giản, không có
  `/opt/homebrew/bin`, nên `shutil.which("ffmpeg")` trả về None và script chết ngay từ đầu.
