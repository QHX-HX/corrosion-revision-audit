# Structure checklist

Run `scripts/check_refs.py` first; then walk this list.

## References

- [ ] Numbering is continuous from [1] to [N], no gaps, no duplicate entries.
- [ ] Every entry is cited at least once in the body.
- [ ] Every citation resolves to an entry (no dangling `[57]`).
- [ ] Range citations `[22–24]` are expanded before validation, otherwise the middle
      entries look uncited. `check_refs.py` does this.
- [ ] Duplicate detection compares the text **after** stripping the `[n]` prefix;
      otherwise identical entries never match.
- [ ] When an entry is deleted, renumber and add a mapping note in the response letter
      ("original [22]–[58] shift down by one").
- [ ] Standards are cited where the method is used, not only in the reference list.
      Cleaning practice and calculation standards are different documents; citing one
      for the other is a common reviewer catch.

## Figures

- [ ] Figure count in the figure file equals the highest figure number cited.
- [ ] Each image is immediately followed by its own caption (no orphan image, no
      orphan caption). Verify programmatically by walking the body elements.
- [ ] Panel letters in the caption match the panels in the image: `(a, c)` vs
      `(a–c)`, `(a1–d1)` ranges, upper vs lower case for multi-part schematics.
- [ ] The text never cites a panel that the caption does not define.
- [ ] Every element of the figure (extra circuit, extra panel, inset) is explained
      somewhere in the text. An unexplained panel reads as an error.

## Tables

- [ ] Every table is cited, including the last one; watch plural forms
      ("Tables 3 and 4" hides table 4 from naive `Table \d+` regexes).
- [ ] Column count in the caption/note matches the actual grid; merged cells make
      `python-docx` return the same cell twice - check `gridSpan` before "fixing"
      apparent duplicates.
- [ ] Units are in the header, with superscripts (`cm⁻²`, `mV dec⁻¹`), not in cells.
- [ ] Number format is uniform inside a column (`1.09×10⁻⁷`, not `1.09ⅹ10-7`).
- [ ] Notes listed under the table define every abbreviation used in it.

## Supplementary

- [ ] Naming is consistent: either `Table S1` or `Supplementary Table 1`, never both.
- [ ] Every supplementary item is cited in the main text.
- [ ] Supplementary tables do not duplicate main-text tables; if they do, delete one
      and renumber.
- [ ] After deletion, update every in-text reference and the numbering of later items.

## Cross-file

- [ ] Response letter comment IDs (R1-1, R2-M3, R3-4) are unique and ordered.
- [ ] Each reviewer comment has exactly one Response and one Changes paragraph.
- [ ] No internal notes, planning tables, or Chinese annotations survive in the
      submitted files. `audit_docx.py` scans the XML, not just paragraphs, because
      tables and text boxes are invisible to `doc.paragraphs`.
