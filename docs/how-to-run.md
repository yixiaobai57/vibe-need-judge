# 如何把 vibe-need-judge 接入可运行框架

> 本仓库目前是 **prompt-based skill**（纯结构化 Markdown + 提示词工程），本身不执行代码。
> 本文说明如何把它落地为一个**可运行、可观测的多 Agent 系统**，让面试官看到它不仅是一份设计文档，而是一套可执行的工程方案。

## 一、总体架构（目标形态）

```
用户输入(想法 / PRD / 成品URL)
        │
        ▼
[阶段识别] ── 自动判断输入成熟度 → 决定可信度权重
        │
        ▼
[编排层 LangGraph]  ← 状态机：裁判流程的串行/并行控制
   ├── 5 位专家证人  ← 主图各节点，独立 system prompt（角色卡）
   ├── 消费群体子Agent ← 7 选 2-3，输入隔离、互不可见（并行派发）
   ├── 第1轮独立举证
   ├── 第2轮分歧质询（重派涉分歧子Agent）
   └── 加权裁决 + 生成 11 章报告
        │
        ▼
[模型路由] 按角色成本分配：主流模型跑专家，轻量模型跑消费群体
        │
        ▼
[观测] LangSmith 链路追踪 + token 统计
```

## 二、推荐技术选型（落地最小可行版）

| 组件 | 选型 | 作用 |
| --- | --- | --- |
| 编排框架 | **LangGraph**（Python） | 用 StateGraph 表达两轮辩论状态机，天然支持条件分支与并行 |
| 模型接入 | OpenAI 兼容 SDK（同 ai-agent 仓库） | 多模型热切换，专家/陪审团可分配不同模型 |
| 输入隔离 | 子 Agent 独立会话上下文（隔离 message history） | 保证消费群体互相不可见，实现 README 承诺的独立性 |
| 角色卡 | 复用仓库 `references/agents/*.md` 与 `consumer-groups/*.md` | 作为每个节点的 system prompt |
| 裁决逻辑 | 仓库 `scoring-rubric.md` 的加权规则，落为 Python 函数 | 消费群体60% + 专家40%，动态匹配与降级 |
| 观测 | LangSmith / 简单 token 计数 | 追踪每轮调用与 token 预算（总预算 8000） |
| 输入识别 | 规则或轻量分类 | 想法 / PRD / 成品URL 三态识别 |

## 三、核心实现要点

### 1. 状态图（LangGraph StateGraph）

```python
from langgraph.graph import StateGraph, END

# 节点：
#   classify_input  → 阶段识别
#   spawn_experts   → 派发 5 专家（并行）
#   spawn_jury      → 从候选库动态匹配 2-3 消费群体子Agent（并行、隔离）
#   round1          → 第1轮独立举证
#   round2          → 第2轮分歧质询（只处理 1 个最大分歧点，含降级）
#   verdict         → 加权裁决（规则函数）
#   report          → 生成 11 章报告（复用 templates/verdict-report.md）
```

### 2. 消费群体输入隔离（关键卖点）

```python
# 每个消费群体子Agent 拥有独立 messages 列表，互不共享
jury_sessions = {gid: [] for gid in matched_groups}   # 候选库 7 → 匹配 2-3

# 派发任务时各自携带独立上下文，避免立场泄漏
for gid, history in jury_sessions.items():
    resp = await llm(chunk_group_prompt(agent_card[gid], user_input), history=history)
```

### 3. 加权裁决规则（复用 scoring-rubric.md）

```python
def verdict(pain_intent_mean, weighted_total):
    if weighted_total >= 7.0 and pain_intent_mean >= 6:
        return "痛点"
    if 4.0 <= weighted_total <= 6.9 or 3 <= pain_intent_mean <= 5:
        return "痒点"
    return "自嗨"
```

### 4. token 预算与降级（对应 README 的硬约束）

- 每轮累计 token，达到预算阈值即触发降级：
  1. 专家补证跳过 → 案例库关闭 → 第2轮只处理 1 个分歧点；
  2. 用轻量模型跑消费群体子Agent，主流模型跑专家，控制成本。

## 四、文件落位建议（可在仓库中新建代码骨架）

```
src/
├── graph.py            # LangGraph 状态图定义
├── nodes/
│   ├── classify.py     # 输入阶段识别
│   ├── experts.py      # 5 位专家派发（读 references/agents/*.md）
│   ├── jury.py         # 消费群体匹配与隔离派发
│   ├── debate.py       # 两轮辩论控制
│   └── verdict.py      # 加权裁决
├── prompts/            # 从 references/ 读取角色卡作为 system prompt
├── utils/
│   ├── token_budget.py # 预算控制与降级规则
│   └── observers.py    # LangSmith / token 统计
└── main.py             # CLI 入口：python main.py "<想法/PRD/URL>"
```

## 五、最小可运行示例（骨架）

```python
# main.py（示意，未含完整实现）
from langgraph.graph import StateGraph, END
from nodes import classify, experts, jury, debate, verdict

g = StateGraph(dict)
g.add_node("classify", classify.run)
g.add_node("experts", experts.run)
g.add_node("jury", jury.run)
g.add_node("debate", debate.run)
g.add_node("verdict", verdict.run)
g.set_entry_point("classify")
g.add_edge("classify", "experts")
g.add_edge("experts", "jury")
g.add_edge("jury", "debate")
g.add_edge("debate", "verdict")
g.add_edge("verdict", END)
app = g.compile()

if __name__ == "__main__":
    import sys
    print(app.invoke({"input": sys.argv[1] if len(sys.argv) > 1 else "一个AI写诗鼓励程序员的应用"}))
```

## 六、面试可讲的技术点（从这份设计提炼）

1. **多 Agent 编排**：用 LangGraph 状态机把"独立举证→分歧质询→加权裁决"建模为图，支持并行派发与条件分支。
2. **角色隔离与独立性**：消费群体子Agent 输入隔离、互不可见，用工程手段保证"不迎合人类"。
3. **成本与可控性**：token 预算 8000 + 分级降级规则，从设计到代码都有可量化的成本治理。
4. **评估意识**：tests/ 提供自嗨/痒点/痛点三档端到端用例，可作为回归测试。
5. **可观测**：LangSmith 追踪每轮，报告可复现。

> 落地优先级建议：先做「专家+裁决」串行最小闭环 → 再加「消费群体隔离并行」→ 再加「token 预算与降级」。
