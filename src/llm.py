"""LLM 客户端封装：支持 OpenAI 兼容 API 与 Mock 两种模式。

- 配置了 OPENAI_API_KEY：走真实模型调用
- 未配置：返回 Mock 响应，让整套流程在无外部依赖时也能跑通演示
"""
import asyncio
from typing import List, Dict
from . import config


class LLMClient:
    """极简 LLM 封装，按消息列表返回文本。"""

    def __init__(self, model: str = None):
        self.model = model or config.MODEL
        self.mock = config.is_mock()
        self._real = None
        if not self.mock:
            from openai import AsyncOpenAI
            self._real = AsyncOpenAI(api_key=config.OPENAI_API_KEY, base_url=config.API_BASE_URL)

    async def complete(self, messages: List[Dict[str, str]], max_tokens: int = 600, temperature: float = 0.7) -> str:
        """给定 messages（含 system/user/assistant），返回模型回复文本。"""
        if self.mock:
            return self._mock_reply(messages)
        resp = await self._real.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return resp.choices[0].message.content or ""

    def _mock_reply(self, messages: List[Dict[str, str]]) -> str:
        """Mock 回复：从 system 里的角色标识抽取要点，给出中性判断文本。"""
        system = next((m["content"] for m in messages if m["role"] == "system"), "")
        user = next((m["content"] for m in messages if m["role"] == "user"), "")
        role = _extract_role(system)
        # 精简演示用：返回结构化、可被裁决规则消费的文本
        return (
            f"[{role}·Mock] 对『{user[:40]}』的中立举证：\n"
            f"- 需求真伪度：7/10（存在真实使用场景）\n"
            f"- 付费意愿：6/10（目标用户有一定付费/留存可能）\n"
            f"- 结论：该产品更接近【痛点】，但需注意竞品替代与留存。"
        )

    async def complete_parallel(self, jobs: List[Dict[str, str]]) -> List[str]:
        """并行执行多个单轮对话（消费群体子Agent隔离派发用）。"""
        return await asyncio.gather(*(self.complete(j["messages"], **j.get("kwargs", {})) for j in jobs))


def _extract_role(system: str) -> str:
    """从 system prompt 中粗略提取角色标识（取第一行，去除标记）。"""
    line = system.strip().splitlines()[0] if system.strip() else "judge"
    return line.lstrip("# ").strip()[:20]
