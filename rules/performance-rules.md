---
name: performance-rules
version: v1.0.1
type: rule
enabled: true
mode: [standard, creator]
updated: 2026-11-05
description: 性能规则 — 数据库 N+1、缓存策略、分页、前端懒加载与资源管理
applies_to:
  agents: ['architect', 'backend-developer', 'frontend-developer']
  phases: ['design', 'implementation']
  project_types: ['全部']
  tech_stacks: ['全部']
---
# 性能规则 (Performance Rules)

> **适用范围**: 本文包含通用架构原则和 FastAPI+React 项目特定实践。通用原则适用于所有项目，项目特定实践以 `[项目特定]` 标注，具体配置以项目根目录 `tech-stack.md` 为准。

本文件定义项目中必须遵守的性能规范，AI 编码代理编写代码时必须考虑以下性能要点。

## 数据库性能

<!-- [项目特定] -->
- **必须**始终考虑 N+1 查询问题
- 关联数据加载使用 `selectinload` 或 `joinedload`（SQLAlchemy）
- 复杂查询**必须**添加适当的数据库索引
- **禁止**在循环中执行数据库查询，必须使用批量操作
- 使用数据库连接池，合理配置连接数
<!-- [项目特定] -->
- **pgvector 向量索引策略**:
  - 数据量 < 100万：使用 **HNSW** 索引（查询快、召回率高）
  - 数据量 > 100万：使用 **IVFFlat** 索引（内存友好）
  - HNSW 参数：`m=16`, `ef_construction=200`
  - IVFFlat 参数：`lists=sqrt(行数)`
  - 批量导入时先插数据后建索引，速度更快
  - 查询时可调整 `hnsw.ef_search` 提高召回率（默认 40）

## 缓存策略

- 图算法（如中心性计算、路径搜索）**必须**使用 Redis 缓存
- 高频查询结果**必须**缓存，设置合理的 TTL
- 缓存 Key 命名必须有清晰的命名规则
- 缓存更新策略：优先考虑 Cache-Aside 模式

## API 性能

- 列表接口**必须**实现分页（pagination）
- **禁止**返回过大的响应 payload，按需裁剪返回字段
- 使用 Gzip 压缩响应数据
- 耗时操作考虑异步处理（如使用 Background Tasks）

## 前端性能

<!-- [项目特定] -->
- 使用 Code Splitting 拆分代码包
- 重型组件使用 `React.lazy()` + `Suspense` 实现懒加载
- 图片资源使用懒加载
- 避免不必要的 re-render，合理使用 `React.memo()`、`useMemo`、`useCallback`

## 资源管理

- 文件上传和大数据处理使用流式处理
- 长时间运行的任务必须支持超时和取消
- 外部 API 调用必须设置合理的超时时间

---

## 禁止事项

- ❌ 在循环中执行数据库查询（必须批量操作）
- ❌ 复杂查询不添加索引
- ❌ 列表接口不实现分页
- ❌ 返回包含大量冗余字段的巨大 payload
- ❌ 不使用连接池直接创建数据库连接
- ❌ 同步加载所有重型组件（不使用懒加载）
- ❌ 缓存不设置 TTL 导致数据永不过期

---

## 可观测性（Observability）

### 三支柱
- **Trace（链路追踪）**：OpenTelemetry（Apache-2.0，CNCF 毕业）
  - 自动插桩：opentelemetry-instrumentation（Python） + @opentelemetry/api（TS）
  - 后端：Jaeger / Tempo（Apache-2.0）或开源 Zipkin
  - 前端：@opentelemetry/web（浏览器端）
- **Metrics（指标）**：Prometheus（Apache-2.0）+ VictoriaMetrics（Apache-2.0，优先）；Grafana（AGPL-3.0）仅限个人/内部自用且不分发时可选——选它属黑名单例外，须按 `open-source-first.md` §3 写 ADR 豁免，商业分发场景禁用
  - 自动暴露：prometheus_client（Python） + prom-client（TS）
  - 必须指标：REQUEST_DURATION、ERROR_RATE、QUEUE_LENGTH
- **Logs（日志）**：structlog（项目已用）+ Quickwit（Apache-2.0，优先）；Loki（AGPL-3.0）同上仅限内部自用且需 ADR 豁免
  - 必须字段：timestamp、level、message、request_id、service.name

### 强制级别
- 个人项目：建议接入 OpenTelemetry SDK（零配置自动插桩）
- 商业项目：必须完整三支柱，告警规则必备
- 图算法场景（如中心性计算）：必须开启 Trace，否则无法定位跨服务延迟热点

### 资源管理
- **Trace 采样率**：生产环境建议 10%~30%，开发环境 100%
- **Metrics 保留期**：默认 15 天，关键业务可调长
- **日志压缩**：生产环境必须开启 gzip/zstd