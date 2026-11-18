---
name: agent-constraints
version: v2.1.0
type: rule
enabled: true
mode: [standard, creator]
updated: 2026-11-11
description: Agent 行为约束 — Agent 生成代码必须通过项目已配置的 Linter（RULE-028）。RULE-026/027/029 已废弃，由运行时会话/轨迹能力替代
applies_to:
  agents: ['全部 Agent']
  phases: ['全程']
  project_types: ['全部']
  tech_stacks: ['全部']
---
# Agent 行为约束规范 (Agent Constraints)
> **本文件落实**: RULE-028（Agent 生成代码必须通过 Linter 检查）

> **v2.0.0 精简说明（ADR-006）**：删除原 RULE-026（上下文审计日志）、RULE-027（分布式锁）、RULE-029（断点续传快照）及全部内嵌示例实现。这些机制现由运行时的会话持久化与轨迹日志原生承担，无需 Agent 自建。详见文末"已废弃规则"。

## RULE-028: Agent 生成代码 Linter 检查

### 规则说明

Agent 生成的代码必须通过**项目已配置**的 Linter / 类型检查 / 格式工具，保证与项目既有风格和约束一致。

### 执行要求

1. **以项目配置为准**：读取项目 `tech-stack.md` 与根目录配置（`pyproject.toml`、`.eslintrc*`、`tsconfig.json` 等），只运行项目**已声明**的工具。
   - 项目**没有**配置的工具（如未启用 mypy 的项目）不强制，不得凭空引入并以其报警阻断。
2. **典型基线**（项目配置了才执行）：
   - Python：`ruff check`、`ruff format --check`；配置了则加 `mypy`、`bandit`。
   - TypeScript/React：`eslint`、`tsc --noEmit`；配置了则加 `prettier --check`。
3. **失败处理**：
   - 优先自动修复（`ruff check --fix`、`eslint --fix`、`prettier --write`）。
   - 无法自动修复时，报告具体错误与文件位置并停止，不得跳过。
   - 禁止在 Linter 未通过时声称"完成"。
4. **无 Linter 的项目**：至少保证代码可解析、可导入（语法正确），并在提交说明中注明项目尚未配置 Linter。
5. **子智能体同受本规则约束**：按 `rules/collaboration.md` §2.5 派发的每个子 Agent，其产出代码**同样必须**通过项目已配置的 Linter / 类型检查；并行**不豁免**本条验证（子 Agent 各自带验证证据）。

### Enforcement

- 由项目 pre-commit / CI 执行（Python 栈模板 `templates/pre-commit/python.yaml`，前端栈模板 `templates/pre-commit/frontend.yaml`；复制到项目根后改名为 `.pre-commit-config.*.yaml`）。
- 辅助脚本：`hooks/scripts/agent_linter_checker.py`（手动/CI 调用）。

---

## 已废弃规则（ADR-006，2026-10-01）

| 编号 | 规则名 | 废弃原因 | 替代方案 |
|------|--------|----------|----------|
| ~~RULE-026~~ | 上下文变更审计日志 | 运行时已提供 append-only 会话与轨迹日志，自建 JSONL 无消费者 | 运行时 trajectory / session 日志 |
| ~~RULE-027~~ | 多 Agent 协作分布式锁 | v4.0.0 已废弃 | 单 Agent + subagent，无需分布式锁 |
| ~~RULE-029~~ | 长时间任务断点续传（Redis + 文件快照） | 运行时 session resume/fork 原生支持；强制 Redis 对个人项目不可行 | 会话持久化 + 任务文件（`docs/tasks/<id>/tasks.md`，v4.16.0 起为目录式命名） |

> 归档脚本见 `hooks/scripts/archive/agent_snapshot_manager.py`（仅历史参考）。
