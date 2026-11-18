---
name: writing-plans
version: v1.4.0
type: skill
enabled: true
mode: [standard, creator]
description: "已有批准的 spec 与设计文档、需要多步骤实现时使用。在 docs/tasks/<id>/plan.md 输出可执行实施计划，并把 spec 的每条 FR 映射为任务；tasks.md 按用户故事分阶段并设 Checkpoint。触发词: 写计划、实施计划、任务拆分。"
updated: 2026-11-07
depends_on: [system-design, api-design]
composes: [executing-plans]
---
# Writing Plans

> **v1.4.0 变更（ADR-008）**：`/plan` 现在有明确的上游输入——`docs/tasks/<id>/spec.md`。
> 计划中的每个任务必须能追到 spec 的某条 FR 或验收场景；FR 覆盖不全、或把 HOW 写回 spec，
> 都判为计划缺陷（由 `hooks/scripts/spec-clarity-gate.mjs` 检出）。

## 负责代理

`architect` — 实施计划编写由架构师负责，确保任务拆解合理、依赖关系清晰。

## 何时使用

- 用户已批准 spec 与设计文档，需要创建实施计划时
- 功能开发涉及多个步骤 (3 步以上)，需要拆分和排序时
- 用户明确要求"出一个 Plan"、"做个实施方案"、"怎么实现"时
- 从 `brainstorming` 技能获得批准后，进入实施准备阶段

**触发关键词**: "出个 plan"、"做个方案"、"怎么实现"、"实施计划"、"task breakdown"

## 执行流程

### 1. 收集上下文

- **读取 spec**（`docs/tasks/<id>/spec.md`）——WHAT/WHY 与编号需求的唯一真源
- 确认已批准的设计文档或 brainstorming 结论
- 读取相关源代码，了解现有实现
- 读取 `rules/workflow-core.md`（工作流与代理分配）
- 读取 `rules/collaboration.md`（爆炸半径 + 上下文投喂约束）
- 读取 `tech-stack.md`（项目技术栈约束）

### 1.5 spec → plan 推导（取代原「设计文档 → 实现清单」）

> 上游是 spec 的功能列表与验收场景，不再是设计文档的散文段落。

#### 清单 1：FR → 任务覆盖表

spec 里**每一条 FR 都必须至少有一个任务**，没有对应任务的 FR 即 FAIL。

```markdown
| FR | 需求摘要 | 任务号 | 验收（引自 spec 场景） | 优先级 |
|----|---------|--------|----------------------|--------|
| FR-001 | 系统 MUST … | T010 | Given/When/Then … | P1 |
```

#### 清单 2：US → 阶段映射

按 P1 → P2 → P3 排序分批；**P1 批结束设 Checkpoint**，停下人工验收再开 P2
（P1 单独即可演示 MVP）。这正是 spec-kit「independently testable user story」的落地。

```markdown
| US | 优先级 | 阶段 | 任务号区间 | 是否可独立交付 |
|----|--------|------|-----------|---------------|
| US-01 | P1 | 阶段1 | T010–T019 | ✅ |
```

#### 硬性规则

- FR 覆盖表与 US 阶段映射必须在用户确认后才能进入 `executing-plans`
- 禁止出现 spec 里有、任务表里没有的 FR（覆盖不全会让 spec 变成装饰）
- 任务的"验收"列**直接引用 spec 的验收场景**，不另造措辞

### 2. 输出实施计划（落盘到 docs/tasks/<id>/）

> **重要**：与 spec 同目录落盘为 `docs/tasks/<id>/plan.md`（模板 `templates/spec/plan-template.md`），
> 禁止与 spec 分家——门禁按目录成对查找。`executing-plans` 通过读取该文件执行任务，实现跨会话续接。
>
> **门禁覆盖范围（明确边界）**：`spec-clarity-gate.mjs` 判 spec 与 tasks 的 FR 覆盖，
> **不判 plan.md 的结构完整性**。plan 的九必填段靠本节的 ✅ 清单 + code-review 维度 0 人工兜底，
> 别以为 `--check` 已经替你查过。

**plan.md 必填段**：Summary / Technical Context / **Constitution Check** / Key Decisions /
System Modules / Data Model / Testing Strategy / Complexity Tracking / Risks。

> **Constitution Check**（spec-kit 的门禁机制）：Phase 0 前必须过、Phase 1 后复查，
> 三道门 = 简洁门 / 反抽象门 / 契约优先门。违规模必须在 Complexity Tracking 书面论证
> 「为什么需要 + 被否定的更简单方案」。详见 `rules/spec-kit.md` RULE-056。

