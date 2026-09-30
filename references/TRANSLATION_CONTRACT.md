# Translation Contract — Final Edition

Apply this contract to every prose chunk and every table-cell translation.

## Fidelity
Translate **every natural-language sentence and clause**. Do not summarize, compress, outline, explain, add commentary, or omit repetitive-looking material. Preserve claims, qualifiers, negation, conditions, comparisons, causal relations, limitations, numbers, citations, and rhetorical strength.

Natural Chinese word order is allowed. Information content must remain equivalent.

## Protected tokens
The chunker replaces audited code, LaTeX, URLs, DOIs, inline code, and standalone numbers with tokens such as `[[IMM_I000123]]`. Keep every such token **byte-for-byte unchanged** and in the same semantic position. Do not translate or expand it. Assembly restores the original audited content.

Tables appear in prose chunks only as tokens such as `[[TABLE_T0001]]`. Keep these tokens unchanged. Tables are translated separately through `chunks/table_tasks/Txxxx.json`.

## Block markers
Preserve every marker exactly:

`<!-- block:B000001 -->`

One source marker corresponds to exactly one translated block. Never merge, delete, duplicate, or reorder markers.

## Academic Chinese style
Prefer precise, conventional research Chinese rather than literal English syntax. On first occurrence, a useful pattern is `定向包围盒（Oriented Bounding Box, OBB）`; later occurrences may use `OBB`. Keep established model/dataset/project names such as Real2Code, SAM, DUSt3R, PartNet-Mobility, CodeLlama, LoRA, ICLR, CVPR unchanged unless the surrounding ordinary words require translation.

## Headings and captions
Translate genuine section/subsection headings, figure/table captions, footnotes, appendices, acknowledgements, and ordinary prose in references. Do not turn transitional prose such as “In summary, our contributions are threefold:” into a Markdown heading unless it is truly a section heading in the source.

## Bibliography
Keep author names, venue names, identifiers, URLs/DOIs, volume/issue/pages, and canonical model/project names. Translate natural-language paper titles unless the user requests otherwise. It is acceptable for venue/publication metadata to remain English.

## Figure-internal text
The raster figure itself is immutable. If parser-extracted figure-internal text is present in a `<details>` block, translate that extracted text while keeping the image unchanged.

## Uncertainty
If a source sentence, formula, table cell, or figure label is ambiguous because parsing is damaged, inspect the PDF/page crop. Do not guess from domain knowledge.
