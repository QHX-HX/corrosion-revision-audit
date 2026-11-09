---
name: corrosion-revision-audit
description: Audit and repair a corrosion-science manuscript revision package (response letter, manuscript, tables, figures, highlights, supplementary material, cover letter, declaration) for cross-document consistency, then package it so reviewers and editors can actually open it.
---

# Corrosion revision audit

Use this skill when the user supplies reviewer comments together with a revised
manuscript package and wants it checked, corrected, and made submission-ready.
Typical trigger phrases: "检查回复信和手稿是否一致", "审稿人意见回复", "返修",
"response to reviewers", "按要求改稿", "投稿包整理".

## Operating rules

- **Read before writing.** Never edit a file you have not parsed.
- **Back up first.** Before the first edit create `_archive/originals_<YYYYMMDD_HHMM>/`
  and copy every file you are about to modify.
- **Numbers need a source.** When two documents disagree, resolve against raw data
  first, then the fitted/measured table, then the text. State which source won and why.
- **Do not invent science.** If a mismatch cannot be resolved from the files, stop and
  ask; do not "harmonise" numbers by guessing.
- **Mark substantive edits red** (`FF0000`) in the manuscript. Leave pure typography
  (dashes, spacing, spelling) unmarked unless the user asks otherwise.
- **Never delete content silently.** Duplicated tables/figures may be removed only after
  the user confirms; it is a content decision, not a formatting one.
- Keep a running issue list with severity: **Fatal** (claim unsupported, number wrong),
  **Major** (cross-document inconsistency), **Minor** (style).

## Phase 0 - inventory

1. List every file in the package; map each to a journal item type.
2. Identify the authoritative sources: raw data workbooks, original images, the
   reviewer comments themselves.
3. Back up, then rename to formal names (`<MANUSCRIPT-ID>_Manuscript.docx` etc.).
   See `references/submission-package.md`.

## Phase 1 - structure (must pass before numbers)

Run:

```text
python scripts/audit_docx.py <files...>
python scripts/check_refs.py <manuscript.docx>
```

Check by hand what the scripts cannot: figure captions vs images one-to-one,
supplementary naming (`Table S1` vs `Supplementary Table 1`), table numbering.
See `references/checklist-structure.md`.

## Phase 2 - numbers

Run:

```text
python scripts/crosscheck_numbers.py <manuscript.docx> <tables.docx> [<supplementary.docx>]
```

Every number that appears in more than one place is a candidate. Compare:
abstract, results, discussion, conclusions, highlights, cover letter, response letter,
tables, supplementary tables, figure captions. See `references/checklist-numbers.md`.

The most expensive failures in practice are **day/condition mix-ups**: a value that is
correct for day 1 quoted as day 14, or a min-max pair quoted as a fixed two-point
comparison. Always re-derive from the raw data.

## Phase 3 - language and claims

Check the response letter against the manuscript line by line:

- Does every "we have added/modified/deleted X" correspond to something that exists?
- Were mechanism claims downgraded everywhere (abstract, conclusions, highlights,
  figure captions, cover letter) or only in one place?
- Are "significant"/"correlation" statements backed by an actual test?

See `references/checklist-language.md` and `references/pitfalls.md`.

## Phase 4 - style

Run:

```text
python scripts/unify_style.py <files...> --fonts --dashes --spelling
```

Defaults used by this author: Times New Roman throughout (including headings and
tables), black text, en dash in `Cu–Ni`, US spelling, 9 pt table text.
Only touch colours if the user asks.

## Phase 5 - package and compatibility

Run:

```text
python scripts/compress_media.py in.docx out.docx --max-px 3000 --quality 90
python scripts/verify_package.py <folder>
```

Then open every file visually (render page 1 at minimum) before declaring it ready.
Large images and invalid font names are the two failure modes that make a reviewer
unable to open a file. See `references/submission-package.md`.

## Phase 6 - redraw figures with Origin (optional)

When the user wants figures produced in Origin rather than an image editor, drive
Origin 2024 through COM from PowerShell (no Python packages required):

```text
powershell -File scripts/origin/probe.ps1
powershell -File scripts/origin/plot.ps1 -Data data.csv -Out <dir> -Name fig10a `
    -XCol zre -YCol zim -NegateY -Square `
    -XTitle "Z' (\g(W)cm\+(2))" -YTitle "-Z'' (\g(W)cm\+(2))" `
    -Template C:\path\house_style.otp
```

Input is a tidy CSV (`x,y,group`, or pass `-XCol/-YCol/-GroupCol`); each group becomes
one curve and its name becomes the legend entry. `-NegateY` is for Nyquist, where the
impedance convention plots `-Z''`. `-Square` makes the Nyquist box physically square and
gives both axes the same 0..max limits.

**Style belongs in the template.** Font, palette and legend placement cannot be set
reliably through LabTalk in Origin 2024 (`layer.plotN.color` ignores assignment,
`xb.font` takes an index, `saveas type:=otp` cannot write templates). Build
`house_style.otp` once in the GUI with Times New Roman, the four-colour palette and a
square box; the driver then reuses it for every figure. `assets/origin/style.ogs`
contains the LabTalk that does work, ready to paste into the Script Window.

Read `references/origin-recipes.md` before changing the driver: several obvious LabTalk
commands (`layer -i202`, `dpi:=`, `yb.text$`) fail silently in 2024. LabTalk returning
`True` does not mean the command worked - always verify the exported file exists.

For publication styling (Times New Roman, square Nyquist axes, palette), build a
template `.otp` once in the Origin GUI and pass it with `-Template`.

## Output contract

End every round with three things:

1. **Fixed** - table of what changed, per file.
2. **Open** - questions that need the author's scientific judgement.
3. **Status** - package table: file, size, pages, references, open/consistent flags.

## References

- `references/checklist-structure.md` - citations, figures, tables, supplementary
- `references/checklist-numbers.md` - cross-document number audit
- `references/checklist-language.md` - claims, significance, tense, hedging
- `references/pitfalls.md` - 18 real failure modes from a completed revision
- `references/docx-recipes.md` - python-docx editing recipes that actually work
- `references/submission-package.md` - naming, size limits, upload order
- `assets/response_letter_skeleton.md` - Comment / Response / Changes template
- `assets/cover_letter_revision_skeleton.md` - revision cover letter template
