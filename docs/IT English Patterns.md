# IT English Patterns — Speaking & Writing

> Mẫu câu tiếng Anh dùng trong môi trường IT quốc tế (team phân tán, khách hàng nước ngoài, code review, incident...), mức **professional**. Phần trong `[ngoặc vuông]` là chỗ thay nội dung của bạn; ví dụ điền sẵn để thấy ngữ cảnh thật.
>
> **Cách luyện:** mỗi ngày chọn 1 nhóm, đọc to từng câu với nội dung công việc thật của bạn, rồi dùng ngay trong stand-up / Slack / PR hôm đó. Nói được tự nhiên quan trọng hơn thuộc nhiều.

**Ký hiệu:** 🟢 thân mật (đồng nghiệp, Slack) · 🟣 trang trọng (khách hàng, sếp lớn, văn bản chính thức) · không đánh dấu = trung tính, dùng được hầu hết mọi nơi · ⭐ = nên học trước

---

# PHẦN 1 — SPEAKING

## 1. Daily stand-up

| # | Pattern | Ghi chú |
|---:|---|---|
| 1 | Yesterday I wrapped up **[the login refactor]**, and today I'm picking up **[the caching ticket]**. | Cấu trúc chuẩn: xong gì → làm gì |
| 2 | I'm still working on **[the migration script]** — should be done by **[end of day]**. | Việc chưa xong + mốc dự kiến |
| 3 | I made good progress on **[the API integration]**; the remaining piece is **[error handling]**. | Báo tiến độ, nêu phần còn lại |
| 4 | No blockers on my side. | Câu chốt quen thuộc |
| 5 | I'm blocked on **[the staging credentials]** — **[Anna]**, could you help me with that after the call? | Báo bị chặn + nhờ đích danh, xử lý sau họp |
| 6 | I'm waiting on **[the design team]** for **[the final mockups]**. | Phụ thuộc người khác |
| 7 | Quick heads-up: **[the deploy pipeline]** was flaky this morning, so keep an eye on it. | Cảnh báo nhanh cho cả team 🟢 |
| 8 | I spent most of yesterday **[chasing down a memory leak]**. | Giải thích vì sao chậm |
| 9 | That took longer than expected because **[the test data was inconsistent]**. | Lý do trễ, không đổ lỗi |
| 10 | I'll pair with **[Minh]** on **[the flaky test]** this afternoon. | Thông báo pair |
| 11 | Let's set up a separate time to dig into this. | Hẹn buổi riêng, không bàn sâu trong stand-up |
| 12 | Let's park that and discuss it after stand-up. | Giữ stand-up ngắn |
| 13 | I'm out tomorrow afternoon, so **[Lan]** will cover **[code reviews]**. | Báo vắng + người thay |
| 14 | Nothing new since yesterday — still heads-down on **[the report module]**. | Không có gì mới 🟢 |
| 15 | I'm about **[80%]** through **[the refactor]**; I'll open a PR **[tomorrow morning]**. | Tiến độ có số liệu |
| 16 | I need a second pair of eyes on **[my PR for the billing service]**. | Nhờ review |
| 17 | I'll be focusing on **[bug fixes]** for the rest of the sprint. | Trọng tâm sắp tới |
| 18 | One thing I want to flag: **[the API rate limit]** might affect **[our release]**. | Nêu rủi ro sớm |

## 2. Meetings — mở đầu, điều phối, kết thúc

| # | Pattern | Ghi chú |
|---:|---|---|
| 19 | Let's get started — I know everyone's busy, so I'll keep this short. | Mở họp |
| 20 | The goal of today's meeting is to **[agree on the rollout plan]**. | Nêu mục tiêu ngay đầu |
| 21 | We have three items on the agenda: **[A]**, **[B]**, and **[C]**. | Liệt kê agenda |
| 22 | Let's give it a minute for people to join. | Chờ người vào |
| 23 | Can everyone see my screen? | Share màn hình |
| 24 | Let me know if I'm going too fast. | Kiểm tra người nghe |
| 25 | Before we dive in, does anyone have anything urgent? | Hỏi việc gấp |
| 26 | **[Linh]**, would you like to kick things off? | Mời người bắt đầu |
| 27 | Sorry to interrupt, but I think we're getting off track. | Kéo về chủ đề |
| 28 | That's a great point, but let's come back to it at the end if we have time. | Hoãn chủ đề lạc |
| 29 | In the interest of time, let's move on to the next item. | Chuyển mục khi hết giờ |
| 30 | Can I jump in here for a second? | Xin chen vào lịch sự |
| 31 | Sorry, go ahead — you were saying? | Nhường lời khi nói đè |
| 32 | I'd like to hear from **[the QA side]** on this. | Mời nhóm khác phát biểu |
| 33 | We haven't heard from **[Huy]** yet — any thoughts? | Mời người im lặng |
| 34 | Just to build on what **[Sara]** said, **[we could also cache the results]**. | Tiếp ý người khác |
| 35 | Let's timebox this to **[five minutes]**. | Giới hạn thời gian |
| 36 | We're running out of time, so let's wrap up. | Sắp hết giờ |
| 37 | To sum up, we've agreed to **[ship behind a feature flag]**. | Tóm tắt quyết định |
| 38 | So the action items are: **[Nam]** will **[update the doc]**, and I'll **[set up the alerts]**. | Chốt việc + người phụ trách |
| 39 | Who's going to own this? | Hỏi người chịu trách nhiệm |
| 40 | Let's set a follow-up for **[Thursday]** to check progress. | Hẹn họp tiếp |
| 41 | I'll send out the notes and action items after the call. | Cam kết gửi biên bản |
| 42 | Thanks, everyone — that was really productive. | Kết họp |
| 43 | I think we can end a few minutes early. Thanks, all! | Kết sớm 🟢 |
| 44 | You're on mute. | Nhắc tắt mic |
| 45 | Your audio is breaking up — could you try turning off your video? | Âm thanh bị rè / đứt quãng |
| 46 | I think there's a bit of lag; I'll turn my camera off to save bandwidth. | Mạng yếu |
| 47 | I have a hard stop at **[3 p.m.]**. | Báo phải rời đúng giờ |
| 48 | I need to drop off a few minutes early. | Rời sớm |
| 49 | I can't make it to **[the 3 p.m. sync]** — could someone share the notes? | Không dự được họp |
| 50 | Is this meeting being recorded? I'd like to watch it later. | Hỏi có ghi hình |
| 51 | Let's do a quick poll before we decide. | Biểu quyết nhanh |
| 52 | Could we move the meeting **[an hour earlier]**? | Đổi giờ họp |

## 3. Hỏi lại & xác nhận hiểu đúng

| # | Pattern | Ghi chú |
|---:|---|---|
| 53 | Sorry, could you say that again? I didn't quite catch that. | Không nghe rõ |
| 54 | Could you elaborate on **[what you mean by "real-time"]**? | Xin giải thích thêm |
| 55 | Just to make sure I understand: you want **[the export to run nightly]**, right? | Diễn đạt lại để xác nhận ⭐ |
| 56 | I think we may be talking about different things: **[you mean the client, I mean the server]**. | Phát hiện hai bên đang hiểu khác nhau ⭐ |
| 57 | When you say **[“scalable”]**, do you mean **[more users]** or **[more data]**? | Làm rõ thuật ngữ mơ hồ |
| 58 | Could you give me an example? | Xin ví dụ |
| 59 | What does "done" look like for this ticket? | Hỏi definition of done |
| 60 | What's the expected behavior here? | Hỏi hành vi mong muốn |
| 61 | Is this a hard requirement or a nice-to-have? | Phân loại yêu cầu ⭐ |
| 62 | What's the deadline we're working toward? | Hỏi mốc |
| 63 | Who's the main stakeholder for this? | Hỏi bên liên quan chính (không nhất thiết là người ra quyết định) |
| 64 | Let me repeat that back to you to make sure I've got it right. | Trước khi tóm tắt lại |
| 65 | Am I right in thinking **[the old endpoint will stay live until Q3]**? | Xác nhận giả định |
| 66 | Sorry, I'm not familiar with **[that acronym]** — what does it stand for? | Hỏi từ viết tắt |
| 67 | Could you walk me through **[how the sync job works]**? | Xin giải thích từng bước |
| 68 | Could you share the link in the chat? | Xin link |
| 69 | Does that make sense? | Hỏi người nghe đã hiểu chưa (thay "Do you understand?") |
| 70 | Are we all on the same page? | Kiểm tra đồng thuận |
| 71 | What's the context behind this request? | Hỏi bối cảnh / lý do |
| 72 | What problem are we actually trying to solve? | Quay về vấn đề gốc ⭐ |
| 73 | Which matters more to you here: **[cost]** or **[speed]**? | Buộc làm rõ ưu tiên khi yêu cầu mơ hồ |
| 74 | Sorry, I lost you at **[the part about sharding]**. | Không theo kịp từ chỗ nào |
| 75 | Could you speak a little more slowly? I want to make sure I get this right. | Xin nói chậm — không có gì đáng ngại ⭐ |
| 76 | Could you type that in the chat? I want to get the name right. | Xin gõ tên riêng / thuật ngữ |
| 77 | I'll confirm this in writing after the call. | Chốt lại bằng văn bản ⭐ |

