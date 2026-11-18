---
name: deploy
version: v1.0.0
type: skill
enabled: true
mode: [standard, creator]
description: "需要部署应用到开发/预发布/生产环境时使用。遵循标准化部署流程，确保部署安全可靠、可回滚。触发词: 部署、发布、上线、deploy、release。"
updated: 2026-08-13
depends_on: [executing-plans]
composes: [ops-monitoring]
---
# Deploy


## 负责代理

`backend-developer` — 部署上线由后端开发工程师代理负责，确保部署流程标准化、可回滚。

## 何时使用

- 需要将代码部署到开发环境时
- 需要将代码部署到预发布环境时
- 需要将代码部署到生产环境时
- 需要更新或回滚部署时

**触发关键词**: "部署"、"上线"、"deploy"、"发布"、"回滚"

## 与其他技能的关系

```
brainstorming → system-design → deploy（设计阶段）
                                      ↓
                               executing-plans → deploy（执行阶段）
                                      ↓
                               ops-monitoring（运维监控）
```

> **衔接规则**: `deploy` 分为两个阶段：
> - **设计阶段**：在编码前输出 `deployment-design.md`，定义环境划分、CI/CD流水线和运维方案
> - **执行阶段**：在编码完成后按设计文档执行部署

## 执行流程

### Phase 0: 设计阶段（输出 deployment-design.md）

**目标**: 在编码前完成部署与运维方案设计，确保上线流程可靠可重复。

#### Step 1: 环境划分

| 环境 | 用途 | 配置来源 | 数据 | 访问 |
|------|------|----------|------|------|
| local | 本地开发 | `.env.local` | 本地Docker | localhost |
| staging | 预发布验证 | `.env.staging` | 脱敏数据 | 内部域名 |
| prod | 生产环境 | `.env.production` | 真实数据 | 正式域名 |

#### Step 2: CI/CD 流水线设计

定义从代码提交到生产部署的完整流水线：

```
PR -> Lint -> 单元测试 -> 构建 -> Staging部署 -> 集成测试 -> 人工审批 -> 生产部署
```

**流水线配置要点**:
- 代码推送自动触发 CI
- PR 合并到 main 自动部署 staging
- 生产部署需要人工审批
- 每次部署保留构建产物用于回滚

#### Step 3: 部署方案选择

根据项目规模和预算选择部署方案：

| 方案 | 适用场景 | 费用 | 复杂度 |
|------|----------|------|--------|
| Docker Compose + VPS | 需要完全控制 | $5-20/月 | 中 |
| K8s | 大规模/高可用 | 高 | 高 |

#### Step 4: 运维监控设计

| 监控维度 | 工具 | 告警条件 | 通知方式 |
|----------|------|----------|----------|
| 服务可用性 | Uptime Kuma（自托管） | 连续3次检测失败 | 邮件/飞书 |
| API 性能 | Prometheus + Grafana | P95 > 1s | 飞书 |
| 错误追踪 | GlitchTip（自托管） | 新错误出现 | 飞书 |
| 数据库 | pgAdmin / Supavisor | 连接数 > 80% | 邮件 |
| 日志 | Loki + Grafana / ELK | Error 级别 | 飞书 |

#### Step 5: 输出 deployment-design.md

文件保存到 `docs/deployment-design.md`：

```markdown
# 部署与运维设计: [项目名称]

## 1. 环境划分

## 2. CI/CD 流水线
### 2.1 流水线配置
### 2.2 构建产物管理

## 3. 部署方案
### 3.1 方案选择与理由
### 3.2 域名与SSL配置

## 4. 运维监控
### 4.1 监控指标与告警
### 4.2 日志聚合方案
### 4.3 备份策略

## 5. 回滚方案
```

---

### Phase 1: 部署前检查

**目标**: 确保部署前所有条件满足。

检查清单:
- ✅ 所有测试通过（`pytest` / `pnpm test`）
- ✅ Lint 检查通过（`ruff check` / `pnpm lint`）
- ✅ 类型检查通过（`pnpm typecheck`）
- ✅ 构建成功（`pnpm build`）
- ✅ 数据库迁移脚本已准备（如适用）
- ✅ 环境变量配置完整（`.env`）
- ✅ Docker 配置正确（`docker-compose.yml`）

### Phase 2: 数据库迁移

**目标**: 在应用部署前完成数据库 Schema 变更。

```bash
# 1. 备份数据库（生产环境）
pg_dump -U user -d dbname > backup_before_deploy.sql

# 2. 执行迁移
uv run alembic upgrade head

# 3. 验证迁移结果
uv run alembic current
uv run pytest tests/models/ -v
```

### Phase 3: 构建与部署

**目标**: 构建应用并部署到目标环境。

