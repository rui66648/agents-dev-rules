---
name: workflow-design
version: v1.3.0
type: rule
enabled: true
mode: [standard, creator]
updated: 2026-11-09
description: 工作流设计 — 生成前查重（RULE-053 §3.5）+ 设计文档结构、HOTL 三合约展开、7 章标准设计文档模板 + spec 规格化阶段（RULE-055）
applies_to:
  agents: ['architect', 'frontend-developer', 'ui-designer']
  phases: ['design']
  project_types: ['web', 'mobile', 'backend']
  tech_stacks: ['全部']
---
# 设计阶段详细说明 (Design Phase)

> 设计阶段输入：brainstorming 输出的需求文档。设计阶段输出：核心四文档 + 按需扩展文档。

## 步骤 0：检索已有同主题文档（强制，RULE-053 §3.5）

四份设计文档**不是每次都从零生成**。动手前先检索 `docs/designs/`、`docs/tasks/<id>/`、`docs/decisions/` 与 `docs/README.md` 索引：

| 检索结果 | 动作 |
|---|---|
| 已有同主题且仍有效 | **就地修改该文件**，升版本 / 追加 `docs/CHANGELOG.md`；不得另存 `-v2`、`-final`、带日期的第二份 |
| 内容属另一真源的派生展示 | 只写链接 + 一句说明，不复制正文 |
| 检索为空，或已有件已冻结 / 归档 / 标注历史依据 | 才允许新建，并在同批登记进 `docs/README.md` |

> 判定与合法例外以 `rules/directory-structure.md` §3.5 为准（唯一真源）；本表只是设计阶段的落地入口，不另立口径。

## 核心四文档流程

```
需求文档
   │
   ├──→ [system-design] ──→ architecture.md（架构设计）
   │           │
   │           └──→ database-schema.md（数据库设计）
   │
   ├──→ [api-design] ─────→ api-design.md（接口设计）
   │           ↑
   │           └──── 依赖架构设计的技术选型 ─────┘
   │
   └──→ [ui-design] ──────→ ui-wireframe.md（UI设计）
               ↑
               └──── 依赖架构设计 + 接口设计 ─────┘
```

## 规格阶段（v1.2.0 新增，ADR-008 / RULE-055）

> 四份文档描述**系统形态与选型**；规格（spec）描述**这个特性要做什么、怎么算做对**。
> 二者分工不同，不互相替代：实现时以 spec 的编号需求为施工依据，四文档回答"放在哪、用什么"。

```
四份设计文档 ──→ [spec 规格化] ──→ docs/tasks/<id>/spec.md
                                      │
                                      ├─→ 用户审批（与设计文档同批，RULE-002）
                                      │
                                      └─→ [writing-plans] ──→ docs/tasks/<id>/plan.md
                                                                  └─→ tasks.md
```

**规格的六个必填段**——可读真源是 `templates/spec/spec-template.md`，可执行真源是
`hooks/scripts/spec-clarity-gate.mjs` 的 `REQUIRED_SECTIONS` 常量。**改段名必须同批改该常量**，
否则门禁认不出新段名 = 假绿。本文件不重复罗列段名（只此一处可读 + 只此一处可执行）。

**规格纪律**（详见 `rules/spec-driven.md`）：只写 WHAT/WHY 不写 HOW；关键分歧标
`[NEEDS CLARIFICATION]`（每份 ≤3 个，有遗留不得进 plan）；单份 ≤200 行；改了代码必须同批改 spec。

**分级**：L0/L1 不落盘规格；L2 落盘 spec；L3 另加 `design.md`（含 Constitution Check 违规模块）。

## 扩展八文档决策矩阵

| 扩展设计文档 | 负责技能 | 何时触发 | 触发条件 |
|-------------|----------|----------|----------|
| `security-design.md` | `security-design` | **[P0]** | 有认证/授权/加密需求 |
| `performance-design.md` | `performance-tuning` | **[P0]** | 有性能/缓存需求 |
| `data-flow-design.md` | `data-flow-design` | **[P1]** | 有复杂业务逻辑 |
| `test-design.md` | `test-strategy` | **[P1]** | 需测试分层策略 |
| `deployment-design.md` | `deploy` | **[P1]** | 需自动化部署 |
| `integration-design.md` | `integration-design` | **[P2]** | 需第三方集成 |
| `i18n-design.md` | `i18n-design` | **[P2]** | 需国际化 |
| `analytics-design.md` | `analytics-design` | **[P2]** | 需埋点/看板 |

> **触发规则**：P0 级别默认建议触发，AI 主动询问用户是否跳过。P1/P2 仅在用户要求时触发。

## 12 份设计文档矩阵

| 设计文档 | 核心内容 | 校验关系 | 负责技能 | 级别 |
|----------|----------|----------|----------|------|
| `architecture.md` | 技术选型、目录结构、模块划分 | 架构模块 → 数据库实体 | `system-design` | 核心 |
| `database-schema.md` | ER图、表结构、索引、迁移策略 | 数据库实体 → API 资源 | `system-design` | 核心 |
| `api-design.md` | 接口清单、请求/响应定义、错误码 | API 接口 → UI 数据来源 | `api-design` | 核心 |
| `ui-wireframe.md` | 页面路由、线框图、组件清单、状态 | UI 页面 → 对应 API | `ui-design` | 核心 |
| `security-design.md` | 认证方案、权限模型、数据加密 | 安全策略 → API 鉴权 | `security-design` | P0 |
| `performance-design.md` | 性能基线、缓存分层、查询优化 | 性能指标 → 架构容量 | `performance-tuning` | P0 |
| `data-flow-design.md` | 业务流程图、状态机、时序图 | 数据流 → API → DB 事务 | `data-flow-design` | P1 |
| `test-design.md` | 测试分层、自动化策略、用例清单 | 测试用例 → 功能需求 | `test-strategy` | P1 |
| `deployment-design.md` | 环境划分、CI/CD 流水线 | 部署方案 → 架构设计 | `deploy` | P1 |
| `integration-design.md` | 第三方服务清单、接口契约 | 集成接口 → API 设计 | `integration-design` | P2 |
| `i18n-design.md` | 语言规划、翻译方案、时区格式 | 国际化 → UI 设计 | `i18n-design` | P2 |
| `analytics-design.md` | 指标定义、事件设计、埋点方案 | 埋点 → UI 页面 → API | `analytics-design` | P2 |

