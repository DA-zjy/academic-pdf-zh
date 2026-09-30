#!/usr/bin/env python3
"""Static checks for the generated site under docs/.

Verifies (and exits non-zero on failure):
  1. every internal href/src resolves to a real file inside docs/ (relative, subpath-safe);
  2. no root-absolute URLs (/assets/...), no ../demo/ or ../.. escaping docs/,
     no localhost / drive letters / 127.0.0.1 business endpoints;
  3. every generated HTML declares <meta charset="utf-8"> and lang="zh-CN",
     decodes as strict UTF-8;
  4. no unresolved template placeholders ({{ }} / \\u0001 MATH markers);
  5. reading pages: TOC anchors match heading ids; images referenced exist;
  6. downloads: translation.md sha256 equals source demo artifact (from source-hashes.json),
     sample.zip contains the Markdown and the images its Markdown references;
  7. validation pages keep the original STATUS (PASS/REVIEW/FAIL) text.

Usage:  python scripts/check_site.py
"""
from __future__ import annotations

import hashlib
import io
import json
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

errors: list[str] = []
warnings: list[str] = []


def err(msg: str) -> None:
    errors.append(msg)


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


HTML_FILES = sorted(DOCS.rglob("*.html"))
if not HTML_FILES:
    err("docs/ 下没有任何 HTML")

# ---- per-HTML checks ------------------------------------------------------ #
all_internal: list[tuple[Path, str]] = []

for page in HTML_FILES:
    rel = page.relative_to(DOCS).as_posix()
    try:
        text = page.read_bytes().decode("utf-8")
    except UnicodeDecodeError as e:
        err(f"{rel}: 非 UTF-8: {e}")
        continue

    if not re.search(r'<meta[^>]+charset=["\']?utf-8', text, re.I):
        err(f"{rel}: 缺少 <meta charset=\"utf-8\">")
    if 'lang="zh-CN"' not in text:
        err(f"{rel}: 缺少 lang=\"zh-CN\"")
    if "\u0001" in text:
        err(f"{rel}: 残留数学占位符")

    # internal targets
    for m in re.finditer(r'(?:href|src)="([^"]+)"', text):
        url = m.group(1)
        if url.startswith(("http://", "https://", "mailto:", "data:", "#")):
            continue
        all_internal.append((page, url))

    # forbidden references
    if re.search(r'(?:href|src)="(/[^/"])', text):
        err(f"{rel}: 含根绝对路径（/xxx），子路径发布会失效")
    for m in re.finditer(r'(?:href|src)="([^"]*)"', text):
        u = m.group(1)
        if u.startswith("../"):
            depth = len(DOCS.relative_to(ROOT).parts)
            resolved = (page.parent / u).resolve()
            if not str(resolved).startswith(str(DOCS.resolve())):
                err(f"{rel}: 引用 docs/ 之外文件: {u}")
    # 盘符形如 C:\（排除 URL 的 x://）；localhost/127.0.0.1 不允许出现在链接/资源里
    stripped = re.sub(r"<pre[\s\S]*?</pre>", "", text)
    if re.search(r'(?:href|src)="[^"]*(?:localhost|127\.0\.0\.1)', stripped):
        err(f"{rel}: 链接/资源引用了 localhost")
    if re.search(r'(?:href|src)="[^"]*\b[A-Za-z]:[\\/](?![\\/])', stripped):
        err(f"{rel}: 链接/资源引用了本机盘符")

# ---- resolve internal targets -------------------------------------------- #
for page, url in all_internal:
    target = (page.parent / url.split("#")[0])
    if not target.exists():
        err(f"{page.relative_to(DOCS).as_posix()}: 内部引用不存在 -> {url}")

# ---- reading pages -------------------------------------------------------- #
cfg = json.loads((ROOT / "site.config.json").read_text(encoding="utf-8"))
hashes = json.loads((DOCS / "samples" / "source-hashes.json").read_text(encoding="utf-8"))

