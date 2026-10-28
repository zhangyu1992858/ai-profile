#!/usr/bin/env python3
"""Generate root-level profile *.html from profile/*.md (checked in for static hosting)."""
import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "profile"
SITE = "https://profile.benzhang.ccwu.cc"

PAGES = [
    ("about", "基本情况", "about.md"),
    ("work", "工作经历", "work.md"),
    ("education", "教育经历", "education.md"),
    ("credentials", "职称材料", "credentials.md"),
    ("skills-interests", "技能与兴趣", "skills-interests.md"),
    ("awards", "获奖与荣誉", "awards.md"),
    ("patents", "专利", "patents.md"),
    ("publications", "论文与出版", "publications.md"),
    ("ai-usage-preferences", "与 AI 协作偏好", "ai-usage-preferences.md"),
]


def inline_md(text: str) -> str:
    text = html.escape(text)
    text = re.sub(
        r"\[([^\]]+)\]\((https?://[^)\s]+|/[^)\s]+)\)",
        r'<a href="\2" target="_blank" rel="noopener">\1</a>',
        text,
    )
    text = re.sub(
        r"(^|[\s（(])((?:https?://)[^\s)）]+)",
        lambda m: f'{m.group(1)}<a href="{m.group(2)}" target="_blank" rel="noopener">{m.group(2)}</a>',
        text,
    )
    return text


def is_table_row(line: str) -> bool:
    s = line.strip()
    return s.startswith("|") and s.endswith("|") and "|" in s[1:-1]


def is_table_sep(line: str) -> bool:
    return bool(re.match(r"^\|[\s\-:|]+\|\s*$", line.strip()))


def parse_table(lines: list[str], i: int) -> tuple[str, int]:
    rows = []
    while i < len(lines) and is_table_row(lines[i]):
        if not is_table_sep(lines[i]):
            cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
            rows.append(cells)
        i += 1
    if not rows:
        return "", i
    header, body = rows[0], rows[1:]
    out = ["<table><thead><tr>"]
    out.extend(f"<th>{inline_md(c)}</th>" for c in header)
    out.append("</tr></thead><tbody>")
    for row in body:
        out.append("<tr>")
        out.extend(f"<td>{inline_md(c)}</td>" for c in row)
        out.append("</tr>")
    out.append("</tbody></table>")
    return "\n".join(out), i


def md_to_html(md: str, skip_leading_h1: bool = False) -> str:
    lines = md.splitlines()
    if skip_leading_h1 and lines and lines[0].strip().startswith("# "):
        lines = lines[1:]
    parts: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped:
            i += 1
            continue
        if stripped.startswith("# "):
            parts.append(f"<h1>{inline_md(stripped[2:].strip())}</h1>")
            i += 1
            continue
        if stripped.startswith("## "):
            parts.append(f"<h2>{inline_md(stripped[3:].strip())}</h2>")
            i += 1
            continue
        if stripped.startswith("### "):
            parts.append(f"<h3>{inline_md(stripped[4:].strip())}</h3>")
            i += 1
            continue
        if is_table_row(line):
            block, i = parse_table(lines, i)
            parts.append(block)
            continue
        if re.match(r"^[-*]\s+", stripped):
            parts.append("<ul>")
            while i < len(lines) and re.match(r"^[-*]\s+", lines[i].strip()):
                item = re.sub(r"^[-*]\s+", "", lines[i].strip())
                parts.append(f"<li>{inline_md(item)}</li>")
                i += 1
            parts.append("</ul>")
            continue
        if re.match(r"^\d+\.\s+", stripped):
            parts.append("<ol>")
            while i < len(lines) and re.match(r"^\d+\.\s+", lines[i].strip()):
                item = re.sub(r"^\d+\.\s+", "", lines[i].strip())
                i += 1
                subs: list[str] = []
                while i < len(lines) and (lines[i].startswith("   ") or lines[i].startswith("\t")):
                    sub = lines[i].strip()
                    if sub.startswith("- ") or sub.startswith("* "):
                        subs.append(sub[2:])
                    elif sub:
                        subs.append(sub)
                    i += 1
                if subs:
                    inner = "".join(f"<li>{inline_md(s)}</li>" for s in subs)
                    parts.append(f"<li>{inline_md(item)}<ul>{inner}</ul></li>")
                else:
                    parts.append(f"<li>{inline_md(item)}</li>")
            parts.append("</ol>")
            continue
        if stripped.startswith("> "):
            parts.append(f"<p><em>{inline_md(stripped[2:].strip())}</em></p>")
            i += 1
            continue
        parts.append(f"<p>{inline_md(stripped)}</p>")
        i += 1
    return "\n".join(parts)


def render_page(slug: str, nav_title: str, md: str) -> str:
    body = md_to_html(md, skip_leading_h1=True)
    title = nav_title
    if md.startswith("# "):
        title = md.splitlines()[0][2:].strip()
    desc = f"张玉川公开档案 · {title}"
    return f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)} · 张玉川</title><meta name="description" content="{html.escape(desc)}">
<link rel="stylesheet" href="/profile-page.css">
</head><body>
<header><h1>{html.escape(title)}</h1><p>张玉川 · Ben Zhang · 公开档案</p><a class="back" href="/">← 返回首页</a></header>
<main><article class="card">{body}</article></main>
<footer>公开版 · <a href="{SITE}/llms.txt">llms.txt</a> · <a href="{SITE}/graph">知识图谱</a></footer>
</body></html>
"""


def main() -> None:
    for slug, nav_title, filename in PAGES:
        md = (PROFILE / filename).read_text(encoding="utf-8")
        out = ROOT / f"{slug}.html"
        out.write_text(render_page(slug, nav_title, md), encoding="utf-8")
        print(f"Wrote {out.name}")


if __name__ == "__main__":
    main()
