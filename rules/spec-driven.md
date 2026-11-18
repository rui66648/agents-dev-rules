---
name: spec-driven
version: v1.0.0
type: rule
enabled: true
mode: [standard, creator]
description: 规范驱动开发（SDD/SSD）规格模型 — 规格锚定、WHAT/HOW 分离、澄清门禁、规格-代码绑定与体量纪律（RULE-055，ADR-008）
updated: 2026-11-07
applies_to:
  agents: ['architect', 'code-reviewer', '全部 Agent']
  phases: ['design', 'implementation', 'review']
  project_types: ['全部']
  tech_stacks: ['全部']
---
# 规范驱动开发（Spec-Driven Development）— RULE-055

> **本文件落实**: RULE-055。**ADR-008** 为决策依据，调研见
> `docs/research/2026-11-07-spec-driven-development.md`。
>
> **流派声明（一句话）**：本库采纳 **spec-anchored（规格锚定）**——规格是跨会话的唯一记忆，
> 代码向下游可再生；**不**采纳 spec-as-source（"人只改规格、永不碰代码"），那是 2000 年代
> MDD 的结局，个人项目不适用。

## 0. 为什么需要（三个已实证的缺口）

| 缺口 | 症状 | 实证 |
|------|------|------|
| 规格是设计级、不是特性级 | agent 没有 per-feature 施工依据，边界靠脑补 | 本库四文档描述系统形态，无编号功能需求 |
| 规格腐烂且无人发现 | 代码与测试都对，agent 按过期规格自信地做错事 | Ken Imoto 2026-08：幂等键位置漂移 → 按旧规格生成退款处理器 → 双重退款 |
| 歧义被静默填充 | "合理地猜一个"，错了只在集成/生产暴露 | Ken Imoto 案例 2：spec 写"返回 400"，4 万行 CSV 第 14000 行失败，用户传六次 |

> **一句话定位**：SDD 买的是**第二次会话**。第一次会话用 plan mode 就够；跨会话、跨代理、
> 跨周重启时，规格是 agent 唯一没被重置的东西。

## 1. 三条不可协商纪律

### 1.1 规格锚定（spec-anchored）

- 规格（`spec.md`）是**功能级唯一真源**：意图、范围、用户故事、验收场景、编号功能需求。
- 四份设计文档（`architecture.md` / `database-schema.md` / `api-design.md` / `ui-wireframe.md`）
  描述**系统形态与选型**；它们的"功能列表"章节只作**引用**，编号需求以 spec 为准。
- 规格可手工编辑（这是本库与 spec-as-source 的分界），但**改了规格必须同批改代码**（见 §4）。

### 1.2 WHAT ≠ HOW

| 允许出现在 spec | 禁止出现在 spec |
|-----------------|-----------------|
| 意图（一句话）、`scope.in` / `scope.out` | 技术栈/框架/库选择 |
| 用户故事（As a … I want … so that …） | 文件路径、目录结构 |
| 验收场景（Given/When/Then 或 EARS） | 代码块、命令行 flag 清单 |
| 编号功能需求（FR-001…） | 行号引用、具体实现参数 |
| 约束、非功能目标（可度量） | 排序/分页/缓存等实现决策 |

> 与 `rules/hotl-contracts.md` 的"实现泄漏禁令"、`skills/brainstorming/references/design-doc-templates.md` §6
> 同源；此处升格为 **spec 级硬纪律**。HOW 的全部归宿是 `plan.md`。
>
> **分级而非矛盾**：设计文档允许 ≤10 行示例代码块与 `> Example` 包裹的例外（见上引两处），
> spec 对代码块**零容忍**（`spec-clarity-gate.mjs` 有代码块即 FAIL）——spec 比设计文档更严，
> 因为它的读者是 agent 而不是人。

### 1.3 澄清门禁（消灭"合理地瞎猜"）

- 遇到**影响范围/安全/数据语义的关键分歧**且无行业默认值时，必须显式标记：

  ```markdown
  [NEEDS CLARIFICATION: 无登录阶段如何标识操作者——会话选择还是固定账号？]
  ```

