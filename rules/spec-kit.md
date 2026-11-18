---
name: spec-kit
version: v1.0.1
type: rule
enabled: true
mode: [standard, creator]
description: Spec-Kit / Kiro 工具镜像 — 八步流程与三文件模型映射到本库既有技能、constitution 九条与斜杠命令口径（RULE-056，ADR-008；配套 RULE-055，不另行声明其落点）
updated: 2026-11-11
applies_to:
  agents: ['architect', '全部 Agent']
  phases: ['design', 'implementation', 'review']
  project_types: ['全部']
  tech_stacks: ['全部']
---
# Spec-Kit / Kiro 工具镜像 — RULE-056

> **配套于** RULE-055（`rules/spec-driven.md`）的工具镜像。**本文件是流程映射说明，不是独立铁律，也不声明 RULE-055 的编号落点**——
> 判定口径一律以 `rules/spec-driven.md`（RULE-055）与 `hooks/scripts/spec-clarity-gate.mjs` 为准；
> `applies_to.md` 因此把本条标为"建议"级。**本库不引入 `specify-cli` / Kiro 本体**
> （理由见 ADR-008 §方案B 与 RULE-055 §7）；本文件只把外部参考实现的步骤、命令、产物，
> 一一映射到本库已有的技能与命令上，使"按 SDD 做"有确定的操作路径。

## 1. Spec Kit 八步 → 本库命令

| Spec Kit | 产物 | 本库落点 | 命令 / 技能 |
|----------|------|----------|-------------|
| `/speckit.constitution` | `.specify/memory/constitution.md` | `tech-stack.md` 的"项目原则"段 + ADR | `/design`（initiative scope 时） |
| `/speckit.specify` | `spec.md` | `docs/tasks/<id>/spec.md` | `/design --type=spec` |
| `/speckit.clarify` | 更新 spec.md | 同文件 `Clarifications` 段 | `/design` 内的澄清循环 |
| `/speckit.plan` | `plan.md` + `research.md` + `data-model.md` + `contracts/` | `docs/tasks/<id>/plan.md` + `docs/decisions/ADR-*.md` + `schemas/` | `/plan` |
| `/speckit.checklist` | 质量清单 | 复用 `spec-clarity-gate.mjs --check` | 门禁 |
| `/speckit.tasks` | `tasks.md` | `docs/tasks/<id>/tasks.md` | `/plan` 输出 + `writing-plans` |
| `/speckit.analyze` | 一致性报告 | `hooks/scripts/spec-clarity-gate.mjs`（FR 覆盖 + 漂移） | 门禁 |
| `/speckit.implement` | 代码 | 代码 | `/test` / `executing-plans` |
| `/speckit.converge` | `Converged` 判定 | `executing-plans` 的收敛循环（§3） | `/verify` |

**短路径 / 全路径**：

```text
短路径（L2 小特性）:  specify → plan → tasks → implement → converge
全路径（L3）:         constitution → specify → clarify → plan → checklist
                     → tasks → analyze → implement → converge
```

## 2. Constitution（项目宪法）口径

### 2.1 仓内已成立原则优先

宪法条款只能来自**仓里已经成立的事实**：README 的工程约定、既有 ADR、CI 配置、
`tech-stack.md` 的禁止事项。**禁止为填满模板编造标准**——那只会让后续 plan/analyze
阶段充满噪音（spec-kit brownfield 指南的原话忠告）。

本库把宪法承载在**两处**，不新建第三处：

| 层 | 载体 | 管什么 |
|----|------|--------|
| 项目级 | 各仓 `tech-stack.md`（§编码规范/安全规范/禁止事项） | 该仓的硬约束 |
| 规则级 | 本库 `AGENTS.md` §3 硬性规则速查 + 各 `rules/*.md` | 跨仓通用铁律 |

### 2.2 参考九条（spec-driven.md 的参考结构，供填写时对照）

1. 库优先：功能先以独立库形态存在
2. CLI 接口强制：功能可经文本 in/out 触达（可观测、可测试）
3. **测试先行（NON-NEGOTIABLE）**：先写测试 → 批准 → 确认 Red → 才写实现 ← 本库 RULE-003 已覆盖
4–6. 项目自定义（集成测试、可观测性、版本化）
7. 简洁门：初始实现最多 3 个项目，直接用框架不包装
8. 反抽象门：仅当存在两个以上真实调用方时才抽层
9. 集成优先：真实依赖优于 mock

> 本库已有等价物：第 3 条 = RULE-003/TDD；第 7、8 条 = RULE-015 YAGNI + `engineering-principles.md`；
> 第 9 条 = `testing-rules.md` 契约测试。**填宪法时优先引用这些，不另起措辞。**

## 3. Kiro 三文件模型 → 本库结构

| Kiro | 本库等价 | 说明 |
|------|----------|------|
| `.kiro/specs/<feature>/requirements.md` | `docs/tasks/<id>/spec.md` | EARS + 用户故事 + 验收标准 |
| `.kiro/specs/<feature>/design.md` | `docs/tasks/<id>/design.md`（L3 才有） | 架构图、数据模型、测试策略 |
| `.kiro/specs/<feature>/tasks.md` | `docs/tasks/<id>/tasks.md` | 离散任务 + 依赖 + 可选/必需 |

**EARS 记法**（本库验收场景的第二种合法格式）：

```text
WHEN <事件/条件> THE SYSTEM SHALL <期望行为>
```

- 优点：无歧义、可直接翻译成测试用例、可追溯、非技术人也读得懂。
- 本库验收格式二选一：**Given/When/Then**（偏行为描述）或 **EARS**（偏规则列表）。
- **需求先行**：Kiro 的核心建议是"先把 what 弄对再定 how"——本库对应
  `brainstorming` 完成后再进 `/design --type=spec`，spec 批准后才 `/plan`。

## 4. Converge（收敛）循环

spec-kit 不假设一次写对；官方口径是 **implement → converge 反复，直到报告 `Converged`**。
本库把这一步落到 `skills/executing-plans` §6 收敛循环——**收敛判据（三条）与循环写法以该技能为真源，
此处不重复维护**（两处各写一份必然漂移）。RULE-056 只声明一件事：`/verify` 的口径 = `/speckit.converge` 的口径。

> 反模式：把"验证实现"这类 task 标成 done 却没写任何单测（spec-kit 社区已记录的假安全感）。
> 本库以 `rules/testing-rules.md` 禁止事项兜底。

## 5. 明确不做

- ❌ 安装 `specify-cli`、`kiro-cli` 或任何 SDD 工具本体（见 RULE-055 §7 与 ADR-008）。
- ❌ 在仓内建 `.specify/` / `.kiro/` 目录——落点统一为 `docs/tasks/<id>/`（RULE-053）。
- ❌ 为每个小改动新建 constitution——宪法一仓一份，按 §2.1 从既有事实提炼。

## 6. Enforcement

| 项 | 工具 |
|----|------|
| spec 结构 / 澄清 / 体量 / 漂移 | `hooks/scripts/spec-clarity-gate.mjs` |
| 收敛判据 3 | 同上 `--check` |
| 落点合规（`docs/tasks/<id>/`） | `tools/root-cleanliness-check.mjs`（RULE-053 L3 落点表） |

参考来源：<https://github.com/github/spec-kit>、<https://kiro.dev/docs/specs/feature-specs/requirements-first/>、
<https://azure.github.io/Azure-Verified-Modules/usage/ai-assisted-sol-dev/spec-kit/>
（完整调研与实测数据见 `docs/research/2026-11-07-spec-driven-development.md`）
