#!/usr/bin/env python3
"""Nhận diện 60 "keo dán" + từ kana/văn báo của trang lộ trình đọc hiểu (docs/kanji-viewer/lo-trinh-doc-hieu.html)
và tách câu theo "quy tắc vàng" (động từ ở cuối, cụm theo trợ từ). Dùng trong tools/doc_bao_vocab.py.

Cần: pip install janome   (tách từ tiếng Nhật, thuần Python)
"""
import re

# (mã, nhóm, mẫu, nghĩa) — số 1–60 đúng thứ tự trên trang lộ trình; 61+ là bảng ⑤ "Từ viết bằng kana & cụm văn báo".
GROUPS = ["Trợ từ", "Đuôi động từ", "Phỏng đoán · nghe nói", "Tính từ · danh từ", "Nối vế", "Cấu trúc câu",
          "⑤ Trợ từ ghép", "⑤ Trạng từ", "⑤ Văn báo", "⑤ Dạng thường (truyện)", "⑤ Kính ngữ",
          "⑥ Bổ sung hay gặp (nối vế · て+động từ · điều kiện · số · こそあど)",
          "⑤ Từ nối câu & cụm văn báo"]
GLUE = [
    (1, 0, "は", "còn nói về… (chủ đề)"), (2, 0, "が", "chủ ngữ / cái được nhấn"),
    (3, 0, "を", "tân ngữ (làm gì cái gì)"), (4, 0, "に", "tới, vào, lúc, cho"),
    (5, 0, "で", "tại (nơi làm), bằng"), (6, 0, "の", "của: A の B = B của A"),
    (7, 0, "と", "và · với · rằng"), (8, 0, "も", "cũng"), (9, 0, "から", "từ · vì"),
    (10, 0, "まで", "đến"), (11, 0, "へ", "hướng tới"), (12, 0, "より", "hơn · từ"),
    (13, 0, "か", "(cuối câu) hỏi · hoặc"), (14, 0, "や", "và… (liệt kê không hết)"),
    (15, 1, "〜る・〜う", "hiện tại / sẽ"), (16, 1, "〜ます", "(lịch sự) làm"), (17, 1, "〜た", "đã"),
    (18, 1, "〜ました", "(lịch sự) đã"), (19, 1, "〜ない", "không"), (20, 1, "〜ません", "(lịch sự) không"),
    (21, 1, "〜なかった", "đã không"), (22, 1, "〜て", "…rồi / và (nối)"),
    (23, 1, "〜ている", "đang · đang ở trạng thái"), (24, 1, "〜たい", "muốn"),
    (25, 1, "〜られる・〜れる", "bị / được · có thể"), (26, 1, "〜させる", "bắt / cho (ai làm)"),
    (27, 1, "〜ば", "nếu"), (28, 1, "〜たら", "nếu / khi… thì"), (29, 1, "〜なら", "nếu là"),
    (30, 1, "〜ても", "dù có… cũng"), (31, 1, "〜なければならない", "phải"), (32, 1, "〜てもいい", "được phép"),
    (33, 1, "〜ことができる", "có thể"), (34, 1, "〜よう・〜おう", "hãy… / định…"),
    (35, 1, "〜ながら", "vừa… vừa"), (36, 1, "〜ために", "để · vì"),
    (37, 2, "〜そうだ", "nghe nói · trông có vẻ"), (38, 2, "〜ようだ", "hình như"), (39, 2, "〜らしい", "nghe đâu là"),
    (40, 2, "〜だろう・〜でしょう", "chắc là"), (41, 2, "〜かもしれない", "có lẽ"),
    (42, 3, "〜い", "tính từ (高い = cao)"), (43, 3, "〜くない", "không (cao)"), (44, 3, "〜かった", "đã (cao)"),
    (45, 3, "だ・です・である", "là"), (46, 3, "ではない・じゃない", "không phải là"),
    (47, 4, "しかし・でも・〜けど", "nhưng"), (48, 4, "そして", "và rồi"), (49, 4, "また", "ngoài ra · lại"),
    (50, 4, "だから・そのため", "vì vậy"), (51, 4, "〜が、", "…, nhưng"), (52, 4, "〜ので・〜から", "vì"),
    (53, 4, "〜のに", "mặc dù"), (54, 4, "〜とき", "khi"), (55, 4, "〜によると", "theo (nguồn)"),
    (56, 4, "〜について", "về (vấn đề)"),
    (57, 5, "V + danh từ", "mệnh đề \"…mà\": 昨日買った本 = sách mà hôm qua mua"),
    (58, 5, "〜の・〜こと", "biến động từ thành danh từ: 読むこと = việc đọc"),
    (59, 5, "〜という", "gọi là · rằng"), (60, 5, "〜と言う・〜と思う", "nói rằng · nghĩ rằng"),
]
# ⑤ — dò bằng regex trên câu
EXTRA = [
    (6, "に対して", "đối với · trái lại", r"に対し"), (6, "によって", "do · bởi · tuỳ theo", r"によっ|により|による"),
    (6, "として", "với tư cách là", r"として"), (6, "において", "tại · trong (trang trọng)", r"におい|における"),
    (6, "に関する", "liên quan đến", r"に関す|に関し"), (6, "にとって", "đối với (ai)", r"にとっ"),
    (6, "とともに", "cùng với · đồng thời", r"とともに|と共に"), (6, "に伴い", "kéo theo · cùng với việc", r"に伴"),
    (7, "すでに", "đã (rồi)", r"すでに|既に"), (7, "まだ", "vẫn còn · chưa", r"まだ"), (7, "もう", "đã · nữa", r"もう"),
    (7, "ほとんど", "hầu hết · hầu như", r"ほとんど|殆ど"), (7, "かなり", "khá là", r"かなり"),
    (7, "とても", "rất", r"とても"), (7, "さらに", "hơn nữa · thêm", r"さらに|更に"), (7, "特に", "đặc biệt", r"特に"),
    (7, "必ず", "nhất định", r"必ず"), (7, "ずっと", "suốt · hơn hẳn", r"ずっと"),
    (8, "〜とみられる", "được cho là", r"とみられ|と見られ"),
    (8, "〜ことが分かった", "đã biết được rằng · được xác nhận", r"ことが分か|ことがわか"),
    (8, "〜と明らかにした", "đã cho biết rằng", r"と明らかに"), (8, "〜方針", "chủ trương (sẽ…)", r"方針"),
    (8, "〜を受けて", "sau khi / do (sự việc)", r"を受け"), (8, "〜とした", "cho rằng · tuyên bố", r"(?<![うょっ])とした(?!い)"),
    (9, "〜んだ", "là vì… · (giải thích, nhấn mạnh)", r"んだ|んです|のだ|のです"),
    (9, "〜ちゃう", "lỡ… mất · …hết", r"ちゃ[うっわいえお]|じゃ[うっ]"),
    (9, "〜てる", "đang (= 〜ている)", None), (9, "よ", "đấy (nhấn, báo tin)", None), (9, "ね", "nhỉ · nhé", None),
    (9, "な", "(nam) nhỉ · đừng (sau động từ)", None),
    (10, "いらっしゃる", "đến · đi · ở (kính)", r"いらっしゃ"), (10, "おっしゃる", "nói (kính)", r"おっしゃ"),
    (10, "いただく", "nhận · ăn (khiêm)", r"いただ|頂"), (10, "くださる", "cho (kính)", r"くださ|下さ"),
    (10, "申す", "nói (khiêm)", r"申し|申す"), (10, "伺う", "hỏi · đến thăm (khiêm)", r"伺"),
    (10, "ご覧になる", "xem (kính)", r"ご覧"),
]
for k, (g, pat, mean, rx) in enumerate(EXTRA):
    GLUE.append((61 + k, g, pat, mean))
