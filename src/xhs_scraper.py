"""小红书爆款笔记抓取器（基于 Playwright + 已登录 cookie）。

输出统一结构：
{
  "note_id": str, "title": str, "desc": str, "url": str,
  "author": {"user_id": str, "nickname": str, "fans": int},
  "stats": {"likes": int, "collects": int, "comments": int, "shares": int},
  "published_at": ISO8601 str,
  "cover": str, "tags": [str]
}
"""

from __future__ import annotations

import asyncio
import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from playwright.async_api import BrowserContext, Page, async_playwright

CN_TZ = timezone(timedelta(hours=8))
SEARCH_URL = "https://www.xiaohongshu.com/search_result?keyword={kw}&source=web_explore_feed"


@dataclass
class ScrapeConfig:
    keywords: list[str]
    per_keyword_limit: int
    recent_hours: int
    max_fans: int
    min_likes: int
    min_interactions: int
    top_n: int


def _parse_count(text: str | int | None) -> int:
    if text is None:
        return 0
    if isinstance(text, int):
        return text
    s = str(text).strip().replace(",", "")
    if not s or s == "-":
        return 0
    m = re.match(r"([\d.]+)\s*(万|w|W|k|K)?", s)
    if not m:
        try:
            return int(float(s))
        except ValueError:
            return 0
    num = float(m.group(1))
    unit = (m.group(2) or "").lower()
    if unit in ("万", "w"):
        num *= 10000
    elif unit == "k":
        num *= 1000
    return int(num)


def _parse_relative_time(text: str, now: datetime) -> datetime | None:
    """把『3小时前』『昨天 12:00』『05-26』之类的文本解析为 datetime。"""
    if not text:
        return None
    text = text.strip()
    if "分钟前" in text:
        n = int(re.search(r"(\d+)", text).group(1))
        return now - timedelta(minutes=n)
    if "小时前" in text:
        n = int(re.search(r"(\d+)", text).group(1))
        return now - timedelta(hours=n)
    if "昨天" in text:
        return (now - timedelta(days=1)).replace(hour=12, minute=0, second=0, microsecond=0)
    if "天前" in text:
        n = int(re.search(r"(\d+)", text).group(1))
        return now - timedelta(days=n)
    m = re.match(r"(\d{1,2})-(\d{1,2})", text)
    if m:
        month, day = int(m.group(1)), int(m.group(2))
        return now.replace(month=month, day=day, hour=12, minute=0, second=0, microsecond=0)
    m = re.match(r"(\d{4})-(\d{1,2})-(\d{1,2})", text)
    if m:
        return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), 12, tzinfo=now.tzinfo)
    return None


async def _load_cookies(context: BrowserContext, cookies_path: Path) -> None:
    if not cookies_path.exists():
        raise FileNotFoundError(
            f"未找到小红书 cookies 文件: {cookies_path}. "
            "请先在本地登录小红书后用浏览器扩展导出 cookies.json。"
        )
    cookies = json.loads(cookies_path.read_text(encoding="utf-8"))
    # 兼容 EditThisCookie 等扩展导出的字段
    for c in cookies:
        if "sameSite" in c and c["sameSite"] not in ("Strict", "Lax", "None"):
            c["sameSite"] = "Lax"
        c.pop("hostOnly", None)
        c.pop("session", None)
        c.pop("storeId", None)
    await context.add_cookies(cookies)


async def _search_keyword(page: Page, keyword: str, limit: int) -> list[dict[str, Any]]:
    """打开搜索页，滚动收集笔记卡片。"""
    await page.goto(SEARCH_URL.format(kw=keyword), wait_until="domcontentloaded")
    await page.wait_for_selector("section.note-item, a.cover", timeout=15_000)

    seen: set[str] = set()
    notes: list[dict[str, Any]] = []
    for _ in range(20):
        cards = await page.query_selector_all("section.note-item")
        for card in cards:
            link = await card.query_selector("a.cover")
            if not link:
                continue
            href = await link.get_attribute("href") or ""
            m = re.search(r"/explore/([0-9a-f]+)", href) or re.search(r"/discovery/item/([0-9a-f]+)", href)
            if not m:
                continue
            note_id = m.group(1)
            if note_id in seen:
                continue
            seen.add(note_id)

            title_el = await card.query_selector(".title, .footer .title")
            title = (await title_el.inner_text()) if title_el else ""

            author_el = await card.query_selector(".author .name, .author-wrapper .name")
            author = (await author_el.inner_text()) if author_el else ""

            like_el = await card.query_selector(".like-wrapper .count, .interaction .count")
            likes = _parse_count(await like_el.inner_text() if like_el else "0")

            cover_el = await card.query_selector("img")
            cover = (await cover_el.get_attribute("src")) if cover_el else ""

            notes.append({
                "note_id": note_id,
                "url": f"https://www.xiaohongshu.com/explore/{note_id}",
                "title": title.strip(),
                "author_name": author.strip(),
                "likes_card": likes,
                "cover": cover,
            })
            if len(notes) >= limit:
                return notes
        await page.mouse.wheel(0, 2400)
        await asyncio.sleep(1.2)
    return notes


