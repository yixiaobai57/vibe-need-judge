---
name: vibe-need-judge
description: >
  判断一个 vibe coding 应用到底解决了真痛点、只是痒点、还是创作者自嗨。
  通过多 agent 法庭辩论：消费群体当陪审团（独立子agent，动态匹配，权重最大），
  产品/工程/备案/竞品/增长5位专家当证人（主上下文扮演），两轮聚焦辩论后加权裁决。
  不迎合人类，纯粹理性客观。支持想法/PRD/成品URL灵活输入。
  触发场景：判断vibe coding应用/项目、是否自嗨还是痛点、解决需求了吗、评价vibe coding、想法值不值得做。
---

# vibe-need-judge

判断一个 vibe coding 应用到底解决了真痛点、只是痒点、还是创作者自嗨。

## 核心理念

把"这个 vibe coding 应用到底解决没解决真需求"交给一个**不迎合人类**的多 agent 法庭：
- 消费群体当陪审团（独立子 agent，动态匹配，权重占 60%）
- 5 位专家当证人（主上下文扮演，权重共 40%）
- 两轮聚焦辩论后加权裁决

## 触发短语

- "判断这个 vibe coding 应用/项目"
- "这个应用是自嗨还是痛点"
- "这个项目解决需求了吗"
- "评价一下这个 vibe coding"
- "这个想法值不值得做"

## 主流程

### 第0步：输入解析与产品画像（≤800 token）

1. 识别输入类型：
   - 一句话/几句话 → 想法阶段
   - 结构化说明（功能/用户/场景） → PRD阶段
   - URL/Demo链接 → 成品阶段（如有URL，先用 WebFetch 抓取页面内容；抓取失败则提示用户补充文字描述，回退为想法阶段）

2. 提取产品画像（固定4字段）：
   - 领域（母婴/教育/SaaS/...）
   - 核心场景（用户在什么情境下用）
   - 付费来源（谁付钱、为什么付）
   - 技术形态（App/Web/小程序/工具/平台）

3. 若输入极度模糊（如"做个AI应用"无任何细节），直接返回"产品画像解析失败，请补充：领域/场景/付费来源"，不进入辩论。

4. 读取 [references/agents/consumer-groups/_matching-rubric.md](references/agents/consumer-groups/_matching-rubric.md)
   对候选库7个群体打相关度（0/1/2/3），选 2-3 个相关度≥2 的群体。
   每个选中群体输出一句话"匹配理由"。

5. 边界：匹配 0 个 → 降级纯专家评判（消费群体权重 0，报告标注可信度降低）；匹配 1 个 → 正常跑。

6. 输出：产品画像 + 匹配群体列表（含相关度+匹配理由）

### 第1轮：独立举证

**1a. 消费群体子 agent 并行派发**（Task 工具，2-3 个并发）

每个子 agent 输入：
- [references/agents/consumer-groups/_subagent-template.md](references/agents/consumer-groups/_subagent-template.md)（prompt 模板）
- 该群体核心画像 [references/agents/consumer-groups/<group>.md](references/agents/consumer-groups/)
- 产品画像
- 输出格式要求（5字段）

子 agent 自行决定是否读 [references/case-library/<group>-cases.md](references/case-library/)（NEEDS_CASES=yes 时）。

返回5字段：
```
GROUP: <群体名>
USE_INTENT: <1-10> - <一句理由>
PAY_INTENT: <1-10> - <一句理由>
PAIN_MATCH: <痛点/痒点/自嗨> - <一句理由>
KEY_ARG: <≤50字>
NEEDS_CASES: <yes/no>
```

**输入隔离**：子 agent 看不到其他 agent 的发言。

**1b. 主上下文依次扮演 5 位专家证人发言**

读取并 inline 对应角色卡：
- [references/agents/product-manager.md](references/agents/product-manager.md)
- [references/agents/code-engineer.md](references/agents/code-engineer.md)
- [references/agents/filing-agent.md](references/agents/filing-agent.md)
- [references/agents/competitor-analyst.md](references/agents/competitor-analyst.md)
- [references/agents/growth-hacker.md](references/agents/growth-hacker.md)