EXTRA_ID = {pat: 61 + k for k, (g, pat, mean, rx) in enumerate(EXTRA)}

# ⑥ — các mẫu rất hay gặp trong báo / blog mà 60 mục + ⑤ chưa có (theo phản biện): (mẫu, nghĩa, ví dụ, regex hoặc None = dò bằng token)
EXTRA6 = [
    ("〜し、・〜り、(gốc động từ + dấu phẩy)", "nối vế: …, rồi / và (báo dùng nhiều như 〜て)", "政府は計画を発表し、", None),
    ("〜ず・〜ずに・〜ないで・〜なくて", "không… (mà) · không… nên", "食べずに寝た", r"(?<!ま)ず(に|、|。)|ないで|なくて"),
    ("〜てしまう", "lỡ… · … mất · xong hết", "食べてしまった", r"[てで]しま[うっいえお]|[てで]ちゃ|ちゃっ"),
    ("〜ておく", "làm sẵn · để nguyên", "買っておく", r"[てで]おく|[てで]おき|[てで]おい[たて]|[てで]おか"),
    ("〜てくる・〜ていく", "dần dần (đến nay / từ nay) · đi làm rồi về", "増えてきた・増えていく", None),
    ("〜てみる", "thử", "食べてみる", None),
    ("〜てある", "đã được (làm sẵn)", "書いてある", None),
    ("〜てもらう・〜てくれる・〜てあげる", "được ai làm cho · ai làm cho mình · làm cho ai", "教えてくれた", None),
    ("〜ようになる・〜ようにする", "trở nên (có thể) · cố gắng để", "話せるようになった", r"ように(なっ|な[るれり]|し[てたま]|する|なり)"),
    ("〜ことになる・〜ことにする", "được quyết định · tự quyết định", "行くことになった", r"ことに(なっ|な[るれり]|し[てたま]|する|なり)"),
    ("〜はず", "chắc chắn · lẽ ra phải", "来るはずだ", r"はず"),
    ("〜わけ", "lý do · 〜わけではない = không hẳn là", "怒っているわけではない", r"わけ"),
    ("〜べき", "nên · phải", "やるべきだ", r"べき|べく"),
    ("〜だけ・〜しか〜ない・〜ばかり", "chỉ · chỉ có · toàn là", "これだけ・一つしかない", None),
    ("〜ほど・〜くらい", "đến mức · khoảng", "驚くほど・三日くらい", None),
    ("〜など・〜さえ・〜すら・〜なんて", "chẳng hạn · thậm chí · … gì chứ", "子供さえ知っている", None),
    ("〜まま・〜うち", "cứ nguyên như vậy · trong lúc", "そのままにする", None),
    ("〜かどうか", "có… hay không", "行くかどうか分からない", r"かどうか"),
    ("〜とされる・〜と考えられる", "được cho là · được coi là", "原因とされる", r"とされ|と考えられ|と思われ"),
    ("〜くて・〜で (nối tính từ)", "và · vì (tính từ)", "高くて・静かで", None),
    ("〜く・〜に (trạng từ)", "một cách… · trở nên…", "早く・静かに", None),
    ("〜な + danh từ (tính từ な)", "静かな部屋 = phòng yên tĩnh", "静かな部屋", None),
    ("こ・そ・あ・ど (これ その そう どう なぜ 何)", "này · đó · kia · nào / thế này · thế nào · tại sao · gì", "その理由は何か", None),
    ("〜際・〜側・〜等・〜氏", "khi · phía · v.v. · ông/bà", "利用の際・政府側", None),
    ("万・億・割・約", "10⁴ · 10⁸ · 10% · khoảng", "3万人・約5割", r"[0-9０-９一二三四五六七八九十百千]\s*(万|億|兆)|[0-9０-９一二三四五六七八九十]割|約"),
    ("N + できる", "làm được (利用できる)", "利用できる", r"[一-鿿ァ-ヿ]{2,}(が)?(できる|できた|できない|できます|できません|できて|できず)"),
    ("〜てください・〜なさい", "hãy… (nhờ · ra lệnh nhẹ)", "見てください", r"[てで]ください|なさい"),
]
_N5 = 61 + len(EXTRA)
EXTRA6_ID = {pat: _N5 + k for k, (pat, mean, ex, rx) in enumerate(EXTRA6)}
for k, (pat, mean, ex, rx) in enumerate(EXTRA6):
    GLUE.append((_N5 + k, 11, pat, mean))

