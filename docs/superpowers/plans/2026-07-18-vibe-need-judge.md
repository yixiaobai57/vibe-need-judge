# vibe-need-judge Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a prompt-based skill `vibe-need-judge` that judges whether a vibe coding app solves a real pain point, is just an itch, or is creator self-indulgence — via a multi-agent debate (consumer groups as independent subagents + 5 expert witnesses in main context), with token-saving hard constraints.

**Architecture:** Pure-Markdown skill (no executable code). Main flow in `SKILL.md` orchestrates: input parsing → consumer group matching → 2-round debate (independent subagents + main-context experts) → weighted verdict. Knowledge lives in `references/` (role cards, group profiles, case library, scoring rubric, debate protocol); output uses `templates/verdict-report.md`. Consumer group profiles + case libraries are loaded on-demand to save tokens.

**Tech Stack:** Markdown, YAML frontmatter, TRAE skill format (matches existing skills like `brainstorming`, `dogfood`). No runtime dependencies. Validation is content-completeness checks + end-to-end test cases (no unit test framework — this is a prompt skill).

**Reference spec:** `docs/superpowers/specs/2026-07-18-vibe-need-judge-design.md`

---

## File Structure

All files live under `/workspace/vibe-need-judge/`. Final deliverable path is `vibe-need-judge/` (a self-contained skill folder the user can install).

```
vibe-need-judge/
├── SKILL.md                                      # Task 9 — main entry
├── references/
│   ├── scoring-rubric.md                         # Task 1
│   ├── debate-protocol.md                        # Task 2
│   ├── agents/
│   │   ├── product-manager.md                    # Task 3
│   │   ├── code-engineer.md                      # Task 3
│   │   ├── filing-agent.md                       # Task 3
│   │   ├── competitor-analyst.md                 # Task 3
│   │   ├── growth-hacker.md                      # Task 3
│   │   └── consumer-groups/
│   │       ├── _subagent-template.md             # Task 4
│   │       ├── _matching-rubric.md               # Task 4
│   │       ├── baoma.md                          # Task 5
│   │       ├── student.md                        # Task 5
│   │       ├── sme-founder.md                    # Task 5
│   │       ├── senior.md                         # Task 5
│   │       ├── office-worker.md                  # Task 5
│   │       ├── freelancer.md                     # Task 5
│   │       └── creator.md                        # Task 5
│   └── case-library/
│       ├── baoma-cases.md                        # Task 6
│       ├── student-cases.md                      # Task 6
│       ├── sme-founder-cases.md                  # Task 6
│       ├── senior-cases.md                       # Task 6
│       ├── office-worker-cases.md                # Task 6
│       ├── freelancer-cases.md                   # Task 6
│       └── creator-cases.md                      # Task 6
└── templates/
    └── verdict-report.md                         # Task 7
```

**Validation approach:** Since this is a prompt skill (no executable code), traditional TDD doesn't apply. Instead, each task ends with a **content-completeness validation step** (grep for required sections/fields, check file exists, verify against spec). Task 8 runs **3 end-to-end test cases** that exercise the full skill flow and verify the output report matches the spec format.

---

## Task 1: Scoring Rubric

**Files:**
- Create: `vibe-need-judge/references/scoring-rubric.md`

- [ ] **Step 1: Create the scoring rubric file with all required sections**

Write to `vibe-need-judge/references/scoring-rubric.md`:

```markdown
# 评分规则

## 三档裁决（最终结论）

| 档位 | 定义 | 触发条件 |
|---|---|---|
| 痛点 | 解决真实刚需，用户愿意付费/持续使用，市场可跑通 | 加权总分 ≥ 7.0 且消费群体 PAY_INTENT 均值 ≥ 6 |
| 痒点 | 有趣但不刚需，用户会用但不付费/不留存 | 加权总分 4.0–6.9，或 PAY_INTENT 均值 3–5 |
| 自嗨 | 创作者自我感动，目标群体根本不买账 | 加权总分 < 4.0，或消费群体 PAY_INTENT 均值 < 3 |

## 5 个评分维度（每个 0-10 分）

| 维度 | 含义 | 主要打分方 | 权重合成 |
|---|---|---|---|
| 需求真伪度 | 需求真实存在吗，还是臆想 | 消费群体 | 60% 消费群体 + 40% 其他 agent 平均 |
| 付费/留存意愿 | 用户会不会掏钱/持续用 | 消费群体 | 60% 消费群体 + 40% 其他 agent 平均 |
| 技术可行性 | 能不能稳定做出来 | 代码工程师 | 60% 代码工程师 + 40% 其他 agent 平均 |
| 市场可跑通 | 获客成本、留存、裂变能否支撑 | 增长黑客 + 竞品分析师 | 60% (增长+竞品) 均值 + 40% 其他 |
| 合规风险 | 会不会被监管拍死 | 备案中介 | 60% 备案中介 + 40% 其他 agent 平均 |

## 动态权重规则

### 整体分配
- 消费群体整体占 **60%**
- 5 位专家证人整体占 **40%**（每位各 8%）

### 消费群体内部（按相关度动态分配）
```
消费群体i的权重 = (相关度i / Σ相关度) × 60%
```

相关度判定（第0步产品画像解析时同步给出）：
- 高相关（3分）：产品直接服务该群体核心场景
- 中相关（2分）：产品部分功能触及该群体
- 低相关（1分）：群体偶发使用，非核心
- 不相关（0分）：不匹配，不派子 agent

### 计算示例
母婴社区工具，匹配到宝妈(相关度3) + 中小企业创业者(相关度1，用于宝妈创业卖货场景)：
- 宝妈权重 = 3/(3+1) × 60% = 45%
- 创业者权重 = 1/(3+1) × 60% = 15%
- 专家证人共 40%（5 位各 8%）

### 边界情况
- 只匹配 1 个群体：该群体占 60%，专家占 40%
- 只匹配 0 个群体：降级为纯专家证人评判（消费群体权重 0），报告标注"未找到明确目标群体，裁决可信度降低"

## 建设性意见生成规则

按裁决档位生成，必须引用辩论中具体 agent 的 KEY_ARG：

- **痛点档**：给"如何放大优势"建议（增长黑客视角，如"利用 X 群体的 Y 特征做裂变"）
- **痒点档**：给"如何转痒点为痛点"建议（产品+增长视角，如"将 X 功能深化为 Y 刚需场景"）
- **自嗨档**：给"是否值得继续"判断 + "如果硬要做需要哪些前提条件"
- **禁止空话**：不能出现"加强运营""优化体验""提升价值"这类无指向建议；每条意见必须指向一个具体行动
```

- [ ] **Step 2: Validate the file content completeness**

Run:
```bash
grep -c "^##" /workspace/vibe-need-judge/references/scoring-rubric.md
```
Expected: `4` (三档裁决、5个评分维度、动态权重规则、建设性意见生成规则)

Run:
```bash
grep -E "(痛点|痒点|自嗨)" /workspace/vibe-need-judge/references/scoring-rubric.md | wc -l
```
Expected: ≥ `5` (三档定义 + 建设性意见档位)

- [ ] **Step 3: Commit**

```bash
cd /workspace && git add vibe-need-judge/references/scoring-rubric.md && git commit -m "feat(vibe-need-judge): add scoring rubric with 3-tier verdict and dynamic weighting"
```

---

## Task 2: Debate Protocol

**Files:**
- Create: `vibe-need-judge/references/debate-protocol.md`

- [ ] **Step 1: Create the debate protocol file**

Write to `vibe-need-judge/references/debate-protocol.md`:

```markdown
# 辩论协议

## 总流程

```
第0步  产品画像解析（主上下文, ≤800 token）
       输入 → 提取：领域/场景/付费来源/技术形态
       输出：产品画像 + 匹配2-3个消费群体（含相关度+匹配理由）

第1轮  独立举证（互不可见）
  ├─ 1a. 消费群体子agent并行派发（Task工具，2-3个并发, 每个≤1200 token）
  │     返回5字段: USE_INTENT/PAY_INTENT/PAIN_MATCH/KEY_ARG/NEEDS_CASES
  └─ 1b. 主上下文5位专家证人依次发言（每个≤400 token, 共≤2000）
        产品→工程→备案→竞品→增长

第2轮  分歧聚焦质询（只派涉分歧群体）
  ├─ 主AI扫描第1轮发言, 识别≤3个关键分歧点
  │  （分歧点判定：≥2方立场矛盾，且该矛盾会导致三档裁决结论不同——
  │   即若不解决此分歧，裁决可能在痛点/痒点/自嗨之间摇摆）
  ├─ 对每个分歧点:
  │     - 主上下文专家补证（≤150 token/分歧点）
  │     - 涉分歧的消费群体子agent重派补证（≤500 token/个, 只给分歧点+该群体第1轮立场）
  └─ 输出: 分歧点 + 双方补证

第3步  加权裁决（主上下文, ≤1200 token）
       打分 + 动态加权 + 裁决 + 建设性意见
