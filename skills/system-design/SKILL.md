---
name: system-design
version: v1.0.0
type: skill
enabled: true
mode: [standard, creator]
description: "需求明确（brainstorming 批准）后、编写实施计划前使用。进行架构设计（决策点、技术选型、目录结构）和数据库设计（ER图、Schema、索引），输出设计文档供 writing-plans 消费。触发词: 架构设计、技术选型、系统设计、数据库设计。"
updated: 2026-08-13
depends_on: [brainstorming]
composes: [api-design, ui-design, data-flow-design, security-design, i18n-design, integration-design, analytics-design, writing-plans]
---
# System Design


## 负责代理

`architect` — 系统架构与数据库设计由架构师代理负责，确保技术选型合理、架构分层清晰。

## 何时使用

- `brainstorming` 输出的设计文档中涉及系统架构决策时
- 需要进行**架构设计**（技术选型、模块划分、目录结构）时
- 需要进行**数据库设计**（ER图、表结构、索引策略）时
- 需要绘制时序图、状态图等设计图时
- `writing-plans` 之前，需要补充架构和数据库设计细节时

**触发关键词**: "系统设计"、"架构设计"、"数据库设计"、"ER图"、"技术选型"、"目录结构"

## 与其他技能的关系

```
brainstorming → system-design → writing-plans → executing-plans
     ↑               ↑  ↓              ↑
  需求探索    架构+数据库设计    计划拆解
                   ↓
            api-design（接口设计）
            ui-design（UI设计）
```

> **衔接规则**:
> - `brainstorming` 输出 `*-design.md`：聚焦需求、约束、HOTL 合约
> - `system-design` 输出 `architecture.md` + `database-schema.md`：聚焦架构、数据库、技术决策
> - `api-design` 和 `ui-design` 与 `system-design` **并行执行**，但依赖其输出的技术选型决策
> - 四份设计文档完成后才进入 `writing-plans`

## 设计阶段总体流程

```
需求确认 → 架构设计 → 数据库设计 → API设计 → UI设计
              ↑                            ↓
              └──── 互相校验、迭代调整 ────────┘
```

**输出文件清单**:

```
docs/
├── architecture.md          ← 架构设计（本技能输出）
├── database-schema.md       ← 数据库设计（本技能输出）
├── api-design.md            ← 接口设计（api-design 技能输出）
├── ui-wireframe.md          ← UI/页面设计（ui-design 技能输出）
└── design-decisions.md      ← 设计决策记录（可选，记录关键决策）
```

> **校验关系**: 架构设计中的模块划分 → 数据库设计中的实体 → API 设计中的接口 → UI 设计中的页面，四者必须一致。任何不一致需回到上游修正。

---

## 执行流程

### Phase 1: 架构设计

**目标**: 确定系统整体架构、技术选型和项目目录结构。

#### Step 1: 技术选型决策

**必须回答的决策点**:

| 决策项 | 要回答的问题 | 个人项目推荐 |
|--------|-------------|-------------|
| **整体模式** | 单体 / 前后端分离 / Serverless / BaaS？ | 前后端分离或 BaaS |
| **前端框架** | React / Vue / Svelte？SSR / SPA？ | React SPA（熟悉生态） |
| **后端方案** | 自建 API / BaaS（Supabase）/ Serverless Functions？ | 根据复杂度选择 |
| **数据库** | PostgreSQL / MySQL / SQLite / MongoDB？ | PostgreSQL（功能最全） |
| **认证方案** | 自建 / NextAuth / Clerk / Supabase Auth？ | NextAuth（开源）或自建 Auth |
| **文件存储** | 本地 / S3 / R2 / Supabase Storage？ | Cloudflare R2（开源协议）或 MinIO（自托管） |
| **状态管理** | Zustand / Redux / Jotai / TanStack Query？ | TanStack Query + Zustand |
| **样式方案** | Tailwind / CSS Modules / styled-components？ | Tailwind（AI 生成友好） |
| **组件库** | shadcn/ui / Ant Design / MUI / 手写？ | shadcn/ui（可定制） |
| **部署方式** | Vercel / Railway / 自有 VPS / Docker？ | Docker Compose（自托管） |
| **monorepo?** | 单仓 / pnpm workspace / Turborepo？ | 单体即可，不急于 monorepo |