# ---------------- GỘP theo phản biện ----------------
# Mã nhận diện bên trong (1..124) giữ nguyên để dò; DISP ánh xạ sang SỐ HIỂN THỊ gọn hơn:
#   45 mục cốt lõi (gộp ます/ました/ません · ない/なかった · ば/たら/なら · 〜い/くない/かった · だ/ではない)
#   + 7 từ nối câu chuyển xuống ⑤ (là từ vựng, không phải ngữ pháp) + ⑤ + ⑥.
CORE_MERGE = [  # (nhóm, mẫu, nghĩa, [mã nhận diện cũ])
    (0, "は", "còn nói về… (chủ đề)", [1]), (0, "が", "chủ ngữ / cái được nhấn", [2]),
    (0, "を", "tân ngữ (làm gì cái gì)", [3]), (0, "に", "tới, vào, lúc, cho", [4]),
    (0, "で", "tại (nơi làm), bằng", [5]), (0, "の", "của: A の B = B của A", [6]),
    (0, "と", "và · với · rằng · hễ… thì", [7]), (0, "も", "cũng", [8]), (0, "から", "từ · vì", [9]),
    (0, "まで", "đến", [10]), (0, "へ", "hướng tới", [11]), (0, "より", "hơn · từ", [12]),
    (0, "か", "(cuối câu) hỏi · hoặc", [13]), (0, "や", "và… (liệt kê không hết)", [14]),
    (1, "〜る・〜う", "hiện tại / sẽ", [15]),
    (1, "〜ます・〜ました・〜ません", "(lịch sự) làm · đã · không", [16, 18, 20]),
    (1, "〜た", "đã", [17]),
    (1, "〜ない・〜なかった", "không · đã không", [19, 21]),
    (1, "〜て", "…rồi / và (nối) · vì · bằng cách", [22]),
    (1, "〜ている", "đang · đang ở trạng thái", [23]), (1, "〜たい", "muốn", [24]),
    (1, "〜られる・〜れる", "bị / được · có thể · kính ngữ · tự phát", [25]),
    (1, "〜させる", "bắt / cho (ai làm)", [26]),
    (1, "〜ば・〜たら・〜なら", "nếu (điều kiện)", [27, 28, 29]),
    (1, "〜ても", "dù có… cũng", [30]), (1, "〜なければならない", "phải", [31]),
    (1, "〜てもいい", "được phép", [32]), (1, "〜ことができる", "có thể", [33]),
    (1, "〜よう・〜おう", "ta hãy… · định… · cố", [34]), (1, "〜ながら", "vừa… vừa", [35]),
    (1, "〜ために", "để · vì", [36]),
    (2, "〜そうだ", "trông như · nghe nói", [37]), (2, "〜ようだ", "hình như", [38]),
    (2, "〜らしい", "nghe đâu là", [39]), (2, "〜だろう・〜でしょう", "chắc là", [40]),
    (2, "〜かもしれない", "có lẽ", [41]),
    (3, "〜い・〜くない・〜かった", "tính từ: cao · không cao · đã cao", [42, 43, 44]),
    (3, "だ・です・である・ではない", "là · không phải là", [45, 46]),
    (4, "〜が、", "…, nhưng (có khi chỉ nối ý)", [51]), (4, "〜ので・〜から", "vì", [52]),
    (4, "〜のに", "mặc dù", [53]),
    (5, "V + danh từ", "mệnh đề \"…mà\": 昨日買った本 = sách mà hôm qua mua", [57]),
    (5, "〜の・〜こと", "biến động từ thành danh từ: 読むこと = việc đọc", [58]),
    (5, "〜という", "gọi là · rằng", [59]), (5, "〜と言う・〜と思う", "nói rằng · nghĩ rằng", [60]),
]
MOVED = [(47, "しかし・でも・〜けど", "nhưng"), (48, "そして", "và rồi"), (49, "また", "ngoài ra · lại"),
         (50, "だから・そのため", "vì vậy"), (54, "〜とき", "khi"), (55, "〜によると", "theo (nguồn)"),
         (56, "〜について", "về (vấn đề)")]
