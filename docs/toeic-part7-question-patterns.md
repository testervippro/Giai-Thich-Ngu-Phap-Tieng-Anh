# TOEIC ETS 2026 – Part 7: Pattern câu hỏi & kỹ thuật nối 2–3 đoạn (target 990)

**Dữ liệu:** toeic-ets-2026-reading (Test 1–10), 540 câu Part 7 (Q147–200 × 10 Test).
**Chi tiết từng câu:** xem [toeic-part7-per-question-analysis.md](toeic-part7-per-question-analysis.md).

## 0. Độ tin cậy của phân tích (đọc trước)

- File nguồn là OCR, **không có answer key**. Đáp án và cách gán dạng câu là do AI tự giải/tự phân loại: độ tin cậy cao 432 câu, vừa 96 câu, thấp 12 câu (tự đánh giá của AI, chưa kiểm chứng với đáp án ETS).
- Một số câu bị mất ảnh hoặc đoạn khi OCR (ví dụ T3-191, T4-187, T6-183, T8-193, T8-194); T5 bị đảo thứ tự Q198/Q199. Những câu này nên đối chiếu lại với sách.
- Số liệu "dạng câu" là phân loại thủ công của agent, có chỗ ranh giới mờ (ví dụ một câu vừa Inference vừa Cross-reference). Dùng như xu hướng, không phải thống kê chính thức của ETS.
- Phân bố đáp án AI giải: A 109, B 147, C 146, D 138, khá lệch A. Điều này có thể do AI giải chưa chuẩn hoặc do đề, mình chưa kiểm chứng.

## 1. Cấu trúc & phân bố

| Nhóm | Câu | Số câu (10 Test) | Ghi chú |
|---|---|---|---|
| Đoạn đơn (S) | 147–175 | 290 | 29 câu/Test, gồm 20 câu Insert-sentence, 20 Chat-intent, 19 NOT |
| Đoạn đôi (D) | 176–185 | 100 | 2 văn bản/bộ × 5 câu |
| Đoạn ba (T) | 186–200 | 150 | 3 văn bản/bộ × 5 câu |

Dạng câu theo nhóm (theo phân loại của agent, một câu có thể có 2 nhãn nên tổng có thể lệch):

| Dạng | S (290) | D (100) | T (150) |
|---|---|---|---|
| Detail | 95 | 38 | 46 |
| Inference | 45 | 24 | 43 |
| Cross-reference (2 hoặc 3 văn bản) | 0 | 30 | 59 |
| Purpose | 25 | 6 | 14 |
| Insert-sentence | 20 | 0 | 0 |
| Reason-Why | 16 | 3 | 7 |
| NOT-detail | 16 | 3 | 0 |
| Who-is (role/job) | 12 | 2 | 8 |
| Chat-intent | 20 (12 + 8) | 0 | 0 |
| Vocab-in-context | 12 | 12 | 0 |
| Time-Date-Deadline | 6 | 4 | 9 |
| Attachment/Form-data-match | 2 | 1 | 6 |
| Discrepancy/Conflict | 0 | 0 | 2 |

Nhận xét dữ liệu:
- Tổng cộng 95/250 câu ở bộ đôi/ba (38%) được gắn nhãn Cross-reference, Discrepancy hoặc Attachment. Nhiều câu Detail/Inference còn lại ở D/T thực chất cũng cần thông tin từ văn bản thứ hai.
- Vocab-in-context xuất hiện cả ở S (12) và D (12), gần như không có ở T.
- Chat-intent chỉ ở bộ đoạn đơn. Insert-sentence chỉ ở bộ đoạn đơn.

## 2. Công thức stem câu hỏi & cách trả lời (dạng đoạn đơn và chung)

