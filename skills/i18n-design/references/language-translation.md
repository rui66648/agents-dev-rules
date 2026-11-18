# 语言规划与翻译方案参考（i18n-design Phase 1-2 配套）

> 本文档按需加载。包含语言清单、检测策略、翻译文件格式、Key 命名规范、插值复数、翻译管理流程。

## Phase 1: 语言与区域规划

**目标**：确定支持的语言列表、默认语言、检测与切换策略。

### 语言清单（示例基线，按产品目标市场调整）

| 语言代码 | 语言名称 | 区域 | 书写方向 | 优先级 | 覆盖范围 |
|----------|----------|------|----------|--------|----------|
| zh-CN | 简体中文 | 中国大陆 | LTR | P0 | 全量 |
| en-US | 英语（美国） | 美国/国际 | LTR | P0 | 全量 |
| zh-TW | 繁体中文 | 台湾/香港 | LTR | P1 | 全量 |
| ja-JP | 日语 | 日本 | LTR | P1 | 全量 |
| ko-KR | 韩语 | 韩国 | LTR | P2 | 核心页面 |
| ar-SA | 阿拉伯语 | 沙特/中东 | RTL | P2 | 核心页面 |
| es-ES | 西班牙语 | 西班牙/拉美 | LTR | P3 | 营销页面 |
| fr-FR | 法语 | 法国/非洲 | LTR | P3 | 营销页面 |

> **语言代码规范**：遵循 BCP 47 标准，格式为 `语言-区域`（如 `zh-CN`、`en-US`）。语言代码使用 ISO 639-1，区域代码使用 ISO 3166-1。

### 默认语言与回退策略

| 配置项 | 值 | 说明 |
|--------|-----|------|
| 默认语言 | `zh-CN` | 无法匹配时的回退语言 |
| 回退链 | `zh-CN` → `en-US` | 翻译缺失时按链路回退 |
| 严格模式 | 否 | Key 缺失时显示回退语言文本，不报错 |

**语言检测优先级**（从高到低）:

```text
1. URL 路径参数     →  /zh-CN/products  → 最高优先级，SEO 友好
2. 用户偏好设置     →  DB 中存储的 locale 字段
3. Cookie/LocalStorage → 上次访问选择的语言
4. 浏览器 Accept-Language 头 → 自动检测
5. 默认语言         →  zh-CN（兜底）
```

### 语言切换方式

| 切换方式 | 实现 | 说明 |
|----------|------|------|
| URL 路径切换 | `/zh-CN/products` → `/en-US/products` | 推荐，SEO 友好 |
| 查询参数切换 | `/products?lang=en-US` | 不推荐，影响 SEO |
| 子域名切换 | `en.example.com/products` | 大型多区域站点 |
| 前端路由切换 | `router.push({ params: { locale: 'en-US' } })` | SPA 应用 |

**语言切换行为**:
- 切换语言后停留在当前页面，不跳回首页
- 切换语言后同步更新 `<html lang="">` 属性
- 如果当前页面在目标语言中不存在，展示 404 并提示切换语言

## Phase 2: 翻译方案设计

**目标**：定义翻译文件格式、Key 命名规范、翻译管理流程。

### 翻译文件格式

| 格式 | 适用场景 | 优点 | 缺点 |
|------|----------|------|------|
| **JSON（推荐）** | 前端项目 | 原生支持、无需解析器、IDE 支持好 | 不支持注释、嵌套层级深 |
| YAML | 全栈项目 | 可读性好、支持注释 | 缩进敏感、需额外解析器 |
| ICU MessageFormat | 复杂语法 | 支持复数/性别/选择 | 学习曲线高、文件体积大 |

**推荐 JSON 格式**（结构化 Key）:

```json
{
  "common": {
    "save": "保存",
    "cancel": "取消",
    "delete": "删除",
    "confirm": "确认",
    "loading": "加载中...",
    "noData": "暂无数据",
    "error": {
      "network": "网络连接失败，请检查网络",
      "server": "服务器错误，请稍后重试",
      "unauthorized": "登录已过期，请重新登录"
    }
  },
  "auth": {
    "login": {
      "title": "登录",
      "username": "用户名",
      "password": "密码",
      "submit": "登录",
      "forgotPassword": "忘记密码？"
    }
  },
  "project": {
    "list": {
      "title": "我的项目",
      "empty": "还没有项目，创建第一个吧",
      "search": "搜索项目",
      "filter": {
        "all": "全部",
        "active": "进行中",
        "completed": "已完成"
      }
    }
  }
}
```

**翻译文件目录结构**:

```text
src/
├── locales/
│   ├── zh-CN.json       # 简体中文
│   ├── en-US.json       # 英语（美国）
│   ├── zh-TW.json       # 繁体中文
│   ├── ja-JP.json       # 日语
│   ├── ko-KR.json       # 韩语
│   ├── ar-SA.json       # 阿拉伯语
│   ├── es-ES.json       # 西班牙语
│   └── fr-FR.json       # 法语
```

### Key 命名规范

| 规则 | 说明 | 示例 |
|------|------|------|
| 模块前缀 | 按页面/功能模块分组 | `auth.`、`project.`、`dashboard.` |
| 层级命名 | 使用点号分隔层级 | `project.list.title` |
| 语义化 | Key 描述文本含义，非位置 | `project.list.title` 优于 `page1.header` |
| 公共 Key | 通用文本放 `common.` 下 | `common.save`、`common.cancel` |
| 错误 Key | 错误信息放 `common.error.` 下 | `common.error.network` |

**反例**:

```text
❌ "btn_save"           — 无法判断是哪个页面的按钮
❌ "page1_title"         — 页面编号无意义
❌ "project_list_title_text"  — 过度冗长
❌ "项目列表标题"          — 不能使用中文作为 Key
```

### 插值与复数

**变量插值**:

```json
{
  "project": {
    "memberCount": "共 {count} 位成员",
    "welcome": "欢迎回来，{username}！",
    "lastLogin": "上次登录时间：{datetime}"
  }
}
```

**复数形式**（ICU MessageFormat 语法）:

```json
{
  "project": {
    "memberCount": "{count, plural, =0 {暂无成员} =1 {1 位成员} other {# 位成员}}",
    "taskCount": "{count, plural, =0 {没有任务} one {# 个任务} other {# 个任务}}"
  }
}
```

### 翻译管理平台与流程

**平台选择**:

| 平台 | 适用场景 | 优点 | 缺点 |
|------|----------|------|------|
| Lokalise | 中大型团队 | 功能全面、API 强大、截图上下文 | 付费 |
| Crowdin | 开源项目 | 开源免费、GitHub 集成 | 高级功能付费 |
| Weblate | 自托管 | 开源、可自部署 | 需自行维护 |
| 手动管理 JSON | 个人项目 | 零成本、无依赖 | 协作困难 |

**翻译工作流**:

```text
开发阶段:
  1. 开发者定义 Key 并在 zh-CN.json 中写入中文源文本
  2. 开发者用机器翻译填充 en-US.json（DeepL / Google Translate）
  3. 提交 PR 时附带新增 Key 清单

校对阶段:
  4. 人工校对者审核机器翻译结果
  5. 校对通过后合并到主分支

持续维护:
  6. CI 检测新增/删除的 Key，自动通知翻译
  7. 定期运行翻译覆盖率检查（目标: 100%）
```
