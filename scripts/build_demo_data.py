#!/usr/bin/env python3
"""Generate docs/demo-data.js for the showcase animation.

All displayed content is built from existing artifacts (no hand-typed evidence):
- table cells:        demo/transformer/table_tasks.T0001.json (source / translation / protected tokens)
- prose EN/CN:        demo/transformer/chunks/0003.source.md & 0003.translated.md (blocks B000061-B000065)
- formulas:           demo/.build/transformer/chunks/manifest.json immutables (I000001, I000004)
- validation metrics: demo/{transformer,resnet,deepseek-r1}/validation.md
- titles & captions:  demo/{transformer,resnet}/<paper>_中文.md

Run:  python scripts/build_demo_data.py
Output: docs/demo-data.js  (window.DEMO_DATA = {...})
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def restore_tokens(text: str, immutables: dict[str, str]) -> str:
    return re.sub(r"\[\[IMM_(I\d+)\]\]", lambda m: immutables.get(m.group(1), m.group(0)), text)


def load_immutables() -> dict[str, str]:
    manifest_path = ROOT / "demo/.build/transformer/chunks/manifest.json"
    if not manifest_path.exists():
        raise SystemExit(
            "ERROR: demo/.build/transformer/chunks/manifest.json not found.\n"
            "docs/demo-data.js (动画数据) 依赖该构建中间材料（冻结 token 的公式真身）。\n"
            "缺少时请勿伪造：保留仓库中已生成的 docs/demo-data.js 即可；如需重建，\n"
            "先运行 prepare_paper.py + chunk_markdown.py 重建 demo/.build/transformer 清单。\n"
            "（站点阅读页构建 scripts/build_site.py 不依赖此文件。）"
        )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    return {item["id"]: item["value"] for item in manifest["immutables"]}


def parse_blocks(path: Path) -> dict[str, str]:
    """Split a chunk file into {block_id: body}."""
    text = path.read_text(encoding="utf-8")
    blocks: dict[str, str] = {}
    parts = re.split(r"<!-- block:(B\d+) -->", text)
    for i in range(1, len(parts), 2):
        blocks[parts[i]] = parts[i + 1].strip()
    return blocks


def strip_md_inline(s: str) -> str:
    return s.replace("**", "").strip()


def extract_prose(immutables: dict[str, str]) -> dict:
    """Positional-encoding section: heading + one paragraph + intro line + formula + where-paragraph."""
    src = parse_blocks(ROOT / "demo/transformer/chunks/0003.source.md")
    dst = parse_blocks(ROOT / "demo/transformer/chunks/0003.translated.md")
    src = {k: restore_tokens(v, immutables) for k, v in src.items()}
    dst = {k: restore_tokens(v, immutables) for k, v in dst.items()}

    heading_en = strip_md_inline(src["B000061"]).removeprefix("###")
    heading_cn = strip_md_inline(dst["B000061"]).removeprefix("###")
    # drop the leading "3.5 " numbering kept by the heading token, keep it consistent
    heading_en = re.sub(r"^3\.5\s*", "", heading_en).strip()
    heading_cn = re.sub(r"^3\.5\s*", "", heading_cn).strip()

    para1_en = re.sub(r"\[+\[IMM_I000147\]\]+", "", src["B000062"]).strip()
    para1_cn = re.sub(r"\[+\[IMM_I000147\]\]+", "", dst["B000062"]).strip()

    # inline math inside the prose: render the restored $$..$$ tokens as inline latex
    def inline_math(html: str) -> str:
        return html

    return {
        "heading": {"en": heading_en, "cn": heading_cn},
        "para1": {"en": para1_en, "cn": para1_cn},
        "line": {"en": src["B000063"], "cn": dst["B000063"]},
        "formulaToken": "PE",
        "para2": {"en": src["B000065"], "cn": dst["B000065"]},
    }


def mathify_para2(en: str, cn: str) -> tuple[str, str]:
    """Turn restored inline math (e.g. $pos$) into <span class="im">…</span> so the
    page can highlight protected inline math. Formula bodies stay untouched."""
    def conv(s: str) -> str:
        s = re.sub(r"\$\$(.+?)\$\$", r"<span class='im'>\1</span>", s)
        s = re.sub(r"\$([^\$]+?)\$", r"<span class='im'>\1</span>", s)
        return s

    return conv(en), conv(cn)


def extract_formulas(immutables: dict[str, str]) -> dict:
    attention = immutables["I000001"].strip().strip("$").strip()
    pe = immutables["I000004"].strip().strip("$").strip()
    if r"\\" in pe:
        pe = r"\begin{aligned}" + pe + r"\end{aligned}"
    return {"attention": attention, "pe": pe}


def extract_table() -> dict:
    task = json.loads(
        (ROOT / "demo/transformer/table_tasks.T0001.json").read_text(encoding="utf-8")
    )
    cells = {c["id"]: c for c in task["cells"]}

    def token_restore(s: str, protected: list[dict]) -> str:
        for p in protected:
            s = s.replace(f"[[TCP_{p['id']}]]", p["value"])
        return s

    order = [f"C{i:04d}" for i in range(1, 21)]
    grid = [order[i * 4:(i + 1) * 4] for i in range(5)]  # 1 header row + 4 data rows

    rows = []
    protected_count = 0
    changed_count = 0
    for row_ids in grid:
        row_cells = []
        for cid in row_ids:
            c = cells[cid]
            src = c["source"]
            dst = token_restore(c["translation"], c["protected"])
            protected_count += len(c["protected"])
            changed = src.replace("<br>", "") != dst.replace("<br>", "")
            changed_count += 1 if changed else 0
            row_cells.append({
                "src": src,
                "dst": dst,
                "changed": changed,
                "protectedIds": [p["id"] for p in c["protected"]],
            })
        rows.append(row_cells)

    return {
        "id": task["id"],
        "headers": rows[0],
        "body": rows[1:],
        "cellCount": len(order),
        "changedCount": changed_count,
        "protectedCount": protected_count,
        "caption": {
            "en": "Table 1: Maximum path lengths, per-layer complexity and minimum number of sequential operations for different layer types.",
            "cn": "表 1：不同层类型的最大路径长度、每层复杂度与最少串行操作数。",
        },
    }


METRIC_PATTERNS = [
    ("blocks", r"Manifest blocks:\s*(\d+)"),
    ("headings", r"Source / translated headings:\s*(\d+)\s*/\s*(\d+)"),
    ("tables", r"Source / translated tables:\s*(\d+)\s*/\s*(\d+)"),
    ("images", r"Source / translated images:\s*(\d+)\s*/\s*(\d+)"),
    ("latex", r"Source / translated LaTeX expressions:\s*(\d+)\s*/\s*(\d+)"),
    ("cjkRatio", r"CJK chars per source English word:\s*([\d.]+)"),
]


def extract_validation(paper: str) -> dict:
    path = ROOT / f"demo/{paper}/validation.md"
    text = path.read_text(encoding="utf-8")
    out: dict = {}
    for key, pat in METRIC_PATTERNS:
        m = re.search(pat, text)
        if not m:
            raise SystemExit(f"validation metric '{key}' not found in {path}")
        out[key] = [int(g) for g in m.groups()] if len(m.groups()) > 1 else float(m.group(1))
    status = "PASS" if re.search(r"\*\*PASS\*\*", text) else ("REVIEW" if "REVIEW" in text else "FAIL")
    out["status"] = status
    out["reportPath"] = f"demo/{paper}/validation.md"
    return out


def extract_cn_title(paper: str, file_key: str) -> str:
    text = (ROOT / f"demo/{paper}/{file_key}").read_text(encoding="utf-8")
    m = re.search(r"^#\s+\*\*(.+?)\*\*", text, re.M)
    if not m:
        raise SystemExit(f"CN title not found in demo/{paper}/{file_key}")
    return m.group(1).strip()


def main() -> None:
    immutables = load_immutables()
    prose = extract_prose(immutables)
    prose["para2"]["en"], prose["para2"]["cn"] = mathify_para2(
        prose["para2"]["en"], prose["para2"]["cn"]
    )
    # also mathify para1 inline math if any ($d_{\text{model}}$ appears there)
    prose["para1"]["en"], prose["para1"]["cn"] = mathify_para2(
        prose["para1"]["en"], prose["para1"]["cn"]
    )

    papers = ["transformer", "resnet", "deepseek-r1"]
    validations = {p: extract_validation(p) for p in papers}

    data = {
        "_meta": {
            "generatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
            "note": "由 scripts/build_demo_data.py 生成；全部内容取自 demo/ 下的真实产物（表格任务 JSON、chunk 源/译文、manifest 公式、validation 报告）。请勿手工编辑。",
            "sources": {
                "table": "demo/transformer/table_tasks.T0001.json",
                "prose": "demo/transformer/chunks/0003.source.md + 0003.translated.md (B000061-B000065)",
                "formulas": "demo/.build/transformer/chunks/manifest.json (I000001, I000004)",
                "metrics": [v["reportPath"] for v in validations.values()],
                "figure": "demo/transformer/images/_pages_subset.pdf-0003-00.png -> docs/assets/figure-1.png",
            },
        },
        "brand": {"name": "academic-pdf-zh"},
        "prose": prose,
        "formulas": extract_formulas(immutables),
        "table": extract_table(),
        "papers": [
            {
                "key": "transformer",
                "titleCn": extract_cn_title("transformer", "transformer_中文.md"),
                "titleEn": "Attention Is All You Need",
                "venue": "NeurIPS 2017",
                "link": "samples/transformer/index.html",
                "report": "samples/transformer/validation.html",
                "validation": validations["transformer"],
            },
            {
                "key": "resnet",
                "titleCn": extract_cn_title("resnet", "resnet_中文.md"),
                "titleEn": "Deep Residual Learning for Image Recognition",
                "venue": "CVPR 2016",
                "link": "samples/resnet/index.html",
                "report": "samples/resnet/validation.html",
                "validation": validations["resnet"],
            },
            {
                "key": "deepseek-r1",
                "titleCn": extract_cn_title("deepseek-r1", "deepseek-r1_中文.md"),
                "titleEn": "DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via RL",
                "venue": "arXiv 2501.12948",
                "link": "samples/deepseek-r1/index.html",
                "report": "samples/deepseek-r1/validation.html",
                "validation": validations["deepseek-r1"],
            },
        ],
        "figure": {"src": "assets/figure-1.png", "caption": "图 1：Transformer——模型架构。"},
    }

    # verify the figure caption claim against the translated markdown
    cn = (ROOT / "demo/transformer/transformer_中文.md").read_text(encoding="utf-8")
    if "图 1：Transformer——模型架构。" not in cn:
        m = re.search(r"^图 1：(.+)$", cn, re.M)
        data["figure"]["caption"] = f"图 1：{m.group(1).strip()}" if m else data["figure"]["caption"]

    out = ROOT / "docs/demo-data.js"
    out.write_text(
        "/* 生成文件：由 scripts/build_demo_data.py 生成，勿手改。 */\n"
        "window.DEMO_DATA = "
        + json.dumps(data, ensure_ascii=False, indent=2)
        + ";\n",
        encoding="utf-8",
    )
    t = data["table"]
    print(
        f"OK docs/demo-data.js  table: {t['cellCount']} cells "
        f"({t['changedCount']} translated, {t['protectedCount']} protected tokens)  "
        f"papers: {[(p['key'], p['validation']['status']) for p in data['papers']]}"
    )


if __name__ == "__main__":
    sys.exit(main())
