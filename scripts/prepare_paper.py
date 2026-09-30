#!/usr/bin/env python3
from __future__ import annotations

import argparse, importlib.util, json, re, shutil, subprocess, sys
from pathlib import Path
from _common import IMAGE_RE, clean_link_target, copy_referenced_images, find_executable, infer_project_root, page_rect_from_bbox
from normalize_markdown import normalize


def run(cmd:list[str],cwd:Path|None=None): print('+',' '.join(str(x) for x in cmd)); subprocess.run(cmd,cwd=cwd,check=True)
def find_best_markdown(root:Path):
    xs=[p for p in root.rglob('*.md') if p.is_file()]
    if not xs: raise RuntimeError(f'Parser produced no Markdown under {root}')
    return max(xs,key=lambda p:p.stat().st_size)
def find_middle_json(root:Path,md:Path):
    xs=list(md.parent.glob('*middle.json'))+list(md.parent.glob('*_middle.json'))+list(root.rglob('*middle.json'))+list(root.rglob('*_middle.json'))
    return max(xs,key=lambda p:p.stat().st_size) if xs else None

def run_mineru(pdf,raw,backend,method,effort):
    exe=find_executable('mineru')
    if not exe: raise RuntimeError('MinerU executable not found. Run install script.')
    out=raw/'mineru';out.mkdir(parents=True,exist_ok=True)
    cmd=[exe,'-p',str(pdf),'-o',str(out),'-b',backend,'-m',method,'-f','true','-t','true']
    if backend=='hybrid-engine': cmd+=['--effort',effort]
    run(cmd); md=find_best_markdown(out); return md,find_middle_json(out,md)
def run_marker(pdf,raw):
    exe=find_executable('marker_single')
    if not exe: raise RuntimeError('marker_single not found; Marker is optional.')
    out=raw/'marker';out.mkdir(parents=True,exist_ok=True);run([exe,str(pdf),'--output_dir',str(out)]);return find_best_markdown(out),None
def run_pymupdf4llm(pdf,raw):
    if not importlib.util.find_spec('pymupdf4llm'): raise RuntimeError('pymupdf4llm not installed.')
    import pymupdf4llm
    out=raw/'pymupdf4llm';imgs=out/'images';imgs.mkdir(parents=True,exist_ok=True)
    kwargs={'write_images':True,'image_path':str(imgs),'show_progress':True,'header':False,'footer':False,'use_ocr':True}
    while True:
        try: md=pymupdf4llm.to_markdown(str(pdf),**kwargs);break
        except TypeError:
            for k in ('use_ocr','footer','header','show_progress'):
                if k in kwargs: kwargs.pop(k);break
            else: raise
    path=out/'document.md';path.write_text(md,encoding='utf-8');return path,None

def iter_image_paths(obj):
    out=[]
    if isinstance(obj,dict):
        if isinstance(obj.get('image_path'),str): out.append(obj['image_path'])
        for v in obj.values(): out+=iter_image_paths(v)
    elif isinstance(obj,list):
        for v in obj: out+=iter_image_paths(v)
    return out

def figure_body_bbox(block):
    for child in block.get('blocks') or []:
        if isinstance(child,dict) and child.get('type') in {'image_body','chart_body'}: return child.get('bbox_fs') or child.get('bbox')
    return block.get('bbox_fs') or block.get('bbox')
def crop_figure(pdf,page_idx,bbox,page_size,out,dpi=190):
    try:
        import fitz
        doc=fitz.open(pdf);page=doc[page_idx];rect=page_rect_from_bbox(page,bbox,page_size)
        if rect is None:return False
        rect=fitz.Rect(max(0,rect.x0-3),max(0,rect.y0-3),min(page.rect.width,rect.x1+3),min(page.rect.height,rect.y1+3))
        if rect.width<12 or rect.height<12:return False
        pix=page.get_pixmap(matrix=fitz.Matrix(dpi/72,dpi/72),clip=rect,alpha=False);out.parent.mkdir(parents=True,exist_ok=True);pix.save(out);return True
    except Exception as e: print(f'WARNING figure crop failed p{page_idx+1}: {e}');return False

def rebuild_figures(md,middle,pdf,crop_dir):
    stats={'figure_blocks':0,'figure_crops':0,'fragment_refs_merged':0}
    if not middle or not middle.exists():return md,stats
    try:data=json.loads(middle.read_text(encoding='utf-8',errors='replace'))
    except Exception:return md,stats
    pages=data.get('pdf_info') if isinstance(data,dict) else None
    if not isinstance(pages,list):return md,stats
    cur=md
    for pos,p in enumerate(pages):
        if not isinstance(p,dict):continue
        page_idx=int(p.get('page_idx',pos));ps=p.get('page_size');fig_no=0
        for b in p.get('para_blocks') or []:
            if not isinstance(b,dict) or b.get('type') not in {'image','chart'}:continue
            stats['figure_blocks']+=1;fig_no+=1;basenames={Path(x.replace('\\','/')).name for x in iter_image_paths(b) if x}
            if not basenames:continue
            matches=[]
            for m in IMAGE_RE.finditer(cur):
                if Path(clean_link_target(m.group(2)).replace('\\','/')).name in basenames:matches.append(m)
            if not matches:continue
            cp=crop_dir/f'fig-p{page_idx+1:04d}-{fig_no:02d}.png'
            if not crop_figure(pdf,page_idx,figure_body_bbox(b),ps,cp):continue
            repl=f'![]({cp.resolve().as_posix()})'; edits=[(m.start(),m.end(),repl if i==0 else '') for i,m in enumerate(matches)]
            for a,z,r in reversed(edits):cur=cur[:a]+r+cur[z:]
            stats['figure_crops']+=1;stats['fragment_refs_merged']+=max(0,len(matches)-1)
    return cur,stats

