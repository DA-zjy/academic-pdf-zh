#!/usr/bin/env python3
from __future__ import annotations

import argparse, json, re, shutil
from pathlib import Path
from html import unescape

from _common import (IMAGE_RE, URL_RE, DOI_RE, FENCE_RE, DISPLAY_MATH_RE, INLINE_MATH_RE,
                     INLINE_CODE_RE, NUMBER_RE, sha256_text)

HTML_TABLE_RE=re.compile(r"<table\b.*?</table>",re.I|re.S)
MD_TABLE_RE=re.compile(r"(?m)(?:^\s*\|.*\|\s*$\n){2,}")
CELL_TAG_RE=re.compile(r"(<(?:td|th)\b[^>]*>)(.*?)(</(?:td|th)>)",re.I|re.S)
SEP_CELL_RE=re.compile(r"^\s*:?-{3,}:?\s*$")


def split_md_row(line:str):
    s=line.strip();
    if s.startswith('|'): s=s[1:]
    if s.endswith('|'): s=s[:-1]
    return [x.strip() for x in s.split('|')]

def join_md_row(cells): return '|'+ '|'.join(cells) +'|'

def requires_cell_translation(s:str)->bool:
    plain=re.sub(r"<[^>]+>"," ",s)
    plain=re.sub(r"[*_`]+","",plain).strip()
    if not plain or SEP_CELL_RE.fullmatch(plain): return False
    return bool(re.search(r"[A-Za-z]",plain))

def protect_table_cell_text(text:str):
    protected=[]
    rx=re.compile(r"(?<![\w])[-+]?\d[\d,]*(?:\.\d+)?(?:[eE][-+]?\d+)?%?(?![\w])|[↑↓]")
    def repl(m):
        key=f"P{len(protected)+1:03d}"; protected.append({'id':key,'value':m.group(0)}); return f"[[TCP_{key}]]"
    return rx.sub(repl,text), protected


def lock_tables(text:str, tasks_dir:Path, prev_tasks:dict|None=None):
    """Lock whole tables into per-table cell-translation tasks.

    When a regenerated table is byte-identical to a previous run's table, previously filled
    `translation` fields are restored so re-chunking does not discard completed cell work.
    """
    stats={'tasks_restored':0,'cells_restored':0}
    tasks_dir.mkdir(parents=True,exist_ok=True)
    matches=[(m.start(),m.end(),'html',m.group(0)) for m in HTML_TABLE_RE.finditer(text)]
    # Avoid Markdown matches that overlap an HTML table.
    for m in MD_TABLE_RE.finditer(text):
        if any(a<=m.start()<b for a,b,_,__ in matches): continue
        matches.append((m.start(),m.end(),'markdown',m.group(0)))
    matches.sort(); tasks=[]; edits=[]
    for idx,(start,end,fmt,raw) in enumerate(matches,1):
        tid=f"T{idx:04d}"; cells=[]; template=raw
        if fmt=='html':
            seq=0
            def repl(m):
                nonlocal seq
                inner=m.group(2)
                if not requires_cell_translation(inner): return m.group(0)
                seq+=1; cid=f"C{seq:04d}"; plain=unescape(re.sub(r'<[^>]+>','',inner)).strip(); task_src,prot=protect_table_cell_text(plain); cells.append({'id':cid,'source':plain,'source_for_translation':task_src,'protected':prot,'translation':''})
                return m.group(1)+f"[[CELL_{cid}]]"+m.group(3)
            template=CELL_TAG_RE.sub(repl,raw)
        else:
            out=[]; seq=0
            for line in raw.rstrip('\n').splitlines():
                cs=split_md_row(line)
                # Keep the Markdown alignment separator entirely immutable.
                if cs and all(SEP_CELL_RE.fullmatch(c or '---') for c in cs): out.append(line); continue
                new=[]
                for c in cs:
                    if requires_cell_translation(c):
                        seq+=1; cid=f"C{seq:04d}"; plain=re.sub(r'[*_`]+','',c).strip(); task_src,prot=protect_table_cell_text(plain); cells.append({'id':cid,'source':plain,'source_for_translation':task_src,'protected':prot,'translation':''}); new.append(f"[[CELL_{cid}]]")
                    else: new.append(c)
                out.append(join_md_row(new))
            template='\n'.join(out)
        task={'id':tid,'format':fmt,'template':template,'original':raw,'cells':cells,'numeric_tokens':NUMBER_RE.findall(raw)}
        old=(prev_tasks or {}).get(tid)
        if old and old.get('original')==raw:
            oldmap={c['id']:c.get('translation','') for c in old.get('cells',[])}
            for c in cells:
                tr=oldmap.get(c['id'],'')
                if tr:
                    c['translation']=tr; stats['cells_restored']+=1
            stats['tasks_restored']+=1
        (tasks_dir/f"{tid}.json").write_text(json.dumps(task,ensure_ascii=False,indent=2),encoding='utf-8')
        tasks.append({'id':tid,'file':f"table_tasks/{tid}.json",'cell_count':len(cells),'numeric_tokens':task['numeric_tokens']})
        edits.append((start,end,f"[[TABLE_{tid}]]\n\n"))
    for a,b,r in reversed(edits): text=text[:a]+r+text[b:]
    return text,tasks


