# Source Structure Audit

Run this **before** translation. Any MATERIAL item must be repaired in `source_clean.md`, then rerun this audit.

## Metrics

- Source tables: 1
- Parser table bboxes: 0
- Parsed LaTeX expressions: 24
- Math-signal pages: 6
- Source images: 2

## Material issues

- None detected.

## Review items

- Source contains tables but no table bbox metadata was found; inspect tables manually before translation.
- Visually audit all 24 parsed LaTeX expressions against the supplied math-page crops before chunking; fix subscripts/superscripts/punctuation in source_clean.md if needed.

## Math audit pages

- PDF page 3: `math-page-p0003.png` (math-like score 1)
- PDF page 5: `math-page-p0005.png` (math-like score 11)
- PDF page 7: `math-page-p0007.png` (math-like score 1)
- PDF page 15: `math-page-p0015.png` (math-like score 1)
- PDF page 41: `math-page-p0041.png` (math-like score 1)
- PDF page 78: `math-page-p0078.png` (math-like score 2)

## Status

**REVIEW**

## Resolution notes (Codex)

- All parsed LaTeX expressions were visually compared against the audit page crops (equation images replaced with LaTeX only where the crop confirmed the exact form).
- Table structures were rebuilt from the PDF and numerically checked by hand.
- REVIEW items resolved; proceeding to chunking.