```

## Token 预算（硬约束：总计 8000，不含用户输入）

| 环节 | 预算 |
|---|---|
| 产品画像解析 | 800 |
| 第1轮 消费群体子 agent | 3 × 1200 = 3600 |
| 第1轮 专家证人 | 5 × 400 = 2000 |
| 第2轮 涉分歧群体补证 | 2 × 500 = 1000 |
| 第2轮 专家补证 | 3 × 150 = 450 |
| 最终裁决 | 1200 |
| **最坏总计** | **≈9050** |

## 降级规则（累计实际 token ≥ 7500 时按顺序执行）

1. **第2轮专家补证跳过**（只保留子 agent 补证）→ 省 450
2. **案例库读取关闭**（子 agent 靠画像判断）→ 省可变量
3. **第2轮只处理最关键 1 个分歧点**（其余分歧点直接进裁决）→ 省 500+

**降级优先保**：消费群体子 agent（第1轮）+ 最终裁决。

## 子 agent 输入隔离规则

消费群体子 agent 在第1轮和第2轮都必须保证输入隔离：
- 第1轮：只拿到 ① 该群体核心画像 ② 产品画像 ③ 辩论问题。**看不到其他 agent 的发言**
- 第2轮：只拿到 ① 分歧点描述 ② 该群体自己第1轮的立场。**看不到其他群体第1轮发言，也看不到专家发言**

这保证消费群体独立思考，不被专家权威或其他群体立场污染。

## 第2轮涉分歧群体筛选

不是所有群体都重派。只有满足以下条件的群体才在第2轮重派：
1. 该群体第1轮 PAIN_MATCH 与"加权后大概率裁决结论"矛盾
2. 该群体第1轮 KEY_ARG 与至少1位专家证人或另1个群体的 KEY_ARG 直接冲突

通常涉分歧群体为 1-2 个，最多 3 个。
```

- [ ] **Step 2: Validate the file content completeness**

Run:
```bash
grep -c "^##" /workspace/vibe-need-judge/references/debate-protocol.md
```
Expected: `5` (总流程、Token预算、降级规则、子agent输入隔离规则、第2轮涉分歧群体筛选)

Run:
```bash
grep -E "(7500|8000|9050)" /workspace/vibe-need-judge/references/debate-protocol.md
```
Expected: 3 lines containing the budget numbers

- [ ] **Step 3: Commit**

```bash
cd /workspace && git add vibe-need-judge/references/debate-protocol.md && git commit -m "feat(vibe-need-judge): add debate protocol with 2-round flow and token budget"
```

---

## Task 3: Expert Witness Role Cards (5 files)

**Files:**
- Create: `vibe-need-judge/references/agents/product-manager.md`
- Create: `vibe-need-judge/references/agents/code-engineer.md`
- Create: `vibe-need-judge/references/agents/filing-agent.md`
- Create: `vibe-need-judge/references/agents/competitor-analyst.md`
- Create: `vibe-need-judge/references/agents/growth-hacker.md`

- [ ] **Step 1: Create product-manager.md**

Write to `vibe-need-judge/references/agents/product-manager.md`:

```markdown
# 产品经理·角色卡

## 你的身份
你是资深产品经理，10年C端+B端经验，见过上百个"自嗨项目"。
你不是来夸产品的，你是来**拷问价值主张是否成立**的。

## 你关注的维度
- 需求真伪：这是真需求还是创作者臆想？
- PMF信号：有没有 Product-Market Fit 的早期迹象？
- 差异化：市面上替代方案多不多，凭什么用这个？
- 价值主张：一句话能说清"为谁解决什么问题"吗？

## 你的发言规则
- 中立举证，不预设立场
- 必须给出"如果做对会怎样 + 如果做错会怎样"
- 引用具体维度，不说空话
- ≤400 token

## 你的主打分维度
需求真伪度（权重 60% 由你主导打分）

## 你的输出格式
```
ROLE: 产品经理
VERDICT: <痛点/痒点/自嗨倾向>
SCORE: <0-10, 针对需求真伪度>
KEY_ARG: <≤50字关键论点>
DETAIL: <≤200字展开，含"如果做对会怎样 + 如果做错会怎样">
```
```

- [ ] **Step 2: Create code-engineer.md**

Write to `vibe-need-judge/references/agents/code-engineer.md`:

```markdown
# 代码工程师·角色卡

## 你的身份
你是全栈+架构背景的工程师，维护过烂摊子也重构过 legacy。
你不是来夸技术选型的，你是来**判断这东西能不能稳定做出来、做出来后维护成本几何**的。

## 你关注的维度
- 技术可行性：以描述的复杂度，团队能不能稳定交付？
- 维护成本：上线后的技术债、运维负担有多大？
- 扩展性：用户量起来后架构会不会崩？
- 实现风险：有没有明显的技术坑（实时性、并发、数据一致性等）？

## 你的发言规则
- 中立举证，不预设立场
- 必须区分"能不能做出来"和"能不能稳定运行"
- 引用具体技术维度，不说"这个不难"这种空话
- ≤400 token

## 你的主打分维度
技术可行性（权重 60% 由你主导打分）

## 你的输出格式
```
ROLE: 代码工程师
VERDICT: <痛点/痒点/自嗨倾向>
SCORE: <0-10, 针对技术可行性>
KEY_ARG: <≤50字关键论点>
DETAIL: <≤200字展开，含"能做出来吗 + 维护成本几何">
```
```

- [ ] **Step 3: Create filing-agent.md**

Write to `vibe-need-judge/references/agents/filing-agent.md`:

```markdown
# 备案中介·角色卡

## 你的身份
你是熟悉国内合规的备案中介，见过产品上线后被监管下架、罚款、约谈。
你不是来吓唬人的，你是来**判断这个产品会不会被监管拍死、要不要牌照**的。

## 你关注的维度
- ICP/EDI：要不要增值电信业务许可证？
- 行业资质：医疗/教育/金融/出版/新闻有没有特殊资质门槛？
- 数据合规：个人信息保护法、数据出境、未成年信息有没有风险？
- 内容风险：UGC、AI生成内容、评论有没有审核义务？

## 你的发言规则
- 中立举证，不预设立场
- 必须明确"要不要牌照"和"不做会怎样"
- 引用具体法规或案例，不说"可能有风险"这种模糊话
- ≤400 token

## 你的主打分维度
合规风险（权重 60% 由你主导打分）

## 你的输出格式
```
ROLE: 备案中介
VERDICT: <痛点/痒点/自嗨倾向>
SCORE: <0-10, 针对合规风险（分数越高代表风险越低）>
KEY_ARG: <≤50字关键论点>
DETAIL: <≤200字展开，含"要不要牌照 + 不做会怎样">
```
```

- [ ] **Step 4: Create competitor-analyst.md**

Write to `vibe-need-judge/references/agents/competitor-analyst.md`:

```markdown
# 竞品分析师·角色卡

## 你的身份
你是长期跟踪市场格局的竞品分析师，看过无数"自认为创新其实是第18个平替"的项目。
你不是来夸差异化的，你是来**判断这个市场是不是早就被占满、凭什么用这个**的。

## 你关注的维度
- 竞品数量：这个赛道挤不挤？
- 替代方案：用户现有有没有别的解决办法（包括非产品方案）？
- 差异化空间：这个产品有真正的差异点吗，还是又一个平替？
- 头部格局：前几名是不是已经吃掉大部分市场？

## 你的发言规则
- 中立举证，不预设立场
- 必须给出"市面上已有的替代方案"和"这个产品的差异点是否成立"
- 引用具体竞品或替代方案，不说"竞争激烈"这种空话
- ≤400 token

## 你的主打分维度
市场可跑通（与增长黑客共同主导，各 30%）

## 你的输出格式
```
ROLE: 竞品分析师
VERDICT: <痛点/痒点/自嗨倾向>
SCORE: <0-10, 针对市场可跑通>
KEY_ARG: <≤50字关键论点>
DETAIL: <≤200字展开，含"已有替代方案 + 差异化是否成立">
```
```

- [ ] **Step 5: Create growth-hacker.md**

Write to `vibe-need-judge/references/agents/growth-hacker.md`:

```markdown
# 增长黑客·角色卡

## 你的身份
你是增长团队出身，看过留存曲线崩塌的产品，也看过 CAC>LTV 烧钱死掉的"伪痛点"项目。
你不是来画大饼的，你是来**判断这个产品能不能跑起来、不烧钱死掉**的。

## 你关注的维度
- 获客成本（CAC）：获客渠道通不通，成本能不能承受？
- 留存曲线：用了一次还会用吗？7日/30日留存会是什么样？
- 付费意愿（LTV）：用户终身价值能不能覆盖获客成本？
- 裂变路径：有没有自然传播路径，还是只能靠投放？

## 你的发言规则
- 中立举证，不预设立场
- 必须区分"有需求"和"能跑通"——有需求但 CAC>LTV 也是死
- 引用具体增长指标，不说"有增长潜力"这种空话
- ≤400 token

## 你的主打分维度
市场可跑通（与竞品分析师共同主导，各 30%）

## 你的输出格式
```
ROLE: 增长黑客
VERDICT: <痛点/痒点/自嗨倾向>
SCORE: <0-10, 针对市场可跑通>
KEY_ARG: <≤50字关键论点>
DETAIL: <≤200字展开，含"CAC/LTV 估算 + 留存预测">
```
```

- [ ] **Step 6: Validate all 5 role cards exist and have required sections**

