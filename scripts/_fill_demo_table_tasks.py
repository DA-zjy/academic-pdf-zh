#!/usr/bin/env python3
"""Demo helper: fill the `translation` field of the demo table task JSONs."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "demo" / ".build"

transformer = {
    "C0001": "层类型",
    "C0002": "每层复杂度",
    "C0003": "串行<br>操作数",
    "C0004": "最大路径长度",
    "C0005": "自注意力",
    "C0006": "O(n² · d)",
    "C0007": "O([[TCP_P001]])",
    "C0008": "O([[TCP_P001]])",
    "C0009": "循环",
    "C0010": "O(n · d²)",
    "C0011": "O(n)",
    "C0012": "O(n)",
    "C0013": "卷积",
    "C0014": "O(k · n · d²)",
    "C0015": "O([[TCP_P001]])",
    "C0016": "O(logₖ(n))",
    "C0017": "自注意力（受限）",
    "C0018": "O(r · n · d)",
    "C0019": "O([[TCP_P001]])",
    "C0020": "O(n/r)",
}

deepseek = {
    "C0001": "问题",
    "C0002": r"若 $a > [[TCP_P001]]$，那么 $\sqrt{a - \sqrt{a + x}} = x$ 的全部实数解之和等于",
    "C0003": "回答",
    "C0004": (r"<think> 为求解方程 $\sqrt{a - \sqrt{a + x}} = x$，我们先对方程两边平方 $\cdots$ "
              r"$\left(\sqrt{a - \sqrt{a+x}}\right)^[[TCP_P001]] = x^[[TCP_P002]] \implies a - \sqrt{a+x} = x^[[TCP_P003]]$。"
              r"整理以分离内层平方根项：$(a - x^[[TCP_P004]])^[[TCP_P005]] = a + x \implies "
              r"a^[[TCP_P006]] - 2ax^[[TCP_P007]] + (x^[[TCP_P008]])^[[TCP_P009]] = a + x \implies "
              r"x^[[TCP_P010]] - 2ax^[[TCP_P011]] - x + (a^[[TCP_P012]] - a) = [[TCP_P013]]$ $\cdots$ "
              r"等等，等等，等等。这是我能够在此标记的一个“aha 时刻”。让我们逐步重新评估，确认正确的解之和是否可以为 $\cdots$ "
              r"我们从方程开始：$\sqrt{a - \sqrt{a+x}} = x$ 首先，对方程两边平方："
              r"$a - \sqrt{a+x} = x^[[TCP_P014]] \implies \sqrt{a+x} = a - x^[[TCP_P015]]$ "
              r"接下来，我可以再次对方程两边平方，把方程视为：$\cdots$ $\cdots$"),
}


def fill(task_file: Path, mapping: dict) -> None:
    task = json.loads(task_file.read_text(encoding="utf-8"))
    for cell in task["cells"]:
        tr = mapping[cell["id"]]
        for item in cell.get("protected", []):
            token = f"[[TCP_{item['id']}]]"
            if token not in tr:
                raise SystemExit(f"{task_file.name} {cell['id']}: missing {token}")
        if tr.count("[[TCP_") != len(cell.get("protected", [])):
            raise SystemExit(f"{task_file.name} {cell['id']}: token count mismatch")
        cell["translation"] = tr
    task_file.write_text(json.dumps(task, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"filled {task_file} ({len(mapping)} cells)")


fill(ROOT / "transformer" / "chunks" / "table_tasks" / "T0001.json", transformer)
fill(ROOT / "deepseek-r1" / "chunks" / "table_tasks" / "T0001.json", deepseek)