- **上限**：单份 spec 最多 3 个标记；有遗留标记时**不得进入 plan / coding**，必须先向用户提问。
- 有行业惯例的地方做合理猜测并记入 `Assumptions`，不占标记额度。
- 问法：一次给出选项表格（A/B/C/自定义），用户回答后回填 spec 并在 `Clarifications` 小节留痕。

## 2. 规格结构（最小骨架）

```markdown
---
spec_id: <slug>          # 与目录同名
status: draft | approved | superseded
spec_version: v1         # 每轮实质修订 +1
created_at: YYYY-MM-DD
---

# <特性名>

## Intent          # 一句话目标 + constraints（不可破坏的东西）
## Scope           # in（表格）/ out（表格，预防 Scope Creep）
## User Stories    # US-01（P1）/ US-02（P2）… 每个独立可交付、独立可测
## Acceptance      # 每个 US 至少一个 Given-When-Then 或 EARS 场景
## Functional Reqs # FR-001 MUST/SHALL …（可测、单一、无歧义）
## Assumptions     # 做出的合理猜测
## Clarifications  # [NEEDS CLARIFICATION] → 已解决记录（问题/答案/日期）
## Open Questions  # 已发现但本轮不问的
```

**优先级口径**：US 按 P1/P2/P3 排序；**P1 单独即可构成可演示的 MVP**。
**可独立测试**：每个 US 必须能脱离其他 US 验证——这条来自 spec-kit 模板的硬要求，
也是 `tasks` 能分阶段的依据。

## 3. 可执行一小步（让规格可验证）

- 每个可交付切片至少一个验收场景，格式二选一：

  ```text
  Given 看板存在一个"待办"任务
  When  成员将其拖入"进行中"
  Then  卡片移动且状态持久化

  # 或 EARS
  WHEN a user submits an email that already exists
  THE SYSTEM SHALL display "Email already registered" error
  ```

- 验收场景必须能在 `tasks.md` 里找到**对应验证动作**（测试命令、可运行步骤、人工验收项）。
  spec-kit 把这称为 "compile the spec to at least one acceptance test"；
  本库口径放宽为"至少一个可执行验证动作"，不必强制自动化。
- **单数—复数自检**：写完每条需求问一句"如果是三千个呢？"（错误全量返回 vs 首个失败；
  一个用户 vs 一万用户）。答"不变"就不用改，答"要分页/批量"就补需求。

## 4. 规格—代码绑定（治漂移）

| 纪律 | 做法 | 检出 |
|------|------|------|
| 合并 PR 记录 spec 版本 | commit message 带 `spec:<slug>@v<N>` | `git log` 可查 |
| 同 PR 内同步 | 改代码行为 → 同 PR 更新对应 FR / 验收场景 | code-review 维度 |
| 漂移即 FAIL | `hooks/scripts/spec-clarity-gate.mjs` 检出**代码改了但 spec 没改** | gate |
| 规格过期即降级 | 规格与实现已知不符且未及时修订时，status 记 `superseded` 并说明 | 人工 |

> 规格是**快照**，不是自履约的契约——没有任何编译器会在你改代码时对你喊。
> 上表四条是替代编译器的工程手段（Ken Imoto 的 Guardrail 1/2 工程化版）。

## 5. 体量纪律（反 Markdown 膨胀）

| 指标 | 上限 | 超出怎么办 |
|------|------|-----------|
| 单份 spec 行数 | ≤ 200 行 | 拆 spec（按 US 边界），不是压缩字号 |
| 单 PR 内 spec 增量 | ≤ 100 行 | 分期交付；本 PR 只带当批 US 的 spec |
| 单份 spec 的 `[NEEDS CLARIFICATION]` | ≤ 3 个（口径见 §1.3） | 先把最关键的问了，其余记 Open Questions |
| spec 内代码块 | 0 | 全是 plan 的活 |

