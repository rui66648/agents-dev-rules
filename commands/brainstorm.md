---
name: brainstorm
version: v1.0.0
type: command
enabled: true
mode: [standard, creator]
updated: 2026-08-03
description: 斜杠命令：brainstorm - "头脑风暴"、"需求分析"、"方案探索"、"设计一下"
---
# /brainstorm - 需求探索

**触发词**: "头脑风暴"、"需求分析"、"方案探索"、"设计一下"

---

## 命令语法

```
/brainstorm [topic] [--scope=feature|phase|initiative]
```

## 参数说明

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `topic` | string | 否 | 当前上下文 | 需求主题，如 `user-auth`、`payment-integration` |
| `--scope` | enum | 否 | `feature` | 需求范围：`feature`（单功能）、`phase`（迭代阶段）、`initiative`（大型项目） |

## 触发场景

- 新功能开发前，需要明确需求边界和验收标准
- 架构调整或重构前，需要探索多种方案
- API 设计或数据库变更前，需要梳理影响范围
- 不确定"做什么"和"为什么做"时

## 前置条件

1. 用户有模糊的需求描述或问题陈述
2. 项目 `tech-stack.md` 已定义（或本次一并确定）
3. 无未审批的设计文档阻塞

## 执行流程

1. **上下文扫描** — 两阶段扫描：Phase 1 Glob 快速扫描，Phase 2 按项目上下文分支决策
2. **需求探索** — 采用选择题优先 + 开放式回退方式，逐层明确需求
3. **约束识别** — 识别不可破坏的约束条件（技术栈、兼容性、性能基线）
4. **方案对比** — 提供 2-3 种可行方案，对比优劣，YAGNI 审查
5. **HOTL 合约** — 输出 Intent / Verification / Governance 三合约
6. **用户审批** — 等待用户明确批准后进入设计阶段

## 产出物

- `docs/designs/YYYY-MM-DD-<slug>-design.md`：结构化设计文档，含 HOTL 三合约
- 范围边界：明确 `scope.in`（本次包含）和 `scope.out`（明确排除）
- 风险等级：`low` / `medium` / `high`（高风险自动触发人工门禁）

## 错误处理

| 常见错误 | 处理方式 |
|----------|----------|
| 需求范围过大（Scope Creep） | 要求用户明确优先级，拆分为多个 feature 迭代 |
| 用户需求自相矛盾 | 指出矛盾点，要求用户澄清优先级 |
| 缺少关键技术上下文 | 引导用户补充或读取相关文件获取 |
| 高风险需求 | 自动标记为人工门禁，强制用户审批 |

## 示例

```
/brainstorm user-auth --scope=feature
```

**预期输出**：
- 需求文档：用户认证功能设计（注册/登录/密码重置/会话管理）
- 方案对比：JWT vs Session vs OAuth 2.0
- 风险等级：high（涉及安全认证）
- 验收标准：可量化验证的标准列表

---

**执行流程**: 遵循 [brainstorming 技能](skills/brainstorming/SKILL.md`) 的完整流程
**负责代理**: `architect`