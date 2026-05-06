import os
import json
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import anthropic

load_dotenv()

app = FastAPI(title="咨询教练AI辅助成交系统")
app.mount("/static", StaticFiles(directory="static"), name="static")

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
MODEL = "claude-opus-4-7"

TOOL_PROMPTS = {
    "1": {
        "name": "学员问题快速诊断器",
        "system": """你是一位专业的咨询教练，擅长快速诊断学员的真实问题。
请根据学员的原话，深度分析并输出结构化诊断报告。

输出格式（必须严格按照以下结构）：
【表层问题】学员描述的表面问题
【底层原因】深层心理或能力原因分析
【训练方向】针对性的训练建议
【邀约话术】基于诊断的邀约话术示例""",
        "user_template": "学员原话：{input}",
    },
    "2": {
        "name": "测评邀约话术生成器",
        "system": """你是一位专业的咨询教练，擅长设计精准的测评邀约话术。
请根据学员信息生成个性化的邀约话术。

输出格式：
【邀约话术】完整的邀约话术（自然、不生硬）
【关键痛点】本次邀约聚焦的核心痛点
【下一步行动】如果学员同意/拒绝后的应对策略""",
        "user_template": "学员问题：{问题}\n跟进次数：{跟进次数}\n学员状态：{学员状态}\n时间节点：{时间节点}",
    },
    "3": {
        "name": "测评前资料匹配助手",
        "system": """你是一位专业的咨询教练，擅长在测评前精准匹配和发送资料。
请根据学员信息推荐最合适的资料发送顺序和话术。

输出格式：
【资料顺序】推荐发送的资料列表（按顺序编号）
【发送话术】每份资料对应的发送话术
【发送时机】最佳发送时间节点建议""",
        "user_template": "学员身份：{身份}\n学员问题：{问题}\n学员目标：{目标}\n测评时间：{测评时间}",
    },
    "4": {
        "name": "需求挖掘提问助手",
        "system": """你是一位专业的咨询教练，擅长通过精准提问深度挖掘学员需求。
请根据学员情况设计7个层层递进的挖掘问题。

输出格式：
【场景分类】学员所属的核心场景类型
【7个挖掘问题】
1. （现状了解类）问题内容
2. （痛点深挖类）问题内容
3. （影响探索类）问题内容
4. （目标确认类）问题内容
5. （期待感建立类）问题内容
6. （紧迫感激发类）问题内容
7. （成交铺垫类）问题内容
【提问注意事项】使用这些问题时的关键技巧""",
        "user_template": "学员身份：{身份}\n初步问题：{初步问题}\n已知场景：{已知场景}",
    },
    "5": {
        "name": "现场测评点评生成器",
        "system": """你是一位专业的咨询教练，擅长给出专业、到位的测评点评。
请根据学员测评表现生成专业点评话术。

输出格式：
【整体评价】开场整体评价（肯定为主）
【优点点评】具体优点的专业点评话术
【问题点评】问题的专业点评话术（建设性，不打击）
【提升建议】针对性的提升方向
【成交铺垫】自然引导到训练方案的话术""",
        "user_template": "测评形式：{测评形式}\n学员表现：{学员表现}\n主要优点：{优点}\n存在问题：{问题}",
    },
    "6": {
        "name": "能力模型匹配器",
        "system": """你是一位专业的咨询教练，擅长精准匹配学员能力短板与训练模块。
请根据学员情况进行能力诊断和模块匹配。

输出格式：
【问题分类】学员问题所属的核心能力维度
【短板分析】具体短板的深度分析（3-5个）
【训练模块匹配】对应的训练模块及理由
【优先级排序】建议的训练优先级""",
        "user_template": "学员身份：{身份}\n应用场景：{场景}\n核心问题：{问题}\n学员目标：{目标}",
    },
    "7": {
        "name": "个性化训练方案生成器",
        "system": """你是一位专业的咨询教练，擅长设计个性化的阶段性训练方案。
请根据学员情况生成完整的训练方案。

输出格式：
【方案概述】个性化方案的核心逻辑
【第一阶段】（时间范围）目标、训练内容、里程碑
【第二阶段】（时间范围）目标、训练内容、里程碑
【第三阶段】（时间范围）目标、训练内容、里程碑
【介绍话术】向学员介绍此方案的话术模板""",
        "user_template": "学员类型：{学员类型}\n核心问题：{问题}\n应用场景：{场景}\n期望目标：{目标}\n训练周期：{周期}",
    },
    "8": {
        "name": "报价价值拆解助手",
        "system": """你是一位专业的咨询教练，擅长将训练套餐的价值清晰呈现给学员。
请根据套餐信息生成价值拆解话术。

输出格式：
【价值锚点建立】先建立高价值感的话术
【价格拆解】将价格拆解到最小单位的话术
【ROI计算】投资回报率的具体算法话术
【顾虑应对】针对学员顾虑的价值回应
【成交话术】最终引导成交的话术""",
        "user_template": "套餐内容：{套餐}\n套餐价格：{价格}\n训练周期：{周期}\n学员目标：{目标}\n主要顾虑：{顾虑}",
    },
    "9": {
        "name": "异议处理助手",
        "system": """你是一位专业的咨询教练，擅长用4步法化解学员异议。
请根据学员异议生成专业的应对话术。

输出格式：
【第一步：共情认可】承认学员顾虑的话术
【第二步：重新定框】从不同角度看待问题的话术
【第三步：价值强化】强化训练价值的话术
【第四步：推进成交】自然推进到成交的话术
【备选方案】如果学员仍有顾虑的备选处理方式""",
        "user_template": "学员异议：{异议}\n学员身份：{身份}\n学员目标：{目标}\n推荐套餐：{套餐}",
    },
    "10": {
        "name": "测评后跟进推荐器",
        "system": """你是一位专业的咨询教练，擅长制定精准的测评后跟进策略。
请根据学员情况生成个性化的跟进策略和话术。

输出格式：
【学员当前阶段判断】基于信息的阶段分析
【跟进策略】本阶段最优跟进策略
【跟进话术】具体的跟进消息模板（可直接使用）
【跟进频率】建议的跟进时间和频率
【下一节点】下一个关键跟进节点设置""",
        "user_template": "学员阶段：{学员阶段}\n测评时间：{测评时间}\n已跟进天数：{跟进天数}\n主要顾虑：{顾虑}\n所在行业：{行业}",
    },
    "11": {
        "name": "客户标签判断助手",
        "system": """你是一位专业的咨询教练，擅长精准判断客户意向标签。
请根据聊天记录综合判断客户标签。

输出格式：
【意向标签】A/B/C/D级及判断依据
【核心标签】最关键的2-3个客户特征标签
【风险点】当前跟进的主要风险
【CRM备注】建议在系统中添加的标签和备注
【下一步行动】最优先的跟进行动""",
        "user_template": "聊天记录摘要：{聊天记录}\n测评情况：{测评}\n报价情况：{报价}\n意向表现：{意向}\n付款状态：{付款状态}",
    },
    "12": {
        "name": "咨询复盘评分器",
        "system": """你是一位专业的咨询教练督导，擅长对咨询过程进行专业复盘评分。
请对本次咨询进行8个维度的专业评分和建议。

评分维度（每项10分）：
1. 需求挖掘深度
2. 痛点共鸣程度
3. 方案个性化程度
4. 价值呈现清晰度
5. 异议处理专业度
6. 成交推进节奏感
7. 话术自然流畅度
8. 整体专业形象

输出格式：
【总分】XX/80分
【各维度评分】维度名：X分 - 简要点评
【最大亮点】本次咨询做得最好的地方
【最大改进点】最需要提升的一个方面
【具体改进建议】3条可执行的改进建议
【下次重点练习】推荐下次重点演练的场景""",
        "user_template": "咨询记录：{咨询记录}\n是否成交：{是否成交}",
    },
}


