"""Ngân hàng 2.055 mẫu câu IELTS 9.0 (docs/tools/pattern-bank-data.js, trang docs/tools/pattern-bank.html)."""
import json
import subprocess

SOURCE = {"code": "pb", "name": "Ngân hàng 2.055 mẫu câu IELTS 9.0", "url": "pattern-bank.html"}
_JS = "const fs=require('fs'),vm=require('vm');const w={};vm.runInNewContext(fs.readFileSync(process.argv[1],'utf8'),{window:w});process.stdout.write(JSON.stringify(w.PB))"


def extract(root):
    out = subprocess.run(["node", "-e", _JS, str(root / "docs/tools/pattern-bank-data.js")], capture_output=True, text=True, check=True).stdout
    D = json.loads(out)
    cat = {c["id"]: c for c in D["cats"]}
    res = []
    for r in D["rows"]:
        c = cat.get(r["c"], {})
        g = (c.get("block", "") + " · " + c.get("vi", "")).strip(" ·")
        res.append({"t": "pattern", "p": r["p"], "m": r.get("vi", ""), "e": r.get("ex", ""), "g": g,
                    "x": ("nghe thấy trong phim " + str(r["n"]) + " lần") if r.get("n") else "", "ref": "", "s": "pb"})
    return res
