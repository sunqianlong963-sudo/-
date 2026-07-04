#!/bin/bash
# 用法: bash 发飞书.sh "消息内容"
# 把下面的 WEBHOOK 换成你自己群机器人的地址

WEBHOOK="https://open.feishu.cn/open-apis/bot/v2/hook/替换成你的地址"

MSG="$1"
if [ -z "$MSG" ]; then
  echo "用法: bash 发飞书.sh \"消息内容\""
  exit 1
fi

curl -s -X POST "$WEBHOOK" \
  -H "Content-Type: application/json" \
  -d "{\"msg_type\":\"text\",\"content\":{\"text\":\"$MSG\"}}"

echo ""
echo "已发送 ✅"