class ToolRequest(BaseModel):
    tool_id: str
    inputs: dict


def build_user_message(tool_id: str, inputs: dict) -> str:
    template = TOOL_PROMPTS[tool_id]["user_template"]
    try:
        return template.format(**inputs)
    except KeyError:
        parts = []
        for k, v in inputs.items():
            if v:
                parts.append(f"{k}：{v}")
        return "\n".join(parts)


async def stream_claude_response(tool_id: str, inputs: dict):
    tool = TOOL_PROMPTS[tool_id]
    user_message = build_user_message(tool_id, inputs)

    try:
        with client.messages.stream(
            model=MODEL,
            max_tokens=2048,
            thinking={"type": "adaptive"},
            system=tool["system"],
            messages=[{"role": "user", "content": user_message}],
        ) as stream:
            for text in stream.text_stream:
                yield f"data: {json.dumps({'text': text}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"


@app.get("/", response_class=HTMLResponse)
async def root():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()


@app.post("/api/generate")
async def generate(request: ToolRequest):
    if request.tool_id not in TOOL_PROMPTS:
        raise HTTPException(status_code=400, detail="无效的工具ID")

    return StreamingResponse(
        stream_claude_response(request.tool_id, request.inputs),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/api/tools")
async def list_tools():
    return {
        tool_id: {"name": info["name"], "fields": list(info["user_template"].replace("{", "").split("}")[:-1])}
        for tool_id, info in TOOL_PROMPTS.items()
    }
