"""Danh sách mẫu ngữ pháp cho "Ngữ pháp trong lời bài hát" — theo đúng thứ tự lý thuyết
của 19 chương (trang Xem Tất Cả). Dùng bởi tools/song_grammar.py.

Mỗi chương: [(tên nhóm = đề mục lý thuyết, [(tên mẫu, spec), ...]), ...]

spec:
  "re:<regex>"     regex trên cả dòng (không phân biệt hoa thường), in đậm phần khớp
  "tg:<nhãn>"      nhãn của bộ gắn nhãn spaCy dùng cho Bản đồ ngữ pháp ETS/IELTS (so khớp đầu chuỗi)
  "fn:<tên>"       hàm Python bên dưới, trả (char_start, char_end) hoặc None
  chuỗi khác       mẫu token (spaCy Matcher) — các token cách nhau bởi dấu cách:
                     word / a|an   chữ thường        @lemma / @a|b   lemma      @~re  lemma regex
                     #TAG / #A|B   tag (VBD, NNS…)   $POS / $A|B     POS        %dep / %a|b  quan hệ phụ thuộc
                     ~re           chữ thường khớp regex (toàn bộ)        .  token bất kỳ
                     ghép điều kiện bằng &, phủ định bằng ! (vd !#VBN, !a|the)
                     tiền tố ? * + là OP (vd ?$ADV)
                     < ở đầu: phải đứng đầu dòng · > ở cuối: phải đứng cuối dòng
  ("and", spec, spec2)  khớp spec (in đậm) và dòng phải khớp thêm spec2
  [spec, spec, ...]     một trong các spec
"""

PERS = "i|you|he|she|we|they"
SUBJ = "i|you|he|she|we|they|it"
BE_PRES = "am|is|are|'s|'re|'m"
OBJ = "me|you|him|her|us|them|it"

CHAPTERS = {}

# ============================================================== 1. DANH TỪ
CHAPTERS["noun"] = [
    ("Danh từ chung và danh từ riêng", [
        ("Danh từ riêng (tên người, địa danh, ngày tháng — viết hoa)",
         r"re:\b(London|Paris|New York|California|Texas|Tennessee|Mississippi|Alabama|Georgia|Memphis|Hollywood|Mexico|Jerusalem|Jesus|Mary|Monday|Friday|Saturday|Sunday|December|July|June|September|Christmas|America|England|Tokyo|Chicago|Vegas|Louisiana|Kentucky|Ohio|Brooklyn)\b"),
        ("Danh từ chung đếm được số ít (a/the + N)", "a|the $ADJ? #NN&%nsubj|dobj|pobj"),
    ]),
    ("Cách thành lập danh từ số nhiều", [
        ("Thêm -s", "#NNS&~[a-z]*[^se]s&!~(.*ss|lyrics|news)"),
        ("Thêm -es (sau -s, -x, -ch, -sh, -o)", "#NNS&~[a-z]+(ches|shes|xes|sses|oes)"),
        ("Phụ âm + y → -ies", "#NNS&~[a-z]+[^aeiou]ies"),
        ("-f/-fe → -ves", "#NNS&~(lives|wives|knives|leaves|wolves|halves|shelves|thieves|loaves|calves|scarves|selves)"),
        ("Số nhiều bất quy tắc (men, women, children, feet, teeth…)",
         "~(men|women|children|feet|teeth|mice|geese|oxen)&$NOUN"),
        ("Danh từ số nhiều không đổi hình thức (sheep, fish, deer…)", "~(sheep|fish|deer|species|aircraft|salmon)&$NOUN"),
        ("Danh từ luôn ở số nhiều (jeans, clothes, scissors…)",
         "~(jeans|clothes|trousers|scissors|pants|shorts|pajamas|pyjamas|sunglasses|binoculars|glasses)&#NNS"),
        ("Danh từ không đếm được (không -s, không a/an)", "tg:Danh từ không đếm được"),
    ]),
    ("Danh từ đơn và danh từ ghép", [
        ("Danh từ ghép N + N (viết rời)", "tg:Danh từ ghép (N + N)"),
        ("Danh từ ghép viết liền (heartbeat, sunshine, midnight…)",
         "~(sunshine|moonlight|heartbeat|heartbreak|daylight|rainbow|sunset|sunrise|midnight|weekend|bedroom|highway|lifetime|nightmare|daydream|wildfire|starlight|firework|fireworks|raindrops?|snowflakes?|teardrops?|heartache|sweetheart|goodbye|railroad|homeland|bloodline|skyline|wildflowers?|downtown|lipstick|seashore|graveyard|footsteps?)&$NOUN|INTJ"),
        ("Danh từ ghép có gạch nối", r"re:\b(merry-go-rounds?|forget-me-nots?|\w+-in-law|passer-by|x-rays?|t-shirts?|break-ups?|make-up|hide-and-seek|hand-me-downs?|good-byes?|know-it-alls?|ex-(boyfriend|girlfriend|lover|wife|husband)s?|self-(esteem|control|respect|love|pity|doubt|defense|defence)|hang-ups?|drive-ins?|pick-ups?|show-offs?|warm-ups?|grown-ups?|check-ins?|rock-and-roll|jack-in-the-box|son-of-a-gun|go-betweens?|has-beens?|daydreams?|lie-ins?)\b"),
        ("Danh từ ghép V-ing + N (danh động từ bổ nghĩa)", "tg:Danh từ ghép V-ing + N"),
        ("Số nhiều của danh từ ghép (passers-by, …-in-law)", r"re:\b(passers-by|\w+s-in-law|\w+-in-law)\b"),
    ]),
    ("Cách phát âm đuôi -s/-es của danh từ số nhiều", [
        ("/s/ sau âm vô thanh p, t, k, f, θ", "#NNS&~[a-z]+(ps|ts|ks|fs|ths|pes|tes|kes)&!~.*(ates|ites|otes|utes)"),
        ("/ɪz/ sau âm gió s, z, ʃ, tʃ, dʒ", "#NNS&~[a-z]+(ses|ches|shes|xes|zes|ges|ces)"),
        ("/z/ sau nguyên âm và phụ âm hữu thanh", "#NNS&~[a-z]+([aeiouy]s|ns|ms|ls|rs|gs|ds|bs|vs|ws)&!~.*(ses|ces|ges|zes)"),
    ]),
    ("Chức năng của danh từ", [
        ("Danh từ làm chủ ngữ", "<$DET? $ADJ? $NOUN&%nsubj $AUX|VERB"),
        ("Danh từ làm tân ngữ trực tiếp", "$VERB $DET|PRON $ADJ? $NOUN&%dobj"),
        ("Danh từ làm bổ ngữ của chủ ngữ (sau be/become)", "@be|become&%ROOT $DET $ADJ? $NOUN&%attr"),
        ("Danh từ làm tân ngữ của giới từ", "$ADP&%prep $DET|PRON $ADJ? $NOUN&%pobj"),
        ("Đồng vị ngữ (N, N bổ sung)", "tg:Đồng vị ngữ"),
    ]),
    ("Sở hữu cách", [
        ("N + 's + N", "$NOUN|PROPN 's&#POS $ADJ? $NOUN"),
        ("Danh từ số nhiều + ' (s')", "#NNS '&#POS $NOUN"),
        ("Sở hữu cách với thời gian (today's, a day's…)", "~(today|tomorrow|yesterday|tonight|night|day|week|year|lifetime|moment|hour) 's&#POS $NOUN"),
        ("Sở hữu với of (the end of the road)", "the $NOUN of the|my|your|our|this $NOUN"),
        ("Sở hữu cách rút gọn (at my mother's…)", r"re:\b(at|to|from) (my|the|your|his|her|our) \w+'s(?=[ ,.!?]*$)"),
        ("Thay thế danh từ bị sở hữu (than John's, like mine)",
         r"re:\b(than|like|as) (?!(it|he|she|that|what|there|who|let|here|where|how|everybody|everyone|nobody|somebody|one)'s)[a-z]+'s(?=[ ,.!?]*$)"),
        ("Sở hữu kép (a friend of mine)", r"re:\b(a|an|this|that|some) \w+ of (mine|yours|his|hers|ours|theirs)\b"),
    ]),
    ("Cách thành lập danh từ", [
        ("Hậu tố -tion/-sion", "$NOUN&~[a-z]{3,}(tion|sion)s?"),
        ("Hậu tố -ment", "$NOUN&~[a-z]{3,}ments?&!~(moments?|comments?)"),
        ("Hậu tố -ness", "$NOUN&~[a-z]{3,}ness(es)?"),
        ("Hậu tố -ity/-ty", "$NOUN&~[a-z]{3,}(ity|ities)"),
        ("Hậu tố -ance/-ence", "$NOUN&~[a-z]{3,}(ance|ence)s?&!~(dance|chance|romance|silence|fence|sentence|science|since|once|hence)"),
        ("Hậu tố -ship/-hood/-dom", "$NOUN&~[a-z]{3,}(ship|hood|dom)s?&!~(condoms?|randoms?)"),
        ("Hậu tố chỉ người -er/-or", "$NOUN&~(lover|dreamer|believer|singer|dancer|stranger|driver|preacher|rider|fighter|leader|killer|teacher|player|sinner|loser|winner|keeper|seeker|hunter|runner|writer|actor|sailor|doctor|creator|survivor|traveler|traveller|liar|beggar)s?"),
        ("Hậu tố chỉ người khác (-ist, -ian, -ant, -ee)", "$NOUN&~(artist|tourist|guitarist|pianist|scientist|terrorist|novelist|musician|magician|politician|comedian|guardian|servant|giant|assistant|immigrant|employee|refugee|attendee)s?"),
        ("Tiền tố + danh từ (mis-, dis-, super-, ex-, over-…)",
         r"re:\b(misunderstanding|disbelief|disorder|discomfort|dishonou?r|disgrace|disrespect|unrest|overtime|overdose|overdrive|underworld|superstar|superhero|superman|supernova|subway|ex-boyfriend|ex-girlfriend|ex-lover|ex-wife|ex-husband|non-stop|afterlife|outlaw|outcast|upside)\b"),
        ("Hậu tố sau tính từ (-ness, -th, -dom…: happiness, truth, freedom)",
         "$NOUN&~(happiness|sadness|darkness|loneliness|kindness|emptiness|madness|weakness|sweetness|truth|strength|length|warmth|depth|width|youth|freedom|wisdom|boredom|honesty|beauty|loyalty|cruelty|safety)"),
    ]),
]

# ============================================================== 2. ĐẠI TỪ
CHAPTERS["pron"] = [
    ("Đại từ nhân xưng", [
        ("Đại từ chủ ngữ (he/she/we/they + V)", "he|she|we|they&%nsubj $AUX|VERB"),
        ("Đại từ tân ngữ sau động từ (V + me/him/her/us/them)", "$VERB me|him|her|us|them&%dobj"),
        ("Đại từ tân ngữ sau giới từ (with me, for you…)", "with|for|to|without|about|from|on|at me|him|her|us|them&%pobj"),
        ("Đại từ sở hữu (mine, yours, hers, ours, theirs)", "~(mine|yours|hers|ours|theirs)&$PRON"),
        ("Tính từ sở hữu + N (my/your/our + N)", "tg:Tính từ sở hữu + N"),
        ("It làm chủ ngữ giả (it's + adj + to V)", "it 's|is|was ?$ADV $ADJ to $VERB"),
        ("It chỉ thời tiết/thời gian/khoảng cách", r"re:\bit('s| is| was) (raining|snowing|cold|hot|late|early|dark|midnight|morning|getting (late|dark|cold))\b"),
    ]),
    ("Đại từ phản thân và đại từ nhấn mạnh", [
        ("Đại từ phản thân làm tân ngữ (hurt myself…)", "$VERB myself|yourself|himself|herself|ourselves|themselves|itself&%dobj"),
        ("Đại từ phản thân sau giới từ (to/for/with myself)", "to|for|with|about|at|of|in myself|yourself|himself|herself|ourselves|themselves"),
        ("by + oneself (một mình)", "by myself|yourself|himself|herself|ourselves|themselves|itself"),
        ("Đại từ nhấn mạnh (I myself / did it myself)",
         [ "i|you|he|she|we|they myself|yourself|himself|herself|ourselves|themselves",
           r"re:\b(did|do|made|make|built|wrote|said) (it|this|that) (myself|yourself|ourselves|himself|herself)\b"]),
    ]),
    ("Đại từ chỉ định", [
        ("this/that/these/those thay cho danh từ", "tg:Đại từ chỉ định"),
        ("Chỉ thời gian (this morning, those days…)", "this|that|these|those morning|night|day|time|year|summer|days|nights|moment|week|winter|evening"),
        ("Nhấn mạnh / thể hiện cảm xúc (That's amazing!)",
         r"re:^(oh,? )?(that|this) (is|was|'s) (so |really |just |pretty )?(amazing|beautiful|crazy|great|awful|insane|funny|cool|sad|perfect|wonderful|incredible|terrible)\b"),
        ("Giới thiệu / gọi điện (This is…, It's me)", r"re:\b(this is|it's) (me|your \w+|\w+) (calling|speaking)\b|\b(hello|hi|hey),? (it's|this is) me\b|^(it's|this is) me\b"),
        ("Thay thế ý tưởng (that's what/why/how…)", r"re:\b(that's|that is|that was) (what|why|how|the way|all|the reason|the thing)\b"),
        ("That/those nhắc chuyện xa (those were the days)", r"re:\b(those were the|those days|those nights|that summer|that night)\b"),
    ]),
    ("Đại từ nghi vấn", [
        ("who (ai — làm chủ ngữ)", "<who $AUX|VERB&!#VBN"),
        ("whom (ai — làm tân ngữ)", "whom"),
        ("whose (của ai)", "<whose $NOUN|AUX"),
        ("which (cái nào)", "<which $NOUN|AUX|VERB"),
        ("what (cái gì)", "<what @do|be|have|can|will|would|should $PRON|DET"),
    ]),
    ("Đại từ quan hệ", [
        ("who (thay cho người)", "$NOUN|PRON who&%nsubj $AUX|VERB"),
        ("which / that (thay cho vật)", "$NOUN which|that&%nsubj|nsubjpass|dobj $AUX|VERB|PRON"),
        ("whose (sở hữu)", "$NOUN|PRON whose $NOUN"),
        ("those who … (những người mà)", "tg:those who"),
    ]),
    ("Đại từ bất định", [
        ("some-/any-/every-/no- + one/body (someone, nobody…)", "~(someone|somebody|anyone|anybody|everyone|everybody|nobody)"),
        ("…thing (something, anything, nothing, everything)", "~(something|anything|nothing|everything)&%nsubj|dobj|pobj|attr"),
        ("…where (somewhere, anywhere, nowhere, everywhere)", "~(somewhere|anywhere|nowhere|everywhere)"),
        ("Đại từ bất định + tính từ (something new)", "~(something|anything|nothing|everything|someone|somebody|anyone|nobody|everyone) $ADJ&!~(else|more)"),
        ("Đại từ bất định + else", "~(something|anything|nothing|everything|someone|somebody|anyone|anybody|nobody|everyone|everybody|somewhere|anywhere|nowhere) else"),
        ("Đại từ bất định + động từ số ít", "~(everybody|everyone|nobody|somebody|everything|nothing|someone|anyone|anything) #VBZ"),
        ("one/ones thay cho danh từ", "tg:one/ones"),
    ]),
    ("Đại từ hỗ tương", [
        ("each other / one another", ["each other", "one another"]),
    ]),
]

