#!/usr/bin/env python3
import importlib.util,platform,sys
from _common import find_executable

def main():
    print('Academic PDF Chinese skill doctor v3')
    print(f'python={sys.version.split()[0]} platform={platform.platform()}')
    print(f'mineru={find_executable("mineru") or "MISSING"}')
    print(f'marker_single={find_executable("marker_single") or "optional/not installed"}')
    print(f'pymupdf={"OK" if importlib.util.find_spec("fitz") else "MISSING"}')
    print(f'pymupdf4llm={"OK" if importlib.util.find_spec("pymupdf4llm") else "MISSING"}')
    if platform.system()=='Windows' and sys.version_info[:2]>=(3,13):print('WARNING: prefer Python 3.10-3.12 for MinerU compatibility on Windows.')
    if not importlib.util.find_spec('fitz'):return 2
    if not find_executable('mineru') and not find_executable('marker_single') and not importlib.util.find_spec('pymupdf4llm'):return 2
    return 0
if __name__=='__main__':raise SystemExit(main())
