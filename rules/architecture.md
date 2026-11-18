---
name: architecture
version: v1.1.0
type: rule
enabled: true
mode: [standard, creator]
updated: 2026-11-11
description: 架构设计规则 — Clean Architecture 分层、依赖注入、事务/缓存/流式响应约束（RULE-005 DB Schema 变更必须走迁移工具）
applies_to:
  agents: ['architect', 'backend-developer', 'database-expert']
  phases: ['design', 'implementation']
  project_types: ['backend', 'fullstack', 'mobile']
  tech_stacks: ['python', 'kotlin', 'typescript']
---
> **本文件落实**: RULE-005（DB Schema 变更必须通过迁移工具，不得手动改表结构）

## 禁止事项

- ❌ 在 Router 层编写业务逻辑
- ❌ 在 Router 层编写 SQL 查询
- ❌ Router 直接调用 Repository 或 Model 进行数据操作
- ❌ Service 内部硬编码数据库连接或外部服务客户端
- ❌ 在前端组件中编写复杂业务逻辑
- ❌ 手动修改数据库表结构（必须使用 Alembic）
- ❌ 迁移脚本缺少 downgrade 回滚逻辑
- ❌ 使用 `alert()` 展示错误信息
- ❌ 在 Repository 层开启或提交事务
- ❌ 使用嵌套事务
- ❌ 大量数据操作不使用批量操作导致事务过大