| Dạng | Stem thật trong đề | Cách làm |
|---|---|---|
| Purpose | "What is the purpose of the notice / e-mail / article?", "What is one purpose of the e-mail?" | Đọc 1–2 câu đầu + câu cuối. "One purpose" nghĩa là có nhiều mục đích, đáp án là một trong số đó. |
| Detail | "According to the advertisement, …", "What is mentioned about …?", "What is indicated about …?" | Tìm từ khóa danh từ riêng trong stem, đáp án là paraphrase của câu chứa từ khóa. |
| Inference | "What most likely is Ms. Seang's job?", "What can be concluded about …?", "What is suggested about …?" | Không có câu nói thẳng. Gom 2 chi tiết rồi suy ra. Loại đáp án "quá mức" (absolute). |
| NOT-detail | "What is NOT offered to Radial Tunes subscribers?", "What does the job posting NOT mention?" | Gạch từng đáp án ứng với câu nào trong đoạn; đáp án là lựa chọn duy nhất không tìm được. Mất thời gian nhất ở dạng đơn. |
| Who-is | "According to the advertisement, who most likely is Ms. Navani?" | Tìm chữ ký, chức danh, nhiệm vụ của người đó, thường qua động từ hành động. |
| Chat-intent | "At 11:23 A.M., what does Ms. Seang imply when she writes, 'I have plenty to go around'?" | Đọc câu trước và câu sau dòng được trích. Câu trích gần như luôn có nghĩa khác nghĩa đen (đáp lại lời nhờ vả, từ chối lịch sự, đồng ý). |
| Insert-sentence | "In which of the positions marked [1], [2], [3], and [4] does the following sentence best belong?" | Tìm đại từ/liên từ trong câu cho sẵn (this, these, also, however, in addition) rồi khớp với câu đứng trước, và chi tiết mà câu đó bổ sung. |
| Vocab-in-context | "The word 'meet' in paragraph 1, line 8, is closest in meaning to" | Thay từng đáp án vào câu; đáp án đúng luôn là nghĩa theo ngữ cảnh, không phải nghĩa phổ biến nhất (T3-180: "meet the demand" = satisfy, không phải "reach" hay "encounter"). |
| Future-action | "What will happen on April 2?", "What does Ms. Correa ask members of the sales team to do?" | Tìm ngày/mốc thời gian hoặc động từ yêu cầu (please, must, should, be asked to). |
| Reason-Why | "Why did Ms. Barry begin an online chat with Mr. Kubelski?" | Lý do thường ở dòng đầu cuộc chat/email; ở bộ D/T có thể chỉ suy ra được. |

## 3. Nối 2–3 đoạn: 12 kiểu liên kết ("link key") gặp trong 10 Test

Ví dụ ghi theo mã Test–Câu. Xem chi tiết từng câu ở file phụ lục.

1. **Cùng thực thể, đặt tên khác nhau.** Văn bản A nhắc "the Business Association", văn bản B ghi tên đầy đủ. T1-183 (Red Hills Business District), T4-199/T4-200 (cùng tên Jerome Lennox; trụ sở ở Portsmouth), T6-195 ("associate" trong email 1 = "your partner" trong email 2), T9-180 (đường Broad Avenue), T10-177 (Exelrate).
2. **Chức danh ↔ tên người.** T9-193 (Rein thuộc Large Appliance Division, danh sách liên hệ cho biết Director là ai), T6-196 (khung giờ 1:00–2:00 "President" là bài của ông Harlington), T8-197 (Matt Grimm = tay trống), T5-199, T10-195.
3. **Khớp ngày/giờ giữa các văn bản.** T3-194 (2 PM thứ Sáu trong email khớp lịch), T7-189 (phòng 203, 1:45), T3-199 (đề cập tháng 8 → ngày 11/8 trong job listing), T8-188, T10-190.
4. **Mã hàng/số ↔ form/bảng/hóa đơn.** T1-195 (N3-GT → Great Thoughts → màu Blue), T8-200 (item 1056 → giá cao nhất), T10-200 (mục thứ 4 trong checklist), T2-195 (2 thùng → giảm giá chỉ khi trên 10 thùng), T7-194, T5-180 (mã CVY-XU → tên Mr. Buddy → "cùng giá").
5. **Điều kiện ở văn bản A, kết quả ở văn bản B.** T9-195 (Hillman chỉ họp nếu về kịp → lịch có tên ông), T7-200 (giữ lại phần thanh toán cho đến khi hàng đến → email sau báo hàng đến 20/8), T10-198.
6. **Quy tắc ở A áp vào trường hợp ở B.** T9-188 (nhà sách chỉ nhận bìa cứng/ấn bản đầu → email liệt kê từng loại sách, mỗi loại vi phạm một quy tắc), T6-188 (chỉ trồng cây bản địa ↔ có bụi oải hương ngoại lai), T10-193 (ký gửi giữ lại 15%), T3-179 (đơn ngày 20/8 rơi vào khoảng "từ 15/8 trở đi" → giao 10–12 tuần), T9-200, T7-193.
7. **Thay đổi/mâu thuẫn: văn bản sau ghi đè văn bản trước.** T4-189 (Trail Cleanup Day: 12/8 trong bài báo, 8/8 trên web), T6-200 (bữa tối đổi từ 6:00 sang 5:00), T1-192 (mẫu bị hoãn vì nền đen), T3-191 (lịch cũ vs email dời lịch).
8. **Đại từ/tham chiếu quay về văn bản khác.** "that service" (T2-188), "the article you sent" (T1-178, T5-188). Đọc cả câu chứa đại từ để biết văn bản đang tham chiếu đến gì.
9. **Từ chung (superordinate) ↔ từ cụ thể.** T5-184 (máy giặt/sấy ↔ household appliances), T9-176 (bát, muỗng, thớt ↔ kitchen items), T1-179 (khuyến mãi ↔ News page).
10. **Tính toán qua 2 văn bản.** T2-199 (giờ đi trong review + lịch tàu → giờ đến), T8-184 (gói dịch vụ → giá), T5-180.
11. **Điều kiện tiên quyết ẩn.** T9-199 (thẻ số 01562 cần đăng ký thiết bị với cơ quan hàng không dân dụng).
12. **Suy ra bằng loại trừ khi văn bản không nói thẳng.** T10-193, T8-190 (route mới của Winglite từ Arlford), T1-184 (lý do đổi lịch hòa nhạc phải suy ra từ email về khoan đường).

