#!/usr/bin/env python3
"""Regenerate graph.html embedded graph data from profile markdown and llms.txt."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GRAPH_HTML = ROOT / "graph.html"
PROFILE = ROOT / "profile"
LLMS = ROOT / "llms.txt"

FILES = [
    ("about.md", PROFILE / "about.md"),
    ("work.md", PROFILE / "work.md"),
    ("education.md", PROFILE / "education.md"),
    ("credentials.md", PROFILE / "credentials.md"),
    ("skills-interests.md", PROFILE / "skills-interests.md"),
    ("awards.md", PROFILE / "awards.md"),
    ("patents.md", PROFILE / "patents.md"),
    ("publications.md", PROFILE / "publications.md"),
    ("ai-usage-preferences.md", PROFILE / "ai-usage-preferences.md"),
    ("llms.txt", LLMS),
]

OPEN_TO_WORK = "正在求职（意向城市：济南，现场或混合办公）"
ROOT_BLURB = (
    "# 张玉川（Ben Zhang）· AI 个人档案（公开版）\n"
    "> 硕士研究生（塔斯马尼亚大学，电力工程）、工业工程工程师（中级），"
    "就职于北京中兴物业管理有限公司生产技术处（国网中兴下属），岗位客服管理（六级职员）；"
    "从事客服管理、安全生产标准化、应急管理、物业能源管理与绿色低碳运行。\n\n"
    f"{OPEN_TO_WORK}\n"
    "领英：https://www.linkedin.com/in/yuchuanzhang21\n"
    "抖音：https://v.douyin.com/d5jOm4gqsWM/\n"
    "哔哩哔哩 · 小川懂生活：https://b23.tv/6DdjSRe\n"
    "YouTube · @ben_zhang：https://youtube.com/@ben_zhang\n"
)

# Display names only. Node ids stay as source filenames so links keep their shape.
LABELS = {
    "about.md": "基本情况",
    "work.md": "工作经历",
    "education.md": "教育经历",
    "credentials.md": "职称材料",
    "skills-interests.md": "技能与兴趣",
    "awards.md": "获奖与荣誉",
    "patents.md": "专利",
    "publications.md": "论文与出版",
    "ai-usage-preferences.md": "AI 协作偏好",
    "llms.txt": "档案索引",
}


def child_name(line: str) -> str:
    s = re.sub(r"^[\d]+\.\s*", "", line)
    s = re.sub(r"^[-*]\s*", "", s)
    s = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s)
    s = s.split("｜")[0].split("|")[0].strip()
    return (s[:22] if len(s) > 22 else s) or "item"


def extract_children(text: str, file_id: str):
    children = []
    section = ""
    for line in text.splitlines():
        if line.startswith("# "):
            section = line[2:].strip()
        elif line.startswith("## "):
            section = line[3:].strip()
        elif re.match(r"^(\d+\.|[-*])\s+", line):
            body = line.strip()
            children.append(
                {
                    "id": f"{file_id}#{len(children)+1}",
                    "name": child_name(body),
                    "group": 2,
                    "val": 2,
                    "text": f"{section}\n{body}" if section else body,
                }
            )
    return children


def build_graph():
    nodes = [
        {
            "id": "root",
            "name": "张玉川 / Ben Zhang",
            "group": 0,
            "val": 14,
            "text": ROOT_BLURB,
        }
    ]
    links = []
    for file_id, path in FILES:
        text = path.read_text(encoding="utf-8")
        nodes.append(
            {
                "id": file_id,
                "name": LABELS.get(file_id, file_id),
                "group": 1,
                "val": 7,
                "text": text,
            }
        )
        links.append({"source": "root", "target": file_id})
        for ch in extract_children(text, file_id):
            nodes.append(ch)
            links.append({"source": file_id, "target": ch["id"]})
    return {"nodes": nodes, "links": links}


def validate_payload(payload: str, data: dict) -> None:
    """Ensure JSON is valid and multiline strings stay escaped (not literal newlines)."""
    if "\n" in payload or "\r" in payload:
        raise SystemExit("graph payload must be a single-line JSON literal")
    parsed = json.loads(payload)
    if parsed != data:
        raise SystemExit("graph payload round-trip mismatch")
    if any("\n" in (n.get("text") or "") for n in data["nodes"]):
        assert "\\n" in payload, "multiline node text must use JSON \\n escapes"
    if len(data["nodes"]) < 20:
        raise SystemExit(f"expected dozens of graph nodes, got {len(data['nodes'])}")


def patch_graph_html(data: dict) -> None:
    html = GRAPH_HTML.read_text(encoding="utf-8")
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ": "))
    validate_payload(payload, data)
    replacement = f"const D={payload};\nconst C="
    new_html, n = re.subn(
        r"const D=.*?;\nconst C=",
        lambda _m: replacement,
        html,
        count=1,
        flags=re.DOTALL,
    )
    if n != 1:
        raise SystemExit("Could not patch graph.html const D=...")
    GRAPH_HTML.write_text(new_html, encoding="utf-8")


if __name__ == "__main__":
    data = build_graph()
    patch_graph_html(data)
    print(f"Updated {GRAPH_HTML} ({len(data['nodes'])} nodes)")