GLUE_FINE = GLUE
DISP, GLUE_DISPLAY, _n = {}, [], 0
for _g, _pat, _mean, _olds in CORE_MERGE:
    _n += 1
    GLUE_DISPLAY.append((_n, _g, _pat, _mean))
    for _o in _olds:
        DISP[_o] = _n
CORE_N = _n
for _o, _pat, _mean in MOVED:
    _n += 1
    DISP[_o] = _n
    GLUE_DISPLAY.append((_n, 12, _pat, _mean))
for _i, _g, _pat, _mean in GLUE_FINE:
    if _i >= 61:
        _n += 1
        DISP[_i] = _n
        GLUE_DISPLAY.append((_n, _g, _pat, _mean))
assert len(DISP) == len(GLUE_FINE), (len(DISP), len(GLUE_FINE))
GLUE = GLUE_DISPLAY
META = {i: (g, pat, mean) for i, g, pat, mean in GLUE_DISPLAY}


def disp_hits(H):
    """Đổi mã nhận diện -> số hiển thị, bỏ trùng (mục gộp có thể chồng nhau)."""
    out = []
    for i, a, z in sorted(((DISP[i], a, z) for i, a, z in H), key=lambda h: (h[0], h[1], -h[2])):
        if out and out[-1][0] == i and a < out[-1][2]:
            continue
        out.append((i, a, z))
    return out


RX = [(31, r"(なけれ[ばど]|なきゃ|なくては|なくちゃ)(なら|いけ)?(ない|なかった|ません)?"), (32, r"[てで]も?(いい|良い|よい|かまわ|構わ)"),
      (33, r"ことができ|ことが出来|ことができ"), (36, r"ために|ため、|ためだ|ための"),
      (37, r"そう(だ|です|な|に)"), (38, r"よう(だ|です)|ような|みたい"), (40, r"だろう|でしょう"),
      (41, r"かもしれ|かも知れ"), (46, r"ではな|じゃな|ではありませ|じゃありませ"), (50, r"だから|そのため|ですから"),
      (55, r"によると|によれば"), (56, r"について|につき"), (59, r"という|といった|っていう|との"),
      (60, r"と(言[っうわいえ]|い[っうわ]|思[っうわいえ]|考え)|って(言|思)")]
RX = [(i, re.compile(r)) for i, r in RX] + [(EXTRA_ID[p], re.compile(r)) for g, p, m, r in EXTRA if r] \
    + [(EXTRA6_ID[p], re.compile(r)) for p, m, e, r in EXTRA6 if r]

_TOK = None


def tokenizer():
    global _TOK
    if _TOK is None:
        from janome.tokenizer import Tokenizer
        _TOK = Tokenizer()
    return _TOK


def tokens(sent):
    """-> list of dict(s=surface, p=pos0, p1=pos1, b=base, f=infl form, a=start, z=end)"""
    out, a = [], 0
    for t in tokenizer().tokenize(sent):
        ps = t.part_of_speech.split(",")
        out.append(dict(s=t.surface, p=ps[0], p1=ps[1], b=t.base_form, f=t.infl_form, a=a, z=a + len(t.surface)))
        a += len(t.surface)
    return out


KOSOADO = set("これ それ あれ どれ この その あの どの ここ そこ あそこ どこ こう そう ああ どう なぜ 何 誰 いつ どんな こんな そんな".split())