# ============================================================== 3. HÒA HỢP S-V
CHAPTERS["sva"] = [
    ("Động từ số ít", [
        ("Danh từ số ít + V số ít", "the|my|your|this|that|a $ADJ? #NN&%nsubj #VBZ"),
        ("V-ing làm chủ ngữ → động từ số ít", "tg:V-ing làm chủ ngữ"),
        ("To V làm chủ ngữ → động từ số ít", r"re:^to (love|live|be|die|know|lose|hold|find|leave|have|see|feel|dream|fall)\b( \w+){0,4} (is|was)\b"),
        ("Mệnh đề làm chủ ngữ (What I need is…)", r"re:\b(what|all) (i|you|we|she|he|they) (really )?(need|want|know|feel|see|do|did|said|got|have|wanted|needed|ask|asked|get)( \w+){0,2} (is|was)\b"),
        ("Đại từ bất định + V số ít (everybody wants…)", "~(everybody|everyone|nobody|somebody|everything|nothing|someone|anyone|no-one) #VBZ"),
        ("each / every + N số ít + V số ít", "each|every $NOUN&#NN #VBZ"),
        ("each/either/neither/none/one of + N số nhiều + V số ít",
         "each|neither|either|none|one of the|my|your|these|those|us|them|you ?#NNS was|is|has|does|'s|knows|wants|seems"),
        ("More than one / Many a + N số ít + V số ít", r"re:\b(more than one|many a) \w+( \w+)? (is|was|has)\b|\bmany a \w+"),
        ("Danh từ tận cùng -s nhưng số ít (news, politics…)", r"re:\b(the news|news|physics|mathematics|politics|economics|measles|the united states) (is|was|has|says)\b|\bgood news\b"),
        ("Khoảng thời gian / tiền / khoảng cách + V số ít", r"re:\b(\w+|a hundred|a thousand|a million) (years|miles|dollars|hours|minutes|days|weeks|months) (is|was|seems|feels) "),
    ]),
    ("Động từ số nhiều", [
        ("Hai chủ ngữ nối bằng and → V số nhiều", ["$NOUN|PROPN|PRON and $DET? $NOUN|PROPN|PRON&%conj #VBP|VBD&@be|have",
                                                    r"re:\b(you and i|you and me|me and you|he and i|she and i) (are|were|have|go|walk|know|belong|got)\b"]),
        ("Hai danh từ cùng chỉ một (rock and roll is…)", r"re:\b(rock and roll|rock 'n' roll|rock n roll|rock n' roll|bread and butter|peace and quiet) (is|was|has|will|ain't|never)\b"),
        ("with / along with / as well as không đổi số của chủ ngữ", r"re:\b(along with|together with|as well as|accompanied by)\b"),
        ("either … or / neither … nor (V theo chủ ngữ gần)", r"re:\b(either|neither) \w+( \w+)? (or|nor) \w+( \w+)? (is|are|was|were|has|have|knows|cares|can|will)\b"),
        ("A number of (+ V số nhiều) / The number of (+ V số ít)", r"re:\b(a|the) number of \w+"),
        ("there is / there's + N số ít", "there is|'s|was a|an|no|nothing|something|somebody|someone|only|one"),
        ("there are / there were + N số nhiều", "there are|were|'re ?$ADV ?$DET|NUM ?$ADJ #NNS"),
        ("people / police (luôn số nhiều)", "the? people|police|cattle&%nsubj #VBP|VBD&!was"),
        ("the + tính từ (the rich, the young) + V số nhiều", "the rich|poor|young|old|brave|lonely|dead|living|wicked|weak|strong|free|blind|lost|broken|weary&%nsubj #VBP|VBD|MD"),
    ]),
    ("Danh từ tập hợp", [
        ("Danh từ tập hợp + V (family, team, crowd…)", "my|the|our|your family|team|crowd|band|army|crew|audience|jury|choir|gang&%nsubj $AUX|VERB"),
        ("Phân số / some / all / most of + N (V theo N)", r"re:\b(half|most|some|all|none|a lot|lots|plenty|the rest) of (the |my |your |our |this |these |those )?\w+ (is|are|was|were)\b"),
    ]),
]

# ============================================================== 4. TÍNH TỪ
CHAPTERS["adj"] = [
    ("Vị trí của tính từ", [
        ("Vị trí thuộc ngữ (Adj + N)", "$DET|PRON $ADJ&%amod $NOUN"),
        ("Vị trí vị ngữ (be + Adj)", "$PRON|NOUN&%nsubj @be&%ROOT ?$ADV $ADJ&%acomp&!~.*(in'|ing)"),
        ("Sau động từ nối (feel/look/seem/become + Adj)", "tg:Tính từ sau động từ nối"),
        ("Tính từ chỉ đứng vị ngữ (afraid, alone, alive, asleep, awake…)",
         "@be|feel|stay|fall|seem|keep|lie|come ?$ADV ~(afraid|alone|alive|asleep|awake|aware|ashamed|alike|ablaze|afloat|adrift)"),
        ("Tính từ chỉ đứng thuộc ngữ (main, only, mere, sheer, elder…)",
         "the|my|your|a ~(main|mere|sheer|former|elder|eldest|inner|outer|upper|utter)&$ADJ $NOUN"),
    ]),
    ("Khác nghĩa ở vị trí thuộc ngữ / vị ngữ", [
        ("late / present / concerned / responsible…",
         r"re:\b(the present (day|moment|time)|my late \w+|the late \w+|(i'm|you're|we're|he's|she's|is|was|am) (so |too )?late\b|(i'm|you're|is|am) (not )?present\b|(is|am|are|i'm) responsible)\b"),
    ]),
    ("Tính từ đứng sau danh từ và đại từ", [
        ("Sau đại từ bất định (something special)", "~(something|anything|nothing|everything|someone|somebody|anyone|nobody|everyone|somewhere|nowhere) $ADJ&!~(else|more|less)"),
        ("Sau danh từ đo lường (ten feet tall, years old)", "$NUM ~(feet|foot|years|miles|inches|meters|metres|stories) tall|old|long|high|deep|wide|away"),
        ("Cụm tính từ theo sau danh từ (a heart full of…)", "$NOUN ~(full|free|ready|afraid|happy|proud|tired|sick|worth|alive|able|deep|filled|lost)&$ADJ|VERB of|from|for|to|with|in"),
    ]),
    ("Động từ + tân ngữ + tính từ", [
        ("make / keep / leave / find / drive + O + Adj", "tg:Tính từ sau tân ngữ"),
    ]),
    ("Tính từ mô tả và tính từ giới hạn", [
        ("Tính từ mô tả (beautiful, old, cold…)", "$DET|PRON ~(beautiful|lonely|cold|old|little|sweet|wild|broken|young|dark|bright|empty|golden|silent)&$ADJ $NOUN"),
        ("Số đếm (two hearts, a thousand years)", "~(one|two|three|four|five|six|seven|eight|nine|ten|hundred|thousand|million)&$NUM #NNS"),
        ("Số thứ tự (the first time, the last dance)", "the|my|our|your ~(first|second|third|last|final|next)&$ADJ $NOUN"),
        ("Tính từ chỉ định (this/that/these/those + N)", "this|that|these|those&%det $NOUN"),
        ("Tính từ phân phối (each, every, either, neither + N)", "either|neither|each|every&%det $NOUN&#NN"),
        ("Tính từ chỉ số lượng (many, few, much, some, no + N)", "many|few|much|several|no|enough&%det|amod $NOUN"),
        ("Tính từ nghi vấn (what/which/whose + N)", "<what|which|whose&%det $NOUN $AUX|VERB|PRON"),
    ]),
    ("Tính từ đơn và tính từ ghép", [
        ("Tính từ ghép có gạch nối", "tg:Tính từ ghép có gạch nối"),
        ("Adj/N + V3 (broken-hearted, blue-eyed…)", r"re:\b\w+-(hearted|eyed|haired|minded|faced|headed|skinned|legged|made|born|bound|sighted|blooded|dressed|built)\b"),
        ("N/Adj + V-ing (heartbreaking, good-looking…)", r"re:\b(\w+-(breaking|looking|lasting|loving|burning|killing|shattering|feeling|making|growing|moving|blowing|shaking|stopping|warming|aching|fearing|tearing)|heartbreaking|breathtaking|mouthwatering|record-breaking|mind-blowing|earth-shaking)\b"),
        ("Số + N (two-way, five-star, one-night…)", r"re:\b(one|two|three|four|five|six|seven|eight|nine|ten|twenty|hundred|thousand|million|single|double)-(way|star|night|horse|dollar|year|day|time|man|room|lane|mile|story|track|minute|hour|piece|bedroom|word|faced|sided|of-a-kind|eyed|legged|tone|step|stop|shot|room)\b"),
    ]),
    ("Thành lập tính từ bằng hậu tố sau danh từ", [
        ("-ful (beautiful, careful…)", "$ADJ&~[a-z]{3,}ful"),
        ("-less (hopeless, endless…)", "$ADJ&~[a-z]{3,}less&!~(unless|bless|less)"),
        ("-ous (dangerous, famous…)", "$ADJ&~[a-z]{3,}ous"),
        ("-al / -ic (magical, electric…)", "$ADJ&~[a-z]{3,}(al|ic|ical)&!~(real|deal)"),
        ("-y (cloudy, sunny, crazy…)", "$ADJ&~(cloudy|rainy|sunny|windy|snowy|stormy|dirty|bloody|dusty|smoky|misty|foggy|icy|salty|starry|sleepy|thirsty|hungry|lucky|noisy|healthy|wealthy|messy|dreamy|shady|rocky|muddy|greedy|guilty|hearty|sexy|moody|bumpy|filthy|frosty)"),
        ("-ly (lovely, lonely, friendly…)", "$ADJ&~(lovely|lonely|friendly|lively|deadly|heavenly|ugly|costly|lowly|holy|silly|manly|motherly|fatherly|brotherly|ghostly|timely|godly|worldly|homely|daily|weekly|yearly|nightly)"),
        ("-ish / -like (childish, foolish, childlike)", "$ADJ&~[a-z]{3,}(ish|like)&!~(english|polish|finish|unlike|alike)"),
    ]),
    ("Thành lập tính từ bằng hậu tố sau động từ", [
        ("-able / -ible (unbreakable, incredible…)", "$ADJ&~[a-z]{3,}(able|ible)&!~(table|vegetable)"),
        ("-ive (creative, positive…)", "$ADJ&~[a-z]{3,}ive&!~(alive|give|live|five|forgive|survive|drive|arrive|olive)"),
        ("-ent / -ant (different, important…)", "$ADJ&~[a-z]{3,}(ent|ant)"),
    ]),
    ("Phân từ dùng như tính từ", [
        ("Tính từ đuôi -ing (tính chất / gây ra cảm xúc)", "tg:Tính từ đuôi -ing"),
        ("Tính từ đuôi -ed (người cảm nhận)", "tg:Tính từ đuôi -ed"),
        ("Phân từ hiện tại đứng trước N (burning fire)", "tg:Tính từ dạng V-ing"),
        ("Phân từ quá khứ đứng trước N (broken heart)", "tg:Tính từ dạng V3/-ed"),
    ]),
    ("Trật tự của tính từ khi đứng trước danh từ", [
        ("Hai/ba tính từ trước danh từ (OSASCOMP)", "$DET|PRON $ADJ&%amod&!~(only|other|same|next|last|first|own|whole|very|little) ,? ?and $ADJ&%amod $NOUN"),
    ]),
    ("Tính từ dùng như danh từ (the + tính từ)", [
        ("the rich, the poor, the young, the brave…",
         r"re:\bthe (rich|poor|young|old|brave|lonely|dead|living|wicked|weak|strong|free|blind|lost|broken|wild|unknown|homeless|innocent|chosen|damned|restless|righteous|faithful|weary|hopeless|meek|hungry|sick|wounded|wise|beautiful|lonesome)\b(?= (and|are|will|who|were|get|have|shall|can|in|of|never|always|don't|ones?)\b|[,.!?]*$)"),
    ]),
]

