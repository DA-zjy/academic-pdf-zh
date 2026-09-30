#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from collections import Counter
from pathlib import Path

PAGE_MARKERS = [
    re.compile(r"^\s*---\s*end of page\.page_number=\d+\s*---\s*$", re.I),
    re.compile(r"^\s*<PARSED TEXT FOR PAGE:\s*\d+\s*/\s*\d+>\s*$", re.I),
]
PICTURE_TEXT_RE = re.compile(r"<!--\s*Start of picture text\s*-->(.*?)<!--\s*End of picture text\s*-->", re.S | re.I)
FIG_CAPTION_RE = r"(?:Figure|Fig\.|图)\s*\d+\s*[:：]"


def convert_picture_text(md: str) -> str:
    def repl(m: re.Match[str]) -> str:
        body = m.group(1).strip()
        body = re.sub(r"<br\s*/?>", "  \n", body, flags=re.I)
        body = re.sub(r"\n{3,}", "\n\n", body).strip()
        if not body:
            return ""
        return "\n<details>\n<summary>图内文字（原文提取，待翻译）</summary>\n\n" + body + "\n\n</details>\n"
    return PICTURE_TEXT_RE.sub(repl, md)


def repeated_header_lines(lines: list[str]) -> set[str]:
    vals = []
    for line in lines:
        s = line.strip()
        if 12 <= len(s) <= 120 and not s.startswith(("#", "|", "!", "<", "- ")):
            vals.append(s)
    c = Counter(vals)
    return {s for s, n in c.items() if n >= 4 and ("conference paper" in s.lower() or "published as" in s.lower())}


def sequential_page_numbers(lines: list[str]) -> set[str]:
    nums = []
    for line in lines:
        s = line.strip()
        if re.fullmatch(r"\d{1,3}", s):
            n = int(s)
            if 0 < n < 500:
                nums.append(n)
    unique = sorted(set(nums))
    if len(unique) < 5:
        return set()
    adjacency = sum(1 for a, b in zip(unique, unique[1:]) if b == a + 1)
    if adjacency < max(4, int(0.7 * (len(unique) - 1))):
        return set()
    return {str(x) for x in unique}


def demote_false_headings(text: str) -> tuple[str, int]:
    count = 0
    out = []
    pat = re.compile(r"^(#{1,6})\s+((?:In summary|Overall|Specifically|To summarize)\b.*[:：])\s*$", re.I)
    for line in text.splitlines():
        m = pat.match(line.strip())
        if m:
            out.append(f"**{m.group(2)}**")
            count += 1
        else:
            out.append(line)
    return "\n".join(out), count


def reflow_interrupted_figures(text: str) -> tuple[str, int]:
    """Move a figure after a sentence that a PDF page break split in half.

    Conservative: previous paragraph must lack terminal punctuation; next paragraph must
    start with a lowercase Latin letter. This targets English source Markdown before translation.
    """
    img = r"!\[[^\]]*\]\([^\n)]+\)"
    caption = rf"(?:{FIG_CAPTION_RE})[^\n]*"
    pattern = re.compile(
        rf"(?P<pre>[^\n]+[^\s.!?;:])\n\n(?P<img>{img})\n\n(?P<cap>{caption})\n\n(?P<post>[a-z][^\n]*)",
        re.M,
    )
    changed = 0
    while True:
        m = pattern.search(text)
        if not m:
            break
        merged = f"{m.group('pre').rstrip()} {m.group('post').lstrip()}\n\n{m.group('img')}\n\n{m.group('cap')}"
        text = text[:m.start()] + merged + text[m.end():]
        changed += 1
        if changed > 50:
            break
    return text, changed


def normalize(md: str) -> tuple[str, dict[str, int]]:
    md = md.replace("\ufeff", "").replace("\u00ad", "").replace("\ufffd", "")
    md = convert_picture_text(md)
    lines = md.splitlines()
    header_values = repeated_header_lines(lines)
    page_numbers = sequential_page_numbers(lines)
    seen_headers: set[str] = set()
    out: list[str] = []
    stats = {"removed_page_markers": 0, "removed_page_numbers": 0, "removed_repeated_headers": 0}

    for line in lines:
        s = line.strip()
        if any(p.match(line) for p in PAGE_MARKERS):
            stats["removed_page_markers"] += 1; continue
        if s in header_values:
            if s in seen_headers:
                stats["removed_repeated_headers"] += 1; continue
            seen_headers.add(s)
        if s in page_numbers:
            stats["removed_page_numbers"] += 1; continue
        out.append(line.rstrip())

    text = "\n".join(out)
    text, false_h = demote_false_headings(text)
    text, reflowed = reflow_interrupted_figures(text)
    text = re.sub(r"\n{4,}", "\n\n\n", text).strip() + "\n"
    stats["demoted_false_headings"] = false_h
    stats["reflowed_figure_interruptions"] = reflowed
    return text, stats


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("input", type=Path)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    clean, stats = normalize(a.input.read_text(encoding="utf-8", errors="replace"))
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(clean, encoding="utf-8")
    print(a.output.resolve()); print(" ".join(f"{k}={v}" for k,v in stats.items()))
    return 0

if __name__ == "__main__": raise SystemExit(main())
