---
name: academic-pdf-zh
description: Convert academic PDFs into complete, clean Simplified-Chinese Markdown for close reading in Obsidian. Codex itself performs all translation; local document parsers only recover structure. Use when full-paper fidelity matters, especially for formulas, tables, figures, captions, references, multi-column PDFs, and long papers. No external translation API is required.
---

# Academic PDF → Chinese Research Markdown — Final Workflow

## Pipeline at a glance

```text
PDF ─► C parse+audit ─► D glossary ─► E freeze+chunk ─► F translate chunks ─┐
                                        └─► G translate table cells ────────┤
                                                                            ▼
                                                     H deterministic assemble ─► I final validation ─► <PDF>_中文.md
```

Every hand-off between phases is a file on disk (audit report, manifest, task JSONs, validation report). "Done" is defined by those artifacts, never by a feeling of completion.

## Goal
Produce a faithful Chinese close-reading edition of an academic paper. Optimize for semantic reading, not pixel-level PDF imitation.

Priority:
1. no omitted or invented technical content;
2. exact scientific data and identifiers;
3. correct formulas, tables, figures, captions, citations, and reading order;
4. natural academic Chinese;
5. clean Obsidian/Markdown reading experience.

## Non-negotiable rules
- **Translate; never summarize.** Do not abridge, outline, explain, or replace prose with takeaways.
- Codex performs translation itself. Do **not** configure OpenAI API, DeepSeek API, Google Translate, or another translation API.
- Default PDF parsing is local MinerU. Do not use a cloud document parser unless the user explicitly requests it.
- Never guess damaged math/table content from domain knowledge. Inspect the source PDF/crop.
- Do not claim completion until source audit and final validation are resolved.

## Phase A — one-time environment setup
From the installed skill directory:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/install.ps1
python scripts/doctor.py
```

On Linux/macOS:

```bash
bash scripts/install.sh
python scripts/doctor.py
```

The first MinerU run may download model weights. This is parser setup, not translation API usage.

## Phase B — capture a stable project root
At the beginning of the task, record the absolute project/workspace root and use absolute paths thereafter. Do not `cd` into `work/PAPER` and then create another relative `work/PAPER`.

The scripts also detect when they are run from inside a `work/` tree and anchor relative output to the parent project, preventing `work/work/...` nesting.

## Phase C — parse and audit the English source
Run:

```bash
python scripts/prepare_paper.py INPUT.pdf --project-root PROJECT_ROOT
```

For long papers, pilot-parse a few pages first to vet parser quality before committing to a full run:

```bash
python scripts/prepare_paper.py INPUT.pdf --project-root PROJECT_ROOT --pages 1-3
```

Default output:

```text
PROJECT_ROOT/work/PDF_STEM/
├── source/
│   ├── source_raw.md
│   ├── source_clean.md
│   ├── parser-meta.json
│   ├── middle.json                 # when MinerU exposes it
│   ├── images/
│   ├── figure_crops/
│   └── audit/
│       ├── table-*.png
│       └── math-page-*.png
├── source-audit.md
└── glossary.md
```

`prepare_paper.py` does **not** start translation. First read:
- `source-audit.md`
- `references/SOURCE_AUDIT.md`

Then inspect every MATERIAL issue and every relevant table/math crop. Repair `source/source_clean.md` until:
- table rows/columns/method names/numbers agree with the PDF;
- LaTeX agrees visually with the PDF;
- broken URLs/DOIs are fixed;
- no figure interrupts a split sentence;
- no fake headings or parser garbage remain.

Rerun the audit directly after edits:

```bash
python scripts/audit_source.py \
  --source WORK/source/source_clean.md \
  --pdf INPUT.pdf \
  --middle-json WORK/source/middle.json \
  --audit-dir WORK/source/audit \
  --report WORK/source-audit.md
```

If there is no `middle.json`, omit that argument. **Do not proceed while MATERIAL issues remain.** Review-only math items require visual inspection and explicit resolution by Codex before proceeding.

## Phase D — establish terminology
Read the first part of `source_clean.md`, then maintain `glossary.md` with recurring technical terms only. Example:

```text
articulated object -> 关节物体
oriented bounding box (OBB) -> 定向包围盒（OBB）
shape completion -> 形状补全
```

Do not overgrow the glossary with one-off ordinary words.

## Phase E — freeze fragile scientific content and create chunks
Read `references/TRANSLATION_CONTRACT.md`, then run:

```bash
python scripts/chunk_markdown.py \
  WORK/source/source_clean.md \
  --output-dir WORK/chunks \
  --assets-dir WORK/source/images \
  --pdf INPUT.pdf