# ============================================================== 5. TRẠNG TỪ
CHAPTERS["adv"] = [
    ("Dạng của trạng từ", [
        ("Tính từ + -ly", "$ADV&~[a-z]{3,}ly&!~(only|early|likely|daily|holy|ugly|lonely|lovely|silly|family)"),
        ("Trạng từ cùng dạng tính từ (fast, hard, late, high…)", "$VERB ?$PRON ~(fast|hard|late|high|deep|straight|far|wrong|low|close|free|loud|tight|wide)&$ADV"),
        ("hard ≠ hardly, late ≠ lately, high ≠ highly…", "~(hardly|lately|highly|deeply|closely|nearly|freely|rightly|shortly|wrongly)&$ADV"),
        ("well — trạng từ của good", "@do|sing|dance|play|know|sleep|treat|go|work|speak|mean|eat|live|age|hide|fit|pay|serve|end|spend|write ?$PRON|NOUN well&$ADV&%advmod"),
    ]),
    ("Trạng từ chỉ cách thức", [
        ("V + trạng từ cách thức (slowly, softly, gently…)", "$VERB ?$PRON|DET ?$NOUN ~(slowly|quickly|softly|gently|quietly|carefully|easily|badly|madly|sweetly|tenderly|beautifully|happily|sadly|silently|desperately|wildly|loudly|perfectly|patiently|nervously|honestly|bravely|freely|blindly|endlessly|truly|deeply)"),
    ]),
    ("Trạng từ chỉ nơi chốn", [
        ("here, there, away, home, everywhere, outside…", "$VERB ?$PRON ~(here|there|everywhere|nowhere|somewhere|away|home|outside|inside|upstairs|downstairs|abroad|anywhere|overseas|nearby|around)&$ADV&%advmod"),
    ]),
    ("Trạng từ chỉ thời gian", [
        ("now, today, tonight, tomorrow, soon, later…", "tg:Trạng từ chỉ thời gian"),
        ("already / yet / still", ["already&$ADV", r"re:\byet[,.!?]*$", "still&$ADV&%advmod $AUX|VERB"]),
        ("tonight / tomorrow / yesterday", "~(tonight|tomorrow|yesterday)&%npadvmod|advmod"),
    ]),
    ("Trạng từ chỉ tần suất không xác định", [
        ("always", "always"),
        ("never", "never&%neg|advmod $AUX|VERB"),
        ("sometimes / often / usually", "~(sometimes|often|usually)"),
        ("rarely / seldom / hardly ever", ["~(rarely|seldom)", "hardly ever"]),
        ("ever (trong câu hỏi / phủ định)", "ever&$ADV&!~(forever|whatever|however)"),
    ]),
    ("Trạng từ chỉ tần suất xác định", [
        ("every day / every night / every time", r"re:\bevery (single )?(day|night|morning|time|week|year|hour|minute|second|now and then)\b"),
        ("once / twice / three times + a day…", r"re:\b(once|twice|(two|three|four|five|ten|a hundred|a thousand|a million) times)( (a|in a|every|per) (day|night|week|year|lifetime|while|minute|row))?\b"),
        ("daily / weekly / nightly / yearly", "~(daily|weekly|nightly|hourly|yearly|annually)&$ADV|ADJ"),
    ]),
    ("Trạng từ chỉ mức độ", [
        ("very / so / too / really / quite + Adj/Adv", "tg:Trạng từ chỉ mức độ + tính từ/trạng từ"),
        ("too + Adj (quá…)", "too&$ADV $ADJ"),
        ("quite / rather / pretty / fairly + Adj", "~(quite|rather|pretty|fairly|kinda|extremely|incredibly|totally|completely|absolutely)&$ADV $ADJ"),
        ("almost / nearly / barely (xấp xỉ)", "~(almost|nearly|barely|practically|virtually)&$ADV"),
        ("even / only (nhấn mạnh)", ["tg:Trạng từ nhấn mạnh even", "tg:Trạng từ nhấn mạnh only"]),
    ]),
    ("Vị trí của trạng từ", [
        ("Đầu câu (Suddenly, Maybe, Someday…)", ["tg:Trạng từ đầu câu", "<~(suddenly|maybe|someday|sometimes|perhaps|tonight|tomorrow|finally|now|honestly|slowly)&$ADV ,? $PRON&%nsubj"]),
        ("Giữa câu — trước động từ chính", "tg:Trạng từ đứng trước động từ"),
        ("Giữa câu — sau động từ be", "@be&!%aux ~(always|never|still|usually|sometimes|often|rarely|seldom|already|just|really|ever|only|probably)&$ADV"),
        ("Giữa trợ động từ và động từ chính", "tg:Trạng từ đứng giữa trợ động từ và động từ chính"),
        ("Có 2 trợ động từ → trạng từ sau trợ động từ đầu",
         r"re:\b(will|would|could|should|might|must|may|have|has|had|i'll|you'll|i'd|you'd|i've|you've)( not|n't)? (always|never|still|just|really|already|ever|probably|forever|surely|truly|only) (have|be|been)\b"),
        ("Cuối câu (sau động từ / tân ngữ)", "tg:Trạng từ đứng sau động từ/tân ngữ"),
    ]),
    ("Trật tự khi có nhiều trạng từ (cách thức – nơi chốn – thời gian)", [
        ("Nơi chốn + thời gian / cách thức + nơi chốn",
         ["~(here|there|home|away|back|outside) ~(tonight|today|tomorrow|now|forever|again|anymore|tonight|yesterday)&$ADV|NOUN",
          "$ADV&~[a-z]{3,}ly ~(here|there|home|away|around|tonight|today|now|again|forever|together|alone)&$ADV"]),
    ]),
    ("Cách thành lập trạng từ", [
        ("-y → -ily (happily, easily…)", "~(happily|easily|angrily|lazily|busily|heavily|readily|steadily|merrily|luckily|hungrily|greedily|noisily|clumsily|wearily|cheerily|crazily|gloomily|sleepily|bloodily|uneasily|unhappily|necessarily|ordinarily|temporarily|momentarily|primarily|voluntarily|hastily|prettily|shakily|dizzily|guiltily|warily|lustily|stealthily|speedily)"),
        ("-le → -ly (gently, simply, terribly…)", "~(gently|simply|terribly|possibly|horribly|humbly|incredibly|probably|subtly|visibly|miserably|comfortably|idly|nobly|impossibly|invisibly|irresistibly|terribly)"),
        ("-ic → -ically (basically, tragically…)", "~[a-z]+ically"),
        ("true → truly, full → fully", "~(truly|fully|duly|wholly)"),
    ]),
    ("Đảo ngữ sau trạng từ chỉ nơi chốn / hướng chuyển động", [
        ("Here/There + V + S (Here comes the sun)", r"re:\b(here (comes|come|goes|go|stands|lies|is|was|went|came)|there (comes|come|goes|go|stands|lies|went|came)) (the|my|your|a|another|that|our|his|her|this)\b"),
        ("Here/There + đại từ + V (không đảo: Here she comes)", r"re:\b(here|there) (she|he|it|they|we|you|i) (comes|goes|go|come|is|are|was|were|went|came)\b"),
        ("Down/Up/Out/Away + V + S", r"re:^(down|up|out|in|away|off|around|over|on|back) (came|comes|went|goes|flew|flies|ran|runs|fell|falls|rolled|rolls) (the|my|a|an|his|her|our|their)\b"),
    ]),
    ("Đảo ngữ sau trạng từ phủ định", [
        ("Never / Rarely / Seldom + trợ động từ + S",
         r"re:^(never|rarely|seldom|nowhere)( (before|again|in (my|your) life|once))?,? (have|has|had|did|do|does|will|would|could|can|was|were|is|am|shall) (i|you|he|she|we|they|it|there)\b"),
        ("Cụm từ bắt đầu bằng not (Not once, Not until…)", r"re:^not (once|until|a (single )?(day|word|night|minute|soul|thing|moment|chance|second)|one (day|night)|even)\b"),
        ("Cụm từ mang nghĩa phủ định (in no way, under no circumstances…)", r"re:\b(in no way|on no account|under no circumstances|at no time|by no means|in no time|no way)\b"),
        ("Little (với nghĩa phủ định)", r"re:^little (did|do|does|have|had|was|were) (i|you|he|she|we|they|it)\b|\blittle did (i|you|he|she|we|they)\b"),
    ]),
]

# ============================================================== 6. SO SÁNH
CHAPTERS["comp"] = [
    ("So sánh bằng", [
        ("as + Adj/Adv + as", "as $ADJ|ADV as"),
        ("not as/so + Adj + as", "not|n't ?@be ?$ADV as|so $ADJ|ADV as"),
        ("as many/much + N + as", "as many|much ?$NOUN as"),
        ("the same (+ N) + as", "the same ?$NOUN as"),
        ("Bội số (twice as … as, three times as …)", r"re:\b(twice|half|(two|three|four|five|ten|a hundred|a thousand|a million) times) as \w+( \w+)? as\b"),
        ("like / alike / different from", ["@be|look|feel|sound|seem ?$ADV like&$ADP|SCONJ", "different from|than|to"]),
    ]),
    ("So sánh hơn", [
        ("Tính từ ngắn + -er + than", "#JJR|RBR&~[a-z]+er&!~(never|ever|over|other|after|under|forever|together|whatever|wherever|however|whenever|neither|either) than"),
        ("more + Adj/Adv dài + than", "more $ADJ|ADV than"),
        ("So sánh hơn không có than", "tg:So sánh hơn (không có than)"),
        ("more + V3 (more tired, more scared)", "more ~[a-z]+ed&$ADJ|VERB&!~(need|indeed)"),
        ("more + fun / real / right / wrong", "more fun|real|right|wrong"),
        ("less + Adj/Adv (+ than)", "less $ADJ|ADV ?than"),
        ("Nhấn mạnh: much/far/a lot/even/way + so sánh hơn", "much|far|even|way|lot|bit|little|lots #JJR|RBR"),
        ("So sánh hơn với danh từ (more/fewer/less + N)", "tg:So sánh hơn với danh từ"),
    ]),
    ("So sánh nhất", [
        ("the + Adj ngắn + -est", "the #JJS&~[a-z]+est"),
        ("the most + Adj dài", "the most $ADJ"),
        ("the least + Adj/N", "the least $ADJ|NOUN"),
        ("Tính từ sở hữu + so sánh nhất (my best friend)", "my|your|his|her|our|their #JJS ?$NOUN"),
        ("one of the + so sánh nhất + N số nhiều", "tg:one of the"),
        ("So sánh nhất + in/of (the best in the world)", "the #JJS ?$NOUN in|of the|my|all $NOUN"),
        ("So sánh nhất + (that) S + have ever + V3", r"re:\bthe (\w+est|most \w+|best|worst) (\w+ )?(that )?(i|you|we|i've|you've|we've|i'd|she|he) (have |'ve |has |had )?(ever|never) \w+"),
        ("by far + so sánh nhất", ["tg:by far", r"re:\bby far( the)? \w+|\b(the )?\w+est by far\b|\b(the )?(best|worst|most \w+) by far\b"]),
    ]),
    ("Cách thêm đuôi -er/-est", [
        ("Gấp đôi phụ âm cuối (bigger, hotter, saddest…)", "~(bigger|biggest|hotter|hottest|sadder|saddest|thinner|thinnest|fatter|wetter|redder|madder|fitter|flatter)"),
        ("Phụ âm + y → -ier / -iest (happier, prettiest…)", "#JJR|JJS|RBR&~[a-z]+(ier|iest)"),
        ("Tận cùng -e → thêm -r / -st (closer, nicest…)", "~(closer|closest|nicer|nicest|wiser|wisest|braver|bravest|larger|largest|safer|safest|stranger|strangest|truer|truest|finer|finest|purer|purest|bluer|freer|later|latest|wider)&#JJR|JJS|RBR"),
    ]),
    ("Hình thức so sánh bất quy tắc", [
        ("good/well → better → best", "~(better|best)&#JJR|JJS|RBR|RBS"),
        ("bad/badly → worse → worst", "~(worse|worst)"),
        ("far → farther/further → farthest/furthest", "~(farther|further|farthest|furthest)"),
        ("many/much → more → most; little → less → least", "~(more|most|less|least)&#JJR|JJS|RBR|RBS $NOUN"),
    ]),
    ("More, most, less, least, fewer, fewest", [
        ("fewer/fewest + N số nhiều", "~(fewer|fewest) ?$ADJ ?$NOUN"),
        ("more/less + N + than", "more|less $NOUN than"),
    ]),
    ("So sánh kép", [
        ("So sánh đồng tiến (the … the …)", r"re:\bthe (\w+er|more( \w+)?|less( \w+)?|better|worse|further|farther)\b[^.!?]{0,40}?,? the (\w+er|more|less|better|worse|further|farther)\b"),
        ("So sánh lũy tiến (more and more, better and better)", ["#JJR|RBR and #JJR|RBR", "more and more ?$ADJ|ADV", "less and less"]),
    ]),
]

# ============================================================== 7. ĐỘNG TỪ
CHAPTERS["verb"] = [
    ("Cách thành lập động từ", [
        ("Hậu tố -ize/-ise (realize, apologize…)", "@~(realize|realise|apologize|apologise|recognize|recognise|memorize|criticize|sympathize|fantasize|hypnotize|paralyze|mesmerize|idolize|romanticize|harmonize|vaporize|minimize|maximize|energize|organize|emphasize|summarize|visualize|terrorize|finalize|hypnotise|paralyse|mesmerise|fantasise)"),
        ("Hậu tố -en (brighten, frighten, weaken…)", "@~(brighten|darken|frighten|lighten|soften|harden|tighten|weaken|strengthen|widen|deepen|sharpen|loosen|sweeten|shorten|lengthen|threaten|awaken|enlighten|flatten|quicken|straighten|heighten|broaden|worsen|fasten|redden|sadden|madden|deafen|dampen|liven)"),
        ("Hậu tố -ify (testify, glorify, purify…)", "@~[a-z]{2,}ify&$VERB"),
        ("Tiền tố en- (enable, ensure, enrich…)", "@~en(able|large|sure|danger|courage|rich|slave|trust|chant|circle|close|dear|force|joy|list|rage|tangle|vision|dure|gulf|lighten|title)&$VERB"),
    ]),
    ("Ngoại động từ và nội động từ", [
        ("Ngoại động từ + tân ngữ", "$PRON&%nsubj $VERB&%ROOT ?$DET|PRON ?$ADJ $NOUN|PRON&%dobj"),
        ("Nội động từ (không có tân ngữ)", "fn:intransitive"),
        ("Động từ + 2 tân ngữ (give me your hand)", "tg:Động từ + 2 tân ngữ"),
    ]),
    ("Trợ động từ be, do, have", [
        ("do/does/did nhấn mạnh (I do love you)", "$PRON&%nsubj do|does|did&%aux ?$ADV $VERB&#VB"),
        ("do/does/did + not (phủ định)", "do|does|did n't|not $VERB&#VB"),
        ("have/has/had làm trợ động từ (hoàn thành)", "have|has|had|'ve&%aux ?$ADV #VBN"),
    ]),
    ("Động từ khuyết thiếu (modal verbs)", [
        ("can + V (khả năng)", "can|ca&#MD ?$ADV $VERB&#VB"),
        ("can't / cannot + V", "ca|can n't|not $VERB&#VB"),
        ("could + V", "could&#MD ?$ADV $VERB&#VB"),
        ("be able to + V", "@be ?$ADV able to $VERB"),
        ("may + V", "may&#MD ?$ADV $VERB&#VB"),
        ("might + V", "might&#MD ?$ADV $VERB&#VB"),
        ("must + V (bắt buộc)", "must&#MD ?$ADV $VERB&#VB&!be"),
        ("must be (suy luận chắc chắn)", "must be"),
        ("have to / has to / had to + V", "@have to $VERB&#VB"),
        ("gotta / got to (văn nói = have to)", r"re:\b(gotta|got to)\b"),
        ("don't have to (không cần)", "do|does|did n't|not have to"),
        ("mustn't (cấm)", "must n't|not"),
        ("should + V", "should&#MD ?$ADV $VERB&#VB"),
        ("ought to + V", "ought ?not to"),
        ("would + V", "would|'d&#MD ?$ADV $VERB&#VB"),
        ("Would/Could/Can/Will you…? (lời đề nghị lịch sự)", "<would|could|can|will you ?$ADV $VERB&#VB"),
        ("shall", "shall"),
        ("need (động từ khuyết thiếu / động từ thường)", ["need n't|not", "@need to $VERB"]),
        ("dare (dám) / How dare you", ["@dare ?not ?to $VERB", "how dare"]),
        ("used to + V (thói quen quá khứ)", "used to $VERB&#VB"),
        ("be/get used to + V-ing / N (quen với)", "@be|get ?$ADV used to $VERB|NOUN|PRON&!#VB"),
        ("had better + V", "had|'d better $VERB|ADV"),
        ("would rather + V", "would|'d rather $VERB|ADV"),
        ("should have + V3 (lẽ ra nên)", r"re:\bshould(n't)?( have|'ve|a) \w+"),
        ("could have + V3", r"re:\bcould(n't)?( have|'ve) \w+"),
        ("would have + V3", r"re:\b(would(n't)?|i'd|you'd|we'd|she'd|he'd|they'd)( have|'ve) \w+"),
        ("must / might / may have + V3 (suy đoán quá khứ)", r"re:\b(must|might|may)( not)?( have|'ve) \w+"),
    ]),
    ("Động từ + giới từ / tính từ + giới từ", [
        ("Động từ + giới từ thường dùng", "tg:Động từ + giới từ"),
        ("Động từ + tân ngữ + giới từ", "tg:Động từ + tân ngữ + giới từ"),
        ("Tính từ + giới từ thường dùng", "tg:Tính từ + giới từ"),
    ]),
    ("Liên động từ (linking verbs)", [
        ("feel / look / sound / seem / smell / taste + Adj", "@feel|look|sound|seem|smell|taste|appear ?$ADV $ADJ&%acomp"),
        ("become / get / grow / turn / go + Adj (biến đổi)", "@become|get|grow|turn|go ?$ADV $ADJ&%acomp"),
        ("stay / remain / keep + Adj", "@stay|remain|keep ?$ADV $ADJ&%acomp"),
        ("Liên động từ + danh từ (become a…)", "@become|remain|seem $DET $ADJ? $NOUN&%attr"),
    ]),
    ("Thể sai khiến và câu giả định", [
        ("have/get + O + V3 (nhờ/thuê làm)", "tg:Thể sai khiến"),
        ("Câu giả định (suggest/insist that + S + V)", r"re:\b(suggest|suggested|suggests|insist|insisted|demand|demanded|recommend|recommended|require|required|request|requested|important|essential|vital|necessary|propose|proposed) that (he|she|you|we|they|i|it|everyone|nobody|the \w+) (be|go|stay|come|have|leave|take|do|give|keep|not|get|make|say|wait|sing|pray|love)\b"),
    ]),
]

