# -*- coding: utf-8 -*-
"""
跟进提醒生成器
================
作用：读取「线索管理/线索表模板.csv」，根据每条线索的状态和"最后联系日期"，
     自动算出今天该跟进谁、该用第几档话术，并生成一份全中文的待办清单。

为什么有用：获客最大的浪费就是"线索来了没人跟"。这个脚本每天帮你把
          "该跟进的人"挑出来排好序，你只管照着说就行。

怎么用（你不懂代码也能用）：
  方式一：让 Claude 帮你运行，把结果直接发给你。
  方式二：在电脑上双击运行（需先装 Python），结果会显示在屏幕上，
         同时存成「跟进清单_日期.md」文件。
  方式三：用 GitHub Actions 设成每天早上定时自动跑（见 docs/落地方案.md）。

不需要联网，不依赖任何第三方库，只用 Python 自带功能。
"""

import csv
import os
import sys
from datetime import date, datetime

# ============ 可调参数 ============
# 各档跟进的"距上次联系天数"门槛
跟进规则 = [
    {"最少天数": 14, "档位": "第3次跟进（给台阶/转长期培育）"},
    {"最少天数": 7, "档位": "第2次跟进（带新干货）"},
    {"最少天数": 2, "档位": "第1次跟进（轻提醒）"},
]
# 哪些状态需要跟进（"已成交""长期培育"不主动催）
需要跟进的状态 = {"待跟进", "已联系未成交"}
# ==================================


def 解析日期(文本):
    """把 CSV 里的日期字符串转成 date 对象，容错处理。"""
    文本 = (文本 or "").strip()
    for 格式 in ("%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(文本, 格式).date()
        except ValueError:
            continue
    return None


def 判断档位(天数):
    """根据距上次联系的天数，返回该用第几档话术；不到门槛返回 None。"""
    for 规则 in 跟进规则:  # 规则已按天数从大到小排列
        if 天数 >= 规则["最少天数"]:
            return 规则["档位"]
    return None


def 生成提醒(csv路径, 今天=None):
    今天 = 今天 or date.today()
    提醒列表 = []

    with open(csv路径, encoding="utf-8") as f:
        for 行 in csv.DictReader(f):
            状态 = (行.get("线索状态") or "").strip()
            if 状态 not in 需要跟进的状态:
                continue

            最后联系 = 解析日期(行.get("最后联系日期"))
            if 最后联系 is None:
                continue

            天数 = (今天 - 最后联系).days
            档位 = 判断档位(天数)
            if 档位 is None:
                continue  # 还没到该跟进的时候

            提醒列表.append({
                "昵称": (行.get("昵称") or "未知").strip(),
                "平台": (行.get("来源平台") or "").strip(),
                "联系方式": (行.get("联系方式") or "").strip(),
                "意向": (行.get("意向标签") or "").strip(),
                "天数": 天数,
                "档位": 档位,
                "备注": (行.get("备注") or "").strip(),
            })

    # 拖得越久越靠前
    提醒列表.sort(key=lambda x: x["天数"], reverse=True)
    return 提醒列表


def 渲染为文本(提醒列表, 今天=None):
    今天 = 今天 or date.today()
    if not 提醒列表:
        return f"# 📋 跟进清单（{今天}）\n\n今天没有需要跟进的线索，棒棒哒～继续产内容吧！💪\n"

    行 = [f"# 📋 跟进清单（{今天}）", "",
          f"今天共有 **{len(提醒列表)}** 条线索需要跟进，按紧急度排好序了👇", ""]
    for i, 条 in enumerate(提醒列表, 1):
        行.append(f"## {i}. {条['昵称']}（{条['平台']}｜{条['意向']}）")
        行.append(f"- ⏰ 距上次联系 **{条['天数']} 天**")
        行.append(f"- 💬 建议话术：**{条['档位']}** → 见 `templates/互动话术与跟进提醒.md`")
        if 条["联系方式"]:
            行.append(f"- 📲 联系方式：{条['联系方式']}")
        if 条["备注"]:
            行.append(f"- 📝 需求摘要：{条['备注']}")
        行.append("")
    行.append("> 跟进原则：给价值 > 催成交。每次带点新东西（资料/案例），别只问\"考虑得怎样\"。")
    return "\n".join(行)


def main():
    根目录 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    默认csv = os.path.join(根目录, "线索管理", "线索表模板.csv")
    csv路径 = sys.argv[1] if len(sys.argv) > 1 else 默认csv

    if not os.path.exists(csv路径):
        print(f"❌ 找不到线索表：{csv路径}")
        print("   请先在「线索管理」目录下准备好 CSV 文件。")
        sys.exit(1)

    提醒列表 = 生成提醒(csv路径)
    文本 = 渲染为文本(提醒列表)

    # 1) 打印到屏幕
    print(文本)

    # 2) 存成 markdown 文件，方便存档或发给客户/自己
    输出文件 = os.path.join(根目录, f"跟进清单_{date.today()}.md")
    with open(输出文件, "w", encoding="utf-8") as f:
        f.write(文本)
    print(f"\n（已保存到：{输出文件}）")


if __name__ == "__main__":
    main()