## 4. Nêu ý kiến · đồng ý · phản đối khéo

| # | Pattern | Ghi chú |
|---:|---|---|
| 78 | In my opinion, **[we should start with a monolith]**. | Ý kiến rõ ràng |
| 79 | From my perspective, **[the main risk is data loss]**. | Góc nhìn cá nhân |
| 80 | I'd lean towards **[option B]**, mainly because **[it's easier to roll back]**. | Nghiêng về phương án + lý do ⭐ |
| 81 | If it were up to me, I'd **[postpone the release]**. | Ý kiến cá nhân khi được hỏi; nói với sếp dễ nghe như phán xét quyết định |
| 82 | My gut feeling is that **[this will take longer than we think]**. | Linh cảm, chưa có số liệu |
| 83 | I see it slightly differently. | Mở đầu phản đối nhẹ ⭐ |
| 84 | I agree with you on **[the timeline]**, but I'm less sure about **[the scope]**. | Đồng ý một phần |
| 85 | That's a fair point. | Ghi nhận ý người khác |
| 86 | I couldn't agree more. | Đồng ý hoàn toàn |
| 87 | Exactly — that's what I was getting at. | Đồng ý mạnh 🟢 |
| 88 | I take your point, but **[the cost of migrating is high]**. | Ghi nhận rồi phản biện |
| 89 | I'm not sure I agree. Have we considered **[the impact on mobile users]**? | Phản đối bằng câu hỏi |
| 90 | I have some concerns about **[the security implications]**. | Nêu lo ngại |
| 91 | I'm with **[Sara]** on this. | Đứng về phía ý kiến của ai đó |
| 92 | Let me play devil's advocate for a second: **[what if traffic doubles?]** | Cố tình phản biện |
| 93 | I'm leaning against **[adding another dependency]**. | Nghiêng về phía không làm |
| 94 | That might work, but I'm worried about **[maintenance cost]**. | Chấp nhận có điều kiện |
| 95 | I'd push back a little on that. | Phản đối nhẹ, chuyên nghiệp |
| 96 | With respect, I think **[the data tells a different story]**. | Phản đối với người cấp cao 🟣 |
| 97 | We're not going to settle this today — let's each **[gather some data]** and reconvene. | Tạm dừng tranh luận không có kết quả (tránh "agree to disagree" — dễ nghe như bực bội) |
| 98 | Can we look at the numbers before we decide? | Đưa về dữ liệu |
| 99 | What would change your mind? | Tìm điểm thuyết phục |
| 100 | I'm on the fence about this. | Còn phân vân |
| 101 | Either option works for me. | Không phản đối |
| 102 | I'm happy to go with the team's decision. | Ủng hộ quyết định chung |
| 103 | I disagree, but I'll commit to it. | Không đồng ý nhưng vẫn làm hết mình (gốc văn hóa Amazon: "disagree and commit") |
| 104 | I don't have a strong opinion either way. | Không có ý kiến mạnh |

## 5. Từ chối · đàm phán scope · nói "không" chuyên nghiệp

| # | Pattern | Ghi chú |
|---:|---|---|
| 105 | I'd love to help, but I'm fully booked this sprint. | Từ chối khéo ⭐ |
| 106 | I can do that, but something else will have to give. What should I deprioritize? | Để người yêu cầu chọn đánh đổi ⭐ |
| 107 | That's not something we can commit to by **[Friday]**. | Không cam kết được mốc |
| 108 | We can do **[A]** by **[Friday]**, or **[A and B]** by **[next Wednesday]**. | Đưa phương án thay vì "không" |
| 109 | What if we ship a smaller version first and iterate? | Đề xuất MVP |
| 110 | Can we move this to the next sprint? | Dời sang sprint sau |
| 111 | That falls outside the current scope. | Ngoài phạm vi 🟣 |
| 112 | Adding this now would put **[the release date]** at risk. | Nêu hậu quả |
| 113 | I'm not the right person for this, but **[Mai]** knows that area well. | Chuyển đúng người |
| 114 | Let me check my bandwidth and get back to you by **[tomorrow]**. | Chưa nhận ngay |
| 115 | I don't want to overpromise, so let's say **[two weeks]**. | Không hứa quá sức |
| 116 | If we cut **[the reporting feature]**, we can still hit the deadline. | Cắt scope giữ deadline |
| 117 | That's a big change late in the cycle; I'd rather not risk it. | Từ chối thay đổi muộn |
| 118 | Could you help me understand the business impact so I can prioritize it? | Đòi lý do ưu tiên |
| 119 | I'll need **[a decision from product]** before I can start on this. | Điều kiện để bắt đầu |
| 120 | This is a one-way door, so I'd like more time to think it through. | Quyết định khó đảo ngược (thuật ngữ kiểu Amazon, không phải công ty nào cũng dùng) |
| 121 | I'm going to say no for now, but let's revisit it next quarter. | "Chưa", không phải "không bao giờ" |

## 6. Ước lượng · cam kết · nói về sự không chắc chắn

| # | Pattern | Ghi chú |
|---:|---|---|
| 122 | Is the scope clear enough to estimate? | Hỏi trước khi ước lượng |
| 123 | It's hard to say without looking at the code, but roughly **[a week]**. | Ước lượng có điều kiện |
| 124 | Ballpark estimate: **[two sprints]**. | Ước lượng thô 🟢 |
| 125 | I'd give it **[five story points]**, mostly because of **[the unknowns in the legacy code]**. | Planning poker + lý do |
| 126 | That's a rough estimate — I'll have a better idea after **[a spike]**. | Cần spike để chắc |
| 127 | Let me do some digging and come back with a proper estimate. | Hẹn ước lượng sau |
| 128 | Best case **[two days]**, worst case **[a week]**. | Khoảng ước lượng ⭐ |
| 129 | There are a lot of unknowns, so I'd add some buffer. | Thêm dự phòng |
| 130 | I'm fairly confident we can hit **[the 15th]**. | Khá tự tin sẽ kịp |
| 131 | That's a stretch, but we can try. | Khó, nhưng sẽ cố |
| 132 | It depends on **[whether the vendor API is stable]**. | Phụ thuộc yếu tố khác |
| 133 | As far as I know, **[nobody else uses that endpoint]**. | Theo hiểu biết hiện tại |
| 134 | I might be wrong, but I think **[the cron job runs at midnight UTC]**. | Hedging, giảm độ chắc chắn |
| 135 | I'd need to double-check, but I believe **[we're on Postgres 14]**. | Hứa kiểm tra lại |
| 136 | We're on track for **[Friday]**. | Đúng tiến độ |
| 137 | We're slightly behind schedule, but we can catch up. | Hơi trễ |
| 138 | This is going to slip by **[a couple of days]**. | Báo trễ ⭐ |
| 139 | Realistically, we're looking at **[end of next week]**. | Mốc thực tế |
| 140 | I'll commit to **[the backend part]**; **[the UI]** is a stretch goal. | Cam kết phần chắc + phần cố gắng |
| 141 | What's our capacity this sprint, given **[two people are on leave]**? | Tính năng lực trước khi cam kết |

## 7. Giải thích kỹ thuật · kiến trúc · thiết kế

