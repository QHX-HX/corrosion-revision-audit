# python-docx recipes that survive real documents

All snippets assume:

```python
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.oxml.ns import qn
```

## Span replacement across runs

The single most useful function. Works when the target text is split across runs
(common after spell-check, superscripts, or partial edits).

```python
def rep(p, old, new, red=False):
    runs = p.runs
    starts, pos = [], 0
    for r in runs:
        starts.append(pos)
        pos += len(r.text)
    full = "".join(r.text for r in runs)
    i = full.find(old)
    if i < 0:
        return False
    end = i + len(old)
    si = max(k for k, s in enumerate(starts) if s <= i)
    ei = max(k for k, s in enumerate(starts) if s < end)
    pre = runs[si].text[:i - starts[si]]
    suf = runs[ei].text[end - starts[ei]:]
    if si == ei:
        runs[si].text = pre + new + suf
        if red:
            runs[si].font.color.rgb = RGBColor(0xFF, 0, 0)
    else:
        runs[si].text = pre + new
        if red:
            runs[si].font.color.rgb = RGBColor(0xFF, 0, 0)
        for k in range(si + 1, ei):
            runs[k].text = ""
        runs[ei].text = suf
    return True
```

## Rebuild a paragraph as label + body without inheriting bold

```python
p = doc.paragraphs[i]
text = p.text
for r in list(p.runs):
    r._element.getparent().remove(r._element)
p.add_run("Response:").bold = True
p.add_run(text[len("Response:"):]).bold = False
```

## Delete a paragraph or a table

```python
p._p.getparent().remove(p._p)
t._tbl.getparent().remove(t._tbl)
```

Deleting a caption paragraph does **not** delete the table under it.

## Insert after an element, in the right order

`add_paragraph()` appends at the end; `add_table()` too. Insert with `addnext` /
`addprevious` and build in reverse when adding several elements.

```python
anchor._p.addnext(new_para._p)     # new_para after anchor
cap._p.addprevious(img._p)         # image before caption
```

## Table cell text without losing formatting

```python
def setcell(cell, txt):
    p = cell.paragraphs[0]
    if p.runs:
        p.runs[0].text = txt
        for r in p.runs[1:]:
            r.text = ""
    else:
        p.add_run(txt)
```

## Check for merged cells before believing duplicates

```python
from docx.oxml.ns import qn
for tr in t._tbl.findall(qn("w:tr")):
    spans = []
    for tc in tr.findall(qn("w:tc")):
        gs = tc.find(qn("w:tcPr") + "/" + qn("w:gridSpan"))
        spans.append(int(gs.get(qn("w:val"))) if gs is not None else 1)
    print(spans)          # [1,2,2,2,1] -> five logical columns
```

## Embed an image safely

```python
p.add_run().add_picture(r"...\fig.jpg", width=Cm(12.5))
```

The path **must** end in `.png`, `.jpg` or `.jpeg`. Afterwards verify:

```python
import zipfile
[ n for n in zipfile.ZipFile(path).namelist() if n.startswith("word/media") ]
# any name ending with a bare '.' is broken in Word
```

## Force fonts at style and document level

```python
for name in ("Normal", "Heading 1", "Heading 2", "Heading 3", "Title", "Caption"):
    try:
        st = doc.styles[name]
    except KeyError:
        continue
    st.font.name = "Times New Roman"
    rPr = st.element.get_or_add_rPr()
    rf = rPr.find(qn("w:rFonts"))
    if rf is None:
        rf = rPr.makeelement(qn("w:rFonts"), {})
        rPr.insert(0, rf)
    for a in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
        if rf.get(qn(a)) is not None:
            del rf.attrib[qn(a)]
    rf.set(qn("w:ascii"), "Times New Roman")
    rf.set(qn("w:hAnsi"), "Times New Roman")
    rf.set(qn("w:cs"), "Times New Roman")
    rf.set(qn("w:eastAsia"), "宋体")
```

Also patch `w:docDefaults/w:rPrDefault/w:rPr/w:rFonts` the same way, otherwise new
text falls back to the theme font (Calibri).

## Detecting "Times" (a real font, not Times New Roman)

```python
import zipfile, re
z = zipfile.ZipFile(path)
for n in ("word/document.xml", "word/styles.xml"):
    xml = z.read(n).decode("utf-8", "ignore")
    hits = re.findall(r'w:(?:ascii|hAnsi|cs)="Times"', xml)
```

`Times` is not installed on most systems, so Word substitutes and line breaks move.

## Scan XML, not paragraphs, for leftovers

```python
xml = z.read("word/document.xml").decode("utf-8")
len(re.findall(r"[\u4e00-\u9fff]", xml))     # Chinese anywhere, including tables
```

## Rebuild a docx zip while replacing media (keeps layout, changes pixels)

```python
with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zout:
    for item in zin.infolist():
        data = zin.read(item.filename)
        if item.filename.startswith("word/media/"):
            data = recompress(data)          # new bytes, same part name
        zout.writestr(item, data)
```

Image extents (EMU) live in `document.xml`, so replacing pixels never moves the frame.

## Lock files

Before writing, check for `~$<name>.docx` in the same folder. If present, ask the user
to close the document; otherwise `save()` raises `PermissionError`.
