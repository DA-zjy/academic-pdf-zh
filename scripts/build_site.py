#!/usr/bin/env python3
"""Generate the standalone reading site under docs/ from the real demo artifacts.

What it creates (and ONLY what it creates — existing files in docs/ are untouched):
  docs/samples/<key>/index.html        full reading page rendered from demo/<key>/<key>_中文.md
  docs/samples/<key>/validation.html   reading page for the existing validation.md (metrics untouched)
  docs/samples/<key>/validation.md     verbatim copy of the existing report
  docs/samples/<key>/translation.md    verbatim copy of the translated Markdown
  docs/samples/<key>/images/…          verbatim copy of the sample images
  docs/samples/<key>/sample.zip        <key>_中文.md + images/ (relative layout preserved)
  docs/samples/index.html              small directory of the three samples
  docs/samples/source-hashes.json      sha256 mapping: source artifact <-> public copy

Inputs: site.config.json, demo/<key>/<key>_中文.md, demo/<key>/validation.md, demo/<key>/images/.
The build does NOT depend on demo/.build manifest.json (that is only needed by
build_demo_data.py for the animation data, which fails loudly when it is missing).

Markdown parsing uses the vendored pure-Python `markdown` package (scripts/_site_libs),
version pinned in requirements-site.txt. Math is protected before parsing and restored
afterwards; rendering to typeset math happens in the browser via the vendored KaTeX
0.16.11 + auto-render (delimiters configured, errors logged, source kept on failure).
"""
from __future__ import annotations

import html
import json
import re
import shutil
import sys
import zipfile
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "_site_libs"))

import markdown  # noqa: E402  (vendored, see scripts/_site_libs)
from markdown.extensions.toc import slugify_unicode  # noqa: E402

BUILD_TIME = datetime.now(timezone.utc).strftime("%Y-%m-%d")

# --------------------------------------------------------------------------- #
# math protection
# --------------------------------------------------------------------------- #

MATH_PLACE = "\u0001MATH{}\u0001"

DISPLAY_PATTERNS = [
    re.compile(r"\$\$.+?\$\$", re.S),          # $$...$$
    re.compile(r"\\\[.+?\\\]", re.S),          # \[...\]
]
INLINE_PATTERNS = [
    re.compile(r"(?<!\\)\$(?!\s)((?:\\.|[^$\n\\])+?)(?<!\\)\$"),   # $...$ (no newline)
    re.compile(r"\\\((.+?)\\\)", re.S),        # \(...\)
]


def protect_math(text: str) -> tuple[str, list[str]]:
    """Replace math spans with placeholders so Markdown parsing cannot mangle
    backslashes / underscores / pipes inside them."""
    store: list[str] = []

    def keep(m: re.Match) -> str:
        store.append(m.group(0))
        return MATH_PLACE.format(len(store) - 1)

    for pat in DISPLAY_PATTERNS + INLINE_PATTERNS:
        text = pat.sub(keep, text)
    return text, store


def restore_math(html_text: str, store: list[str]) -> str:
    def put(m: re.Match) -> str:
        return html.escape(store[int(m.group(1))], quote=False)
    return re.sub(MATH_PLACE.format(r"(\d+)"), put, html_text)


# --------------------------------------------------------------------------- #
# HTML sanitation (allowlist) — content is our own generated Markdown, but the
# reader must not execute script/event-handler payload or keep unknown raw tags.
# --------------------------------------------------------------------------- #

ALLOWED_TAGS = {
    "h1", "h2", "h3", "h4", "h5", "h6", "p", "br", "hr",
    "ul", "ol", "li", "blockquote", "strong", "em", "b", "i", "del", "s",
    "code", "pre", "a", "img", "sup", "sub", "span",
    "table", "thead", "tbody", "tfoot", "tr", "th", "td", "caption", "colgroup", "col",
    "details", "summary", "figure", "figcaption",
}
VOID_TAGS = {"br", "hr", "img", "col"}
ALLOWED_ATTRS = {
    "a": {"href", "title"},
    "img": {"src", "alt", "title", "width", "height", "loading"},
    "td": {"colspan", "rowspan", "align"},
    "th": {"colspan", "rowspan", "align"},
    "ol": {"start", "type"},
    "details": {"open"},
}
# 目录锚点：标题的 id 属性必须保留
for _h in ("h1", "h2", "h3", "h4", "h5", "h6"):
    ALLOWED_ATTRS[_h] = {"id"}
