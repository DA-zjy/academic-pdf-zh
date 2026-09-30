#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

from _common import DISPLAY_MATH_RE, INLINE_MATH_RE, IMAGE_RE, numeric_tokens, page_rect_from_bbox

HTML_TABLE_RE = re.compile(r"<table\b.*?</table>", re.I | re.S)
MD_TABLE_RE = re.compile(r"(?m)(?:^\s*\|.*\|\s*$\n){2,}")
BROKEN_URL_RE = re.compile(r"https?:\s+//|\b[A-Za-z0-9-]+\.\s+(?:com|org|net|edu|io|gov|ai|cn)\b|/[A-Za-z0-9._/-]*\.\s+\d{2,}", re.I)
GARBAGE = [re.compile(r"page\.page_number", re.I), re.compile(r"<PARSED TEXT FOR PAGE", re.I)]
MATH_CHARS = "∈∑∏√≤≥≈≠±∞θλμσφψαβγδΔ∂∇"


def extract_tables(md: str) -> list[str]:
    found = [(m.start(), m.group(0)) for m in HTML_TABLE_RE.finditer(md)]
    found += [(m.start(), m.group(0)) for m in MD_TABLE_RE.finditer(md)]
    return [t for _, t in sorted(found)]


def walk_blocks(obj):
    if isinstance(obj, dict):
        yield obj
        for v in obj.values():
            yield from walk_blocks(v)
    elif isinstance(obj, list):
        for v in obj: yield from walk_blocks(v)


def table_blocks_from_middle(path: Path | None):
    if not path or not path.exists(): return []
    try: data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception: return []
    pages = data.get("pdf_info", []) if isinstance(data, dict) else []
    out=[]
    for pos,p in enumerate(pages):
        if not isinstance(p,dict): continue
        page_idx=int(p.get("page_idx",pos)); page_size=p.get("page_size")
        seen=set()
        for b in walk_blocks(p.get("para_blocks") or []):
            typ=str(b.get("type","")).lower()
            if typ not in {"table","table_body"}: continue
            bbox=b.get("bbox_fs") or b.get("bbox")
            key=(page_idx, tuple(bbox or []))
            if not bbox or key in seen: continue
            seen.add(key); out.append((page_idx,page_size,bbox))
    return out


def crop_and_text(pdf: Path, page_idx:int, page_size, bbox, out:Path):
    import fitz
    doc=fitz.open(pdf); page=doc[page_idx]
    rect=page_rect_from_bbox(page,bbox,page_size)
    if rect is None: return ""
    rect=fitz.Rect(max(0,rect.x0-3),max(0,rect.y0-3),min(page.rect.width,rect.x1+3),min(page.rect.height,rect.y1+3))
    pix=page.get_pixmap(matrix=fitz.Matrix(2.4,2.4),clip=rect,alpha=False)
    out.parent.mkdir(parents=True,exist_ok=True); pix.save(out)
    return page.get_text("text",clip=rect)


def render_math_pages(pdf:Path, out_dir:Path):
    import fitz
    doc=fitz.open(pdf); rows=[]
    for i,page in enumerate(doc):
        txt=page.get_text("text")
        score=sum(txt.count(c) for c in MATH_CHARS)
        if score:
            out=out_dir/f"math-page-p{i+1:04d}.png"
            pix=page.get_pixmap(matrix=fitz.Matrix(1.6,1.6),alpha=False); pix.save(out)
            rows.append((i+1,score,out.name))
    return rows


