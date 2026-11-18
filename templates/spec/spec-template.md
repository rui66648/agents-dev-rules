---
spec_id: <slug>
status: draft            # draft | approved | superseded
spec_version: v1         # 每轮实质修订 +1
created_at: YYYY-MM-DD
gate_level: L2           # L2 | L3
supersedes: —            # 被哪份规格取代（status: superseded 时必填）
---

# <特性名>

> 本文件是**功能级唯一真源**：意图、范围、用户故事、验收场景、编号功能需求。
> 技术选型 / 文件路径 / 代码结构**一律不得出现在此**——那是 `plan.md` 的内容（RULE-055 §1.2）。

## Intent

一句话目标：<做什么、为谁、达成什么效果>

**Constraints（不可破坏的东西）**：
- <例：不能破坏现有 JWT 认证流程>
- <例：必须兼容现有用户数据>

## Scope

### in

| # | 本次包含 | 说明 |
|---|---------|------|
| 1 |  |  |

### out（预防 Scope Creep —— YAGNI 的显式化）

| # | 明确不做 | 为什么 |
|---|---------|--------|
| 1 |  |  |

## User Stories

### US-01: <标题> （优先级 P1 —— 单独即可构成可演示 MVP）

作为 <角色>，我想要 <能力>，以便 <价值>。

**Why this priority**: <为什么它排这个位置>
**Independent Test**: <如何脱离其他 US 单独验证>

### US-02: <标题> （P2）

作为 <角色>，我想要 <能力>，以便 <价值>。

**Why this priority**: 
**Independent Test**: 

## Acceptance

> 每个 US 至少一个场景。格式二选一：**Given/When/Then** 或 **EARS**。
> 每条场景必须能在 `tasks.md` 找到对应验证动作（RULE-055 §3）。

### US-01

```text
Given <前置状态>
When  <动作>
Then  <可观察结果>
```

### US-02

```text
WHEN <事件/条件>
THE SYSTEM SHALL <期望行为>
```

## Functional Reqs

| 编号 | 需求 | 优先级 | 对应 US |
|------|------|--------|---------|
| FR-001 | 系统 MUST <可测的单一行为> | P1 | US-01 |
| FR-002 | 系统 SHALL <可测的单一行为> | P1 | US-01 |
| FR-003 | 系统 MUST <可测的单一行为> | P2 | US-02 |

> **单数—复数自检**：每条问一句"如果是三千个呢？"——答"不变"就不用改，
> 答"要分页/批量/全量错误"就补一条 FR。

## Assumptions

| # | 假设 | 依据 | 若错了影响 |
|---|------|------|-----------|
| 1 | <有行业惯例处做的合理猜测> | <惯例/现有实现> |  |

## Clarifications

| # | 问题 | 答案 | 日期 |
|---|------|------|------|
| 1 | （原 `[NEEDS CLARIFICATION]` 已解决则迁到此处） |  |  |

> 遗留标记上限 3 个；有遗留**不得进入 plan / coding**。

## Open Questions

| # | 问题 | 为何本轮不问 | 何时答 |
|---|------|-------------|--------|
| 1 |  |  |  |

---

**审批**：用户明确批准后才进入 `/plan`；批准记录见 commit message `spec:<slug>@v<N>`。
