"""调用 Claude 按照爆款框架仿写演讲口才主题的小红书笔记。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from anthropic import Anthropic

PROMPT = Path(__file__).parent.parent / "prompts" / "generate.txt"


def generate_notes(
    frames: dict[str, Any],
    reference_notes: list[dict[str, Any]],
    count: int,
    client: Anthropic,
    model: str,
    max_tokens: int,
) -> list[dict[str, Any]]:
    template = PROMPT.read_text(encoding="utf-8")
    ref_titles = [n["title"] for n in reference_notes[:10]]
    prompt = (
        template
        .replace("{{COUNT}}", str(count))
        .replace("{{FRAMES_JSON}}", json.dumps(frames, ensure_ascii=False, indent=2))
        .replace("{{REF_TITLES}}", json.dumps(ref_titles, ensure_ascii=False, indent=2))
    )

    resp = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    text = resp.content[0].text.strip()
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1:
        raise ValueError(f"模型返回非预期格式，无法解析 JSON 数组：{text[:400]}")
    return json.loads(text[start:end + 1])