def detect6(sent, T):
    """⑥: các mẫu dò bằng token (regex thì nằm trong RX)."""
    I = EXTRA6_ID
    H, n = [], len(T)
    for k, t in enumerate(T):
        nt = T[k + 1] if k + 1 < n else None
        pv = T[k - 1] if k else None
        s, p, p1, b, f = t["s"], t["p"], t["p1"], t["b"], t["f"]
        if p == "動詞" and f == "連用形" and p1 == "自立" and nt and nt["s"] in ("、", "，"):
            H.append((I["〜し、・〜り、(gốc động từ + dấu phẩy)"], t["a"], nt["z"]))
        if p == "動詞" and p1 == "非自立" and pv and pv["s"] in ("て", "で") and pv["p"] == "助詞":
            key = ("〜てくる・〜ていく" if b in ("来る", "くる", "行く", "いく") else "〜てみる" if b in ("みる", "見る")
                   else "〜てある" if b == "ある" else "〜てもらう・〜てくれる・〜てあげる"
                   if b in ("もらう", "くれる", "あげる", "いただく", "くださる", "やる") else None)
            if key:
                H.append((I[key], pv["a"], t["z"]))
        if p == "助詞":
            key = ("〜だけ・〜しか〜ない・〜ばかり" if s in ("だけ", "しか", "ばかり") else "〜ほど・〜くらい" if s in ("ほど", "くらい", "ぐらい")
                   else "〜など・〜さえ・〜すら・〜なんて" if s in ("など", "さえ", "すら", "なんて") else None)
            if key:
                H.append((I[key], t["a"], t["z"]))
        if p == "名詞" and p1 == "非自立" and s in ("まま", "うち"):
            H.append((I["〜まま・〜うち"], t["a"], t["z"]))
        if p == "形容詞" and f == "連用テ接続" and s.endswith("く"):
            if nt and nt["s"] == "て":
                H.append((I["〜くて・〜で (nối tính từ)"], t["a"], nt["z"]))
            elif not (nt and nt["b"] in ("ない", "なる")):
                H.append((I["〜く・〜に (trạng từ)"], t["a"], t["z"]))
        if p == "名詞" and p1 == "形容動詞語幹" and nt:
            if nt["s"] == "な":
                H.append((I["〜な + danh từ (tính từ な)"], t["a"], nt["z"]))
            elif nt["s"] == "に":
                H.append((I["〜く・〜に (trạng từ)"], t["a"], nt["z"]))
            elif nt["s"] == "で":
                H.append((I["〜くて・〜で (nối tính từ)"], t["a"], nt["z"]))
        if s in KOSOADO and p in ("名詞", "連体詞", "副詞") and p1 != "接尾":
            H.append((I["こ・そ・あ・ど (これ その そう どう なぜ 何)"], t["a"], t["z"]))
        if p == "名詞" and s in ("際", "側", "等", "氏"):
            H.append((I["〜際・〜側・〜等・〜氏"], t["a"], t["z"]))
    return H