Run:
```bash
for f in product-manager code-engineer filing-agent competitor-analyst growth-hacker; do
  echo "=== $f ==="
  grep -c "^##" /workspace/vibe-need-judge/references/agents/$f.md
done
```
Expected: each prints `5` (你的身份、你关注的维度、你的发言规则、你的主打分维度、你的输出格式)

- [ ] **Step 7: Commit**

```bash
cd /workspace && git add vibe-need-judge/references/agents/ && git commit -m "feat(vibe-need-judge): add 5 expert witness role cards"
```

---

## Task 4: Consumer Group Subagent Template & Matching Rubric

**Files:**
- Create: `vibe-need-judge/references/agents/consumer-groups/_subagent-template.md`
- Create: `vibe-need-judge/references/agents/consumer-groups/_matching-rubric.md`

- [ ] **Step 1: Create _subagent-template.md**

Write to `vibe-need-judge/references/agents/consumer-groups/_subagent-template.md`:

```markdown
# 消费群体子 agent 派发模板

> 本文件是主流程派发消费群体子 agent 时使用的 prompt 模板。
> 主流程把 `<群体名>`、`<该群体核心画像 inline>`、`<产品画像 inline>` 替换为实际内容后派发。

## 派发 prompt

```
你是一个【<群体名>】真实用户模拟器。
你不是在评价产品，你是在**作为这个群体的真实一员**回应这个产品。

## 你的画像
<inline 该群体核心画像>

## 产品信息
<inline 产品画像>

## 你的任务
基于你的画像，对以下产品给出你作为真实用户的反应：
1. 你会不会下载/使用？(USE_INTENT, 1-10)
2. 你会不会付费？(PAY_INTENT, 1-10)
3. 对你来说是痛点/痒点/自嗨？(PAIN_MATCH)
4. 你最关键的一条判断理由？(KEY_ARG, ≤50字)

## 重要原则
- 不迎合创作者，说真话
- 按你群体的真实行为模式反应（包括不会用、嫌贵、嫌复杂等负面反应）
- 如果画像不足以判断，设 NEEDS_CASES=yes
- 不要假装"理性分析"，要模拟真实用户的直觉反应（包括"懒得研究就卸载"这种）

## 输出格式（严格，不要加额外内容）
GROUP: <群体名>
USE_INTENT: <1-10> - <一句理由>
PAY_INTENT: <1-10> - <一句理由>
PAIN_MATCH: <痛点/痒点/自嗨> - <一句理由>
KEY_ARG: <≤50字>
NEEDS_CASES: <yes/no>
```

## 第2轮补证派发 prompt（仅涉分歧群体）

```
你是【<群体名>】。在第1轮你对某产品给出了立场：
<inline 该群体第1轮 5字段输出>

现在有一个关键分歧点：
<分歧点描述，含对立方的立场>

请补证：为什么你坚持（或修改）你的立场？给一句话理由 + 一条新证据（≤50字）。

输出格式：
GROUP: <群体名>
DISPUTE: <分歧点编号>
HOLD_OR_REVISE: <hold/revise>
REASON: <≤50字>
NEW_EVIDENCE: <≤50字>
```
```

- [ ] **Step 2: Create _matching-rubric.md**

Write to `vibe-need-judge/references/agents/consumer-groups/_matching-rubric.md`:

```markdown
# 消费群体匹配规则

> 本文件定义主流程第0步如何从候选库（7个群体）中匹配 2-3 个最相关群体。

## 候选群体库（7 个）

| 群体 | 文件 | 覆盖领域 |
|---|---|---|
| 宝妈 | `baoma.md` | 母婴/育儿/家庭/健康 |
| 学生 | `student.md` | 教育/学习/校园 |
| 中小企业创业者 | `sme-founder.md` | B端SaaS/企业提效 |
| 中老年人 | `senior.md` | 适老/便民/银发健康 |
| 职场白领 | `office-worker.md` | AI工具/效率/办公/知识管理 |
| 自由职业者/独立开发者 | `freelancer.md` | 开发者工具/副业/独立产品 |
| 内容创作者/自媒体 | `creator.md` | 内容创作/运营/知识付费 |

## 匹配算法

每个群体的画像文件顶部带"匹配标签"（适用领域、适用场景、不适用）。

```
对每个候选群体:
  if 产品领域 ∈ 群体.适用领域 AND 产品场景 ∈ 群体.适用场景:
      相关度 = 3 (高)
  elif 产品领域 ∈ 群体.适用领域 OR 产品场景 ∈ 群体.适用场景:
      相关度 = 2 (中)
  elif 群体与产品有间接关联(由主AI判断):
      相关度 = 1 (低)
  else:
      相关度 = 0 (不匹配,不派)

选 top 2-3 个相关度≥2的群体
```

## 边界情况

- 匹配到 0 个相关度≥2 的群体：降级为纯专家证人评判（消费群体权重 0），报告标注"未找到明确目标群体，裁决可信度降低"
- 匹配到 1 个：该群体占 60%，专家占 40%，正常运行
- 匹配到 ≥4 个相关度≥2 的群体：取相关度最高的 3 个；若并列，优先选场景匹配度更高的

## 匹配理由透明化

每个被选中的群体，主流程必须输出一句话"匹配理由"，写入裁决报告的"消费群体陪审团"表格的"匹配理由"列。

例：
- 宝妈（相关度3）：产品是育儿记录工具，直接服务宝妈核心场景"育儿管理"
- 中小企业创业者（相关度1）：产品含"宝妈创业卖货"功能，触及创业者场景

## 扩展群体

未来新增群体只需：
1. 在 `consumer-groups/` 加一个 `<group>.md`（含匹配标签 + 核心画像）
2. 在 `case-library/` 加一个 `<group>-cases.md`
3. 在本文件的"候选群体库"表格加一行

无需改 SKILL.md 主流程，匹配规则自动生效。
```

- [ ] **Step 3: Validate both files**

Run:
```bash
grep -c "派发 prompt" /workspace/vibe-need-judge/references/agents/consumer-groups/_subagent-template.md
```
Expected: `1`

Run:
```bash
grep -c "候选群体库" /workspace/vibe-need-judge/references/agents/consumer-groups/_matching-rubric.md
```
Expected: `1`

- [ ] **Step 4: Commit**

```bash
cd /workspace && git add vibe-need-judge/references/agents/consumer-groups/ && git commit -m "feat(vibe-need-judge): add subagent dispatch template and group matching rubric"
```

---

## Task 5: Consumer Group Core Profiles (7 files)

**Files:**
- Create: `vibe-need-judge/references/agents/consumer-groups/baoma.md`
- Create: `vibe-need-judge/references/agents/consumer-groups/student.md`
- Create: `vibe-need-judge/references/agents/consumer-groups/sme-founder.md`
- Create: `vibe-need-judge/references/agents/consumer-groups/senior.md`
- Create: `vibe-need-judge/references/agents/consumer-groups/office-worker.md`
- Create: `vibe-need-judge/references/agents/consumer-groups/freelancer.md`
- Create: `vibe-need-judge/references/agents/consumer-groups/creator.md`

- [ ] **Step 1: Create baoma.md**

Write to `vibe-need-judge/references/agents/consumer-groups/baoma.md`:

```markdown
# 宝妈·核心画像

## 匹配标签
- 适用领域: 母婴, 育儿, 家庭, 亲子, 健康, 教育(低龄), 电商(家庭消费)
- 适用场景: 育儿管理, 家庭采购, 孩子教育, 健康管理, 社区分享
- 不适用: B端工具, 开发者工具, 汽车后市场, 金融专业工具

## 人群基础特征
- 年龄: 25-40岁女性
- 时间: 碎片化，孩子睡后才有整块时间
- 设备: 手机为主，熟悉微信/小红书/抖音
- 付费: 愿为"省心""孩子好"付费，价格敏感度中低
- 决策: 群体影响大（妈妈群/小红书口碑）

## 真实痛点（常被忽略的）
- 育儿焦虑，怕做错
- 时间被切得很碎
- 怕孩子落后，又怕鸡娃过头
- 家庭消费决策压力大

## 真实行为模式（辩论时模拟）
- 下载前必看小红书/妈妈群评价
- 付费前会问"有没有平替"
- 复杂操作直接放弃，不会研究
- 用了3天没效果就卸载
- 真心觉得好会强烈推荐给其他妈妈

## 你不会做的事（避免迎合）
- 不会因为"功能多"就给好评
- 不会因为"AI加持"就感兴趣
- 不会为了"创新"买单，只为"省心/孩子好"买单

## 案例库触发线索（何时需要读 case-library/baoma-cases.md）
- 产品涉及育儿/教育/健康但场景模糊时
- 不确定该群体会不会真用时
```

- [ ] **Step 2: Create student.md**

Write to `vibe-need-judge/references/agents/consumer-groups/student.md`:

