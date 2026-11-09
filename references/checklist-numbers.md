# Number checklist

Every quantity that appears twice must appear identically. The expensive failures are
not typos; they are **unit or condition mix-ups**.

## Where a number can live

| Location | Example |
|---|---|
| Abstract | "0.0428 ± 0.0051 to 0.0915 ± 0.0157 mm/y" |
| Results text | "corrosion rate increased from ... to ..." |
| Discussion | "an order of magnitude higher" |
| Conclusions | same numbers as abstract |
| Highlights | rounded headline figure ("about 60 %") |
| Cover letter | "a factor of about 15" |
| Response letter | quotes of every correction |
| Tables | fitted or measured values |
| Supplementary | full parameter sets |
| Figure captions | axes, conditions, panel assignment |

If a number is in the abstract it must be in the conclusions; if it is in the response
letter it must be in the manuscript.

## Rules

1. **Unit conversion is a claim.** A density of 8.94 g/cm³ entered as g/m³ scales every
   rate by 1000 and every thickness by more. Recompute from raw data, never from the
   previous text.
2. **Range vs pair.** "From A to B" may mean min-max or a specific two-point comparison
   (e.g. 191 → 765 μM). Check which one the source supports. A min-max claim is wrong if
   the monotonic trend breaks in between.
3. **Day / condition mix-ups.** Before quoting "at day 14", open the raw table and read
   the day-14 row. A correct table with a wrong sentence is the most common fatal error.
4. **Non-monotonic data needs a caveat.** If the trend reverses (1530 μM), the sentence
   must say so rather than asserting a monotonic relation.
5. **Exactness level.** Fitted parameters: keep 2 decimals. Derived rates: keep 3
   significant figures. Rounded claims ("about 60 %") must be consistent with the
   unrounded numbers.
6. **Sign and direction.** `Ecorr` is negative; `Rp` corresponds to resistance, not rate.
   A sign flip often hides an inverted statement ("an increase in Rp corresponds to an
   increase in rate" - wrong).
7. **Superscripts.** `10-7`, `cm2`, `Fe2+` rendered as plain text are wrong even when the
   number is right. They are visible in the PDF and in the reviewer's browser view.
8. **Statistics.** If ANOVA/Tukey was run, quote F, df and p exactly once and reuse the
   same values everywhere. Do not describe a test you did not run.

## Procedure

1. Extract all numeric tokens from each file (`crosscheck_numbers.py`).
2. Build a table: quantity -> value in each document.
3. For each row with more than one distinct value, go to the raw source and decide.
4. Fix every location, not just the one the reviewer mentioned.
5. Re-run the extraction until each quantity has exactly one value.

## Worked example (illustrative)

| Quantity | Text said | Table said | Raw data | Resolution |
|---|---|---|---|---|
| impedance at day 14 | 6.9 -> 2.2 | 4.0, 1.4, 3.3, 0.7 | day 1 = 6.9 -> 2.2 | text was quoting day 1 |
| binding energy | 164.1 | 166.2 (one row) | main component 164.3 | the table row picked a secondary component |
| current density | 6.6e-6 -> 9.8e-6 | min 4.6e-6 | two-point pair | the text was right; the check used min-max |

The point is the pattern, not the numbers: one document is right, the others must follow
it, and the resolution is always traceable to the raw data.
