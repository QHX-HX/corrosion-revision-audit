# corrosion-revision-audit

A workflow skill for auditing and repairing a corrosion-science manuscript revision
package: response letter, manuscript, tables, figures, highlights, supplementary
material, cover letter and declaration.

It exists because revision packages fail in predictable ways: a number that is right in
the table and wrong in the sentence, a claim downgraded in the text but not in the
abstract, a letter that promises a change the manuscript does not contain, a 97-megapixel
image that a reviewer's Word cannot open.

## What is inside

```
SKILL.md                      five-phase workflow (inventory -> structure -> numbers
                              -> language -> style -> package)
references/
  checklist-structure.md      citations, figures, tables, supplementary
  checklist-numbers.md        cross-document number audit, with worked examples
  checklist-language.md       claims, significance, hedging, rebuttal tone
  pitfalls.md                 18 real failure modes and how to detect them
  docx-recipes.md             python-docx recipes that survive real documents
  submission-package.md       naming, size limits, upload order
  origin-recipes.md           Origin 2024 COM automation, verified and broken commands
assets/
  response_letter_skeleton.md
  cover_letter_revision_skeleton.md
  origin/style.ogs            LabTalk styling commands that actually work
scripts/
  audit_docx.py               structure, fonts, colours, leftovers
  check_refs.py               reference integrity with range expansion
  crosscheck_numbers.py       abstract vs conclusions, letter vs manuscript, text vs tables
  unify_style.py              fonts, colours, dashes, spelling
  compress_media.py           downsample embedded images without moving layout
  verify_package.py           pre-flight check for the upload folder
  origin/probe.ps1            Origin install / COM probe
  origin/plot.ps1             tidy CSV -> multi-curve Origin figure -> PNG/TIFF
```

## Requirements

- Python 3.10+ with `python-docx`, `openpyxl`, `Pillow`
- PowerShell (for the Origin driver)
- Optional: Origin 2024 with COM enabled (`Origin.ApplicationSI`)

## Install

Copy the folder into your agent's skills directory, for example:

```
~/.dsh/skills/corrosion-revision-audit/
```

The skill is then available under the name `corrosion-revision-audit`.

## Quick start

```bash
python scripts/audit_docx.py manuscript.docx response.docx
python scripts/check_refs.py manuscript.docx --letter response.docx
python scripts/crosscheck_numbers.py manuscript.docx --letter response.docx \
       --tables tables.docx --supplementary supplementary.docx
python scripts/verify_package.py ./submission
```

```powershell
powershell -File scripts/origin/probe.ps1
powershell -File scripts/origin/plot.ps1 -Data nyquist.csv -Out out -Name fig10a `
    -XCol zre -YCol zim -NegateY -Square `
    -XTitle "Z' (\g(W)cm\+(2))" -YTitle "-Z'' (\g(W)cm\+(2))"
```

## Design principles

1. Numbers need a source: raw data, then the fitted table, then the text.
2. The response letter is a claim about the files - verify it like any other claim.
3. A mechanism downgrade must reach every surface (abstract, conclusions, highlights,
   captions, cover letter).
4. Back up before editing; mark substantive edits red.
5. A file that opens in your editor but not in a reviewer's Word is usually an
   oversized image, an extensionless media part, or a missing font.

## Known limitations

- Origin 2024 cannot set curve colours through COM: `layer.plotN.color` accepts the
  assignment and ignores it. Build the palette once in the GUI and save a `.otp`
  template; `plot.ps1 -Template` reuses it.
- Templates cannot be written by LabTalk either (`saveas type:=otp` fails); save them
  from the Origin GUI.
- Language and claim checks are only partly automatable; `references/checklist-language.md`
  is meant to be walked by hand.

## License

MIT
