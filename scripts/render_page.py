#!/usr/bin/env python3
from __future__ import annotations
import argparse
from pathlib import Path

def main():
    p=argparse.ArgumentParser();p.add_argument('pdf',type=Path);p.add_argument('page',type=int,help='1-based page');p.add_argument('--output',type=Path);p.add_argument('--dpi',type=int,default=180);a=p.parse_args()
    import fitz
    doc=fitz.open(a.pdf);idx=a.page-1
    if idx<0 or idx>=len(doc):p.error('page out of range')
    out=a.output or Path(f'page-{a.page:04d}.png');pix=doc[idx].get_pixmap(matrix=fitz.Matrix(a.dpi/72,a.dpi/72),alpha=False);pix.save(out);print(out.resolve());return 0
if __name__=='__main__':raise SystemExit(main())
