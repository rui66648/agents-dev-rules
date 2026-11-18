---
name: hotl-contracts
version: v1.2.1
type: rule
enabled: true
mode: [standard, creator]
updated: 2026-11-11
description: HOTL 合约定义 — Intent / Verification / Governance 三合约完整规范
applies_to:
  agents: ['architect', '全部 Agent']
  phases: ['design', 'implementation']
  project_types: ['全部']
  tech_stacks: ['全部']
---
# HOTL 合约定义
> **本文件落实**: RULE-004（"完成"声明前必须通过验证）
> **引用** RULE-002（设计文档未批准前禁止写代码，落点见 `rules/collaboration.md`）——本文件只定义三合约的字段与完整性门禁。

> HOTL（Human-On-The-Loop）合约是设计文档的核心组成部分，确保人机协作的可追溯性与可验证性。

> **完整性门禁**：三合约中任一「必填」字段缺失时，设计文档不得标记为已批准（对应 RULE-002）。Governance 合约缺失 `approval_gates` / `rollback` 时，高风险任务禁止进入 `executing-plans`。

## 7.1 Intent Contract（目标合约）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `intent` | string | 是 | 一句话目标，清晰无歧义 |
| `scope` | object | 是 | 明确"做"与"不做"的边界 |
| `scope.in` | string[] | 是 | 本次包含的工作范围 |
| `scope.out` | string[] | 是 | 明确排除的工作范围（预防 Scope Creep） |
| `constraints` | string[] | 是 | 不可改变/破坏的约束条件 |
| `success_criteria` | string[] | 是 | 验收标准，可量化验证 |
| `risk_level` | enum | 是 | `low` / `medium` / `high` |

**风险等级判定：**

| 等级 | 判定条件 | 审批要求 | 示例 |
|------|----------|----------|------|
| `high` | 安全/认证/隐私/计费/生产数据变更 | 必须人工门禁 | 2FA、支付接口、DB Schema 变更 |
| `medium` | 多模块交互/外部 API 集成/数据迁移 | 需人工确认设计 | 第三方登录、批量导入 |
| `low` | 单模块优化/UI 调整/文档/配置 | 自检通过即可 | 样式调整、日志优化 |

**示例：**
```yaml
intent: 为用户登录接口添加双因素认证 (2FA)
scope:
  in:
    - TOTP 生成与验证逻辑
    - 用户设置页面增加 2FA 开关
    - 登录接口集成 2FA 验证步骤
  out:
    - 不涉及 SMS 短信验证方式
    - 不涉及后台管理界面的 2FA 统计
    - 不涉及已有用户的强制迁移
constraints:
  - 不能破坏现有 JWT 认证流程
  - 必须兼容现有用户数据
  - 必须在 500ms 内完成验证
success_criteria:
  - 用户可在设置中启用/禁用 2FA
  - 登录时正确验证 TOTP 码
  - 单元测试覆盖率达到 90%   # 示例值，实际阈值以 tech-stack.md 约定为准
risk_level: high
```

## 7.2 Verification Contract（验证合约）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `verify_steps` | object[] | 是 | 验证步骤列表 |
| `verify_steps[].phase` | enum | 是 | `pre` / `during` / `post` / `rollback` |
| `verify_steps[].run` | string | 是 | 执行的命令或操作 |
| `verify_steps[].check` | string | 是 | 检查的内容 |
| `verify_steps[].confirm` | string | 是 | 成功信号 |
| `verify_steps[].checkpoint` | bool | 否 | 是否保存检查点（during 阶段） |
| `verify_steps[].fail_action` | string | 否 | 失败时行动：`abort` / `rollback` / `continue` |

**四阶段验证模型：**

| 阶段 | 验证点 | 通过标准 | fail_action |
|------|--------|---------|-------------|
| `pre` | 前置条件 | 依赖安装、配置就绪、测试环境可用 | `abort` |
| `during` | 过程检查 | 每步完成后快照 + 测试通过 | `continue`（可记录） |
| `post` | 最终验证 | 全部测试通过、lint 无警告 | `rollback` |
| `rollback` | 回滚验证 | 回滚后系统可恢复 | — |

**示例：**
```yaml
verify_steps:
  - phase: pre
    run: pip install -r requirements.txt && alembic check
    check: 依赖就绪、数据库连接正常
    confirm: "Alembic check passed"
    fail_action: abort

  - phase: during
    run: pytest tests/auth/test_2fa.py -v
    check: 所有测试用例通过
    confirm: "100% passed"
    checkpoint: true
    fail_action: continue

  - phase: post
    run: pytest --tb=short -q
    check: 全部测试通过、lint 无警告
    confirm: "All checks passed"
    fail_action: rollback
```

## 7.3 Governance Contract（治理合约）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `approval_gates` | string[] | 是 | 需要人工审查的步骤 |
| `rollback` | string | 是 | 出问题时的回滚方案 |
| `ownership` | string | 是 | 负责人（角色或用户） |
| `checkpoints` | object[] | 否 | 关键检查点列表（during 阶段） |
| `checkpoints[].name` | string | 是 | 检查点名称 |
| `checkpoints[].save` | string | 是 | 保存的命令（如 git commit） |
| `checkpoints[].load` | string | 是 | 恢复的命令（如 git checkout） |

**示例：**
```yaml
approval_gates:
  - 设计文档审批（安全相关）
  - 数据库 Schema 变更审查
  - 生产环境部署前最终确认
rollback: |
  1. 关闭 2FA 功能开关
  2. 回滚数据库迁移 (alembic downgrade)
  3. 回滚代码到上一版本
ownership: backend-developer
checkpoints:
  - name: 接口实现完成
    save: "git add -A && git commit -m 'feat: 2FA 接口实现'"
    load: "git checkout HEAD~1 -- ."
  - name: 测试通过
    save: "git add -A && git commit -m 'test: 2FA 测试通过'"
    load: "git checkout HEAD~1 -- ."
```

## 7.4 Checkpoint 机制说明

**何时保存 Checkpoint**

| 场景 | 建议 Checkpoint | 说明 |
|------|---------------|------|
| 单个接口实现完成 | 必须 | 可回滚到干净状态 |
| 单元测试全部通过 | 必须 | 保留已验证状态 |
| 数据库迁移执行前 | 必须 | 防止损坏数据 |
| 文件批量修改（>10 个） | 建议 | 便于局部回滚 |
| 多步设计文档确认 | 建议 | 保留设计版本 |

**Checkpoint 格式**

```yaml
# 在 design-doc.md 或 hotl-contracts.md 中声明
## Checkpoint 列表

| # | 名称 | 保存命令 | 恢复命令 | 状态 |
|---|------|---------|---------|------|
| 1 | 接口实现完成 | `git commit -m "checkpoint: 接口实现"` | `git reset --hard HEAD~1` | ✅ 已保存 |
| 2 | 测试通过 | `git commit -m "checkpoint: 测试通过"` | `git reset --hard HEAD~1` | ⏳ 待执行 |
```