> **依据**：实测数据为 689 行代码生成 2577 行 markdown、spec-kit 自身指令约 18.6k tokens/会话
> （见调研 §4.2）。规格变长的每一行都要 agent 重读，越过窗口就开始被 skim 或丢弃——
> **SDD 治漂移的药和致漂移的病是同一个动作：写更多 Markdown**。所以体量是本规则的硬边界，不是建议。
>
> **与"不设行数阈值"的关系（不矛盾，是分级）**：`rules/collaboration.md` §任务拆解粒度明确
> **不设行数阈值**——那边判的是**代码任务**（行数不是可验证的拆分依据，按依赖与验证点拆）。
> 本表判的是 **spec 文档**，长度直接决定 agent 能否读完，是可度量的审读成本。两个对象不同。

## 6. 分级适用（与 `rules/collaboration.md` 门禁对齐）

| 门禁级 | spec 要求 | 落盘位置 |
|--------|-----------|----------|
| **L0** | 无（对话内说明即可） | — |
| **L1** | 对话内轻量规格：意图 + 范围一句话 + 验收一条 | — |
| **L2** | 落盘完整 spec（§2 骨架） | `docs/tasks/<id>/spec.md` |
| **L3** | spec + design.md（含 Constitution Check 违规模块，见 RULE-056） | 同上 + `docs/tasks/<id>/design.md` |

> 触发检查点沿用 `collaboration.md §分级设计门禁`：任务启动时定级、执行中升级、**禁止降级**。

## 7. 明确不做（NOT list）

| 不做 | 为什么 |
|------|--------|
| ❌ spec-as-source（人不碰代码） | MDD 的历史结局；个人项目无收益 |
| ❌ 全仓强制 SDD | 小改动加流程税，正是 Marmelab 论证的失败形态 |
| ❌ 引入 `specify-cli` / uv 依赖链 | 18.6k tokens/会话指令开销 + Python 3.11+ 依赖，四仓过重（ADR-008 §方案B） |
| ❌ 把 spec 写成第二份设计文档 | 重复既有的四文档，制造第二处真相 |
| ❌ 为填模板编造宪法条款 | brownfield 指南忠告：只写仓里**已成立**的原则（RULE-056 §2） |
| ❌ 用 spec 替代测试 | spec 是输入，不是验证；RULE-003/013 不变 |

## 8. Enforcement

| 规则 | 工具 | 失败语义 |
|------|------|----------|
| RULE-055a 澄清门禁 | `hooks/scripts/spec-clarity-gate.mjs` | 遗留 `[NEEDS CLARIFICATION]` 或超 3 个 → FAIL |
| RULE-055b 结构完整 | 同上：缺 Intent/Scope/US/Acceptance/FR 中任一 → FAIL |
| RULE-055c 体量 | 同上：>200 行 / 代码块存在 → FAIL（HOW 泄漏为 WARN） |
| RULE-055d 漂移 | 同上：spec `spec_version` 落后于代码侧的 `spec:` 标注 → FAIL |
| RULE-055e 无 spec 的仓 | L0/L1 场景默认不落 spec → 仅 WARN，不 FAIL |

挂载：`rules/gate.sh` 第 5 步、`hooks/configs/gate-inventory.yaml`（`spec-clarity-gate`）。

## 9. 与其他规则的关系

- **RULE-001/002（collaboration）**：brainstorming 产出**需求**，spec 是需求的**特性级结构化展开**；
  审批门禁不变，spec 随设计文档同批审批。
- **RULE-004（hotl-contracts）**：hotl 的 `success_criteria` → spec 的 Acceptance；
  `verify_steps` → tasks 的验证动作。三合约仍在**设计文档**里，spec 引用它。
- **RULE-030~033（schema-as-code）**：spec 的 FR 是 schema 的上游；schema 是 FR 的机器化物。两者不合并。
- **RULE-003/013（testing-rules）**：TDD 的"先写测试"现在有了明确输入——spec 的验收场景。
- **RULE-015（YAGNI）**：`scope.out` 是 YAGNI 的显式化。
- **优先级**：冲突时按 `rules/priority-system.md` 裁决。