> **[技术栈条件]** 以上决策由项目 `tech-stack.md` 决定。若 `tech-stack.md` 已存在，直接读取并确认；若不存在，需先完成技术选型并创建该文件。

#### Step 2: 用 AI 做架构设计（3 轮渐进法）

**第 1 轮 Prompt — 让 AI 给方案**:

```
我要做一个 [项目描述]，一个人开发，预算有限。
核心功能：[列出]
预期用户量：[初期 xxx]

请给我 2-3 种技术栈方案，对比优劣，推荐最适合独立开发者的。
```

**第 2 轮 Prompt — 确认方案后细化**:

```
我选择方案 [A/B/C]（[技术栈]），请帮我：
1. 画出项目目录结构
2. 列出需要安装的核心依赖
3. 说明各模块之间的调用关系
4. 指出技术风险和注意事项
```

**第 3 轮 Prompt — 验证扩展性**:

```
这个架构下，如果未来用户量到 1万/10万，
哪些地方会成为瓶颈？现在需要预留什么？
```

#### Step 3: 个人项目架构决策原则

| 原则 | 说明 |
|------|------|
| **优先选「少一层」** | 能用 BaaS 就不自建后端；能用 Serverless 就不管服务器；能用现成服务就不自己造轮子 |
| **优先选「你熟悉的」** | 会 React 就别为了"新"去学 Svelte；会 MySQL 就别硬上 MongoDB |
| **优先选「生态成熟的」** | 遇到问题能搜到答案；AI 训练数据多，生成质量高 |
| **避免过度设计** | 不需要微服务（一个人维护不了）；不需要消息队列（初期没有异步场景）；不需要 K8s（Docker Compose 足够） |

#### Step 4: 输出 architecture.md

文件保存到 `docs/architecture.md`:

```markdown
# 架构设计: [项目名称]

## 1. 架构总览图
（使用 Mermaid 绘制整体结构图）

## 2. 技术选型表

| 层级 | 选择 | 理由 | 被否定的替代方案 |
|------|------|------|-----------------|
| 前端框架 | React 19 | RSC 稳定、Actions API、性能提升 30%+ | Vue（不想学新框架） |
| ... | ... | ... | ... |

## 3. 项目目录结构树

```
project-root/
├── backend/
│   ├── src/
│   │   ├── api/         # Router 层
│   │   ├── services/    # Service 层
│   │   ├── repositories/# Repository 层
│   │   ├── models/      # ORM Model
│   │   └── schemas/     # Pydantic Schema
├── frontend/
│   ├── src/
│   │   ├── pages/       # 页面路由
│   │   ├── components/  # 组件
│   │   ├── hooks/       # 自定义 Hooks
│   │   ├── lib/         # 工具函数
│   │   └── types/       # 类型定义
└── docs/                # 设计文档
```

## 4. 模块划分与职责

| 模块 | 职责 | 依赖 |
|------|------|------|
| API 层 | 路由定义、参数校验、调用 Service | Service 层 |
| Service 层 | 业务逻辑、事务管理 | Repository 层 |
| Repository 层 | 数据库操作 | Model 层 |

## 5. 核心数据流
（描述请求从前端到数据库的完整路径）

## 6. 第三方服务依赖清单

| 服务 | 用途 | 费用 | 替代方案 |
|------|------|------|----------|
| PostgreSQL | 数据库 + 认证 | 免费额度 | — |

## 7. 环境划分

- **local**: 本地开发，热重载，调试日志全开
- **staging**: 预发布环境，与生产一致的数据库
- **prod**: 生产环境，禁用调试、启用监控

## 8. 已知限制与未来扩展点

| 当前限制 | 未来扩展方案 | 触发条件 |
|----------|-------------|----------|
| 单体架构 | 微服务拆分 | 团队 > 3 人 |
| 单数据库 | 读写分离 | QPS > 1000 |
```

---

### Phase 2: 数据库设计

**目标**: 设计完整的数据库 Schema，包含 ER 图、表结构、索引和迁移策略。

#### Step 1: 从需求中提取实体

从 `brainstorming` 输出的需求文档中提取核心实体：

```
用户、项目、任务、标签、评论...
```

#### Step 2: 确定实体关系

