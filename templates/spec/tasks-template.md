---
spec_id: <slug>
spec_version: v1
status: pending          # pending | in-progress | done
updated: YYYY-MM-DD
---

# Tasks: <特性名>

**Input**: `./spec.md`（WHAT/WHY）+ `./plan.md`（HOW）
**Prerequisites**: spec.md approved；plan.md approved

## 学习目标（RULE-057，L2/L3 必填）

> 与规格同步声明的「本次要弄懂什么」。缺此段 = L2/L3 任务未完成（RULE-057 §8 检查项 1）。

- **本次要弄懂**：<概念 / 机制 / 失败模式>
- **完成后能解释**：<能脱稿讲透的数据流与关键边界>
- **对应知识资产**：`docs/learning/<YYYY-MM-DD>-<slug>.md`（半页模板 `templates/learning/note-template.md`）

## 阶段 0：准备（无故事依赖）

- [ ] T000 建立骨架/分支/依赖；**验证**：构建通过
- [ ] T001 <契约先行：先写接口/Schema，无实现>；**验证**：契约测试 Red

## 阶段 1：US-01（P1，可独立交付）

> 完成本阶段即停机验收：P1 单独构成可演示 MVP。

- [ ] T010 <契约先行：先写接口 / Schema / 失败测试（RED，RULE-003）>；**验收**：测试 Red；**依赖**：T001
- [ ] T011 <最小实现使测试通过>；**验收**：测试 Green
- [ ] T012 <重构（如需）+ 该 FR 的边界用例>；**验收**：FR-00N 全部断言通过
- [ ] **Checkpoint**：US-01 全场景跑通 → 停下人工验收再进 P2

> **顺序纪律（RULE-003）**：每个 FR 都必须 RED → GREEN → REFACTOR——**先写失败测试，再写实现**。
> 模板不许示范"先实现后补测试"；测试用例直接译自 spec 的验收场景（`rules/testing-rules.md`）。
> **Checkpoint 的停机条件**：US-01 的全部任务 `done` **且**其全部验收场景跑通。
> P1 只含 1–2 个任务时，可与阶段 0 合并为一次停机（不制造无意义中断）。

## 阶段 2：US-02（P2）

- [ ] T020 <任务>；**验收**：FR-003；**依赖**：Checkpoint 1
- [ ] T021 <测试>；**验收**：
- [ ] T022 <实现>；**验收**：

## 收尾：收敛

- [ ] T090 跑 spec-clarity-gate --check（FR 覆盖 / 漂移 / 遗留澄清）
- [ ] T091 跑全量测试 + linter + 安全扫描
- [ ] T092 更新 spec_version（若本轮修订了规格）并记 commit `spec:<slug>@v<N>`

---

## 任务模板

```markdown
- [ ] T<NNN> <一句话动作，具体到可验证>
  - **验收**: <可观察条件>
  - **依赖**: 无 / T<NNN>
  - **复杂度**: Low / Medium / High
  - **验证动作**: <测试命令 / 可运行步骤 / 人工验收项>
```

### 硬性规则

- 每个任务必须有**验收**与**验证动作**，二者缺一即不许开始。
- 任务按依赖排序；**P1 阶段结束必须设 Checkpoint**，等人工验收后再开 P2。
- 改动超出计划范围 → 暂停升级（`rules/collaboration.md` 门禁升级规则）。
- 标记 `done` 前必须真的跑过验证动作——**禁止把"验证实现"标成 done 却没写测试**。

### 状态机

`pending → in-progress → done`；全部 `done` 后置文件 `status: done`，并在 `CHANGELOG.md` 记一条该特性的完成说明。