def detect(sent, T=None, raw=False):
    """-> list of (mã keo dán, start, end) trong câu"""
    T = T if T is not None else tokens(sent)
    hits = []
    add = lambda i, a, z: hits.append((i, a, z))
    n = len(T)
    nx = lambda k: T[k] if 0 <= k < n else dict(s="", p="", p1="", b="", f="", a=0, z=0)
    for k, t in enumerate(T):
        s, p, p1, b, f = t["s"], t["p"], t["p1"], t["b"], t["f"]
        pv, nt = nx(k - 1), nx(k + 1)
        if p == "助詞":
            if s == "は" and p1 == "係助詞" and not (pv["s"] in ("で", "じゃ") and nt["b"] == "ない"):
                add(1, t["a"], t["z"])
            elif s == "が":
                add(51 if p1 == "接続助詞" else 2, t["a"], t["z"])
            elif s == "を":
                add(3, t["a"], t["z"])
            elif s == "に" and p1 == "格助詞":
                add(4, t["a"], t["z"])
            elif s == "で" and p1 == "格助詞" and not (nt["s"] == "は" and nx(k + 2)["b"] == "ない"):
                add(5, t["a"], t["z"])
            elif s in ("て", "で") and p1 == "接続助詞":
                if nt["s"] == "も":
                    add(30, t["a"], nt["z"])
                elif nt["b"] in ("いる", "おる") and nt["p"] == "動詞":
                    add(23, t["a"], nt["z"])
                else:
                    add(22, t["a"], t["z"])
            elif s == "の" and p1 in ("連体化", "格助詞"):
                add(6, t["a"], t["z"])
            elif s == "と" and p1 in ("格助詞", "並立助詞", "接続助詞"):
                add(7, t["a"], t["z"])
            elif s == "も" and p1 == "係助詞" and pv["s"] not in ("て", "で"):
                add(8, t["a"], t["z"])
            elif s == "から":
                add(52 if p1 == "接続助詞" else 9, t["a"], t["z"])
            elif s == "まで":
                add(10, t["a"], t["z"])
            elif s == "へ":
                add(11, t["a"], t["z"])
            elif s == "より":
                add(12, t["a"], t["z"])
            elif s == "か" and p1 in ("副助詞／並立助詞／終助詞", "終助詞", "並立助詞", "副助詞"):
                add(13, t["a"], t["z"])
            elif s == "や" and p1 == "並立助詞":
                add(14, t["a"], t["z"])
            elif s == "ので":
                add(52, t["a"], t["z"])
            elif s == "のに" and p1 == "接続助詞":
                add(53, t["a"], t["z"])
            elif s == "ながら":
                add(35, t["a"], t["z"])
            elif s == "ば" and p1 == "接続助詞" and pv["s"] != "なけれ":
                add(27, t["a"], t["z"])
            elif p1 == "終助詞" and s in ("よ", "ね", "な"):
                add(EXTRA_ID[s], t["a"], t["z"])
        elif p == "助動詞":
            if b == "ます":
                if f.startswith("連用") and nt["b"] == "た":
                    add(18, t["a"], nt["z"])
                elif f == "未然形" and nt["s"] == "ん":
                    add(20, t["a"], nt["z"])
                elif f == "未然ウ接続":
                    add(34, t["a"], nt["z"])
                else:
                    add(16, t["a"], t["z"])
            elif b == "た" or (b == "だ" and pv["p"] == "動詞" and pv["f"] == "連用タ接続"):
                if pv["b"] == "ます" or (pv["b"] == "ない" and pv["f"] == "連用タ接続"):
                    pass  # đã tính ở ました / なかった
                elif pv["p"] == "形容詞" and pv["f"] == "連用タ接続":
                    add(44, pv["a"], t["z"])
                elif f == "仮定形":
                    add(28, t["a"], t["z"])
                elif pv["b"] == "だ" and pv["f"] == "連用タ接続":
                    add(45, pv["a"], t["z"])  # だった
                else:
                    add(17, t["a"], t["z"])
            elif b == "ない":
                if f == "連用タ接続" and nt["b"] == "た":
                    add(43 if pv["p"] == "形容詞" else 21, t["a"], nt["z"])
                elif pv["p"] == "形容詞" and pv["f"].startswith("連用テ"):
                    add(43, pv["a"], t["z"])
                elif pv["s"] in ("は", "じゃ"):
                    add(46, nx(k - 2)["a"] if pv["s"] == "は" else pv["a"], t["z"])
                elif f != "仮定形":
                    add(19, t["a"], t["z"])
            elif b == "たい":
                add(24, t["a"], t["z"])
            elif b in ("だ", "です"):
                if f == "仮定形":
                    add(29, t["a"], t["z"])
                elif f.startswith("未然ウ"):
                    add(40, t["a"], nt["z"])
                elif b == "だ" and f == "連用タ接続" and nt["b"] == "た":
                    pass  # だった: tính ở た
                elif b == "だ" and f == "連用形" and nt["b"] == "ある":
                    add(45, t["a"], nt["z"])  # である
                elif nt["b"] in ("ない",) or (b == "だ" and f == "連用形"):
                    pass
                else:
                    add(45, t["a"], t["z"])
            elif b == "らしい":
                add(39, t["a"], t["z"])
            elif b in ("う", "よう") and pv["b"] not in ("だ", "です", "ます"):
                add(34, t["a"], t["z"])
        elif p == "動詞":
            if p1 == "接尾" and b in ("れる", "られる"):
                add(25, t["a"], t["z"])
            elif p1 == "接尾" and b in ("せる", "させる"):
                add(26, t["a"], t["z"])
            elif p1 == "非自立" and b in ("てる", "でる"):
                add(EXTRA_ID["〜てる"], t["a"], t["z"])
            elif f == "基本形" and p1 == "非自立" and b not in ("てる", "でる") and nt["p"] == "名詞" and nt["p1"] not in ("非自立", "接尾", "数"):
                add(57, t["a"], t["z"])      # 読んでいる本
            elif p1 == "自立" and f == "基本形":
                if nt["p"] == "名詞" and (nt["p1"] not in ("非自立", "接尾", "数") or nt["s"] in HEADN):
                    add(57, t["a"], t["z"])
                else:
                    add(15, t["a"], t["z"])
        elif p == "形容詞" and b == "ない":
            if pv["s"] in ("は", "じゃ") and pv["p"] == "助詞":
                add(46, nx(k - 2)["a"] if pv["s"] == "は" and nx(k - 2)["s"] == "で" else pv["a"], t["z"])
            elif f == "連用タ接続" and nt["b"] == "た":
                add(21, t["a"], nt["z"])
            else:
                add(19, t["a"], t["z"])
        elif p == "形容詞" and p1 == "自立" and f == "基本形":
            add(42, t["a"], t["z"])
        elif p == "接続詞":
            if s in ("しかし", "でも", "けれども", "けど", "だけど"):
                add(47, t["a"], t["z"])
            elif s == "そして":
                add(48, t["a"], t["z"])
            elif s == "また":
                add(49, t["a"], t["z"])
        elif p == "名詞":
            if p1 == "非自立" and s in ("の", "こと") and pv["p"] in ("動詞", "形容詞", "助動詞"):
                add(58, t["a"], t["z"])
            elif s in ("とき", "時") and pv["p"] in ("動詞", "助動詞", "形容詞") or (s in ("とき", "時") and pv["s"] == "の"):
                add(54, t["a"], t["z"])
        # mệnh đề "…mà": cụm động từ chia (た/ない) đứng ngay trước danh từ
        if p == "助動詞" and b in ("た", "ない", "だ") and f == "基本形" and nt["p"] == "名詞" and (
                nt["p1"] in ("一般", "サ変接続", "固有名詞", "副詞可能", "形容動詞語幹") or nt["s"] in HEADN):
            add(57, t["a"], t["z"])
    for i, rx in RX:
        for m in rx.finditer(sent):
            add(i, m.start(), m.end())
    hits += detect6(sent, T)
    # mục nhỏ nằm trong mục lớn hơn -> bỏ mục nhỏ (ない trong なければならない, と trong と思う, だ trong んだ…)
    inside = {19: (31, 32, 41, 46), 7: (59, 60), 45: (EXTRA_ID["〜んだ"], 40, 37, 38), 2: (33,), 4: (55, 56) + tuple(
        EXTRA_ID[x] for x in ("に対して", "にとって", "において", "に関する", "に伴い")), 5: (46,), 1: (46,),
              22: (30, 32) + tuple(EXTRA6_ID[x] for x in ("〜てしまう", "〜ておく", "〜てくる・〜ていく", "〜てみる", "〜てある", "〜てもらう・〜てくれる・〜てあげる", "〜てください・〜なさい", "〜くて・〜で (nối tính từ)")),
              8: (30, 32), 15: (33,), 42: (32,), 3: (EXTRA_ID["〜を受けて"],),
              21: (EXTRA6_ID["〜く・〜に (trạng từ)"],), 4: (EXTRA6_ID["〜ようになる・〜ようにする"], EXTRA6_ID["〜ことになる・〜ことにする"])}
    big = [h for h in hits]
    hits = [h for h in hits if not any(b[0] in inside.get(h[0], ()) and b[1] <= h[1] and h[2] <= b[2] for b in big)]
    # bỏ trùng (cùng mã, chồng nhau)
    hits.sort(key=lambda h: (h[0], h[1], -h[2]))
    out = []
    for h in hits:
        if out and out[-1][0] == h[0] and h[1] < out[-1][2]:
            continue
        out.append(h)
    return out if raw else disp_hits(out)