## 4. Bẫy thường gặp (rút từ cột "Paraphrase/trap" của 540 câu)

| Bẫy | Ví dụ |
|---|---|
| Đáp án là thông tin có thật nhưng ở văn bản sai | T1-188: các ngày thi công 19–20/12 là nhiễu, đáp án theo ngày trên form + "the very next day". |
| Thông tin cũ đã bị thay | T4-189, T6-200, T1-192 (chọn theo văn bản mới nhất). |
| Bẫy con số/đơn vị | T8-184 (giá vs giá trị), T3-198 (phí ban đầu 300 euro vs phí thường niên 150 euro), T5-180 ($359 vs $499). |
| Bẫy "người khác cùng công ty" | T5-198/199, T6-196 (Tanaka là COO chi nhánh, không phải người phát biểu). |
| Bẫy paraphrase hai bước | T1-194 (display rack = display stand), T6-198 (challenges → difficulties). |
| "NOT" phải kiểm tra qua cả các văn bản | T9-188 (mỗi đáp án bị loại bởi một quy tắc khác nhau). |
| Bẫy ngày/chỉ là ngày đăng | T3-199 (8/7 đăng bài, 21/7 hạn nộp, 4/8 báo kết quả, đáp án là 11/8). |
| Đáp án tuyệt đối/quá mức | Thường sai ở dạng Inference. |
| Văn bản đích chỉ "gợi ý" | T10-193, T8-190 (không có câu khẳng định trực tiếp). |

## 5. Chiến lược làm bài cho mục tiêu 990

Đây là khuyến nghị của mình dựa trên dữ liệu ở trên, không phải quy định của ETS.

1. **Bộ đôi/ba: đọc câu hỏi trước.** Với mỗi bộ, đọc 5 stem để biết cần tìm gì, đặc biệt các câu nhắc tên riêng, mã hàng, ngày giờ. Sau đó đọc văn bản 1 và tìm ngay "link key".
2. **Xác định link key trước khi đọc kỹ.** Trong 12 kiểu ở mục 3, kiểu 1–4 chiếm phần lớn: tên, chức danh, ngày giờ, mã số. Gạch chân chúng khi đọc.
3. **Luôn kiểm tra ngày của văn bản** khi có nhiều email/thông báo: văn bản mới hơn thường ghi đè.
4. **Câu NOT và Insert-sentence** tốn thời gian nhất ở nhóm đoạn đơn (39 câu trong 10 Test). Nếu thiếu giờ, để cuối bộ.
5. **Chat-intent (20 câu):** luôn đọc dòng trước và sau câu trích; đừng chọn nghĩa đen.
6. **Vocab-in-context:** thay từng đáp án vào câu, chú ý collocation (ví dụ meet the demand).
7. **Luyện paraphrase** với danh sách trong file phụ lục cột "Paraphrase/trap", và cụm từ trong toeic-ets-2026-reading-phrases.md.
8. **Ôn theo lỗi sai:** khi làm lại, ghi từng câu sai vào dạng câu (mục 2) và link key (mục 3) để biết mình yếu ở đâu.

## 6. Gợi ý bước tiếp theo

- Đối chiếu đáp án AI giải với đáp án chính thức trong sách, sau đó đếm lại tỷ lệ theo dạng câu.
- Lập bộ 30 "bộ đôi/ba" tiêu biểu (mỗi kiểu link key 2–3 bộ) để luyện nhận biết link key.
