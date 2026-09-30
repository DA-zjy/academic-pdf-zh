#!/usr/bin/env python3
from __future__ import annotations

import argparse, json, re, shutil
from pathlib import Path
from _common import BLOCK_ID_RE, strip_block_markers


def render_table(task:dict)->str:
    template=task['template']
    for cell in task['cells']:
        tr=cell.get('translation','').strip()
        if not tr:
            raise ValueError(f"{task['id']} {cell['id']} has no translation. Fill the `translation` field in its table task JSON; for canonical names use the original text explicitly.")
        tr=' '.join(tr.splitlines()).strip()
        for item in cell.get('protected',[]):
            token=f"[[TCP_{item['id']}]]"
            if token not in tr:
                raise ValueError(f"{task['id']} {cell['id']} lost protected table token {token}; translate `source_for_translation` and preserve tokens exactly.")
            tr=tr.replace(token,item['value'])
        if '[[TCP_' in tr:
            raise ValueError(f"{task['id']} {cell['id']} contains an unknown protected table token")
        template=template.replace(f"[[CELL_{cell['id']}]]",tr)
    if '[[CELL_' in template: raise ValueError(f"Unresolved cell placeholder in {task['id']}")
    return template


def main()->int:
    p=argparse.ArgumentParser(description='Assemble translated chunks, restore immutable literals, and deterministically rebuild tables')
    p.add_argument('manifest',type=Path); p.add_argument('--output',type=Path)
    a=p.parse_args(); man=json.loads(a.manifest.read_text(encoding='utf-8')); root=a.manifest.parent
    assembled=[]; ids=[]
    for ch in man['chunks']:
        f=root/ch['translated']
        if not f.exists(): p.error(f"Missing translated chunk: {f}")
        txt=f.read_text(encoding='utf-8',errors='replace'); got=BLOCK_ID_RE.findall(txt)
        if got!=ch['block_ids']: p.error(f"Block IDs changed/reordered in {f.name}: expected {ch['block_ids']}, got {got}")
        ids+=got; assembled.append(strip_block_markers(txt).strip())
    expected=[b['id'] for b in man['blocks']]
    if ids!=expected: p.error('Global block order mismatch')
    final='\n\n'.join(x for x in assembled if x).strip()+'\n'
    # Tables first: their source text was excluded from chunk translation and translated per-cell.
    for tmeta in man.get('tables',[]):
        task=json.loads((root/tmeta['file']).read_text(encoding='utf-8'))
        try: table=render_table(task)
        except ValueError as e: p.error(str(e))
        final=final.replace(f"[[TABLE_{task['id']}]]",table)
    if '[[TABLE_' in final: p.error('Unresolved table placeholder remains')
    # Restore code/math/URL/DOI/numbers exactly as they appeared in audited source.
    for item in man.get('immutables',[]): final=final.replace(f"[[IMM_{item['id']}]]",item['value'])
    if '[[IMM_' in final: p.error('Unresolved immutable placeholder remains')

    if a.output: out=a.output
    else:
        stem=Path(man.get('source_pdf') or 'paper').stem
        out=root.parent/f"{stem}_中文.md"
    out.parent.mkdir(parents=True,exist_ok=True)
    if not final.lstrip().startswith('---'):
        final='---\ncssclasses:\n  - research-paper\n---\n\n'+final
    out.write_text(final,encoding='utf-8')
    assets=man.get('assets_dir')
    if assets and Path(assets).exists():
        dst=out.parent/'images'; dst.mkdir(parents=True,exist_ok=True)
        for src in Path(assets).rglob('*'):
            if not src.is_file(): continue
            try:
                if src.resolve().is_relative_to(dst.resolve()): continue
            except AttributeError: pass
            rel=src.relative_to(Path(assets)); target=dst/rel; target.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,target)
    print(out.resolve()); print(f"chunks={len(man['chunks'])} blocks={len(ids)} tables={len(man.get('tables',[]))}")
    return 0
if __name__=='__main__': raise SystemExit(main())
