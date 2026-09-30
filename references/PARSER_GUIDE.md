# Parser Guide

## Default: local MinerU `pipeline`
Use local MinerU as the primary scientific-document parser. The skill invokes:

```bash
mineru -p INPUT.pdf -o OUTPUT -b pipeline -m auto -f true -t true
```

`pipeline` is the conservative local backend and is appropriate when GPU/VLM requirements are uncertain. Formula and table parsing are explicitly enabled. The paper is not sent to a translation service; Codex performs translation itself.

Current MinerU CLI also supports `hybrid-engine` with `--effort medium|high`. Use it only when the local machine has the required acceleration/resources and the pipeline parser visibly damages layout/math/tables.

## Marker fallback
If MinerU fails structurally and Marker is already installed:

```bash
python scripts/prepare_paper.py INPUT.pdf --parser marker
```

Always run the same source audit afterward.

## PyMuPDF4LLM emergency fallback
Use only when heavier parsers are unavailable:

```bash
python scripts/prepare_paper.py INPUT.pdf --parser pymupdf4llm
```

Treat formulas, composite figures, and complex tables as high-risk and inspect them manually.

## Parser switching rule
Do not switch for speed alone. Switch when reading order, formula fidelity, table structure, or figure integrity is materially worse than the PDF.