# ---------------- tách câu theo quy tắc vàng ----------------
ROLE = {"は": 1, "が": 2, "を": 3, "に": 4, "で": 5, "の": 6, "と": 7, "も": 8, "から": 9, "まで": 10, "へ": 11,
        "より": 12, "か": 13, "や": 14}


def kind(t):
    p = t["p"]
    if p == "助詞":
        return "p"
    if p in ("動詞", "助動詞") or (p == "形容詞"):
        return "v"
    if p == "名詞" and t["p1"] in ("非自立",) and t["s"] in ("ん", "の") and False:
        return "v"
    if p in ("名詞", "接頭詞"):
        return "n"
    return "o"


def chunks(sent, T=None):
    """Cắt câu thành cụm: [ [ [chữ, loại n/p/v/o, gốc từ], ... ], ... ]. Cụm kết thúc sau trợ từ (trừ の nối danh từ) hoặc dấu 、"""
    T = T if T is not None else tokens(sent)
    out, cur = [], []
    for k, t in enumerate(T):
        if t["p"] == "記号" and t["s"] in "。！？!?":
            continue
        if t["p"] == "接続詞" and cur:
            out.append(cur); cur = []
        if t["s"] == "、" and not cur and out:
            out[-1].append([t["s"], "o", t["s"]]); continue
        cur.append([t["s"], kind(t), t["b"] if t["b"] != "*" else t["s"]])
        nt = T[k + 1] if k + 1 < len(T) else None
        end = False
        if t["p"] == "助詞" and not (t["s"] == "の" and t["p1"] == "連体化") and not (nt and nt["p"] in ("助詞", "助動詞")):
            end = t["p1"] != "接続助詞" or (nt and nt["p"] not in ("動詞",))
        if t["p"] == "助動詞" and t["f"] == "仮定形" and nt and nt["p"] != "助詞":
            end = True
        if t["s"] == "、" or t["p"] == "接続詞":
            end = True
        if end:
            out.append(cur); cur = []
    if cur:
        out.append(cur)
    return out


# ---------------- chia vế (mệnh đề) + chỗ phải đảo khi dịch ----------------
# danh từ "phụ thuộc" nhưng vẫn làm đầu mệnh đề quan hệ: 降った日 (ngày mà mưa), 来た時, 会ったところ…
HEADN = {"日", "時", "とき", "ところ", "所", "頃", "ころ", "前", "後", "間", "場合", "方", "人", "もの", "物", "感じ"}
# Ranh giới vế: dấu 、 hoặc đuôi nối câu. Các vế dịch theo thứ tự trái -> phải; chỉ đảo BÊN TRONG mỗi vế.
BOUND = {"て": 22, "で": 22, "から": 52, "ので": 52, "が": 51, "のに": 53, "ば": 27, "ながら": 35,
         "けど": 47, "けれど": 47, "けれども": 47, "し": None}
VERB_AFTER_TE = {"いる", "おる", "いく", "くる", "しまう", "みる", "おく", "ある", "もらう", "くれる", "あげる",
                 "いただく", "くださる", "ちゃう", "てる"}


def clauses(sent, T=None):
    """-> [dict(a, z, why)] — why: '、' hoặc mã keo dán của đuôi nối (22 〜て, 52 〜から…)"""
    T = T if T is not None else tokens(sent)
    out, start, n = [], 0, len(T)
    pending = None
    for k, t in enumerate(T):
        nt = T[k + 1] if k + 1 < n else None
        why = None
        if t["s"] in ("、", "，", ",") and not (t["s"] == "," and k and nt and T[k - 1]["s"][-1:].isdigit() and nt["s"][:1].isdigit()):
            why = pending or "、"
            pending = None
        elif t["p"] == "助詞" and t["p1"] == "接続助詞" and t["s"] in BOUND:
            if t["s"] in ("て", "で") and nt and (nt["b"] in VERB_AFTER_TE or nt["p1"] == "非自立" or nt["s"] in ("も", "は")):
                why = None
            else:
                why = BOUND[t["s"]] or "し"
        elif t["p"] == "助動詞" and t["f"] == "仮定形" and t["s"] in ("たら", "だら", "なら"):
            why = 29 if t["s"] == "なら" else 28
        if why is not None and why != "、" and nt and nt["s"] in ("、", "，", ","):
            pending = why          # để dấu phẩy đi cùng vế này
            continue
        if why is not None and nt is not None and not all(x["p"] == "記号" for x in T[k + 1:]):
            out.append(dict(a=start, z=t["z"], why=DISP.get(why, why) if isinstance(why, int) else why))
            start = t["z"]
    if start < len(sent):
        out.append(dict(a=start, z=len(sent), why=None))
    return out


