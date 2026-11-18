---
name: design
version: v1.1.0
type: command
enabled: true
mode: [standard, creator]
updated: 2026-11-07
description: 斜杠命令：design - "系统设计"、"架构设计"、"数据库设计"、"技术方案"；L2/L3 追加 spec 规格化（--type=spec）
---
# /design - 系统设计

**触发词**: "系统设计"、"架构设计"、"数据库设计"、"技术方案"、"写规格"、"spec"

---

## 命令语法

```
/design [module] [--type=architecture|database|api|ui|spec|all]
```

## 参数说明

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `module` | string | 否 | 当前模块 | 设计目标模块，如 `user-service`、`payment-module` |
| `--type` | enum | 否 | `all` | `architecture`/`database`/`api`/`ui`/`spec`（规格化）/`all`（四文档 + spec） |

## 触发场景

- 需求文档（brainstorming 输出）已批准，需要进入设计阶段
- 需要产出架构设计、数据库 Schema、API 契约、UI 线框图
- 新模块需要技术方案设计
- **L2/L3 任务**：需要把需求规格化为可施工、可验收的 `spec.md`
- 架构调整需要重新评估技术选型

## 前置条件

1. 已完成 `brainstorming` 阶段并输出批准的设计文档
2. 项目 `tech-stack.md` 已定义
3. 当前分支干净，无阻塞性未提交变更
4. **判定门禁级别**（`rules/collaboration.md`）：L0/L1 不落盘规格；**L2/L3 才执行本命令的 spec 步骤**

## 执行流程

1. **架构设计** (`system-design`) — 技术选型、模块划分、目录结构、部署方案
2. **数据库设计** (`system-design`) — ER 图、表结构、索引策略、迁移规划
3. **API 设计** (`api-design`) — 接口清单、请求/响应定义、错误码、限流策略
4. **UI 设计** (`ui-design`) — 页面路由、线框图、组件清单、状态处理
5. **按需扩展** — 根据需求特征触发 P0/P1/P2 扩展设计文档
6. **交叉校验** — 确保四份文档互相一致
7. **规格化（L2/L3）** — 按 `templates/spec/spec-template.md` 产出 `docs/tasks/<id>/spec.md`

## 产出物

| 文档 | 负责技能 | 负责代理 |
|------|----------|----------|
| `docs/architecture.md` | `system-design` | `architect` |
| `docs/database-schema.md` | `system-design` | `architect` + `database-expert` |
| `docs/api-design.md` | `api-design` | `backend-developer` |
| `docs/ui-wireframe.md` | `ui-design` | `frontend-developer` |
| **`docs/tasks/<id>/spec.md`**（L2/L3） | **`brainstorming`（步骤 5.5）** | **`architect`** |

## 错误处理

| 常见错误 | 处理方式 |
|----------|----------|
| 设计文档未经批准 | 返回 `brainstorming` 阶段，等待用户审批 |
| spec 有遗留 `[NEEDS CLARIFICATION]` | **先问清再继续**——有遗留不得进 plan / coding（RULE-055 §1.3） |
| spec 里写了技术栈/文件路径/代码 | HOW 泄漏，移到 plan.md（RULE-055 §1.2） |
| 技术选型与 tech-stack.md 冲突 | 提示更新 tech-stack.md 或调整选型 |
| 交叉校验不一致 | 定位不一致点，回到上游设计文档修正 |

## 示例

```
/design user-service --type=all
```

**预期输出**：
- 架构文档：user-service 的四层分层架构（Router → Service → Repository → Model）
- 数据库文档：users 表、sessions 表、索引策略
- API 文档：`POST /api/v1/auth/register`、`POST /api/v1/auth/login` 等接口
- UI 文档：登录页、注册页、个人设置页的线框图和组件清单
- **规格**：`docs/tasks/001-user-auth/spec.md`（FR-001…、P1 用户故事 + Given/When/Then 验收）

---

**执行流程**: 遵循 [system-design](skills/system-design/SKILL.md`)、[api-design](skills/api-design/SKILL.md`)、[ui-design](skills/ui-design/SKILL.md`) 的完整流程
**负责代理**: `architect`（架构 + 规格）+ `backend-developer`（API）+ `frontend-developer`（UI）
**规则**: `rules/workflow-core.md`（7 步闭环）、`rules/workflow-design.md`（设计阶段 + 规格阶段）、`rules/spec-driven.md`（RULE-055）