def main()->int:
    p=argparse.ArgumentParser(description="Audit parser output before translation")
    p.add_argument("--source",type=Path,required=True); p.add_argument("--pdf",type=Path,required=True)
    p.add_argument("--middle-json",type=Path); p.add_argument("--audit-dir",type=Path,required=True); p.add_argument("--report",type=Path,required=True)
    a=p.parse_args(); md=a.source.read_text(encoding="utf-8",errors="replace"); a.audit_dir.mkdir(parents=True,exist_ok=True)
    material=[]; review=[]; lines=[]
    for g in GARBAGE:
        if g.search(md): material.append(f"Parser garbage remains: `{g.pattern}`")
    if BROKEN_URL_RE.search(md): material.append("Broken/spaced URL-like text remains; repair URLs from the PDF before chunking.")

    src_tables=extract_tables(md); middle_tables=table_blocks_from_middle(a.middle_json)
    table_rows=[]
    for idx,b in enumerate(middle_tables,1):
        page_idx,page_size,bbox=b; crop=a.audit_dir/f"table-p{page_idx+1:04d}-{idx:02d}.png"
        pdf_text=crop_and_text(a.pdf,page_idx,page_size,bbox,crop)
        pdf_nums=numeric_tokens(pdf_text)
        src_nums=numeric_tokens(src_tables[idx-1]) if idx-1 < len(src_tables) else []
        mismatch = Counter(pdf_nums) != Counter(src_nums) if pdf_nums and src_nums else False
        if idx-1 >= len(src_tables): material.append(f"Table {idx}: MinerU middle JSON has a table block but source Markdown has no corresponding table.")
        elif mismatch:
            material.append(f"Table {idx} (page {page_idx+1}): numeric-token mismatch between PDF crop and source table. Inspect `{crop.name}` and repair source table before translation.")
        table_rows.append((idx,page_idx+1,crop.name,len(pdf_nums),len(src_nums),mismatch))
    if src_tables and not middle_tables:
        review.append("Source contains tables but no table bbox metadata was found; inspect tables manually before translation.")
    if middle_tables and len(src_tables)!=len(middle_tables):
        material.append(f"Table count mismatch: source={len(src_tables)} parser-bbox={len(middle_tables)}")

    math_exprs=[]
    for m in DISPLAY_MATH_RE.finditer(md): math_exprs.append(next(g for g in m.groups() if g is not None))
    math_exprs += [m.group(1) for m in INLINE_MATH_RE.finditer(md)]
    math_pages=render_math_pages(a.pdf,a.audit_dir)
    masked=DISPLAY_MATH_RE.sub(" ",md); masked=INLINE_MATH_RE.sub(" ",masked)
    loose=[c for c in MATH_CHARS if c in masked]
    if loose: review.append("Math-like Unicode appears outside LaTeX delimiters: "+", ".join(sorted(set(loose)))+". Compare with math-page crops.")
    if math_pages and not math_exprs: material.append("PDF has math-like signals but source Markdown has zero LaTeX expressions.")
    if math_exprs: review.append(f"Visually audit all {len(math_exprs)} parsed LaTeX expressions against the supplied math-page crops before chunking; fix subscripts/superscripts/punctuation in source_clean.md if needed.")

    # Detect obvious figure interruption that normalization failed to reflow.
    fig_interrupt=re.compile(r"[^.!?;:\n]\n\n!\[[^\]]*\]\([^\n]+\)\n\n(?:Figure|Fig\.)\s*\d+[:：][^\n]*\n\n[a-z]")
    if fig_interrupt.search(md): material.append("A figure still interrupts an unfinished English sentence; join the sentence and move the figure after the completed paragraph.")

    status="PASS" if not material and not review else ("FAIL" if material else "REVIEW")
    lines=["# Source Structure Audit","","Run this **before** translation. Any MATERIAL item must be repaired in `source_clean.md`, then rerun this audit.","","## Metrics","",f"- Source tables: {len(src_tables)}",f"- Parser table bboxes: {len(middle_tables)}",f"- Parsed LaTeX expressions: {len(math_exprs)}",f"- Math-signal pages: {len(math_pages)}",f"- Source images: {len(IMAGE_RE.findall(md))}","","## Material issues","",*( [f"- {x}" for x in material] if material else ["- None detected."] ),"","## Review items","",*( [f"- {x}" for x in review] if review else ["- None."] )]
    if table_rows:
        lines += ["","## Table audit crops","","|Table|PDF page|crop|PDF numeric tokens|source numeric tokens|mismatch|","|---:|---:|---|---:|---:|---|"]
        for i,pg,c,pn,sn,mis in table_rows: lines.append(f"|{i}|{pg}|`{c}`|{pn}|{sn}|{'YES' if mis else 'no'}|")
    if math_pages:
        lines += ["","## Math audit pages",""]+[f"- PDF page {pg}: `{name}` (math-like score {score})" for pg,score,name in math_pages]
    lines += ["","## Status","",f"**{status}**",""]
    a.report.parent.mkdir(parents=True,exist_ok=True); a.report.write_text("\n".join(lines),encoding="utf-8")
    print(a.report.resolve()); print(f"status={status} material={len(material)} review={len(review)}")
    return 2 if material else (1 if review else 0)

if __name__=="__main__": raise SystemExit(main())
