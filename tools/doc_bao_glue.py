#!/usr/bin/env python3
"""Nhận diện 60 "keo dán" + từ kana/văn báo của trang lộ trình đọc hiểu (docs/kanji-viewer/lo-trinh-doc-hieu.html)
và tách câu theo "quy tắc vàng" (động từ ở cuối, cụm theo trợ từ). Dùng trong tools/doc_bao_vocab.py.

Cần: pip install janome   (tách từ tiếng Nhật, thuần Python)
"""
import re

# (mã, nhóm, mẫu, nghĩa) — số 1–60 đúng thứ tự trên trang lộ trình; 61+ là bảng ⑤ "Từ viết bằng kana & cụm văn báo".
GROUPS = ["Trợ từ", "Đuôi động từ", "Phỏng đoán · nghe nói", "Tính từ · danh từ", "Nối câu", "Cấu trúc câu",
          "⑤ Trợ từ ghép", "⑤ Trạng từ", "⑤ Văn báo", "⑤ Dạng thường (truyện)", "⑤ Kính ngữ"]
GLUE = [
    (1, 0, "は", "còn nói về… (chủ đề)"), (2, 0, "が", "chủ ngữ / cái được nhấn"),
    (3, 0, "を", "tân ngữ (làm gì cái gì)"), (4, 0, "に", "tới, vào, lúc, cho"),
    (5, 0, "で", "tại (nơi làm), bằng"), (6, 0, "の", "của: A の B = B của A"),
    (7, 0, "と", "và · với · rằng"), (8, 0, "も", "cũng"), (9, 0, "から", "từ"),
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
    (47, 4, "しかし・でも", "nhưng"), (48, 4, "そして", "và rồi"), (49, 4, "また", "ngoài ra · lại"),
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
    (8, "〜を受けて", "sau khi / do (sự việc)", r"を受け"), (8, "〜とした", "cho rằng · tuyên bố", r"とした(?!い)"),
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
META = {i: (g, pat, mean) for i, g, pat, mean in GLUE}

RX = [(31, r"(なけれ[ばど]|なきゃ|なくては|なくちゃ)(なら|いけ)?(ない|なかった|ません)?"), (32, r"[てで]も?(いい|良い|よい|かまわ|構わ)"),
      (33, r"ことができ|ことが出来|ことができ"), (36, r"ために|ため、|ためだ|ための"),
      (37, r"そう(だ|です|な|に)"), (38, r"よう(だ|です|な|に)|みたい"), (40, r"だろう|でしょう"),
      (41, r"かもしれ|かも知れ"), (46, r"ではな|じゃな|ではありませ|じゃありませ"), (50, r"だから|そのため|ですから"),
      (55, r"によると|によれば"), (56, r"について|につき"), (59, r"という|といった|っていう|との"),
      (60, r"と(言[っうわいえ]|い[っうわ]|思[っうわいえ]|考え)|って(言|思)")]
RX = [(i, re.compile(r)) for i, r in RX] + [(EXTRA_ID[p], re.compile(r)) for g, p, m, r in EXTRA if r]

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


def detect(sent, T=None):
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
            elif p1 == "自立" and f == "基本形":
                if nt["p"] == "名詞" and nt["p1"] not in ("非自立", "接尾"):
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
        if p == "助動詞" and b in ("た", "ない") and f == "基本形" and nt["p"] == "名詞" and nt["p1"] in ("一般", "サ変接続", "固有名詞"):
            add(57, t["a"], t["z"])
    for i, rx in RX:
        for m in rx.finditer(sent):
            add(i, m.start(), m.end())
    # mục nhỏ nằm trong mục lớn hơn -> bỏ mục nhỏ (ない trong なければならない, と trong と思う, だ trong んだ…)
    inside = {19: (31, 32, 41, 46), 7: (59, 60), 45: (EXTRA_ID["〜んだ"], 40, 37, 38), 2: (33,), 4: (55, 56) + tuple(
        EXTRA_ID[x] for x in ("に対して", "にとって", "において", "に関する", "に伴い")), 5: (46,), 1: (46,),
              22: (30, 32), 8: (30, 32), 15: (33,), 42: (32,), 3: (EXTRA_ID["〜を受けて"],)}
    big = [h for h in hits]
    hits = [h for h in hits if not any(b[0] in inside.get(h[0], ()) and b[1] <= h[1] and h[2] <= b[2] for b in big)]
    # bỏ trùng (cùng mã, chồng nhau)
    hits.sort(key=lambda h: (h[0], h[1], -h[2]))
    out = []
    for h in hits:
        if out and out[-1][0] == h[0] and h[1] < out[-1][2]:
            continue
        out.append(h)
    return out


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