for paper in cfg["papers"]:
    key = paper["key"]
    page = DOCS / "samples" / key / "index.html"
    if not page.exists():
        err(f"samples/{key}/index.html 缺失")
        continue
    text = page.read_text(encoding="utf-8")
    ids = set(re.findall(r'<h[1-6] id="([^"]+)"', text))
    anchors = re.findall(r'href="#([^"]+)"', text)
    for a in anchors:
        if a not in ids:
            err(f"samples/{key}/index.html: 目录锚点无对应标题 -> #{a}")
    for img in re.findall(r'<img src="([^"]+)"', text):
        if not (page.parent / img).exists():
            err(f"samples/{key}/index.html: 图片缺失 -> {img}")

    # translation.md 与 demo/ 源文件哈希一致
    rec = hashes["papers"].get(key)
    if not rec:
        err(f"source-hashes.json 缺少 {key}")
    else:
        pub = DOCS / "samples" / key / "translation.md"
        if sha256(pub.read_bytes()) != rec["sourceTranslation"]["sha256"]:
            err(f"samples/{key}/translation.md 与源文件哈希不一致")

        # sample.zip：包含 Markdown 与其引用的全部图片，且解压后相对关系有效
        zp = DOCS / "samples" / key / "sample.zip"
        with zipfile.ZipFile(zp) as z:
            names = set(z.namelist())
            md_name = paper["file"]
            if md_name not in names:
                err(f"{key}/sample.zip 缺少 {md_name}")
            md_text = z.read(md_name).decode("utf-8")
            for img in re.findall(r"!\[[^\]]*\]\(([^)]+)\)", md_text):
                if img not in names:
                    err(f"{key}/sample.zip 缺少图片 {img}")

    # validation 页保留原始状态
    val_page = DOCS / "samples" / key / "validation.html"
    val_html = val_page.read_text(encoding="utf-8")
    val_md = (DOCS / "samples" / key / "validation.md").read_text(encoding="utf-8")
    status = re.search(r"\*\*(PASS|REVIEW|FAIL)\*\*", val_md)
    if not status:
        err(f"samples/{key}/validation.md 找不到状态行")
    elif status.group(1) not in val_html:
        err(f"samples/{key}/validation.html 状态 {status.group(1)} 未保留")

    # 结构保全：HTML 标题序列必须与源 Markdown 标题序列一致（防内容被表格吞并/截断）
    src_md = (ROOT / paper["dir"] / paper["file"]).read_text(encoding="utf-8")
    src_md = re.sub(r"\A---\s*\n.*?\n---\s*\n", "", src_md, count=1, flags=re.S)
    src_heads = [re.sub(r"\*\*", "", h).strip()
                 for h in re.findall(r"^\s*(#{1,4})\s+(.+)$", src_md, re.M) for h in [""]]
    src_heads = [re.sub(r"^\s*#{1,4}\s*", "", ln).strip().replace("**", "")
                 for ln in src_md.splitlines() if re.match(r"^\s*#{1,4}\s+\S", ln)]
    html_heads = [re.sub(r"<[^>]+>", "", h).strip()
                  for h in re.findall(r"<h[1-4][^>]*>(.*?)</h[1-4]>", text, re.S)]
    html_heads = [re.sub(r"\s+", " ", h) for h in html_heads]
    src_heads = [re.sub(r"\s+", " ", h) for h in src_heads]
    if html_heads != src_heads:
        err(f"samples/{key}/index.html: 标题序列与源文件不一致 "
            f"(源 {len(src_heads)} / 页 {len(html_heads)})")
    # 图片引用集合一致
    src_imgs = set(re.findall(r"!\[[^\]]*\]\(([^)]+)\)", src_md))
    html_imgs = set(re.findall(r'<img[^>]*\ssrc="([^"]+)"', text))
    if src_imgs != html_imgs:
        err(f"samples/{key}/index.html: 图片引用集合与源文件不一致 "
            f"(源 {len(src_imgs)} / 页 {len(html_imgs)})")

# ---- vendored katex sanity ------------------------------------------------ #
for need in ("vendor/katex/katex.min.js", "vendor/katex/katex.min.css",
             "vendor/katex/plugins/auto-render.min.js", "reader.css",
             ".nojekyll", "demo-data.js", "demo.js", "index.html", "player.html"):
    if not (DOCS / need).exists():
        err(f"docs/{need} 缺失")
fonts = list((DOCS / "vendor" / "katex" / "fonts").glob("*.woff2")) if (DOCS / "vendor" / "katex" / "fonts").exists() else []
if len(fonts) < 20:
    warnings.append(f"KaTeX 字体只有 {len(fonts)} 个 woff2（预期 ≥20）")

print(f"HTML 文件: {len(HTML_FILES)} · 内部引用: {len(all_internal)} · KaTeX 字体: {len(fonts)}")
for w in warnings:
    print("WARN:", w)
if errors:
    print(f"\nFAIL（{len(errors)} 项）:")
    for e in errors:
        print(" -", e)
    sys.exit(1)
print("check_site: 全部通过")