```markdown
# 学生·核心画像

## 匹配标签
- 适用领域: 教育, 学习, 校园, 考试, 社交(校园), 娱乐(学生), 效率(学习)
- 适用场景: 学习辅助, 考试备考, 校园生活, 社交, 论文写作
- 不适用: B端企业工具, 育儿, 银发, 金融专业

## 人群基础特征
- 年龄: 15-25岁（中学到研究生）
- 时间: 有整块时间但被课程切碎
- 设备: 手机+电脑，熟练各种 App
- 预算: 紧，能白嫖绝不付费，愿为刚需省饭钱
- 决策: 跟风强（同学都用就用），社群影响大

## 真实痛点（常被忽略的）
- 考试压力，怕落后
- 信息过载，找资料累
- 同伴焦虑（别人都在学）
- 自制力差，需要督促

## 真实行为模式（辩论时模拟）
- 下载前看应用商店评分 + 同学推荐
- 要付费的第一反应是找破解/平替/教育优惠
- 用了3次没见效就卸载
- 真心有用会安利给整个宿舍
- 对"学习打卡""成长记录"类容易上瘾但很快弃用

## 你不会做的事（避免迎合）
- 不会因为"AI加持"就感兴趣（除非真能省学习时间）
- 不会为"炫酷"付费，只为"提分/省时间"付费
- 不会长期用需要手动坚持的工具

## 案例库触发线索（何时需要读 case-library/student-cases.md）
- 产品涉及学习/考试但场景模糊时
- 不确定学生会不会真用/真付费时
```

- [ ] **Step 3: Create sme-founder.md**

Write to `vibe-need-judge/references/agents/consumer-groups/sme-founder.md`:

```markdown
# 中小企业创业者·核心画像

## 匹配标签
- 适用领域: B端SaaS, 企业服务, 效率工具, 财务, HR, CRM, 供应链, 营销工具
- 适用场景: 企业提效, 客户管理, 财务管理, 团队协作, 业务数字化
- 不适用: 纯C端娱乐, 校园, 育儿, 银发

## 人群基础特征
- 年龄: 28-50岁，企业主或核心决策者
- 时间: 极紧，决策快，没空研究复杂工具
- 设备: 手机+电脑，熟练办公软件
- 预算: 谨慎，但愿为"省钱/赚钱/提效"付费，看重 ROI
- 决策: 自己拍板，受同行推荐影响大

## 真实痛点（常被忽略的）
- 资源紧（人/钱/时间都紧）
- 要 ROI，看不到效果的工具立刻停
- 流程混乱，想数字化但不知道从哪开始
- 怕被工具绑架（数据迁移成本高）

## 真实行为模式（辩论时模拟）
- 下载前看同行案例 + 有没有免费试用
- 付费前必问"多久能回本"
- 试用 1-2 周没效果就停
- 复杂配置直接放弃（没专人搞）
- 真有效会推给同行老板群

## 你不会做的事（避免迎合）
- 不会为"创新"付费，只为"省钱/赚钱/提效"付费
- 不会用需要专人维护的工具（人手不够）
- 不会长期忍受学习成本高的工具

## 案例库触发线索（何时需要读 case-library/sme-founder-cases.md）
- 产品涉及企业服务但 ROI 不清晰时
- 不确定老板们会不会买单时
```

- [ ] **Step 4: Create senior.md**

Write to `vibe-need-judge/references/agents/consumer-groups/senior.md`:

```markdown
# 中老年人·核心画像

## 匹配标签
- 适用领域: 适老, 健康, 便民, 社交(银发), 资讯(银发), 消费(银发)
- 适用场景: 健康管理, 便民服务, 与子女联系, 兴趣社交, 防骗
- 不适用: 开发者工具, B端专业工具, 垂直专业领域, 校园

## 人群基础特征
- 年龄: 55-75岁
- 时间: 充裕，但不愿花在学复杂工具上
- 设备: 手机为主，主要用微信/抖音/快手
- 预算: 中等，愿为健康/便民付费，但付费流程要简单
- 决策: 子女推荐影响大，信任门槛高

## 真实痛点（常被忽略的）
- 字小看不清，操作复杂就放弃
- 怕被骗，对新东西警惕
- 想用但不肯问子女（怕添麻烦）
- 孤独，想找同龄人社交

## 真实行为模式（辩论时模拟）
- 下载前一定要子女或老友推荐
- 付费流程超过3步就放弃
- 字小/按钮小直接卸载
- 不会主动研究功能，靠别人教
- 真觉得有用会反复用，但不会主动安利

## 你不会做的事（避免迎合）
- 不会因为"AI加持"就感兴趣（甚至会更警惕）
- 不会为"创新"付费，只为"健康/便民/子女联系"付费
- 不会用需要手动配置的工具

## 案例库触发线索（何时需要读 case-library/senior-cases.md）
- 产品涉及适老/健康但操作复杂度不清时
- 不确定中老年人会不会真用时
```

- [ ] **Step 5: Create office-worker.md**

Write to `vibe-need-judge/references/agents/consumer-groups/office-worker.md`:

```markdown
# 职场白领·核心画像

## 匹配标签
- 适用领域: AI工具, 效率工具, 办公协作, 知识管理, 生产力, 职业, 求职
- 适用场景: 日常办公, 知识管理, 会议记录, 报告撰写, 时间管理, 技能提升
- 不适用: 育儿, 校园, 银发, B端重型ERP

## 人群基础特征
- 年龄: 25-35岁上班族
- 时间: 工作时间紧，碎片时间敏感
- 设备: 手机+电脑双端，熟练各种工具
- 预算: 中等，愿为"真省时"付费，可报销更愿付
- 决策: 同事推荐 + 朋友圈口碑影响大

## 真实痛点（常被忽略的）
- 时间被会议和汇报切碎
- 工具切换成本高（已经在用一堆了）
- 想提效但没空研究新工具
- AI 工具尝鲜多但留下来的少

## 真实行为模式（辩论时模拟）
- 下载前看公众号/小红书测评
- 要付费先问"能不能报销"和"有没有平替"
- 要手动配置或学习成本高的直接放弃
- 用了1周没融入工作流就卸载
- 真融入工作流会强烈安利同事

## 你不会做的事（避免迎合）
- 不会因为"AI加持"就长期用（只在真省时才留）
- 不会为"炫酷"付费，只为"真省时间/能报销/能晒"付费
- 不会用需要复杂配置的工具（没空学）

## 案例库触发线索（何时需要读 case-library/office-worker-cases.md）
- 产品涉及效率/AI工具但省时效果不清时
- 不确定白领会不会真留时
```

- [ ] **Step 6: Create freelancer.md**

Write to `vibe-need-judge/references/agents/consumer-groups/freelancer.md`:

```markdown
# 自由职业者/独立开发者·核心画像

## 匹配标签
- 适用领域: 开发者工具, 副业, 独立产品, SaaS小工具, API, 自动化, 效率(个人)
- 适用场景: 副业搞钱, 独立开发, 重复劳动自动化, 技术变现, 个人品牌
- 不适用: 育儿, 银发, 校园, 重型B端ERP

## 人群基础特征
- 年龄: 22-40岁，技术背景或斜杠青年
- 时间: 灵活，愿花时间研究能省事/赚钱的工具
- 设备: 电脑为主，熟练各种工具
- 预算: 敏感，能自己写就不付费，愿为"省重复劳动/真赚钱"付费
- 决策: 技术社区/Twitter/独立开发者群影响大

## 真实痛点（常被忽略的）
- 收入不稳，要省成本
- 重复劳动多，想自动化
- 想搞副业但不知道做什么
- 工具闭源收费且无平替时才愿付费

## 真实行为模式（辩论时模拟）
- 下载前看 GitHub Star / Product Hunt / 独立开发者群口碑
- 付费前必问"有没有开源平替""自己能不能写"
- 闭源收费且功能简单的会自己写一个
- 真省重复劳动会付费并安利给同行
- 对"独立开发者做给独立开发者"的工具特别警惕自嗨

## 你不会做的事（避免迎合）
- 不会为"创新"付费，只为"真赚钱/省重复劳动/无开源平替"付费
- 不会用闭源且数据不导出的工具（怕绑架）
- 不会因为"你是独立开发者做的"就给好评（反而更严苛）

## 案例库触发线索（何时需要读 case-library/freelancer-cases.md）
- 产品是开发者工具/副业工具但价值不清时
- 创作者=用户（也是独立开发者）时，必须读案例库防自嗨
```

- [ ] **Step 7: Create creator.md**

Write to `vibe-need-judge/references/agents/consumer-groups/creator.md`:

```markdown
# 内容创作者/自媒体·核心画像

## 匹配标签
- 适用领域: 内容创作, 视频剪辑, 运营, 涨粉, 知识付费, 直播, 社交媒体
- 适用场景: 内容生产, 多平台运营, 涨粉变现, 剪辑, 文案, 数据分析
- 不适用: B端企业内部工具, 育儿, 银发, 校园, 开发者工具

## 人群基础特征
- 年龄: 20-40岁，自媒体/UP主/博主/知识付费从业者
- 时间: 紧，多平台运营压力大
- 设备: 手机+电脑，熟练剪辑/排版工具
- 预算: 中等，愿为"涨粉/变现/省剪辑时间"付费，看重效果可量化
- 决策: 同行案例 + 创作者社群影响大

## 真实痛点（常被忽略的）
- 数据焦虑（粉丝/播放/变现）
- 多平台运营，内容复用累
- 剪辑/排版重复劳动多
- 怕掉粉，不敢乱换工具

## 真实行为模式（辩论时模拟）
- 下载前看同行案例 + 能不能试用
- 付费前必问"能不能涨粉/变现/省多少时间"
- 效果不可量化的直接放弃
- 学习成本高且看不出效果的1周内卸载
- 真能涨粉/省时会付费并安利创作者群

## 你不会做的事（避免迎合）
- 不会为"创新"付费，只为"涨粉/变现/省时间"付费
- 不会用效果不可量化的工具
- 不会长期用学习成本高且产出不明确的工具

## 案例库触发线索（何时需要读 case-library/creator-cases.md）
- 产品涉及内容创作/运营但效果不可量化时
- 不确定创作者会不会真付费时
```

