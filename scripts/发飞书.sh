#!/bin/bash
# 飞书自定义机器人 - 发送文本消息
# 用法: bash scripts/发飞书.sh "要发送的消息内容"

set -e

WEBHOOK="请把这里替换成你的飞书机器人Webhook地址"

MESSAGE="${1:?用法: bash scripts/发飞书.sh \"消息内容\"}"

if [ "$WEBHOOK" = "请把这里替换成你的飞书机器人Webhook地址" ]; then
  echo "错误：请先在脚本里把 WEBHOOK 换成你的飞书机器人 Webhook 地址" >&2
  exit 1
fi

PAYLOAD=$(python3 -c 'import json,sys; print(json.dumps({"msg_type":"text","content":{"text":sys.argv[1]}}))' "$MESSAGE")

curl -sS -X POST "$WEBHOOK" -H "Content-Type: application/json" -d "$PAYLOAD"
echo