**tasks.md 必填段**：阶段 0 准备 → 按 US 分阶段（每阶段含 Checkpoint）→ 收尾收敛检查。

#### 计划模板选择

根据上下文选择合适的计划模板：

**模板 A：代码实现计划**（默认，用于主开发流）

计划必须包含以下结构（直接输出到对话）：

```markdown
# 实施计划: [功能名称]

## Context (上下文)
- 背景: 为什么需要这个功能
- 已批准的设计摘要
- 技术栈约束

## Tasks (任务列表)

### Task 1: [任务名称]
- **文件**: 涉及的文件路径 (精确到文件名)
- **验收标准**: 明确的、可验证的完成条件
- **复杂度**: Low / Medium / High
- **依赖**: 无 / 依赖 Task N
- **估算**: < 2 小时

### Task 2: [任务名称]
...

## Testing Strategy (测试策略)
- 单元测试覆盖哪些模块
- 集成测试覆盖哪些场景
- 手动验证哪些功能

## Risks (风险)
- 潜在的技术风险和应对方案
```

**模板 B：HTML 文档生成计划**（用于 HTML 文档流）

当上下文涉及 `html-document-center` 技能时，自动切换为文档生成模板：

```markdown
# 文档生成计划: [文档中心名称]

## Context (上下文)
- 背景: 为什么需要生成文档中心
- 文档类型清单与内容来源
- 视觉风格与架构模式选择

## Documents (文档列表)

### Doc 1: [文档名称，如 PRD]
- **类型**: PRD / 技术报告 / API 文档 / 设计规范 / 白皮书
- **来源**: 已有 Markdown / 从零编写 / 基于代码生成
- **输出路径**: docs/<category>/index.html + docs/<category>/assets/
- **验收标准**: 可独立打开，暗色主题，图表正常渲染，链接可点击
- **依赖**: 无
- **复杂度**: Low / Medium / High

### Doc 2: [文档名称]
...

### Doc N+1: 文档中心入口
- **输出路径**: docs/doc-center.html
- **验收标准**: 左侧导航树可折叠，iframe 预览正常，搜索可用
- **依赖**: Doc 1, Doc 2, ...（所有文档完成后）
- **复杂度**: Low

## Cross-Workflow Checks (交叉工作流检查)
- 交叉点 A: 是否有已审批设计文档可复用？（来源：`docs/designs/*.md`）
- 交叉点 B: 是否有已实现代码可用于 API 文档生成？（来源：实际代码）
- 交叉点 D: API 文档中的示例代码需与实际接口一致（验证阶段反向检查）

## Validation Strategy (验证策略)
- 链接完整性：所有文档链接可点击跳转
- iframe 隔离：各文档样式独立，不互相干扰
- 搜索功能：全局搜索可过滤文档标题和描述
- 响应式：移动端自动折叠侧边栏
- API 一致性（交叉点 D）：文档示例与实际接口对比验证
```

### 3. 用户审核

- 将完整计划写入 `docs/tasks/<id>/plan.md`（+ `tasks.md`），并在对话中输出摘要
- 等待用户确认或调整
- 用户批准后，调用 `executing-plans` 技能按 plan 逐步执行（读取落盘文件）

## 硬性规则

- ✅ **spec 的每条 FR 都必须有对应任务**（FR 覆盖表由 §1.5 清单 1 承载）
- ✅ 每个任务工作量 **< 2 小时**，超过则必须继续拆分
- ✅ 每个任务必须有**明确的验收标准**（直接引用 spec 验收场景）
- ✅ 每个任务必须**标注依赖关系**
- ✅ 任务必须指定**涉及的文件路径**
- ✅ 计划必须包含**测试策略**（Testing Strategy 段，动作映射到 US / 验收场景）
- ❌ 禁止创建含糊的任务 (如 "优化性能" — 必须具体化)
- ❌ 禁止跳过上下文收集直接写计划
- ❌ 禁止用户未批准就进入执行
- ❌ 禁止把 spec 的 FR 留在任务表外（那等于 spec 白写）

## 反模式

- ❌ 任务粒度过大 ("实现整个用户模块" — 需要 2 天)
- ❌ 没有验收标准 ("写好代码" — 什么叫"好"?)
- ❌ 没有依赖关系 — 导致执行顺序混乱
- ❌ 忽略测试策略 — 导致功能无法验证
- ❌ 一次性列出 20+ 个任务 — 信息过载，建议分阶段规划
- ❌ 把技术选型写进 spec（HOW 属 plan，RULE-055 §1.2）
- ❌ 一个任务覆盖多条 FR（验收模糊，无法独立判定完成）
