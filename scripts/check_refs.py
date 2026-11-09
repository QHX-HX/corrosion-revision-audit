#!/usr/bin/env python
"""Reference-list integrity: numbering, dangling citations, uncited entries, duplicates.

Usage:
    python check_refs.py manuscript.docx [--letter response.docx]
"""
import re
import sys
from collections import Counter

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from docx import Document

ENTRY = re.compile(r"^\[(\d+)\]\s*(.*)$")
CITE = re.compile(r"\[(\d+(?:\s*[,\u2013\-]\s*\d+)*)\]")


def load(path):
    doc = Document(path)
    paras = [p.text.strip() for p in doc.paragraphs]
    refs, body = {}, []
    in_refs = False
    for t in paras:
        m = ENTRY.match(t)
        if m:
            in_refs = True
            refs[int(m.group(1))] = m.group(2).strip()
        elif in_refs and not t:
            continue
        elif in_refs and re.match(r"^[A-Z][a-z]+ \d{4}", t):
            continue
        else:
            if t:
                body.append(t)
    return refs, "\n".join(body)


def citations(body):
    cited = set()
    for m in CITE.finditer(body):
        for part in (x.strip() for x in m.group(1).split(",")):
            if re.fullmatch(r"\d+", part):
                cited.add(int(part))
            else:
                a, b = re.split(r"[\u2013\-]", part)
                cited.update(range(int(a), int(b) + 1))
    return cited


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    refs, body = load(argv[0])
    cited = citations(body)

    print(f"entries: {len(refs)}  (numbered {min(refs)}-{max(refs)})")
    missing_numbers = [n for n in range(1, max(refs) + 1) if n not in refs]
    if missing_numbers:
        print(f"!! gaps in numbering: {missing_numbers}")

    dangling = sorted(n for n in cited if n not in refs)
    if dangling:
        print(f"!! cited but not listed: {dangling}")

    uncited = sorted(n for n in refs if n not in cited)
    if uncited:
        print(f"!! listed but never cited: {uncited}")

    norm = {}
    for n, t in refs.items():
        key = re.sub(r"[^a-z0-9]", "", t.lower())[:120]
        norm.setdefault(key, []).append(n)
    dupes = {tuple(v) for v in norm.values() if len(v) > 1}
    if dupes:
        print(f"!! duplicate entries: {sorted(dupes)}")

    if not (dangling or uncited or dupes or missing_numbers):
        print("OK: all entries cited, all citations resolved, no duplicates")

    if "--letter" in argv:
        letter = argv[argv.index("--letter") + 1]
        doc = Document(letter)
        seen = Counter()
        for p in doc.paragraphs:
            if p.text.startswith("Response"):
                for n in CITE.findall(p.text):
                    for part in (x.strip() for x in n.split(",")):
                        if re.fullmatch(r"\d+", part):
                            seen[int(part)] += 1
        unknown = sorted(n for n in seen if n not in refs)
        print(f"letter cites {len(seen)} distinct refs; unknown: {unknown or 'none'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
