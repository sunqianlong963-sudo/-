# 飞书（Lark）MCP 配置说明

本仓库已通过 `.mcp.json` 接入飞书官方 MCP 服务器
[`@larksuiteoapi/lark-mcp`](https://github.com/larksuite/lark-openapi-mcp)，
覆盖能力：**发消息 / 机器人通知、多维表格 Bitable、云文档 Docs、日历 Calendar**。

> ⚠️ 重要：密钥**不写进仓库**，而是通过环境变量 `FEISHU_APP_ID` / `FEISHU_APP_SECRET`
> 注入。请勿把 App Secret 直接提交到 git。

---

## 一、配置内容

`.mcp.json`（仓库根目录）：

```json
{
  "mcpServers": {
    "feishu": {
      "command": "npx",
      "args": [
        "-y",
        "@larksuiteoapi/lark-mcp",
        "mcp",
        "-t",
        "preset.default,preset.im.default,preset.base.default,preset.doc.default,preset.calendar.default"
      ],
      "env": {
        "APP_ID": "${FEISHU_APP_ID}",
        "APP_SECRET": "${FEISHU_APP_SECRET}"
      }
    }
  }
}
```

`-t` 指定加载的工具预设（preset）：

| 预设 | 能力 |
| --- | --- |
| `preset.default` | 常用基础工具（IM + 多维表格 + 文档等精选） |
| `preset.im.default` | 即时消息：发消息、卡片、群管理 |
| `preset.base.default` | 多维表格 Bitable：读写记录、字段、视图 |
| `preset.doc.default` | 云文档 Docs：读写文档内容 |
| `preset.calendar.default` | 日历：日程的增删查改 |

> 审批、通讯录等其它能力可按需追加对应工具 ID 或预设到 `-t` 列表。
> 国际版 Lark 需在 `args` 里追加 `-d https://open.larksuite.com`（默认是飞书中国版 `open.feishu.cn`）。

---

## 二、本地 / 桌面端使用步骤

1. 安装 Node.js 18+（`npx` 随 Node 自带）。
2. 在 shell 中导出环境变量（替换成你自己的凭证）：

   ```bash
   export FEISHU_APP_ID="cli_xxxxxxxxxxxx"
   export FEISHU_APP_SECRET="xxxxxxxxxxxxxxxxxxxxxxxx"
   ```

3. 在该目录启动 Claude Code，MCP 会自动加载名为 `feishu` 的服务器。
4. 用 `/mcp` 命令确认 `feishu` 状态为已连接。

---

## 三、Claude Code 网页版（云环境）使用步骤

网页版的 MCP 在**创建/编辑环境时**配置，按以下方式启用：

1. **网络策略**：确保环境允许访问飞书开放平台域名
   - 飞书中国版：`open.feishu.cn`
   - 国际版 Lark：`open.larksuite.com`
   - 同时允许 `registry.npmjs.org`（首次 `npx` 拉包需要）。
2. **环境变量 / Secret**：在环境设置里添加
   - `FEISHU_APP_ID`
   - `FEISHU_APP_SECRET`
3. 保存后**新开一个会话**，新的 MCP 服务器才会被加载。
4. 文档参考：<https://code.claude.com/docs/en/claude-code-on-the-web>

---

## 四、飞书开放平台需要开通的权限

在 [飞书开放平台](https://open.feishu.cn/app) → 你的自建应用 → **权限管理**，
按用途开通对应权限（scope），然后**发布版本**让权限生效：

- 发消息 / 机器人：`im:message`、`im:message:send_as_bot`
- 多维表格 Bitable：`bitable:app`（读写）
- 云文档 Docs：`docx:document`、`drive:drive`（按需）
- 日历 Calendar：`calendar:calendar`

另外：

- 机器人能发消息前，需在应用「**机器人**」能力中启用，并把机器人加入目标群。
- 给个人发消息需要拿到对方的 `open_id` / `user_id`（通讯录权限或扫码获取）。

---

## 五、验证

环境就绪并新开会话后，可以让 Claude 调用飞书工具，例如：

- “给群里发一条测试消息”
- “读取这张多维表格的前 10 条记录”
- “在我日历上新建一个明天 10 点的日程”
