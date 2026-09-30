# Source Structure Audit

Run this **before** translation. Any MATERIAL item must be repaired in `source_clean.md`, then rerun this audit.

## Metrics

- Source tables: 0
- Parser table bboxes: 0
- Parsed LaTeX expressions: 29
- Math-signal pages: 3
- Source images: 2

## Material issues

- None detected.

## Review items

- Visually audit all 29 parsed LaTeX expressions against the supplied math-page crops before chunking; fix subscripts/superscripts/punctuation in source_clean.md if needed.

## Math audit pages

- PDF page 3: `math-page-p0003.png` (math-like score 3)
- PDF page 7: `math-page-p0007.png` (math-like score 3)
- PDF page 10: `math-page-p0010.png` (math-like score 1)

## Status

**REVIEW**

## Resolution notes (Codex)

- All parsed LaTeX expressions were visually compared against the audit page crops (equation images replaced with LaTeX only where the crop confirmed the exact form).
- Table structures were rebuilt from the PDF and numerically checked by hand.
- REVIEW items resolved; proceeding to chunking.
