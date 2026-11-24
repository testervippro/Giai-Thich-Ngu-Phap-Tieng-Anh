"""Idioms, Phrasal Verbs, Collocations, Fixed expressions, IT/QA expressions + 800 Phrasal Verb IELTS Fighter
(docs/tools/expressions-data.js, trang docs/tools/expressions-bank.html)."""
import json
import subprocess

SOURCE = {"code": "ex", "name": "Idioms, Phrasal Verbs & Natural Expressions", "url": "expressions-bank.html"}
SOURCE_PV = {"code": "pv800", "name": "800 Phrasal Verb — IELTS Fighter", "url": "expressions-bank.html"}
TYPE = {"IDIOM": "idiom", "PHR": "phrasal", "PRO-PHR": "phrasal", "COL": "collocation", "FIX": "fixed", "IT-EXP": "it"}
_JS = "const fs=require('fs'),vm=require('vm');const w={};vm.runInNewContext(fs.readFileSync(process.argv[1],'utf8'),{window:w});process.stdout.write(JSON.stringify(w.EXB))"


def _load(root):
    out = subprocess.run(["node", "-e", _JS, str(root / "docs/tools/expressions-data.js")], capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def extract(root):
    D = _load(root)
    res = []
    for e in D["entries"]:
        pre = e["id"].rsplit("-", 1)[0]
        ex = next((x for x in e.get("ex", []) if x and x != "-"), "")
        x = " · ".join(v for v in (e.get("cefr"), e.get("register"), {"P1": "ưu tiên cao", "P2": "hữu ích", "P3": "nâng cao"}.get(e.get("prio"))) if v)
        res.append({"t": TYPE.get(pre, "idiom"), "p": e["expr"], "m": e.get("vi", ""), "d": e.get("en", ""), "e": ex, "g": e.get("group", ""),
                    "x": x, "ref": "#" + e["id"], "s": "ex"})
    return res


def extract_pv(root):
    D = _load(root)
    res = []
    for b in D.get("book", []):
        res.append({"t": "phrasal", "p": b["pv"], "m": "", "d": b.get("def", ""), "e": b.get("ex", ""), "g": "800 Phrasal Verb",
                    "x": "tách được (*)" if b.get("sep") else "", "ref": ("#" + b["id"]) if b.get("id") else "", "s": "pv800"})
    return res
