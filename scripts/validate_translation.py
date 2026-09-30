#!/usr/bin/env python3
from __future__ import annotations

import argparse, json, re
from collections import Counter
from pathlib import Path
from _common import (BLOCK_ID_RE, IMAGE_RE, URL_RE, DOI_RE, extract_math, multiset_missing,
                     numeric_tokens, TABLE_PLACEHOLDER_RE, IMM_PLACEHOLDER_RE)

HTML_TABLE_RE=re.compile(r"<table\b.*?</table>",re.I|re.S)
MD_TABLE_RE=re.compile(r"(?m)(?:^\s*\|.*\|\s*$\n){2,}")
BROKEN_URL_RE = re.compile(r"https?:\s+//|\b[A-Za-z0-9-]+\.\s+(?:com|org|net|edu|io|gov|ai|cn)\b|/[A-Za-z0-9._/-]*\.\s+\d{2,}", re.I)
ENGLISH_RUN_RE=re.compile(r"(?:\b[A-Za-z][A-Za-z'’-]*\b[\s,;:()\-–—]*){8,}")


def tables(text):
    xs=[(m.start(),m.group(0)) for m in HTML_TABLE_RE.finditer(text)]+[(m.start(),m.group(0)) for m in MD_TABLE_RE.finditer(text)]
    return [x for _,x in sorted(xs)]

def mask_nonprose(text):
    text=re.sub(r"```.*?```|~~~.*?~~~"," ",text,flags=re.S); text=re.sub(r"\$\$.*?\$\$|\\\[.*?\\\]"," ",text,flags=re.S); text=re.sub(r"\$[^$]+\$"," ",text)
    text=URL_RE.sub(' ',text); text=DOI_RE.sub(' ',text); text=IMAGE_RE.sub(' ',text); text=re.sub(r"<[^>]+>"," ",text); return text

def validate_manifest(mp:Path):
    man=json.loads(mp.read_text(encoding='utf-8')); root=mp.parent; err=[]; allids=[]
    for ch in man['chunks']:
        f=root/ch['translated']
        if not f.exists(): err.append(f"Missing translated chunk: {f}"); continue
        ids=BLOCK_ID_RE.findall(f.read_text(encoding='utf-8',errors='replace'))
        if ids!=ch['block_ids']: err.append(f"{f.name}: block IDs changed/reordered")
        allids+=ids
    if allids!=[b['id'] for b in man['blocks']]: err.append('Global block sequence differs from manifest')
    return man,err

def main()->int:
    p=argparse.ArgumentParser(); p.add_argument('--manifest',type=Path,required=True); p.add_argument('--source',type=Path,required=True); p.add_argument('--translated',type=Path,required=True); p.add_argument('--report',type=Path,required=True)
    a=p.parse_args(); src=a.source.read_text(encoding='utf-8',errors='replace'); dst=a.translated.read_text(encoding='utf-8',errors='replace'); man,material=validate_manifest(a.manifest); review=[]
    if TABLE_PLACEHOLDER_RE.search(dst) or IMM_PLACEHOLDER_RE.search(dst): material.append('Unresolved protected placeholder remains in final Markdown')
    si=[m.group(2).strip() for m in IMAGE_RE.finditer(src)]; di=[m.group(2).strip() for m in IMAGE_RE.finditer(dst)]
    if multiset_missing(si,di): material.append('One or more source image references disappeared/changed')
    broken=[]
    for x in di:
        if x.lower().startswith(('http://','https://','data:')): continue
        if not (a.translated.parent/x).exists(): broken.append(x)
    if broken: material.append(f"Broken local image files: {len(broken)}")
    sm=extract_math(src); dm=extract_math(dst)
    if Counter(sm)!=Counter(dm): material.append(f"Math expressions changed: source={len(sm)} translated={len(dm)}")
    su=URL_RE.findall(src)+DOI_RE.findall(src); du=URL_RE.findall(dst)+DOI_RE.findall(dst)
    if Counter(su)!=Counter(du): material.append('URL/DOI multiset differs from audited source')
    if BROKEN_URL_RE.search(dst): material.append('Broken/spaced URL pattern appears in final Markdown')
    st=tables(src); dt=tables(dst)
    if len(st)!=len(dt): material.append(f"Table count changed: source={len(st)} translated={len(dt)}")
    else:
        for i,(s,d) in enumerate(zip(st,dt),1):
            if Counter(numeric_tokens(s))!=Counter(numeric_tokens(d)): material.append(f"Table {i}: numeric tokens changed")
            # Row/column structure guard for Markdown/HTML.
            sr=len(re.findall(r'<tr\b',s,re.I)) or len([x for x in s.splitlines() if x.strip().startswith('|')])
            dr=len(re.findall(r'<tr\b',d,re.I)) or len([x for x in d.splitlines() if x.strip().startswith('|')])
            if sr!=dr: material.append(f"Table {i}: row count changed ({sr}->{dr})")
    sh=len(re.findall(r'(?m)^#{1,6}\s+',src)); dh=len(re.findall(r'(?m)^#{1,6}\s+',dst))
    if sh!=dh: review.append(f"Heading count differs: source={sh}, translated={dh}; inspect outline for false/missing headings")
    if re.search(r'(?m)^#{1,6}\s+(?:总而言之|总之|具体而言|综上)',dst): material.append('A prose transition appears as a Markdown heading; demote it to normal/bold prose')
    prose_s=mask_nonprose(src); prose_d=mask_nonprose(dst); sw=re.findall(r"\b[A-Za-z][A-Za-z'’-]*\b",prose_s); cjk=re.findall(r'[\u3400-\u4dbf\u4e00-\u9fff]',prose_d); ratio=len(cjk)/max(1,len(sw))
    if len(sw)>300 and ratio<0.65: material.append(f"Chinese text appears too short for complete translation: ratio={ratio:.3f}")
    eng=[]
    for n,line in enumerate(dst.splitlines(),1):
        if n>0 and ENGLISH_RUN_RE.search(mask_nonprose(line)): eng.append((n,ENGLISH_RUN_RE.search(mask_nonprose(line)).group(0)[:180]))
    if eng: review.append(f"Long residual English prose lines: {len(eng)}; bibliography/proper metadata may be intentional")
    status='PASS' if not material and not review else ('FAIL' if material else 'REVIEW')
    lines=['# Academic PDF Chinese Validation','', '## Metrics','',f'- Manifest blocks: {len(man["blocks"])}',f'- Source / translated headings: {sh} / {dh}',f'- Source / translated tables: {len(st)} / {len(dt)}',f'- Source / translated images: {len(si)} / {len(di)}',f'- Source / translated LaTeX expressions: {len(sm)} / {len(dm)}',f'- CJK chars per source English word: {ratio:.3f}','', '## Material issues','']
    lines += [f'- {x}' for x in material] if material else ['- None detected.']
    lines += ['', '## Review items',''] + ([f'- {x}' for x in review] if review else ['- None.'])
    if eng:
        lines += ['', '### Residual English samples','']+[f'- L{n}: {x}' for n,x in eng[:20]]
    lines += ['', '## Status','',f'**{status}**','']
    a.report.write_text('\n'.join(lines),encoding='utf-8'); print(a.report.resolve()); print(f"status={status} material={len(material)} review={len(review)}")
    return 2 if material else (1 if review else 0)
if __name__=='__main__': raise SystemExit(main())
