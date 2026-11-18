---
spec_id: <slug>          # 与 spec.md 同名
spec_version: v1         # 本 plan 依据的规格版本
status: draft            # draft | approved
created_at: YYYY-MM-DD
---

# Implementation Plan: <特性名>

> **HOW 的归宿**：技术选型、文件路径、模块划分、数据模型、测试策略只出现在本文件。
> 上游真源是 `./spec.md`（WHAT/WHY）；本文件每节都应能追到某条 FR 或 US。

## Summary

<1-3 段：主要需求 + 技术路线>

## Technical Context

| 字段 | 值 |
|------|----|
| 语言 / 版本 |  |
| 主要依赖 |  |
| 存储 |  |
| 测试 |  |
| 目标平台 |  |
| 项目类型 | web-service / library / cli / mobile / backend |
| 性能目标 | <可度量> |
| 约束 |  |
| 规模 |  |

> 未知项写 `[NEEDS CLARIFICATION: <问题>]`（与 spec 同形同方括号），**全文上限 3 个**，不得留空。
> 该标记只用于 plan 内的待定技术项；`spec-clarity-gate.mjs` 当前只扫 spec.md，**不扫 plan**——
> 所以 plan 的遗留标记靠 code-review 维度 0 人工兜底，别指望门禁替你抓。

## Constitution Check

*门禁：Phase 0 研究前必须过；Phase 1 设计后复查。违规则必须在 Complexity Tracking 书面论证。*

| 门禁 | 结论 | 一句话理由 |
|------|------|-----------|
| 简洁门（初始实现 ≤3 个项目，直接用框架不包装） | pass / violation |  |
| 反抽象门（仅当有 2+ 真实调用方才抽层） | pass / violation |  |
| 契约优先门（先契约/接口，后实现） | pass / violation |  |
| 项目宪法其他条款 | pass / violation |  |

## Key Decisions

| 决策 | 理由 | 被否定的替代方案 |
|------|------|-----------------|
|  |  |  |

> 涉及框架/库/架构/合规的决策另立 ADR（RULE-019），本表指向 ADR 编号。

## System Modules

| 模块 | 职责 | 关键接口 | 依赖 | 错误处理 |
|------|------|---------|------|---------|

## Data Model

<ER 图 / 实体字段 / 校验规则 / 状态迁移>

## Testing Strategy

| US / FR | 验证动作 | 类型（单测/集成/契约/E2E/人工） |
|---------|---------|-------------------------------|
| US-01 / FR-001 |  |  |

> 每行必须对应 spec 里的一个 US 或验收场景——这是 FR 覆盖率的判据。

## Complexity Tracking

*仅在 Constitution Check 有 violation 时填写。*

| 违规模 | 为什么需要 | 被否定的更简单替代方案 |
|--------|-----------|----------------------|
|  |  |  |

## Risks

| 风险 | 影响 | 缓解 |
|------|------|------|
|  |  |  |

---

**审批**：plan 经用户批准后进入 `/plan` 产出的 tasks，或直接 `/test` 开始 RED 阶段。
