# Agent 索引

> 汇总所有子代理的调用关系，包含: 使用规则、使用技能、调用条件。
> 与 `rules/applies_to.md` 互补: 本文件从 Agent 视角出发，applies_to.md 从规则视角出发。

---

## Agent 总览

| Agent | 版本 | 调用条件 | 使用 Rules | 使用 Skills | 输出文档 |
|-------|------|---------|-----------|------------|---------|
| architect | v1.2.0 | 架构决策、模块拆分、任务编排 | architecture, workflow-core, hotl-contracts, collaboration, priority-system, exceptions | project-initiation, brainstorming, system-design, writing-plans, finishing-branch, project-closure, performance-tuning, data-flow-design, integration-design, analytics-design, verification | design-doc.md, plan.md |
| backend-developer | v1.2.0 | 后端开发、API 设计、数据访问 | architecture, security-rules, testing-rules, git-conventions, cicd-rules, coding-standards | executing-plans, api-design, database-migration, deploy, ops-monitoring, refactoring | API spec, migration scripts |
| frontend-developer | v1.2.0 | 前端开发、组件设计、状态管理 | workflow-core, collaboration, anti-patterns, cicd-rules, performance-rules, ui-design-patterns, coding-standards | executing-plans, frontend-component, refactoring | component code, tests |
| ui-designer | v1.0.0 | UI 设计、设计令牌、可访问性 | ui-design-patterns, workflow-design, i18n-design, collaboration | ui-design, i18n-design, refactoring | design-tokens.md, ui-wireframe.md |
| database-expert | v1.1.0 | 数据库设计、迁移、性能优化 | architecture, security-rules, testing-rules, git-conventions | system-design, database-migration, performance-tuning, refactoring | migration scripts, schema docs |
| test-engineer | v1.1.0 | 测试策略、测试执行、质量门禁 | testing-rules, workflow-core, security-rules, anti-patterns | test-strategy, test-driven-development, verification, systematic-debugging | test reports, coverage |
| security-auditor | v1.1.0 | 安全审计、漏洞分析、合规检查 | security-rules, architecture, testing-rules, collaboration, cross-project-conflicts | security-design, ai-safety-check, code-review | security report |
| code-reviewer | v1.2.0 | 代码审查、质量门禁、规范检查 | anti-patterns, collaboration, testing-rules, git-conventions, security-rules, coding-standards | code-review, verification, ai-safety-check | review comments |
| docs-author | v1.2.0 | 技术文档生成、API 文档、设计文档 | workflow-html, security-rules, collaboration | html-document-center | HTML docs, API docs |
| verifier | v1.0.0 | 前端/后端实现完成后，校验设计文档 API 集成矩阵 ↔ 代码一致性 | workflow-core, hotl-contracts, collaboration | verification | 集成验证报告 |

---

## Agent 调用链

### 调用关系图

```
architect
  ├── → backend-developer (后端任务委派)
  ├── → frontend-developer (前端任务委派)
  ├── → ui-designer (UI 设计任务委派)
  ├── → database-expert (DB 设计任务委派)
  ├── → test-engineer (测试任务委派)
  ├── → security-auditor (安全任务委派)
  └── → docs-author (文档任务委派)

verifier
  └── → (独立触发：前端/后端实现完成后自动校验，只检查不修复)

code-reviewer
  └── → (与 architect 协作，无委派关系)

security-auditor
  └── → (独立审计，发现问题通知 architect)
```

### 调用规则

| 场景 | 调用 Agent | 说明 |
|------|-----------|------|
| 新功能开发（首次） | architect → 各专项 Agent | architect 先编排，再分派 |
| 新功能开发（迭代） | 直接调用对应专项 Agent | 已知上下文，无需重新编排 |
| Bug 修复（已知原因） | 直接调用 backend-developer 或 frontend-developer | 单点修复 |
| Bug 修复（原因不明） | architect（先诊断）→ 专项 Agent（修复） | 先排查根因 |
| 架构评审 | architect + security-auditor + database-expert | 三方联合评审 |
| 安全审计 | security-auditor（独立执行） | 安全审计独立于开发流程 |
| 代码审查 | code-reviewer + test-engineer | 代码质量 + 测试质量联合审查 |
| 部署相关 | architect → backend-developer (执行) | 架构师确认，开发者执行 |
| 集成验证 | verifier（前端/后端实现完成后自动触发） | 校验设计文档 API 集成矩阵与代码一致性，仅报告不修复 |

### 冲突仲裁优先级

当多个 Agent 的意见发生冲突时，按以下优先级裁决：

1. **安全** → security-auditor 有最终决定权
2. **数据完整性** → database-expert 有最终决定权
3. **架构正确性** → architect 有最终决定权
4. **代码质量** → code-reviewer 有最终决定权
5. **测试覆盖** → test-engineer 有最终决定权

> **仲裁规则**：优先级高的 Agent 否决优先级低的 Agent，但必须书面说明理由。

---

## 待创建规则文件（按需）

> **反膨胀原则**：仅在通用规则无法覆盖项目特定栈差异时才创建下列文件；优先通过 `rules/applies_to.md` 的 `tech_stacks` 过滤复用通用规则，避免无依据拆文件（参见 AGENTS.md 使用纪律）。

以下规则文件暂未创建，按需创建后更新本索引：

| 规则文件 | 用途 | 建议优先级 |
|---------|------|-----------|
| `rules/architecture-python.md` | Python 后端架构规范 | 高（应用 C/应用 D） |
| `rules/security-python.md` | Python 安全编码规范 | 中 |
| `rules/security-android.md` | Android 安全规范 | 中（应用 B/应用 D） |
| `rules/testing-python.md` | Python 测试规范 | 中 |
| `rules/testing-android.md` | Android 测试规范 | 中 |

> **已创建（2026-08-11）**：`rules/agent-constraints.md`（Agent 行为约束规范，RULE-026~029，见 AGENTS.md 入口路由）已从待创建列表移除并登记到 `rules/applies_to.md`。

### AI Coding Agent 角色登记

> 以下角色为 AI Coding Agent 融合规范定义的功能角色（原 AGENTS.md §4.3 章节已在 v4.0.0 个人开发者精简时移除，**本表为唯一定源**），无独立代理文件，行为约束引用 `agent-constraints.md` 与 `agent-context.md` 规则：

| 角色 | 职责 | 使用规则 | 工具 |
|------|------|---------|------|
| `orchestrator` | 任务分解、状态协调 | agent-constraints, agent-context, collaboration | 全部 |
| `context-agent` | 上下文构建、知识图谱 | agent-context, agent-constraints | 文件系统、MCP |
| `planner-agent` | 执行规划、依赖分析 | agent-context, agent-constraints | LLM、规划引擎 |
| `code-agent` | 代码生成、修改 | agent-constraints, coding-standards | 文件系统、终端 |
| `test-agent` | 测试生成、执行 | agent-constraints, testing-rules | 终端、覆盖率工具 |
| `reviewer-agent` | 代码审查、质量检查 | agent-constraints, anti-patterns | 文件系统、Linter |
| `security-agent` | 安全审计、漏洞扫描 | agent-constraints, security-rules | 终端、安全工具 |

---

## 新增 Agent 时

1. 在本文件添加对应行
2. 在 `rules/applies_to.md` 中更新相关规则的 `applies_to.agents`
3. 在 AGENTS.md 入口路由表中添加对应场景
4. 在 templates/AGENTS_TEMPLATE.md 中添加 Agent 模板