| # | Pattern | Ghi chú |
|---:|---|---|
| 142 | Let me give you a high-level overview first, then we can go into the details. | Từ tổng quan → chi tiết ⭐ |
| 143 | At a high level, **[the service receives events, enriches them, and writes them to S3]**. | Mô tả luồng tổng quát |
| 144 | Basically, **[it's a queue sitting between the API and the workers]**. | Đơn giản hóa 🟢 |
| 145 | The way it works is: first **[...]**, then **[...]**, and finally **[...]**. | Mô tả tuần tự |
| 146 | The main reason we chose **[Kafka]** is **[ordering guarantees]**. | Lý do lựa chọn |
| 147 | The trade-off is **[higher latency]** in exchange for **[stronger consistency]**. | Nói về trade-off ⭐ |
| 148 | This component is responsible for **[authentication and rate limiting]**. | Vai trò thành phần |
| 149 | **[Service A]** talks to **[Service B]** over **[gRPC]**. | Quan hệ giữa service |
| 150 | Under the hood, **[it uses a Redis cache]**. | Bên trong hoạt động thế nào |
| 151 | The bottleneck is **[the database write path]**. | Điểm nghẽn |
| 152 | This approach scales well up to **[about 10k requests per second]**. | Giới hạn mở rộng |
| 153 | The downside of this design is **[tight coupling]**. | Nhược điểm |
| 154 | Think of it as **[a post office that sorts and forwards messages]**. | Ẩn dụ cho người non-tech ⭐ |
| 155 | That's a single point of failure. | Điểm lỗi duy nhất — hỏng là sập cả hệ thống |
| 156 | Let me draw this out — it'll be easier to follow. | Vẽ sơ đồ |
| 157 | I'll skip the details for now, but happy to go deeper if anyone's interested. | Bỏ chi tiết, mở cửa hỏi thêm |
| 158 | The key thing to remember is **[writes are idempotent]**. | Nhấn mạnh điểm chính |
| 159 | One thing that's not obvious is **[the retry logic lives in the client]**. | Điểm dễ bỏ sót |
| 160 | We went with **[Postgres]** over **[MongoDB]** because **[our data is highly relational]**. | So sánh lựa chọn |
| 161 | We considered **[a microservices approach]**, but it felt like overkill for our scale. | Phương án đã loại |
| 162 | This is a known limitation, and we have a ticket to address it. | Thừa nhận giới hạn |
| 163 | In terms of performance, **[p99 latency is under 200 milliseconds]**. | Số liệu hiệu năng |
| 164 | The source of truth for **[user data]** is **[the accounts service]**. | Nguồn dữ liệu chuẩn |
| 165 | It's backward compatible, so existing clients won't break. | Tương thích ngược |
| 166 | The system is eventually consistent, so **[reads may lag by a few seconds]**. | Nhất quán cuối cùng |
| 167 | We can scale this horizontally by **[adding more workers]**. | Mở rộng ngang |
| 168 | As a rule of thumb, **[keep functions under 50 lines]**. | Nguyên tắc kinh nghiệm |
| 169 | There's no silver bullet here. | Không có giải pháp thần kỳ |

## 8. Code review (nói) · pair programming

| # | Pattern | Ghi chú |
|---:|---|---|
| 170 | Do you want to drive, or should I? | Pair: ai cầm bàn phím 🟢 |
| 171 | Let me share my screen and walk you through the changes. | Dẫn qua code |
| 172 | Can you scroll up a bit? | Điều hướng khi xem code |
| 173 | What's the reasoning behind **[this extra check]**? | Hỏi lý do, không phán xét ⭐ |
| 174 | Have you thought about **[extracting this into a helper]**? | Gợi ý nhẹ nhàng |
| 175 | I wonder if we could simplify this by **[using a map instead]**. | Gợi ý mềm |
| 176 | This looks good to me overall — just a couple of small things. | Khen tổng thể trước |
| 177 | This part's a bit hard to follow; could we add a comment or rename it? | Góp ý readability |
| 178 | What happens if **[the list is empty]**? | Hỏi edge case ⭐ |
| 179 | Is this covered by tests? | Hỏi test |
| 180 | Let's try running it and see what happens. | Thử nghiệm |
| 181 | Hang on, I think there's a typo on line **[42]**. | Chỉ lỗi nhỏ 🟢 |
| 182 | Nice catch! | Khen phát hiện lỗi |
| 183 | Good call — that's much cleaner. | Khen quyết định |
| 184 | Let me think out loud for a second. | Nghĩ thành tiếng khi pair |
| 185 | Let's commit this and refactor later. | Ưu tiên chạy được trước 🟢 (đừng biến thành thói quen) |
| 186 | Should we write the test first? | Gợi ý TDD |

## 9. Debug · troubleshooting

| # | Pattern | Ghi chú |
|---:|---|---|
| 187 | I'm able to reproduce it on **[staging]**, but not locally. | Tái hiện lỗi ⭐ |
| 188 | I can't reproduce it. Do you have the steps? | Không tái hiện được |
| 189 | It seems to be environment-specific — **[it only fails on the ARM build agents]**. | Lỗi chỉ ở 1 môi trường ("works on my machine" là câu đùa, nói nghiêm túc nghe như chối) |
| 190 | It looks like **[the token expires before the request completes]**. | Giả thuyết nguyên nhân |
| 191 | Let's test one hypothesis at a time. | Kiểm tra từng giả thuyết |
| 192 | I've ruled out **[the network]** — the requests are reaching the server. | Đã loại trừ |
| 193 | I narrowed it down to **[the date-parsing function]**. | Khoanh vùng lỗi ⭐ |
| 194 | The logs show **[a timeout right after the deploy]**. | Dẫn chứng log |
| 195 | It started happening after **[yesterday's release]**. | Mốc bắt đầu lỗi |
| 196 | It only happens intermittently, which makes it hard to track down. | Lỗi chập chờn |
| 197 | Let's add some logging and see if it happens again. | Thêm log |
| 198 | Can you check whether **[the feature flag]** is on in that environment? | Nhờ kiểm tra |
| 199 | I tried **[clearing the cache]**, but no luck. | Đã thử nhưng không được 🟢 |
| 200 | That fixed it! | Báo đã sửa xong |
| 201 | The root cause was **[a missing index on the orders table]**. | Nguyên nhân gốc ⭐ |
| 202 | It's a workaround, not a proper fix. | Phân biệt workaround / fix |
| 203 | We should add a regression test so this doesn't come back. | Ngăn tái phát |
| 204 | Let's check the dashboards before we touch anything. | Xem số liệu trước khi hành động |
| 205 | I'm going to bisect the commits to find where it broke. | git bisect |

## 10. Incident · on-call

| # | Pattern | Ghi chú |
|---:|---|---|
| 206 | I'm declaring a **[P1]** incident: **[checkout is failing for all users]**. | Tuyên bố sự cố |
| 207 | I'll be incident commander; **[Phong]**, can you handle comms? | Phân vai khi xử lý sự cố |
| 208 | What's the customer impact? | Câu hỏi đầu tiên ⭐ |
| 209 | Roughly **[15%]** of requests are failing in **[the EU region]**. | Mô tả phạm vi ảnh hưởng |
| 210 | Let's focus on mitigation first; we'll dig into the root cause later. | Khôi phục trước |
| 211 | I'm rolling back to the previous version now. | Hành động đang làm |
| 212 | The fix is deployed and error rates are back to normal. | Đã khắc phục |
| 213 | We're monitoring closely to make sure it's stable. | Theo dõi tiếp |
| 214 | Next update in **[30 minutes]**. | Hẹn cập nhật |
| 215 | Who's on call this week? | Hỏi trực |
| 216 | I got paged at **[2 a.m.]** for **[a disk space alert]**. | Kể bị gọi trực 🟢 |
| 217 | It was a false alarm — **[the alert threshold is too sensitive]**. | Báo động giả |
| 218 | Let's write a blameless postmortem for this. | Đề xuất postmortem |
| 219 | What can we do to prevent this from happening again? | Phòng ngừa |
| 220 | Can we get more eyes on this? | Cần thêm người |
| 221 | I'm escalating this to **[the platform team]**. | Leo thang |
| 222 | We're declaring this resolved; I'll write up a summary. | Đóng sự cố |
| 223 | Can someone keep a timeline in the incident channel? | Ghi lại dòng thời gian |
| 224 | I'm handing over on-call to **[Duc]** — here's what's still open. | Bàn giao ca trực |

## 11. Nhờ giúp · đề nghị giúp

| # | Pattern | Ghi chú |
|---:|---|---|
| 225 | Do you have a minute? I'm stuck on something. | Mở lời nhờ giúp 🟢 |
| 226 | Could I pick your brain about **[Kubernetes networking]**? | Xin ý kiến chuyên môn 🟢 ⭐ |
| 227 | I've been stuck on this for **[an hour]**; I've already tried **[X and Y]**. | Nhờ giúp kèm những gì đã thử ⭐ |
| 228 | Would you mind taking a look at **[this error]** when you get a chance? | Nhờ không gấp |
| 229 | Is there any documentation on **[the deploy process]**? | Hỏi tài liệu |
| 230 | Who would be the best person to ask about **[billing]**? | Hỏi đúng người |
| 231 | I'd appreciate any pointers. | Xin gợi ý |
| 232 | Happy to help — what do you need? | Nhận lời 🟢 |
| 233 | Let me know if there's anything I can do. | Đề nghị giúp |
| 234 | I've got some time this afternoon if you want to pair on it. | Đề nghị pair |
| 235 | I've dealt with something similar before — want me to take a look? | Chia sẻ kinh nghiệm |
| 236 | Thanks, that really helped. I owe you one. | Cảm ơn 🟢 |
| 237 | Thanks for your time — I know you're busy. | Cảm ơn khi người kia bận |

## 12. Feedback · 1:1 với manager

| # | Pattern | Ghi chú |
|---:|---|---|
| 238 | Can I give you some feedback on **[the demo]**? | Xin phép góp ý ⭐ |
| 239 | What worked really well was **[how you handled the Q&A]**. | Khen cụ thể |
| 240 | One thing you could try next time is **[showing the numbers first]**. | Góp ý hướng tới tương lai |
| 241 | I noticed that **[the PR descriptions have been quite short]**, and it makes reviews slower. | Hành vi → tác động (SBI) |
| 242 | How do you think it went? | Để người kia tự đánh giá trước |
| 243 | Thanks for the feedback — that's really useful. | Nhận góp ý chuyên nghiệp |
| 244 | That's fair. I'll work on that. | Chấp nhận góp ý |
| 245 | What would you have done differently? | Để người kia tự rút kinh nghiệm |
| 246 | I'd like to get your feedback on how I'm doing. | Chủ động xin feedback |
| 247 | What would I need to demonstrate to get to **[the senior level]**? | Hỏi lộ trình thăng tiến ⭐ |
| 248 | I'd like to take on more ownership of **[the payments domain]**. | Xin thêm trách nhiệm |
| 249 | I'm interested in growing into **[a tech lead role]**. | Định hướng nghề nghiệp |
| 250 | I'm stretched pretty thin at the moment. | Báo đang quá tải, nói nhẹ nhàng |
| 251 | I'd like to talk about my workload. | Mở đầu đề tài khó |
| 252 | I'd like to discuss my compensation. | Bàn về lương 🟣 |
| 253 | Is there anything I could be doing better? | Hỏi điểm cần cải thiện |
| 254 | I really appreciate you **[taking the time to mentor me]**. | Cảm ơn sếp/mentor |
| 255 | Shout-out to **[Trang]** for **[jumping in on the outage last night]**. | Ghi nhận công đồng nghiệp 🟢 |

## 13. Thuyết trình · demo

| # | Pattern | Ghi chú |
|---:|---|---|
| 256 | Today I'm going to walk you through **[our new onboarding flow]**. | Mở đầu |
| 257 | By the end of this session, you'll **[know how to deploy with one command]**. | Nêu kết quả cho người nghe ⭐ |
| 258 | I'll talk for about **[15 minutes]**, then we'll have time for questions. | Cấu trúc thời gian |
| 259 | Feel free to interrupt if you have questions. | Mời hỏi bất cứ lúc nào |
| 260 | Let me set the context with a quick story from **[last quarter's outage]**. | Mở bài bằng một câu chuyện thật |
| 261 | Moving on to **[the results]**. | Chuyển phần |
| 262 | As you can see on this slide, **[latency dropped by 40%]**. | Dẫn slide |
| 263 | This is the part I'm most excited about. | Gây chú ý |
| 264 | Let me show you a quick demo. | Chuyển sang demo |
| 265 | Fingers crossed the demo gods are on our side. | Đùa nhẹ trước demo 🟢 |
| 266 | Okay, that didn't go as planned — let me try that again. | Demo lỗi, giữ bình tĩnh |
| 267 | Here's a recording in case the live demo doesn't cooperate. | Phương án dự phòng |
| 268 | To recap, **[we've reduced build time from 20 to 5 minutes]**. | Tóm tắt |
| 269 | The key takeaway is **[automate the boring parts first]**. | Thông điệp chính |
| 270 | That's all from me. Happy to take any questions. | Kết thúc + mời hỏi |
| 271 | That's a great question. | Câu đệm khi nhận câu hỏi (đừng lạm dụng) |
| 272 | I don't have that number in front of me, but I'll follow up after the session. | Không biết câu trả lời ⭐ |
| 273 | That's a bit outside the scope of today's talk, but let's chat afterwards. | Câu hỏi lạc đề |
| 274 | Did that answer your question? | Kiểm tra sau khi trả lời |

## 14. Khách hàng · stakeholder · người không chuyên kỹ thuật

| # | Pattern | Ghi chú |
|---:|---|---|
| 275 | Thanks for making the time to meet with us today. | Mở đầu với khách 🟣 |
| 276 | Could you tell us a bit about **[your current workflow]**? | Khai thác nhu cầu |
| 277 | What are the biggest pain points with **[the current system]**? | Hỏi điểm đau ⭐ |
| 278 | How do you measure success for this project? | Hỏi tiêu chí thành công |
| 279 | In plain terms, this means **[users will see their orders update instantly]**. | Dịch kỹ thuật sang ngôn ngữ kinh doanh ⭐ |
| 280 | From a business perspective, **[this reduces support tickets]**. | Góc độ kinh doanh |
| 281 | We recommend **[a phased rollout]** to minimize risk. | Khuyến nghị 🟣 |
| 282 | There are two options, each with pros and cons. | Trình bày lựa chọn |
| 283 | The short answer is yes; the longer answer is that it depends on **[data volume]**. | Trả lời ngắn + dài |
| 284 | I understand your frustration, and we're treating this as a top priority. | Khách bực bội 🟣 |
| 285 | I'll look into it and get back to you by **[end of day tomorrow]**. | Hứa phản hồi có mốc ⭐ |
| 286 | That's a great idea — let me check feasibility with the team. | Không hứa ngay |
| 287 | Let me make sure I set the right expectations: **[this won't be ready before May]**. | Quản lý kỳ vọng ⭐ |
| 288 | We'll need sign-off from your side before we proceed. | Cần phê duyệt |
| 289 | That would be a change request. | Yêu cầu nằm ngoài phạm vi đã thống nhất |
| 290 | We'll keep you posted on progress. | Hứa cập nhật |
| 291 | Is there anything else you'd like us to consider? | Hỏi thêm yêu cầu |
| 292 | We appreciate your patience. | Cảm ơn khách đã chờ 🟣 |

## 15. Small talk · gắn kết team remote

| # | Pattern | Ghi chú |
|---:|---|---|
| 293 | How's your week going so far? | Mở đầu cuộc gọi 🟢 |
| 294 | What time is it over there? | Team khác múi giờ |
| 295 | It must be late for you — thanks for joining. | Ghi nhận người ở múi giờ bất tiện ⭐ |
| 296 | Any plans for the weekend? | Small talk thứ Sáu |
| 297 | How was your weekend? | Small talk thứ Hai |
| 298 | Did you take any time off? | Hỏi về kỳ nghỉ |
| 299 | Welcome back! How was the trip? | Người đi nghỉ về |
| 300 | Congrats on **[the launch]** — that was a huge effort. | Chúc mừng |
| 301 | Welcome to the team! Let me know if you need anything. | Chào người mới |
| 302 | I'm based in **[Hanoi]**, so I'm **[seven hours ahead of]** you. | Giới thiệu múi giờ |
| 303 | Are you working from home today? | Hỏi chỗ làm |
| 304 | Sorry about the background noise. | Xin lỗi ồn |
| 305 | Let's grab a virtual coffee sometime. | Rủ trò chuyện 1-1 🟢 |
| 306 | Nice to finally put a face to the name! | Lần đầu gặp mặt |
| 307 | Have a good one! | Chào cuối ngày 🟢 |
| 308 | Enjoy the rest of your day. | Chào kết thúc |

## 16. Phỏng vấn xin việc (behavioral + technical)

| # | Pattern | Ghi chú |
|---:|---|---|
| 309 | I'm a backend engineer with **[five years]** of experience, mostly in **[fintech]**. | Giới thiệu bản thân, câu mở ⭐ |
| 310 | Most recently, I've been leading **[the migration of our payment system to the cloud]**. | Kinh nghiệm gần nhất |
| 311 | What I enjoy most is **[solving performance problems]**. | Điều mình đam mê |
| 312 | The situation was **[...]**; my task was **[...]**; so I **[...]**; as a result, **[...]**. | Khung STAR ⭐ |
| 313 | One example that comes to mind is **[when our main database ran out of disk space]**. | Mở đầu câu chuyện |
| 314 | My role in that project was **[designing the data pipeline]**. | Nêu vai trò cá nhân (dùng "I", không chỉ "we") |
| 315 | As a result, we **[cut infrastructure costs by 30%]**. | Kết quả định lượng ⭐ |
| 316 | In hindsight, I'd involve QA earlier next time. | Bài học rút ra |
| 317 | Can I take a moment to structure my answer? | Xin thời gian sắp xếp ý (phỏng vấn) |
| 318 | Before I start, can I ask a few clarifying questions? | Phỏng vấn system design ⭐ |
| 319 | Let me start with a simple solution and then optimize it. | Coding interview |
| 320 | The time complexity here is **[O(n log n)]** because of **[the sort]**. | Nói về độ phức tạp |
| 321 | I'm going to assume **[the input fits in memory]** — is that okay? | Nêu giả định |
| 322 | I haven't worked with **[Rust]** directly, but I've used **[Go]**, which has a similar **[concurrency model]**. | Thiếu kinh nghiệm nhưng có liên hệ ⭐ |
| 323 | My main strength is **[turning vague requirements into a clear plan]**. | Điểm mạnh |
| 324 | Something I'm working on is **[delegating more]**. | Điểm yếu (thật, đang cải thiện) |
| 325 | I'm looking for a role where I can **[have more impact on architecture]**. | Lý do tìm việc |
| 326 | What does a typical day look like for this role? | Hỏi nhà tuyển dụng |
| 327 | How does the team handle **[code reviews and on-call]**? | Hỏi quy trình |
| 328 | What would success look like in the first **[90 days]**? | Câu hỏi gây ấn tượng ⭐ |
| 329 | What are the biggest challenges the team is facing right now? | Hỏi thách thức |
| 330 | Based on my experience and the market, I'm looking for something in the range of **[X to Y]**. | Đàm phán lương — chỉ nêu con số khi được hỏi 🟣 |
| 331 | Thank you for your time — I really enjoyed the conversation. | Kết thúc phỏng vấn |

## 17. Mắc lỗi · xin lỗi · nhận trách nhiệm

| # | Pattern | Ghi chú |
|---:|---|---|
| 332 | That's on me — I **[merged it without running the full test suite]**. | Nhận lỗi thẳng thắn ⭐ |
| 333 | I dropped the ball on this one. | Nhận lỗi bỏ sót 🟢 |
| 334 | Sorry for the delay in getting back to you. | Trả lời chậm |
| 335 | I apologize for the inconvenience this caused. | Xin lỗi khách 🟣 |
| 336 | Here's what happened, and here's what I'm doing to fix it. | Giải thích + hành động ⭐ |
| 337 | To prevent a repeat, I've **[added a checklist to our release process]**. | Biện pháp cụ thể thay cho lời hứa suông "It won't happen again" |
| 338 | My mistake — I misread the requirements. | Lỗi nhỏ 🟢 |
| 339 | Thanks for catching that. | Cảm ơn người phát hiện lỗi mình |
| 340 | No worries, it happens to all of us. | Trấn an đồng nghiệp mắc lỗi 🟢 |
| 341 | Let's focus on fixing it rather than on who caused it. | Văn hóa không đổ lỗi |

## 18. Câu đệm · câu câu giờ · sửa lời khi nói

| # | Pattern | Ghi chú |
|---:|---|---|
| 342 | Let me think about that for a second. | Câu giờ tự nhiên ⭐ |
| 343 | How can I put this? | Tìm cách diễn đạt |
| 344 | What I mean is **[we need a single source of truth]**. | Diễn đạt lại ⭐ |
| 345 | Let me rephrase that. | Nói lại cho rõ |
| 346 | Sorry, I mean **[Tuesday]**, not **[Thursday]**. | Sửa lỗi nói nhầm |
| 347 | I'm blanking on the word — it's the thing that **[balances traffic across servers]**. | Quên từ, mô tả thay thế ⭐ |
| 348 | Where was I? Oh right, **[the database layer]**. | Mất mạch nói |
| 349 | To be honest, **[I haven't had time to look at it]**. | Thành thật |
| 350 | The thing is, **[the legacy system has no tests]**. | Nêu vấn đề cốt lõi 🟢 |
| 351 | Long story short, **[we had to roll back]**. | Nói ngắn gọn |
| 352 | Out of curiosity, **[why did we pick MongoDB originally?]** | Hỏi vì tò mò, không mang ý chất vấn |
| 353 | That said, **[it's still better than the old approach]**. | Tuy nhiên (mềm) |
| 354 | On the flip side, **[it adds operational overhead]**. | Mặt trái 🟢 |
| 355 | On top of that, **[the vendor is raising prices]**. | Thêm vào đó 🟢 |
| 356 | At the end of the day, **[the user experience is what matters]**. | Rốt cuộc |
| 357 | For what it's worth, **[I think it's a solid plan]**. | Ý kiến khiêm tốn |
| 358 | If I remember correctly, **[we tried that last year]**. | Theo trí nhớ |
| 359 | Correct me if I'm wrong, but **[isn't that service deprecated?]** | Hỏi khéo, mời sửa ⭐ |
| 360 | Bear with me for a second while I find the link. | Xin chờ chút |

## 19. Báo rủi ro · leo thang · nêu vấn đề sớm

| # | Pattern | Ghi chú |
|---:|---|---|
| 361 | I want to raise a potential risk early: **[the third-party SDK is end-of-life in June]**. | Báo rủi ro sớm ⭐ |
| 362 | This could become a problem if **[traffic grows as expected]**. | Rủi ro có điều kiện |
| 363 | I don't want to be alarmist, but **[our error budget is almost used up]**. | Cảnh báo không gây hoảng |
| 364 | If we don't address this now, it'll cost us more later. | Nợ kỹ thuật |
| 365 | We're accumulating a lot of tech debt in **[the checkout module]**. | Nói về tech debt |
| 366 | I think this needs a decision from someone above our level. | Cần cấp trên quyết |
| 367 | I've tried resolving it with **[the other team]**, but we're stuck, so I'm looping you in. | Leo thang có lý do ⭐ |
| 368 | What's the plan B if **[the vendor misses their deadline]**? | Phương án dự phòng |
| 369 | Just flagging this so it doesn't catch anyone by surprise. | Báo trước để không bất ngờ |
| 370 | We're at risk of missing **[the launch date]** unless **[we get another engineer]**. | Rủi ro + điều kiện giải quyết |

## 20. Ưu tiên · đánh đổi · ra quyết định

| # | Pattern | Ghi chú |
|---:|---|---|
| 371 | What's the priority here — speed or quality? | Hỏi ưu tiên |
| 372 | If we can only do one thing this sprint, it should be **[fixing the login bug]**. | Chọn một việc quan trọng nhất ⭐ |
| 373 | This is high impact, low effort, so let's do it first. | Ma trận impact/effort |
| 374 | That's a must-have for launch. | Bắt buộc phải có khi ra mắt |
| 375 | Let's not let perfect be the enemy of good. | Đủ tốt thì làm |
| 376 | What's the cost of doing nothing? | Chi phí của việc không làm ⭐ |
| 377 | Is this reversible? If so, let's just try it. | Quyết nhanh khi dễ đảo ngược |
| 378 | Let's go with **[option A]** for now and revisit in **[a month]**. | Quyết tạm thời |
| 379 | What would we need to see to change course? | Tiêu chí đổi hướng |
| 380 | Who has the final say on this? | Hỏi ai là người quyết cuối cùng ⭐ |
| 381 | Let's align on the goal before we debate the solution. | Thống nhất mục tiêu trước ⭐ |
| 382 | So the decision is **[to delay the launch by a week]**. Any objections? | Chốt quyết định |
| 383 | We'll cross that bridge when we come to it. | Chưa cần lo trước |
| 384 | Let's not over-engineer this. | Tránh làm phức tạp quá mức |
| 385 | This is a quick win. | Việc nhỏ, hiệu quả nhanh |

## 21. Làm việc khác múi giờ · bàn giao async

| # | Pattern | Ghi chú |
|---:|---|---|
| 386 | I'll hand over to **[the EU team]** at the end of my day; everything's in **[the ticket]**. | Bàn giao cuối ngày ⭐ |
| 387 | Here's where I left off: **[the migration is half done; step 3 is next]**. | Ghi chú bàn giao |
| 388 | Please don't wait for me — I'm offline until **[9 a.m. ICT tomorrow]**. | Báo giờ offline |
| 389 | Could you reply by your end of day so I can pick it up in my morning? | Tận dụng lệch múi giờ ⭐ |
| 390 | We're **[seven hours]** apart, so **[9 a.m.]** your time is **[4 p.m.]** for me. Does that work? | Chọn giờ họp chung |
| 391 | I'll record a short video walkthrough instead of scheduling a call. | Thay họp bằng video async |
| 392 | Overlap hours are **[2–5 p.m. my time]**, so let's keep sync meetings in that window. | Giờ trùng nhau giữa các múi |

## 22. Sprint planning · retrospective

| # | Pattern | Ghi chú |
|---:|---|---|
| 393 | Let's break this down into smaller pieces. | Chia nhỏ việc |
| 394 | That's too big for one sprint — can we split it? | Tách story quá lớn |
| 395 | Our velocity is about **[30 points]** per sprint. | Tốc độ team |
| 396 | Do we have enough information to start, or do we need a spike first? | Cần spike không |
| 397 | Let's add that to the backlog and refine it next week. | Đưa vào backlog |
| 398 | What went well this sprint, and what could we do better? | Câu hỏi retro ⭐ |
| 399 | One thing I'd like us to try next sprint is **[smaller PRs]**. | Đề xuất cải tiến |
| 400 | I'd like to propose an action item: **[set up a review rotation]**. | Đề xuất việc cụ thể từ retro |
| 401 | Did we follow through on last retro's action items? | Kiểm tra việc từ retro trước |

## 23. Kèm cặp junior · mentoring

| # | Pattern | Ghi chú |
|---:|---|---|
| 402 | What have you tried so far? | Câu hỏi đầu tiên khi junior hỏi ⭐ |
| 403 | Walk me through your thinking. | Hiểu cách suy nghĩ |
| 404 | Give it **[30 minutes]** on your own, and if you're still stuck, come find me. | Cân bằng tự học và hỏi |
| 405 | I'd rather you ask early than stay stuck for hours. | Khuyến khích hỏi sớm |
| 406 | Don't worry if this feels hard — it took me a while too. | Trấn an |
| 407 | That's a good instinct; let's build on it. | Khen hướng đúng |
| 408 | Here's how I'd approach it: **[start from the failing test]**. | Chia sẻ cách tiếp cận |
| 409 | Take a stab at it, and I'll review it with you. | Giao việc kèm hỗ trợ 🟢 |

## 24. Bảo mật · tuân thủ

| # | Pattern | Ghi chú |
|---:|---|---|
| 410 | Do we have sign-off from **[security]** for this? | Hỏi phê duyệt bảo mật |
| 411 | This is **[PII]**, so it needs to be **[encrypted at rest]**. | Dữ liệu cá nhân |
| 412 | Let's follow the principle of least privilege. | Quyền tối thiểu ⭐ |
| 413 | I found a possible vulnerability in **[the login endpoint]** — I'll report it privately. | Báo lỗ hổng đúng kênh |
| 414 | That key was exposed, so we need to rotate it immediately. | Đổi khóa bị lộ |
| 415 | Is this compliant with **[GDPR]**? | Hỏi tuân thủ |
| 416 | Please don't paste secrets in Slack — use **[the password manager]**. | Nhắc an toàn thông tin |

## 25. Dữ liệu · số liệu

| # | Pattern | Ghi chú |
|---:|---|---|
| 417 | What's the baseline we're comparing against? | Hỏi mốc so sánh ⭐ |
| 418 | That's within the margin of error. | Chênh lệch không đáng kể |
| 419 | The sample size is too small to draw conclusions. | Mẫu quá nhỏ |
| 420 | Correlation isn't causation — **[the spike could be seasonal]**. | Tương quan ≠ nhân quả |
| 421 | Let's A/B test it before rolling it out to everyone. | Đề xuất A/B test |
| 422 | How are we going to measure whether this worked? | Hỏi cách đo thành công |

## 26. Làm việc với vendor · đối tác

| # | Pattern | Ghi chú |
|---:|---|---|
| 423 | Could you send us a formal quote? | Xin báo giá 🟣 |
| 424 | What's covered under the SLA? | Hỏi cam kết dịch vụ |
| 425 | What uptime do you guarantee, and what happens if you miss it? | Hỏi cam kết uptime + đền bù |
| 426 | If we commit to **[a one-year contract]**, is there any flexibility on price? | Đàm phán giá 🟣 |
| 427 | We'd like to run a proof of concept before signing. | Xin thử nghiệm trước |

## 27. Khi bạn là người phỏng vấn

| # | Pattern | Ghi chú |
|---:|---|---|
| 428 | Could you walk me through your resume? | Mở đầu phỏng vấn |
| 429 | Tell me about a time when **[you disagreed with a teammate]**. | Câu hỏi behavioral |
| 430 | How would you approach **[designing a rate limiter]**? | Câu hỏi system design |
| 431 | Take your time — thinking out loud is totally fine. | Giúp ứng viên bớt căng thẳng |
| 432 | Do you have any questions for us? | Kết thúc phỏng vấn |

## 28. Xử lý mâu thuẫn

| # | Pattern | Ghi chú |
|---:|---|---|
| 433 | I want to make sure we're not talking past each other. | Hai người nói không gặp nhau |
| 434 | I felt **[frustrated]** when **[my PR sat for a week]**. Can we talk about how to avoid that? | Nói cảm xúc + đề nghị giải pháp ⭐ |
| 435 | Let's assume good intent here. | Giả định thiện chí |
| 436 | I'd like to understand your side of this. | Lắng nghe phía bên kia |
| 437 | What would a good outcome look like for you? | Tìm điểm chung |

---

# PHẦN 2 — WRITING

## 29. Slack / Teams (giao tiếp không đồng bộ)

| # | Pattern | Ghi chú |
|---:|---|---|
| 438 | Hi **[Hana]**, quick question about **[the deploy script]**: **[does it run migrations automatically?]** | Chào + câu hỏi trong cùng tin nhắn (đừng chỉ gõ "Hi") ⭐ |
| 439 | Can you unblock me on **[the DB permissions]**? | Nhờ gỡ việc đang chặn mình |
| 440 | Thanks for the heads-up! | Cảm ơn đã báo trước 🟢 |
| 441 | FYI: **[staging will be down from 2–3 p.m. UTC for maintenance]**. | Thông báo ngắn |
| 442 | I'll be heads-down until **[noon]** — ping me only if it's urgent. | Báo đang tập trung, hạn chế làm phiền |
| 443 | Looping in **[@Khoa]**, who owns **[the auth service]**. | Kéo người liên quan vào |
| 444 | Tagging **[@Lan]** since you worked on **[the search API]** — does this look expected? | Tag người có chuyên môn liên quan |
| 445 | Bumping this in case it got buried. | Nhắc lại tin nhắn trôi ⭐ |
| 446 | Just following up on this — any update? | Hỏi tiến độ ("Just" làm câu mềm hơn) |
| 447 | Thanks! Taking a look now. | Xác nhận đang xử lý 🟢 |
| 448 | On it. | Nhận việc cực ngắn 🟢 |
| 449 | Done ✅ Let me know if anything looks off. | Báo xong |
| 450 | I'll get back to you on this by **[EOD]**. | Hẹn trả lời |
| 451 | Let's move this to a thread to keep the channel clean. | Dọn kênh |
| 452 | Could we hop on a quick call? It'll be faster than typing. | Chuyển sang gọi ⭐ |
| 453 | Sorry for the wall of text — TL;DR: **[the bug is in the client, not the API]**. | Tin dài + tóm tắt |
| 454 | I'm OOO **[Friday]**; ping **[Duc]** if anything urgent comes up. | Báo nghỉ |
| 455 | Signing off for the day — I'll pick this up tomorrow morning. | Kết thúc ngày làm |
| 456 | Context: **[...]**. Problem: **[...]**. Ask: **[...]**. | Khung tin nhắn nhờ việc rõ ràng ⭐ |
| 457 | +1 to what **[Minh]** said. | Đồng ý ngắn 🟢 |
| 458 | Great work on this, team! 🎉 | Khen chung |
| 459 | Sorry, wrong thread — please ignore! | Gửi nhầm chỗ 🟢 |
| 460 | Ping me when **[the build is green]**. | Nhờ báo khi xong |

## 30. Email công việc

| # | Pattern | Ghi chú |
|---:|---|---|
| 461 | Hi **[Mark]**, I hope you're doing well. | Mở đầu thân thiện (không lạm dụng) |
| 462 | I'm writing about **[the API integration timeline]**. | Nêu mục đích ⭐ |
| 463 | I'm writing to follow up on **[our call last Tuesday]**. | Email follow-up |
| 464 | Thank you for your quick response. | Cảm ơn phản hồi nhanh |
| 465 | Thanks for flagging this. | Cảm ơn người báo vấn đề |
| 466 | I've attached **[the logs]** for reference. | Đính kèm |
| 467 | Could you please confirm **[whether the 15th still works for you]**? | Đề nghị xác nhận |
| 468 | I'd appreciate it if you could **[send the API spec by Friday]**. | Yêu cầu lịch sự 🟣 |
| 469 | Would it be possible to **[extend the deadline by one week]**? | Xin điều chỉnh 🟣 |
| 470 | Just a gentle reminder that **[the invoice is due on Monday]**. | Nhắc khéo ⭐ |
| 471 | As discussed, **[we'll start the pilot on May 2]**. | Dẫn lại điều đã bàn |
| 472 | To clarify, **[the price covers maintenance for 12 months]**. | Làm rõ |
| 473 | Please note that **[the old endpoint will be removed on June 1]**. | Lưu ý quan trọng |
| 474 | Unfortunately, **[we won't be able to meet the original deadline]**. | Báo tin xấu |
| 475 | I'm happy to jump on a call if that's easier. | Đề nghị gọi |
| 476 | Let me know if you have any questions. | Kết thư |
| 477 | Please don't hesitate to reach out if you need anything else. | Kết thư 🟣 |
| 478 | Looking forward to hearing from you. | Chờ hồi âm |
| 479 | Thanks in advance for your help. | Cảm ơn trước |
| 480 | Best regards, / Best, / Thanks, / Cheers, | Ký tên: trang trọng → thân mật (*Cheers* phổ biến ở Anh/Úc hơn Mỹ) |
| 481 | Adding **[Linh]** (cc) for visibility. | Thêm người vào email |
| 482 | Moving **[Tom]** to bcc to save his inbox. | Chuyển người ra bcc |
| 483 | Sorry, I missed this message — catching up now. | Lỡ tin nhắn |
| 484 | I'm currently out of the office with limited access to email. I'll be back on **[March 10]**. | Thư tự động |
| 485 | Any update on the ETA? | Hỏi thời gian dự kiến (khách/đối tác) |

## 31. Pull request · code review comment

| # | Pattern | Ghi chú |
|---:|---|---|
| 486 | **What:** **[Adds retry logic to the payment client]**. **Why:** **[Transient 503s were causing failed orders]**. | Mô tả PR: what/why ⭐ |
| 487 | **How to test:** 1. **[...]** 2. **[...]** | Hướng dẫn test |
| 488 | This PR is a follow-up to **[#123]**. | Liên kết PR trước |
| 489 | Closes **[#456]**. | Tự đóng issue |
| 490 | This is a draft — not ready for review yet. | PR nháp |
| 491 | I'd especially appreciate feedback on **[the caching strategy]**. | Chỉ chỗ cần review kỹ ⭐ |
| 492 | Out of scope for this PR: **[refactoring the old handlers]**. | Ghi rõ không làm |
| 493 | **nit:** **[extra blank line here]**. | Góp ý vụn vặt, không bắt buộc ⭐ |
| 494 | **suggestion:** Consider **[using `Optional` here]** to make the null case explicit. | Đề xuất (Conventional Comments) |
| 495 | **question:** Why do we need **[this timeout]**? | Câu hỏi thật, không phải chê |
| 496 | **issue:** This will break if **[the user has no email]**. | Vấn đề cần sửa |
| 497 | **blocking:** **[This exposes the API key in the logs]**. | Bắt buộc sửa trước khi merge |
| 498 | Feel free to push back if you disagree with my comment. | Mời người được review phản biện |
| 499 | Could we add a test for **[the empty-cart case]**? | Xin thêm test |
| 500 | **thought:** Down the line, we might want to **[split this module]**. | Ý tưởng cho tương lai, không cần làm trong PR này |
| 501 | Nice! This is much easier to read. | Khen trong review |
| 502 | LGTM 👍 | Looks good to me — duyệt 🟢 |
| 503 | Approved with minor comments — feel free to merge once addressed. | Duyệt có điều kiện |
| 504 | Good catch, fixed in **[abc123]**. | Trả lời review: đã sửa ⭐ |
| 505 | Done. | Trả lời review ngắn |
| 506 | I'd prefer to keep it as is, because **[it matches the existing pattern]**. Happy to discuss. | Không đồng ý review, lịch sự ⭐ |
| 507 | Good point — I'll address that in a follow-up PR. | Hoãn sang PR sau |
| 508 | Re-requesting review after the changes. | Nhờ review lại |

## 32. Ticket · bug report · user story

| # | Pattern | Ghi chú |
|---:|---|---|
| 509 | **Steps to reproduce:** 1. **[...]** 2. **[...]** 3. **[...]** | Bug report ⭐ |
| 510 | **Expected:** **[the order is saved]**. **Actual:** **[a 500 error is returned]**. | Kỳ vọng vs thực tế ⭐ |
| 511 | **Environment:** **[Chrome 120, macOS, staging]**. | Môi trường |
| 512 | This happens consistently / intermittently (about **[1 in 10]** attempts). | Tần suất |
| 513 | **Impact:** **[Users can't complete checkout]**. | Mức ảnh hưởng |
| 514 | **Workaround:** **[Refreshing the page fixes it]**. | Cách tạm thời |
| 515 | As a **[store manager]**, I want to **[export sales data]** so that **[I can do my monthly report]**. | User story ⭐ |
| 516 | **Given** **[a logged-in user]**, **when** **[they click "Pay"]**, **then** **[the order is created]**. | Acceptance criteria (Gherkin) |
| 517 | **Acceptance criteria:** **[...]** | Tiêu chí nghiệm thu |
| 518 | **Definition of done:** code reviewed, tests passing, docs updated. | Định nghĩa hoàn thành |
| 519 | Blocked by **[#789]**. | Phụ thuộc ticket khác |
| 520 | Splitting this into smaller tickets: **[...]** | Tách ticket |
| 521 | Closing as won't fix — **[the feature is being removed]**. | Đóng ticket không sửa |
| 522 | Closing as a duplicate of **[#321]**. | Trùng ticket |
| 523 | Moving to the backlog until we have more information. | Đưa về backlog |

## 33. Tài liệu kỹ thuật · design doc · RFC

| # | Pattern | Ghi chú |
|---:|---|---|
| 524 | **Summary:** This document proposes **[moving session storage from Redis to DynamoDB]**. | Câu mở RFC ⭐ |
| 525 | **Background:** Currently, **[...]**. This causes **[...]**. | Bối cảnh + vấn đề |
| 526 | **Goals:** **[...]** / **Non-goals:** **[...]** | Mục tiêu / ngoài phạm vi ⭐ |
| 527 | We propose **[...]** because **[...]**. | Đề xuất |
| 528 | **Alternatives considered:** **[...]** — rejected because **[...]**. | Phương án đã cân nhắc |
| 529 | **Open questions:** **[Who owns the migration?]** | Câu hỏi còn mở |
| 530 | **Risks and mitigations:** **[...]** | Rủi ro + cách giảm |
| 531 | This service exposes **[a REST API]** for **[managing user profiles]**. | Câu mở README |
| 532 | **Prerequisites:** **[Docker 24+, Node 20]**. | Điều kiện cần |
| 533 | To get started, run **[`make setup`]**. | Hướng dẫn nhanh |
| 534 | **Note:** **[This command deletes all local data]**. | Lưu ý |
| 535 | **Warning:** **[Do not run this in production]**. | Cảnh báo |
| 536 | For more details, see **[the architecture doc]**. | Dẫn tài liệu khác |
| 537 | This section is a work in progress. | Đang viết dở |
| 538 | Feedback welcome — please leave comments by **[Friday]**. | Xin góp ý có hạn ⭐ |

## 34. Postmortem · incident report

| # | Pattern | Ghi chú |
|---:|---|---|
| 539 | On **[March 3]** between **[14:05 and 14:50 UTC]**, **[users were unable to log in]**. | Câu tóm tắt sự cố ⭐ |
| 540 | **Impact:** **[About 12,000 users]** were affected. | Ảnh hưởng |
| 541 | **Root cause:** **[An expired TLS certificate on the auth gateway]**. | Nguyên nhân gốc |
| 542 | **Detection:** The issue was detected by **[an automated alert]** at **[14:07]**. | Phát hiện |
| 543 | **Resolution:** We **[renewed the certificate and restarted the gateway]**. | Khắc phục |
| 544 | **Timeline:** **[14:05]** — **[...]** / **[14:12]** — **[...]** | Dòng thời gian |
| 545 | **What went well:** **[...]** / **What went wrong:** **[...]** | Rút kinh nghiệm |
| 546 | **Where we got lucky:** **[...]** | Điểm may mắn (giúp nhận ra lỗ hổng) |
| 547 | **Action items:** **[Automate certificate renewal]** — owner: **[@Huy]**, due **[March 17]**. | Việc cần làm có chủ & hạn ⭐ |
| 548 | This was not caused by any individual; it was a gap in our process. | Giọng blameless |

## 35. Status update · báo cáo tuần

| # | Pattern | Ghi chú |
|---:|---|---|
| 549 | **TL;DR:** **[Launch is still set for May 15; one open risk around payments]**. | Tóm tắt 1 dòng đầu báo cáo ⭐ |
| 550 | **Status:** 🟢 On track / 🟡 At risk / 🔴 Off track | Trạng thái màu |
| 551 | **Done this week:** **[...]** | Đã xong |
| 552 | **In progress:** **[...]** | Đang làm |
| 553 | **Next week:** **[...]** | Kế hoạch |
| 554 | **Blockers / Help needed:** **[...]** | Cần hỗ trợ ⭐ |
| 555 | **Key metrics:** **[conversion +3%, error rate 0.2%]** | Chỉ số |
| 556 | We shipped **[...]**, which **[reduced page load time by 1.5 s]**. | Nêu kết quả, không chỉ việc |
| 557 | No change from last week. | Không thay đổi |

## 36. Release notes · changelog · commit message

| # | Pattern | Ghi chú |
|---:|---|---|
| 558 | **Added:** **[Dark mode for the dashboard]**. | Tính năng mới |
| 559 | **Changed:** **[The export now includes timestamps]**. | Thay đổi |
| 560 | **Fixed:** **[An issue where invoices were sent twice]**. | Sửa lỗi |
| 561 | **Deprecated:** **[`/v1/users` will be removed in version 3.0]**. | Sắp bỏ |
| 562 | **Breaking change:** **[The `id` field is now a string]**. | Thay đổi phá vỡ tương thích ⭐ |
| 563 | `fix: handle empty cart in checkout` | Commit dạng Conventional Commits, câu mệnh lệnh |
| 564 | `feat(auth): add SSO login via Google` | Commit có scope |
| 565 | `refactor: extract price calculation into a service` | Commit refactor |
| 566 | `Revert "Add caching to search endpoint"` | Commit revert (mặc định của git) |

## 37. Từ nối & signposting khi viết lập luận

| # | Pattern | Ghi chú |
|---:|---|---|
| 567 | First, **[...]**. Second, **[...]**. Finally, **[...]**. | Liệt kê có thứ tự |
| 568 | As a result, **[...]** / Therefore, **[...]** | Kết quả |
| 569 | However, **[...]** / On the other hand, **[...]** | Tương phản |
| 570 | In addition, **[...]** / Also, **[...]** | Bổ sung (*Moreover* nghe khá cứng trong văn bản kỹ thuật) |
| 571 | For example, **[...]** / For instance, **[...]** | Ví dụ |
| 572 | In short, **[...]** / In summary, **[...]** | Tóm tắt |
| 573 | Given that **[the budget is fixed]**, **[we should reuse the existing service]**. | Vì (đã biết) ⭐ |
| 574 | Assuming **[traffic stays flat]**, **[one instance is enough]**. | Giả định |
| 575 | Unless **[we hear otherwise]**, **[we'll proceed on Monday]**. | Trừ khi ⭐ |
| 576 | While **[option A is cheaper]**, **[option B is faster to build]**. | So sánh đối lập (*Whereas* đứng đầu câu nghe như văn bản pháp lý) |
| 577 | This is primarily due to **[...]**. | Nguyên nhân chính |
| 578 | It's worth noting that **[...]**. | Đáng lưu ý |
| 579 | Going forward, **[...]**. | Từ nay về sau |

---

# PHẦN 3 — LỖI THƯỜNG GẶP CỦA NGƯỜI VIỆT TRONG MÔI TRƯỜNG IT

> **Phát âm — lỗi khiến người nghe khó hiểu nhất:** người Việt hay bỏ âm cuối. Hãy bật rõ âm cuối như *fixed* /fɪkst/, *deployed* /dɪˈplɔɪd/, *tests* /tests/, *API* /ˌeɪ.piːˈaɪ/. Phân biệt *ship* / *sheep*, *live* (/lɪv/ sống, /laɪv/ trực tiếp). Nhấn đúng trọng âm: *deVELopment*, *ARchitecture*, *deTERmine*, *cache* /kæʃ/ (không phải "cát-chê").

| # | ❌ Tránh | ✅ Nên dùng | Ghi chú |
|---:|---|---|---|
| 580 | discuss **about** the plan | discuss the plan | *discuss* không đi với *about* |
| 581 | explain **me** the issue | explain the issue **to me** | explain sth to sb |
| 582 | **open / close** the camera / mic | **turn on / turn off** the camera, **unmute / mute** | |
| 583 | Please **kindly** check | Could you please check…? | "please kindly" thừa, nghe lạ |
| 584 | I will **revert** to you | I'll **get back** to you | *revert* với nghĩa "phản hồi" là cách dùng của tiếng Anh Ấn Độ; người khác hiểu là "hoàn tác, quay về bản cũ" |
| 585 | Do you understand? | Does that make sense? / Is that clear? | "Do you understand?" nghe trịch thượng |
| 586 | I'm **agree** | I agree | |
| 587 | **Same same** / same with you | Same here. / Me too. | |
| 588 | **make** a meeting | **set up / schedule** a meeting | |
| 589 | **an** information / **a** feedback / **advices** | some information, some feedback, some advice (hoặc *a piece of …*) | Danh từ không đếm được (cả *equipment, software, knowledge*) |
| 590 | **a** feedback / feedbacks | some feedback / a piece of feedback | |
| 591 | The code **is not work** | The code **doesn't work** / **isn't working** | |
| 592 | **How to** fix this? | **How do I / How can we** fix this? | Được dùng làm tiêu đề / từ khóa tìm kiếm; khi hỏi người khác thì dùng câu đầy đủ |
| 593 | I **very** like it | I **really** like it | |
| 594 | **depend** the requirement | **depending on** the requirements | |
| 595 | **According to me**, … | **In my opinion / I think** … | |
| 596 | Please **send me** before Friday | Please send **it to me** before Friday | Thiếu tân ngữ |
| 597 | **Waiting your reply** | **Looking forward to** your reply / I look forward to **hearing from you** | |
| 598 | I'm **busy now**, call later | I'm **tied up** right now — can I call you back in an hour? | Lịch sự hơn |
| 599 | Ok, noted. (với khách) | Thanks, noted. / Thanks — I'll take that into account. | Tránh cụt lủn |
| 600 | **Sorry for** disturb you | Sorry to **bother** you / Sorry to **interrupt** | |
| 601 | The bug is **fixed done** | The bug **has been fixed** / is fixed | |
| 602 | We **have** a meeting **at** Monday | We have a meeting **on** Monday | on + ngày |
| 603 | Can you **share me** the link? | Can you **share the link with me**? | share sth with sb |
| 604 | **Remind** the deadline | **Remind** me **of** the deadline / a reminder **about** the deadline | |
| 605 | I **will** finish **it** **in** tomorrow | I'll finish it **tomorrow** / **by** tomorrow | không dùng "in tomorrow"; *by* = trước hạn |
| 606 | discuss / mention / emphasize **about** sth | discuss / mention / emphasize sth | Cả ba không cần *about* |
| 607 | He **work** on the backend | He **works** on the backend | Ngôi 3 số ít thêm -s |
| 608 | I **have fixed** it yesterday | I **fixed** it yesterday | Có mốc quá khứ → quá khứ đơn |
| 609 | Yesterday I **go** to the office | Yesterday I **went** to the office | Quên chia quá khứ |
| 610 | I **fix bug** in **API** | I fixed **a** bug in **the** API | Thiếu mạo từ — lỗi phổ biến nhất của người Việt |
| 611 | I'm **boring** in this meeting | I'm **bored** | *boring* = gây chán; *bored* = thấy chán |
| 612 | **Wait me** a minute | **Wait for me** / Give me a minute |  |
| 613 | Sorry **for late** | Sorry **I'm late** / Sorry **for being late** |  |
| 614 | I **make** a bug | I **introduced** a bug | Gây ra bug = introduce |
| 615 | **Thanks you** | **Thank you** / **Thanks** |  |
| 616 | Please **do the needful** | Please **take care of it** / Could you **handle this**? | Cách nói Ấn Độ, nhiều người không quen |
