"""Destination C1 & C2 Grammar and Vocabulary (Macmillan): phrasal verbs, idioms, phrases/patterns/collocations
từ phần tra cứu cuối sách — tools/data/destination_c1c2.json (tools/destination_extract.py, OCR)."""
import json

SOURCE = {"code": "dest", "name": "Destination C1 & C2 Grammar and Vocabulary", "url": ""}
G = {"phrasal": "Phrasal verbs database", "idiom": "Idioms database", "collocation": "Phrases, patterns and collocations"}


def extract(root):
    out = []
    for r in json.loads((root / "tools/data/destination_c1c2.json").read_text(encoding="utf-8")):
        out.append({"t": r["t"], "p": r["p"], "m": "", "d": r.get("d", ""), "e": r.get("e", ""), "ev": "",
                    "g": "Destination C1&C2 — " + G[r["t"]], "x": "C1–C2", "ref": ""})
    return out
