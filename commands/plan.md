---
name: plan
version: v1.1.0
type: command
enabled: true
mode: [standard, creator]
updated: 2026-11-07
description: 斜杠命令：plan - "规划一下"、"做个计划"、"任务拆解"、"设计方案"；输入是已批准的 spec，输出 docs/tasks/<id>/{plan,tasks}.md
---
# /plan - 规划流程

**触发词**: "规划一下"、"做个计划"、"任务拆解"、"设计方案"

---

## 命令语法

```
/plan [scope] [--priority=high|medium|low] [--deadline=YYYY-MM-DD]
```

## 参数说明

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `scope` | string | 否 | 当前模块 | 规划范围，如 `user-module`、`api-redesign` |
| `--priority` | enum | 否 | `medium` | 任务优先级：`high`（核心功能）、`medium`（常规需求）、`low`（优化/重构） |
| `--deadline` | date | 否 | 无 | 目标完成日期，格式 `YYYY-MM-DD` |

## 触发场景

- **已批准的 spec**（`docs/tasks/<id>/spec.md`）在手，需要转成可执行计划
- 新功能开发前，需要将需求拆解为可执行的任务清单
- 迭代开始前的 Sprint 规划
- 技术方案确定后，需要将设计文档转化为实施计划
- 复杂 Bug 修复前，需要梳理修复步骤与依赖关系
- 重构工作开始前，需要规划迁移路径与回滚策略

## 前置条件

1. **spec 已批准**（L2/L3）：`docs/tasks/<id>/spec.md` 存在且用户已批准，
   且**无遗留 `[NEEDS CLARIFICATION]`**（有遗留先问，RULE-055 §1.3）
2. 项目 `tech-stack.md` 已定义，技术选型已确定
3. 当前工作目录为项目根目录或对应模块目录
4. Git 工作区已提交或暂存，无未保存的重要变更

> L0/L1（无落盘 spec）不受前置条件 1 约束，按轻量规格在对话中规划。

## 执行流程

1. **读取上游** — 读 `docs/tasks/<id>/spec.md` + `tech-stack.md` + 相关设计文档
2. **FR → 任务覆盖** — spec 里每条 FR 必须至少有一个任务，生成覆盖表（缺一条即计划缺陷）
3. **US → 阶段映射** — 按 P1→P2→P3 分批；P1 批结束设 Checkpoint 停机验收
4. **任务拆解** — 拆为原子级任务（每个 < 2 小时，验收 + 验证动作齐备）
5. **依赖排序** — 分析任务间先后与阻塞关系，构建依赖图
6. **Constitution Check** — 过简洁门 / 反抽象门 / 契约优先门；违规模写进 Complexity Tracking
7. **落盘** — 写 `docs/tasks/<id>/plan.md`（模板 `templates/spec/plan-template.md`）+ `tasks.md`

## 产出物

- **`docs/tasks/<id>/plan.md`**：Summary / Technical Context / Constitution Check / Key Decisions / System Modules / Data Model / Testing Strategy / Complexity Tracking / Risks
- **`docs/tasks/<id>/tasks.md`**：按 US 分阶段的任务清单，每任务含验收（引自 spec 场景）+ 依赖 + 验证动作
- **FR 覆盖表** + **US 阶段映射**（对话中确认）

## 错误处理

| 常见错误 | 处理方式 |
|----------|----------|
| 找不到已批准的 spec | L2/L3 提示先 `/design --type=spec`；L0/L1 可直接轻量规划 |
| spec 有遗留澄清标记 | 先问清并回填 spec，再进本流程 |
| spec 的 FR 没有任务对应 | 计划缺陷——补任务，或说明该 FR 本轮不做（并改 spec） |
| 范围过于模糊 | 要求用户明确 scope 或拆分多个 `/plan` 调用 |
| 任务间存在循环依赖 | 识别循环依赖点，建议调整模块边界或引入中间层 |
| 缺少 `tech-stack.md` | 提示创建技术栈定义文件后再执行规划 |

## 示例

### 示例 1：按已批准 spec 排计划

```
/plan user-auth
```

**预期输出**：
- `docs/tasks/001-user-auth/plan.md`：JWT 方案 + Constitution Check 三门结论
- `docs/tasks/001-user-auth/tasks.md`：阶段0 骨架 → 阶段1（US-01 P1，T010–T019 + Checkpoint）→ 阶段2
- FR 覆盖表：FR-001…FR-005 全部有任务且验收引自 spec 场景

---

**执行流程**: 遵循 [writing-plans 技能](skills/writing-plans/SKILL.md`) 的完整流程
**负责代理**: `architect`
**规则**: `rules/spec-driven.md`（RULE-055）、`rules/spec-kit.md`（RULE-056）
