# Từ vựng theo sắc thái — nhóm từ nghĩa na ná nhau.
# Mỗi nhóm: (tiêu đề, [(từ, sắc thái / khi nào dùng, cấu trúc + collocation)], bẫy hay gặp, câu hỏi kiểu đề (câu, [A,B,C,D], đáp án, giải thích))

CATS = [
("🔧 Động từ dễ nhầm (TOEIC Part 5–6)", "Đề ETS/Hackers hay cho 4 động từ cùng nghĩa, chỉ khác **cấu trúc đi kèm** hoặc **tân ngữ**. Nhìn giới từ / tân ngữ sau chỗ trống trước khi nhìn nghĩa.", [

("affect · effect · influence · impact", [
 ("affect", "(v) tác động đến (trung tính)", "affect sb/sth (không giới từ)"),
 ("effect", "(n) kết quả, hiệu lực; (v, trang trọng) tạo ra, thực hiện", "have an effect on · take effect · effect change"),
 ("influence", "(v/n) ảnh hưởng dần dần đến suy nghĩ, hành vi", "influence sb/sth · have an influence on"),
 ("impact", "(n) tác động mạnh, rõ rệt; (v) = affect, hay gặp trong văn kinh doanh", "have an impact on · impact sth"),
], "affect là **động từ**, effect thường là **danh từ**. *take effect* (có hiệu lực) — không dùng *take affect*.",
("The new regulations will take ------- on January 1.", ["affect", "effect", "influence", "impact"], 1,
 "take effect = có hiệu lực (cụm cố định).")),

("rise · raise · arise · arouse", [
 ("rise", "(nội ĐT) tăng, đi lên — không có tân ngữ", "prices rise · rise by 5% · a rise in"),
 ("raise", "(ngoại ĐT) nâng, tăng; gây quỹ; nêu (vấn đề)", "raise prices / funds / a question / concerns"),
 ("arise", "(nội ĐT) nảy sinh (vấn đề, cơ hội)", "problems arise · arise from"),
 ("arouse", "(ngoại ĐT) khơi dậy (sự quan tâm, nghi ngờ)", "arouse interest / suspicion"),
], "Sau chỗ trống có **tân ngữ** → raise. Không có tân ngữ, nói về vấn đề → arise; về số lượng → rise.",
("Please contact us if any problems ------- during installation.", ["rise", "raise", "arise", "arouse"], 2,
 "Chủ ngữ là problems, không có tân ngữ → arise.")),

("lend · borrow · loan · rent · lease · hire", [
 ("lend", "cho mượn (người cho)", "lend sb sth · lend sth to sb"),
 ("borrow", "mượn (người nhận)", "borrow sth from sb"),
 ("loan", "(n) khoản vay; (v, Mỹ) cho vay", "take out a loan · on loan"),
 ("rent", "thuê/cho thuê (nhà, xe) theo thời gian, trả tiền định kỳ", "rent an apartment · rent out"),
 ("lease", "thuê dài hạn theo hợp đồng (văn phòng, thiết bị)", "sign a lease · lease equipment"),
 ("hire", "(Anh) thuê ngắn hạn đồ; (Mỹ/Anh) thuê người", "hire staff · hire a car (UK)"),
], "Hướng của đồ vật: lend = đi ra, borrow = đi vào. Văn phòng/thiết bị dài hạn theo hợp đồng → lease (rent cũng đúng nếu có trong đáp án).",
("The company decided to ------- the photocopiers rather than buy them.", ["lend", "borrow", "lease", "loan"], 2,
 "Thiết bị văn phòng, thuê theo hợp đồng → lease.")),

("say · tell · speak · talk · state · mention", [
 ("say", "nói ra lời (nội dung)", "say (that) · say sth to sb"),
 ("tell", "nói cho ai biết; kể; bảo ai làm gì", "tell sb sth · tell sb to V · tell the truth"),
 ("speak", "nói (ngôn ngữ, phát biểu), trang trọng hơn talk", "speak to/with sb · speak English · speak at a conference"),
 ("talk", "nói chuyện, trò chuyện", "talk to/with sb about sth"),
 ("state", "tuyên bố chính thức, ghi rõ (văn bản)", "state that · as stated in the contract"),
 ("mention", "nhắc đến ngắn gọn", "mention sth (to sb) — không có *about*"),
], "tell + người (tell me); say không đi trực tiếp với người (say to me). Ngoại lệ: tell the truth / a story / a joke. *mention about* là sai.",
("As ------- in the contract, payment is due within 30 days.", ["spoken", "told", "stated", "talked"], 2,
 "Văn bản hợp đồng → stated (ghi rõ). *As told* không dùng được.")),

("remind · remember · recall · memorize", [
 ("remind", "nhắc (người khác) nhớ", "remind sb to V · remind sb of/about sth · remind sb that"),
 ("remember", "nhớ (tự mình)", "remember to V (nhớ để làm) · remember V-ing (nhớ đã làm)"),
 ("recall", "hồi tưởng, nhớ lại (trang trọng); thu hồi (sản phẩm)", "recall V-ing · recall a product"),
 ("memorize", "học thuộc lòng", "memorize a password / a speech"),
], "Có **người + to V / that** → remind. Ngữ cảnh sản phẩm lỗi → recall (thu hồi) — nghĩa hay ra Part 7.",
("This is to ------- all staff that the office will close early on Friday.", ["remember", "remind", "recall", "memorize"], 1,
 "remind sb that ...")),

("prevent · avoid · prohibit · ban · forbid", [
 ("prevent", "ngăn (điều gì xảy ra)", "prevent sb/sth from V-ing"),
 ("avoid", "tránh (chủ ngữ tự tránh)", "avoid V-ing"),
 ("prohibit", "cấm (bằng luật/quy định)", "prohibit sb from V-ing · be prohibited"),
 ("ban", "cấm (chính thức, thường bởi cơ quan)", "ban sth · ban sb from V-ing"),
 ("forbid", "cấm (cá nhân, quy tắc)", "forbid sb to V / from V-ing"),
], "avoid + V-ing (không có *from*). prevent/prohibit + sb + **from** V-ing.",
("Smoking is strictly ------- on the premises.", ["avoided", "prohibited", "prevented", "forbidding"], 1,
 "strictly prohibited = nghiêm cấm. prevent cần 'from' + V-ing; avoid không hợp nghĩa (chủ thể tự tránh).")),

("allow · permit · let · enable · authorize", [
 ("allow", "cho phép (trung tính)", "allow sb to V · allow V-ing · be allowed to"),
 ("permit", "cho phép (trang trọng, quy định)", "permit sb to V · (n) permit = giấy phép"),
 ("let", "để cho (thân mật)", "let sb V (không to) — gần như không dùng bị động (trừ be let in/off)"),
 ("enable", "giúp có **khả năng** làm gì (công cụ, công nghệ)", "enable sb/sth to V"),
 ("authorize", "trao quyền chính thức", "authorize sb to V · authorized personnel"),
], "Chủ ngữ là **công cụ/phần mềm** → enable. *let sb to V* là sai.",
("The new app ------- users to track their orders in real time.", ["lets", "enables", "authorizes", "persuades"], 1,
 "Chủ ngữ là app, nói về khả năng → enables. lets không đi với to V.")),

("offer · provide · supply · furnish · equip", [
 ("offer", "đề nghị, mời (bên kia có thể từ chối)", "offer sb sth · offer to V"),
 ("provide", "cung cấp (thứ cần thiết)", "provide sb with sth · provide sth for/to sb"),
 ("supply", "cung ứng (số lượng lớn, đều đặn)", "supply sb with sth · supply sth to sb"),
 ("furnish", "trang bị nội thất; cung cấp (thông tin, trang trọng)", "furnish sb with information · a furnished apartment"),
 ("equip", "trang bị (thiết bị, kỹ năng)", "equip sb/sth with sth · well-equipped"),
], "provide **sb with** sth — không nói *provide sb sth*. offer thì được: offer sb sth.",
("The hotel will ------- all guests with a free city map.", ["offer", "provide", "grant", "give"], 1,
 "provide sb with sth. offer/grant/give không đi với with.")),

("refuse · reject · decline · deny · turn down", [
 ("refuse", "từ chối thẳng (làm/nhận)", "refuse to V · refuse an offer"),
 ("reject", "bác bỏ (đề xuất, đơn, hàng lỗi) sau xem xét", "reject a proposal / an application"),
 ("decline", "từ chối lịch sự; (nội ĐT) giảm", "decline an invitation · decline to comment · sales declined"),
 ("deny", "phủ nhận (sự thật); từ chối cấp (quyền)", "deny V-ing / that · deny sb access"),
 ("turn down", "từ chối (thân mật hơn)", "turn down an offer / a request"),
], "deny ≠ refuse: deny = nói *không phải sự thật*. Lịch sự với lời mời → decline.",
("Mr. Ford politely ------- the invitation to speak at the event.", ["denied", "declined", "delivered", "refused to"], 1,
 "politely + invitation → declined.")),

("assure · ensure · insure · reassure", [
 ("assure", "cam đoan với **ai**", "assure sb (that) · assure sb of sth"),
 ("ensure", "đảm bảo điều gì xảy ra", "ensure (that) · ensure sth"),
 ("insure", "mua bảo hiểm", "insure sth against sth"),
 ("reassure", "trấn an", "reassure sb (that)"),
], "Sau chỗ trống là **người** → assure. Là **mệnh đề/sự việc** → ensure.",
("We ------- you that your personal information will remain confidential.", ["ensure", "assure", "insure", "secure"], 1,
 "assure + you (người) + that.")),

("expect · anticipate · look forward to · await · wait for", [
 ("expect", "chờ đợi, dự kiến (có cơ sở)", "expect to V · expect sb to V · be expected to"),
 ("anticipate", "dự đoán trước (và chuẩn bị)", "anticipate V-ing · anticipate demand"),
 ("look forward to", "mong đợi (vui vẻ)", "look forward to V-ing / N"),
 ("await", "chờ đợi (trang trọng, không giới từ)", "await sth · await your reply"),
 ("wait for", "đợi", "wait for sb/sth · wait for sb to V"),
], "await **không** có *for*. look forward to **+ V-ing** (to là giới từ).",
("We look forward to ------- with you.", ["work", "working", "be working", "have worked"], 1,
 "look forward to + V-ing.")),

("reply · respond · answer", [
 ("reply", "trả lời (thư, tin nhắn)", "reply to sth/sb"),
 ("respond", "phản hồi; phản ứng (với tình huống)", "respond to sth · respond quickly"),
 ("answer", "trả lời (không giới từ)", "answer a question / the phone / inquiries · (answer to sb = chịu trách nhiệm trước ai)"),
], "reply/respond **+ to**; answer **không** + to.",
("Please ------- all customer inquiries within 24 hours.", ["reply", "respond", "answer", "talk"], 2,
 "Có tân ngữ trực tiếp, không giới từ → answer.")),

("attend · participate · join · take part · engage", [
 ("attend", "có mặt tại (sự kiện)", "attend a meeting (KHÔNG attend to = lo liệu)"),
 ("participate", "tham gia tích cực", "participate in"),
 ("take part", "tham gia (ít trang trọng hơn)", "take part in"),
 ("join", "gia nhập; đi cùng ai", "join a club / join sb for lunch"),
 ("engage", "tham gia sâu; thu hút", "engage in · engage customers"),
], "attend **không giới từ** (attend to = xử lý, chăm sóc). participate/take part/engage **in**.",
("More than 200 people ------- the seminar last week.", ["participated", "attended", "took part", "engaged"], 1,
 "Không có giới từ sau chỗ trống → attended.")),

("reach · arrive · get to · access", [
 ("reach", "đến nơi; đạt (mục tiêu); liên lạc được", "reach a place / an agreement / sb by phone"),
 ("arrive", "đến (nội ĐT)", "arrive at (điểm nhỏ) · arrive in (thành phố, nước)"),
 ("get to", "đến (thân mật)", "get to the office"),
 ("access", "truy cập, vào được", "access the database / the building"),
], "reach **không giới từ**; arrive **at/in**.",
("You can ------- me at 555-0123 after 3 P.M.", ["arrive", "reach", "join", "access"], 1,
 "reach sb (by phone) = liên lạc được.")),

("postpone · delay · cancel · suspend · put off · call off", [
 ("postpone", "dời sang thời gian sau (có kế hoạch)", "postpone sth until/to · postpone V-ing"),
 ("delay", "làm chậm / bị trễ (thường ngoài ý muốn)", "the flight was delayed · delay V-ing"),
 ("cancel", "hủy hẳn", "cancel an order / a meeting"),
 ("suspend", "tạm ngừng (dịch vụ, hoạt động)", "suspend service / operations"),
 ("put off / call off", "= postpone / = cancel (thân mật)", "put off V-ing · call off a strike"),
], "Thường gặp: dời có kế hoạch (until/to + mốc) → postpone; trễ ngoài ý muốn (by + thời lượng) → delay.",
("Due to the storm, all flights were ------- by at least two hours.", ["postponed", "delayed", "canceled", "suspended"], 1,
 "“by two hours” → bị trễ (delayed).")),

("reimburse · refund · compensate · repay", [
 ("reimburse", "hoàn lại **chi phí** đã bỏ ra (công tác)", "reimburse sb for expenses"),
 ("refund", "hoàn **tiền mua hàng**", "refund the purchase price · a full refund"),
 ("compensate", "bồi thường (tổn thất)", "compensate sb for loss/damage"),
 ("repay", "trả lại (nợ)", "repay a loan"),
], "Công tác phí → reimburse. Trả hàng → refund. Thiệt hại → compensate.",
("Employees will be ------- for travel expenses within two weeks.", ["refunded", "reimbursed", "repaid", "returned"], 1,
 "travel expenses → reimbursed.")),

("require · request · demand · ask", [
 ("require", "đòi hỏi (bắt buộc, quy định)", "require sb to V · be required to · require that sb (should) V"),
 ("request", "yêu cầu (lịch sự, trang trọng)", "request sth (from sb) · request that sb V · upon request"),
 ("demand", "đòi (mạnh, gay gắt)", "demand sth · demand to V · demand that"),
 ("ask", "hỏi, nhờ", "ask sb to V · ask for sth"),
], "request **không** có *for* (n thì có: a request for). Mệnh đề sau require/request/demand dùng **V nguyên mẫu** (giả định).",
("The client requested that the report ------- by Monday.", ["is sent", "be sent", "was sent", "sends"], 1,
 "request that + S + (should) be V3 — thức giả định.")),

("agree · consent · approve · accept", [
 ("agree", "đồng ý", "agree with sb · agree to a proposal · agree on terms · agree to V"),
 ("consent", "ưng thuận (cho phép, trang trọng)", "consent to sth · give consent"),
 ("approve", "phê duyệt (chính thức); tán thành", "approve a budget · approve of sb/sth"),
 ("accept", "chấp nhận (nhận lấy)", "accept an offer / responsibility"),
], "Cấp trên duyệt ngân sách → approve (không giới từ). Thỏa thuận chi tiết → agree **on**.",
("The board ------- the budget for next year.", ["agreeing", "consented", "approved", "accepting"], 2,
 "approve a budget = phê duyệt.")),

("fit · suit · match · go with", [
 ("fit", "vừa (kích cỡ); phù hợp (yêu cầu)", "The jacket fits (me) · fit the description"),
 ("suit", "hợp (người, phong cách, nhu cầu)", "suit sb · suit your needs"),
 ("match", "giống, khớp; đi đôi", "match the sample · matching shoes"),
 ("go with", "hợp nhau (đồ vật)", "This tie goes with that shirt"),
], "Kích cỡ → fit. Hợp với nhu cầu, sở thích → suit.",
("We offer a range of plans to ------- every budget.", ["fit in", "suit", "go with", "matching"], 1,
 "suit every budget/need = phù hợp.")),

("predict · forecast · project · estimate", [
 ("predict", "dự đoán (chung)", "predict that · predict an outcome"),
 ("forecast", "dự báo (thời tiết, kinh tế) bằng dữ liệu", "forecast growth / sales"),
 ("project", "dự phóng con số tương lai (thường bị động)", "projected revenue · be projected to V"),
 ("estimate", "ước tính (con số hiện tại/chi phí)", "estimate the cost · an estimated 500 people"),
], "Ước số người/chi phí hiện tại → estimated. Con số tương lai theo kế hoạch → projected.",
("Organizers ------- that about 3,000 visitors attended the festival.", ["predicted", "forecast", "estimated", "projected"], 2,
 "Con số của sự việc đã xảy ra → estimated (ước tính). predict/forecast/project nói về tương lai.")),

("suggest · recommend · propose · advise", [
 ("suggest", "gợi ý (nhẹ)", "suggest V-ing · suggest (that) sb (should) V — KHÔNG suggest sb to V"),
 ("recommend", "khuyến nghị (có chuyên môn)", "recommend V-ing · recommend that sb V · highly recommended"),
 ("propose", "đề xuất chính thức (kế hoạch); propose to V = dự định", "propose a plan · propose that"),
 ("advise", "khuyên (chuyên gia, cảnh báo)", "advise sb to V · be advised that · advise against V-ing"),
], "suggest / recommend **không** + sb + to V (đề Part 5 bẫy rất hay). Sau that dùng V nguyên mẫu (giả định).",
("The consultant recommended that the company ------- its prices.", ["lowers", "lower", "lowered", "lowering"], 1,
 "recommend that + S + (should) V nguyên mẫu → lower.")),

("consist of · comprise · include · contain · be composed of", [
 ("consist of", "gồm (toàn bộ các phần)", "The team consists of five members (không bị động)"),
 ("comprise", "gồm (trang trọng, không giới từ); bị động: be comprised of (hay gặp, nhưng bị coi là kém chuẩn)", "The board comprises seven directors"),
 ("be composed of / be made up of", "được cấu thành từ", "be composed of three parts"),
 ("include", "bao gồm (chỉ **một phần**)", "Prices include tax"),
 ("contain", "chứa (bên trong vật chứa, văn bản)", "The box contains ten items · the file contains errors"),
], "consist **of** nhưng comprise **không** of (chủ động). include = liệt kê một phần, không phải toàn bộ.",
("The committee ------- of representatives from each department.", ["comprises", "consists", "includes", "contains"], 1,
 "Có of phía sau → consists.")),

("change · alter · modify · adjust · revise · amend", [
 ("change", "thay đổi (chung)", ""),
 ("alter", "thay đổi một phần (quần áo, kế hoạch)", "alter a dress / the schedule"),
 ("modify", "điều chỉnh để cải thiện (thiết kế, kỹ thuật)", "modify the design"),
 ("adjust", "chỉnh nhẹ cho khớp; thích nghi", "adjust the settings · adjust to"),
 ("revise", "sửa đổi lại (văn bản, ước tính, kế hoạch)", "revised edition · revise estimates"),
 ("amend", "sửa đổi chính thức (luật, hợp đồng)", "amend the contract / constitution"),
], "Hợp đồng/luật → amend; bản thảo, số liệu dự báo → revise; thích nghi → adjust to.",
("Both parties must sign any document that ------- the original contract.", ["adjusts", "amends", "alters to", "revises to"], 1,
 "Sửa đổi chính thức hợp đồng → amends.")),

("improve · enhance · upgrade · boost · refine", [
 ("improve", "cải thiện (chung)", "improve efficiency"),
 ("enhance", "nâng cao (chất lượng, giá trị, hình ảnh) — vốn đã tốt", "enhance the customer experience"),
 ("upgrade", "nâng cấp (thiết bị, phần mềm, hạng ghế)", "upgrade to business class"),
 ("boost", "đẩy mạnh (doanh số, tinh thần) nhanh", "boost sales / morale"),
 ("refine", "tinh chỉnh từng chút", "refine the process"),
], "Phần mềm/phòng/ghế → upgrade; doanh số → boost.",
("Passengers can ------- to first class for an additional fee.", ["enhance", "upgrade", "boost", "refine"], 1,
 "upgrade to + hạng cao hơn.")),

("cause · lead to · result in · result from · contribute to · trigger", [
 ("cause", "gây ra (trực tiếp)", "cause damage / delays"),
 ("lead to / result in", "dẫn đến (kết quả)", "A leads to / results in B"),
 ("result from", "**là kết quả của** (ngược chiều!)", "B results from A"),
 ("contribute to", "góp phần (một trong nhiều nguyên nhân) — IELTS hedging", "contribute to climate change"),
 ("trigger", "châm ngòi, kích hoạt (đột ngột)", "trigger an alarm / a crisis"),
], "result **in** = gây ra; result **from** = do. Đây là bẫy chiều nhân–quả kinh điển.",
("The delay ------- from a shortage of materials.", ["caused", "resulted", "led", "triggered"], 1,
 "Chủ ngữ là kết quả + from → resulted from.")),

("obtain · acquire · gain · earn · win · receive", [
 ("obtain", "có được (bằng nỗ lực, thủ tục — trang trọng)", "obtain a permit / approval"),
 ("acquire", "thu được (kỹ năng); mua lại (công ty)", "acquire skills"),
 ("gain", "đạt thêm (kinh nghiệm, cân nặng, lợi thế)", "gain experience / access"),
 ("earn", "kiếm được (xứng đáng: tiền, uy tín)", "earn a salary / a reputation"),
 ("win", "giành được (giải, hợp đồng qua cạnh tranh)", "win an award / a contract"),
 ("receive", "nhận (bị động, người khác gửi)", "receive an email"),
], "Giấy phép → obtain; kinh nghiệm → gain; danh tiếng do nỗ lực → earn.",
("Applicants must ------- a permit before starting construction.", ["earn", "obtain", "win", "gain"], 1,
 "obtain a permit (qua thủ tục).")),
]),

("🪞 Tính từ cùng gốc, khác nghĩa (word-form trap)", "Đây là dạng Part 5 “4 đáp án chung một gốc từ” — không phải chọn từ loại mà chọn **nghĩa**.", [

("economic · economical", [
 ("economic", "thuộc về kinh tế", "economic growth / policy / crisis"),
 ("economical", "tiết kiệm (tiền, nhiên liệu)", "an economical car · economical with"),
], "Nghĩa “tiết kiệm” → economical. economic = thuộc kinh tế (hiếm: có lãi — not economic to run).",
("The new model is more ------- to run than its predecessor.", ["economic", "economical", "economics", "economy"], 1,
 "Tiết kiệm chi phí vận hành → economical.")),

("considerable · considerate", [
 ("considerable", "đáng kể (số lượng, mức độ)", "a considerable amount / increase"),
 ("considerate", "chu đáo, biết nghĩ cho người khác", "be considerate of others"),
], "Đi với số lượng → considerable.",
("The renovation will require a ------- investment.", ["considerate", "considerable", "considering", "considered"], 1,
 "investment (số tiền) → considerable.")),

("respective · respectful · respectable", [
 ("respective", "riêng của mỗi người/vật (tương ứng)", "their respective departments"),
 ("respectful", "tỏ ra tôn trọng", "be respectful of / to"),
 ("respectable", "đáng kính; khá, tươm tất", "a respectable firm · a respectable score"),
], "“their ------- offices” → respective.",
("After the meeting, the managers returned to their ------- offices.", ["respectful", "respectable", "respective", "respected"], 2,
 "Văn phòng riêng của mỗi người → respective.")),

("successful · successive", [
 ("successful", "thành công", "a successful launch"),
 ("successive", "liên tiếp", "for the third successive year"),
], "Đi với số thứ tự + year/quarter → successive (= consecutive).",
("Sales have increased for the fifth ------- year, without a single break.", ["successful", "successive", "success", "successfully"], 1,
 "five successive quarters = năm quý liên tiếp.")),

("reliable · reliant · dependable · dependent", [
 ("reliable / dependable", "đáng tin cậy", "a reliable supplier"),
 ("reliant / dependent", "phụ thuộc vào", "be reliant on / dependent on"),
], "Có **on** phía sau → reliant/dependent.",
("The region is heavily ------- on tourism.", ["reliable", "dependable", "dependent", "depending"], 2,
 "be dependent on.")),

("comprehensive · comprehensible", [
 ("comprehensive", "toàn diện, đầy đủ", "a comprehensive guide / insurance"),
 ("comprehensible", "dễ hiểu", "comprehensible to readers"),
], "Hướng dẫn/bảo hiểm/khảo sát → comprehensive.",
("The insurance plan provides ------- coverage for all employees.", ["comprehensible", "comprehensive", "comprehending", "comprehension"], 1,
 "coverage đầy đủ → comprehensive.")),

("sensible · sensitive", [
 ("sensible", "hợp lý, khôn ngoan", "a sensible decision"),
 ("sensitive", "nhạy cảm; (thông tin) mật", "sensitive skin / data · sensitive to"),
], "Thông tin cần bảo mật → sensitive information.",
("Do not store ------- information on shared drives.", ["sensible", "sensitive", "sensory", "sensational"], 1,
 "sensitive information = thông tin nhạy cảm.")),

("confident · confidential", [
 ("confident", "tự tin; tin chắc", "be confident that / of"),
 ("confidential", "bí mật, bảo mật", "confidential documents"),
], "Tài liệu → confidential.",
("All applications will be treated as strictly -------.", ["confident", "confidential", "confidence", "confidently"], 1,
 "strictly confidential (cụm cố định).")),

("informative · informed", [
 ("informative", "cung cấp nhiều thông tin (bài, buổi nói)", "an informative session"),
 ("informed", "có hiểu biết; được thông báo", "make an informed decision · keep sb informed"),
], "keep sb ------- → informed.",
("We will keep you ------- of any changes.", ["informative", "informed", "information", "informing"], 1,
 "keep sb informed = thông báo liên tục.")),

("industrial · industrious", [
 ("industrial", "thuộc công nghiệp", "an industrial zone"),
 ("industrious", "cần cù, chăm chỉ", "an industrious worker"),
], "Người → industrious.",
("She is known as an ------- and reliable employee.", ["industrial", "industrious", "industry", "industrialized"], 1,
 "Mô tả người → industrious.")),

("historic · historical", [
 ("historic", "mang tính lịch sử, quan trọng (đáng ghi nhớ)", "a historic building / moment"),
 ("historical", "thuộc về lịch sử, liên quan quá khứ", "historical records / novels"),
], "Thường phân biệt: historic = quan trọng, làm nên lịch sử; historical = thuộc về lịch sử, quá khứ.",
("It was a ------- victory, the team's first in 100 years.", ["historic", "historical", "history", "historian"], 0,
 "Chiến thắng làm nên lịch sử → historic.")),

("complementary · complimentary", [
 ("complementary", "bổ sung cho nhau", "complementary skills"),
 ("complimentary", "**miễn phí** (đồ tặng kèm); khen ngợi", "complimentary breakfast / tickets"),
], "TOEIC: complimentary = free — xuất hiện trong mọi đề khách sạn, sự kiện.",
("Guests receive a ------- breakfast every morning.", ["complementary", "complimentary", "compliment", "complement"], 1,
 "Bữa sáng miễn phí → complimentary.")),

("extensive · extended", [
 ("extensive", "rộng, nhiều (kinh nghiệm, thiệt hại, bộ sưu tập)", "extensive experience / research"),
 ("extended", "được kéo dài (thời gian)", "extended hours / warranty"),
], "Được kéo dài thêm (giờ, bảo hành, hạn) → extended; quy mô rộng, nhiều → extensive (cả extensive delays).",
("The store will have ------- hours during the holiday season.", ["extensive", "extended", "extending", "extension"], 1,
 "Giờ mở cửa kéo dài → extended.")),

("alternate · alternative", [
 ("alternate", "xen kẽ; (Mỹ) thay thế", "on alternate days"),
 ("alternative", "thay thế, lựa chọn khác", "an alternative route / energy"),
], "Lựa chọn khác → alternative (alternate cũng được ở Mỹ nhưng đề chuẩn chọn alternative).",
("Due to construction, drivers should use an ------- route.", ["alternative", "alternating", "alteration", "altered"], 0,
 "alternative route.")),

("continual · continuous", [
 ("continual", "lặp đi lặp lại (có ngắt quãng), thường gây khó chịu", "continual interruptions"),
 ("continuous", "liên tục không ngắt", "continuous improvement / flow"),
], "Phân biệt truyền thống (nhiều từ điển coi gần như nhau): không ngắt quãng → continuous.",
("The factory operates on a ------- 24-hour schedule.", ["continual", "continuous", "continued", "continuing"], 1,
 "Không ngắt → continuous.")),

("temporary · tentative · contemporary · temporal", [
 ("temporary", "tạm thời", "a temporary position"),
 ("tentative", "dự kiến, chưa chốt", "a tentative schedule / agreement"),
 ("contemporary", "đương đại; cùng thời", "contemporary art"),
 ("temporal", "thuộc thời gian (học thuật)", "temporal changes"),
], "Lịch chưa chốt → tentative (rất hay ra TOEIC).",
("The dates below are -------, so they may change.", ["temporary", "tentative", "contemporary", "temporal"], 1,
 "Chưa chốt, có thể đổi → tentative.")),

("valuable · invaluable · valueless · priceless", [
 ("valuable", "có giá trị", "valuable advice"),
 ("invaluable", "**vô giá**, cực kỳ hữu ích (không phải ‘không có giá trị’)", "invaluable support"),
 ("valueless / worthless", "không có giá trị", "a worthless coin"),
 ("priceless", "vô giá (đồ vật quý)", "a priceless painting"),
], "in- ở invaluable **không** mang nghĩa phủ định.",
("Your feedback has been ------- in improving our service.", ["valueless", "invaluable", "invalid", "worthless"], 1,
 "invaluable = cực kỳ hữu ích.")),

("eligible · available · capable · able", [
 ("eligible", "đủ điều kiện (theo quy định)", "eligible for a discount · eligible to V"),
 ("available", "có sẵn; rảnh", "available for/to sb"),
 ("capable", "có năng lực", "capable of V-ing"),
 ("able", "có thể", "able to V"),
], "Theo quy định/tiêu chuẩn → eligible. Đi với **of** → capable.",
("Members are ------- for a 10% discount.", ["capable", "able", "eligible", "possible"], 2,
 "eligible for a discount.")),

("responsible · liable · accountable", [
 ("responsible", "chịu trách nhiệm (công việc)", "responsible for V-ing/N"),
 ("liable", "chịu trách nhiệm pháp lý; dễ bị", "liable for damage · liable to change"),
 ("accountable", "phải giải trình (với ai)", "accountable to sb for sth"),
], "Ngữ cảnh pháp lý, thiệt hại → liable. Bổn phận công việc → responsible.",
("Drivers will be held legally ------- for any damage to the rental car.", ["responsive", "liable", "reliant", "reliable"], 1,
 "held legally liable for = chịu trách nhiệm pháp lý.")),

("timely · punctual · prompt", [
 ("timely", "kịp thời, đúng lúc (adj, không phải adv)", "in a timely manner · timely delivery"),
 ("punctual", "đúng giờ (người, tàu xe)", "a punctual employee"),
 ("prompt", "nhanh chóng, ngay lập tức", "a prompt reply · promptly"),
], "timely tận cùng -ly nhưng là **tính từ**: in a timely manner.",
("Thank you for your ------- response to our inquiry.", ["punctual", "prompt", "promptly", "punctually"], 1,
 "Phản hồi nhanh → prompt response.")),
]),

("🏷️ Danh từ cùng trường nghĩa", "Đề hay cho 4 danh từ đều “đúng nghĩa tiếng Việt” — chỉ một từ đúng **collocation** tiếng Anh.", [

("cost · price · fee · fare · charge · rate · toll · tuition · premium", [
 ("price", "giá bán của hàng hóa", "the price of a product"),
 ("cost", "chi phí phải bỏ ra (sản xuất, sinh hoạt)", "the cost of living / shipping costs"),
 ("fee", "phí dịch vụ chuyên môn, phí thành viên", "registration / membership / legal fee"),
 ("fare", "giá vé phương tiện công cộng", "bus / train / air fare"),
 ("charge", "khoản tính phí cho dịch vụ", "a service / delivery charge · free of charge"),
 ("rate", "mức giá theo đơn vị (giờ, đêm, lãi)", "hourly rate · room rate · interest rate"),
 ("toll", "phí cầu đường", "a toll road / bridge toll"),
 ("tuition", "học phí", "tuition fees"),
 ("premium", "phí bảo hiểm; khoản phụ trội", "insurance premium"),
], "Vé xe/tàu → fare; phí hội viên → fee; phòng khách sạn → rate.",
("Taxi ------- have risen sharply this year.", ["fees", "fares", "tolls", "premiums"], 1,
 "Giá cước phương tiện → fares.")),

("customer · client · patron · guest · passenger · consumer · clientele", [
 ("customer", "khách mua hàng", "regular customers"),
 ("client", "khách hàng dịch vụ chuyên môn (luật, ngân hàng, agency)", "a law firm's clients"),
 ("patron", "khách quen (nhà hàng, thư viện, rạp)", "library patrons"),
 ("guest", "khách khách sạn, khách mời", "hotel guests"),
 ("passenger", "hành khách", "airline passengers"),
 ("consumer", "người tiêu dùng (nói chung, kinh tế)", "consumer demand"),
 ("clientele", "tập khách hàng (danh từ tập hợp)", "a loyal clientele"),
], "Luật sư, kế toán, tư vấn → client.",
("The accounting firm serves over 300 corporate -------.", ["passengers", "clients", "patrons", "guests"], 1,
 "Dịch vụ chuyên môn → clients.")),

("job · work · occupation · profession · career · position · employment", [
 ("job", "một công việc cụ thể (đếm được)", "a full-time job"),
 ("work", "công việc nói chung (không đếm được)", "look for work · at work"),
 ("occupation", "nghề nghiệp (khai trên form)", "please state your occupation"),
 ("profession", "nghề chuyên môn (bằng cấp)", "the medical profession"),
 ("career", "sự nghiệp (cả quá trình)", "a career in finance"),
 ("position", "vị trí (trong công ty, tuyển dụng)", "apply for the position of"),
 ("employment", "việc làm (trang trọng); sự tuyển dụng", "employment opportunities"),
], "*a work* sai khi nghĩa là công việc (work không đếm được) — nhưng a work of art thì đúng.",
("She has had a long ------- in the hospitality industry.", ["job", "work", "career", "occupation"], 2,
 "Cả quá trình dài → career.")),

("schedule · agenda · itinerary · timetable · calendar", [
 ("schedule", "lịch trình, kế hoạch thời gian", "ahead of / behind schedule"),
 ("agenda", "chương trình nghị sự (cuộc họp)", "the first item on the agenda"),
 ("itinerary", "lịch trình chuyến đi", "travel itinerary"),
 ("timetable", "bảng giờ (tàu xe, lớp học)", "the train timetable"),
 ("calendar", "lịch; lịch sự kiện", "the events calendar"),
], "Cuộc họp → agenda; chuyến đi → itinerary.",
("Please review the ------- before the meeting begins.", ["itinerary", "agenda", "timetable", "calendar"], 1,
 "Cuộc họp → agenda.")),

("salary · wage · income · earnings · pension · allowance · bonus", [
 ("salary", "lương tháng/năm (văn phòng)", "an annual salary"),
 ("wage(s)", "lương theo giờ/tuần (lao động)", "the minimum wage"),
 ("income", "thu nhập (mọi nguồn)", "household income"),
 ("earnings", "tiền kiếm được; lợi nhuận công ty", "quarterly earnings"),
 ("pension", "lương hưu", "a retirement pension"),
 ("allowance", "phụ cấp", "a travel / housing allowance"),
 ("bonus", "tiền thưởng", "a year-end bonus"),
], "Báo cáo tài chính quý → earnings (= profits).",
("The company reported record ------- for the third quarter.", ["wages", "salaries", "earnings", "allowances"], 2,
 "earnings = lợi nhuận công ty.")),

("trip · journey · travel · tour · voyage · excursion · commute", [
 ("trip", "chuyến đi (đi và về, mục đích cụ thể)", "a business trip"),
 ("journey", "hành trình (quá trình di chuyển, thường dài)", "a long train journey"),
 ("travel", "việc đi lại (không đếm được)", "air travel · travel expenses"),
 ("tour", "chuyến tham quan có hướng dẫn", "a guided tour of the factory"),
 ("voyage", "chuyến đi biển/vũ trụ dài", "an ocean voyage"),
 ("excursion", "chuyến đi chơi ngắn (tập thể)", "a day excursion"),
 ("commute", "quãng đường đi làm hằng ngày", "a long commute"),
], "*a travel* sai. Tham quan nhà máy có hướng dẫn → tour.",
("New employees will be given a ------- of the facility.", ["trip", "journey", "tour", "travel"], 2,
 "a tour of the facility.")),

("permission · permit · license · authorization", [
 ("permission", "sự cho phép (không đếm được)", "ask for / grant permission"),
 ("permit", "giấy phép (đếm được, cụ thể)", "a parking / work permit"),
 ("license", "giấy phép hành nghề, bằng lái; bản quyền sử dụng (Anh: licence)", "a driver's license · software license"),
 ("authorization", "sự ủy quyền chính thức", "prior authorization"),
], "Cần **mạo từ a** → permit (permission không đếm được).",
("Visitors must display a parking ------- on the dashboard.", ["permission", "permit", "authorization", "licensing"], 1,
 "a parking permit.")),

("receipt · invoice · bill · quote · estimate", [
 ("receipt", "biên lai (đã trả tiền); sự nhận được", "keep your receipt · upon receipt of"),
 ("invoice", "hóa đơn yêu cầu thanh toán (thường giữa doanh nghiệp)", "pay the invoice within 30 days"),
 ("bill", "hóa đơn (điện nước, nhà hàng)", "the electricity bill"),
 ("quote", "báo giá chốt (thường ràng buộc)", "get a quote for 200 units"),
 ("estimate", "giá ước tính, không ràng buộc", "request a free estimate"),
], "Đổi trả hàng cần → receipt. Chưa làm, cần biết giá → estimate/quote.",
("Items may be returned within 30 days with the original -------.", ["estimate", "receipt", "quote", "reminder"], 1,
 "Trả hàng cần biên lai → receipt.")),

("opportunity · chance · possibility · occasion", [
 ("opportunity", "cơ hội (thuận lợi để làm gì)", "an opportunity to V / for"),
 ("chance", "cơ hội; khả năng xảy ra (thân mật)", "a chance to V · there's a chance that"),
 ("possibility", "khả năng (có thể xảy ra)", "the possibility of V-ing"),
 ("occasion", "dịp, lần", "on special occasions"),
], "Không nói *possibility to V* → dùng opportunity to V.",
("This is a great ------- to meet industry leaders.", ["possibility", "occasion", "opportunity", "probability"], 2,
 "opportunity to V.")),

("amount · number · quantity · volume", [
 ("amount", "lượng (danh từ không đếm được, tiền)", "a large amount of money"),
 ("number", "số lượng (danh từ đếm được số nhiều)", "a number of applicants"),
 ("quantity", "số lượng (hàng hóa), cả hai loại", "in large quantities"),
 ("volume", "khối lượng (công việc, giao dịch)", "a high volume of calls"),
], "Danh từ đếm được số nhiều → number. Chia động từ: **a number of** + N số nhiều + V số nhiều; **the number of** + N + V số ít.",
("A large ------- of applicants are expected this year.", ["amount", "number", "deal", "volume"], 1,
 "applicants đếm được → number (động từ số nhiều are).")),

("problem · issue · matter · trouble · challenge · concern", [
 ("problem", "vấn đề cần giải quyết (trung tính, hơi tiêu cực)", "solve a problem"),
 ("issue", "vấn đề đang được bàn; cũng dùng nói giảm cho problem", "address an issue · technical issues"),
 ("matter", "việc, chuyện (trang trọng)", "a private matter · discuss the matter"),
 ("trouble", "rắc rối (không đếm được)", "have trouble V-ing"),
 ("challenge", "thử thách (tích cực hơn)", "face a challenge"),
 ("concern", "mối lo ngại", "raise concerns about"),
], "have trouble **V-ing** (không *to V*). IELTS: issue nghe trung tính hơn problem; challenge mang nghĩa khác (thử thách cần vượt qua).",
("Some users have had ------- logging into the new system.", ["problem", "trouble", "issue", "matter"], 1,
 "have trouble V-ing.")),

("benefit · advantage · profit · interest", [
 ("benefit", "lợi ích (cho người); phúc lợi", "employee benefits · benefit from"),
 ("advantage", "lợi thế (so với cái khác)", "a competitive advantage · take advantage of"),
 ("profit", "lợi nhuận (tiền)", "make a profit"),
 ("interest", "lợi ích (của ai); tiền lãi", "in the interest of safety"),
], "So sánh với đối thủ → advantage. Bảo hiểm, nghỉ phép… → benefits.",
("The position offers a competitive salary and generous -------.", ["advantages", "benefits", "profits", "interests"], 1,
 "salary and benefits (phúc lợi).")),

("site · location · venue · premises · facility", [
 ("site", "khu đất, địa điểm (xây dựng, web)", "a construction site · on site"),
 ("location", "vị trí", "a convenient location"),
 ("venue", "địa điểm tổ chức sự kiện", "a wedding / concert venue"),
 ("premises", "khuôn viên (tòa nhà + đất) của doanh nghiệp", "on the premises"),
 ("facility", "cơ sở (nhà máy, trung tâm có chức năng)", "a manufacturing facility"),
], "Sự kiện → venue. Hút thuốc/đỗ xe trong khuôn viên → premises.",
("The ------- for this year's conference has not yet been decided.", ["position", "venue", "premises", "facility"], 1,
 "Địa điểm tổ chức sự kiện → venue.")),
]),

("🎭 Sắc thái tích cực / tiêu cực (connotation — IELTS Writing & Speaking)", "Cùng mô tả một sự vật nhưng khen hay chê. Dùng nhầm từ là lỗi **Lexical Resource** ở IELTS 7+.", [

("slim · slender · lean · thin · skinny · underweight", [
 ("slim / slender", "😊 thon thả, đẹp", "a slim figure"),
 ("lean", "😊 gọn, săn chắc; (công ty) tinh gọn", "lean meat · a lean organization"),
 ("thin", "😐 gầy (trung tính)", ""),
 ("skinny", "😕 gầy nhom (thân mật, hơi chê)", ""),
 ("underweight", "😟 thiếu cân (y khoa)", ""),
], "Muốn khen → slim/slender. lean còn dùng cho doanh nghiệp: lean manufacturing.",
("After restructuring, the company became ------- and more efficient.", ["skinny", "lean", "slender", "thin"], 1,
 "lean = tinh gọn (doanh nghiệp).")),

("thrifty · economical · frugal · stingy · mean · tight-fisted", [
 ("thrifty / frugal", "😊 tằn tiện, biết tiết kiệm", "a frugal lifestyle"),
 ("economical", "😊 tiết kiệm (đồ vật, cách làm)", ""),
 ("stingy / mean / tight-fisted", "😠 keo kiệt", ""),
], "Khen → frugal/thrifty; chê → stingy.",
("My grandmother was very -------; she never wasted anything.", ["stingy", "frugal", "mean", "greedy"], 1,
 "Ngữ cảnh khen → frugal.")),

("confident · self-assured · assertive · arrogant · aggressive", [
 ("confident / self-assured", "😊 tự tin", ""),
 ("assertive", "😊 quyết đoán, dám nói lên ý mình", "assertive leadership"),
 ("arrogant", "😠 kiêu ngạo", ""),
 ("aggressive", "😠 hung hăng · 😐 (kinh doanh) quyết liệt", "aggressive marketing"),
], "aggressive ở kinh doanh có thể trung tính/tích cực: an aggressive growth strategy.",
("A good negotiator should be ------- without being aggressive.", ["arrogant", "assertive", "stubborn", "reckless"], 1,
 "Tích cực, đối lập với aggressive → assertive.")),

("determined · persistent · persevering · stubborn · obstinate", [
 ("determined", "😊 quyết tâm", ""),
 ("persistent / persevering", "😊 bền bỉ (persistent đôi khi trung tính: persistent cough)", ""),
 ("stubborn / obstinate", "😠 bướng bỉnh, cố chấp", ""),
], "persistent problem = vấn đề dai dẳng (tiêu cực) — nghĩa phụ thuộc danh từ đi kèm.",
("Despite many failures, she remained ------- to succeed.", ["stubborn", "determined", "obstinate", "persistent"], 1,
 "determined to V. persistent không đi với to V.")),

("famous · well-known · renowned · celebrated · notorious · infamous", [
 ("famous / well-known", "😐 nổi tiếng", ""),
 ("renowned / celebrated / acclaimed", "😊 lừng danh (trang trọng, khen)", "renowned for"),
 ("notorious / infamous", "😠 khét tiếng (xấu)", "notorious for"),
], "infamous **không** phải ‘không nổi tiếng’.",
("The city is ------- for its traffic jams.", ["renowned", "celebrated", "notorious", "acclaimed"], 2,
 "Kẹt xe (xấu) → notorious.")),

("childlike · childish", [
 ("childlike", "😊 hồn nhiên như trẻ con", "childlike curiosity"),
 ("childish", "😠 trẻ con, ấu trĩ", "childish behavior"),
], "",
("Her ------- sense of wonder makes her a great teacher.", ["childish", "childlike", "childhood", "children"], 1,
 "Khen → childlike.")),

("cheap · inexpensive · affordable · budget · low-cost", [
 ("affordable / inexpensive", "😊 giá phải chăng", "affordable housing"),
 ("budget / low-cost", "😐 giá rẻ (phân khúc)", "a budget airline"),
 ("cheap", "😕 rẻ (có thể hàm ý kém chất lượng)", "cheap materials"),
], "Văn quảng cáo TOEIC thường dùng affordable / low prices, tránh cheap.",
("We offer high-quality furniture at ------- prices.", ["costly", "affordable", "cheaply", "luxurious"], 1,
 "Văn quảng cáo, tích cực → affordable.")),

("scent · fragrance · aroma · odor · stench", [
 ("scent / fragrance", "😊 hương thơm (hoa, nước hoa)", ""),
 ("aroma", "😊 mùi thơm (đồ ăn, cà phê)", "the aroma of fresh bread"),
 ("odor", "😕 mùi (thường khó chịu)", "unpleasant odors"),
 ("stench", "😠 mùi hôi thối", ""),
], "",
("The ------- of freshly brewed coffee filled the café.", ["odor", "stench", "aroma", "fume"], 2,
 "Cà phê → aroma.")),

("look · stare · gaze · glance · glimpse · peer", [
 ("stare", "nhìn chằm chằm (có thể bất lịch sự)", "stare at"),
 ("gaze", "nhìn đăm đăm (ngưỡng mộ, mơ màng)", "gaze at the stars"),
 ("glance", "liếc nhanh (chủ động)", "glance at the clock"),
 ("glimpse", "thoáng thấy (bị động, không chủ ý)", "catch a glimpse of"),
 ("peer", "nhìn kỹ (vì khó thấy)", "peer through the fog"),
], "catch a glimpse — không *catch a glance*.",
("She ------- at her watch and hurried out.", ["stared", "gazed", "glanced", "glimpsed"], 2,
 "Liếc nhanh đồng hồ → glanced.")),

("old · elderly · senior · aged · ancient · antique · outdated", [
 ("elderly / senior", "😊 lịch sự khi nói về người già", "senior citizens · elderly residents"),
 ("old", "😐 già, cũ (thẳng)", ""),
 ("ancient", "cổ đại; (đùa) quá cũ", "ancient Rome"),
 ("antique", "😊 đồ cổ có giá trị", "antique furniture"),
 ("outdated / obsolete", "😠 lỗi thời", "outdated equipment"),
], "Văn bản chính thức: elderly / senior (senior citizens); văn phong hiện đại (IELTS, báo chí) ưa older people.",
("Discounts are available for ------- citizens.", ["old", "senior", "ancient", "aged"], 1,
 "senior citizens (cụm cố định).")),
]),

("📈 Mức độ & văn phong (IELTS Writing Task 1–2)", "Chọn đúng **cường độ** và **register** để đạt Lexical Resource 8–9.", [

("Tăng: rise · increase · climb · grow · surge · soar · rocket · edge up · creep up", [
 ("edge up / creep up", "tăng rất nhẹ, chậm", "edged up to 12%"),
 ("rise / increase / grow / climb", "tăng (trung tính)", "rose steadily"),
 ("surge", "tăng vọt đột ngột", "surged in 2010"),
 ("soar / rocket / skyrocket", "tăng vọt rất mạnh", "soared to a peak of"),
], "Không lạm dụng rocket cho mức +2%. Đi kèm trạng từ: slightly / steadily / sharply / dramatically.",
("The number of users ------- from 2 million to 40 million in just two years.", ["edged up", "crept up", "soared", "leveled off"], 2,
 "Tăng 20 lần → soared.")),

("Giảm: fall · drop · decline · decrease · dip · slump · plunge · plummet", [
 ("dip", "giảm nhẹ, tạm thời", "dipped slightly"),
 ("fall / drop / decline / decrease", "giảm (trung tính)", "fell gradually"),
 ("slump", "sụt mạnh và kéo dài (kinh tế)", "sales slumped"),
 ("plunge / plummet", "lao dốc", "plummeted to"),
], "dip = giảm nhẹ rồi thường hồi lại.",
("Sales ------- slightly in March before recovering in April.", ["plummeted", "dipped", "plunged", "slumped"], 1,
 "slightly + hồi lại → dipped.")),

("Đi ngang & dao động: remain stable · level off · plateau · fluctuate · peak · bottom out", [
 ("remain stable / steady / unchanged", "giữ nguyên trong một giai đoạn", "remained stable at 20%"),
 ("level off / plateau", "chững lại **sau** khi tăng/giảm", "leveled off at · reached a plateau"),
 ("fluctuate", "dao động lên xuống", "fluctuated between 10 and 15%"),
 ("peak (at)", "đạt đỉnh", "peaked at 90 in 2015 · reached a peak of"),
 ("bottom out / hit a low", "chạm đáy rồi thôi giảm", "bottomed out in 2009"),
], "fluctuate **between** A and B; peak **at** + số; level off **at** + số.",
("Oil prices ------- between $60 and $80 throughout the year.", ["peaked", "fluctuated", "leveled off", "bottomed out"], 1,
 "between … and … + lên xuống → fluctuated.")),

("show · indicate · suggest · demonstrate · prove · reveal · illustrate", [
 ("show / illustrate", "cho thấy (biểu đồ)", "The chart illustrates"),
 ("indicate / suggest", "gợi ý, cho thấy (mức chắc chắn thấp hơn)", "data suggest that"),
 ("demonstrate", "chứng minh rõ (bằng bằng chứng)", ""),
 ("prove", "chứng minh chắc chắn (dùng thận trọng trong học thuật)", ""),
 ("reveal", "tiết lộ (điều chưa biết)", "the survey revealed"),
], "Học thuật: tránh prove khi bằng chứng chưa tuyệt đối → suggest/indicate (hedging).",
("The limited data only ------- a possible link between diet and memory.", ["prove", "suggest", "demonstrate", "confirm"], 1,
 "“only… possible” → mức chắc chắn thấp → suggest.")),

("Động từ tường thuật: claim · argue · assert · maintain · contend · acknowledge · concede", [
 ("claim", "cho rằng (người viết hơi nghi ngờ)", "claim that"),
 ("argue / contend", "lập luận (có lý lẽ)", ""),
 ("assert / maintain", "khẳng định mạnh / kiên định", ""),
 ("acknowledge / concede", "thừa nhận (điểm của phía kia)", "concede that"),
], "IELTS Reading Yes/No/Not Given: *claim* **có thể** hàm ý tác giả nghi ngờ — phải dựa vào ngữ cảnh (câu sau thường phản bác).",
("Although critics ------- that the policy failed, recent data show a clear improvement.", ["concede", "acknowledge", "claim", "prove"], 2,
 "Tác giả phản bác → claim (hàm ý nghi ngờ).")),

("important · significant · crucial · vital · essential · paramount", [
 ("important", "quan trọng (chung)", ""),
 ("significant", "đáng kể; có ý nghĩa thống kê", "a significant increase"),
 ("crucial / vital / essential", "thiết yếu, sống còn", "vital to / essential for"),
 ("paramount", "quan trọng nhất (trên hết)", "Safety is paramount."),
], "Số liệu tăng/giảm → significant (không dùng *an important increase*).",
("There was a ------- increase in the number of tourists.", ["vital", "significant", "paramount", "crucial"], 1,
 "increase → significant.")),

("large · considerable · substantial · vast · massive · enormous", [
 ("considerable / substantial", "đáng kể (học thuật, số lượng)", "a substantial amount"),
 ("vast", "rộng lớn (diện tích, đa số)", "the vast majority"),
 ("massive / enormous / huge", "khổng lồ (nhấn mạnh, ít trang trọng hơn)", ""),
], "the ------- majority → vast (collocation cố định).",
("The ------- majority of respondents preferred online shopping.", ["massive", "vast", "giant", "wide"], 1,
 "the vast majority.")),

("buy · purchase · acquire · procure", [
 ("buy", "mua (thông thường)", ""),
 ("purchase", "mua (trang trọng, văn bản)", "proof of purchase"),
 ("acquire", "thu mua (công ty); đạt được (kỹ năng)", "acquire a rival firm"),
 ("procure", "mua sắm (vật tư, chính phủ, trang trọng)", "procure equipment"),
], "Mua lại công ty → acquire (n: acquisition).",
("The tech giant plans to ------- a smaller start-up for $2 billion.", ["procure", "obtain", "acquire", "gain"], 2,
 "Mua lại công ty → acquire (n: acquisition). procure dùng cho vật tư, không dùng cho công ty.")),

("help · assist · aid · facilitate", [
 ("help", "giúp (chung)", "help sb (to) V"),
 ("assist", "hỗ trợ (trang trọng)", "assist sb with/in V-ing"),
 ("aid", "viện trợ; hỗ trợ (học thuật)", "aid recovery"),
 ("facilitate", "làm cho dễ dàng hơn (quá trình, không phải người)", "facilitate communication"),
], "facilitate + **sự việc**, không + người (*facilitate students* là sai).",
("The new software will ------- communication between departments.", ["assist", "allow", "facilitate", "persuade"], 2,
 "facilitate communication.")),

("start · begin · commence · initiate · launch · embark on", [
 ("start / begin", "bắt đầu (chung)", ""),
 ("commence", "bắt đầu (rất trang trọng, văn bản)", "construction will commence"),
 ("initiate", "khởi xướng (quy trình, kế hoạch)", "initiate a review"),
 ("launch", "ra mắt, phát động (chiến dịch, sản phẩm)", ""),
 ("embark on", "bắt tay vào (việc lớn, lâu dài)", "embark on a career"),
], "embark **on** — không bỏ giới từ.",
("The firm is about to ------- on an ambitious expansion plan.", ["commence", "embark", "initiate", "launch"], 1,
 "embark on.")),

("remove · eliminate · eradicate · abolish", [
 ("remove", "loại bỏ, gỡ (vật lý hoặc chung)", ""),
 ("eliminate", "loại bỏ hoàn toàn (rủi ro, chi phí)", "eliminate the need for"),
 ("eradicate", "diệt trừ tận gốc (bệnh, nghèo đói)", "eradicate poverty"),
 ("abolish", "bãi bỏ (luật, chế độ)", "abolish the death penalty"),
], "Bệnh tật/nghèo đói → eradicate; luật lệ → abolish.",
("Parliament voted to ------- the 1970 Land Act.", ["eradicate", "abolish", "exterminate", "excavate"], 1,
 "Thuế/luật → abolish.")),
]),

("🔗 Liên từ & giới từ na ná nghĩa (Part 5 tần suất cao nhất)", "Cùng nghĩa “mặc dù / vì / trong khi” nhưng khác **loại từ**: sau liên từ là **mệnh đề**, sau giới từ là **danh từ / V-ing**, trạng từ nối đứng **sau dấu chấm / chấm phẩy**.", [

("although · though · even though · despite · in spite of · however · nevertheless", [
 ("although / though / even though", "liên từ: mặc dù + **mệnh đề** (even though nhấn mạnh hơn)", "Although sales fell, profits rose."),
 ("despite / in spite of", "giới từ: mặc dù + **N / V-ing** (không *despite of*)", "Despite the rain, ..."),
 ("despite the fact that", "giới từ + the fact that + mệnh đề", ""),
 ("however / nevertheless / nonetheless", "trạng từ nối: tuy nhiên — đứng đầu câu mới, có dấu phẩy", "...fell. However, profits rose."),
], "Nhìn sau chỗ trống: có S + V → although; chỉ có cụm danh từ → despite.",
("------- the heavy traffic, the shuttle arrived on time.", ["Although", "Despite", "However", "Even though"], 1,
 "Sau là cụm danh từ (the heavy traffic) → giới từ Despite.")),

("because · since · as · because of · due to · owing to · thanks to", [
 ("because / since / as", "liên từ: vì + **mệnh đề**", "because the flight was delayed"),
 ("because of / owing to", "giới từ: vì + N", "because of the delay"),
 ("due to", "giới từ: do + N; cũng làm vị ngữ sau be (be due to)", "The delay was due to fog."),
 ("thanks to", "nhờ (kết quả tốt)", "thanks to your support"),
], "thanks to cho nguyên nhân **tích cực**; due to/owing to trung tính (thông báo trễ, hủy).",
("The concert was canceled ------- the singer's illness.", ["because", "since", "due to", "thanks to"], 2,
 "Sau là cụm danh từ, nguyên nhân tiêu cực → due to.")),

("during · while · for · throughout · within", [
 ("during", "giới từ: trong suốt + **N (sự kiện, khoảng thời gian)**", "during the meeting"),
 ("while", "liên từ: trong khi + **mệnh đề / V-ing**", "while (you are) waiting"),
 ("for", "trong (bao lâu) + **thời lượng**", "for three hours"),
 ("throughout", "suốt từ đầu đến cuối; khắp", "throughout the year / the building"),
 ("within", "trong vòng (không quá)", "within 30 days"),
], "during + sự kiện (the meeting), for + con số (two weeks). Hạn chót “không quá X ngày” → within.",
("Please keep your phone switched off ------- the performance.", ["while", "for", "during", "within"], 2,
 "Sau là danh từ sự kiện → during.")),

("by · until · before · no later than", [
 ("by", "trước hoặc đúng (hạn chót) — hành động **một lần**", "submit the report by Friday"),
 ("until / till", "cho đến khi — hành động **kéo dài**", "The store is open until 9 P.M."),
 ("before", "trước (không bao gồm mốc)", "before noon"),
 ("no later than", "chậm nhất là (trang trọng)", "no later than May 5"),
], "Động từ hoàn tất một lần (submit, return, finish) → by. Trạng thái kéo dài (stay, remain open, wait) → until.",
("All applications must be submitted ------- March 31.", ["until", "by", "during", "while"], 1,
 "submit (hoàn tất một lần) + hạn chót → by.")),

("unless · if · otherwise · provided that · in case", [
 ("if", "nếu", ""),
 ("unless", "trừ khi (= if … not)", "unless otherwise stated"),
 ("provided (that) / as long as", "miễn là (điều kiện bắt buộc)", "provided that payment is received"),
 ("in case", "phòng khi (đề phòng)", "take an umbrella in case it rains"),
 ("otherwise", "trạng từ: nếu không thì", "Hurry; otherwise, you'll miss it."),
], "unless đã mang nghĩa phủ định — không dùng *unless … not*.",
("The order will ship tomorrow ------- payment is received today.", ["unless", "otherwise", "provided that", "in case"], 2,
 "Điều kiện bắt buộc để giao hàng → provided that.")),
]),

("🎯 Trạng từ dễ nhầm (Part 5)", "Cặp “có -ly / không -ly” khác nghĩa và nhóm trạng từ mức độ.", [

("hard/hardly · late/lately · high/highly · near/nearly · short/shortly · close/closely", [
 ("hard / hardly", "chăm chỉ / hầu như không", "work hard · hardly ever"),
 ("late / lately", "muộn / gần đây", "arrive late · lately (+ hiện tại hoàn thành)"),
 ("high / highly", "cao (vị trí) / rất (mức độ)", "highly recommended"),
 ("near / nearly", "gần (khoảng cách) / gần như", "nearly finished"),
 ("short / shortly", "ngắn, hụt / sắp, ngay sau", "shortly after · will arrive shortly"),
 ("close / closely", "gần / chặt chẽ, kỹ lưỡng", "work closely with · monitor closely"),
], "Đuôi -ly **không** chỉ là dạng trạng từ của cái kia — nghĩa khác hẳn.",
("Ms. Wong works ------- with the design team.", ["close", "closely", "closing", "closed"], 1,
 "work closely with = phối hợp chặt chẽ.")),

("almost · most · mostly · most of", [
 ("almost", "gần như (+ all, every, always, never)", "almost all employees"),
 ("most", "hầu hết (+ N không mạo từ)", "most employees"),
 ("most of", "hầu hết (+ the/my/these + N)", "most of the employees"),
 ("mostly", "chủ yếu là", "mostly young people"),
], "*almost employees* sai → almost all employees.",
("------- all of the seats were taken.", ["Most", "Almost", "Mostly", "Most of"], 1,
 "Almost all.")),

("especially · specially · particularly", [
 ("especially / particularly", "đặc biệt là (nhấn mạnh một thành phần)", "especially in winter"),
 ("specially", "được làm riêng cho mục đích", "specially designed for"),
], "Thường dùng specially designed/made; especially designed vẫn gặp ở người bản xứ, nhưng đề ETS luôn chọn specially.",
("The chair was ------- designed for people with back problems.", ["especially", "specially", "special", "specialty"], 1,
 "specially designed.")),

("formerly · previously · originally · initially", [
 ("formerly", "trước đây (tên/chức vụ cũ)", "formerly known as"),
 ("previously", "trước đó (so với thời điểm đang nói)", "as previously mentioned"),
 ("originally", "ban đầu, vốn dĩ", "originally scheduled for"),
 ("initially", "lúc đầu (sau đó thay đổi)", "initially reluctant"),
], "Ban đầu như thế, giờ đã khác → originally / initially. formerly = trước đây (tên, chức vụ cũ).",
("The system was ------- designed for 50 users but now serves 5,000.", ["formerly", "originally", "lately", "shortly"], 1,
 "originally designed = ban đầu được thiết kế (giờ đã khác).")),

("much · far · even · considerably · very (+ so sánh hơn)", [
 ("much / far / even / considerably / significantly / a lot", "nhấn mạnh **so sánh hơn**", "much better · far more expensive"),
 ("very", "**không** đứng trước so sánh hơn", "very good (đúng) · very better (sai)"),
], "Trước -er / more → much/far/even, không very.",
("This year's results were ------- better than expected.", ["very", "much", "too", "so"], 1,
 "much + so sánh hơn.")),
]),
]
