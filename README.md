# 小红书「演讲口才」爆款抓取 + Claude 仿写 + 飞书同步

每天北京时间 **07:00** 自动执行：

1. 抓取小红书「演讲/口才/表达」赛道近 24 小时的**低粉爆款**笔记（粉丝 ≤ 5000，互动 ≥ 阈值）
2. 用 Claude 提炼共性的「爆款框架」（钩子 / 结构 / 标题套路 / tag）
3. 按框架仿写 **10 篇**原创笔记
4. 把「爆款样本 + 仿写产出」批量写入你的**飞书多维表格**

整套流程通过 GitHub Actions 调度，完全免费。

---

## 一次性配置（约 15 分钟）

### 1. 准备小红书 cookies

> 小红书没有公开 API，抓取依赖你**已登录账号的 cookie**。

1. Chrome 安装扩展 [EditThisCookie](https://chrome.google.com/webstore/detail/editthiscookie/) 或 [Cookie-Editor](https://cookie-editor.com/)
2. 登录 https://www.xiaohongshu.com
3. 打开任意页面，点击扩展图标 → **Export → JSON**
4. 保存得到的 JSON 文本，下一步要粘进 GitHub Secrets

> ⚠️ Cookie 一般 1–3 个月失效，失效后重复以上步骤更新 Secret。

### 2. 准备飞书多维表格

1. 打开飞书 → 新建一份**多维表格**，添加下列字段（字段名严格一致）：

| 字段名 | 字段类型 |
|---|---|
| 类型 | 单选（选项：爆款样本 / 仿写产出） |
| 标题 | 多行文本 |
| 正文 | 多行文本 |
| 作者 | 文本 |
| 粉丝数 | 数字 |
| 点赞 | 数字 |
| 收藏 | 数字 |
| 评论 | 数字 |
| 互动总数 | 数字 |
| 发布时间 | 文本 |
| 链接 | 超链接 |
| Tags | 多行文本 |
| 钩子 | 文本 |
| 结构 | 文本 |
| 序号 | 数字 |
| 抓取日期 | 文本 |

2. 从表格 URL 取出两个 ID：
   - URL 形如 `https://xxx.feishu.cn/base/<APP_TOKEN>?table=<TABLE_ID>&view=...`
   - 记下 `<APP_TOKEN>` 和 `<TABLE_ID>`

3. 创建一个**飞书自建应用**：
   - 进入 https://open.feishu.cn → 开发者后台 → 创建企业自建应用
   - 在「权限管理」中开启：`bitable:app`（多维表格读写权限）
   - 发布版本（务必走完审批和发布流程）
   - 在多维表格右上角「...」→「更多」→「添加文档应用」，把你刚创建的应用加进来
   - 记下「凭证与基础信息」里的 **App ID** 和 **App Secret**

### 3. 填写仓库配置

把 `config/config.example.yaml` 复制为 `config/config.yaml`，把飞书表格的 `app_token` 和 `table_id` 填进去（其他默认值已能直接跑）：

```bash
cp config/config.example.yaml config/config.yaml
# 编辑 app_token、table_id；可按需调整关键词、阈值
git add config/config.yaml && git commit -m "config: fill feishu ids"
```

> 注意：`config/cookies.json` 已被 `.gitignore` 忽略，绝不会进仓库。

### 4. 在 GitHub Secrets 里填入凭证

仓库 → Settings → Secrets and variables → Actions → New repository secret，添加 **4 个**：

| Name | Value |
|---|---|
| `ANTHROPIC_API_KEY` | 你的 Claude API Key（https://console.anthropic.com） |
| `FEISHU_APP_ID` | 上一步拿到的飞书 App ID |
| `FEISHU_APP_SECRET` | 上一步拿到的飞书 App Secret |
| `XHS_COOKIES_JSON` | 第 1 步导出的 cookies JSON **全文** |

---

## 启动

- **手动跑一次（推荐先试一次）**：仓库 → Actions → 选择「小红书演讲口才爆款日抓 ...」→ Run workflow
- **每日自动运行**：workflow 已配置 cron `0 23 * * *`（UTC），即北京时间 07:00 自动触发

执行结束后：
- 飞书多维表格里会新增 ≤15 条「爆款样本」 + 10 条「仿写产出」
- 当日数据快照保存在 Actions 的 Artifacts 里（保留 14 天，便于排查）

---

## 本地调试

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium

# 把 cookies.json 放到 config/，把 config.yaml 填好
export ANTHROPIC_API_KEY=sk-ant-...
export FEISHU_APP_ID=cli_...
export FEISHU_APP_SECRET=...
python -m src.main
```

排查抓取问题时把 `src/main.py` 里 `headless=True` 改成 `False`，可以肉眼看浏览器行为。

---

## 目录结构

```
.
├── .github/workflows/daily.yml   # GitHub Actions 日定时任务
├── config/
│   ├── config.example.yaml       # 配置模板（关键词、阈值、飞书 ID）
│   └── cookies.json              # 小红书 cookie（gitignore，本地用）
├── prompts/
│   ├── analyze.txt               # 爆款框架分析 prompt
│   └── generate.txt              # 仿写 prompt
├── src/
│   ├── xhs_scraper.py            # Playwright 抓取 + 爆款筛选
│   ├── analyzer.py               # Claude 框架分析
│   ├── generator.py              # Claude 仿写
│   ├── feishu_client.py          # 飞书多维表格 API
│   └── main.py                   # 主流程
├── data/                         # 每日 JSON 快照（gitignore）
├── requirements.txt
└── README.md
```

---

## 常见问题

**Q: 跑完发现『未找到符合条件的笔记』。**
A: 把 `config/config.yaml` 中 `viral_thresholds.min_likes` / `min_interactions` 调低，或扩大 `recent_hours` 到 48 小时。

**Q: 报错 `未找到 cookies` / 抓到 0 条。**
A: cookie 失效了，重新导出并更新 `XHS_COOKIES_JSON` Secret。

**Q: 飞书写入报 `99991663` 错误。**
A: 没在多维表格里把应用加为「可编辑」协作者，或 `bitable:app` 权限未开通。

**Q: 想换主题（不止演讲口才）。**
A: 改 `config/config.yaml` 里的 `keywords` 列表即可，其他逻辑通用。
