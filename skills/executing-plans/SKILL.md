---
name: executing-plans
version: v2.1.0
type: skill
enabled: true
mode: [standard, creator]
description: "执行已获用户批准的 spec/plan/tasks（docs/tasks/<id>/）时使用。按依赖顺序推进，跑收敛循环直到 spec 门禁 PASS，支持断点续传。触发词: 执行计划、开始实施、按计划做。"
updated: 2026-11-07
depends_on: [writing-plans]
composes: [test-driven-development, ai-safety-check, deploy]
---

# Executing Plans

> **v2.1.0 说明（ADR-006）**：删除面向"人在聊天框逐步指挥"的内容——编码节奏表、Prompt 模板、DO/DON'T 清单、未经验证的"效率提升"宣称，以及"每 3-5 个任务必须停下等人工确认"。自主 Agent 按依赖与风险推进，仅在真正的风险点升级。
>
> **v2.1.0 追加（ADR-008）**：按 spec-kit 的 converge 口径执行——**迭代到收敛，而非假设一次写对**。

## 负责代理

按任务类型自动分配 — 后端 API 任务分配给 `backend-developer`，前端组件任务分配给 `frontend-developer`，数据库变更分配给 `database-expert`，安全相关任务分配给 `security-auditor`。

## 何时使用

- 用户已批准实施计划，准备开始编码时
- 需要按顺序执行多个开发任务时
- 用户明确要求"开始执行"、"按计划来"时

**触发关键词**: "开始执行"、"按计划来"、"按顺序实现"、"execute the plan"

## 执行流程

### 1. 加载计划

- 读取已批准的 `docs/tasks/<id>/spec.md`、`plan.md`、`tasks.md`
- 确认任务列表、依赖关系和验收标准
- **确认 spec 无遗留 `[NEEDS CLARIFICATION]`**——有遗留先问，不许边写边猜（RULE-055 §1.3）
- 检查当前工作区状态（未提交的变更、分支状态）

### 2. SPEC 拆解（关键步骤）

把 `spec.md`（WHAT/WHY）与 `plan.md`（HOW）组合成可执行结构：

1. **目标定义**：从 `spec.md` 取 `Intent` 的 intent / constraints / 成功标准——**引用，不重抄**（spec 改了就自动生效，抄一份只会漂移）
2. **任务拆分**：按依赖与验证点拆为边界清晰的子任务；**每条任务回指 spec 的 FR 编号或验收场景**
3. **阶段划分**：按 US 优先级分阶段（阶段0 准备 → 阶段1 = P1 → 阶段2 = P2 …），每阶段内含 checkpoint
4. **变更清单**：需修改的文件列表与改动规模（供最小变更与爆炸半径评估）

**落盘（强制）**：写入 `docs/tasks/<id>/tasks.md`，**结构以 `templates/spec/tasks-template.md` 为准**（阶段划分、任务模板、Checkpoint、收敛检查、硬性规则、状态机）。不要在 skill 与模板各写一份骨架——那正是漂移的来源。

**落盘规则**：

1. 目录 `docs/tasks/<id>/`，`<id>` 取 `NNN-<slug>`（如 `001-user-auth`）
2. 状态机 `pending → in-progress → done`；每完成一个子任务，更新该行状态并刷新 `updated`
3. 断点续传：跨会话/中断恢复时先读 tasks 文件，从未完成子任务继续
4. 完成闭环：全部 `done` 后置文件 `status: done`，并在 `CHANGELOG.md` 记一条该特性的完成说明（跨仓统一口径；本规则库不设 `task_metrics.py`，历史引用已清）

### 3. 逐任务执行

对每个任务：

1. **先 RED**：为该任务的 FR 写失败测试，用例译自 spec 的验收场景（RULE-003 + `rules/testing-rules.md`）
2. 按 SPEC 实现，遵循 `tech-stack.md` 与 `rules/collaboration.md` 的"最小变更"
3. 对照 spec 的验收场景自检（**不是**对照自己的理解），跑测试确认 Green、无回归
4. 更新 tasks 状态

> **推进原则**：任务之间若**无依赖**，可在确认无文件冲突后连续推进，不必逐个等待人工确认。Agent 自行完成"RED → 实现 → 自检 → 测试"循环，并以可验证结果为准。
> **嵌套口径（两条不冲突，是范围关系）**：
> - **阶段内**（同一 US）连续推进，只在无依赖且无文件冲突时合并步骤；
> - **跨阶段**（P1 → P2）以 tasks 模板的 Checkpoint 为准，**必须停机**等人工验收。
>
> 停机条件：US-01 全部任务 `done` 且其全部验收场景跑通。**P1 只含 1–2 个任务时，允许与阶段 0 合并为一次停机**——`writing-plans` 的"任务 < 2 小时"是**拆解要求**，不是停机节奏；停机只按 US 边界。

### 4. 进度汇报与升级点

- 阶段性汇报进度即可；**仅在以下情况暂停并请求确认**：
  - 改动超出原计划范围，或需要新增/调整设计决策
  - 触及高风险面（安全/认证/隐私/计费、DB Schema、生产数据）
  - 需要引入新依赖
  - 计划本身存在缺陷或验收标准无法满足
- 其余情况按计划继续，不制造无意义的中断。

### 5. 并行执行（可选）

当多个子任务无依赖关系时可并行：前后端接口、独立工具函数、测试与实现。确保并行任务之间无文件冲突，各自独立验证。

### 6. 收敛循环（Converge，v2.1.0 新增）

不追求"一次写对"，而是迭代到收敛：

```text
执行 tasks → 跑验证 → node <规则库根>/hooks/scripts/spec-clarity-gate.mjs --root <仓根>
   ├─ 未收敛 → 修代码；若发现是规格本身的问题，升 spec_version 改规格 → 再来一轮
   └─ 收敛 → code-review → finishing
```

**收敛判据（三条全满足才算 Converged）**：

1. tasks 全部 `done`
2. spec 的每个验收场景都有对应可执行验证且通过
3. `spec-clarity-gate.mjs` PASS（无遗留澄清、无 spec 漂移、FR 全被 tasks 覆盖）

> 规格本身错了是**正常**发现，不是失败：改规格要升 `spec_version` 并记 commit
> `spec:<slug>@v<N>`（RULE-055 §4）。禁止悄悄改规格不改版本号——那正是漂移的起点。

### 7. 异常处理

- 测试失败：诊断原因，修复后重跑
- 阻塞问题：暂停并说明情况，请求指导
- 发现计划缺陷：暂停并与用户讨论调整
- 需求变更：建议回到 `brainstorming` 重新评估
- 上下文过长：按依赖进一步拆分任务，或将独立子任务委派给 subagent

## 硬性规则

- ✅ 按依赖顺序执行；无依赖时可连续推进
- ✅ 每完成一个任务运行测试，测试失败不得继续下一个
- ✅ 遇到高风险面、计划偏差或新依赖时暂停并确认
- ❌ 禁止添加计划外的功能（YAGNI）
- ❌ 禁止在测试失败时继续下一个任务
- ❌ 禁止静默处理异常而不告知用户

## 反模式

- ❌ 跳过"看起来简单"的任务 — 每个任务都有存在理由
- ❌ 遇到问题不暂停直接绕过 — 隐藏了潜在风险
- ❌ 顺带"顺手"加了计划外的功能 — 偏离计划，增加风险
- ❌ 不运行测试就说"应该没问题" — 假设不是证据
