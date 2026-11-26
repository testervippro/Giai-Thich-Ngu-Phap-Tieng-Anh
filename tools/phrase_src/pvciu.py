"""Phrasal verbs trong English Collocations in Use (Intermediate + Advanced): docs/tools/pv-ciu-data.js (window.PVCIU)."""
import json
import subprocess

SOURCE = {"code": "pvciu", "name": "Phrasal verbs — English Collocations in Use", "url": "phrasal-verbs-collocations-in-use.html"}

_JS = ("const fs=require('fs'),vm=require('vm');const c={window:{}};"
       "vm.runInNewContext(fs.readFileSync(process.argv[1],'utf8'),c);process.stdout.write(JSON.stringify(c.window.PVCIU));")


def extract(root):
    D = json.loads(subprocess.run(["node", "-e", _JS, str(root / "docs/tools/pv-ciu-data.js")],
                                  capture_output=True, text=True, check=True).stdout)
    out = []
    for x in D:
        cs = x.get("c") or []
        out.append({"t": "phrasal", "p": x["pv"], "m": x.get("vi", ""), "e": (x.get("ex") or [""])[0], "ev": "",
                    "g": cs[0][3] if cs and len(cs[0]) > 3 else "", "x": " · ".join(c[0] for c in cs[:3]), "ref": ""})
    return out
