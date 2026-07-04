#!/bin/bash
# 用法: bash 发飞书.sh "消息内容"
# Webhook 地址按以下顺序查找(仓库是公开的,地址等于群的钥匙,绝不能写死在这个文件里):
#   1. 环境变量 FEISHU_WEBHOOK
#   2. 同目录下的 webhook.txt(已加入 .gitignore,不会被提交)

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WEBHOOK="${FEISHU_WEBHOOK:-}"
if [ -z "$WEBHOOK" ] && [ -f "$SCRIPT_DIR/webhook.txt" ]; then
  WEBHOOK="$(head -n1 "$SCRIPT_DIR/webhook.txt" | tr -d '[:space:]')"
fi
if [ -z "$WEBHOOK" ]; then
  echo "未配置 Webhook ❌ 设置环境变量 FEISHU_WEBHOOK,或把地址写入 scripts/webhook.txt"
  exit 1
fi

MSG="$1"
if [ -z "$MSG" ]; then
  echo "用法: bash 发飞书.sh \"消息内容\""
  exit 1
fi

RESP=$(curl -s -X POST "$WEBHOOK" \
  -H "Content-Type: application/json" \
  -d "{\"msg_type\":\"text\",\"content\":{\"text\":\"$MSG\"}}")

# 只有飞书返回 code:0 才算真的发出去了,不许假装完成
if echo "$RESP" | grep -q '"code":0'; then
  echo "已发送 ✅"
else
  echo "发送失败 ❌ 服务器响应: $RESP"
  exit 1
fi
