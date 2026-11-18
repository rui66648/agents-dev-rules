# 时区、货币与 UI 适配参考（i18n-design Phase 3-6 配套）

> 本文档按需加载。包含时区存储、日期格式化、多货币、数字度量、RTL 布局、文字溢出、字体选择与输出文档结构。

## Phase 3: 时区与日期设计

**目标**：定义时区存储策略、日期格式化规范和转换规则。

### 时区存储策略

**核心原则**：所有日期时间统一以 **UTC** 存储，展示时按用户时区转换。

| 存储层 | 策略 | 说明 |
|--------|------|------|
| 数据库 | UTC (TIMESTAMP WITH TIME ZONE) | 所有 `created_at`、`updated_at` 统一 UTC |
| API 响应 | UTC (ISO 8601 格式) | `2026-07-24T10:00:00Z` |
| 前端展示 | 用户本地时区 | 根据 `Intl.DateTimeFormat` 自动转换 |

**时区获取优先级**:

```text
1. 用户设置中的时区偏好  →  DB 中存储的 timezone 字段
2. 浏览器时区            →  Intl.DateTimeFormat().resolvedOptions().timeZone
3. 服务端默认时区        →  Asia/Shanghai（兜底）
```

### 日期时间格式化

| 场景 | 格式 | 示例（zh-CN） | 示例（en-US） |
|------|------|---------------|---------------|
| 完整日期时间 | `YYYY年M月D日 HH:mm` | 2026年7月24日 16:30 | Jul 24, 2026, 4:30 PM |
| 短日期 | `YYYY-MM-DD` | 2026-07-24 | 07/24/2026 |
| 相对时间 | 刚刚 / 5分钟前 / 昨天 | 3小时前 | 3 hours ago |
| 日期范围 | `M月D日 - M月D日` | 7月20日 - 7月24日 | Jul 20 - Jul 24 |
| 仅时间 | `HH:mm` | 16:30 | 4:30 PM |

**前端实现**（使用 `Intl` API）:

```typescript
// 推荐：使用浏览器原生 Intl API，无需额外库
const formatDate = (date: string, locale: string): string => {
  return new Intl.DateTimeFormat(locale, {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    timeZone: getUserTimezone(),
  }).format(new Date(date));
};

// 相对时间推荐使用 dayjs + relativeTime 插件
const relativeTime = dayjs(date).locale(locale).fromNow();
```

## Phase 4: 货币与数字格式

**目标**：定义多货币、数字格式化、度量单位的处理方案。

### 货币格式

| 货币代码 | 符号 | 区域 | 格式示例 | 小数位数 |
|----------|------|------|----------|----------|
| CNY | ￥ | zh-CN | ￥1,234.56 | 2 |
| USD | $ | en-US | $1,234.56 | 2 |
| JPY | ￥ | ja-JP | ￥1,235 | 0 |
| KRW | ₩ | ko-KR | ₩1,235 | 0 |
| EUR | € | es-ES/fr-FR | 1.234,56 € | 2 |

**核心规则**:
- 所有货币金额存储时以**最小单位**（分/厘）存储为整数，避免浮点精度问题
- API 返回时标注 ISO 4217 货币代码（`currency: "CNY"`）
- 前端根据 `locale` 使用 `Intl.NumberFormat` 格式化

**存储与展示**:

```typescript
// 数据库存储: 金额以分为单位存储为整数
// price_in_cents: 123456  → 表示 1,234.56 元

// API 响应格式
{
  "price": 1234.56,
  "currency": "CNY",
  "priceInCents": 123456
}

// 前端格式化
const formatCurrency = (amount: number, currency: string, locale: string) => {
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency,
  }).format(amount);
};
```

### 数字与度量格式

**数字格式化**:

| 场景 | 格式说明 | 示例（zh-CN） | 示例（en-US） |
|------|----------|---------------|---------------|
| 千分位分隔 | 数字分组 | 1,234,567 | 1,234,567 |
| 百分比 | 含百分号 | 85.5% | 85.5% |
| 文件大小 | 自动单位 | 1.5 MB | 1.5 MB |
| 大数缩写 | 万/亿 | 1.2万 | 12K |

**度量单位**:

| 度量类型 | 公制（zh-CN） | 英制（en-US） | 策略 |
|----------|---------------|---------------|------|
| 长度 | 厘米/米/公里 | 英寸/英尺/英里 | 按区域显示 |
| 重量 | 克/千克 | 盎司/磅 | 按区域显示 |
| 温度 | 摄氏度 | 华氏度 | 按区域显示 |
| 面积 | 平方米 | 平方英尺 | 按区域显示 |

**排序规则**（Collation）:

| 语言 | 排序规则 | 说明 |
|------|----------|------|
| zh-CN | 拼音排序 | 按拼音首字母排序 |
| en-US | 字母排序 | 按 A-Z 排序 |
| ja-JP | 五十音排序 | 按五十音图排序 |
| ko-KR | 韩文排序 | 按韩文字母排序 |

## Phase 5: UI 适配设计

**目标**：处理 RTL 布局、文字溢出、动态内容长度适配和字体选择。

### RTL 布局支持

**核心原则**：使用 CSS 逻辑属性，避免硬编码 `left`/`right`。

**CSS 逻辑属性对照表**:

| 物理属性（禁止） | 逻辑属性（推荐） | 说明 |
|------------------|------------------|------|
| `margin-left` | `margin-inline-start` | 行内起始边距 |
| `margin-right` | `margin-inline-end` | 行内结束边距 |
| `padding-left` | `padding-inline-start` | 行内起始内边距 |
| `padding-right` | `padding-inline-end` | 行内结束内边距 |
| `text-align: left` | `text-align: start` | 文本对齐 |
| `left` | `inset-inline-start` | 绝对定位 |
| `right` | `inset-inline-end` | 绝对定位 |
| `border-left` | `border-inline-start` | 边框 |
| `border-right` | `border-inline-end` | 边框 |

