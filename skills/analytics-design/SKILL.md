---
name: analytics-design
version: v1.1.0
type: skill
enabled: true
mode: [standard, creator]
description: "在 ui-design 完成后、编码前进行数据埋点与分析设计 — 指标体系、事件埋点方案、数据存储、报表看板、A/B 测试。触发词: 埋点、数据分析、用户行为、转化率、A/B测试、指标、报表、事件追踪、analytics、tracking。"
updated: 2026-09-11
depends_on: [system-design]
composes: [writing-plans]
---

# Analytics Design

## 负责代理

`architect` — 数据埋点与分析设计由架构师代理负责，确保埋点方案与业务目标对齐。

## 何时使用

- 需要定义**核心业务指标（KPI）**和**北极星指标**时
- 需要设计**用户行为埋点方案**（页面浏览、点击、表单提交、错误）时
- 需要规划**数据报表与看板**布局时
- 需要搭建**A/B 测试框架**和实验设计时
- 需要定义**数据存储策略**（事件表结构、聚合、保留策略）时
- 需要确保**数据合规**（GDPR、个保法、CCPA）时
- `ui-design` 完成后，需要为每个页面确定埋点位置时

**触发关键词**: "埋点"、"数据分析"、"用户行为"、"转化率"、"A/B测试"、"指标"、"报表"、"事件追踪"、"analytics"、"tracking"

## 与其他技能的关系

```text
brainstorming → system-design
          ↓           ↓
       ui-design   api-design
          ↓           ↓
   analytics-design ←─┘（数据上报接口）
          ↓
   frontend-component（编码时添加埋点）
          ↓
   ops-monitoring（数据看板持续监控）
```

> **衔接规则**:
> - `analytics-design` 依赖 `ui-design` 的页面设计 — 通过页面清单和组件清单确定埋点位置
> - `analytics-design` 与 `api-design` **并行执行** — 数据上报接口（如 `POST /analytics/events`）需要在 API 设计中定义
> - `frontend-component` 编码时在每个组件中按 `analytics-design` 的埋点方案添加追踪代码
> - `ops-monitoring` 阶段基于 `analytics-design` 的看板设计建立持续监控
> - 埋点方案不影响核心业务逻辑，但每个 P0 功能必须有对应的埋点覆盖

## 执行流程（骨架）

> 各 Phase 的详细模板、表格与代码见文末参考文档，按需加载。

### Phase 1: 指标定义

确定核心业务指标，建立可量化的衡量体系：

- 构建**指标金字塔**：北极星指标（1 个）→ 一级指标（3-5 个）→ 二级指标（每项 3-5 个）
- 北极星必须是衡量产品核心价值的单一指标，禁止虚荣指标
- 每个指标必须有：计算公式、数据来源、目标值、告警阈值、采集频率

详细模板（金字塔图、指标定义表、公式 YAML）→ [references/metrics-events.md](references/metrics-events.md) Phase 1。

### Phase 2: 事件设计

定义统一的事件命名规范、属性结构和用户标识方案：

- 命名格式 `{模块}.{操作}_{状态}`（如 `auth.login.success`）
- 定义完整事件清单（P0/P1/P2 分级）+ 通用属性 + 事件级属性
- 用户属性与身份识别：anonymous_id → user_id 别名合并；会话定义（30 分钟超时、跨日强制结束）

详细模板（事件清单基线、属性表、身份合并）→ [references/metrics-events.md](references/metrics-events.md) Phase 2。

### Phase 3: 埋点方案

基于 `ui-design` 页面清单，为每个页面定义埋点矩阵：

- 页面 × 事件 × 触发时机 × 属性 × 优先级
- 封装统一 `track()` 函数；SDK 选型（自建/PostHog/Mixpanel/Amplitude/GA4）
- 上报策略分级：P0 实时、P1/P2 批量、离线缓存、高频采样

详细模板 → [references/tracking-storage-dashboards.md](references/tracking-storage-dashboards.md) Phase 3。

### Phase 4: 数据存储设计

- 原始事件表 + 用户属性表（JSONB properties + GIN 索引）
- 预聚合表（daily/hourly/user_daily/funnel），避免实时查询原始表
- 数据保留策略 + 合规要求（GDPR/个保法/CCPA：知情同意、删除权、导出权、脱敏、不出境）

表结构与合规清单 → [references/tracking-storage-dashboards.md](references/tracking-storage-dashboards.md) Phase 4。

### Phase 5: 报表与看板设计

- 看板分类（实时大屏/产品概览/增长/功能/技术/收入）+ 统计周期定义
- 报表类型：转化漏斗、留存矩阵、用户路径桑基图
- 数据导出格式（PNG/CSV/定时 PDF/API）

