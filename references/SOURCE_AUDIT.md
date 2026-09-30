# Source Audit Protocol

Run this before translation. The principle is: **fix the English structural source first, then freeze fragile content.**

## Tables — mandatory visual audit
Every detected MinerU table should have a crop under `source/audit/`. Compare the table in `source_clean.md` with the crop.

- Row count, column count, method names, arrows, N/A values, and **every numeric cell** must agree with the PDF.
- Do not infer a missing value from surrounding prose. Read it from the crop/page.
- If the table is malformed, rebuild the source table before chunking. Markdown or HTML are both acceptable.
- Rerun `audit_source.py`. Numeric-token mismatch must be resolved before translation.

After chunking, whole tables are removed from free-form prose translation. Each table gets `chunks/table_tasks/Txxxx.json`. Codex edits only each cell's `translation` field. If `source_for_translation` contains `[[TCP_...]]` tokens, preserve them exactly; they represent numbers/arrows restored by script. The original template, row/column structure, and protected values are reconstructed deterministically.

For a canonical method/model name such as `Real2Code`, `Ditto`, `PARIS`, or `GPT-4`, explicitly set `translation` to the same string rather than leaving it blank.

## Math — mandatory visual audit when present
`audit_source.py` renders any page with math-like signals into `source/audit/math-page-*.png`.

For each LaTeX expression in `source_clean.md`, compare subscript/superscript placement, Greek symbols, punctuation, vector/bold styling, dimensions, inequalities, and equation numbering against the PDF image. Correct the source LaTeX first.

Typical parser mistakes to catch:
- `u^p` when the PDF shows `u_p`;
- a Greek symbol such as `θ` left outside `$...$`;
- punctuation accidentally absorbed into math (`$d;$`);
- `R` vs `\mathbb{R}`;
- broken exponents such as `96<sup>3</sup>` instead of `$96^3$`.

After this audit, chunking locks the LaTeX so Codex cannot mutate it during translation.

## Figures and page breaks
Composite figures should appear as one figure-level crop, not a row of PDF image fragments. If a figure interrupts an unfinished sentence because it sat at the top of the next PDF page, join the sentence and move the figure/caption after the completed paragraph.

## URLs / DOI
Repair parser-induced spaces before chunking, e.g. `https: //`, `github. com`, `arxiv.org/abs/2101. 06605`. Verify against the PDF. Once repaired, chunking locks them byte-for-byte.

## Outline
Check that only true paper sections are Markdown headings. Transitional sentences and list lead-ins should remain prose/bold prose.
