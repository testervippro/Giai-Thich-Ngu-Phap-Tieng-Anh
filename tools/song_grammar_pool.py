#!/usr/bin/env python3
"""Bước 1 của "Ngữ pháp trong lời bài hát": lấy mọi dòng lời tiếng Anh (bỏ trùng) trong
tools/data/lrclib_corpus.jsonl.gz (kho LRCLIB đã tải), cho spaCy phân tích rồi lưu ra
build/song_grammar/ (pool-NN.spacy + meta.jsonl) để tools/song_grammar.py dò mẫu ngữ pháp.

Chạy: ~/Ielts-Reading/.venv-nlp/bin/python tools/song_grammar_pool.py
"""
import gzip, json, os, re, sys
import spacy
from spacy.tokens import DocBin

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "tools/data/lrclib_corpus.jsonl.gz")
OUT = os.path.join(ROOT, "build/song_grammar")
STOP = set("the a an i you he she it we they me my your is are was were be been to of and in on for "
           "with that this what when not no do don't can will just all so but love".split())
CHUNK = 100_000


def lines():
    seen = set()
    for ln in gzip.open(SRC, "rt", encoding="utf-8"):
        d = json.loads(ln)
        for i, l in enumerate(d["l"].split("\n")):
            l = re.sub(r"\s+", " ", l.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')).strip()
            w = l.split()
            if not 4 <= len(w) <= 18 or not l.isascii():
                continue
            low = [re.sub(r"[^a-z']", "", x.lower()) for x in w]
            if sum(x in STOP for x in low) / len(w) < 0.25:
                continue
            k = re.sub(r"[^a-z ]", "", l.lower())
            if k in seen:
                continue
            seen.add(k)
            yield l, {"id": d["id"], "t": d["t"], "a": d["a"], "n": i}


def main():
    os.makedirs(OUT, exist_ok=True)
    nlp = spacy.load("en_core_web_sm", disable=["ner"])
    items = list(lines())
    print(len(items), "dòng", flush=True)
    with open(os.path.join(OUT, "meta.jsonl"), "w") as f:
        for _, m in items:
            f.write(json.dumps(m, ensure_ascii=False) + "\n")
    for c in range(0, len(items), CHUNK):
        p = os.path.join(OUT, "pool-%02d.spacy" % (c // CHUNK))
        if os.path.exists(p):
            continue
        db = DocBin(store_user_data=False)
        texts = [t for t, _ in items[c:c + CHUNK]]
        for doc in nlp.pipe(texts, batch_size=1000, n_process=int(sys.argv[1]) if len(sys.argv) > 1 else 6):
            db.add(doc)
        db.to_disk(p)
        print("xong", p, flush=True)


if __name__ == "__main__":
    main()
