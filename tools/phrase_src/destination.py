"""Destination C1 & C2 Grammar and Vocabulary (Macmillan): phrasal verbs, idioms, phrases/patterns/collocations
từ phần tra cứu cuối sách — tools/data/destination_c1c2.json (tools/destination_extract.py, OCR)."""
import json

SOURCE = {"code": "dest", "name": "Destination C1 & C2 Grammar and Vocabulary", "url": ""}
G = {"phrasal": "Phrasal verbs database", "idiom": "Idioms database", "collocation": "Phrases, patterns and collocations"}


def _vi(root):
    vi = {}
    for l in (root / "tools/data/destination_vi.tsv").read_text(encoding="utf-8").splitlines():
        if "\t" in l and not l.startswith("#"):
            a, b = l.split("\t")[:2]
            vi.setdefault(a.strip(), b.strip())
    return vi


def extract(root):
    vi = _vi(root)
    out = []
    for r in json.loads((root / "tools/data/destination_c1c2.json").read_text(encoding="utf-8")):
        out.append({"t": r["t"], "p": r["p"], "m": vi.get(r["p"], ""), "d": r.get("d", ""), "e": r.get("e", ""), "ev": "",
                    "g": "Destination C1&C2 — " + G[r["t"]], "x": "C1–C2", "ref": ""})
    return out