顺序：产品经理 → 代码工程师 → 备案中介 → 竞品分析师 → 增长黑客
每位 ≤400 token。

### 第2轮：分歧聚焦质询

读取 [references/debate-protocol.md](references/debate-protocol.md) 执行：

1. 扫描第1轮所有发言，识别 ≤3 个关键分歧点
   （分歧点判定：≥2方立场矛盾，且该矛盾会导致三档裁决结论不同）

2. 对每个分歧点：
   - 主上下文专家补证（≤150 token/分歧点）
   - 涉分歧的消费群体子 agent 重派补证（≤500 token/个，只给分歧点+该群体第1轮立场，用 _subagent-template.md 的"第2轮补证派发 prompt"）

3. 涉分歧群体筛选：只有 PAIN_MATCH 与大概率裁决矛盾，或 KEY_ARG 与其他方直接冲突的群体才重派。通常 1-2 个。

4. 检查 token 预算：若累计实际 ≥ 7500，按降级规则：
   - 专家补证跳过 → 案例库关闭 → 第2轮只处理 1 个分歧点

### 第3步：加权裁决（≤1200 token）

读取 [references/scoring-rubric.md](references/scoring-rubric.md) 执行：

1. 每个维度按"主要打分方 60% + 其他 agent 平均 40%"合成得分
2. 消费群体内部按相关度动态分配权重（占整体 60%）
3. 专家证人各占 8%（共 40%）
4. 计算加权总分 → 三档裁决：
   - 痛点: 加权总分 ≥ 7.0 且消费群体 PAY_INTENT 均值 ≥ 6
   - 痒点: 加权总分 4.0–6.9，或 PAY_INTENT 均值 3–5
   - 自嗨: 加权总分 < 4.0，或 PAY_INTENT 均值 < 3
5. 生成建设性意见（按档位规则，引用具体 KEY_ARG）
6. 填充 [templates/verdict-report.md](templates/verdict-report.md)，输出紧凑版报告

### 可选：完整辩论实录

用户要求时，在报告末尾追加"## 完整辩论实录"章节，或单独保存 verdict-full.md（不计入 1200 预算）。

## 输入阶段可信度

| 输入阶段 | 可信度 | 说明 |
|---|---|---|
| 想法点子 | 低 | 只有概念，技术/市场/合规都没验证 |
| PRD 说明 | 中 | 有结构化设计，但未经验证 |
| 成品 URL | 高 | 可观察实际产品，消费群体可"真实体验"后判断 |

成品 URL 时，消费群体子 agent 会先被提示"基于该 URL 的产品形态判断"，判断更接近真实。

## 已知局限

- **消费群体仍是被模拟的**：子 agent 按画像模拟，不等于真实用户调研，裁决是"理性推断"而非"市场验证"
- **专家证人在主上下文扮演**：不是真正独立 AI，可能有立场泄漏，但通过消费群体子 agent 独立性对冲
- **无真实数据支撑**：不抓竞品数据、不查真实留存，全靠 agent 推理，适合早期筛选不适合最终决策
- **中文产品语境**：备案中介角色针对国内合规，海外产品需调整

## 参考文件索引

| 文件 | 用途 |
|---|---|
| references/scoring-rubric.md | 评分维度+动态权重+建设性意见规则 |
| references/debate-protocol.md | 两轮辩论协议+token预算+降级规则 |
| references/agents/*.md | 5位专家证人角色卡 |
| references/agents/consumer-groups/_subagent-template.md | 消费群体子agent派发模板 |
| references/agents/consumer-groups/_matching-rubric.md | 群体匹配规则 |
| references/agents/consumer-groups/<group>.md | 7个群体核心画像（候选库） |
| references/case-library/<group>-cases.md | 7个群体案例库（按需读） |
| templates/verdict-report.md | 裁决报告输出模板 |