# ============================================================== 8. CỤM ĐỘNG TỪ
CHAPTERS["phr"] = [
    ("Nghĩa của cụm động từ", [
        ("Nghĩa đen (go out, come back, sit down…)", "@go|come|sit|stand|walk|run|fall|lie|jump|climb|look|get ~(up|down|out|in|back|away|around|off|over|inside|outside)&%prt|advmod"),
        ("Nghĩa bóng (give up, break up, figure out…)", "@give|break|make|figure|find|work|turn|put|let|move|show|take|pick|call|hang|wake|grow|calm|cheer|light|shut|hold|carry|back ~(up|on|out|down|off|over|in|back|away)&%prt"),
        ("Cụm động từ nói chung (V + tiểu từ)", "tg:Cụm động từ"),
    ]),
    ("Intransitive phrasal verbs (không tân ngữ)", [
        ("give up / grow up / hold on / carry on / calm down…",
         "@give|grow|hold|carry|show|wake|calm|break|move|go|come|hang|fall|cheer|back|slow|shut|settle|sit|stand|stay|fade|run|get|keep|break up|on|down|in|out|apart|away|off|over|back|along|through&%prt >"),
    ]),
    ("Transitive phrasal verbs — tách được", [
        ("V + đại từ + tiểu từ (turn it off, let me down)", "$VERB $PRON&%dobj ~(up|down|out|off|on|in|away|back|over|around|apart)&%prt"),
        ("V + tiểu từ + danh từ (pick up the phone)", "$VERB ~(up|down|out|off|on|away|back|over)&%prt $DET|PRON ?$ADJ $NOUN&%dobj"),
    ]),
    ("Transitive phrasal verbs — không tách được", [
        ("look after/for, get over, go through, run into, count on…",
         r"re:\b(look(s|ed|ing)? (after|for)|get(s|ting)? over|got over|go(es|ing)? through|went through|been through|run(s|ning)? into|ran into|come(s)? across|came across|take(s)? after|took after|count(s|ing)? on|rel(y|ies|ied) on|depend(s|ed)? on|stand(s|ing)? by|stood by|deal(s|t)? with) (me|you|him|her|us|them|it|the|my|your|this|that|our|his)\b"),
    ]),
    ("Three-word phrasal verbs", [
        ("look forward to, put up with, run out of, come up with…",
         r"re:\b(look(ing|ed|s)? forward to|get(ting)? away with|got away with|put(ting)? up with|run(ning)? out of|ran out of|catch(ing)? up (with|on)|come up with|came up with|keep(ing)? up with|kept up with|give up on|gave up on|giving up on|look(ed)? up to|get(ting)? along with|hold(ing)? on to|held on to|live up to|make up for|made up for|get rid of|got rid of|walk(ed)? out on|run(ning)? away from|ran away from|cut back on|go along with|stand up for|stood up for|break up with|broke up with|end(ed)? up with|look(ing)? out for|get back to|came back to|come back to)\b"),
    ]),
]

# ============================================================== 9. BỊ ĐỘNG
CHAPTERS["pass"] = [
    ("Cấu trúc tổng quát (be + V3) theo từng thì", [
        ("Hiện tại đơn: am/is/are + V3", "am|is|are|'s|'re|'m&%auxpass ?$ADV #VBN"),
        ("Quá khứ đơn: was/were + V3", "was|were&%auxpass ?$ADV #VBN"),
        ("Hiện tại hoàn thành: have/has been + V3", "have|has|'ve|'s ?$ADV been&%auxpass ?$ADV #VBN"),
        ("Quá khứ hoàn thành: had been + V3", "had|'d been&%auxpass ?$ADV #VBN"),
        ("Hiện tại tiếp diễn: am/is/are being + V3", "am|is|are|'s|'re|'m being&%auxpass #VBN"),
        ("Quá khứ tiếp diễn: was/were being + V3", "was|were being&%auxpass #VBN"),
        ("Tương lai đơn: will be + V3", "will|'ll|wo ?n't ?$ADV be&%auxpass ?$ADV #VBN"),
        ("be going to be + V3", "going to be&%auxpass #VBN|JJ"),
    ]),
    ("Giữ / bỏ by + tác nhân", [
        ("Có by + tác nhân", "#VBN by&%agent ?$DET ?$ADJ $NOUN|PRON|PROPN"),
    ]),
    ("Bị động với động từ khuyết thiếu", [
        ("modal + be + V3 (can be done)", "can|could|may|might|must|should|would|ca ?n't ?$ADV be&%auxpass ?$ADV #VBN"),
        ("modal + have been + V3", "could|should|would|might|must|may|'d ?n't have|'ve been&%auxpass #VBN"),
    ]),
    ("Bị động với 2 tân ngữ", [
        ("I was given / told / shown / sent / promised…", "@be&%auxpass ?$ADV given|told|sent|shown|offered|taught|promised|handed|granted|paid|lent|owed|denied|left $PRON|DET|NOUN|PART|ADP|SCONJ"),
    ]),
    ("Bị động với động từ nguyên mẫu và danh động từ", [
        ("to be + V3 (want to be loved)", "to be&%auxpass ?$ADV #VBN"),
        ("being + V3 (being loved)", "!@be being&%auxpass #VBN"),
        ("be + V3 + to V (be asked/expected/supposed to)", "tg:Bị động + to V"),
    ]),
    ("Bị động với mệnh đề that (reporting passive)", [
        ("It is said / believed / known that…", r"re:\b(it is|it's|it was) (said|believed|known|thought|rumou?red|written|told|reported|foretold|prophesied)( that)?\b"),
        ("S + be + said / supposed / meant / born + to V", r"re:\b(is|are|was|were|'s|'re|am|'m) (said|believed|supposed|known|thought|meant|destined|born|made|built|bound) to \w+"),
    ]),
    ("Get-passive (văn nói)", [
        ("get/got + V3 (get hurt, got caught…)", ["@get&%auxpass ?$ADV #VBN", "@get hurt|caught|lost|married|killed|burned|burnt|broken|paid|left|played|fired|dumped|stuck|kicked|thrown|shot|laid|robbed|busted|tangled"]),
    ]),
    ("Rút gọn mệnh đề bị động", [
        ("N + V3 (a heart broken by…)", "tg:Rút gọn MĐQH bị động"),
    ]),
    ("Bẫy: nội động từ không có bị động (happen, die, arrive…)", [
        ("happen / die / arrive / appear / disappear / exist (chủ động)", "$NOUN|PRON&%nsubj ?$AUX @happen|die|arrive|appear|disappear|exist|occur|fall|rise|emerge&%ROOT"),
    ]),
]

# ============================================================== 10. TO V / V-ING
CHAPTERS["inf"] = [
    ("Động từ + to V", [
        ("want/need/try/decide/learn/promise… + to V", "tg:Động từ + to V"),
        ("wanna / gonna / gotta (văn nói: want to / going to / got to)", r"re:\b(wanna|gonna|gotta|wanted to|tryna)\b"),
    ]),
    ("Động từ + V-ing", [
        ("enjoy/keep/avoid/mind/finish/imagine/miss + V-ing", "@keep|enjoy|avoid|mind|finish|imagine|miss|quit|risk|deny|admit|consider|practice|resist|delay|postpone ?$ADV #VBG"),
        ("can't help + V-ing", "ca|can n't|not help #VBG"),
        ("Động từ + V-ing (nói chung)", "tg:Động từ + V-ing"),
    ]),
    ("Động từ + giới từ + V-ing", [
        ("think of / dream of / talk about / insist on + V-ing", "@think|dream|talk|insist|succeed|believe|keep|give|stop|apologize|worry|care|feel|plan|go of|about|on|in|from|for|like #VBG"),
        ("Giới từ + V-ing (nói chung)", "tg:Giới từ + V-ing"),
        ("to (giới từ) + V-ing (look forward to…)", "tg:To (giới từ) + V-ing"),
    ]),
    ("Động từ + to V hoặc V-ing (nghĩa không đổi)", [
        ("begin/start/like/love/hate/continue + to V", "@begin|start|like|love|hate|continue|prefer to $VERB&#VB"),
        ("begin/start/like/love/hate/continue + V-ing", "@begin|start|like|love|hate|continue|prefer #VBG&%xcomp"),
    ]),
    ("Động từ + to V hoặc V-ing (nghĩa thay đổi)", [
        ("remember/forget + V-ing (nhớ/quên đã làm)", "@remember|forget #VBG"),
        ("remember/forget + to V (nhớ/quên phải làm)", "@remember|forget to $VERB&#VB"),
        ("stop + V-ing (ngừng làm)", "@stop #VBG&!going"),
        ("stop + to V (dừng lại để làm)", "@stop to $VERB&#VB"),
        ("try + to V (cố gắng) / try + V-ing (thử)", ["@try to $VERB&#VB", "@try #VBG"]),
        ("regret / mean + to V / V-ing", ["@regret #VBG|to", "@mean to $VERB", "@mean #VBG"]),
    ]),
    ("Động từ + tân ngữ + to V", [
        ("want/ask/tell/need + O + to V", "tg:Động từ + O + to V"),
    ]),
    ("Động từ + V nguyên mẫu không to", [
        ("let + O + V", "@let $PRON|PROPN|NOUN $VERB&#VB"),
        ("make + O + V", "@make $PRON|NOUN&%nsubj|dobj $VERB&#VB"),
        ("help + O + (to) V", "@help $PRON ?to $VERB&#VB"),
        ("see/hear/watch/feel + O + V / V-ing", "@see|hear|watch|feel|notice $PRON|NOUN $VERB&#VB|VBG"),
        ("Modal / had better / would rather / why not + V", ["tg:%s + O + V nguyên mẫu", "why not $VERB"]),
    ]),
    ("Tính từ + to V", [
        ("Adj + to V (happy to, ready to, afraid to…)", "tg:Tính từ + to V"),
        ("too + Adj + to V / Adj + enough + to V", "tg:too/enough + to V"),
    ]),
    ("To V chỉ mục đích", [
        ("To V chỉ mục đích", "tg:To V chỉ mục đích"),
        ("in order to / so as to + V", ["tg:In order to", r"re:\b(in order (not )?to|so as (not )?to)\b"]),
    ]),
    ("Danh động từ làm chủ ngữ / bổ ngữ", [
        ("V-ing làm chủ ngữ", "tg:V-ing (danh động từ) làm chủ ngữ"),
        ("Từ để hỏi + to V (how/what/where to V)", "tg:Từ để hỏi + to V"),
        ("Danh từ/đại từ + to V (nothing to lose, a reason to…)", "tg:Danh từ/đại từ + to V"),
        ("be + to V (kế hoạch / sắp đặt)", "tg:be + to V"),
    ]),
]