```

This is a critical safety boundary:
- audited LaTeX, code, inline code, URLs, DOIs, and standalone numbers become immutable `[[IMM_Ixxxxxx]]` tokens;
- each whole table becomes one `[[TABLE_Txxxx]]` token in prose chunks;
- tables are converted into deterministic cell-translation tasks under `chunks/table_tasks/`;
- prose is assigned stable hidden block IDs.

Do not bypass this step by translating `source_clean.md` directly.

## Phase F — translate prose chunks with Codex
For every manifest chunk, in order:

```text
chunks/source/0001.md -> chunks/translated/0001.md
chunks/source/0002.md -> chunks/translated/0002.md
...
```

For each chunk:
- translate all natural-language prose;
- keep every `<!-- block:Bxxxxxx -->` marker exactly;
- keep every `[[IMM_Ixxxxxx]]` and `[[TABLE_Txxxx]]` token exactly;
- preserve image Markdown and HTML structure;
- translate parser-extracted text inside `<details>` when it is ordinary natural language;
- never merge source blocks or omit bibliography/appendix prose.

Write each completed chunk to disk immediately before moving to the next chunk. **Re-chunking is safe**: rerunning `chunk_markdown.py` preserves already-translated chunks and restores filled table-cell translations wherever the underlying table is unchanged, so interruptions and source repairs never discard completed work.

## Phase G — translate tables safely
For every `WORK/chunks/table_tasks/Txxxx.json`, fill **only** each cell object's `translation` field. Translate from `source_for_translation` when present; it may contain protected tokens such as `[[TCP_P001]]` for numbers/arrows. Preserve those tokens exactly.

Example:

```json
{
  "id": "C0001",
  "source": "2 Parts (15)",
  "source_for_translation": "[[TCP_P001]] Parts ([[TCP_P002]])",
  "translation": "[[TCP_P001]] 个部件（[[TCP_P002]]）"
}
```

For canonical names, explicitly copy the original:

```json
{
  "source": "Real2Code",
  "translation": "Real2Code"
}
```

Do not edit `template`, `original`, `numeric_tokens`, cell IDs, or table IDs. This design prevents Codex from changing values such as `2.47` into `72.47` or merging `Ditto` and `PARIS` rows.

Check status:

```bash
python scripts/table_task_status.py WORK/chunks/table_tasks
```

It must report all cells translated before assembly.

## Phase H — assemble deterministically
Run:

```bash
python scripts/assemble_markdown.py WORK/chunks/manifest.json
```

Default final filename:

```text
WORK/PDF_STEM_中文.md
```

Assembly:
- verifies block order;
- reconstructs table rows/cells programmatically;
- restores exact audited math/code/URL/DOI/number literals;
- adds only unobtrusive Obsidian CSS metadata;
- copies images beside the Markdown.

## Phase I — final validation
Run:

```bash
python scripts/validate_translation.py \
  --manifest WORK/chunks/manifest.json \
  --source WORK/source/source_clean.md \
  --translated WORK/PDF_STEM_中文.md \
  --report WORK/validation.md
```

A material FAIL includes:
- missing/reordered chunk/block IDs;
- unresolved placeholders;
- changed/missing LaTeX;
- changed URL/DOI inventory or spaced/broken URLs;
- changed table number inventory or row count;
- missing/broken images;
- a transition sentence incorrectly turned into a heading;
- implausibly short Chinese output.

`REVIEW` may be caused by bibliography/venue metadata that intentionally remains English. Inspect it and document the resolution in `validation.md` before calling the paper complete.

## Final output policy
The primary reading artifact is:

```text
PDF_STEM_中文.md
images/
```

Keep `source-audit.md`, `validation.md`, `glossary.md`, and `chunks/` as audit/work files.

Never mix AI study notes into the faithful translation. Only if the user separately asks for a 精读版 / reading companion, create `reading-notes.md` after translation and clearly label it as assistant-generated reading support.

## Reading-quality conventions
- remove visible PDF page boundaries, repeated conference headers, and standalone page numbers;
- preserve genuine section hierarchy, not transitional prose as headings;
- rejoin sentences split only by PDF page breaks;
- composite Figure = one figure-level crop whenever possible;
- put translated caption immediately below the figure/table;
- leave raster figure pixels unchanged; translated extracted labels may live in a collapsed `<details>` block;
- complex/wide tables may remain HTML; the optional Obsidian CSS makes them horizontally scrollable;
- institution names in author affiliation lines should normally be translated to Chinese; author names remain unchanged.

Optional Obsidian snippet: `assets/obsidian-research.css`. Never modify the user's vault automatically.

## Definition of done
Done means all of the following:
- source structural audit repaired and visually reviewed;
- all prose chunks translated in source order;
- all table cell tasks completed;
- block IDs accounted for;
- exact math/code/URL/DOI/number restoration succeeded;
- figures resolve and are not fragmented;
- table numerics/rows match the audited source;
- final validation has no unresolved material issue;
- the output is complete Chinese academic prose, not a summary.
