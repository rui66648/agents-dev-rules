---
name: backup-recovery
version: v1.0.1
type: rule
enabled: true
mode: [standard, creator]
updated: 2026-11-11
description: 备份与恢复规范 — 数据库定期备份、备份存储、恢复演练（RULE-050）
applies_to:
  agents: ['database-expert', 'backend-developer', 'architect']
  phases: ['deploy', 'operations']
  project_types: ['全部']
  tech_stacks: ['全部']
---
# 备份与恢复规范 (Backup & Recovery)
> **本文件落实**: RULE-050（备份与恢复）

> **核心目标**: 线上数据可恢复，避免「数据丢失 = 项目终结」。

---

## 核心规则

| 编号 | 规则 | Enforcement 路径 |
|------|------|------------------|
| RULE-050 | 备份与恢复遵循本规则 | 备份脚本 + 恢复演练记录 |

---

## 数据库备份策略

| 数据 | 备份频率 | 保留周期 | 存储位置 |
|------|---------|---------|---------|
| 数据库（PostgreSQL） | 每日 | 30 天 | 本地 + 远端对象存储（R2/S3） |
| 上传文件 | 每周 | 90 天 | 远端对象存储 |
| 配置/部署记录 | 随代码 | 永久 | Git 仓库 |

备份命令示例（PostgreSQL）：

```bash
pg_dump -Fc "$DATABASE_URL" > backups/db-$(date +%Y%m%d).dump
# 远端备份（可选）
rclone copy backups/db-*.dump r2:backup-bucket/
```

---

## 备份验证（必须）

- 每次备份后必须验证备份文件可读（`pg_restore --list` 检查）
- 备份文件大小异常（为 0 或过小）视为备份失败，需告警

---

## 恢复演练

- 每季度至少执行一次恢复演练（从备份恢复到临时库）
- 演练记录写入 `docs/operations/restore-drill.md`：日期、备份点、恢复耗时、结果
- 恢复流程：
  1. 创建临时数据库
  2. 从最新备份恢复
  3. 校验关键数据完整性
  4. 记录演练结果

---

## 禁止事项

- ❌ 线上数据库无备份
- ❌ 备份文件仅存本地（无远端副本）
- ❌ 备份后不验证文件可读性
- ❌ 从未执行恢复演练