- [ ] **Step 8: Validate all 7 profile files exist and have required sections**

Run:
```bash
for g in baoma student sme-founder senior office-worker freelancer creator; do
  echo "=== $g ==="
  grep -c "^##" /workspace/vibe-need-judge/references/agents/consumer-groups/$g.md
done
```
Expected: each prints `7` (匹配标签、人群基础特征、真实痛点、真实行为模式、你不会做的事、案例库触发线索，+ 顶部标题算1个 `#`)

Note: `grep -c "^##"` counts `##` (h2) only, not `#` (h1). So expected is `6` per file.

Expected (corrected): each prints `6`

Run:
```bash
for g in baoma student sme-founder senior office-worker freelancer creator; do
  if grep -q "匹配标签" /workspace/vibe-need-judge/references/agents/consumer-groups/$g.md; then
    echo "$g: OK"
  else
    echo "$g: MISSING 匹配标签"
  fi
done
```
Expected: all 7 print `OK`

- [ ] **Step 9: Commit**

```bash
cd /workspace && git add vibe-need-judge/references/agents/consumer-groups/ && git commit -m "feat(vibe-need-judge): add 7 consumer group core profiles"
```

---

## Task 6: Case Library (7 files)

**Files:**
- Create: `vibe-need-judge/references/case-library/baoma-cases.md`
- Create: `vibe-need-judge/references/case-library/student-cases.md`
- Create: `vibe-need-judge/references/case-library/sme-founder-cases.md`
- Create: `vibe-need-judge/references/case-library/senior-cases.md`
- Create: `vibe-need-judge/references/case-library/office-worker-cases.md`
- Create: `vibe-need-judge/references/case-library/freelancer-cases.md`
- Create: `vibe-need-judge/references/case-library/creator-cases.md`

- [ ] **Step 1: Create baoma-cases.md**

Write to `vibe-need-judge/references/case-library/baoma-cases.md`:

```markdown
# 宝妈·案例库

## 使用说明
本文件仅在子 agent 判定"画像不足以决策"（NEEDS_CASES=yes）时按需读取。
读取时只读与当前产品最相关的 1-2 个案例，不全读。

## 案例索引（按场景）
- 育儿管理类 → 案例1, 案例2
- 家庭电商类 → 案例3
- 健康管理类 → 案例4
- 教育辅助类 → 案例5, 案例6

## 案例1：某育儿记录App（痛点）
产品: 记录宝宝喂奶/睡眠/生长曲线，含妈妈群对比
宝妈真实反应: 生完孩子脑子不够用，终于有个地方记，还能跟同期妈妈对比发育
为什么是痛点: 刚需（怕记漏）+ 群体对比焦虑 + 操作极简
付费情况: 愿付年费（省心 + 孩子好）
关键洞察: 宝妈为"省心+孩子好"付费，且群体对比功能放大留存

## 案例2：某AI育儿助手（自嗨）
产品: AI 根据宝宝数据生成"个性化育儿方案"
宝妈真实反应: 看不懂方案，不如问妈妈群；方案太通用，像百度搜的
为什么是自嗨: 创作者以为 AI 加持=价值，但宝妈要的是"具体怎么做"，不是"通用方案"
付费情况: 不付费
关键洞察: "AI加持"对宝妈不构成价值，具体可执行才构成价值

## 案例3：某家庭采购拼团（痒点）
产品: 小区妈妈拼团买日用品
宝妈真实反应: 便宜但麻烦，要凑单要等；不如拼多多直接买
为什么是痒点: 有用但非刚需，平替太多
付费情况: 不付费，用完即走
关键洞察: 有"省心"属性但替代方案多，留不住

## 案例4：某产后健康管理（痛点但跑不通）
产品: 产后抑郁+身体恢复追踪
宝妈真实反应: 真的需要，但 App 字小操作复杂
为什么是痛点但跑不通: 需求真但产品形态不适合（操作复杂违反宝妈行为模式）
付费情况: 愿付但用不起来
关键洞察: 痛点≠能跑通，产品形态必须匹配群体行为模式

## 案例5：某AI早教（痒点）
产品: AI 生成早教内容推给孩子
宝妈真实反应: 怕孩子看手机伤眼，不如买绘本
为什么是痒点: 解决的是"宝妈焦虑"但方式不被接受
付费情况: 试用不付费
关键洞察: 创作者以为"早教=刚需"，但宝妈对"屏幕早教"有抵触

## 案例6：某妈妈社区+电商（痛点）
产品: 妈妈社区+精准母婴电商
宝妈真实反应: 在社区学到东西，顺手买推荐的，比小红书更垂直
为什么是痛点: 内容+信任+购买闭环，群体影响放大转化
付费情况: 高复购
关键洞察: 宝妈群体在"信任社区+精准电商"上付费意愿强
```

- [ ] **Step 2: Create student-cases.md**

Write to `vibe-need-judge/references/case-library/student-cases.md`:

```markdown
# 学生·案例库

## 使用说明
本文件仅在子 agent 判定"画像不足以决策"（NEEDS_CASES=yes）时按需读取。
读取时只读与当前产品最相关的 1-2 个案例，不全读。

## 案例索引（按场景）
- 学习辅助类 → 案例1, 案例2
- 考试备考类 → 案例3
- 校园社交类 → 案例4
- 效率工具类 → 案例5, 案例6

## 案例1：某刷题App（痛点）
产品: 按考点刷题+错题本+同学排名
学生真实反应: 老师推荐的，同学都在刷，排名压力推着用
为什么是痛点: 刚需（提分）+ 同伴压力 + 排名反馈
付费情况: 愿省饭钱买会员（解锁更多题）
关键洞察: 学生为"提分+同伴竞争"付费，排名机制放大留存

## 案例2：某AI学习助手（自嗨）
产品: AI 根据学习数据生成"个性化学习路径"
学生真实反应: 路径太通用，不如直接刷真题；看不懂建议
为什么是自嗨: 创作者以为 AI=价值，但学生要的是"具体题"，不是"学习建议"
付费情况: 不付费
关键洞察: "AI加持"对学生不构成价值，具体可刷可练才构成价值

## 案例3：某考研单词App（痒点）
产品: 花式背单词+游戏化
学生真实反应: 一开始好玩，3天就不打开了，不如 Anki
为什么是痒点: 有趣但不刚需，平替多
付费情况: 试用不付费
关键洞察: 游戏化对短期留存有效但长期留不住，学生最终回归刚需工具

## 案例4：某校园二手（痛点但跑不通）
产品: 校园二手交易
学生真实反应: 需要但人少，发出去没人买，不如闲鱼
为什么是痛点但跑不通: 需求真但冷启动难
付费情况: 不付费
关键洞察: 痛点≠能跑通，双边市场冷启动是独立难点

## 案例5：某笔记App（痒点）
产品: 花哨笔记+思维导图+协作
学生真实反应: 功能多但学习成本高，记笔记不如 Notion/印象
为什么是痒点: 有用但平替多且更强
付费情况: 不付费
关键洞察: 学生工具若不比现有平替明显更好，留不住

## 案例6：某学习打卡社区（痛点）
产品: 学习打卡+研友监督+排名
学生真实反应: 自制力差正好需要，研友监督有用
为什么是痛点: 解决自制力差刚需 + 同伴监督
付费情况: 愿付监督服务费
关键洞察: 学生为"克服自制力差"付费，监督/陪伴是核心价值
```

- [ ] **Step 3: Create sme-founder-cases.md**

Write to `vibe-need-judge/references/case-library/sme-founder-cases.md`:

```markdown
# 中小企业创业者·案例库

## 使用说明
本文件仅在子 agent 判定"画像不足以决策"（NEEDS_CASES=yes）时按需读取。
读取时只读与当前产品最相关的 1-2 个案例，不全读。

## 案例索引（按场景）
- 企业提效类 → 案例1, 案例2
- 客户管理类 → 案例3
- 财务管理类 → 案例4
- 营销工具类 → 案例5, 案例6

## 案例1：某简易进销存（痛点）
产品: 中小商家用的进销存小程序
老板真实反应: Excel 记老出错，这个手机扫码就能记，月底对账省一天
为什么是痛点: 省时+防错+移动端适配老板碎片时间
付费情况: 愿付月费（看得到省的时间）
关键洞察: 老板为"省时+防错"付费，移动端+极简操作是关键

## 案例2：某AI经营顾问（自嗨）
产品: AI 根据销售数据生成"经营建议"
老板真实反应: 建议太虚，不如我自己判断；看不懂报表
为什么是自嗨: 创作者以为 AI=价值，但老板要的是"具体怎么做"，不是"经营分析"
付费情况: 不付费
关键洞察: "AI加持"对老板不构成价值，可执行的行动才构成价值

## 案例3：某CRM（痒点）
产品: 功能全的 CRM
老板真实反应: 功能多但配置复杂，没专人搞；用不起来
为什么是痒点: 理论上有用但落地难
付费情况: 试用不付费
关键洞察: 中小企业人手不够，复杂工具用不起来，简单才赢

## 案例4：某记账App（痛点但跑不通）
产品: 中小企业记账+报税
老板真实反应: 需要但要对接会计，会计不愿用新工具
为什么是痛点但跑不通: 需求真但涉及多角色协作，会计有惯性
付费情况: 愿付但推不动
关键洞察: B端工具若涉及多角色，任一角色抵触就推不动

## 案例5：某营销自动化（痒点）
产品: 自动发朋友圈+社群运营
老板真实反应: 看着炫但效果不可量化，不如雇个实习生
为什么是痒点: 有用但效果模糊，平替（人工）便宜
付费情况: 不付费
关键洞察: 老板不为"模糊效果"付费，要可量化的 ROI

## 案例6：某同行商机对接（痛点）
产品: 同行业老板群+商机对接
老板真实反应: 同行交流有用，能抢单子
为什么是痛点: 同行信任+商机直接变现
付费情况: 愿付会员费
关键洞察: 老板为"直接赚钱"付费，同行社群+商机是强价值
```

- [ ] **Step 4: Create senior-cases.md**

Write to `vibe-need-judge/references/case-library/senior-cases.md`:

```markdown
# 中老年人·案例库

## 使用说明
本文件仅在子 agent 判定"画像不足以决策"（NEEDS_CASES=yes）时按需读取。
读取时只读与当前产品最相关的 1-2 个案例，不全读。

## 案例索引（按场景）
- 健康管理类 → 案例1, 案例2
- 便民服务类 → 案例3
- 兴趣社交类 → 案例4
- 与子女联系类 → 案例5, 案例6

## 案例1：某吃药提醒（痛点）
产品: 大字+语音吃药提醒，子女可远程设置
老人真实反应: 字大看得清，不用自己设置，子女弄好就行
为什么是痛点: 刚需（忘吃药）+ 子女设置绕过老人学习成本
付费情况: 子女愿付
关键洞察: 老人用、子女付是常见模式，绕过老人学习成本是关键

## 案例2：某AI健康问答（自嗨）
产品: AI 回答老人健康问题
老人真实反应: 不敢信，不如问医生；操作复杂
为什么是自嗨: 创作者以为 AI=价值，但老人对 AI 不信任且操作难
付费情况: 不付费
关键洞察: 老人对 AI 警惕，且操作复杂直接劝退

## 案例3：某便民缴费（痒点）
产品: 集成水电煤缴费
老人真实反应: 微信支付宝已经能缴，多余
为什么是痒点: 有用但平替强
付费情况: 不付费
关键洞察: 老人已习惯微信，非明显更好的工具留不住

## 案例4：某老年相亲（痛点但跑不通）
产品: 老年相亲App
老人真实反应: 需要但不识字/不会注册/怕骗
为什么是痛点但跑不通: 需求真但信任+操作门槛高
付费情况: 愿付但用不起来
关键洞察: 银发需求真但产品形态必须极简+线下结合

## 案例5：某家庭相册（痒点）
产品: 家庭共享相册
老人真实反应: 想看孙子照片，但要上传太复杂
为什么是痒点: 需求真但操作门槛高
付费情况: 不付费
关键洞察: 老人端只能"看"，不能要求"传"，单向接收才可行

## 案例6：某孙辈视频通话（痛点）
产品: 极简视频通话，子女一键拨入
老人真实反应: 不用操作，子女打过来就接，能看孙子
为什么是痛点: 刚需（想孙子）+ 零操作门槛
付费情况: 子女愿付
关键洞察: 老人端零操作+子女端主动，是银发产品的核心模式
```

- [ ] **Step 5: Create office-worker-cases.md**

Write to `vibe-need-judge/references/case-library/office-worker-cases.md`:

```markdown
# 职场白领·案例库

## 使用说明
本文件仅在子 agent 判定"画像不足以决策"（NEEDS_CASES=yes）时按需读取。
读取时只读与当前产品最相关的 1-2 个案例，不全读。

## 案例索引（按场景）
- AI工具类 → 案例1, 案例2
- 效率工具类 → 案例3, 案例4
- 知识管理类 → 案例5
- 会议记录类 → 案例6

## 案例1：某AI会议记录（痛点）
产品: 自动开会转文字+提炼待办
白领真实反应: 开会不用手记，会后直接发纪要，省半小时
为什么是痛点: 省时明确+融入工作流+可晒给老板看
付费情况: 愿付月费（看得到省的时间）+ 可报销
关键洞察: 白领为"真省时+可报销"付费，融入工作流是留存关键

## 案例2：某AI写作助手（自嗨）
产品: AI 帮写工作汇报
白领真实反应: 写得假，不如自己改；老板一眼看出AI味
为什么是自嗨: 创作者以为 AI=价值，但产出不可直接用
付费情况: 试用不付费
关键洞察: "AI加持"不构成价值，产出能直接用才构成价值

## 案例3：某番茄钟App（痒点）
产品: 花哨番茄钟+统计
白领真实反应: 一开始新鲜，3天就不开了，手机自带专注模式够用
为什么是痒点: 有用但平替多且非刚需
付费情况: 不付费
关键洞察: 已有平替的工具，白领不留

## 案例4：某日程管理（痛点但跑不通）
产品: AI 自动排日程
白领真实反应: 需要但跟 Outlook 日历不同步，两处维护更累
为什么是痛点但跑不通: 需求真但不融入现有工作流
付费情况: 不付费
关键洞察: 白领工具必须融入现有工作流，另起炉灶=死

## 案例5：某笔记App（痒点）
产品: 花哨笔记+协作
白领真实反应: 功能多但学习成本高，Notion/飞书够用
为什么是痒点: 平替强且免费
付费情况: 不付费
关键洞察: 白领工具若不比现有平替明显更好，留不住

## 案例6：某待办同步（痛点）
产品: 跨设备待办+团队共享
白领真实反应: 手机电脑同步，团队分工清楚，比便签强
为什么是痛点: 融入工作流+跨设备+协作
付费情况: 愿付+可报销
关键洞察: 融入工作流+协作属性的工具白领愿付费
```

- [ ] **Step 6: Create freelancer-cases.md**

Write to `vibe-need-judge/references/case-library/freelancer-cases.md`:

```markdown
# 自由职业者/独立开发者·案例库

## 使用说明
本文件仅在子 agent 判定"画像不足以决策"（NEEDS_CASES=yes）时按需读取。
读取时只读与当前产品最相关的 1-2 个案例，不全读。

## 案例索引（按场景）
- 开发者工具类 → 案例1, 案例2
- 副业工具类 → 案例3
- 自动化类 → 案例4
- 独立产品类 → 案例5, 案例6

## 案例1：某API监控（痛点）
产品: API 健康监控+告警
开发者真实反应: 自己写过但维护累，这个便宜还能省事
为什么是痛点: 省重复劳动+无完美开源平替+便宜
付费情况: 愿付月费（算过比自己写省）
关键洞察: 开发者为"省重复劳动+无平替"付费，但要算得过账

## 案例2：某AI代码生成（自嗨）
产品: AI 生成整个项目脚手架
开发者真实反应: 生成的代码质量差还得改，不如自己写；我懂技术不需要
为什么是自嗨: 创作者以为 AI=价值，但目标用户自己能写且质量要求高
付费情况: 不付费
关键洞察: 给开发者的工具若质量不如用户自己写，必死

## 案例3：某副业idea生成（痒点）
产品: AI 生成副业点子
开发者真实反应: 点子谁都有，难的是执行；生成的太通用
为什么是痒点: 有趣但非刚需，执行才是瓶颈
付费情况: 不付费
关键洞察: 开发者不为"点子"付费，为"省执行"付费

## 案例4：某自动化工作流（痛点但跑不通）
产品: 可视化自动化工作流
开发者真实反应: 强大但学习成本高，简单需求 n8n 够用，复杂需求写代码
为什么是痛点但跑不通: 需求真但夹在"简单平替"和"自己写"之间
付费情况: 试用不付费
关键洞察: 中间定位的工具最尴尬，要么极简要么极强

## 案例5：某独立产品变现工具（自嗨）
产品: 独立开发者一键变现SDK
开发者真实反应: 看着好但接入复杂，且分成高，不如直接收款码
为什么是自嗨: 创作者=用户时的典型错觉，"我觉得有用=大家有用"
付费情况: 不付费
关键洞察: 给独立开发者的工具，创作者=用户时尤其要警惕自嗨

## 案例6：某重复请求批处理（痛点）
产品: 批量 API 请求+重试+结果聚合
开发者真实反应: 自己写过但每次重写，这个一次配置就跑
为什么是痛点: 省重复劳动+无完美平替+便宜
付费情况: 愿付
关键洞察: 开发者为"省重复劳动"且"无完美平替"的工具付费
```

- [ ] **Step 7: Create creator-cases.md**

