#!/usr/bin/env python
"""Cross-check numbers that must agree across a revision package.

High-signal comparisons, in order of usefulness:
  1. Abstract vs Conclusions (same numbers, same rounding)
  2. Response letter vs manuscript (the letter quotes what it claims to have fixed)
  3. Text vs tables, for scientific-notation values only

Usage:
    python crosscheck_numbers.py manuscript.docx
    python crosscheck_numbers.py manuscript.docx --letter response.docx
    python crosscheck_numbers.py manuscript.docx --tables tables.docx [--supplementary si.docx]
"""
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from docx import Document

SUP = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺", "0123456789-+")
SCI = re.compile(r"(\d+(?:\.\d+)?)\s*[×x]\s*10\s*([⁻⁺]?[⁰¹²³⁴⁵⁶⁷⁸⁹0-9\-+]+)")
PLAIN = re.compile(r"(?<![\d.])(\d+\.\d{2,})(?![\d.])")


def numbers(text, sci_only=False):
    out = set()
    for m in SCI.finditer(text):
        e = m.group(2).translate(SUP).replace("^", "")
        try:
            out.add(f"{float(m.group(1)):.4g}e{int(e)}")
        except ValueError:
            pass
    if not sci_only:
        for m in PLAIN.finditer(text):
            out.add(f"{float(m.group(1)):.4g}")
    return out


def paragraphs(path):
    return [p.text for p in Document(path).paragraphs]


def section(paras, start_pat, stop_pat=r"^\d+\.\s|^References|^Acknowledg"):
    out, on = [], False
    for t in paras:
        s = t.strip()
        if re.match(start_pat, s, flags=re.I):
            on = True
            out.append(s)
            continue
        if on and re.match(stop_pat, s):
            break
        if on and s:
            out.append(s)
    return "\n".join(out)


def table_numbers(path):
    doc = Document(path)
    vals = set()
    for t in doc.tables:
        for row in t.rows:
            for c in row.cells:
                vals |= numbers(c.text, sci_only=True)
    return vals


def ctx(text, value):
    mant = value.split("e")[0]
    i = text.find(mant)
    return text[max(0, i - 40):i + 45].replace("\n", " ") if i >= 0 else ""


def report(name, a, b, a_name, b_name, sci_only=False):
    na, nb = numbers(a, sci_only), numbers(b, sci_only)
    miss = sorted(na - nb)
    print(f"{name}: {len(na)} numbers in {a_name}, {len(nb)} in {b_name}, "
          f"{len(na & nb)} shared")
    for v in miss[:15]:
        print(f"   {v:>10} only in {a_name}  <- {ctx(a, v)[:70]}")
    return miss


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    path = argv[0]
    paras = paragraphs(path)
    abstract = section(paras, r"^Abstract")
    concl = section(paras, r"^\d*\.?\s*Conclusions?", r"^Acknowledg|^References|^Declaration")

    problems = 0
    if abstract and concl:
        m1 = report("Abstract -> Conclusions", abstract, concl, "abstract", "conclusions")
        m2 = report("Conclusions -> Abstract", concl, abstract, "conclusions", "abstract")
        problems += len(m1) + len(m2)
    else:
        print("could not locate abstract/conclusions sections")

    if "--letter" in argv:
        letter = argv[argv.index("--letter") + 1]
        ltext = "\n".join(t for t in paragraphs(letter) if t.startswith("Response"))
        body = "\n".join(paras)
        print()
        report("Letter -> Manuscript", ltext, body, "letter", "manuscript")

    if "--tables" in argv:
        tabs = argv[argv.index("--tables") + 1]
        vals = table_numbers(tabs)
        if "--supplementary" in argv:
            vals |= table_numbers(argv[argv.index("--supplementary") + 1])
        body = "\n".join(paras)
        missing = sorted(v for v in vals if v not in numbers(body, sci_only=True))
        print(f"\nScientific-notation values in tables not found in the text: {len(missing)}")
        for v in missing[:15]:
            print(f"   {v:>10}")

    print()
    print("Review each flagged value against the raw data; the script finds candidates,")
    print("it does not decide which document is right.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