# ============================================================== 11. GIỚI TỪ
_ADJP = lambda adjs, p: "~(%s)&$ADJ %s" % (adjs, p)
_NP = lambda ns, p: "~(%s)&$NOUN %s" % (ns, p)
_VP = lambda vs, p: "@~(%s)&$VERB ?$PRON %s" % (vs, p)
CHAPTERS["prep"] = [
    ("Vị trí của giới từ trong câu", [
        ("Giới từ đứng cuối câu (who are you talking to?)", r"re:^(who|what|where|which)\b.* (to|for|from|with|about|of|at|on|in)[?!.]*$"),
        ("Giới từ + danh từ/đại từ (cụm giới từ)", "$ADP&%prep $DET $ADJ? $NOUN&%pobj >"),
        ("Giới từ kép / cụm giới từ (because of, in front of…)", "tg:Giới từ kép"),
    ]),
    ("Giới từ chỉ nơi chốn", [
        ("in (bên trong: in the dark, in my arms)", "in the|my|your|his|her $ADJ? ~(dark|rain|room|house|car|bed|sky|world|city|night|middle|arms|heart|eyes|air|sea|water|crowd|corner|street|garden|kitchen|mirror|wind)"),
        ("at (tại điểm: at the door, at home)", "at the|my|your ?$ADJ ~(door|corner|bar|station|party|top|bottom|end|edge|window|table|gate|start|beach|club|altar|crossroads|wheel)"),
        ("on (trên bề mặt: on the floor, on my mind)", "on the|my|your ?$ADJ ~(floor|wall|table|road|street|radio|phone|screen|ground|bed|roof|shoulder|mind|lips|side|beach|stage|dance)"),
        ("under / over / above / below", "~(under|over|above|below|beneath|underneath)&%prep the|my|your|a|our ?$ADJ $NOUN"),
        ("between / among", "~(between|among|amongst)&%prep"),
        ("behind / in front of / next to / beside / near", ["~(behind|beside|near|opposite)&%prep $DET|PRON", "in front of", "next to"]),
        ("inside / outside / across / around", "~(inside|outside|across|around|throughout)&%prep the|my|your|this|our"),
        ("Giới từ nơi chốn (tổng hợp)", "tg:Giới từ chỉ nơi chốn"),
    ]),
    ("Giới từ chỉ thời gian", [
        ("in + tháng/năm/mùa/buổi (in the morning)", "in the? ~(morning|evening|afternoon|summer|winter|spring|fall|autumn|night|daytime|end|past|future|meantime|beginning|[0-9]{4}|january|february|march|april|may|june|july|august|september|october|november|december)"),
        ("on + ngày/thứ (on Sunday, on Christmas Day)", "on ?a ~(monday|tuesday|wednesday|thursday|friday|saturday|sunday|christmas|weekends?|holidays?|birthday)|my|your|the"),
        ("at + giờ/thời điểm (at night, at midnight)", "at ~(night|midnight|dawn|noon|sunrise|sunset|first|last|once|times|christmas|the)"),
        ("for (trong khoảng) / since (từ khi)", ["for $DET|NUM|ADJ ?$ADJ ~(years|days|weeks|months|hours|minutes|nights|ages|while|lifetime|time|seconds)", "since $DET|NUM|PROPN ?$NOUN&!%mark"]),
        ("during / within / throughout", "~(during|within|throughout)&%prep"),
        ("by (trước/muộn nhất) / until / till", ["by ~(tomorrow|tonight|morning|now|then|midnight|the)&!%agent", "~(until|till|'til|til)&%prep"]),
        ("from … to / from … till", "from $NOUN|PROPN|DET ?$NOUN to|till|until $NOUN|PROPN|DET"),
        ("before / after + N", "~(before|after)&%prep $DET|PRON|NOUN ?$NOUN"),
        ("Giới từ thời gian (tổng hợp)", "tg:Giới từ chỉ thời gian"),
    ]),
    ("Giới từ chỉ phương hướng / chuyển động", [
        ("to / into / onto", "$VERB ~(to|into|onto)&%prep the|my|your|a|this ?$ADJ $NOUN"),
        ("out of / off / away from", ["out of the|my|your|this", "away from", "$VERB off the|my|your"]),
        ("through / across / along / past / towards", "$VERB ~(through|across|along|past|towards|toward)&%prep"),
        ("up / down + N (up the hill, down the road)", "$VERB up|down&%prep the|my|this|that ?$ADJ $NOUN"),
    ]),
    ("Giới từ chỉ nguyên nhân và lí do", [
        ("because of / due to / thanks to / out of (love)", r"re:\b(because of|due to|thanks to|owing to|out of (love|fear|spite|pity|respect|kindness|jealousy|curiosity|habit))\b"),
        ("for / from (chết vì, run vì…)", r"re:\b(die|died|dying|cry|cried|crying|shaking|trembling|suffer(ing)?) (for|from|of) (love|you|fear|cold|a broken heart|hunger|pain|loneliness)\b"),
    ]),
    ("Giới từ so sánh và tương phản", [
        ("like + N (giống như — so sánh ví von)", "like&$ADP a|an|the $ADJ? $NOUN"),
        ("as + N (với tư cách là)", "as&$ADP a|an|your|my $ADJ? $NOUN >"),
        ("unlike / despite / in spite of", ["unlike&$ADP", "despite", "in spite of"]),
    ]),
    ("Giới từ chỉ sự sở hữu", [
        ("of (friend of mine)", "$NOUN of $PRON&~(mine|yours|his|hers|ours|theirs)"),
        ("with / without (có / không có)", ["$NOUN with $DET ?$ADJ $NOUN", "without $DET|PRON ?$ADJ $NOUN"]),
    ]),
    ("Giới từ chỉ mục đích và kết quả", [
        ("for + N/đại từ (mục đích)", "$VERB ?$PRON|DET ?$NOUN for you|me|us|love|money|fun|good|real|nothing|sure"),
        ("to + one's + N (to my surprise)", r"re:\bto (my|your|his|her|our|their) (surprise|delight|dismay|horror|amazement|disappointment|shame|regret)\b"),
    ]),
    ("Tính từ + giới từ", [
        ("Adj + ABOUT", _ADJP("crazy|sorry|worried|sure|serious|mad|nervous|excited|right|wrong|careful|honest|curious|anxious|wild|happy|sad|upset|concerned", "about")),
        ("Adj + TO", _ADJP("kind|close|nice|good|mean|cruel|used|similar|married|addicted|attached|loyal|true|faithful|new|polite|rude|grateful|thankful|open|blind", "to")),
        ("Adj + FROM", _ADJP("different|far|free|safe|absent|away|separate|apart", "from")),
        ("Adj + FOR", _ADJP("ready|sorry|responsible|famous|good|bad|late|grateful|thankful|perfect|enough|hungry|eager|desperate|right", "for")),
        ("Adj + WITH", _ADJP("angry|happy|bored|fed|familiar|pleased|satisfied|busy|crowded|filled|wrong|done|obsessed|careful|patient|honest|content|okay|ok", "with")),
        ("Adj + AT", _ADJP("good|bad|surprised|mad|amazed|angry|clever|terrible|great|shocked|brilliant|hopeless", "at")),
        ("Adj + IN", _ADJP("interested|lost|involved|rich|successful|confident|caught|trapped|stuck|wrapped|dressed|covered", "in")),
        ("Adj + ON", _ADJP("keen|dependent|hard|easy|hooked|based|sweet|soft|tough|high", "on")),
        ("Adj + OF", _ADJP("afraid|scared|proud|tired|sick|full|aware|capable|fond|jealous|ashamed|sure|certain|worthy|guilty|free|short|terrified|careful", "of")),
    ]),
    ("Danh từ + giới từ", [
        ("N + OF", _NP("fear|lack|smell|taste|end|thought|memories|memory|sound|piece|part|kind|sort|thousands|hundreds|million|edge|top|middle|out|sake|light|name", "of")),
        ("N + TO", _NP("key|answer|way|road|door|invitation|reply|solution|ticket|stairway|highway|letter|visit|attention|access|welcome|return", "to")),
        ("N + FOR", _NP("love|need|reason|desire|demand|respect|search|room|time|place|cure|hope|chance|reward|thanks|wish|price|excuse", "for")),
        ("N + IN", _NP("change|faith|interest|belief|rise|increase|decrease|trust|pride|role|part|lesson|experience", "in")),
        ("N + WITH / BETWEEN", _NP("relationship|problem|difference|distance|connection|contact|trouble|fight|deal|date|peace|war|love|nothing|something|space|wall|line", "with|between")),
        ("Danh từ + giới từ (tổng hợp)", "tg:Danh từ + giới từ"),
    ]),
    ("Động từ + giới từ", [
        ("V + FROM", _VP("escape|suffer|hide|run|come|protect|keep|save|stay|recover|differ|borrow|rescue|walk|fall|break", "from")),
        ("V + TO", _VP("listen|belong|talk|happen|lead|apologize|apologise|speak|reply|object|refer|explain|pray|sing|dance|whisper|lie|turn|get|go|come|run|cling|hold", "to")),
        ("V + ABOUT", _VP("think|dream|talk|care|worry|know|forget|sing|tell|hear|complain|lie|cry|write|ask|learn|wonder|joke", "about")),
        ("V + FOR", _VP("wait|look|pray|fight|ask|care|live|die|hope|search|apply|pay|cry|long|beg|stand|fall|reach|vote|wish", "for")),
        ("V + WITH", _VP("deal|agree|stay|stick|play|share|lie|dance|argue|fight|cope|mess|live|go|come|run|sleep|fall|talk|walk|cover|fill", "with")),
        ("V + AT", _VP("look|stare|laugh|smile|shout|aim|point|yell|glance|wink|scream|throw|arrive|knock|wave", "at")),
        ("V + IN", _VP("believe|live|trust|succeed|participate|lose|drown|bathe|stay|hide|join|result|specialize|invest|lock", "in")),
        ("V + INTO", _VP("fall|turn|run|look|walk|crash|dive|disappear|bump|get|change|break|fade|step|melt|sink|grow", "into")),
        ("V + ON", _VP("depend|rely|count|focus|insist|hold|concentrate|live|carry|move|turn|lean|spend|pass|wait|try|work|call", "on")),
        ("Động từ + giới từ (tổng hợp)", "tg:Động từ + giới từ"),
    ]),
]

# ============================================================== 12. LIÊN TỪ
CHAPTERS["conj"] = [
    ("Vị trí của liên từ trong câu", [
        ("Nối hai từ (black and white, now or never)", ["$ADJ and|or|but $ADJ&%conj", "$NOUN and|or $NOUN&%conj", "now or never"]),
        ("Nối hai cụm từ (in the dark or in the light)", "$ADP $DET ?$ADJ $NOUN and|or|but $ADP $DET ?$ADJ $NOUN"),
        ("Nối hai mệnh đề (…, but I…)", "tg:Liên từ đẳng lập nối 2 mệnh đề"),
        ("and nối 2 động từ song song", "tg:and nối 2 động từ"),
    ]),
    ("Liên từ kết hợp (FANBOYS)", [
        ("for (vì — văn chương)", r"re:,\s*for (i|you|he|she|we|they|it|there|thou) (am|are|is|was|were|have|had|know|knew|will|shall|can|could|would|do|did|art|hast|love|loved|'m|'re|'s|see|saw|must|may|might|never)\b"),
        ("and", ", and $PRON&%nsubj"),
        ("nor", "nor"),
        ("but", "but&%cc $PRON&%nsubj"),
        ("or / or else", ["or&%cc $PRON&%nsubj", "or else"]),
        ("yet (nhưng mà)", r"re:,\s*(and )?yet (i|you|he|she|we|they|it|there|the|still)\b"),
        ("so (vì vậy)", "so&%cc|advmod $PRON&%nsubj $AUX|VERB"),
    ]),
    ("Liên từ phụ thuộc chỉ thời gian", [
        ("when", "when&%advmod|mark $PRON|DET|PROPN"),
        ("while", "while&%mark $PRON|DET"),
        ("before / after + mệnh đề", "~(before|after)&%mark $PRON|DET"),
        ("until / till", "~(until|till|'til|til)&%mark $PRON|DET"),
        ("since (từ khi)", "since&%mark $PRON|DET|PROPN #VBD|AUX|VERB"),
        ("as soon as / once / whenever / every time", ["as soon as", "once&%mark|advmod $PRON", "whenever $PRON", "every time $PRON"]),
    ]),
    ("Liên từ phụ thuộc chỉ nguyên nhân, lí do", [
        ("because / 'cause", ["because&%mark $PRON|DET|PROPN", "~('cause|cause|cuz|coz)&%mark $PRON"]),
        ("since / as (vì)", "~(since|as)&%mark $PRON&%nsubj ?$AUX ?$ADV $VERB|AUX&!#VBG"),
        ("now that", "now that"),
    ]),
    ("Liên từ phụ thuộc chỉ điều kiện", [
        ("if", "if&%mark $PRON|DET|PROPN"),
        ("unless", "unless"),
        ("as long as / provided (that) / in case", ["as long as", "provided|providing that?", "in case"]),
        ("even if", "even if"),
    ]),
    ("Liên từ phụ thuộc chỉ sự tương phản", [
        ("although / though / even though", ["although", "even though", "though&%mark $PRON|DET"]),
        ("while / whereas (trong khi)", ["whereas", "tg:MĐ trạng ngữ với while"]),
    ]),
    ("Liên từ phụ thuộc chỉ mục đích", [
        ("so that / in order that", ["so that $PRON", "in order that"]),
        ("so + S + can/could (để mà)", "so $PRON&%nsubj can|could|will|would|ca|may"),
    ]),
    ("Liên từ tương quan", [
        ("both … and", "both $NOUN|PRON|ADJ|VERB|DET ?$NOUN and"),
        ("either … or", r"re:\beither\b.{1,40}?\bor\b"),
        ("neither … nor", r"re:\bneither\b.{1,40}?\bnor\b"),
        ("not only … but (also)", r"re:\bnot only\b.{1,50}?\bbut\b"),
        ("whether … or (not)", r"re:\bwhether\b.{1,40}?\bor\b"),
        ("not … but … (không phải … mà là)", r"re:\bnot (a|the|my|your) \w+,? but (a|the|my|your)\b"),
    ]),
    ("Trạng từ liên kết", [
        ("however / therefore / otherwise / anyway / besides…", ["tg:Trạng từ liên kết", "~(otherwise|anyway|anyhow|besides|meanwhile|nevertheless|therefore|however)&$ADV&%advmod ,"]),
    ]),
]

# ============================================================== 13. MẠO TỪ
CHAPTERS["art"] = [
    ("Mạo từ xác định: the", [
        ("Vật duy nhất (the sun, the moon, the world…)", "the sun|moon|world|sky|sea|earth|universe|ocean|stars|horizon|wind|rain"),
        ("Danh từ được xác định bởi cụm/mệnh đề theo sau (the one that I love)", "the one|girl|boy|man|woman|way|day|night|place|thing|time|love|reason that|who|which|i|you&%nsubj|dobj|nsubjpass"),
        ("Địa danh, sông, biển, núi, nước số nhiều (the Mississippi, the USA…)", r"re:\bthe (united states|usa|uk|mississippi|nile|thames|rhine|danube|atlantic|pacific|alps|rockies|bahamas|philippines|netherlands|amazon|sahara|eiffel tower|golden gate|rio grande|ohio|hudson|bayou|delta|seven seas|red sea|dead sea|caribbean|mediterranean)\b"),
        ("Tập thể, nhóm (the police, the government, the people)", "the police|government|army|people|crowd|church|navy|media|public|preacher|band|devil|lord"),
        ("the + so sánh nhất / số thứ tự / only / same", "tg:the + so sánh nhất"),
        ("the + nhạc cụ (play the guitar)", "@play|strum|pick|beat the guitar|piano|drums|violin|bass|fiddle|banjo|harmonica|trumpet|saxophone|organ|tambourine|drum|horn|blues"),
        ("the + tính từ (the rich, the brave)", r"re:\bthe (rich|poor|young|old|brave|lonely|dead|living|wicked|weak|strong|free|blind|lost|broken|innocent|chosen|damned|restless|faithful|weary|hopeless|meek)\b(?= (and|are|will|who|were|have|shall|can|in|of)\b|[,.!?]*$)"),
    ]),
    ("Không dùng mạo từ", [
        ("Danh từ trừu tượng nói chung (Love is…, Life is…)", "<love|life|time|money|music|death|hope|freedom|faith|happiness|beauty|truth|nature|war|peace&%nsubj is|'s|was|ai|can|will|makes|takes|goes|never"),
        ("go to bed / school / church / work… (không the)", "@go|come|get|send|walk to bed|school|church|work|sleep|jail|prison|heaven|hell|town|college|war|sea"),
        ("at / in + home, school, church, night…", "at|in home|school|church|work|night|bed|heaven|hell|dawn|sea|war"),
        ("by + phương tiện (by car, by phone)", "tg:by + phương tiện"),
    ]),
    ("Mạo từ không xác định: a và an", [
        ("an + nguyên âm", "tg:an + nguyên âm"),
        ("an + h câm (an hour, an honest…)", "tg:an + h câm"),
        ("a + âm /j/, /w/ (a university, a one-…)", "tg:a + âm /j/ hoặc /w/"),
        ("a/an giới thiệu lần đầu (there's a…)", "there 's|is|was a|an ?$ADJ $NOUN"),
        ("a/an + thành viên của nhóm (she's a dreamer)", "$PRON&%nsubj 'm|am|'s|is|'re|are|was|were a|an ?$ADJ $NOUN&%attr"),
        ("a/an + nghề nghiệp / vai trò", "@be a|an ?$ADJ ~(doctor|teacher|soldier|singer|dancer|writer|lawyer|preacher|cowboy|sailor|pilot|nurse|poet|painter|farmer|driver|waitress|actor|actress|star|king|queen|fighter|lover|rider|believer|dreamer|stranger|liar|loser|winner|survivor|rebel|hero|saint|sinner|thief|fool|gambler|hustler|millionaire|prisoner|soldier)"),
        ("a/an = mỗi (once a week, 90 miles an hour)", r"re:\b(once|twice|\w+ times|\d+ (miles|dollars|times|bucks)|(one|two|three|four|five|ten|twenty|forty|fifty|sixty|seventy|eighty|ninety|a hundred|a thousand|a million) (miles|dollars|times|bucks|days|hours|nights)) (a|an|per) (day|week|night|hour|minute|year|month|second|lifetime)\b"),
        ("Cụm lượng từ với a (a lot of, a few, a little, a couple of)", ["a lot of", "a couple of|bit", "a few|little $NOUN"]),
        ("Cụm cố định (all of a sudden, once upon a time, in a while…)", r"re:\b(in a hurry|all of a sudden|as a matter of fact|once upon a time|(once )?in a while|a long time ago|for a while|in a minute|in a way|in a heartbeat|in a row|at a time|a little bit)\b"),
        ("such a / what a + N", ["such a|an $ADJ? $NOUN", "<what a|an ?$ADJ $NOUN"]),
    ]),
]