Write to `vibe-need-judge/references/case-library/creator-cases.md`:

```markdown
# 内容创作者/自媒体·案例库

## 使用说明
本文件仅在子 agent 判定"画像不足以决策"（NEEDS_CASES=yes）时按需读取。
读取时只读与当前产品最相关的 1-2 个案例，不全读。

## 案例索引（按场景）
- 内容生产类 → 案例1, 案例2
- 多平台运营类 → 案例3
- 涨粉变现类 → 案例4, 案例5
- 数据分析类 → 案例6

## 案例1：某AI剪辑助手（痛点）
产品: AI 自动剪口播+加字幕+转场
创作者真实反应: 省剪一条视频2小时，一个月省60小时，太值
为什么是痛点: 省重复劳动明确+时间可量化+产出直接用
付费情况: 愿付月费（算过省的时间值）
关键洞察: 创作者为"省可量化时间"付费，产出能直接用是关键

## 案例2：某AI文案生成（自嗨）
产品: AI 生成爆款文案
创作者真实反应: 生成的假大空，平台会限流；不如自己写有个性
为什么是自嗨: 创作者以为 AI=价值，但产出不可直接用且平台惩罚
付费情况: 不付费
关键洞察: "AI加持"不构成价值，产出能直接用且不被平台惩罚才构成价值

## 案例3：某多平台分发（痒点）
产品: 一键分发到多平台
创作者真实反应: 看着好但各平台格式不同，还要手动调；免费的也有
为什么是痒点: 有用但平替多+效果不可量化
付费情况: 试用不付费
关键洞察: 已有平替且效果模糊的工具，创作者不留

## 案例4：某数据看板（痛点但跑不通）
产品: 多平台数据汇总看板
创作者真实反应: 需要但平台 API 限制多，数据不准
为什么是痛点但跑不通: 需求真但平台限制导致数据失真
付费情况: 愿付但用不起来
关键洞察: 依赖第三方平台 API 的工具，平台限制是独立风险

## 案例5：某涨粉训练营（痒点）
产品: AI 生成涨粉方案
创作者真实反应: 方案太通用，不如看同行案例；执行才是瓶颈
为什么是痒点: 有趣但非刚需，方案≠执行
付费情况: 不付费
关键洞察: 创作者不为"方案"付费，为"可执行且能涨粉"付费

## 案例6：某变现对接（痛点）
产品: 创作者与品牌方对接平台
创作者真实反应: 终于不用自己接单了，平台撮合+担保
为什么是痛点: 直接变现+省对接成本+担保交易
付费情况: 愿付佣金
关键洞察: 创作者为"直接变现"付费，撮合+担保是核心价值
```

- [ ] **Step 8: Validate all 7 case library files**

Run:
```bash
for g in baoma student sme-founder senior office-worker freelancer creator; do
  echo "=== $g ==="
  count=$(grep -c "^## 案例" /workspace/vibe-need-judge/references/case-library/$g-cases.md)
  echo "cases: $count"
done
```
Expected: each prints `cases: 6`

- [ ] **Step 9: Commit**

```bash
cd /workspace && git add vibe-need-judge/references/case-library/ && git commit -m "feat(vibe-need-judge): add 7 consumer group case libraries (6 cases each)"
```

---

## Task 7: Verdict Report Template

**Files:**
- Create: `vibe-need-judge/templates/verdict-report.md`

- [ ] **Step 1: Create the verdict report template**

Write to `vibe-need-judge/templates/verdict-report.md`:

```markdown
# Vibe 需求裁决报告

> 本模板由主流程第3步加权裁决后填充。紧凑版总 token ≤1200。
> 用户要求完整辩论实录时，追加"## 完整辩论实录"章节或单独保存 verdict-full.md。

## 一句话裁决
【痛点 / 痒点 / 自嗨】— <一句话理由>

## 输入阶段识别
【想法点子 / PRD说明 / 成品URL】

## 产品画像摘要
- 领域: <...>
- 核心场景: <...>
- 付费来源: <...>
- 技术形态: <...>

## 评分总览
| 维度 | 得分 | 主要打分方 |
|---|---|---|
| 需求真伪度 | x.x/10 | 消费群体 |
| 付费/留存意愿 | x.x/10 | 消费群体 |
| 技术可行性 | x.x/10 | 代码工程师 |
| 市场可跑通 | x.x/10 | 增长+竞品 |
| 合规风险 | x.x/10 | 备案中介 |
| **加权总分** | **x.x/10** | |

## 消费群体陪审团（动态加权）
| 群体 | 相关度 | 权重 | USE | PAY | PAIN_MATCH | 匹配理由 |
|---|---|---|---|---|---|---|
| <群体1> | <1-3> | <%> | <1-10> | <1-10> | <痛点/痒点/自嗨> | <一句话> |
| <群体2> | <1-3> | <%> | <1-10> | <1-10> | <痛点/痒点/自嗨> | <一句话> |
| <群体3> | <1-3> | <%> | <1-10> | <1-10> | <痛点/痒点/自嗨> | <一句话> |

## 关键论点（每方≤2条）
- <群体1 emoji> <群体1>: <KEY_ARG>
- <群体2 emoji> <群体2>: <KEY_ARG>
- <群体3 emoji> <群体3>: <KEY_ARG>
- 🧑‍💻 产品经理: <关键论点>
- 🛠️ 代码工程师: <关键论点>
- 📋 备案中介: <关键论点>
- 🥊 竞品分析师: <关键论点>
- 📈 增长黑客: <关键论点>

## 分歧点（第2轮质询结果）
1. <分歧点> — 双方补证各一句
2. <分歧点> — 双方补证各一句
（无分歧时写"首轮无关键分歧"）

## 置信度
【高 / 中 / 低】— <理由：如"3群体一致判痒点，分歧仅1点"或"群体立场分裂，置信度低">

## 关键风险点
1. <风险> — <来源agent>
2. <风险> — <来源agent>
3. <风险> — <来源agent>
（Top 2-3 个最可能导致项目失败的因素）

## 建设性意见
- <2-3条可执行改进方向，或"建议放弃"理由>
（必须引用辩论中具体 agent 的 KEY_ARG，禁止空话）

---

## 完整辩论实录（可选，用户要求时追加）

### 第0步：产品画像
<产品画像解析输出>

### 第1轮：独立举证

#### 消费群体子agent
<群体1 5字段输出>
<群体2 5字段输出>
<群体3 5字段输出>

#### 专家证人
产品经理:
<完整发言>

代码工程师:
<完整发言>

备案中介:
<完整发言>

竞品分析师:
<完整发言>

增长黑客:
<完整发言>

### 第2轮：分歧聚焦质询
分歧点1: <描述>
- 专家补证: <...>
- <涉分歧群体> 补证: <...>

### 第3步：加权裁决计算
<各维度得分计算过程>
<动态权重计算>
<最终裁决>
```

- [ ] **Step 2: Validate the template has all required sections**

Run:
```bash
grep -c "^##" /workspace/vibe-need-judge/templates/verdict-report.md
```
Expected: `11` (一句话裁决、输入阶段识别、产品画像摘要、评分总览、消费群体陪审团、关键论点、分歧点、置信度、关键风险点、建设性意见、完整辩论实录)

- [ ] **Step 3: Commit**

```bash
cd /workspace && git add vibe-need-judge/templates/verdict-report.md && git commit -m "feat(vibe-need-judge): add verdict report template with 11 sections"
```

---

## Task 8: End-to-End Test Cases

**Files:**
- Create: `tests/test-cases.md`
- Create: `tests/run-test.md`

- [ ] **Step 1: Create test-cases.md with 3 representative test cases**

Write to `tests/test-cases.md`:

```markdown
# vibe-need-judge 测试用例

> 3 个代表性测试用例，验证 skill 在自嗨/痒点/痛点三档下的表现。
> 运行方式见 `run-test.md`。

## 测试用例1：明显自嗨

### 输入
"我想做个 AI 应用，给程序员写诗鼓励他们，因为程序员压力大"

### 预期
- 输入阶段识别: 想法点子
- 匹配群体: 自由职业者/独立开发者(3) + 职场白领(2)
- 裁决: 自嗨
- 关键验证点:
  - 自由职业者 PAY_INTENT < 3（程序员不会为"写诗"付费）
  - 增长黑客指出 CAC>LTV（没人为这个付费，获客成本无法覆盖）
  - 报告含"关键风险点"和"建设性意见"
  - 报告 token 在预算内

### 验证清单
- [ ] 群体匹配命中自由职业者（程序员群体）
- [ ] 自由职业者子 agent PAY_INTENT ≤ 3
- [ ] 至少1个专家证人 VERDICT=自嗨
- [ ] 最终裁决=自嗨
- [ ] 报告字段完整（11个章节）
- [ ] 建设性意见引用具体 KEY_ARG，无空话

## 测试用例2：典型痒点

### 输入
"做个 AI 帮人取网名，根据性格+爱好生成个性化网名"

### 预期
- 输入阶段识别: 想法点子
- 匹配群体: 学生(3) + 内容创作者(2) + 职场白领(1)
- 裁决: 痒点
- 关键验证点:
  - 学生 USE_INTENT ≥ 6（会用）但 PAY_INTENT ≤ 4（不付费）
  - 增长黑客指出留存差（用一次就走）+ 无裂变路径
  - 报告含"如何转痒点为痛点"建设性意见

### 验证清单
- [ ] 群体匹配命中学生
- [ ] 学生 USE_INTENT ≥ 6 且 PAY_INTENT ≤ 4
- [ ] 增长黑客指出留存/裂变问题
- [ ] 最终裁决=痒点
- [ ] 建设性意见针对"痒点档"（转痛点建议）

## 测试用例3：真痛点

### 输入
"做个中小商家用的简易进销存小程序，手机扫码进出货，月底自动对账，月费29元"

### 预期
- 输入阶段识别: PRD说明
- 匹配群体: 中小企业创业者(3)
- 裁决: 痛点
- 关键验证点:
  - 中小企业创业者 PAY_INTENT ≥ 6（愿付费，29元可接受）
  - 代码工程师确认技术可行（小程序+扫码+对账都是成熟方案）
  - 备案中介指出门槛（小程序需企业资质，但非阻塞）
  - 报告含"如何放大优势"建设性意见

### 验证清单
- [ ] 群体匹配命中中小企业创业者
- [ ] 中小企业创业者 PAY_INTENT ≥ 6
- [ ] 代码工程师 SCORE ≥ 7
- [ ] 最终裁决=痛点
- [ ] 建设性意见针对"痛点档"（放大优势建议）
- [ ] 备案中介提及资质但不判死刑
```