#### 开发环境
```bash
# 后端
uv run fastapi dev

# 前端
pnpm dev
```

#### 预发布/生产环境
```bash
# 停止旧服务
docker compose down

# 构建新镜像
docker compose build

# 启动新服务
docker compose up -d

# 等待服务启动
sleep 10

# 健康检查
curl -f http://localhost:8000/health
```

### Phase 4: 部署后验证

**目标**: 确认部署成功且服务正常运行。

验证清单:
- ✅ 服务启动成功（`docker compose ps`）
- ✅ 健康检查通过（`/health` 端点）
- ✅ 核心 API 功能正常
- ✅ 前端页面可访问且渲染正常
- ✅ 日志中无错误信息

### Phase 5: 回滚（如需要）

**目标**: 在部署失败时快速回滚到上一版本。

```bash
# 停止当前服务
docker compose down

# 回滚数据库（如有迁移失败）
uv run alembic downgrade -1

# 使用上一版本镜像启动
docker compose up -d --no-build

# 验证回滚结果
curl -f http://localhost:8000/health
```

## 部署策略

### 蓝绿部署
- 生产环境推荐使用蓝绿部署策略
- 蓝环境运行当前版本，绿环境部署新版本
- 验证绿环境通过后切换流量

### 滚动更新
- 使用 Docker Compose 的滚动更新功能
- 逐步替换容器，避免服务中断

## 环境配置

### `.env` 文件规范
每个环境必须有独立的 `.env` 文件：
- `.env.development` — 开发环境
- `.env.staging` — 预发布环境
- `.env.production` — 生产环境

### 敏感配置
- 数据库密码、API Key、JWT Secret 等必须存储在环境变量中
- 禁止在代码中硬编码任何敏感信息

## 硬性规则

- ✅ **部署前必须通过所有测试** — 测试是部署的前提条件
- ✅ **生产环境部署前必须备份数据库** — 防止数据丢失
- ✅ **部署后必须执行健康检查** — 确认服务正常
- ✅ **必须有回滚方案** — 准备好回滚步骤
- ✅ **不同环境使用不同配置** — 禁止开发配置用于生产
- ❌ **禁止跳过测试直接部署** — 测试是安全网
- ❌ **禁止在生产环境使用开发配置** — 安全风险
- ❌ **禁止部署未验证的迁移脚本** — 必须先在 staging 验证
- ❌ **禁止在部署过程中修改代码** — 确保部署包与测试包一致

## 部署 Prompt 模板

> 以下 Prompt 模板可在部署阶段使用。

### 部署步骤生成模板

```
我的项目是 [技术栈，如 Next.js + PostgreSQL / FastAPI + Docker]，请帮我：
1. 写一份 [Docker Compose] 部署步骤
2. 列出需要配置的环境变量
3. 配置自定义域名步骤（如需要）
4. 上线前的 checklist
5. 写一份简单的监控方案（开源方案优先）
```

### 个人项目推荐部署方案

| 类别 | 推荐方案 | 费用 | 适用场景 |
|------|----------|------|----------|
| 前端 + 全栈 | Docker Compose + Nginx | 自托管 | React/Next.js/Vue |
| 数据库 | PostgreSQL（自托管）/ Neon | 免费额度 | 小型项目 |
| 文件存储 | MinIO（自托管）/ Cloudflare R2 | 自托管优先 | 图片/文件上传 |
| 域名 | Cloudflare / Namecheap | ~$10/年 | 自定义域名 |
| 监控 | Uptime Kuma + Prometheus + Grafana | 免费 | 基础监控 |
| 日志 | Loki + Grafana / ELK | 免费额度 | 错误追踪 |
| 邮件 | Postal / Mailpit（开发） | 自托管 | 事务邮件 |
| 支付 | 按业务需求选择（Stripe/LemonSqueezy） | 按需 | 付费功能 |

> **总成本参考**：个人项目 0~$20/月即可跑起来。

### 上线前 Checklist

- [ ] 环境变量已配置（无硬编码密钥）
- [ ] 数据库迁移已验证
- [ ] 核心流程手动测试通过
- [ ] 错误处理和日志已配置
- [ ] HTTPS 已启用
- [ ] 健康检查端点可用
- [ ] 监控和告警已配置
- [ ] 回滚方案已准备

## 反模式

- ❌ "直接部署到生产" — 跳过 staging 验证风险极高
- ❌ 部署前不备份数据库 — 数据丢失后无法恢复
- ❌ 部署后不验证 — 问题可能在生产环境才发现
- ❌ 使用单一 `.env` 文件管理所有环境 — 配置混乱
- ❌ 手动执行部署步骤 — 容易遗漏或出错，应自动化