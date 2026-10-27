"""各流程节点：阶段识别、专家举证、消费群体隔离、两轮辩论、加权裁决。

每个节点为纯异步函数，state 为 dict，可在 LangGraph 中使用。
"""
from typing import Dict, List
from . import config
from .llm import LLMClient
from . import prompts

# ---- 输入阶段识别 ----
def classify_input(user_input: str) -> Dict:
    """识别输入成熟度：想法 / PRD / 成品URL → 可信度。"""
    if user_input.startswith(("http://", "https://")):
        stage, trust = "成品URL", 1.0
    elif any(k in user_input for k in ("背景", "目标", "用户", "功能", "PRD")):
        stage, trust = "PRD", 0.7
    else:
        stage, trust = "想法", 0.4
    return {"stage": stage, "trust": trust}


# ---- 专家举证（主上下文扮演，串行） ----
async def run_experts(state: Dict, llm: LLMClient) -> Dict:
    statements = []
    for name in config.EXPERT_NAMES:
        card = prompts.agent_card(name)
        sys_prompt = f"你是产品/工程/合规/竞品/增长领域的专家。{card}\n\n要求：中立举证，不迎合人类。"
        msgs = [{"role": "system", "content": sys_prompt}, {"role": "user", "content": state["user_input"]}]
        statements.append({"agent": name, "text": await llm.complete(msgs, max_tokens=500)})
    state["expert_statements"] = statements
    return state


# ---- 消费群体隔离派发（并行、独立上下文） ----
async def run_jury(state: Dict, llm: LLMClient) -> Dict:
    picks = config.JURY_POOL[: config.JURY_PICK]  # 简化：取前 N 个，真实可加匹配打分
    jobs = []
    for g in picks:
        card = prompts.consumer_card(g)
        case = prompts.case_library(g)
        sys_prompt = f"你是消费群体『{g}』的代表。{card}\n\n参考案例：{case}\n\n要求：独立发言，输入与其他群体隔离，互不可见。"
        jobs.append({"messages": [{"role": "system", "content": sys_prompt}, {"role": "user", "content": state["user_input"]}], "kwargs": {"max_tokens": 400}})
    results = await llm.complete_parallel(jobs)
    state["jury_statements"] = [{"group": g, "text": t} for g, t in zip(picks, results)]
    return state


# ---- 两轮辩论（最小实现：第2轮仅汇总分歧点） ----
async def run_debate(state: Dict, llm: LLMClient) -> Dict:
    all_evidences = [s["text"] for s in state["expert_statements"]] + [j["text"] for j in state["jury_statements"]]
    sys_prompt = "你是法庭裁判。基于以下双方举证，用一句话指出最大的一个分歧点。"
    msgs = [{"role": "system", "content": sys_prompt}, {"role": "user", "content": "\n---\n".join(all_evidences)}]
    state["key_divergence"] = await llm.complete(msgs, max_tokens=150)
    return state


# ---- 加权裁决 ----
def run_verdict(state: Dict) -> Dict:
    """从举证文本中粗解析评分并加权裁决（骨架版）。"""
    texts = [s["text"] for s in state["expert_statements"]] + [j["text"] for j in state["jury_statements"]]
    scores = [_extract_score(t) for t in texts]
    weighted_total = sum(scores) / len(scores) if scores else 5.0
    # 消费群体权重更高：取 jury 均值作为付费意愿代理指标
    jury_scores = [_extract_score(j["text"]) for j in state["jury_statements"]]
    pay_intent = sum(jury_scores) / len(jury_scores) if jury_scores else 5.0
    weighted_total = config.JURY_WEIGHT * pay_intent + config.EXPERT_WEIGHT * weighted_total
    if weighted_total >= 7.0 and pay_intent >= 6:
        verdict = "痛点"
    elif 4.0 <= weighted_total <= 6.9 or 3 <= pay_intent <= 5:
        verdict = "痒点"
    else:
        verdict = "自嗨"
    state["verdict"] = verdict
    state["weighted_score"] = round(weighted_total, 2)
    state["confidence"] = "中"  # 骨架版：未接真实数据
    return state


def _extract_score(text: str) -> float:
    """从如 '需求真伪度：7/10' 的文本中提取第一个分数。"""
    import re
    m = re.search(r"(\d+(?:\.\d+)?)\s*/", text)
    return float(m.group(1)) if m else 5.0