## 交叉校验规则、API集成矩阵

> 设计文档必须互相一致。任何不一致需回到上游修正：

| 不一致 | 回退目标 |
|--------|----------|
| 架构模块数 ≠ 数据库实体数 | `system-design` |
| 数据库表数 ≠ API 接口资源数 | `system-design` / `api-design` |
| API 接口数 ≠ UI 页面数据需求 | `api-design` / `ui-design` |
| UI 页面数 ≠ 功能需求数 | `brainstorming` |
| 安全策略 ≠ API 接口鉴权 | `security-design` / `api-design` |
| 性能指标 ≠ 架构设计容量 | `performance-tuning` / `system-design` |

## 设计文档审批

- 设计文档完成后，AI 询问用户"设计文档已完成，请审阅。输入'批准'或'同意'继续，或提出修改意见。"
- 用户明确批准后，AI 自动调用 `writing-plans` 技能
- 用户拒绝时，AI 记录拒绝原因，返回 `brainstorming` 阶段迭代
- **L2/L3 追加**：`docs/tasks/<id>/spec.md` 与设计文档**同批审批**（RULE-002 门禁一次覆盖两份产物，非新增审批）。审批口径唯一真源见 `rules/collaboration.md` §分级设计门禁。

## Schema-As-Code 强制（RULE-030~033）

> **核心原则**：设计文档必须产出机器可读的 Schema 文件，而非仅放在 Markdown 中。AI 生成代码前必须通过 Schema 校验。
>
> **编号说明**：RULE-026/027/029 已于 v4.11.0（ADR-006）废弃归档（见 `agent-constraints.md`），RULE-030~033 为 Schema-As-Code 规则（规则定义见 `schema-as-code.md`）。

### 12 份设计文档 → 12 个 Schema 文件

| 设计文档 | 对应 Schema 文件 | 格式 | 校验工具 |
|----------|----------------|------|---------|
| `architecture.md` | `schemas/architecture.yaml` | YAML | `schema-validator.py` |
| `database-schema.md` | `schemas/db-schema.sql` | SQL DDL | `alembic check` |
| `api-design.md` | `schemas/api.jsonschema` | JSON Schema | `jsonschema` + `schema-validator.py` |
| `ui-wireframe.md` | `schemas/design-tokens.yaml` | YAML | `design-token-linter.js` |
| `security-design.md` | `schemas/security-policy.yaml` | YAML | `schema-validator.py` |
| `performance-design.md` | `schemas/performance-budget.yaml` | YAML | `schema-validator.py` |
| `data-flow-design.md` | `schemas/data-flow.yaml` | YAML | `schema-validator.py` |
| `test-design.md` | `schemas/test-coverage.yaml` | YAML | `schema-validator.py` |
| `deployment-design.md` | `schemas/deployment.yaml` | YAML | `schema-validator.py` |
| `integration-design.md` | `schemas/integration.yaml` | YAML | `schema-validator.py` |
| `i18n-design.md` | `schemas/i18n-config.yaml` | YAML | `schema-validator.py` |
| `analytics-design.md` | `schemas/analytics-config.yaml` | YAML | `schema-validator.py` |

### 契约一致性检查（RULE-030）

设计文档产出的机器可读 Schema 必须通过以下一致性检查：

```python
# hooks/contract-diff.py 自动检测
# 注意：模块/实体/页面数天然不必严格相等，采用覆盖度与容差校验，
# 避免强等式带来的误报阻断。
CONTRACT_RULES = [
    {"name": "module-entity-alignment", "check": "架构模块数与数据库实体数大致对齐（偏差 ≤ 30%）"},
    {"name": "entity-resource-coverage", "check": "核心数据表均有对应 API 资源（覆盖率 ≥ 80%）"},
    {"name": "resource-page-consistency", "check": "API 接口数 >= UI 页面需求数"},
    {"name": "page-requirement-coverage", "check": "UI 页面覆盖全部功能需求（允许多需求合并一页实现）"},
]
```

### AI 生成约束（RULE-032）

AI 在生成代码前必须：

1. 读取 `tech-stack.md`（技术栈约束）
2. 读取对应 Schema 文件（契约约束）
3. 确认生成目标在契约边界内
4. 生成代码 → Schema 校验 → 违规则拒绝重生成

### 与现有规则的补充关系

| 现有规则 | Schema-As-Code 增强 |
|---------|-------------------|
| `open-source-first.md` | 新增 ADR Schema 文件要求（含 License、成熟度、取舍分析） |
| `security-rules.md` | 安全策略必须可执行校验（不是文档描述） |
| `ui-design-patterns.md` | UI 选型结论写入 Schema 并可校验（设计令牌语义约束已随 RULE-031 废弃） |
| `testing-rules.md` | 测试覆盖率必须写入 Schema 并自动检测 |