def parse_pages_spec(spec:str)->list[int]:
    """Parse a 1-based page spec like '1-3,8' into 0-based indices."""
    pages=[]
    for part in spec.split(','):
        part=part.strip()
        if not part:continue
        if '-' in part:
            lo,hi=part.split('-',1);pages+=list(range(int(lo)-1,int(hi)))
        else:pages.append(int(part)-1)
    return sorted({n for n in pages if n>=0})

def build_page_subset(pdf:Path,pages:list[int],out:Path)->Path:
    import fitz
    doc=fitz.open(pdf);sub=fitz.open()
    for n in pages:
        if n>=doc.page_count:p.error(f'--pages index {n+1} out of range (PDF has {doc.page_count} pages)')
        sub.insert_pdf(doc,from_page=n,to_page=n)
    sub.save(str(out));sub.close();doc.close()
    return out

def main()->int:
    p=argparse.ArgumentParser(description='Parse and structurally audit an academic PDF before Codex translation')
    p.add_argument('input',type=Path);p.add_argument('--project-root',type=Path);p.add_argument('--work-dir',type=Path)
    p.add_argument('--pages',type=str,default=None,help='1-based page subset, e.g. "1-3,8"; runs a pilot parse on a page-extracted copy of the PDF')
    p.add_argument('--parser',choices=['auto','mineru','marker','pymupdf4llm'],default='auto');p.add_argument('--backend',choices=['pipeline','hybrid-engine'],default='pipeline');p.add_argument('--effort',choices=['medium','high'],default='high');p.add_argument('--method',choices=['auto','txt','ocr'],default='auto')
    a=p.parse_args(); pdf=a.input.resolve(); original_pdf=pdf
    if not pdf.exists() or pdf.suffix.lower()!='.pdf':p.error(f'Input PDF not found: {pdf}')
    root=(a.project_root.resolve() if a.project_root else infer_project_root(Path.cwd()))
    work=(a.work_dir if a.work_dir else Path('work')/pdf.stem)
    if not work.is_absolute():work=(root/work).resolve()
    source=work/'source';raw=source/'parser_raw';images=source/'images';crops=source/'figure_crops';audit=source/'audit'
    if source.exists(): shutil.rmtree(source)
    for d in (raw,images,crops,audit):d.mkdir(parents=True,exist_ok=True)
    pages=parse_pages_spec(a.pages) if a.pages else None
    if pages: pdf=build_page_subset(pdf,pages,raw/'_pages_subset.pdf')
    parser=a.parser
    if parser=='auto': parser='mineru' if find_executable('mineru') else ('marker' if find_executable('marker_single') else 'pymupdf4llm')
    if parser=='mineru':mdp,middle=run_mineru(pdf,raw,a.backend,a.method,a.effort)
    elif parser=='marker':mdp,middle=run_marker(pdf,raw)
    else:mdp,middle=run_pymupdf4llm(pdf,raw)
    rawmd=mdp.read_text(encoding='utf-8',errors='replace');fst={'figure_blocks':0,'figure_crops':0,'fragment_refs_merged':0}
    if parser=='mineru':rawmd,fst=rebuild_figures(rawmd,middle,pdf,crops)
    portable,map_,missing=copy_referenced_images(rawmd,mdp.parent,images);(source/'source_raw.md').write_text(portable,encoding='utf-8')
    clean,nstats=normalize(portable);cleanp=source/'source_clean.md';cleanp.write_text(clean,encoding='utf-8')
    middle_copy=None
    if middle: middle_copy=source/'middle.json';shutil.copy2(middle,middle_copy)
    meta={'version':4,'input_pdf':str(original_pdf),'pages_selected':[n+1 for n in pages] if pages else None,'parse_input':str(pdf) if pages else None,'project_root':str(root),'work_dir':str(work),'parser':parser,'backend':a.backend if parser=='mineru' else None,'method':a.method if parser=='mineru' else None,'image_assets_copied':len(map_),'missing_image_assets':missing,**fst,**nstats}
    (source/'parser-meta.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
    glossary=work/'glossary.md'
    if not glossary.exists():glossary.write_text('# Translation Glossary\n\n<!-- English -> 中文（acronym if needed） -->\n',encoding='utf-8')
    audit_script=Path(__file__).with_name('audit_source.py');report=work/'source-audit.md'
    cmd=[sys.executable,str(audit_script),'--source',str(cleanp),'--pdf',str(pdf),'--audit-dir',str(audit),'--report',str(report)]
    if middle_copy:cmd+=['--middle-json',str(middle_copy)]
    rc=subprocess.run(cmd).returncode
    print(f'prepared={work}');print(f'parser={parser} figures={fst["figure_crops"]} fragments_merged={fst["fragment_refs_merged"]}')
    print('NEXT: inspect source-audit.md and audit crops. Fix source/source_clean.md until source audit has no material issues; visually resolve math/table review items. Then run chunk_markdown.py.')
    return 0 if rc in (0,1,2) else rc
if __name__=='__main__':raise SystemExit(main())
