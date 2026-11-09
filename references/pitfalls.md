# Pitfalls - 18 failure modes seen in a real revision

Each entry: symptom -> why it happens -> how to detect -> how to fix.

## Document structure

**1. Chinese text survives in a "cleaned" letter.**
`doc.paragraphs` does not include table cells or text boxes. A planning table at the end
of the file kept 142 Chinese characters after the heading paragraph above it was deleted.
Detect: scan `word/document.xml` for `[\u4e00-\u9fff]`.
Fix: delete the whole table (`t._tbl.getparent().remove(t._tbl)`), not just its caption.

**2. Duplicated table: main text vs supplementary.**
A supplementary table duplicated two main-text tables row for row.
Detect: compare row sets after dropping the condition column.
Fix: delete one set, renumber, update every citation.

**3. Merged cells look like duplicated columns.**
A 14x8 ANOVA table printed every value twice because `row.cells` repeats merged cells.
Detect: check `w:gridSpan`; `[1,2,2,2,1]` means 5 logical columns, not 8.
Fix: do not "repair" it; rebuild as two clean tables if the layout is confusing.

**4. Heading capitalisation drifts.**
"The Electrochemical measurements under different concentration of Fe2+" mixed title
case with sentence case.
Fix: one convention per level; units and species symbols keep their own case.

## Text editing with python-docx

**5. One `settext` bolds the whole paragraph.**
Replacing text via `runs[0].text = new` keeps run 0's formatting. When run 0 was the bold
label ("Response:"), the entire paragraph became bold.
Fix: rebuild as `(label, bold)` + `(body, regular)` runs.

**6. Targeted replacement silently fails when a word spans runs.**
`Fe2+` may be `Fe` + superscript `2+`; a search for `"Fe2+"` in a single run finds nothing.
Fix: join run texts, locate the span, write into the first run, clear the middle runs,
re-emit the tail (see `docx-recipes.md`).

**7. Superscripts are lost by naive replacement.**
Writing `"cm2"` as plain text renders `cm2`. After any text rewrite, re-check that
`2+`, `-7`, `⁻¹` are still superscript runs or Unicode superscripts.

**8. Colour reverts to theme default.**
New runs inherit the theme font/colour. If the document default is Calibri and the body
is Times New Roman, inserted sentences look different.
Fix: set the style (`Normal`, headings) and `docDefaults`, not just runs.

## Images

**9. Extensionless media part breaks Word.**
Inserting from a path without a suffix produced `word/media/image1.`; LibreOffice
rendered it, Word showed a blank.
Fix: always insert from a file ending in `.png` / `.jpg`; verify part names afterwards.

**10. Image part deduplicated back to the broken one.**
Re-inserting the same bytes reuses the existing part (hash match), so the broken name
persists.
Fix: re-encode first (different bytes), or strip the orphan part from the zip.

**11. 97-megapixel images.**
Decoder limits (PIL warns at 89 MP) and Word memory. Files > 50 MB are often rejected by
the submission system before a reviewer ever sees them.
Fix: `compress_media.py` with long side 3000 px (~476 dpi at 16 cm), JPEG q90.

**12. Caption above the image.**
Journal style is image then caption. Also a caption on the previous page separates the
two if a page break falls between them.

## Numbers and claims

**13. Day/condition mix-up.**
Day-1 impedance quoted as day 14. The table was right; the sentence was wrong.
Detect: re-derive from raw data for the exact day, not from the previous draft.

**14. "Significant" without a test.**
Abstract, conclusions and four results sentences claimed significance with no ANOVA.
Fix: either run the test or change the word; both are acceptable, silence is not.

**15. Mechanism downgraded in one place only.**
Main text hedged, but the abstract, highlights and cover letter still asserted the old
mechanism. The cover letter is the one everybody forgets.

**16. Response letter promises a change that does not exist.**
The letter described replacements and comparisons absent from the manuscript. Verify
each "Changes made" paragraph against the file.

## References

**17. Duplicate entry invisible to naive comparison.**
Two entries with identical text but different `[n]` prefixes look different until the
prefix is stripped.

**18. Range citation hides uncited entries.**
`[22–24]` marks only 22 in a naive regex; 23 and 24 appear uncited.
Fix: expand ranges before validation.

## Meta

Two more that are not bugs but cost the most time:

- **Editing a file while the user has it open in Word** -> `PermissionError` on save.
  Check for `~$*.docx` lock files first.
- **Rebuilding a table moves it.** `add_table` appends to the end; `addnext` inserts
  after a table, so building two tables in sequence reverses their order. Insert anchors
  in reverse, or re-order the XML elements explicitly.