详细模板 → [references/tracking-storage-dashboards.md](references/tracking-storage-dashboards.md) Phase 5。

### Phase 6: 输出 analytics-design.md

保存到 `docs/analytics-design.md`，章节结构模板 → [references/tracking-storage-dashboards.md](references/tracking-storage-dashboards.md) Phase 6。

## 参考文档（一层深，按需加载）

| 文档 | 内容 | 何时读 |
|------|------|--------|
| [references/metrics-events.md](references/metrics-events.md) | 指标金字塔、指标定义表、事件命名/清单/属性、身份识别 | 执行 Phase 1-2 时 |
| [references/tracking-storage-dashboards.md](references/tracking-storage-dashboards.md) | 埋点矩阵、实现规范、SDK、表结构、聚合、合规、看板 | 执行 Phase 3-6 时 |

## 分析检查清单

**指标定义**:
- [ ] 北极星指标已确定，非虚荣指标
- [ ] 所有指标有明确的计算公式
- [ ] 所有指标有数据来源标注
- [ ] 指标有目标值和告警阈值

**事件设计**:
- [ ] 事件命名遵循 `{模块}.{操作}_{状态}` 规范
- [ ] 通用属性（event_id、timestamp、session_id 等）已定义
- [ ] 用户属性与匿名用户标识方案已确定
- [ ] 会话定义明确（超时时间、跨日处理）

**埋点方案**:
- [ ] 所有 P0 页面有埋点覆盖
- [ ] 所有关键操作（登录、注册、核心功能）有埋点
- [ ] 所有错误场景有埋点
- [ ] 埋点代码审查通过（无敏感信息上报）

**数据存储**:
- [ ] 事件表结构设计完成，索引合理
- [ ] 聚合策略已定义，避免实时查询原始表
- [ ] 数据保留策略明确（原始数据、聚合数据、用户数据）
- [ ] 合规检查通过（GDPR/个保法/CCPA）

**报表看板**:
- [ ] 核心看板布局已设计
- [ ] 转化漏斗、留存矩阵、用户路径图已规划
- [ ] 数据刷新频率合理
- [ ] 导出格式已定义

## 硬性规则

- **埋点事件必须有统一命名规范** — 所有事件名遵循 `{模块}.{操作}_{状态}` 格式，不可随意命名
- **所有 P0 功能必须有埋点覆盖** — 北极星指标相关的事件、核心业务流程、登录注册、错误场景必须 100% 埋点
- **用户隐私数据不得上报** — 密码、完整手机号、完整邮箱、身份证号、信用卡号等严禁出现在埋点数据中
- **必须遵守 GDPR/个保法/CCPA** — 用户知情同意、数据删除权、数据导出权、数据不出境等合规要求必须满足
- **指标定义必须有计算公式** — 每个指标必须包含完整的计算公式、数据来源和维度，不可模糊描述
- **事件必须携带通用属性** — 所有事件必须包含 event_id、timestamp、session_id、platform、app_version
- **敏感信息上报前必须脱敏** — 邮箱脱敏为 `u***@example.com`，手机号脱敏为 `138****1234`
- **原始事件表必须设置合理的保留期** — 默认 90 天，超过保留期自动归档或删除
- **不允许只设埋点不设看板** — 每个埋点事件必须有对应的看板或报表消费
- **指标定义前后必须一致** — 同一指标在埋点、聚合、看板中的定义不能有差异

## 反模式

- **上报用户密码等敏感信息** — 密码、Token、身份证号等敏感信息绝对禁止出现在埋点数据中
- **全量埋点不加筛选** — 每个页面每个点击都埋点，数据量大且无分析价值，应按优先级筛选
- **只设埋点不设看板** — 埋点数据上报后无人消费，浪费存储和带宽
- **指标定义前后不一致** — 埋点中的"注册成功"定义与看板中的"注册成功"定义不同，导致数据对不上
- **使用虚荣指标当北极星** — "注册用户总数"、"页面浏览量"等无法衡量产品核心价值的指标
- **不设会话机制** — 无法计算用户行为路径、会话时长、页面跳转关系
- **硬编码埋点事件名** — 事件名字符串散落在代码各处，不统一管理，导致命名不一致
- **忽略错误埋点** — 只埋点成功路径，不埋点失败路径，无法分析用户流失原因
- **不设数据保留策略** — 原始事件无限期存储，数据库膨胀，查询性能下降
- **跨平台事件名不一致** — Web 端用 `login_success`，移动端用 `user.login.completed`，导致数据分析时无法对齐
