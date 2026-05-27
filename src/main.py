"""主流程：抓取 → 分析 → 仿写 → 飞书入库。

环境变量：
- ANTHROPIC_API_KEY    Claude API key
- FEISHU_APP_ID        飞书自建应用 App ID
- FEISHU_APP_SECRET    飞书自建应用 App Secret
- XHS_COOKIES_JSON     小红书登录 cookies（JSON 字符串）
                       本地调试可改为放 config/cookies.json
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import yaml
from anthropic import Anthropic

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from src.analyzer import analyze_viral_frames
from src.feishu_client import FeishuClient
from src.generator import generate_notes
from src.xhs_scraper import CN_TZ, ScrapeConfig, scrape


def load_config() -> dict:
    path = ROOT / "config" / "config.yaml"
    if not path.exists():
        path = ROOT / "config" / "config.example.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def ensure_cookies() -> Path:
    """优先用环境变量里的 cookies，落地到 config/cookies.json 供 Playwright 使用。"""
    target = ROOT / "config" / "cookies.json"
    raw = os.environ.get("XHS_COOKIES_JSON")
    if raw:
        target.write_text(raw, encoding="utf-8")
        return target
    if target.exists():
        return target
    raise FileNotFoundError(
        "未提供小红书 cookies。请设置环境变量 XHS_COOKIES_JSON，"
        "或在 config/cookies.json 放入导出的 cookies 数组。"
    )


def build_feishu_record_for_viral(note: dict) -> dict:
    """爆款笔记入库字段。"""
    return {
        "类型": "爆款样本",
        "标题": note["title"],
        "正文": note["desc"],
        "作者": note["author"]["nickname"],
        "粉丝数": note["author"]["fans"],
        "点赞": note["stats"]["likes"],
        "收藏": note["stats"]["collects"],
        "评论": note["stats"]["comments"],
        "互动总数": note["stats"]["interactions"],
        "发布时间": note.get("published_at") or "",
        "链接": {"link": note["url"], "text": note["url"]},
        "抓取日期": datetime.now(CN_TZ).strftime("%Y-%m-%d"),
    }


def build_feishu_record_for_generated(note: dict, idx: int) -> dict:
    """仿写笔记入库字段。"""
    return {
        "类型": "仿写产出",
        "标题": note.get("title", ""),
        "正文": note.get("content", ""),
        "Tags": " ".join(note.get("tags", [])),
        "钩子": note.get("hook_used", ""),
        "结构": note.get("structure_used", ""),
        "序号": idx,
        "抓取日期": datetime.now(CN_TZ).strftime("%Y-%m-%d"),
    }


async def run() -> int:
    cfg = load_config()
    xhs = cfg["xiaohongshu"]
    gen = cfg["generation"]
    fs = cfg["feishu"]

    scrape_cfg = ScrapeConfig(
        keywords=xhs["keywords"],
        per_keyword_limit=xhs["per_keyword_limit"],
        recent_hours=xhs["recent_hours"],
        max_fans=xhs["max_fans"],
        min_likes=xhs["viral_thresholds"]["min_likes"],
        min_interactions=xhs["viral_thresholds"]["min_interactions"],
        top_n=xhs["top_n"],
    )

    cookies_path = ensure_cookies()
    print(f"[1/4] 开始抓取小红书爆款笔记，关键词: {scrape_cfg.keywords}")
    viral_notes = await scrape(scrape_cfg, cookies_path, headless=True)
    print(f"      抓到 {len(viral_notes)} 条符合『低粉爆款』条件的笔记")

    today = datetime.now(CN_TZ).strftime("%Y%m%d")
    (ROOT / "data" / f"viral_{today}.json").write_text(
        json.dumps(viral_notes, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    if not viral_notes:
        print("      今日无符合条件的爆款笔记，流程结束。")
        return 0

    anthropic = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    print("[2/4] 调用 Claude 分析爆款框架...")
    frames = analyze_viral_frames(viral_notes, anthropic, gen["model"])
    (ROOT / "data" / f"frames_{today}.json").write_text(
        json.dumps(frames, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"      框架提炼完成，summary: {frames.get('summary', '')[:80]}")

    print(f"[3/4] 按框架仿写 {gen['count']} 篇笔记...")
    generated = generate_notes(
        frames, viral_notes, gen["count"], anthropic, gen["model"], gen["max_tokens"]
    )
    (ROOT / "data" / f"generated_{today}.json").write_text(
        json.dumps(generated, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"      生成 {len(generated)} 篇仿写笔记")

    print("[4/4] 写入飞书多维表格...")
    feishu = FeishuClient(
        app_id=os.environ["FEISHU_APP_ID"],
        app_secret=os.environ["FEISHU_APP_SECRET"],
    )
    records = [build_feishu_record_for_viral(n) for n in viral_notes]
    records += [build_feishu_record_for_generated(n, i + 1) for i, n in enumerate(generated)]
    written = feishu.batch_create(fs["app_token"], fs["table_id"], records)
    print(f"      飞书写入完成: {written} 条")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(run()))