# ============================================================== 14. LƯỢNG TỪ
CHAPTERS["quant"] = [
    ("Vị trí của lượng từ", [
        ("Lượng từ + N", "many|few|several|much|some|any|all|most|no|enough&%det|amod $ADJ? $NOUN"),
        ("Lượng từ + of + the/my + N", "tg:%s of + the/tính từ sở hữu + N"),
        ("Lượng từ đứng một mình (làm đại từ)", "tg:%s dùng như đại từ"),
    ]),
    ("Lượng từ đi với danh từ đếm được", [
        ("many + N số nhiều", "many&%amod|det ?$ADJ #NNS"),
        ("how many / so many / too many", "how|so|too many"),
        ("a few + N (một vài — tích cực)", "a few ?$ADJ #NNS"),
        ("few + N (rất ít — tiêu cực)", r"re:(?<!a )(?<!quite a )\bfew (people|friends|words|things|times|days|years|men|ones|moments|minutes|hours|nights)\b"),
        ("several + N", "several ?$ADJ #NNS"),
        ("a number of / the number of", r"re:\b(a|the) number of\b"),
        ("a couple of / a handful of / dozens/hundreds/thousands of", r"re:\b(a couple of|a handful of|dozens of|hundreds of|thousands of|millions of|a million|a thousand) \w+"),
        ("each + N số ít", "each&%det $NOUN&#NN"),
        ("every + N số ít", "every&%det $NOUN&#NN"),
        ("each of + N số nhiều / đại từ", "each of"),
        ("various / numerous", "~(various|numerous|countless)&$ADJ $NOUN"),
    ]),
    ("Lượng từ đi với danh từ không đếm được", [
        ("much + N (câu phủ định / câu hỏi)", "much&%amod|det $NOUN&#NN"),
        ("how much / so much / too much", "how|so|too much"),
        ("a little + N (một ít — tích cực)", "a little $NOUN&#NN"),
        ("little + N (rất ít — tiêu cực)", r"re:(?<!a )\blittle (time|hope|love|faith|chance|money|sleep|room|choice|doubt|light)\b"),
        ("a great deal of / a good deal of", r"re:\ba (great|good) deal( of)?\b"),
        ("an amount of / a large amount of", r"re:\b(an|a (large|small|huge)) amount of\b"),
    ]),
    ("Lượng từ đi với cả danh từ đếm được và không đếm được", [
        ("some (câu khẳng định)", "some&%det ?$ADJ $NOUN"),
        ("some trong lời mời / đề nghị (want some…?)", r"re:\b(would you like|do you want|you want|you wanna|want|wanna|care for|how about|could i have|can i have|can i get|let's have|have) some \w+( \w+)?\?|\b(would you like|do you want|you wanna|how about|care for) some\b"),
        ("any (câu phủ định / câu hỏi)", ["n't|not|never ?$VERB any ?$ADJ $NOUN|PRON", "n't|not ?$VERB any more|longer"]),
        ("any = bất kỳ (câu khẳng định)", "any&%det $NOUN&#NN"),
        ("a lot of / lots of", ["a lot of", "lots of"]),
        ("plenty of", "plenty of"),
        ("no + N / none of", ["no&%det ?$ADJ $NOUN", "none of"]),
        ("all / most + N (nói chung)", "all|most&%det ?$ADJ #NNS|NN"),
        ("all of / most of / some of + đại từ / the + N", "all|most|some|many|none|both|half|any of the|my|your|us|them|you|these|those|it|this|our"),
        ("both / both of", ["both&%det|preconj $NOUN|PRON", "both of"]),
        ("either / neither (of)", "either|neither ?of $NOUN|PRON|DET"),
        ("half (of)", "half ?of ?a|an|the|my|your $NOUN"),
        ("enough + N / Adj + enough", ["enough&%amod|det $NOUN", "tg:adj/adv + enough"]),
        ("the whole / entire + N", "tg:the whole/entire"),
    ]),
]

# ============================================================== 15. THÌ
CHAPTERS["tense"] = [
    ("Thì hiện tại đơn", [
        ("Hiện tại đơn (nói chung)", "tg:Hiện tại đơn"),
        ("Ngôi thứ ba số ít + V-s/es", "he|she|it&%nsubj ?$ADV #VBZ&!~(is|has|does|'s)"),
        ("Thói quen (always/usually/every day + V)", "$PRON&%nsubj ~(always|usually|often|never|sometimes|rarely)&$ADV #VBZ|VBP&!~(is|are|am|'m|'re|'s)"),
        ("Cảm xúc / trạng thái (I love, I know, I need…)", "i|you|we|they love|know|need|want|believe|feel|remember|hate|understand|miss|wish|like&#VBP"),
        ("Sự thật hiển nhiên (the sun rises…)", r"re:\bthe (sun|moon|earth|world|river|wind|sea|tide|rain) (rises|sets|shines|turns|spins|flows|blows|comes|goes|falls|keeps)\b"),
        ("Lịch trình (the train leaves at…)", r"re:\b(train|bus|plane|flight|show|party|ship|game) (leaves|starts|departs|arrives|begins|opens|closes|comes)\b"),
        ("Phủ định don't/doesn't + V", "do|does n't $VERB&#VB"),
        ("Câu hỏi Do/Does + S + V?", "<do|does $PRON|DET|PROPN ?$NOUN ?$ADV $VERB&#VB"),
    ]),
    ("Thì hiện tại tiếp diễn", [
        ("Hiện tại tiếp diễn (nói chung)", "tg:Hiện tại tiếp diễn"),
        ("Đang xảy ra lúc nói (now, right now)", ("and", "tg:Hiện tại tiếp diễn", r"re:\b(right now|now|at the moment|this minute|as we speak)\b")),
        ("Kế hoạch tương lai gần (I'm leaving tonight/tomorrow)", ("and", "tg:Hiện tại tiếp diễn", r"re:\b(tonight|tomorrow|next (week|year|month|summer|time)|this weekend)\b")),
        ("always + V-ing (than phiền)", "@be ~(always|forever|constantly)&$ADV #VBG"),
    ]),
    ("Thì hiện tại hoàn thành", [
        ("Hiện tại hoàn thành (nói chung)", "tg:Hiện tại hoàn thành"),
        ("Kinh nghiệm (ever / never / before)", "have|has|'ve|'s ?n't ever|never #VBN"),
        ("just / already + V3", "have|has|'ve|'s just|already&$ADV #VBN"),
        ("yet (chưa / … chưa?)", r"re:\b(haven't|hasn't|have not|has not|have you|has he|has she) (\w+ )?\w+( \w+){0,3} yet\b"),
        ("for / since (kéo dài đến hiện tại)", ("and", "tg:Hiện tại hoàn thành", r"re:\b(since|for (so long|years|ages|a (long )?while|a long time|days|weeks|months|forever|all my life))\b")),
        ("This is the first time + HTHT", r"re:\b(the first time) (that )?(i|you|we|i've|you've|we've|i have|you have)( have|'ve)? (ever )?\w+"),
    ]),
    ("Thì hiện tại hoàn thành tiếp diễn", [
        ("have/has been + V-ing", "tg:Hiện tại hoàn thành tiếp diễn"),
        ("… + for / since / all day", ("and", "tg:Hiện tại hoàn thành tiếp diễn", r"re:\b(for|since|all (day|night|my life|this time|these years))\b")),
    ]),
    ("Thì quá khứ đơn", [
        ("Quá khứ đơn (nói chung)", "tg:Quá khứ đơn"),
        ("Động từ có quy tắc (V-ed)", "$PRON&%nsubj #VBD&~[a-z]+ed"),
        ("Động từ bất quy tắc (went, saw, knew…)", "$PRON&%nsubj #VBD&~(went|saw|knew|came|gave|took|made|said|told|felt|thought|found|left|got|fell|broke|ran|wrote|sang|drove|lost|met|held|kept|stood|spoke|began|became|forgot|threw|flew|drew|wore|chose|rose|hid|bit)"),
        ("Với ago / yesterday / last night", ("and", "tg:Quá khứ đơn", r"re:\b(ago|yesterday|last (night|year|week|summer|time|christmas|month|winter|spring|fall))\b")),
        ("did + not + V / Did + S + V?", ["did n't|not $VERB&#VB", "<did $PRON $VERB&#VB"]),
        ("Chuỗi hành động nối tiếp trong quá khứ", "#VBD&%ROOT ?$PRON|DET ?$NOUN ,? and|then ?$PRON #VBD&%conj"),
        ("was / were", "$PRON|NOUN&%nsubj was|were&%ROOT"),
    ]),
    ("Thì quá khứ tiếp diễn", [
        ("was/were + V-ing", "tg:Quá khứ tiếp diễn"),
        ("Đang làm thì việc khác xen vào (when / while)", ("and", "tg:Quá khứ tiếp diễn", r"re:\b(when|while|as)\b")),
        ("was/were going to (định làm)", "tg:Quá khứ tiếp diễn (was going to)"),
    ]),
    ("Thì quá khứ hoàn thành", [
        ("had + V3", "tg:Quá khứ hoàn thành"),
        ("Với before / after / by the time / when", ("and", "tg:Quá khứ hoàn thành", r"re:\b(before|after|by the time|when|until|already|never)\b")),
    ]),
    ("Thì quá khứ hoàn thành tiếp diễn", [
        ("had been + V-ing", "tg:Quá khứ hoàn thành tiếp diễn"),
    ]),
    ("Thì tương lai đơn", [
        ("will + V (nói chung)", "tg:Tương lai đơn"),
        ("Lời hứa / quyết định (I'll always…, I will…)", "i|we 'll|will ?always|never|forever|be $VERB|AUX"),
        ("won't + V", "wo n't $VERB"),
        ("Shall I / Shall we…?", "shall i|we"),
    ]),
    ("Thì tương lai gần (be going to)", [
        ("be going to + V", "tg:Tương lai gần (be going to)"),
        ("gonna (văn nói của going to)", r"re:\bgonna\b"),
    ]),
    ("Thì tương lai tiếp diễn", [
        ("will be + V-ing", "tg:Tương lai tiếp diễn"),
    ]),
    ("Thì tương lai hoàn thành", [
        ("will have + V3", "tg:Tương lai hoàn thành"),
    ]),
    ("Thì tương lai hoàn thành tiếp diễn", [
        ("will have been + V-ing", r"re:\b(will|'ll|won't) have been \w+ing\b"),
    ]),
    ("Quy tắc thêm -ed và -ing", [
        ("Gấp đôi phụ âm + -ed (stopped, planned…)", "#VBD|VBN&~[a-z]+(pped|tted|nned|gged|mmed|bbed|dded|rred)"),
        ("Phụ âm + y → -ied (cried, tried…)", "#VBD|VBN&~[a-z]+[^aeiou]ied"),
        ("Gấp đôi phụ âm + -ing (running, getting…)", "#VBG&~[a-z]+(pping|tting|nning|gging|mming|bbing|dding|rring)"),
        ("Bỏ -e + -ing (making, loving…)", "#VBG&~(making|loving|living|leaving|taking|coming|giving|having|dancing|driving|smiling|hoping|writing|moving|saving|breathing|chasing|closing|riding|shining|losing|using|hiding|fading|waking)"),
        ("-ie → -ying (dying, lying, tying)", "~(dying|lying|tying)&#VBG"),
    ]),
    ("Cách phát âm đuôi -ed", [
        ("/ɪd/ sau t, d (wanted, needed)", "#VBD|VBN&~[a-z]+(ted|ded)"),
        ("/t/ sau âm vô thanh p, k, s, ʃ, tʃ, f", "#VBD|VBN&~[a-z]+(ped|ked|ssed|shed|ched|fed|xed|ced)"),
        ("/d/ sau nguyên âm và phụ âm hữu thanh", "#VBD|VBN&~[a-z]+(ned|led|red|ved|wed|yed|ged|med|bed|zed|ied)"),
    ]),
    ("Cách phát âm đuôi -s/-es (động từ)", [
        ("/s/ (hopes, wants, likes…)", "#VBZ&~[a-z]+(ps|ts|ks|fs|ths|pes|kes)&!~.*(ates|ites|otes|utes)"),
        ("/ɪz/ (kisses, watches, changes…)", "#VBZ&~[a-z]+(ses|ches|shes|xes|zes|ges|ces)"),
        ("/z/ (loves, sees, runs…)", "#VBZ&~[a-z]+([aeiouy]s|ns|ms|ls|rs|gs|ds|bs|vs|ws)&!~(is|has|does|was|goes|.*ses|.*ces|.*ges|.*zes)"),
    ]),
]

