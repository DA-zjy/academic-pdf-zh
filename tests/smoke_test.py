#!/usr/bin/env python3
"""Minimal regression test for immutable literals and table reconstruction."""
from __future__ import annotations
import json, subprocess, sys, tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
S=ROOT/'scripts'

def run(*args): subprocess.run([sys.executable,*map(str,args)],check=True)

def main():
    with tempfile.TemporaryDirectory() as td:
        d=Path(td); src=d/'source.md'
        src.write_text('# Paper\n\nWe test 10 cases with $x_1=2$ at https://example.com.\n\n|Group|Method|Score|\n|---|---|---:|\n|2 Parts (15)|Real2Code|2.47|\n|3 Parts (9)|Ditto|3.63|\n',encoding='utf-8')
        run(S/'chunk_markdown.py',src,'--output-dir',d/'chunks')
        chunk=d/'chunks/source/0001.md'; text=chunk.read_text().replace('# Paper','# 论文').replace('We test','我们测试').replace('cases with','个样本，条件为').replace(' at ','，地址为 ')
        (d/'chunks/translated/0001.md').write_text(text,encoding='utf-8')
        task=d/'chunks/table_tasks/T0001.json'; obj=json.loads(task.read_text())
        for c in obj['cells']:
            st=c.get('source_for_translation',c['source'])
            c['translation']={'Group':'分组','Method':'方法','Score':'分数','Real2Code':'Real2Code','Ditto':'Ditto'}.get(st,st.replace('Parts','个部件'))
        task.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
        out=d/'out.md';run(S/'assemble_markdown.py',d/'chunks/manifest.json','--output',out)
        final=out.read_text(encoding='utf-8')
        assert '2.47' in final and '3.63' in final and '72.47' not in final
        assert '$x_1=2$' in final and 'https://example.com' in final
    print('smoke test PASS')
    return 0
if __name__=='__main__':raise SystemExit(main())
