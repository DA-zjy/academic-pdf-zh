from __future__ import annotations

import hashlib
import re
import shutil
import sysconfig
from collections import Counter
from pathlib import Path
from urllib.parse import unquote

IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
URL_RE = re.compile(r"https?://[^\s)\]>]+", re.I)
DOI_RE = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b", re.I)
FENCE_RE = re.compile(r"```.*?```|~~~.*?~~~", re.S)
DISPLAY_MATH_RE = re.compile(r"\$\$(.+?)\$\$|\\\[(.+?)\\\]", re.S)
INLINE_MATH_RE = re.compile(r"(?<!\$)\$(?!\$)(.+?)(?<!\$)\$(?!\$)", re.S)
INLINE_CODE_RE = re.compile(r"`[^`\n]+`")
BLOCK_ID_RE = re.compile(r"<!--\s*block:(B\d{6})\s*-->")
TABLE_PLACEHOLDER_RE = re.compile(r"\[\[TABLE_(T\d{4})\]\]")
IMM_PLACEHOLDER_RE = re.compile(r"\[\[IMM_(I\d{6})\]\]")
NUMBER_RE = re.compile(r"(?<![\w])[-+]?\d[\d,]*(?:\.\d+)?(?:[eE][-+]?\d+)?%?(?![\w])")


def find_executable(name: str) -> str | None:
    found = shutil.which(name)
    if found:
        return found
    scripts = Path(sysconfig.get_path("scripts"))
    for candidate in (scripts / name, scripts / f"{name}.exe", scripts / f"{name}.cmd"):
        if candidate.exists():
            return str(candidate)
    return None


def infer_project_root(cwd: Path) -> Path:
    """Avoid accidental work/work/... nesting when commands are rerun from an output folder."""
    cwd = cwd.resolve()
    chain = [cwd, *cwd.parents]
    for p in chain:
        if p.name.lower() == "work":
            return p.parent
    for p in chain:
        if (p / ".git").exists():
            return p
    return cwd


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def clean_link_target(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("<") and raw.endswith(">"):
        raw = raw[1:-1]
    if ' "' in raw:
        raw = raw.split(' "', 1)[0]
    if " '" in raw:
        raw = raw.split(" '", 1)[0]
    return unquote(raw)


def copy_referenced_images(md: str, md_base: Path, out_images: Path) -> tuple[str, dict[str, str], list[str]]:
    out_images.mkdir(parents=True, exist_ok=True)
    mapping: dict[str, str] = {}
    missing: list[str] = []
    used_names: dict[str, Path] = {}

    def repl(match: re.Match[str]) -> str:
        alt, raw_target = match.group(1), match.group(2)
        target = clean_link_target(raw_target)
        if target.lower().startswith(("http://", "https://", "data:")):
            return match.group(0)
        src = Path(target)
        if not src.is_absolute():
            src = (md_base / src).resolve()
        if not src.exists() or not src.is_file():
            missing.append(target)
            return match.group(0)
        base = src.name or "figure.png"
        chosen = base
        if chosen in used_names and used_names[chosen] != src:
            digest = hashlib.sha1(str(src).encode("utf-8")).hexdigest()[:8]
            chosen = f"{src.stem}-{digest}{src.suffix}"
        used_names[chosen] = src
        dst = out_images / chosen
        if not dst.exists():
            shutil.copy2(src, dst)
        new_target = f"images/{chosen}"
        mapping[target] = new_target
        return f"![{alt}]({new_target})"

    return IMAGE_RE.sub(repl, md), mapping, missing


def norm_math(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip())


def extract_math(text: str) -> list[str]:
    out: list[str] = []
    occupied: list[tuple[int, int]] = []
    for m in DISPLAY_MATH_RE.finditer(text):
        body = next((g for g in m.groups() if g is not None), "")
        out.append(norm_math(body))
        occupied.append(m.span())
    for m in INLINE_MATH_RE.finditer(text):
        if any(a <= m.start() < b for a, b in occupied):
            continue
        out.append(norm_math(m.group(1)))
    return out


def multiset_missing(source: list[str], target: list[str]) -> list[str]:
    remain = Counter(target)
    missing: list[str] = []
    for item in source:
        if remain[item] > 0:
            remain[item] -= 1
        else:
            missing.append(item)
    return missing


def strip_block_markers(text: str) -> str:
    return re.sub(r"(?m)^\s*<!--\s*block:B\d{6}\s*-->\s*\n?", "", text)


def numeric_tokens(text: str) -> list[str]:
    clean = re.sub(r"<[^>]+>", " ", text)
    return NUMBER_RE.findall(clean)


def page_rect_from_bbox(page, bbox, page_size=None):
    import fitz
    pw, ph = float(page.rect.width), float(page.rect.height)
    if not bbox or len(bbox) != 4:
        return None
    if page_size and len(page_size) >= 2 and float(page_size[0]) > 0 and float(page_size[1]) > 0:
        sx = pw / float(page_size[0]); sy = ph / float(page_size[1])
    else:
        sx = sy = 1.0
    x0, y0, x1, y1 = [float(v) for v in bbox]
    return fitz.Rect(max(0, x0*sx), max(0, y0*sy), min(pw, x1*sx), min(ph, y1*sy))
