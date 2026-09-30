#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path

def main():
    p=argparse.ArgumentParser();p.add_argument('table_tasks_dir',type=Path);a=p.parse_args();total=done=0
    for f in sorted(a.table_tasks_dir.glob('T*.json')):
        d=json.loads(f.read_text(encoding='utf-8')); miss=[]
        for c in d.get('cells',[]):
            total+=1
            if c.get('translation','').strip():done+=1
            else:miss.append(f"{c['id']}={c.get('source_for_translation',c['source'])}")
        print(f"{d['id']}: {len(d.get('cells',[]))-len(miss)}/{len(d.get('cells',[]))} translated")
        for x in miss[:20]:print('  MISSING',x)
    print(f"TOTAL {done}/{total}");return 0 if done==total else 1
if __name__=='__main__':raise SystemExit(main())
