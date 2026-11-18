---
name: migrate
version: v1.0.0
type: command
enabled: true
mode: [standard, creator]
updated: 2026-08-03
description: 斜杠命令：migrate - "迁移数据库"、"alembic"、"schema 变更"、"创建迁移"
---
# /migrate - 数据库迁移

**触发词**: "迁移数据库"、"alembic"、"schema 变更"、"创建迁移"

---

## 命令语法

```
/migrate [action] [--message="描述"] [--auto=true|false] [--env=dev|staging|prod]
```

## 参数说明

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `action` | enum | 否 | `create` | 操作类型：`create`（创建迁移）、`upgrade`（升级）、`downgrade`（回滚）、`history`（查看历史）、`check`（检查状态） |
| `--message` | string | `action=create` 时必填 | 无 | 迁移描述，如 `add_user_status_column` |
| `--auto` | bool | 否 | `true` | 是否使用 autogenerate（`true`：自动检测 Model 变更；`false`：手写迁移） |
| `--env` | enum | 否 | `dev` | 目标环境：`dev`、`staging`、`prod` |

## 触发场景

- 新增或修改 SQLAlchemy Model 后，需要同步到数据库 Schema
- 需要回滚错误的数据库变更
- 查看当前数据库的迁移历史与状态
- 部署前检查是否有未执行的迁移脚本
- 需要手动编写复杂迁移（数据迁移、分表等）

## 前置条件

1. Alembic 已初始化（`alembic.ini` 和 `versions/` 目录存在）
2. 数据库连接配置正确（`.env` 中 `DATABASE_URL` 已配置）
3. 目标数据库可访问且权限充足（DDL 权限）
4. 如 `action=create`，SQLAlchemy Model 已修改并保存
5. 已备份数据库（生产环境操作前）

## 执行流程

1. **状态检查** — 确认当前数据库版本与迁移历史状态
2. **变更确认** — 如 `action=create`，对比 Model 与当前 Schema，确认变更意图
3. **迁移生成** — 如 `--auto=true`，执行 `alembic revision --autogenerate`；否则创建空白迁移模板
4. **脚本审查** — 人工检查生成的迁移脚本 SQL 逻辑，确认 `upgrade` / `downgrade` 完整性
5. **本地验证** — 在 dev 环境执行 `upgrade` + `downgrade` + `upgrade`，验证可回滚性
6. **执行迁移** — 在目标环境执行 `alembic upgrade head`
7. **结果验证** — 确认 Schema 变更生效，应用正常运行
8. **文档归档** — 记录迁移内容、影响表、回滚指令

## 产出物

- **迁移脚本**：`alembic/versions/YYYY-MM-DD_<hash>_<message>.py`
- **执行日志**：`upgrade` / `downgrade` 执行记录
- **验证结果**：Schema 变更确认、数据完整性检查结果
- **回滚指令**：`alembic downgrade <target_version>`

## 错误处理

| 常见错误 | 处理方式 |
|----------|----------|
| autogenerate 未检测到变更 | 确认 Model 已保存，或改为 `--auto=false` 手写迁移 |
| 迁移脚本生成后无法 upgrade | 检查生成的 SQL 合法性，修正后重新执行 |
| downgrade 逻辑缺失 | 标记为 Blocker，要求补充 `downgrade()` 实现 |
| 数据库版本不一致（多人协作） | 合并迁移脚本，确保线性版本历史，避免分支迁移 |
| 生产环境迁移超时 | 对大表操作使用 `op.batch_alter_table` 或分批次执行 |
| 迁移后应用报错 | 立即执行 `alembic downgrade` 回滚，排查问题后重试 |

## 示例

### 示例 1：自动创建迁移并应用到开发环境

```
/migrate create --message="add_user_status_column" --auto=true --env=dev
```

**预期输出**：
- 检测到 `User` 模型新增 `status` 字段
- 生成迁移脚本 `alembic/versions/20260724_a1b2c3d4_add_user_status_column.py`
- 自动执行 `upgrade` 到 dev 数据库
- 验证：用户表新增 `status` 列（VARCHAR，默认 `active`）

### 示例 2：回滚生产环境最后一次迁移

```
/migrate downgrade --env=prod
```

**预期输出**：
- 确认当前版本 `a1b2c3d4`
- 回滚到上一个版本 `e5f6g7h8`
- 执行 `alembic downgrade e5f6g7h8`
- 验证：Schema 恢复到回滚前状态
- 应用运行正常

---

**执行流程**: 遵循 [database-migration 技能](skills/database-migration/SKILL.md`) 的完整流程
