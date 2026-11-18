---
name: anti-patterns
version: v1.2.0
type: rule
enabled: true
mode: [standard, creator]
updated: 2026-11-07
description: 反模式禁止清单索引 — 按后端/前端/测试/流程/安全/性能/AI 辅助/SDD 分类
applies_to:
  agents: ['code-reviewer', '全部 Agent']
  phases: ['全程']
  project_types: ['全部']
  tech_stacks: ['全部']
---
# 反模式禁止清单索引 (Anti-Patterns Index)

> **适用范围**: 通用原则，适用于所有项目。项目特定规范见项目根目录 `tech-stack.md`。

本文件为项目反模式的索引汇总，详细规则请查阅各具体规则文件。

## 后端反模式

| 反模式 | 来源文件 |
|--------|----------|
| 在 Router 层编写业务逻辑 | [architecture.md](rules/architecture.md) |
| 在 Router 层编写 SQL 查询 | [architecture.md](rules/architecture.md) |
| 在循环中执行数据库查询 | [performance-rules.md](rules/performance-rules.md) |
| 手动修改数据库表结构 | [architecture.md](rules/architecture.md) |
| 在迁移脚本中硬编码数据库连接字符串 | [security-rules.md](rules/security-rules.md) |
| 使用 `eval()` 或 `exec()` | [security-rules.md](rules/security-rules.md) |
| 硬编码密钥、密码或 URL | [security-rules.md](rules/security-rules.md) |
| 在生产环境使用 `print()` | [security-rules.md](rules/security-rules.md) |
| 在 Repository 层开启或提交事务 | [architecture.md](rules/architecture.md) |
| 使用嵌套事务 | [architecture.md](rules/architecture.md) |

## 前端反模式

| 反模式 | 来源文件 |
|--------|----------|
| 在 TypeScript 中使用 `any` 类型 | [coding-standards.md](rules/coding-standards.md) |
| 忽略 TypeScript 编译错误或 ESLint 警告 | [coding-standards.md](rules/coding-standards.md) |
| 前端组件直接调用数据库 | [architecture.md](rules/architecture.md) |
| 在 React 组件 render 中执行副作用 | [coding-standards.md](rules/coding-standards.md) |
| 在 React 中使用 Class 组件 | [coding-standards.md](rules/coding-standards.md) |
| 单个组件超过 300 行不拆分 | [coding-standards.md](rules/coding-standards.md) |

## 测试反模式

| 反模式 | 来源文件 |
|--------|----------|
| 跳过测试声称功能"完成" | [testing-rules.md](rules/testing-rules.md) |
| 编写不包含断言的空测试 | [testing-rules.md](rules/testing-rules.md) |
| 测试之间共享可变状态 | [testing-rules.md](rules/testing-rules.md) |
| 测试命名描述实现而非行为 | [testing-rules.md](rules/testing-rules.md) |

## 工程流程反模式

| 反模式 | 来源文件 |
|--------|----------|
| 安装依赖未经确认 | [coding-standards.md](rules/coding-standards.md) |
| 猜测根因而不调试 | [coding-standards.md](rules/coding-standards.md) |
| 直接提交到 `main` / `master` 分支 | [git-conventions.md](rules/git-conventions.md) |
| 提交未经格式化的代码 | [coding-standards.md](rules/coding-standards.md) |
| 使用中文编写 commit message | [git-conventions.md](rules/git-conventions.md) |
| 单个 PR 超过 400 行变更 | [git-conventions.md](rules/git-conventions.md) |

## 安全反模式

| 反模式 | 来源文件 |
|--------|----------|
| CORS 配置使用 `*` 通配符 | [security-rules.md](rules/security-rules.md) |
| 在日志中记录敏感数据 | [security-rules.md](rules/security-rules.md) |
| 将 `.env` 文件提交到代码仓库 | [security-rules.md](rules/security-rules.md) |
| 公开端点不设置 Rate Limiting | [security-rules.md](rules/security-rules.md) |
| JWT Token 不设置过期时间 | [security-rules.md](rules/security-rules.md) |
| 明文存储密码 | [security-rules.md](rules/security-rules.md) |
| 拼接 SQL 字符串 | [security-rules.md](rules/security-rules.md) |

## 性能反模式

| 反模式 | 来源文件 |
|--------|----------|
| 复杂查询不添加索引 | [performance-rules.md](rules/performance-rules.md) |
| 列表接口不实现分页 | [performance-rules.md](rules/performance-rules.md) |
| 返回包含大量冗余字段的巨大 payload | [performance-rules.md](rules/performance-rules.md) |
| 缓存不设置 TTL | [performance-rules.md](rules/performance-rules.md) |
| 同步加载所有重型组件 | [performance-rules.md](rules/performance-rules.md) |

## AI 辅助开发特有反模式

> **v1.1.0（ADR-006）**：原清单多为"弱模型 + 人逐条提问"时代的条目（盲目信任、过度依赖、上下文丢失、一次生成太多、完美主义等），已删除。保留以下与"验证"直接相关的项。

| 反模式 | 说明 | 对策 |
|--------|------|------|
| **AI 幻觉** | 编造不存在的 API、库、参数 | 用**可执行验证**兜底：类型检查、单元测试、真实调用，而非记忆或关键词白名单 |
| **代码膨胀** | 倾向写冗长、过度抽象的代码 | 遵循 YAGNI 与"最小变更"；无调用方的抽象一律不加 |
| **安全忽视** | 不主动考虑安全风险 | 遵循 `security-rules.md`；提交前跑安全扫描 |
| **范围蔓延** | "再加个小功能"停不下来 | 严格 MVP 范围；用 HOTL Intent Contract 的 `scope.out` 控制 |

## 规格驱动（SDD）特有反模式（v1.2.0 新增，ADR-008）

> 以下条目来自 spec-kit / Kiro 社区已公开记录的失败模式，判据与对策见
> `rules/spec-driven.md` 与 `docs/research/2026-11-07-spec-driven-development.md` §4。

| 反模式 | 症状 | 对策 |
|--------|------|------|
| **规格漂移** | 代码改了、spec 没改；agent 按过期 spec 自信地做错事 | commit 记 `spec:<slug>@v<N>`；`spec-clarity-gate.mjs` 判 FAIL |
| **静默猜测** | 遇到关键分歧"合理地猜一个"，错在集成/生产才暴露 | `[NEEDS CLARIFICATION]` 显式标记（≤3 个），有遗留不进 plan |
| **Markdown 瀑布** | spec 越写越长，agent 读不完开始 skim → 反而更容易漂移 | 单 spec ≤200 行；超了按 US 拆，不是压缩 |
| **HOW 泄漏** | spec 里写技术栈、文件路径、代码块 | 见 `workflow-design.md` 规格纪律；门禁对代码块判 FAIL、选型词判 WARN |
| **假安全感** | 把"验证实现"这类 task 标 done，却没有任何单测 | `rules/testing-rules.md` 禁止事项 + tasks 的 Checkpoint 停机验收 |
| **双重代码审查** | 规格里已含代码，实现里还有 bug → 同一件事审两遍 | spec 只写 WHAT/WHY；审查一份 plan + 一份代码，不审两份"代码" |
| **spec-as-source 执念** | 要求"人永不碰代码"，代码只从规格生成 | 个人项目用 spec-anchored：规格可手改，但改规格必须同批改代码 |
| **为填模板编宪法** | 把不成立的原则写进 constitution，后续 plan/analyze 全是噪音 | 宪法只写仓内**已成立**的条目（README/ADR/CI 为证，RULE-056 §2） |