```
用户 1:N 项目
项目 1:N 任务
任务 N:M 标签
任务 1:N 评论
```

#### Step 3: 定义字段

每个实体需要定义：
- 字段名 / 类型 / 约束 / 说明
- 默认值 / 是否可空
- 主键策略（自增 / UUID / 雪花ID）

#### Step 4: 设计索引

- 哪些字段会被频繁查询/筛选/排序
- 外键是否需要索引
- 唯一约束字段
- 全文搜索需求

#### Step 5: 考虑扩展

- 软删除？（deleted_at）
- 审计字段？（created_at / updated_at）
- 多租户？（tenant_id）
- JSONB 扩展字段？（谨慎使用）

#### Step 6: 用 AI 做数据库设计

**Prompt 模板**:

```
根据以下需求设计 PostgreSQL 数据库：

业务实体：
[实体1]：[核心属性]
[实体2]：[核心属性]
关系：[描述关系]

要求：
- 使用 UUID 作为主键
- 包含 created_at / updated_at / deleted_at
- 设计合理索引
- 写出完整 CREATE TABLE + INDEX 的 SQL
- 如果用 Supabase，加上 RLS 策略（可选）
- 给出 5 个最常用的查询 SQL 示例
- 指出设计中的取舍和注意事项
```

#### Step 7: 输出 database-schema.md

文件保存到 `docs/database-schema.md`:

```markdown
# 数据库设计: [项目名称]

## 1. ER 图
（使用 Mermaid erDiagram 语法）

## 2. 表清单

| 表名 | 说明 | 预估数据量 |
|------|------|-----------|
| users | 用户表 | 10万 |
| projects | 项目表 | 5万 |

## 3. 表结构定义

### users

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | 主键 |
| email | VARCHAR(255) | UNIQUE, NOT NULL | 邮箱 |
| created_at | TIMESTAMPTZ | NOT NULL | 创建时间 |

### projects

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | UUID | PK | 主键 |
| user_id | UUID | FK → users.id | 所属用户 |
| name | VARCHAR(255) | NOT NULL | 项目名称 |

## 4. 索引设计

| 索引名 | 表 | 字段 | 用途 |
|--------|------|------|------|
| idx_users_email | users | email | 登录查询 |
| idx_projects_user_id | projects | user_id | 用户项目列表 |

## 5. 表关系说明

| 关系 | 类型 | 外键 | 级联策略 |
|------|------|------|----------|
| users → projects | 1:N | projects.user_id | ON DELETE CASCADE |

## 6. 枚举值定义

| 枚举 | 值 | 说明 |
|------|------|------|
| task_status | todo / doing / done | 任务状态 |

## 7. RLM / 权限策略（如用 Supabase，可选）

```sql
-- 用户只能访问自己的项目
CREATE POLICY "Users can only access their own projects"
  ON projects FOR ALL
  USING (auth.uid() = user_id);
```

## 8. 数据量预估

| 表 | 初期 | 1年后 | 索引策略 |
|----|------|-------|----------|
| users | 1千 | 1万 | B-tree |
| projects | 5千 | 5万 | B-tree + 分区 |

## 9. 常用查询 SQL

```sql
-- 查询用户的所有项目
SELECT * FROM projects WHERE user_id = ? ORDER BY created_at DESC;

-- 查询项目的任务统计
SELECT status, COUNT(*) FROM tasks WHERE project_id = ? GROUP BY status;
```

## 10. 迁移策略

使用 [Alembic / Prisma Migrate / Drizzle Kit] 管理 Schema 变更：

```
backend/migrations/
├── 20260724_init.sql
├── 20260725_add_tags.sql
└── ...
```
```

---

### Phase 3: 详细设计补充

**目标**: 为关键业务流程补充时序图和状态图。

#### 核心时序图

为关键业务流程绘制时序图（使用 Mermaid sequenceDiagram）：
- 覆盖：正常流程 + 主要异常流程
- 标注跨模块调用和外部服务交互

#### 状态图

为有生命周期的实体绘制状态图（使用 Mermaid stateDiagram-v2）：
- 明确状态转换条件和触发事件
- 标注不可达状态和非法转换

#### 异常处理方案

- 定义统一错误码体系
- 设计全局异常处理中间件
- 标注哪些异常需要重试、哪些需要熔断

---