# literal template tags appearing inside translated prose/table cells
PRE_ESCAPE_TAGS = {"think"}


class Sanitizer(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.out: list[str] = []
        self.open_stack: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag not in ALLOWED_TAGS:
            return
        keep = ALLOWED_ATTRS.get(tag, set())
        parts = [f"<{tag}"]
        for name, value in attrs:
            if name not in keep:
                continue
            if value is None:
                parts.append(f" {name}")
            else:
                v = value.strip()
                if (name in {"href", "src"}) and (v.lower().startswith("javascript:") or v.lower().startswith("data:")):
                    continue
                parts.append(f' {name}="{html.escape(v, quote=True)}"')
        parts.append(">") if tag in VOID_TAGS else parts.append(">")
        self.out.append("".join(parts))
        if tag not in VOID_TAGS:
            self.open_stack.append(tag)

    def handle_startendtag(self, tag, attrs) -> None:
        if tag in VOID_TAGS:
            self.handle_starttag(tag, attrs)
        elif tag in ALLOWED_TAGS:
            keep = ALLOWED_ATTRS.get(tag, set())
            parts = [f"<{tag}"]
            for name, value in attrs:
                if name in keep:
                    parts.append(f' {name}="{html.escape((value or "").strip(), quote=True)}"')
            parts.append("></%s>" % tag)
            self.out.append("".join(parts))

    def handle_endtag(self, tag: str) -> None:
        if tag not in ALLOWED_TAGS or tag in VOID_TAGS:
            return
        if tag in self.open_stack:
            # close intermediate unclosed tags to keep output well-formed
            while self.open_stack:
                top = self.open_stack.pop()
                self.out.append(f"</{top}>")
                if top == tag:
                    break

    def handle_data(self, data: str) -> None:
        self.out.append(html.escape(data, quote=False))

    def handle_entityref(self, name: str) -> None:
        self.out.append(f"&{name};")

    def handle_charref(self, name: str) -> None:
        self.out.append(f"&#{name};")

    def handle_comment(self, data: str) -> None:
        pass  # drop comments

    def close(self) -> None:
        super().close()
        while self.open_stack:
            self.out.append(f"</{self.open_stack.pop()}>")


def sanitize(fragment: str) -> str:
    s = Sanitizer()
    s.feed(fragment)
    s.close()
    return "".join(s.out)


def pre_escape_literal_tags(text: str) -> str:
    def sub(m: re.Match) -> str:
        name = m.group(2).lower()
        if name in PRE_ESCAPE_TAGS:
            return f"&lt;{m.group(1)}{m.group(2)}&gt;"
        return m.group(0)

    return re.sub(r"<(/?)([a-zA-Z][a-zA-Z0-9-]*)", sub, text)


# --------------------------------------------------------------------------- #
# markdown rendering
# --------------------------------------------------------------------------- #

def normalize_table_blanks(text: str) -> tuple[str, int]:
    """显示层修补：源 Markdown 里表格块与其他块之间缺空行时，python-markdown
    会把后续行吞进表格（作为单格行）。在不改动 demo/ 源文件的前提下，构建时在
    「表格行 ↔ 非表格行」交界补空行，仅影响网页渲染。"""
    lines = text.split("\n")
    out: list[str] = []
    fixups = 0
    for i, ln in enumerate(lines):
        out.append(ln)
        s, nxt = ln.strip(), (lines[i + 1].strip() if i + 1 < len(lines) else "")
        if s.startswith("|") and nxt and not nxt.startswith("|"):
            out.append("")
            fixups += 1
        elif nxt.startswith("|---") and s and not s.startswith("|"):
            out.append("")
            fixups += 1
    return "\n".join(out), fixups


def render_markdown(text: str) -> tuple[str, list[dict]]:
    text, store = protect_math(text)
    text, fixups = normalize_table_blanks(text)
    if fixups:
        print(f"  - 表格空行修补 {fixups} 处（仅渲染层，源文件未改）")
    text = pre_escape_literal_tags(text)
    md = markdown.Markdown(
        # vendored 复制没有 dist-info，字符串短名（"tables"）依赖 entry points 会失败，
        # 因此使用完整模块路径。
        extensions=["markdown.extensions.tables",
                    "markdown.extensions.fenced_code",
                    "markdown.extensions.sane_lists",
                    "markdown.extensions.toc"],
        extension_configs={"toc": {"slugify": slugify_unicode,
                                   "permalink": False, "toc_depth": "2-4"}},
        output_format="html5",
    )
    body = md.convert(text)
    toc_tokens = md.toc_tokens
    md.reset()
    body = sanitize(body)
    body = restore_math(body, store)
    # 宽表格局部横向滚动，不挤压整页
    body = re.sub(r"(<table>.*?</table>)", r'<div class="tbl-scroll">\1</div>', body, flags=re.S)
    return body, toc_tokens


def toc_html(tokens: list[dict]) -> str:
    def walk(items) -> str:
        if not items:
            return ""
        out = ["<ul>"]
        for it in items:
            out.append(f'<li><a href="#{it["id"]}">{html.escape(it["name"], quote=False)}</a>')
            if it.get("children"):
                out.append(walk(it["children"]))
            out.append("</li>")
        out.append("</ul>")
        return "".join(out)

    return walk(tokens)


# --------------------------------------------------------------------------- #
# page templates
# --------------------------------------------------------------------------- #

def katex_bootstrap(depth: int) -> str:
    up = "../" * depth
    return (
        f'<link rel="stylesheet" href="{up}vendor/katex/katex.min.css">\n'
        f'<script defer src="{up}vendor/katex/katex.min.js"></script>\n'
        f'<script defer src="{up}vendor/katex/plugins/auto-render.min.js"></script>\n'
        f"<script>\n"
        "document.addEventListener('DOMContentLoaded', function () {\n"
        "  var el = document.getElementById('article');\n"
        "  if (!el || !window.renderMathInElement) return;\n"
        "  var errs = [];\n"
        "  renderMathInElement(el, {\n"
        "    delimiters: [\n"
        "      {left: '$$', right: '$$', display: true},\n"
        "      {left: '\\\\[', right: '\\\\]', display: true},\n"
        "      {left: '\\\\(', right: '\\\\)', display: false},\n"
        "      {left: '$', right: '$', display: false}\n"
        "    ],\n"
        "    ignoredTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code'],\n"
        "    throwOnError: false,\n"
        "    strict: 'ignore',\n"
        "    errorCallback: function (msg) { errs.push(String(msg && msg.message || msg));"
        " console.warn('KaTeX 无法渲染，保留原文：', msg); }\n"
        "  });\n"
        "  if (errs.length) { el.dataset.katexErrors = errs.length;"
        " console.warn('KaTeX 渲染失败条数：', errs.length); }\n"
        "});\n"
        "</script>\n"
    )


READER_PAGE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · {site_title}</title>
<meta name="description" content="{desc}">
{katex}
<link rel="stylesheet" href="{up}reader.css">
</head>
<body class="reader">
<header class="reader-top">
  <div class="reader-top-in">
    <a class="home" href="{up}index.html">← 返回主页</a>
    <span class="crumb">{crumb}</span>
    <nav class="actions">
      <a href="translation.md" download>下载 Markdown</a>
      <a href="sample.zip" download>下载 Markdown＋图片</a>
      <a href="validation.html">结构校验报告</a>
    </nav>
  </div>
</header>
<div class="reader-band">
  <p>{band}</p>
</div>
<div class="reader-shell">
  {toc_box}
  <main class="paper" id="article">
{body}
  </main>
</div>
<footer class="reader-foot">
  <p>来源文件：<code>{src_rel}</code> · 译文 sha256 前 12 位：<code>{sha12}</code> · 网页由 <code>scripts/build_site.py</code> 于 {build_time} 从该文件生成，未改写译文内容。</p>
</footer>
</body>
</html>
"""

VALIDATION_BANNER = (
    '<div class="reader-band"><p><b>报告展示</b>：本页是已有 '
    '<code>validation.md</code>（由翻译流水线的终检脚本生成）的网页展示，'
    '指标与状态原样保留；不是本次网站构建重新执行校验的结果。</p></div>'
)


SAMPLE_BAND = ("<b>已有样章</b>：本页展示 {pages_note}的真实译文，由流水线完整生成并保留原文结构；"
               "非完整论文翻译，语义以原文为准。原论文：{source}。")
REPORT_BAND = ("<b>报告展示</b>：本页是既有 <code>validation.md</code> 终检报告的网页版，"
               "指标与状态原样保留。")


def toc_box(toc: str) -> str:
    if not toc.strip():
        return ""
    inner = f'<nav class="toc">{toc}</nav>'
    collapse = ("<script>if (matchMedia('(max-width: 900px)').matches) {"
                "var tb = document.querySelector('.toc-box');"
                "if (tb) tb.removeAttribute('open');}</script>")
    return ('<details class="toc-box" open>\n    <summary>本节目录</summary>\n    '
            + inner + '\n  </details>\n  ' + collapse)


def build_validation_page(key: str, label: str, report_text: str, depth: int) -> str:
    up = "../" * depth
    body, _ = render_markdown(report_text)
    title = f"结构校验报告 · {label}"
    return READER_PAGE.format(
        title=html.escape(title, quote=True),
        site_title="academic-pdf-zh",
        desc="已有 validation.md 终检报告的网页展示，指标与状态原样保留。",
        katex=katex_bootstrap(depth),
        up=up,
        crumb=html.escape(label, quote=False),
        band=REPORT_BAND,
        toc_box="",
        body=VALIDATION_BANNER + body,
        src_rel=f"demo/{key}/validation.md",
        sha12="-",
        build_time=BUILD_TIME,
    )


def build_sample_zip(dst: Path, md_name: str, md_bytes: bytes, images_dir: Path) -> None:
    with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(md_name, md_bytes)
        if images_dir.exists():
            for img in sorted(images_dir.rglob("*")):
                if img.is_file():
                    z.writestr(str(img.relative_to(images_dir.parent)), img.read_bytes())


def sha256(b: bytes) -> str:
    import hashlib
    return hashlib.sha256(b).hexdigest()


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #

def main() -> int:
    cfg = json.loads((ROOT / "site.config.json").read_text(encoding="utf-8"))
    docs = ROOT / "docs"
    samples_root = docs / "samples"
    samples_root.mkdir(parents=True, exist_ok=True)

    hashes: dict[str, dict] = {}
    nav = cfg["site"]["samplesNav"]

    for paper in cfg["papers"]:
        key = paper["key"]
        src_dir = ROOT / paper["dir"]
        src_md = src_dir / paper["file"]
        if not src_md.exists():
            print(f"ERROR: missing translation file: {src_md}")
            return 2

        md_bytes = src_md.read_bytes()
        text = md_bytes.decode("utf-8")  # strict — fail loudly on encoding problems
        # strip YAML front matter (cssclasses etc.) — never rendered as prose
        text = re.sub(r"\A---\s*\n.*?\n---\s*\n", "", text, count=1, flags=re.S)

        # page range comes from the artifact's own tail note; fail if absent
        m = re.search(r"第\s*([0-9]+(?:\s*[–-]\s*[0-9]+)?)\s*页", text)
        pages_note = f"第 {m.group(1)} 页节选" if m else "已抽样页"
        if m is None:
            print(f"ERROR: cannot verify page range in {src_md}")
            return 2

        out_dir = samples_root / key
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "translation.md").write_bytes(md_bytes)

        # images: verbatim copy, relative layout preserved
        img_src = src_dir / "images"
        img_dst = out_dir / "images"
        if img_dst.exists():
            shutil.rmtree(img_dst)
        if img_src.exists():
            shutil.copytree(img_src, img_dst)

        build_sample_zip(out_dir / "sample.zip", paper["file"], md_bytes, img_src)

        val_src = src_dir / "validation.md"
        if not val_src.exists():
            print(f"ERROR: missing report: {val_src}")
            return 2
        val_bytes = val_src.read_bytes()
        (out_dir / "validation.md").write_bytes(val_bytes)

        label = next(n["label"] for n in nav if n["key"] == key)
        depth = 2  # docs/samples/<key>/xxx.html → ../../
        body, _ = render_markdown(text)
        page = READER_PAGE.format(
            title=html.escape(paper["titleCn"], quote=True),
            site_title=cfg["site"]["title"],
            desc=html.escape(f"{paper['titleEn']} 的中文样章阅读页（{pages_note}）。", quote=True),
            katex=katex_bootstrap(depth),
            up="../" * depth,
            crumb=html.escape(label, quote=False),
            band=SAMPLE_BAND.format(pages_note=pages_note,
                                    source=f'<a href="{paper["sourceLink"]}" target="_blank" rel="noopener">{paper["sourceNote"]}</a>'),
            toc_box=toc_box(toc_html(_)),
            body=body,
            src_rel=f"{paper['dir']}/{paper['file']}",
            sha12=sha256(md_bytes)[:12],
            build_time=BUILD_TIME,
        )
        (out_dir / "index.html").write_text(page, encoding="utf-8")

        vpage = build_validation_page(key, label, val_bytes.decode("utf-8"), depth)
        (out_dir / "validation.html").write_text(vpage, encoding="utf-8")

        hashes[key] = {
            "sourceTranslation": {"path": f"{paper['dir']}/{paper['file']}", "sha256": sha256(md_bytes)},
            "publicTranslation": {"path": f"docs/samples/{key}/translation.md", "sha256": sha256(md_bytes)},
            "validation": {"path": f"{paper['dir']}/validation.md", "sha256": sha256(val_bytes),
                            "publicCopy": f"docs/samples/{key}/validation.md"},
            "sampleZip": f"docs/samples/{key}/sample.zip",
            "pagesNote": pages_note,
        }
        print(f"OK samples/{key}: index/validation/translation/sample.zip/images")

    # sample directory page
    cards = []
    for n in nav:
        p = next(x for x in cfg["papers"] if x["key"] == n["key"])
        cards.append(
            f'<a class="s-card" href="{n["key"]}/index.html"><b>{html.escape(p["titleCn"])}</b>'
            f"<span>{html.escape(p['titleEn'])} · {p['venue']} · "
            f'{hashes[n["key"]]["pagesNote"]}</span>'
            f'<span class="go">阅读 →</span></a>'
        )
    idx = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>样章目录 · academic-pdf-zh</title>
<link rel="stylesheet" href="../reader.css">
</head>
<body class="reader">
<header class="reader-top"><div class="reader-top-in">
<a class="home" href="../index.html">← 返回主页</a>
<span class="crumb">样章目录</span></div></header>
<div class="reader-band"><p><b>已有样章</b>：以下三篇均由流水线从真实论文生成，阅读页完整展示译文内容；样章为节选，非完整论文翻译。</p></div>
<main class="paper s-index">
{cards}
</main>
</body>
</html>
""".format(cards="\n".join(cards))
    (samples_root / "index.html").write_text(idx, encoding="utf-8")

    (samples_root / "source-hashes.json").write_text(
        json.dumps({"generatedAt": BUILD_TIME, "papers": hashes}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print("OK samples/index.html + source-hashes.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