def flips(sent, T, a, z, H):
    """Chỗ phải đảo trong vế [a, z): [loại, cụm tiếng Nhật, gợi ý thứ tự tiếng Việt]"""
    ins = [t for t in T if t["a"] >= a and t["z"] <= z]
    out = []
    noun = lambda t: t["p"] == "名詞" or t["p"] == "接頭詞"
    for k, t in enumerate(ins):
        # A の B  ->  B của A
        if t["s"] == "の" and t["p"] == "助詞" and t["p1"] == "連体化" and 0 < k < len(ins) - 1 and noun(ins[k - 1]) and noun(ins[k + 1]):
            i = k - 1
            while i > 0 and noun(ins[i - 1]):
                i -= 1
            j = k + 1
            while j < len(ins) - 1 and noun(ins[j + 1]):
                j += 1
            A = "".join(x["s"] for x in ins[i:k]); B = "".join(x["s"] for x in ins[k + 1:j + 1])
            out.append(["の", A + "の" + B, f"{B} của {A}"])
    # động từ ngay trước danh từ (#57): [mệnh đề] N -> N mà [mệnh đề]
    for h in H:
        if h[0] != DISP[57] or not (a <= h[1] and h[2] <= z):
            continue
        k = next((i for i, t in enumerate(ins) if t["z"] == h[2]), None)
        if k is None or k + 1 >= len(ins) or not noun(ins[k + 1]) or (
                ins[k + 1]["p1"] in ("非自立", "接尾") and ins[k + 1]["s"] not in HEADN):
            continue
        j = k + 1
        while j + 1 < len(ins) and noun(ins[j + 1]) and ins[j + 1]["p1"] != "非自立":
            j += 1
        i = k
        while i > 0 and not (ins[i - 1]["p"] == "助詞" and ins[i - 1]["s"] in ("は", "も")) and ins[i - 1]["p"] != "記号":
            i -= 1
        M = "".join(x["s"] for x in ins[i:k + 1]); N = "".join(x["s"] for x in ins[k + 1:j + 1])
        if M and N:
            out.append(["57", f"[{M}]{N}", f"{N} mà {M}"])
    def back(k):   # đầu mệnh đề bổ nghĩa: lùi tới は/も, dấu câu hoặc đầu vế
        i = k
        while i > 0 and not (ins[i - 1]["p"] == "助詞" and ins[i - 1]["s"] in ("は", "も")) and ins[i - 1]["p"] != "記号":
            i -= 1
        return i
    for k, t in enumerate(ins):
        # [mệnh đề] こと / の  ->  việc / điều mà …
        if t["p"] == "名詞" and t["p1"] == "非自立" and t["s"] in ("こと", "事", "の") and k > 0 and ins[k - 1]["p"] in ("動詞", "助動詞", "形容詞"):
            M = "".join(x["s"] for x in ins[back(k - 1):k])
            if M:
                out.append(["koto", f"[{M}]{t['s']}", f"việc / điều (mà) {M}"])
        # X という N  ->  N (gọi là / tên là) X
        tiu = (t["s"] == "と" and k + 2 < len(ins) and ins[k + 1]["b"] in ("いう", "言う") and noun(ins[k + 2]) and 2) or (
            t["s"] in ("という", "っていう") and k + 1 < len(ins) and noun(ins[k + 1]) and 1)
        if tiu:
            i = k
            while i > 0 and noun(ins[i - 1]):
                i -= 1
            X = "".join(x["s"] for x in ins[i:k]); N = ins[k + tiu]["s"]
            if X:
                out.append(["toiu", f"{X}という{N}", f"{N} (gọi là / tên là) {X}"])
        # tính từ + danh từ  ->  danh từ + tính từ (高い山 = núi cao; 静かな部屋 = phòng yên tĩnh)
        nxt = ins[k + 1] if k + 1 < len(ins) else None
        if nxt and t["p"] == "形容詞" and t["p1"] == "自立" and t["f"] == "基本形" and noun(nxt) and nxt["p1"] not in ("非自立", "接尾"):
            out.append(["adj", t["s"] + nxt["s"], f"{nxt['s']} + {t['s']}"])
        if nxt and k + 2 < len(ins) and t["p1"] == "形容動詞語幹" and nxt["s"] == "な" and noun(ins[k + 2]) and ins[k + 2]["p1"] not in ("非自立", "接尾"):
            out.append(["adj", t["s"] + "な" + ins[k + 2]["s"], f"{ins[k + 2]['s']} + {t['s']}"])
    # を + động từ  ->  động từ trước, tân ngữ sau
    for k, t in enumerate(ins):
        if t["s"] == "を" and t["p"] == "助詞":
            v = next((x for x in ins[k + 1:] if x["p"] == "動詞" and x["p1"] == "自立"), None)
            i = k
            while i > 0 and (noun(ins[i - 1]) or (ins[i - 1]["s"] == "の" and i > 1)):
                i -= 1
            O = "".join(x["s"] for x in ins[i:k])
            if v and O:
                out.append(["を", O + "を…" + v["s"], f"{v['b']} → {O}"])
    return out[:5]
