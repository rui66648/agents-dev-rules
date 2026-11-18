---
name: monitoring-rules
version: v1.0.1
type: rule
enabled: true
mode: [standard, creator]
updated: 2026-11-11
description: 监控与告警规范 — 健康检查、结构化日志聚合、核心指标、告警机制（RULE-049）
applies_to:
  agents: ['backend-developer', 'security-auditor']
  phases: ['deploy', 'operations']
  project_types: ['全部']
  tech_stacks: ['全部']
---
# 监控与告警规范 (Monitoring & Alerting)
> **本文件落实**: RULE-049（监控与告警）

> **核心目标**: 线上故障可被发现、可被定位、可被响应，避免「线上挂了没人知道」。

---

## 核心规则

| 编号 | 规则 | Enforcement 路径 |
|------|------|------------------|
| RULE-049 | 监控与告警遵循本规则 | `/health` 端点 + 日志聚合 + 告警服务 |

---

## 健康检查端点（必须）

- 每个服务必须提供 `/health` 端点，返回 `{"status": "ok"}` 及依赖状态（DB/Redis）
- 部署后必须执行健康检查（对应 `.deployed.json` 的 `healthCheck` 字段）
- 健康检查失败视为部署失败，触发回滚

---

## 结构化日志聚合

- 使用 `structlog` 输出 JSON 日志（遵循 `security-rules.md` 日志规范）
- 日志必须包含 `request_id`、`level`、`timestamp`、`logger`、`message`
- 线上日志必须可检索（本地文件 + 远端聚合二选一）

---

## 核心指标

| 指标 | 说明 | 告警阈值（建议） |
|------|------|------------------|
| 错误率 | 5xx / 总请求 | > 1% 持续 5 分钟 |
| 延迟 | P95 响应时间 | > 1s 持续 5 分钟 |
| 资源 | CPU / 内存 / 磁盘 | CPU > 80% / 磁盘 > 85% |
| 可用性 | 健康检查失败次数 | 连续 3 次失败 |

---

## 告警机制（推荐）

- 个人项目使用轻量告警：UptimeRobot / Cloudflare Health Checks / 自建 cron + 邮件
- 告警通道：邮件 / 飞书机器人 / Telegram（任选其一）
- 告警内容必须包含：服务名、环境、指标值、时间、处理建议

---

## 故障响应流程

1. 收到告警 → 确认影响范围
2. 查看日志定位根因（按 `request_id` 追踪）
3. 修复或回滚（回滚命令见 `.deployed.json` 的 `rollback`）
4. 恢复后更新 `.deployed.json` 并记录故障原因

---

## 禁止事项

- ❌ 线上服务无健康检查端点
- ❌ 日志不包含 `request_id`（无法追踪）
- ❌ 告警无接收人/无响应流程
