# 指标定义与事件设计参考（analytics-design Phase 1-2 配套）

> 本文档按需加载。包含指标金字塔、指标定义表、事件命名规范、事件清单、属性定义与身份识别方案。

## Phase 1: 指标定义

**目标**：确定核心业务指标，建立可量化的衡量体系。

### 核心指标层级

**指标金字塔**:

```text
                  ┌──────────────┐
                  │  北极星指标   │  ← 1 个，衡量产品核心价值
                  └──────┬───────┘
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
   ┌──────────┐   ┌──────────┐   ┌──────────┐
   │ 一级指标  │   │ 一级指标  │   │ 一级指标  │  ← 3-5 个，核心业务维度
   └────┬─────┘   └────┬─────┘   └────┬─────┘
   ┌────┼────┐    ┌────┼────┐    ┌────┼────┐
   ▼    ▼    ▼    ▼    ▼    ▼    ▼    ▼    ▼
 二级  二级  二级  ...                    ← 每项 3-5 个，可执行指标
```

**指标定义表**（示例，按项目实际调整）:

| 层级 | 指标名称 | 计算公式 | 数据来源 | 目标值 | 采集频率 |
|------|----------|----------|----------|--------|----------|
| 北极星 | 日活跃用户数 (DAU) | `COUNT(DISTINCT user_id) WHERE active_date = today` | 登录事件 + 核心操作事件 | 月环比 +10% | 每日 |
| 一级 | 新用户注册数 | `COUNT(DISTINCT user_id) WHERE event = 'register'` | 注册事件 | 月环比 +5% | 每日 |
| 一级 | 用户留存率 (D7) | `注册第7天仍活跃用户数 / 注册用户数` | 注册事件 + 活跃事件 | > 30% | 每日 |
| 一级 | 核心功能转化率 | `完成核心操作用户数 / 进入功能用户数` | 页面浏览 + 操作事件 | > 40% | 每日 |
| 一级 | 人均使用时长 | `SUM(session_duration) / COUNT(DISTINCT user_id)` | 会话事件 | > 15 分钟 | 每日 |
| 二级 | 注册转化率 | `注册成功数 / 注册页面访问数` | 页面浏览 + 注册事件 | > 60% | 每日 |
| 二级 | 功能 A 使用率 | `使用功能A用户数 / DAU` | 功能A操作事件 | > 20% | 每周 |
| 二级 | 页面平均加载时间 | `AVG(page_load_time)` | 性能事件 | < 2s | 每日 |
| 二级 | 错误率 | `错误事件数 / 总事件数` | 错误事件 | < 0.5% | 实时 |

> **北极星指标选择原则**：必须是能衡量产品核心价值的单一指标，反映用户是否真正获得了产品价值。避免选择"注册用户数"等虚荣指标。

### 指标计算公式规范化

每个指标必须包含完整的计算公式和数据来源：

```yaml
指标定义示例:
  - name: "用户留存率 (D7)"
    description: "新用户注册后第7天仍活跃的比例"
    formula: |
      D7留存率 = COUNT(用户在注册后第7天有活跃事件) / COUNT(注册用户)
      WHERE 注册日期 = target_date - 7
    data_sources:
      - event: "user.registered"
      - event: "user.active"
    dimensions:
      - 注册渠道 (channel)
      - 用户地域 (region)
      - 设备类型 (device_type)
    target: "> 30%"
    alert_threshold: "< 25% 触发告警"
    review_frequency: "每日"
```

## Phase 2: 事件设计

**目标**：定义统一的事件命名规范、属性结构和用户标识方案。

### 事件命名规范

**命名格式**: `{模块}.{操作}_{状态}`

| 命名部分 | 说明 | 示例 |
|----------|------|------|
| 模块 | 功能模块，使用小写 + 点号分隔 | `auth`、`project`、`payment` |
| 操作 | 动作，使用过去式动词 | `viewed`、`clicked`、`submitted` |
| 状态 | 结果状态（可选） | `success`、`failure`、`cancelled` |

**完整事件清单**（示例基线，按项目增删）:

| 事件名 | 分类 | 说明 | 触发时机 | 优先级 |
|--------|------|------|----------|--------|
| `page.viewed` | 页面浏览 | 页面加载完成 | 页面 onMount | P0 |
| `page.left` | 页面浏览 | 用户离开页面 | 页面 onUnmount | P1 |
| `auth.login.clicked` | 认证 | 点击登录按钮 | 按钮 onClick | P0 |
| `auth.login.success` | 认证 | 登录成功 | API 返回 200 | P0 |
| `auth.login.failure` | 认证 | 登录失败 | API 返回 4xx/5xx | P0 |
| `auth.register.started` | 认证 | 开始注册流程 | 进入注册页 | P1 |
| `auth.register.completed` | 认证 | 注册成功 | API 返回 201 | P0 |
| `auth.register.abandoned` | 认证 | 放弃注册 | 离开注册页未完成 | P1 |
| `project.created` | 项目 | 创建项目成功 | API 返回 201 | P0 |
| `project.viewed` | 项目 | 查看项目详情 | 进入详情页 | P1 |
| `project.deleted` | 项目 | 删除项目 | 确认删除后 | P1 |
| `search.performed` | 搜索 | 执行搜索 | 提交搜索 | P1 |
| `search.result.clicked` | 搜索 | 点击搜索结果 | 点击结果项 | P2 |
| `error.client` | 错误 | 客户端错误 | ErrorBoundary 捕获 | P0 |
| `error.api` | 错误 | API 调用失败 | API 返回非 2xx | P0 |
| `performance.page_load` | 性能 | 页面加载耗时 | 页面加载完成 | P1 |

### 事件属性定义

**通用属性**（所有事件必须携带）:

| 属性名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|
| `event_id` | string | 是 | 事件唯一标识 | `uuid` |
| `event_name` | string | 是 | 事件名称 | `auth.login.success` |
| `timestamp` | timestamp | 是 | 事件发生时间（UTC） | `2026-07-24T08:30:00Z` |
| `session_id` | string | 是 | 会话 ID | `uuid` |
| `user_id` | string | 否 | 用户 ID（未登录为空） | `user_123` |
| `anonymous_id` | string | 是 | 匿名用户 ID（设备指纹） | `anon_abc` |
| `platform` | string | 是 | 平台 | `web` / `ios` / `android` |
| `app_version` | string | 是 | 应用版本号 | `2.1.0` |
| `page_url` | string | 是 | 当前页面 URL | `/projects/123` |
| `referrer` | string | 否 | 来源页面 URL | `/dashboard` |

**页面浏览事件属性**:

| 属性名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `page_title` | string | 是 | 页面标题 |
| `page_category` | string | 否 | 页面分类（如 `project`、`settings`） |
| `load_time_ms` | number | 否 | 页面加载耗时（毫秒） |

**点击事件属性**:

| 属性名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `element_id` | string | 是 | 元素唯一标识 |
| `element_type` | string | 是 | 元素类型（`button`、`link`、`input`） |
| `element_text` | string | 否 | 元素显示文本 |
| `element_position` | string | 否 | 元素位置（`header`、`sidebar`、`content`） |

**错误事件属性**:

| 属性名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `error_type` | string | 是 | 错误类型（`network`、`validation`、`server`） |
| `error_message` | string | 是 | 错误信息（脱敏后） |
| `error_stack` | string | 否 | 错误堆栈（脱敏后） |
| `api_endpoint` | string | 否 | 失败的 API 端点 |

### 用户属性与身份识别

**用户属性**（在识别用户时设置）:

| 属性名 | 类型 | 说明 | 示例 |
|--------|------|------|------|
| `user_id` | string | 注册用户唯一 ID | `user_123` |
| `anonymous_id` | string | 匿名用户 ID（设备级） | `anon_abc` |
| `email` | string | 邮箱（脱敏） | `u***@example.com` |
| `registration_date` | date | 注册日期 | `2026-07-01` |
| `plan_type` | string | 套餐类型 | `free` / `pro` / `enterprise` |
| `user_role` | string | 用户角色 | `admin` / `member` / `viewer` |

**身份合并策略**:

```text
匿名用户 (anonymous_id) → 注册 → 识别用户 (user_id)
                                  ↓
                          anonymous_id 与 user_id 建立别名映射
                                  ↓
                          历史匿名事件关联到注册用户
```

**会话定义**:

| 参数 | 值 | 说明 |
|------|-----|------|
| 会话超时 | 30 分钟 | 无操作 30 分钟后会话结束 |
| 会话标识 | `session_id` (UUID) | 每次页面打开时生成 |
| 跨日处理 | 午夜 00:00 强制结束会话 | 避免跨天数据混淆 |
