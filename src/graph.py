"""流程编排：提供 LangGraph 状态图版本 与 纯 Python 串行版本两种入口。

- build_graph：LangGraph StateGraph，展示多Agent编排能力
- run_serial：不依赖 LangGraph 的兜底串行实现，保证无额外依赖也能跑
"""
from typing import Dict
from .llm import LLMClient
from . import nodes


def build_graph():
    """LangGraph 状态图：classify → experts → jury → debate → verdict。"""
    from langgraph.graph import StateGraph, END

    llm = LLMClient()

    async def _experts(state): return await nodes.run_experts(state, llm)
    async def _jury(state): return await nodes.run_jury(state, llm)
    async def _debate(state): return await nodes.run_debate(state, llm)

    g = StateGraph(dict)
    g.add_node("classify", nodes.classify_input)
    g.add_node("experts", _experts)
    g.add_node("jury", _jury)
    g.add_node("debate", _debate)
    g.add_node("verdict", nodes.run_verdict)
    g.set_entry_point("classify")
    g.add_edge("classify", "experts")
    g.add_edge("experts", "jury")
    g.add_edge("jury", "debate")
    g.add_edge("debate", "verdict")
    g.add_edge("verdict", END)
    return g.compile()


async def run_serial(user_input: str) -> Dict:
    """纯 Python 串行兜底实现，不依赖 LangGraph。"""
    llm = LLMClient()
    state: Dict = {"user_input": user_input}
    state.update(nodes.classify_input(user_input))
    state = await nodes.run_experts(state, llm)
    state = await nodes.run_jury(state, llm)
    state = await nodes.run_debate(state, llm)
    state = nodes.run_verdict(state)
    return state