async def _enrich_note(page: Page, note: dict[str, Any], now: datetime) -> dict[str, Any] | None:
    """打开笔记详情页，补全粉丝数、互动数、发布时间、正文、tag。"""
    try:
        await page.goto(note["url"], wait_until="domcontentloaded", timeout=20_000)
        await page.wait_for_selector(".note-content, #detail-desc", timeout=10_000)
    except Exception:
        return None

    async def text(sel: str) -> str:
        el = await page.query_selector(sel)
        return (await el.inner_text()).strip() if el else ""

    title = await text("#detail-title, .title") or note.get("title", "")
    desc = await text("#detail-desc, .desc")

    likes = _parse_count(await text(".like-wrapper .count, .like-active .count"))
    collects = _parse_count(await text(".collect-wrapper .count"))
    comments = _parse_count(await text(".chat-wrapper .count, .comments-container .total"))

    publish_text = await text(".date, .bottom-container .date")
    published_at = _parse_relative_time(publish_text, now)

    author_link = await page.query_selector(".author-wrapper a.name, .author a")
    user_id = ""
    nickname = note.get("author_name", "")
    if author_link:
        href = await author_link.get_attribute("href") or ""
        m = re.search(r"/user/profile/([0-9a-f]+)", href)
        if m:
            user_id = m.group(1)
        nickname = (await author_link.inner_text()).strip() or nickname

    fans = 0
    if user_id:
        try:
            await page.goto(f"https://www.xiaohongshu.com/user/profile/{user_id}",
                            wait_until="domcontentloaded", timeout=15_000)
            await page.wait_for_selector(".user-info, .info", timeout=8_000)
            fans_text = await text(".user-info .data-info:has-text('粉丝') .count, "
                                   ".info .data-info:nth-child(2) .count")
            fans = _parse_count(fans_text)
        except Exception:
            fans = 0

    tag_els = await page.query_selector_all("a.tag, .tag-item")
    tags = [(await t.inner_text()).strip().lstrip("#") for t in tag_els if t]

    return {
        "note_id": note["note_id"],
        "title": title,
        "desc": desc,
        "url": note["url"],
        "cover": note.get("cover", ""),
        "tags": [t for t in tags if t],
        "author": {"user_id": user_id, "nickname": nickname, "fans": fans},
        "stats": {
            "likes": likes,
            "collects": collects,
            "comments": comments,
            "shares": 0,
            "interactions": likes + collects + comments,
        },
        "published_at": published_at.isoformat() if published_at else None,
    }


def _is_viral(note: dict[str, Any], cfg: ScrapeConfig, now: datetime) -> bool:
    if not note:
        return False
    author = note.get("author", {})
    stats = note.get("stats", {})
    if author.get("fans", 0) > cfg.max_fans:
        return False
    pub = note.get("published_at")
    if not pub:
        return False
    pub_dt = datetime.fromisoformat(pub)
    if (now - pub_dt) > timedelta(hours=cfg.recent_hours):
        return False
    if stats.get("likes", 0) >= cfg.min_likes:
        return True
    if stats.get("interactions", 0) >= cfg.min_interactions:
        return True
    return False


async def scrape(cfg: ScrapeConfig, cookies_path: Path, headless: bool = True) -> list[dict[str, Any]]:
    now = datetime.now(CN_TZ)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless, args=["--disable-blink-features=AutomationControlled"])
        context = await browser.new_context(
            user_agent=("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/126.0.0.0 Safari/537.36"),
            viewport={"width": 1440, "height": 900},
            locale="zh-CN",
        )
        await _load_cookies(context, cookies_path)
        page = await context.new_page()

        candidates: list[dict[str, Any]] = []
        for kw in cfg.keywords:
            try:
                got = await _search_keyword(page, kw, cfg.per_keyword_limit)
                candidates.extend(got)
            except Exception as exc:
                print(f"[scrape] 关键词 '{kw}' 抓取失败: {exc}")

        seen_ids: set[str] = set()
        unique = []
        for n in candidates:
            if n["note_id"] in seen_ids:
                continue
            seen_ids.add(n["note_id"])
            unique.append(n)

        enriched: list[dict[str, Any]] = []
        for n in unique:
            full = await _enrich_note(page, n, now)
            if full and _is_viral(full, cfg, now):
                enriched.append(full)

        await browser.close()

    enriched.sort(key=lambda x: x["stats"]["interactions"], reverse=True)
    return enriched[: cfg.top_n]
