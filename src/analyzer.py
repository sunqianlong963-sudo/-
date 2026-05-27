"""调用 Claude 分析爆款笔记的共性框架。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from anthropic import Anthropic

PROMPT = Path(__file__).parent.parent / "prompts" / "analyze.txt"


def analyze_viral_frames(notes: list[dict[str, Any]], client: Anthropic, model: str) -> dict[str, Any]:
    """输入爆款笔记列表，返回结构化的爆款框架分析结果。"""
    if not notes:
        return {"hooks": [], "structures": [], "tones": [], "keywords": [], "summary": ""}

    sample = [
        {
            "title": n["title"],
            "desc": n["desc"][:600],
            "tags": n.get("tags", []),
            "likes": n["stats"]["likes"],
            "collects": n["stats"]["collects"],
            "comments": n["stats"]["comments"],
        }
        for n in notes
    ]

    prompt = PROMPT.read_text(encoding="utf-8").replace("{{NOTES_JSON}}", json.dumps(sample, ensure_ascii=False, indent=2))

    resp = client.messages.create(
        model=model,
        max_tokens=3000,
        messages=[{"role": "user", "content": prompt}],
    )
    text = resp.content[0].text.strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        return {"raw": text, "hooks": [], "structures": [], "tones": [], "keywords": [], "summary": text}
    try:
        return json.loads(text[start:end + 1])
    except json.JSONDecodeError:
        return {"raw": text, "hooks": [], "structures": [], "tones": [], "keywords": [], "summary": text}
