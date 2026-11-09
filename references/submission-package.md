# Submission package

## Naming

Use `<MANUSCRIPT-ID>_<Item>.docx`, ASCII only, no spaces, no version numbers, no
brackets. Example set for Elsevier:

| File | Editorial Manager item type |
|---|---|
| `JOURNAL-0000-00000_Cover_Letter.docx` | Cover Letter |
| `JOURNAL-0000-00000_Highlights.docx` | Highlights |
| `JOURNAL-0000-00000_Manuscript.docx` | Manuscript |
| `JOURNAL-0000-00000_Response_to_Reviewers.docx` | Response to Reviewers |
| `JOURNAL-0000-00000_Figures.docx` | Figures |
| `JOURNAL-0000-00000_Tables.docx` | Tables |
| `JOURNAL-0000-00000_Supplementary_Material.docx` | Supplementary Material |
| `JOURNAL-0000-00000_Declaration_of_Interests.docx` | Declaration of Interest |

Keep drafts and backups out of the upload folder (`_archive/`).

## Size limits

- Editorial systems commonly reject files above 10-50 MB; email gateways around 20 MB.
- Target: every file under ~10 MB, hard ceiling 20 MB.
- Images: 300 dpi minimum at final print width. For a 16 cm figure, 300 dpi = 1900 px,
  600 dpi = 3800 px. A 3000 px long side (~476 dpi) is a safe, high-quality default.
- Do not store 6000-13000 px renders; they add nothing on screen and break viewers.

## Compatibility

- Standard OOXML (`.docx`) only; no `.docm`, no OLE objects, no linked images.
- Fonts: Times New Roman / Arial / Symbol / Cambria Math only. Check for `Times`,
  `Tahoma`, `Courier` in unused styles and in `docDefaults`.
- Every media part must have an extension and a matching `[Content_Types].xml` entry.
- Images: baseline JPEG or PNG, RGB (not CMYK), no progressive JPEG.

## Verification before upload

```text
python scripts/verify_package.py <folder>
```

Then open each file once (render page 1) and confirm it is not blank. A file that opens
in your editor but not in a reviewer's Word is usually one of: oversized image,
extensionless media part, or a missing font.

## Upload order

Cover Letter -> Manuscript -> Response to Reviewers -> Highlights -> Figures -> Tables ->
Supplementary Material -> Declaration.

## Response letter structure

- Header block: manuscript number, title, journal.
- "General Response": 4-6 bullets summarising the revision; no new claims.
- Per reviewer: heading `Reviewer N (Major/Minor revision)`.
- Per comment: `R<N>-<k>  <short title>`, then three paragraphs:
  `Comment:` (the reviewer's text, quoted), `Response:`, `Changes made:`.
- Evidence (certificates, extra plots) as `Fig. R1`, `Fig. R2` inside the relevant
  response, caption below the image.
- No Chinese, no internal notes, no planning tables.

## Cover letter (revision)

Must describe the revision as submitted, not the original submission. Specifically:
never restate a mechanism claim that the revision downgraded, and never claim
"for the first time" for something the reviewers challenged.