**Tailwind CSS RTL 方案**:

```html
<!-- 使用 logical 工具类（Tailwind v3.3+） -->
<div class="ps-4 pe-2">  <!-- 替代 pl-4 pr-2 -->
<div class="ms-auto">     <!-- 替代 ml-auto -->
<div class="text-start">  <!-- 替代 text-left -->
<div class="rounded-s-lg rounded-e-none">  <!-- 替代 rounded-l-lg rounded-r-none -->
```

**RTL 特有处理**:

| 场景 | LTR 行为 | RTL 行为 |
|------|----------|----------|
| 箭头图标 | → | ←（镜像翻转） |
| 时间轴 | 从左到右 | 从右到左 |
| 步骤条 | 1 → 2 → 3 | 1 → 2 → 3（顺序不变，但布局镜像） |
| 输入框 | 文本左对齐 | 文本右对齐 |
| 面包屑 | 首页 > 分类 > 详情 | 详情 < 分类 < 首页 |

**RTL 检测与切换**:

```typescript
// 根据语言自动设置 dir 属性
const isRTL = (locale: string): boolean => {
  return ['ar-SA', 'he-IL', 'fa-IR'].includes(locale);
};

// 在 <html> 标签上设置
document.documentElement.dir = isRTL(locale) ? 'rtl' : 'ltr';
document.documentElement.lang = locale;
```

### 文字溢出处理

**各语言文本膨胀率**:

| 源语言 | 目标语言 | 典型膨胀率 | 处理策略 |
|--------|----------|-----------|----------|
| 中文 | 英语 | 150% | 预留 1.5 倍宽度 |
| 中文 | 日语 | 110% | 预留 1.2 倍宽度 |
| 中文 | 韩语 | 120% | 预留 1.3 倍宽度 |
| 中文 | 德语 | 180% | 预留 2 倍宽度 |
| 中文 | 阿拉伯语 | 130% | 预留 1.5 倍宽度 |

**溢出处理策略**:

| 场景 | 策略 | CSS 实现 |
|------|------|----------|
| 按钮文字 | 允许换行，设置 min-width | `min-width: 80px; white-space: normal;` |
| 表格列头 | 省略号 + Tooltip | `text-overflow: ellipsis; overflow: hidden;` |
| 导航菜单 | 缩短文字或使用图标 | 提供短版翻译 Key |
| 卡片标题 | 限制行数 + 省略号 | `line-clamp: 2;` |
| 标签/Badge | 设定最大宽度 | `max-width: 120px;` |

**短版翻译 Key**（用于空间受限场景）:

```json
{
  "project": {
    "create": {
      "full": "创建新项目",
      "short": "新建"
    },
    "delete": {
      "full": "删除此项目",
      "short": "删除"
    }
  }
}
```

### 字体选择

**字体栈设计**:

| 语言 | 推荐字体栈 | 说明 |
|------|-----------|------|
| 中文 | `"PingFang SC", "Microsoft YaHei", sans-serif` | 系统默认中文字体 |
| 英文 | `"Inter", "Helvetica Neue", sans-serif` | 现代无衬线字体 |
| 日语 | `"Hiragino Sans", "Yu Gothic", sans-serif` | 日文系统字体 |
| 韩语 | `"Apple SD Gothic Neo", "Malgun Gothic", sans-serif` | 韩文系统字体 |
| 阿拉伯语 | `"Noto Naskh Arabic", "Traditional Arabic", sans-serif` | 阿拉伯文专用字体 |

**字体加载策略**:

```css
/* 按语言动态加载字体，避免加载全部字体文件 */
:root {
  --font-family-base: "PingFang SC", "Microsoft YaHei", sans-serif;
}

:root[lang="en-US"] {
  --font-family-base: "Inter", "Helvetica Neue", sans-serif;
}

:root[lang="ja-JP"] {
  --font-family-base: "Hiragino Sans", "Yu Gothic", sans-serif;
}

:root[lang="ar-SA"] {
  --font-family-base: "Noto Naskh Arabic", "Traditional Arabic", sans-serif;
  --font-size-base: 16px; /* 阿拉伯语需要稍大字号 */
  --line-height-base: 1.8; /* 阿拉伯语需要更大行高 */
}
```

## Phase 6: 输出 i18n-design.md

文件保存到 `docs/i18n-design.md`，章节结构：

```markdown
# 国际化设计: [项目名称]

## 1. 语言与区域规划
### 1.1 支持的语言列表
### 1.2 默认语言与回退策略
### 1.3 语言检测优先级
### 1.4 语言切换方式

## 2. 翻译方案设计
### 2.1 翻译文件格式选择
### 2.2 翻译文件目录结构
### 2.3 Key 命名规范
### 2.4 插值与复数处理
### 2.5 翻译管理平台与流程
### 2.6 翻译覆盖率要求

## 3. 时区与日期设计
### 3.1 时区存储策略
### 3.2 日期时间格式化规范
### 3.3 时区转换规则

## 4. 货币与数字格式
### 4.1 支持的货币列表
### 4.2 数字格式化规范
### 4.3 度量单位对照
### 4.4 排序规则（Collation）

## 5. UI 适配设计
### 5.1 RTL 布局方案
### 5.2 文字溢出处理
### 5.3 动态内容长度适配
### 5.4 字体选择方案
### 5.5 各语言截图对比（关键页面）

## 6. 国际化测试清单
```
