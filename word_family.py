# -*- coding: utf-8 -*-
"""Đọc 5000 từ, tra ĐỒNG NGHĨA + WORD FAMILY (noun/verb/adj/adv) qua WordNet.

Cài 1 lần:  pip install nltk openpyxl
            python -c "import nltk; nltk.download('wordnet'); nltk.download('omw-1.4')"
Chạy     :  python word_family.py
"""
from nltk.corpus import wordnet as wn

POSMAP = {'n': 'noun', 'v': 'verb', 'a': 'adj', 's': 'adj', 'r': 'adv'}

def word_family(word):
    """Trả về dict: {word, pos, synonyms, noun, verb, adj, adv}."""
    w = word.lower().strip()
    synonyms = set()
    fam = {'noun': set(), 'verb': set(), 'adj': set(), 'adv': set()}
    pos_self = set()

    for syn in wn.synsets(w):
        pos_self.add(POSMAP.get(syn.pos(), syn.pos()))
        for lemma in syn.lemmas():
            name = lemma.name().replace('_', ' ')
            if name.lower() != w:
                synonyms.add(name)                       # đồng nghĩa
            for rel in lemma.derivationally_related_forms():   # word family
                p = POSMAP.get(rel.synset().pos())
                fam_word = rel.name().replace('_', ' ')
                if p and fam_word.lower() != w:
                    fam[p].add(fam_word)

    return {
        'word': w,
        'pos': sorted(pos_self),
        'synonyms': sorted(synonyms),
        'noun': sorted(fam['noun']),
        'verb': sorted(fam['verb']),
        'adj':  sorted(fam['adj']),
        'adv':  sorted(fam['adv']),
    }


def main():
    from openpyxl import Workbook
    # đọc & khử trùng, giữ thứ tự
    seen = set(); words = []
    for line in open("5000.txt", encoding="utf-8"):
        x = line.strip().lower()
        if x and x not in seen:
            seen.add(x); words.append(x)

    wb = Workbook(); ws = wb.active; ws.title = "word_families"
    ws.append(["Word", "POS", "Synonyms", "Noun forms", "Verb forms",
               "Adjective forms", "Adverb forms"])
    n_syn = n_fam = 0
    for w in words:
        r = word_family(w)
        has_fam = any(r[k] for k in ('noun', 'verb', 'adj', 'adv'))
        n_syn += bool(r['synonyms']); n_fam += has_fam
        ws.append([
            r['word'], ", ".join(r['pos']),
            ", ".join(r['synonyms'][:25]),
            ", ".join(r['noun']), ", ".join(r['verb']),
            ", ".join(r['adj']),  ", ".join(r['adv']),
        ])
    ws.freeze_panes = "A2"
    for c, wdt in zip("ABCDEFG", [16, 12, 50, 26, 22, 26, 22]):
        ws.column_dimensions[c].width = wdt
    wb.save("word_families_5000.xlsx")
    print(f"Đã xử lý {len(words)} từ → word_families_5000.xlsx")
    print(f"Có đồng nghĩa: {n_syn} | Có word family: {n_fam}")
    print("\n--- Ví dụ ---")
    for demo in ("beauty", "decide", "happy", "nation", "create"):
        r = word_family(demo)
        print(f"[{demo}] pos={r['pos']}")
        print("  syn :", ", ".join(r['synonyms'][:8]))
        print("  noun:", ", ".join(r['noun']), "| verb:", ", ".join(r['verb']),
              "| adj:", ", ".join(r['adj']), "| adv:", ", ".join(r['adv']))


if __name__ == "__main__":
    main()