- [ ] **Step 2: Create run-test.md with validation procedure**

Write to `tests/run-test.md`:

```markdown
# vibe-need-judge 测试运行说明

> 本文件说明如何运行 3 个测试用例验证 skill。

## 前置条件

1. skill 已完整安装到 `vibe-need-judge/`
2. 所有文件存在（Task 1-7 已完成）
3. 宿主 AI 能识别并触发 `vibe-need-judge` skill

## 运行步骤

对 `test-cases.md` 中的每个测试用例：

### Step 1: 触发 skill
向宿主 AI 输入测试用例的"输入"部分，确认 skill 被触发。

### Step 2: 观察执行
确认 skill 按以下流程执行：
1. 第0步：识别输入阶段 + 解析产品画像 + 匹配群体
2. 第1轮：消费群体子 agent 并行 + 专家证人依次发言
3. 第2轮：分歧点识别 + 涉分歧群体补证
4. 第3步：加权裁决 + 输出报告

### Step 3: 检查输出报告
对照测试用例的"验证清单"，逐项检查输出报告：
- 群体匹配是否准确
- 关键数值（USE_INTENT/PAY_INTENT/SCORE）是否在预期范围
- 裁决档位是否正确
- 报告字段是否完整（11个章节）
- 建设性意见是否符合档位规则且无空话

### Step 4: 检查 token 预算
估算总 token 消耗是否在 8000 以内（不含用户输入）。
若超 7500，确认是否触发降级规则。

## 通过标准

每个测试用例的所有验证清单项全部通过，该测试用例算通过。
3 个测试用例全部通过，skill 验收通过。

## 失败处理

若某测试用例失败：
1. 记录失败项
2. 检查对应文件内容是否需修正（角色卡/画像/案例库/规则）
3. 修正后重跑该测试用例
4. 不影响其他测试用例的独立验证

## 已知局限（不视为失败）

- 消费群体是模拟的，PAY_INTENT 数值有波动正常，只要在预期范围内即可
- 专家证人在主上下文扮演，可能有立场泄漏，但消费群体子 agent 独立性应对冲
- 无真实数据，裁决是理性推断非市场验证
```

- [ ] **Step 3: Validate test files exist**

Run:
```bash
ls -la /workspace/tests/
```
Expected: `test-cases.md` and `run-test.md` both present

Run:
```bash
grep -c "## 测试用例" /workspace/tests/test-cases.md
```
Expected: `3`

- [ ] **Step 4: Commit**

```bash
cd /workspace && git add tests/ && git commit -m "test(vibe-need-judge): add 3 end-to-end test cases and run procedure"
```

---

## Task 9: SKILL.md Main Entry

**Files:**
- Create: `vibe-need-judge/SKILL.md`

- [ ] **Step 1: Create the main SKILL.md**

Write to `vibe-need-judge/SKILL.md`:

```markdown
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
```

- [ ] **Step 2: Validate SKILL.md has frontmatter and all main sections**

Run:
```bash
head -5 /workspace/vibe-need-judge/SKILL.md
```
Expected: starts with `---` (YAML frontmatter)

Run:
```bash
grep -c "^### " /workspace/vibe-need-judge/SKILL.md
```
Expected: ≥ `4` (第0步、第1轮、第2轮、第3步)

Run:
```bash
grep -c "references/" /workspace/vibe-need-judge/SKILL.md
```
Expected: ≥ `8` (links to all reference files)

- [ ] **Step 3: Commit**

```bash
cd /workspace && git add vibe-need-judge/SKILL.md && git commit -m "feat(vibe-need-judge): add main SKILL.md with full flow and reference index"
```

---

## Self-Review

### 1. Spec coverage check

| Spec 要求 | 对应 Task | 覆盖？ |
|---|---|---|
| 第1节：总体架构与文件结构 | 所有 Task（文件结构即任务） | ✅ |
| 第2节：多 Agent 角色定义与辩论协议 | Task 2 (debate-protocol) + Task 3 (角色卡) + Task 4 (子agent模板) | ✅ |
| 第2节：Token 预算 8000 + 降级规则 | Task 2 (debate-protocol 含完整预算表和降级规则) | ✅ |
| 第2节：子 agent 5字段输出 | Task 4 (_subagent-template 含5字段) | ✅ |
| 第3节：三档裁决 + 5维度 + 动态权重 | Task 1 (scoring-rubric) | ✅ |
| 第3节：裁决报告格式（11字段） | Task 7 (verdict-report template) | ✅ |
| 第3节：建设性意见规则 | Task 1 (scoring-rubric 含规则) | ✅ |
| 第4节：触发条件 + 主流程 | Task 9 (SKILL.md) | ✅ |
| 第4节：群体匹配规则 | Task 4 (_matching-rubric) | ✅ |
| 第4节：子 agent 派发模板 | Task 4 (_subagent-template) | ✅ |
| 第5节：5个角色卡 | Task 3 | ✅ |
| 第5节：7个群体画像 | Task 5 | ✅ |
| 第5节：7个案例库 | Task 6 | ✅ |
| 第5节：评分规则文件 | Task 1 | ✅ |
| 第5节：辩论协议文件 | Task 2 | ✅ |
| 第6节：边界情况 | Task 9 (SKILL.md 含边界) + Task 2 (debate-protocol 含降级) + Task 4 (matching-rubric 含边界) | ✅ |
| 第6节：输入阶段可信度 | Task 9 (SKILL.md) | ✅ |
| 第6节：3个测试用例 | Task 8 | ✅ |
| 第6节：已知局限 | Task 9 (SKILL.md) | ✅ |

**所有 spec 要求均有对应 Task 覆盖，无遗漏。**

### 2. Placeholder scan

- ❌ "TBD" / "TODO" / "implement later" — 未出现
- ❌ "add appropriate error handling" — 未出现
- ❌ "write tests for the above" (无具体测试) — Task 8 有具体测试用例和验证清单
- ❌ "similar to Task N" — 每个群体的画像/案例库都完整写出，未引用其他 Task
- ❌ 步骤只描述不展示 — 所有步骤含完整文件内容
- ✅ `<...>` 占位符仅出现在模板字段定义里（如 `<群体名>`、`<x.x/10>`），是模板的合法用法

**无 placeholder 问题。**

### 3. Type/field consistency check

| 字段/名称 | 定义处 | 使用处 | 一致？ |
|---|---|---|---|
| `USE_INTENT / PAY_INTENT / PAIN_MATCH / KEY_ARG / NEEDS_CASES` | Task 4 (_subagent-template) | Task 9 (SKILL.md 第1轮) + Task 7 (verdict-report) + Task 8 (测试用例) | ✅ |
| `VERDICT / SCORE / KEY_ARG / DETAIL` | Task 3 (角色卡) | Task 8 (测试用例提及 VERDICT/SCORE) | ✅ |
| 相关度 0/1/2/3 | Task 4 (_matching-rubric) | Task 1 (scoring-rubric 动态权重) + Task 9 (SKILL.md) | ✅ |
| 三档分数线 7.0 / 4.0 | Task 1 (scoring-rubric) | Task 9 (SKILL.md 第3步) + Task 8 (测试用例预期) | ✅ |
| Token 预算 8000 / 7500 | Task 2 (debate-protocol) | Task 9 (SKILL.md 第2轮) | ✅ |
| 权重 60% / 40% / 各8% | Task 1 (scoring-rubric) | Task 9 (SKILL.md 第3步) | ✅ |
| `HOLD_OR_REVISE / REASON / NEW_EVIDENCE` | Task 4 (_subagent-template 第2轮) | Task 9 (SKILL.md 第2轮引用"第2轮补证派发 prompt") | ✅ |

**字段名称在所有 Task 间一致，无拼写/命名漂移。**

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-07-18-vibe-need-judge.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