# ============================================================== 16. MỆNH ĐỀ
CHAPTERS["clause"] = [
    ("Mệnh đề danh ngữ", [
        ("that + mệnh đề làm tân ngữ (I know that…)", "tg:Mệnh đề danh từ với that"),
        ("Lược that (I know you…)", "tg:Mệnh đề danh từ (lược that)"),
        ("Từ để hỏi + mệnh đề (I don't know why…)", "tg:Mệnh đề danh từ với từ để hỏi"),
        ("if / whether + mệnh đề (I wonder if…)", "@know|wonder|ask|see|tell|care|matter|doubt if|whether $PRON|DET"),
        ("Mệnh đề danh từ làm chủ ngữ (What you did was…)", "tg:Mệnh đề danh từ làm chủ ngữ"),
        ("Mệnh đề danh từ sau giới từ (about what…)", "tg:Mệnh đề danh từ sau giới từ"),
        ("It + be + Adj + that…", r"re:\bit('s| is| was) (so |too )?(true|clear|obvious|funny|strange|sad|crazy|good|plain|possible|impossible|likely|a shame|a pity) (that|how|what)\b"),
        ("Rút gọn MĐ danh ngữ (Wh- + to V)", "tg:Từ để hỏi + to V"),
    ]),
    ("Mệnh đề quan hệ", [
        ("who (người — chủ ngữ)", "$NOUN|PRON who&%nsubj $AUX|VERB"),
        ("whom (người — tân ngữ)", "$NOUN|PRON ?$ADP whom"),
        ("which (vật)", "$NOUN which&%nsubj|dobj|nsubjpass $AUX|VERB|PRON"),
        ("that (người / vật)", "$NOUN|PRON that&%nsubj|nsubjpass|dobj $AUX|VERB|PRON"),
        ("whose (sở hữu)", "$NOUN|PRON whose $ADJ? $NOUN"),
        ("where (nơi mà)", "~(place|town|city|land|world|room|house|home|street|road|bar|spot|corner|heaven|garden|island|country|river|bed) where $PRON|DET|PROPN"),
        ("when (khi mà — the day when)", "the|that ~(day|night|time|moment|year|summer|days|nights|morning|winter) when $PRON|DET"),
        ("why (the reason why)", "reason why|that"),
        ("Lược bỏ đại từ quan hệ tân ngữ (the one I love)", "tg:MĐQH lược bỏ đại từ quan hệ"),
        ("Giới từ + which / whom", ["tg:MĐQH giới từ + which", "$ADP whom"]),
        ("MĐQH không xác định (…, who/which …)", r"re:\b(?<!\bso)(?<!\boh)(?<!\band)(?<!\bbut)(?<!\byeah)[a-z]{3,},\s*(who|which|whose) (is|was|has|had|are|were|loves?|loved|knew|knows|never|always|could|would|will|can|said|says|made|makes|lives?|lived|came|comes|gave|seems|seemed)\b"),
        ("which thay cho cả mệnh đề (…, which means…)", r"re:,\s*which (is|means|was|made|makes|meant|leaves|brings) "),
        ("Đại từ quan hệ kép (whatever, whoever, wherever…)", "~(whatever|whoever|wherever|whenever|whichever)"),
    ]),
    ("Rút gọn mệnh đề quan hệ", [
        ("Rút gọn chủ động: N + V-ing", "tg:Rút gọn MĐQH chủ động"),
        ("Rút gọn bị động: N + V3", "tg:Rút gọn MĐQH bị động"),
        ("Rút gọn bằng to V (the first / last / only one to…)", "the first|last|only|next ?one|person|man|girl|thing|woman|boy to $VERB&#VB"),
    ]),
    ("Mệnh đề trạng ngữ chỉ thời gian", [
        ("when / while / before / after / until / as soon as…", "tg:MĐ trạng ngữ chỉ thời gian"),
        ("Rút gọn: liên từ + V-ing (after leaving, while waiting)", "tg:Rút gọn MĐ trạng ngữ (liên từ + V-ing)"),
    ]),
    ("Mệnh đề trạng ngữ chỉ nơi chốn", [
        ("where / wherever / everywhere + S + V", ["wherever $PRON|DET", "everywhere|anywhere $PRON&%nsubj $VERB|AUX"]),
    ]),
    ("Mệnh đề trạng ngữ chỉ nguyên nhân / lí do", [
        ("because / since / as + mệnh đề", "tg:MĐ trạng ngữ chỉ nguyên nhân"),
        ("Rút gọn bằng V-ing / Having V3 / Being…", ["tg:Rút gọn MĐ trạng ngữ bằng V-ing", r"re:^(being|having) \w+"]),
    ]),
    ("Mệnh đề trạng ngữ chỉ sự nhượng bộ", [
        ("although / though / even though", "tg:MĐ trạng ngữ chỉ nhượng bộ"),
        ("no matter what/how/where… / however + Adj", ["no matter what|how|where|who|when|if", "however $ADJ|ADV $PRON|DET"]),
    ]),
    ("Mệnh đề trạng ngữ chỉ mục đích", [
        ("so that / in order that / so + S + can", "tg:MĐ trạng ngữ chỉ mục đích"),
    ]),
    ("Mệnh đề trạng ngữ chỉ kết quả", [
        ("so + Adj/Adv + that", "so $ADJ|ADV ?, that $PRON|DET"),
        ("such (a/an) + Adj + N + that", "such ?a|an ?$ADJ $NOUN that $PRON|DET"),
        ("so/such … that (tổng hợp)", "tg:MĐ trạng ngữ chỉ kết quả"),
    ]),
    ("Mệnh đề trạng ngữ chỉ điều kiện", [
        ("in case / as long as / suppose", ["tg:MĐ trạng ngữ chỉ điều kiện", "as long as", "~(suppose|supposing) $PRON"]),
    ]),
    ("Mệnh đề trạng ngữ chỉ thể cách", [
        ("as if / as though", "as if|though $PRON|DET"),
        ("like + mệnh đề (like I do) / the way + mệnh đề", ["like&%mark $PRON&%nsubj $VERB|AUX", "the way $PRON&%nsubj $VERB|AUX"]),
        ("as (như là)", "tg:MĐ trạng ngữ chỉ thể cách"),
    ]),
    ("Mệnh đề sau Wish và If only", [
        ("wish + QKĐ / were (ước hiện tại)", "@wish ?that $PRON|DET|PROPN ?$NOUN were|was|knew|had|did|could|felt|loved|wanted|understood|lived&!%aux"),
        ("wish + had V3 (ước quá khứ)", "@wish ?that $PRON|DET had|'d ?n't|never ?$ADV #VBN"),
        ("wish + would / could (ước tương lai / phàn nàn)", "@wish ?that $PRON|DET would|could|'d ?$ADV $VERB"),
        ("If only…", "if only"),
    ]),
    ("Mệnh đề sau It's time và Would rather", [
        ("It's (high/about) time + S + V2 / to V", r"re:\b(it's|it is) (high |about )?time (to|we|you|i|for|that)\b"),
        ("would rather + S + V2", "would|'d rather $PRON&%nsubj #VBD|MD|VBN"),
        ("would rather + V (thích … hơn)", "would|'d rather $VERB&#VB|ADV"),
    ]),
]

# ============================================================== 17. CÂU
CHAPTERS["sent"] = [
    ("Các thành phần trong câu", [
        ("Chủ ngữ + Động từ (S + V)", "fn:intransitive"),
        ("S + V + O", "$PRON|NOUN&%nsubj $VERB&%ROOT ?$DET|PRON ?$ADJ $NOUN|PRON&%dobj >"),
        ("S + V + C (bổ ngữ là tính từ)", "$PRON|NOUN&%nsubj ?$AUX @be|become|seem|feel|look|get|stay&%ROOT ?$ADV $ADJ&%acomp >"),
        ("S + be + bổ ngữ là danh từ (You are my sunshine)", "$PRON&%nsubj @be&%ROOT my|your|the|a|an|our ?$ADJ $NOUN&%attr"),
        ("S + V + IO + DO", "tg:Động từ + 2 tân ngữ"),
        ("S + V + O + to/for + O (give it to me)", "@give|send|show|tell|bring|buy|write|sing|sell|leave|throw|pass $NOUN|PRON&%dobj to|for me|you|him|her|us|them"),
        ("S + V + O + C (call me…, make you happy)", ["tg:Tính từ sau tân ngữ", r"re:\b(call|calls|called|calling|name|named) (me|you|him|her|it|us|them) (a|an|the|my|your|his|her|mister|miss|baby|crazy|insane|names|honey|sweetheart|darling|daddy|mama)\b"]),
        ("Trạng ngữ đầu câu (In the morning, …)", r"re:^(in|at|on|under|after|before|during|for|from|by|with) (the |my |your |a |this |that |our )?\w+( \w+)?, (i|you|he|she|we|they|it|the)\b"),
    ]),
    ("Trật tự từ trong câu", [
        ("Câu hỏi gián tiếp giữ trật tự S + V (tell me where you are)", r"re:\b(tell me|do you know|i wonder|i don't know|can you tell me|i know|ask me|i don't care|show me) (what|where|why|how|who|when|if|whether) (you|i|he|she|we|they|it|this|love) (are|is|am|were|was|want|need|feel|do|did|go|went|have|'re|can|will|should|could|would|mean|think|see|know)\b"),
        ("enough đứng sau Adj/Adv, trước N", "tg:adj/adv + enough"),
    ]),
    ("Phân loại câu theo cấu trúc", [
        ("Câu đơn (1 mệnh đề)", "<$PRON&%nsubj ?$AUX ?$ADV $VERB&%ROOT ?$DET|PRON ?$ADJ $NOUN|PRON&%dobj|attr ?$ADV >"),
        ("Câu ghép (2 mệnh đề độc lập)", "$PRON&%nsubj $AUX|VERB *. ?, and|but|so|or|yet&%cc $PRON&%nsubj $AUX|VERB"),
        ("Câu phức (mệnh đề chính + mệnh đề phụ)", "$PRON&%nsubj $AUX|VERB *. because|when|if|although|though|while|since|until|before|after|unless&%mark|advmod $PRON&%nsubj $AUX|VERB"),
        ("Câu phức hợp (ghép + phức)", "tg:Câu phức hợp"),
    ]),
    ("Câu trần thuật và câu hỏi", [
        ("Câu khẳng định / phủ định", ["$PRON&%nsubj ca|do|does|did|wo|is|are|am|was|were|have|has|'m|'re n't|not $VERB|ADJ"]),
        ("Câu hỏi Yes/No (trợ động từ + S + V?)", "<do|does|did|are|is|am|was|were|can|could|will|would|have|has|should|shall $PRON&%nsubj"),
        ("Câu hỏi Wh-", "<what|where|why|how|who|when|which $AUX|VERB|PRON|ADJ|ADV"),
        ("Câu hỏi đuôi (…, isn't it? / don't you?)", r"re:,\s*(is|are|was|were|do|does|did|have|has|had|will|would|can|could|should|ai)(n't| not)? (i|you|he|she|it|we|they|there)[?!. ]*$|,\s*(isn't|aren't|wasn't|weren't|don't|doesn't|didn't|won't|can't|haven't|hasn't|wouldn't|couldn't|shouldn't|ain't) (i|you|he|she|it|we|they|there)[?!. ]*$"),
        ("Câu hỏi trần thuật (You're leaving?)", r"re:^(?!.*\b(why|what|how|where|who|when|do|does|did|can|will|would|could|should|is|are|am|was|were)\b.*\?)(so )?(you|you're|you've|she's|he's|it's|we're|they're|you'll|you really) [^?]{3,}\?$"),
        ("Câu hỏi hồi đáp (Oh, did you? / Is it?)", r"re:^(oh,? |really,? |well,? )?(do|did|does|are|is|was|were|have|has|can|will|would) (you|i|he|she|it|we|they)\?$"),
        ("Câu hỏi tu từ (Who cares? / Who knows?)", r"re:\b(who cares|who knows|what's the point|what's the use|what else is new|who am i to|how could i (forget|know)|what do you expect)\b"),
    ]),
    ("Câu mệnh lệnh", [
        ("Mệnh lệnh khẳng định (Take my hand)", "<$VERB&#VB&%ROOT&!~(be|do|have|will|let|please|love|baby|oh|can|could|would|need|want|say|tell|see|look)|be|love $PRON|DET"),
        ("Mệnh lệnh phủ định (Don't…, Never…)", ["<do n't $VERB&#VB", "<never $VERB&#VB&%ROOT"]),
        ("Let's + V", "<let 's $VERB"),
        ("please + V", "please $VERB&#VB"),
    ]),
    ("Câu cảm thán", [
        ("What (a/an) + Adj + N!", "<what a|an ?$ADJ $NOUN"),
        ("How + Adj/Adv + S + V!", "<how $ADJ|ADV $PRON|DET&%nsubj ?$NOUN $AUX|VERB"),
        ("so + Adj / such (a) + Adj + N", ["such a|an ?$ADJ $NOUN", "$PRON&%nsubj @be so $ADJ"]),
    ]),
    ("Hình thức nhấn mạnh", [
        ("do/does/did nhấn mạnh động từ", "$PRON&%nsubj do|does|did&%aux ?$ADV $VERB&#VB"),
        ("Nhấn mạnh tính từ (so/really/very + Adj, the very + N)", ["the very $ADJ|NOUN", "so|really|very so|really|very $ADJ"]),
        ("Câu chẻ It is/was … that/who", ["tg:Câu chẻ", r"re:\bit('s| is| was) (only |always |just )?(you|me|him|her|us|them|love|this|that) (who|that)\b"]),
        ("Câu chẻ Wh- (What I want is… / All I need is…)", r"re:^(what|all) (i|you|we|they|she|he) (really |ever )?(\w+ ){0,2}(is|was|'s)\b"),
        ("Đại từ phản thân nhấn mạnh (I myself)", "i|you|he|she|we|they myself|yourself|himself|herself|ourselves|themselves"),
    ]),
    ("Câu điều kiện", [
        ("Loại 0 (sự thật: If + HTĐ, HTĐ)", "fn:cond0"),
        ("Loại 1 (If + HTĐ, will/can + V)", "fn:cond1"),
        ("Loại 1 — mệnh lệnh ở mệnh đề chính", "fn:cond1imp"),
        ("Loại 2 (If + QKĐ/were, would + V)", "fn:cond2"),
        ("If I were you", r"re:\bif i (were|was) you\b"),
        ("If … were to + V", "if $PRON were|was to $VERB"),
        ("Loại 3 (If + had V3, would have V3)", "fn:cond3"),
        ("Hỗn hợp (If + had V3, would + V)", "fn:condmix"),
        ("unless = if … not", "unless"),
        ("What if…?", "<what if"),
        ("If it weren't for / But for / If not for", r"re:\b(if it (weren't|wasn't|hadn't been) for|if not for|if it wasn't for|but for (you|your|the grace|him|her|love))\b"),
        ("Đảo ngữ điều kiện (Should/Were/Had + S…)", ["tg:Đảo ngữ câu điều kiện", r"re:^(had|were) (i|you|he|she|we|they) (known|been|seen|to|only|stayed|gone|listened|told|tried)\b"]),
        ("Câu điều kiện (tổng hợp)", "tg:Câu điều kiện"),
    ]),
    ("Câu tường thuật", [
        ("Câu trần thuật: said / told + (that) + S + V lùi thì", r"re:\b(said|told (me|you|him|her|us|them)) (that )?(i|you|he|she|we|they|it|there) (was|were|would|could|had|did|didn't|wasn't|weren't|loved|knew|wanted|needed|'d)\b"),
        ("say vs. tell (tell + O)", r"re:\b(you|she|he|they|i) (said|told me|told you|told him|told her|told us) (that|you|i|she|he|we|it)\b"),
        ("Không lùi thì (sự thật / vẫn đúng)", r"re:\b(said|told me|told you|knew|know|says|swore) (that )?(the (world|earth|sun)|love|god|life|you|i|he|she|it|we|they) (is|are|am|'s|'re|will|'ll|can|loves?|knows?|wants?|needs?)\b"),
        ("Câu hỏi Yes/No: asked / wondered + if / whether", "@ask|wonder ?$PRON if|whether $PRON|DET"),
        ("Câu hỏi Wh-: asked + wh- + S + V", "@ask ?$PRON what|where|why|how|who|when $PRON|DET&%nsubj $AUX|VERB"),
        ("Mệnh lệnh: told / asked + O + (not) to V", r"re:\b(told|asked|begged|warned|ordered|advised|urged|reminded|tell|ask|beg) (me|you|him|her|us|them) (not )?to \w+"),
        ("Thay đổi trạng từ thời gian (that night, the next day, then)", ("and", r"re:\b(said|told|asked|says)\b", r"re:\b(the next day|the day before|that night|the night before|that day|the following (day|night|morning)|the day after|the week before)\b")),
        ("Động từ tường thuật + to V (promised / swore / refused to)", "@promise|swear|agree|refuse|offer|threaten|vow|pretend|claim to $VERB"),
        ("Động từ tường thuật + V-ing (admit / deny / suggest)", "@admit|deny|suggest|recommend|regret ?$ADV #VBG"),
        ("Động từ tường thuật + giới từ + V-ing (apologize for, blame for)", "@apologize|apologise|blame|accuse|thank|insist|forgive|congratulate|warn ?$PRON for|of|on|against #VBG"),
        ("Động từ + that + giả định (demand / suggest that…)", r"re:\b(suggest|suggested|suggests|insist|insisted|demand|demanded|recommend|recommended|require|required|request|requested|important|essential|vital|necessary|propose|proposed) that (he|she|you|we|they|i|it|everyone|nobody|the \w+) (be|go|stay|come|have|leave|take|do|give|keep|not|get|make|say|wait|sing|pray|love)\b"),
        ("Tường thuật câu cảm thán (exclaimed, cried out…)", r"re:\b(exclaimed|cried out|shouted|screamed|yelled|whispered|sighed)\b"),
        ("Tường thuật Yes / No (said yes / said no)", r"re:\b(said|says|say|saying|told \w+) (yes|no)\b"),
        ("Lùi thì sau động từ tường thuật ở quá khứ", "tg:Lùi thì sau động từ tường thuật"),
    ]),
]

