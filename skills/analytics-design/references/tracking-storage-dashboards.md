# 埋点方案、数据存储与看板参考（analytics-design Phase 3-6 配套）

> 本文档按需加载。包含页面埋点矩阵、实现规范、SDK 选择、事件表结构、聚合策略、合规要求与看板设计。

## Phase 3: 埋点方案

**目标**：为每个页面和关键交互确定具体的埋点实现方案。

### 页面埋点矩阵（示例基线，基于 ui-design 页面清单逐页定义）

| 页面 | 路由 | 埋点事件 | 触发时机 | 属性 | 优先级 |
|------|------|----------|----------|------|--------|
| 首页 | `/` | `page.viewed` | 页面加载 | page_title, load_time_ms | P0 |
| 首页 | `/` | `page.left` | 页面离开 | duration_ms | P1 |
| 登录页 | `/login` | `page.viewed` | 页面加载 | referrer | P0 |
| 登录页 | `/login` | `auth.login.clicked` | 点击登录 | — | P0 |
| 登录页 | `/login` | `auth.login.success` | 登录成功 | user_id | P0 |
| 登录页 | `/login` | `auth.login.failure` | 登录失败 | error_message | P0 |
| 注册页 | `/register` | `page.viewed` | 页面加载 | referrer | P0 |
| 注册页 | `/register` | `auth.register.started` | 开始填写 | — | P1 |
| 注册页 | `/register` | `auth.register.completed` | 注册成功 | user_id | P0 |
| 注册页 | `/register` | `auth.register.abandoned` | 未完成离开 | step_reached | P1 |
| 仪表盘 | `/dashboard` | `page.viewed` | 页面加载 | load_time_ms | P0 |
| 项目列表 | `/projects` | `page.viewed` | 页面加载 | — | P0 |
| 项目列表 | `/projects` | `project.created` | 创建成功 | project_id | P0 |
| 项目列表 | `/projects` | `search.performed` | 搜索 | query_length | P1 |
| 项目详情 | `/projects/:id` | `page.viewed` | 页面加载 | project_id | P0 |
| 项目详情 | `/projects/:id` | `project.deleted` | 删除确认 | project_id | P1 |
| 设置页 | `/settings` | `page.viewed` | 页面加载 | — | P1 |
| 全局 | `*` | `error.client` | 客户端错误 | error_type, error_message | P0 |
| 全局 | `*` | `error.api` | API 错误 | api_endpoint, status_code | P0 |
| 全局 | `*` | `performance.page_load` | 加载完成 | load_time_ms, resource_count | P1 |

### 埋点实现规范

```typescript
// 推荐：封装统一的 track 函数
import { track } from '@/lib/analytics';

// 页面浏览埋点 — 在页面组件 onMount 中调用
useEffect(() => {
  track('page.viewed', {
    page_title: '项目列表',
    page_category: 'project',
    load_time_ms: performance.now(),
  });

  return () => {
    track('page.left', {
      page_title: '项目列表',
      duration_ms: Date.now() - entryTime,
    });
  };
}, []);

// 点击事件埋点 — 在事件处理函数中调用
const handleLogin = async () => {
  track('auth.login.clicked');

  try {
    const result = await loginAPI(credentials);
    track('auth.login.success', { user_id: result.userId });
  } catch (error) {
    track('auth.login.failure', {
      error_type: 'api',
      error_message: error.message,
    });
  }
};

// 表单步骤埋点 — 在关键步骤完成时调用
const handleStepComplete = (step: number) => {
  track('auth.register.step_completed', {
    step_number: step,
    step_name: stepNames[step],
  });
};
```

### 埋点 SDK 选择

| SDK | 适用场景 | 优点 | 缺点 |
|-----|----------|------|------|
| 自建埋点 | 对数据安全要求高 | 完全可控、无第三方依赖 | 需自行维护 |
| PostHog | 中小团队 | 开源、自托管、功能全面 | 大规模数据需付费 |
| Mixpanel | 产品分析 | 分析能力强、漏斗直观 | 价格较高 |
| Amplitude | 中大型产品 | 强大的行为分析、实验平台 | 学习曲线 |
| Google Analytics 4 | 全场景 | 免费、生态完善 | 数据隐私顾虑 |

### 数据上报策略

| 策略 | 说明 | 适用场景 |
|------|------|----------|
| 实时上报 | 事件发生后立即发送 | P0 事件（登录、注册、错误） |
| 批量上报 | 每 10 条或每 30 秒批量发送 | P1/P2 事件 |
| 离线缓存 | 网络不可用时缓存到 localStorage | 所有事件 |
| 采样上报 | 高频事件按比例采样 | 性能事件、滚动事件 |

## Phase 4: 数据存储设计

**目标**：定义事件数据存储结构、聚合策略和合规要求。

### 事件表结构

**原始事件表**（`analytics_events`）:

```sql
CREATE TABLE analytics_events (
    id              BIGSERIAL PRIMARY KEY,
    event_id        UUID NOT NULL UNIQUE,          -- 事件唯一标识
    event_name      VARCHAR(128) NOT NULL,          -- 事件名称
    timestamp       TIMESTAMPTZ NOT NULL DEFAULT NOW(),  -- 事件时间 UTC
    session_id      UUID NOT NULL,                 -- 会话 ID
    user_id         VARCHAR(64),                   -- 用户 ID（可为空）
    anonymous_id    VARCHAR(128) NOT NULL,          -- 匿名用户 ID
    platform        VARCHAR(16) NOT NULL DEFAULT 'web',  -- 平台
    app_version     VARCHAR(32) NOT NULL,          -- 应用版本
    page_url        VARCHAR(2048) NOT NULL,        -- 页面 URL
    referrer        VARCHAR(2048),                 -- 来源页面
    properties      JSONB NOT NULL DEFAULT '{}',   -- 事件属性
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 索引
CREATE INDEX idx_events_name_ts ON analytics_events(event_name, timestamp DESC);
CREATE INDEX idx_events_user_id ON analytics_events(user_id) WHERE user_id IS NOT NULL;
CREATE INDEX idx_events_session ON analytics_events(session_id);
CREATE INDEX idx_events_timestamp ON analytics_events(timestamp DESC);
CREATE INDEX idx_events_properties ON analytics_events USING GIN(properties);
```

**用户属性表**（`analytics_users`）:

```sql
CREATE TABLE analytics_users (
    user_id         VARCHAR(64) PRIMARY KEY,
    anonymous_id    VARCHAR(128) NOT NULL,          -- 关联匿名 ID
    traits          JSONB NOT NULL DEFAULT '{}',    -- 用户属性
    first_seen_at   TIMESTAMPTZ NOT NULL,           -- 首次出现
    last_seen_at    TIMESTAMPTZ NOT NULL,           -- 最近出现
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_anonymous ON analytics_users(anonymous_id);
```

### 聚合策略

**预聚合表**（提升查询性能）:

| 聚合表 | 粒度 | 聚合维度 | 刷新频率 | 保留期 |
|--------|------|----------|----------|--------|
| `daily_metrics` | 按天 | `event_name` + `platform` + `app_version` | 每小时 | 2 年 |
| `hourly_metrics` | 按小时 | `event_name` + `page_url` | 每 15 分钟 | 90 天 |
| `user_daily_summary` | 按天/用户 | `user_id` + 活跃状态 + 事件数 | 每小时 | 1 年 |
| `funnel_metrics` | 按天 | `funnel_name` + `step` | 每小时 | 1 年 |

**聚合 SQL 示例**（每日指标）:

```sql
INSERT INTO daily_metrics (date, event_name, platform, app_version, event_count, unique_users)
SELECT
    DATE(timestamp) AS date,
    event_name,
    properties->>'platform' AS platform,
    app_version,
    COUNT(*) AS event_count,
    COUNT(DISTINCT COALESCE(user_id, anonymous_id)) AS unique_users
FROM analytics_events
WHERE DATE(timestamp) = CURRENT_DATE - INTERVAL '1 day'
GROUP BY DATE(timestamp), event_name, properties->>'platform', app_version
ON CONFLICT (date, event_name, platform, app_version) DO UPDATE
SET event_count = EXCLUDED.event_count,
    unique_users = EXCLUDED.unique_users;
```

### 数据保留与合规

**数据保留策略**:

| 数据类型 | 保留期 | 归档策略 | 说明 |
|----------|--------|----------|------|
| 原始事件 | 90 天 | 聚合后删除 | 仅保留用于调试和回放 |
| 聚合指标 | 2 年 | 按年归档 | 长期趋势分析 |
| 用户属性 | 账号存续期间 | 账号删除后 30 天清理 | 合规要求 |
| 会话记录 | 30 天 | 聚合后删除 | 仅用于会话分析 |

**合规要求（GDPR / 个保法 / CCPA）**:

| 要求 | 实现方式 | 验证方式 |
|------|----------|----------|
| 用户知情同意 | 首次访问时展示 Cookie/隐私弹窗 | 检查 consent 字段 |
| 数据最小化 | 仅采集必要字段，禁止采集敏感信息 | 代码审查 |
| 用户删除权 | 提供数据删除 API，30 天内完成 | 自动化测试 |
| 数据导出权 | 提供用户数据导出 API | 自动化测试 |
| 数据加密 | 传输层 TLS 1.3，存储层 AES-256 | 安全扫描 |
| 数据脱敏 | 上报前脱敏邮箱、手机号、IP | 代码审查 |
| 数据不出境 | 中国用户数据存储在中国境内服务器 | 部署架构审查 |

**隐私合规埋点检查**:

```typescript
// 禁止上报的敏感信息
const PII_FIELDS = [
  'password',
  'password_hash',
  'credit_card',
  'ssn',
  'id_card',
  'phone',        // 完整手机号
  'email',        // 完整邮箱
  'ip_address',   // 完整 IP
  'full_name',    // 完整姓名
];

// 脱敏函数
const sanitizeProperties = (props: Record<string, unknown>): Record<string, unknown> => {
  const sanitized = { ...props };
  for (const key of Object.keys(sanitized)) {
    if (PII_FIELDS.some(field => key.toLowerCase().includes(field))) {
      delete sanitized[key];
    }
  }
  return sanitized;
};
```

## Phase 5: 报表与看板设计

**目标**：设计核心数据看板，确保数据可观测、可分析。

### 核心看板布局

| 看板名称 | 目标用户 | 更新频率 | 核心指标 |
|----------|----------|----------|----------|
| 实时大屏 | 全员 | 实时（5 秒） | DAU、在线用户数、今日事件数 |
| 产品概览 | 产品经理 | 每日 | DAU/MAU、留存率、核心转化率 |
| 增长看板 | 运营/增长 | 每日 | 新增用户、渠道来源、注册转化漏斗 |
| 功能看板 | 产品经理 | 每周 | 功能使用率、功能留存、用户路径 |
| 技术看板 | 开发团队 | 实时 | 错误率、API 响应时间、页面加载时间 |
| 收入看板 | 管理层 | 每日 | ARPU、付费转化率、MRR |

**统计周期**:

| 周期 | 缩写 | 说明 | 对比基准 |
|------|------|------|----------|
| 今日 | Today | 当日 00:00 至今 | 昨日同时段 |
| 昨日 | Yesterday | 昨日全天 | 前日 |
| 最近 7 天 | L7D | 过去 7 天（不含今日） | 上周期 |
| 最近 30 天 | L30D | 过去 30 天（不含今日） | 上周期 |
| 本周 | WTD | 本周一 00:00 至今 | 上周同时段 |
| 本月 | MTD | 本月 1 日 00:00 至今 | 上月同时段 |

### 报表类型

**转化漏斗**:

```text
注册转化漏斗:
  访问注册页    100%  ████████████████████  1000 人
  开始填写表单   80%  ████████████████       800 人
  提交表单      60%  ████████████           600 人
  邮箱验证      45%  █████████              450 人
  注册成功      40%  ████████               400 人
                                    ↓
                          整体转化率: 40%
                          流失最大环节: 邮箱验证（流失 150 人）
```

**用户留存矩阵**:

| 注册日期 | D0 用户数 | D1 | D3 | D7 | D14 | D30 |
|----------|-----------|-----|-----|-----|------|------|
| 2026-07-01 | 100 | 60% | 45% | 35% | 28% | 20% |
| 2026-07-08 | 120 | 65% | 50% | 40% | — | — |
| 2026-07-15 | 90 | 55% | 42% | — | — | — |

**用户路径桑基图**:

```text
首页 → 项目列表 → 项目详情 → 任务编辑
  │        │          │
  └→ 注册   └→ 搜索    └→ 删除项目
                │
                └→ 项目详情
```

### 数据导出格式

| 导出类型 | 格式 | 触发方式 | 说明 |
|----------|------|----------|------|
| 看板截图 | PNG | 手动 | 用于周报/汇报 |
| 原始数据 | CSV | 手动 | 最多导出 10 万条 |
| 定时报表 | PDF/Email | 自动（每周一 9:00） | 上周数据摘要 |
| API 访问 | JSON | 程序调用 | 通过 API Key 认证 |

## Phase 6: 输出 analytics-design.md

文件保存到 `docs/analytics-design.md`，章节结构：

```markdown
# 数据分析设计: [项目名称]

## 1. 指标定义
### 1.1 北极星指标
### 1.2 一级指标（核心业务维度）
### 1.3 二级指标（可执行指标）
### 1.4 指标计算公式汇总

## 2. 事件设计
### 2.1 事件命名规范
### 2.2 事件清单（完整列表）
### 2.3 通用属性定义
### 2.4 事件级属性定义
### 2.5 用户属性与身份识别
### 2.6 会话定义

## 3. 埋点方案
### 3.1 页面埋点矩阵
### 3.2 埋点 SDK 选择
### 3.3 数据上报策略
### 3.4 埋点实现规范

## 4. 数据存储设计
### 4.1 原始事件表结构
### 4.2 用户属性表结构
### 4.3 聚合策略与预聚合表
### 4.4 数据保留策略
### 4.5 合规要求（GDPR/个保法/CCPA）

## 5. 报表与看板设计
### 5.1 核心看板布局
### 5.2 报表类型（漏斗/留存/路径/热力图）
### 5.3 数据刷新频率
### 5.4 数据导出格式

## 6. A/B 测试框架（可选）
```