### Phase 4: 自检与衔接

#### 自检清单

**架构设计检查**:
- [ ] 所有 11 项技术选型决策已回答
- [ ] 项目目录结构清晰，模块职责明确
- [ ] 核心数据流已描述
- [ ] 第三方服务依赖已列出费用和替代方案
- [ ] 已知限制和未来扩展点已记录

**数据库设计检查**:
- [ ] 主键策略确定（自增 / UUID / 雪花ID）
- [ ] 所有表有 created_at / updated_at
- [ ] 需要软删除的表有 deleted_at
- [ ] 外键关系明确（CASCADE / RESTRICT / SET NULL）
- [ ] 枚举字段用 VARCHAR + CHECK 或单独枚举表
- [ ] 高频查询字段有索引
- [ ] 唯一约束该加的加了（手机号、邮箱、slug）
- [ ] 大文本字段用 TEXT 不用 VARCHAR(255)
- [ ] 金额用 DECIMAL / INTEGER（分）不用 FLOAT
- [ ] 时间统一用 UTC + TIMESTAMPTZ
- [ ] 预留了扩展字段或 JSON 字段（谨慎使用）

**交叉校验**:
- [ ] 架构中的模块 → 数据库中的实体 一一对应
- [ ] 数据库中的表 → API 设计中的接口 覆盖完整
- [ ] 数据库字段 → UI 设计中的表单字段 一致

#### 进入下游技能

```
system-design 完成
    ├── → api-design（基于架构和数据库设计接口）
    ├── → ui-design（基于架构和数据库设计页面）
    └── → writing-plans（四份设计文档全部完成后）
```

---

## 硬性规则

- ✅ **必须使用 Mermaid 绘制图表** — ER图、时序图、状态图统一使用 Mermaid
- ✅ **必须记录设计决策** — 每个重要决策需记录选择和被否定的替代方案
- ✅ **必须覆盖异常流程** — 时序图不能只有 Happy Path
- ✅ **模块边界必须清晰** — 遵循 Clean Architecture 分层，禁止循环依赖
- ✅ **必须先读取 `tech-stack.md`** — 架构设计受技术栈约束
- ✅ **数据库设计必须包含检查清单全部 11 项** — 防止常见设计缺陷
- ✅ **主键必须用 UUID** — 避免自增 ID 的安全和迁移问题
- ✅ **所有表必须有审计字段** — created_at / updated_at 不可少
- ❌ **禁止在设计文档中写具体代码实现**（>10 行代码块）
- ❌ **禁止跳过异常处理设计**
- ❌ **禁止模块间直接跨层调用**
- ❌ **禁止手动改表** — Schema 变更必须通过迁移工具
- ❌ **禁止在迁移脚本中硬编码数据库连接字符串**

## Prompt 模板

### 架构设计模板

```
我要用 [技术栈，如 Next.js + PostgreSQL / FastAPI + Docker] 做一个 [XXX] 项目，
功能包括：[列出功能]

请帮我设计：
1. 项目目录结构
2. 数据库表结构（DDL）
3. 核心 API 路由设计
4. 页面路由规划
5. 需要注意的技术难点
```

### 数据库设计模板

```
根据以下需求，帮我设计数据库：
[描述核心实体和关系]

请输出：
1. 完整 CREATE TABLE 语句
2. 索引设计
3. 常用查询 SQL 示例
4. 数据迁移策略（如有）
```

### 核心时序图模板

```
请为以下业务流程绘制时序图：
[描述流程步骤和参与者]

覆盖场景：
- 正常流程（Happy Path）
- 主要异常流程（参数校验失败/权限不足/超时）
```

## 反模式

- ❌ "先写代码再画图" — 设计图应指导实现，不是事后补文档
- ❌ 时序图只有正常流程 — 异常流程才是 Bug 高发区
- ❌ ER 图缺少索引策略 — 上线后性能问题难以排查
- ❌ 模块边界模糊 — "utils 什么都能放"是反模式
- ❌ 设计决策无记录 — 后来者不知道为什么这样选
- ❌ 直接用 `psql` 执行 ALTER TABLE — 绕过了版本控制
- ❌ 不写 downgrade — 出问题时无法回滚
- ❌ 一个迁移脚本包含 10 个不相关的变更 — 应拆分为多个迁移