def protect_immutables(text:str):
    imm=[]
    def apply(regex):
        nonlocal text
        def repl(m):
            val=m.group(0); iid=f"I{len(imm)+1:06d}"; imm.append({'id':iid,'value':val}); return f"[[IMM_{iid}]]"
        text=regex.sub(repl,text)
    # Protect large/specific spans first, then literals and standalone numbers.
    for rx in (FENCE_RE, DISPLAY_MATH_RE, INLINE_MATH_RE, INLINE_CODE_RE, URL_RE, DOI_RE, NUMBER_RE): apply(rx)
    return text,imm


def split_blocks(text:str):
    lines=text.splitlines(); blocks=[]; buf=[]; details=0
    def flush():
        nonlocal buf
        if buf and any(x.strip() for x in buf): blocks.append('\n'.join(buf).strip('\n'))
        buf=[]
    for line in lines:
        s=line.strip()
        if re.search(r'<details\b',s,re.I): details+=1
        if re.search(r'</details>',s,re.I): details=max(0,details-1)
        if not s and details==0: flush(); continue
        if re.match(r'^#{1,6}\s+',s) and buf: flush()
        buf.append(line)
        if re.match(r'^#{1,6}\s+',s) and details==0: flush()
    flush(); return blocks


def collect_previous_work(output_dir:Path)->dict:
    """Collect completed work across re-chunking: translated chunks and filled table tasks.

    Re-runs are common (source repairs, chunk-size tweaks). Translated chunks are copied back
    as-is; table-task cell translations are restored only where the underlying table is
    byte-identical, so a changed table is forced back into translation.
    """
    trd=output_dir/'translated'; taskd=output_dir/'table_tasks'
    data={'translations':{}, 'tasks':{}}
    if trd.exists():
        data['translations']={f.name:f.read_text(encoding='utf-8',errors='replace') for f in trd.glob('*.md')}
    if taskd.exists():
        for f in taskd.glob('T*.json'):
            try: data['tasks'][f.stem]=json.loads(f.read_text(encoding='utf-8'))
            except Exception: pass
    return data


def main()->int:
    p=argparse.ArgumentParser(description='Create safe translation chunks with immutable literals and locked tables')
    p.add_argument('input',type=Path); p.add_argument('--output-dir',type=Path,required=True); p.add_argument('--max-chars',type=int,default=9000)
    p.add_argument('--assets-dir',type=Path); p.add_argument('--pdf',type=Path)
    a=p.parse_args(); text=a.input.read_text(encoding='utf-8',errors='replace')
    prev=collect_previous_work(a.output_dir)
    if a.output_dir.exists(): shutil.rmtree(a.output_dir)
    srcd=a.output_dir/'source'; trd=a.output_dir/'translated'; taskd=a.output_dir/'table_tasks'
    srcd.mkdir(parents=True); trd.mkdir(); taskd.mkdir()
    for name,txt in prev['translations'].items(): (trd/name).write_text(txt,encoding='utf-8')
    restored_chunks=len(prev['translations']); restored_tasks=0; restored_cells=0
    locked,tables=lock_tables(text,taskd,prev['tasks']); protected,immutables=protect_immutables(locked)
    raw_blocks=split_blocks(protected)
    blocks=[]; marked=[]
    for i,body in enumerate(raw_blocks,1):
        bid=f"B{i:06d}"; marked.append(f"<!-- block:{bid} -->\n{body.strip()}")
        blocks.append({'id':bid,'chars':len(body),'sha256':sha256_text(body),'images':[m.group(2).strip() for m in IMAGE_RE.finditer(body)]})
    chunks=[]; cur=[]; ids=[]; nchar=0
    def flush():
        nonlocal cur,ids,nchar
        if not cur:return
        n=len(chunks)+1; name=f"{n:04d}.md"; payload='\n\n'.join(cur).strip()+'\n'; (srcd/name).write_text(payload,encoding='utf-8')
        chunks.append({'index':n,'source':f"source/{name}",'translated':f"translated/{name}",'block_ids':ids.copy(),'chars':len(payload),'sha256':sha256_text(payload)})
        cur=[];ids=[];nchar=0
    for body,meta in zip(marked,blocks):
        size=len(body)+2
        if cur and nchar+size>a.max_chars: flush()
        cur.append(body);ids.append(meta['id']);nchar+=size
    flush()
    manifest={'version':3,'source_clean':str(a.input.resolve()),'source_clean_sha256':sha256_text(text),'source_pdf':str(a.pdf.resolve()) if a.pdf else None,
              'assets_dir':str(a.assets_dir.resolve()) if a.assets_dir else None,'blocks':blocks,'chunks':chunks,'immutables':immutables,'tables':tables}
    mp=a.output_dir/'manifest.json'; mp.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print(mp.resolve()); print(f"blocks={len(blocks)} chunks={len(chunks)} immutables={len(immutables)} tables={len(tables)}")
    print(f"restored: translated_chunks={restored_chunks} table_tasks={restored_tasks} table_cells={restored_cells}")
    if restored_chunks and restored_chunks!=len(chunks): print('WARNING: translated chunk count differs from current chunking; stale chunks must be re-translated.')
    return 0
if __name__=='__main__': raise SystemExit(main())
