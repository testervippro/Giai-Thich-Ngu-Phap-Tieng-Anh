"""Conversational American English: docs/tools/cae-data.js (window.CAE = {cats,subs,reg,t})."""
import html
import json
import re
import subprocess

SOURCE = {"code": "cae", "name": "Conversational American English", "url": "conversational-american-english.html"}

_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")


def _c(s):
    if s is None:
        return ""
    return _WS.sub(" ", html.unescape(_TAG.sub("", str(s)))).strip()


_JS = ("const fs=require('fs'),vm=require('vm');const c={window:{}};"
       "vm.runInNewContext(fs.readFileSync(process.argv[1],'utf8'),c);"
       "process.stdout.write(JSON.stringify(c.window.CAE));")


def extract(root):
    path = root / "docs/tools/cae-data.js"
    D = json.loads(subprocess.run(["node", "-e", _JS, str(path)], capture_output=True,
                                  text=True, check=True).stdout)
    out, seen = [], set()
    for tp in D["t"]:
        n, en, vi, xs = tp[2], _c(tp[3]), _c(tp[4]), tp[5]
        g = en
        for x in xs:
            p = _c(x[0])
            if not p:
                continue
            key = (g, p)
            if key in seen:
                continue
            seen.add(key)
            tags = [D["reg"].get(t, t) for t in (x[1] if len(x) > 1 and x[1] else [])]
            notes = [_c(t) for t in (x[2] if len(x) > 2 and x[2] else [])]
            xn = " · ".join(tags + notes)[:120]
            out.append({"t": "situation", "p": p, "m": "", "e": "", "ev": "",
                        "g": g, "x": xn, "ref": "t%s" % n})
    return out
