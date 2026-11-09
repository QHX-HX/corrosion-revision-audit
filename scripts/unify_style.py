#!/usr/bin/env python
"""Unify fonts, colours, dashes and spelling across .docx files.

Usage:
    python unify_style.py file.docx [...] [--fonts] [--colors] [--dashes] [--spelling]

Only the requested operations are applied.
"""
import re
import sys
import zipfile
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from docx import Document
from docx.shared import RGBColor
from docx.oxml.ns import qn

SPELLING = [
    ("favourable", "favorable"), ("centres", "centers"), ("centre", "center"),
    ("characterised", "characterized"), ("characterisation", "characterization"),
    ("behaviour", "behavior"), ("analysed", "analyzed"), ("analyse", "analyze"),
    ("oxidise", "oxidize"), ("minimising", "minimizing"), ("minimisation", "minimization"),
    ("colouring", "coloring"), ("colour", "color"), ("optimisation", "optimization"),
    ("stabilise", "stabilize"), ("utilise", "utilize"),
]


def set_style_font(style, name="Times New Roman", east_asia="宋体"):
    rPr = style.element.get_or_add_rPr()
    rf = rPr.find(qn("w:rFonts"))
    if rf is None:
        rf = rPr.makeelement(qn("w:rFonts"), {})
        rPr.insert(0, rf)
    for a in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
        if rf.get(qn(a)) is not None:
            del rf.attrib[qn(a)]
    for a in ("w:ascii", "w:hAnsi", "w:cs"):
        rf.set(qn(a), name)
    rf.set(qn("w:eastAsia"), east_asia)
    style.font.name = name


def fix_fonts(doc, path):
    for sname in ("Normal", "Heading 1", "Heading 2", "Heading 3", "Title", "Caption"):
        try:
            set_style_font(doc.styles[sname])
        except KeyError:
            pass
    dd = doc.styles.element.find(qn("w:docDefaults"))
    if dd is not None:
        rPr = dd.find(qn("w:rPrDefault") + "/" + qn("w:rPr"))
        if rPr is not None:
            rf = rPr.find(qn("w:rFonts"))
            if rf is not None:
                for a in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
                    if rf.get(qn(a)) is not None:
                        del rf.attrib[qn(a)]
                for a in ("w:ascii", "w:hAnsi", "w:cs"):
                    rf.set(qn(a), "Times New Roman")
                rf.set(qn("w:eastAsia"), "宋体")
    fixed = 0
    for p in doc.paragraphs:
        for r in p.runs:
            if r.font.name == "Times":
                r.font.name = "Times New Roman"
                fixed += 1
    return fixed


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


def unify_colours(doc):
    n = 0
    for r in iter_runs(doc):
        if r.text.strip():
            r.font.color.rgb = RGBColor(0, 0, 0)
            n += 1
    return n


def unify_dashes(doc):
    n = 0
    for r in iter_runs(doc):
        if "Cu-Ni" in r.text:
            r.text = r.text.replace("Cu-Ni", "Cu\u2013Ni")
            n += 1
    return n


def unify_spelling(doc):
    n = 0
    for r in iter_runs(doc):
        t = r.text
        for uk, us in SPELLING:
            t = re.sub(r"\b" + uk + r"\b",
                       lambda m: us.capitalize() if m.group(0)[0].isupper() else us,
                       t, flags=re.I)
        if t != r.text:
            r.text = t
            n += 1
    return n


def strip_times_refs(path):
    """Replace the non-existent font name 'Times' inside the XML parts."""
    path = Path(path)
    tmp = path.with_suffix(".tmp")
    zin = zipfile.ZipFile(path)
    changed = 0
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename in ("word/document.xml", "word/styles.xml"):
                s = data.decode("utf-8", "ignore")
                s2 = (s.replace('w:ascii="Times"', 'w:ascii="Times New Roman"')
                       .replace('w:hAnsi="Times"', 'w:hAnsi="Times New Roman"')
                       .replace('w:cs="Times"', 'w:cs="Times New Roman"'))
                if s2 != s:
                    changed += s.count('="Times"')
                    data = s2.encode("utf-8")
            zout.writestr(item, data)
    zin.close()
    tmp.replace(path)
    return changed


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    flags = {a for a in argv if a.startswith("--")}
    files = [a for a in argv if not a.startswith("--")]
    for f in files:
        doc = Document(f)
        report = []
        if "--fonts" in flags:
            report.append(f"fonts fixed: {fix_fonts(doc, f)}")
        if "--colors" in flags:
            report.append(f"runs recoloured: {unify_colours(doc)}")
        if "--dashes" in flags:
            report.append(f"runs with Cu-Ni: {unify_dashes(doc)}")
        if "--spelling" in flags:
            report.append(f"runs respelled: {unify_spelling(doc)}")
        doc.save(f)
        if "--fonts" in flags:
            xml_fixed = strip_times_refs(f)
            if xml_fixed:
                report.append(f"'Times' xml refs: {xml_fixed}")
        print(f"{Path(f).name}: " + " | ".join(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