# ============================================================== 18. PHỐI HỢP THÌ
CHAPTERS["seq"] = [
    ("Mệnh đề chính và mệnh đề phụ", [
        ("MĐ chính quá khứ → MĐ phụ quá khứ (I knew you were…)", "knew|thought|said|felt|believed|guessed|told|hoped|wished|wondered|swore|promised ?$PRON ?that $PRON&%nsubj #VBD|MD&!~(can|will|'ll|shall|may|must)"),
        ("MĐ chính hiện tại → MĐ phụ mọi thì", "i|you|we know|think|believe|guess|hope|swear|bet ?that $PRON&%nsubj will|'ll|#VBD|#VBZ|was|were"),
        ("Lùi thì sau động từ tường thuật ở quá khứ", "tg:Lùi thì sau động từ tường thuật"),
        ("Không lùi thì (sự việc vẫn đúng)", r"re:\b(said|told me|told you|knew|know|says|swore) (that )?(the (world|earth|sun)|love|god|life|you|i|he|she|it|we|they) (is|are|am|'s|'re|will|'ll|can|loves?|knows?|wants?|needs?)\b"),
    ]),
    ("Các quy tắc phối hợp thì quan trọng", [
        ("MĐ thời gian dùng hiện tại thay cho tương lai (when you come, I'll…)", "tg:MĐ thời gian dùng hiện tại thay cho tương lai"),
        ("Quá khứ hoàn thành (trước) + quá khứ đơn (sau)", "tg:Quá khứ hoàn thành (xảy ra trước)"),
        ("after + had V3, … QKĐ", "after $PRON had|'d #VBN"),
        ("since + QKĐ, HTHT (ever since you left…)", ("and", "since $PRON|DET #VBD", r"re:\b(have|has|'ve|haven't|hasn't|been)\b")),
        ("as if / as though + quá khứ (giả định)", "as if|though $PRON&%nsubj were|was|had|knew|did|could|would|#VBD"),
    ]),
    ("Câu ước (Wish & If only)", [
        ("wish + QKĐ (ước hiện tại)", "@wish ?that $PRON|DET were|was|knew|had|did|could|felt|loved|understood|lived"),
        ("wish + had V3 (ước quá khứ)", "@wish ?that $PRON had|'d ?n't|never #VBN"),
        ("wish + would (ước tương lai)", "@wish ?that $PRON would|'d ?$ADV $VERB"),
        ("If only + quá khứ", "if only $PRON|DET ?$NOUN were|was|had|could|knew|would|did|#VBD"),
    ]),
]

# ============================================================== 19. ĐẢO NGỮ
CHAPTERS["inv"] = [
    ("Đảo ngữ trong câu hỏi", [
        ("Trợ động từ + S + V…?", "<are|is|do|does|did|can|could|will|would|have|has|should|was|were $PRON&%nsubj ?$ADV $VERB|ADJ|DET|NOUN|PRON"),
        ("Wh- + trợ động từ + S…?", "<what|where|why|how|who|when do|does|did|are|is|can|will|would|have|should $PRON&%nsubj"),
    ]),
    ("Đảo ngữ với trạng từ / cụm phủ định đầu câu", [
        ("Never / Rarely / Seldom + trợ động từ + S", r"re:^(never|rarely|seldom|nowhere)( (before|again|in (my|your) life|once))?,? (have|has|had|did|do|does|will|would|could|can|was|were|is|am|shall) (i|you|he|she|we|they|it|there)\b"),
        ("Hardly / Scarcely / No sooner … when / than", r"re:\b(hardly|scarcely|barely) (had|did|have) (i|you|he|she|we|they)\b|\bno sooner (had|did|have|than)\b"),
        ("Not until / Not once / Not a word…", r"re:^not (once|until|a (single )?(day|word|night|minute|soul|thing|moment|chance)|one (day|night|time)|even once) (did|do|does|have|has|had|will|would|could|can|was|is)\b|^not (once|until)\b"),
        ("Little + did + S", r"re:\blittle (did|do|does) (i|you|he|she|we|they)\b"),
        ("Nor + trợ động từ + S", "nor $AUX $PRON&%nsubj"),
        ("Đảo ngữ phủ định (tổng hợp)", "tg:Đảo ngữ với trạng từ phủ định"),
    ]),
    ("Đảo ngữ trong câu điều kiện", [
        ("Had / Were / Should + S … (bỏ if)", ["tg:Đảo ngữ câu điều kiện", r"re:^(had|were) (i|you|he|she|we|they) (known|been|seen|to|only|stayed|gone|listened|told|tried)\b"]),
    ]),
    ("Đảo ngữ với Only + trạng ngữ", [
        ("Only then / Only when / Only if + trợ động từ + S", r"re:\bonly (then|now|when|after|by|in|once|if|through|with|at|love)\b[^.]{0,40}? (do|did|can|could|will|would|have|has|had|is|was|does|am|shall) (i|you|he|she|we|they|it)\b"),
        ("Only (chưa đảo — để so sánh)", "<only $ADV|SCONJ|ADP"),
    ]),
    ("Đảo ngữ với So và Such … that", [
        ("So + Adj + be + S + that…", r"re:^so (?!what|why|how|where|who|when|now|then|if|i\b|you\b|we\b|they\b|he\b|she\b|it\b|there\b|this\b|that\b)\w+( \w+)? (is|was|are|were|did|do|does|had|have|am) (i|you|he|she|it|we|they|the|my|your|his|her)\b.*\bthat\b"),
        ("Such + be + S + that…", r"re:^such (is|was|are|were) \w+"),
        ("so … that (dạng chưa đảo)", "so $ADJ|ADV ?, that $PRON|DET"),
    ]),
    ("Đảo ngữ với So / Neither / Nor (đồng tình)", [
        ("So + trợ động từ + S (So do I)", "so @do|be|have|can|will|would&$AUX|VERB i|you|he|she|we|they >"),
        ("Neither / Nor + trợ động từ + S (Neither do I)", "neither|nor @do|be|have|can|will|would|could|shall&$AUX i|you|he|she|we|they >"),
    ]),
    ("Đảo ngữ với trạng ngữ chỉ nơi chốn (đảo ngữ toàn phần)", [
        ("Here / There + V + S", r"re:\b(here (comes|come|goes|go|stands|lies|is|was|went|came)|there (comes|come|goes|go|stands|lies|went|came)) (the|my|your|a|another|that|our|his|her|this)\b"),
        ("Cụm giới từ / trạng từ đầu câu + V + S", [r"re:^(in|on|at|under|beside|behind|from|across|along|around|over|through|into|down|up|out) (the|a|my|this|that|her|his|your) \w+( \w+)? (stood|stands|lay|lies|sat|sits|came|comes|lived|lives|rose|rises|grew|grows|walked|ran|hung|hangs|shone|shines) (a|an|the|my|your|his|her|our|two|three)\b"]),
        ("Here is / Here are + N", "tg:Đảo ngữ Here is/are"),
    ]),
    ("Đảo ngữ sau as / than trong so sánh", [
        ("as / than + trợ động từ + S", r"re:\b(as|than) (do|does|did|is|was|are|were|would|could) (i|you|he|she|we|they|most|many|my|your|others|everyone|anyone)\b(?![ ]+\w+ing)"),
        ("Not only + trợ động từ + S", r"re:^not only (do|does|did|is|was|are|were|have|has|had|can|could|will|would) (i|you|he|she|we|they|it|this)\b"),
    ]),
]

ORDER = ["noun", "pron", "sva", "adj", "adv", "comp", "verb", "phr", "pass", "inf",
         "prep", "conj", "art", "quant", "tense", "clause", "sent", "seq", "inv"]


# ============================================================== hàm dò đặc biệt
INTRANS = set("cry die fall sleep arrive rise smile laugh happen exist shine disappear wait dance breathe "
              "shiver tremble bleed burn fade fly glow grow hide kneel lie live pray rain run shake sing "
              "sit stand stay swim walk weep wonder work talk come go".split())


def _span(doc, toks):
    lo = min(t.i for t in toks)
    hi = max(t.i for t in toks)
    return doc[lo].idx, doc[hi].idx + len(doc[hi].text)


def intransitive(doc):
    for t in doc:
        if t.dep_ == "ROOT" and t.pos_ == "VERB" and t.lemma_ in INTRANS:
            if any(c.dep_ in ("dobj", "ccomp", "xcomp", "attr", "prt", "dative", "acomp", "oprd") for c in t.children):
                continue
            subj = [c for c in t.children if c.dep_ == "nsubj"]
            if subj and t.i - subj[0].i <= 3:
                aux = [c for c in t.children if c.dep_ in ("aux", "neg")]
                return _span(doc, subj + aux + [t])
    return None


def _verb_info(v):
    auxs = [c for c in v.children if c.dep_ in ("aux", "auxpass")]
    al = [a.lower_ for a in auxs]
    return auxs, al


def _if_parts(doc):
    for t in doc:
        if t.lower_ == "if" and t.dep_ == "mark":
            h = t.head
            if h.dep_ != "advcl" or h.head is h:
                continue
            m = h.head
            if m.pos_ not in ("VERB", "AUX"):
                continue
            yield t, h, m


def _clause_kind(v, cond_side):
    auxs, al = _verb_info(v)
    lem = [a.lemma_ for a in auxs]
    if cond_side:
        if ("had" in al or "'d" in al) and v.tag_ == "VBN":
            return "pp"
        if v.tag_ == "VBD" and not auxs:
            return "past"
        if v.lower_ in ("were",) or (v.tag_ == "VBD" and v.lemma_ == "be"):
            return "past"
        if any(a.tag_ == "VBD" and a.lemma_ in ("be", "do") for a in auxs):
            return "past"
        if any(x in ("could", "would", "might") for x in al):
            return "past"
        if not any(a.tag_ == "MD" for a in auxs) and (v.tag_ in ("VBZ", "VBP") or
                                                       any(a.tag_ in ("VBZ", "VBP") for a in auxs)):
            return "pres"
        return None
    md = [a for a in auxs if a.tag_ == "MD"]
    if md:
        m = md[0].lower_
        if m in ("would", "could", "might", "'d", "should"):
            if "have" in lem and v.tag_ == "VBN":
                return "wouldhave"
            return "would"
        if m in ("will", "'ll", "can", "ca", "may", "must", "shall", "wo"):
            return "will"
        return None
    if v.tag_ == "VB" and not auxs and not any(c.dep_ == "nsubj" for c in v.children):
        return "imp"
    if v.tag_ in ("VBZ", "VBP") or any(a.tag_ in ("VBZ", "VBP") for a in auxs):
        return "pres"
    return None


def _cond(doc, want_if, want_main):
    for t, h, m in _if_parts(doc):
        k1 = _clause_kind(h, True)
        k2 = _clause_kind(m, False)
        if k1 == want_if and k2 == want_main:
            toks = [t, h, m] + _verb_info(m)[0] + _verb_info(h)[0]
            return _span(doc, toks)
    return None


def cond0(doc): return _cond(doc, "pres", "pres")
def cond1(doc): return _cond(doc, "pres", "will")
def cond1imp(doc): return _cond(doc, "pres", "imp")
def cond2(doc): return _cond(doc, "past", "would")
def cond3(doc): return _cond(doc, "pp", "wouldhave")
def condmix(doc): return _cond(doc, "pp", "would")


FUNCS = {f.__name__: f for f in (intransitive, cond0, cond1, cond1imp, cond2, cond3, condmix)}
