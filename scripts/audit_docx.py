#!/usr/bin/env python
"""Structural audit of a .docx: counts, cross-references, fonts, leftovers.

Usage:
    python audit_docx.py file1.docx [file2.docx ...]
"""
import re
import sys
import zipfile
from collections import Counter
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from docx import Document
from docx.oxml.ns import qn

CJK = re.compile(r"[\u4e00-\u9fff]")


def doc_text(doc):
    parts = [p.text for p in doc.paragraphs]
    for t in doc.tables:
        for row in t.rows:
            for cell in row.cells:
                parts.append(cell.text)
    return "\n".join(parts)


def iter_runs(doc):
    for p in doc.paragraphs:
        for r in p.runs:
            yield r
    for t in doc.tables:
        for row in t.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    for r in p.runs:
                        yield r


def font_refs(path):
    z = zipfile.ZipFile(path)
    fonts = Counter()
    for name in ("word/document.xml", "word/styles.xml"):
        try:
            xml = z.read(name).decode("utf-8", "ignore")
        except KeyError:
            continue
        for f in re.findall(r'w:(?:ascii|hAnsi|cs|eastAsia)="([^"]+)"', xml):
            fonts[f] += 1
    return fonts


def body_text_nodes(path):
    """Text that a reader actually sees: <w:t> nodes only."""
    z = zipfile.ZipFile(path)
    xml = z.read("word/document.xml").decode("utf-8", "ignore")
    return "".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", xml))


def tables_cited(text):
    nums = set()
    for m in re.finditer(r"Tables?\s+(\d+)(?:\s*(?:and|,|\u2013|-)\s*(\d+))?", text):
        nums.add(int(m.group(1)))
        if m.group(2):
            nums.add(int(m.group(2)))
    return sorted(nums)


def audit(path):
    path = Path(path)
    print("=" * 78)
    print(f"{path.name}  ({path.stat().st_size / 1048576:.2f} MB)")
    doc = Document(str(path))
    text = doc_text(doc)

    n_par = sum(1 for p in doc.paragraphs if p.text.strip())
    print(f"  paragraphs: {n_par} | tables: {len(doc.tables)} | "
          f"inline images: {len(doc.inline_shapes)}")

    figs = sorted({int(x) for x in re.findall(r"Fig(?:s)?\.?\s*(\d+)", text)})
    print(f"  figures cited: {figs}")
    print(f"  tables cited:  {tables_cited(text)}")
    st = sorted({int(n) for m in re.finditer(
        r"Supplementary Tables?\s+(\d+(?:\s*(?:and|,)\s*\d+)*)", text)
        for n in re.findall(r"\d+", m.group(1))})
    sf = sorted({int(n) for m in re.finditer(
        r"Supplementary Figs?\.?\s*(\d+(?:\s*(?:and|,)\s*\d+)*)", text)
        for n in re.findall(r"\d+", m.group(1))})
    if st or sf:
        print(f"  supplementary: tables {st} figures {sf}")

    print(f"  fonts: {dict(font_refs(path))}")

    colours = Counter()
    for r in iter_runs(doc):
        if r.text.strip():
            c = r.font.color
            colours[str(c.rgb) if (c and c.rgb) else "inherit"] += 1
    print(f"  run colours: {dict(colours)}")

    body = body_text_nodes(path)
    cjk = len(CJK.findall(body))
    if cjk:
        print(f"  !! CJK characters in visible text: {cjk}")

    # run-level artefacts: a superscript 2+ lives in its own run, so a single run
    # containing "Fe2+" means the charge is plain text.
    plain_fe = sum(1 for r in iter_runs(doc) if "Fe2+" in r.text)
    plain_cm = sum(1 for r in iter_runs(doc) if re.search(r"cm2(?![0-9])", r.text))
    if plain_fe:
        print(f"  ~ Fe2+ as plain text (not superscript): {plain_fe}")
    if plain_cm:
        print(f"  ~ cm2 as plain text: {plain_cm}")

    for label, pattern in {
        "Table S": r"Table S\d",
        "double space": r"[^\s]  +[^\s]",
        "double period": r"\.\.",
        "duplicated word": r"\b(\w+) \1\b",
        "TODO/TBD": r"\bTODO\b|\bTBD\b|待补|待定",
    }.items():
        if label == "double space":
            # "R1-1  Title" uses two spaces as a deliberate separator; skip those lines
            hits = sum(len(re.findall(pattern, line)) for line in text.splitlines()
                       if not re.match(r"^R\d+[-\w]*\s\s", line))
        else:
            hits = len(re.findall(pattern, text))
        if hits:
            print(f"  ~ {label}: {hits}")


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    for f in argv:
        audit(f)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
