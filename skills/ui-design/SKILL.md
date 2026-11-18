---
name: ui-design
version: v2.0.0
type: skill
enabled: true
mode: [standard, creator]
description: "system-design 阶段进行页面路由规划、线框图设计、组件库选择与状态处理，输出 UI 设计文档供前端开发参考。参考 shadcn/ui、Material Design 3、Ant Design。触发词: UI、页面设计、线框图、原型、设计稿。"
updated: 2026-08-13
depends_on: [system-design]
composes: [frontend-component, html-document-center]
---
# UI Design


## 负责代理

`ui-designer` — UI 设计由 UI 设计师代理负责，连接需求分析与前端实现，确保页面路由、线框图、组件库和状态处理完整。

## 何时使用

- 需要规划**页面路由和页面清单**时
- 需要设计**页面线框图（Wireframe）**时
- 需要选择**组件库和确定设计风格**时
- 需要定义**空态/加载态/错误态**处理方式时
- 需要规划**响应式布局和移动端适配**时
- `frontend-component` 编码前，需要 UI 设计参考时

**触发关键词**: "UI设计"、"页面设计"、"线框图"、"页面路由"、"组件库"、"响应式"、"wireframe"、"设计令牌"、"Design Tokens"

## 开源设计系统参考

> 设计阶段应参考以下优秀开源设计系统，确保设计质量和一致性。

### 推荐设计系统

| 设计系统 | 特点 | 适用场景 | 参考链接 |
|----------|------|----------|----------|
| **shadcn/ui** | 开放代码、AI 友好、可定制 | React + Tailwind 项目（首选） | [ui.shadcn.com/docs](https://ui.shadcn.com/docs) |
| **Material Design 3** | 完整设计系统、动效丰富 | 通用 Web / Android 项目 | [material.io/design](https://material.io/design) |
| **Ant Design** | 企业级、组件丰富 | 后台管理系统 | [ant.design/docs/spec](https://ant.design/docs/spec/introduce) |
| **Chakra UI** | 开箱即用、默认可访问 | 快速原型 / 可访问性优先 | [chakra-ui.com/docs](https://chakra-ui.com/docs/getting-started) |
| **Radix UI** | 无样式基础、无障碍 | 需要高度自定义的项目 | [radix-ui.com/primitives](https://www.radix-ui.com/primitives) |

### shadcn/ui 核心原则（AI-Ready 设计系统）

1. **Open Code**: 组件源码可访问、可修改 — 不是 NPM 包，而是可复制的代码
2. **Composition**: 所有组件共享可组合接口 — 学习一次，处处可用
3. **Beautiful Defaults**: 精心设计的默认样式 — 开箱即用，无需额外配置
4. **AI-Ready**: 代码结构清晰、类型明确 — LLM 可读取、理解、改进

### 设计令牌（Design Tokens）参考

设计令牌是设计系统的基础原子，建议参考以下结构定义：

```yaml
# 设计令牌层级
原始令牌（原始值）→ 语义令牌（用途描述）→ 组件令牌（组件特定）
例: --color-primary-500: #6366f1 → --color-button-primary: var(--color-primary-500)
```

详细规范见 `rules/ui-design-patterns.md`。

### AI 辅助 UI 设计工具

> **注意**：以下工具仅用于辅助设计探索，核心实现仍需使用开源组件库。优先使用本地开发工具而非云端服务。

| 工具 | 用途 | 特点 | 开源替代 |
|------|------|------|----------|
| **v0.dev** | AI 生成 React 组件原型 | 基于 shadcn/ui，自然语言描述即生成 | 直接使用 shadcn/ui 组件 |
| **Bolt.new** | AI 全栈开发原型 | 快速生成完整应用原型 | 手动搭建 + AI 辅助编码 |
| **Cursor AI** | AI 代码编辑器 | 支持设计稿 → 代码转换 | VS Code + 开源插件（Continue、Codeium） |

## 与其他技能的关系

```
brainstorming → system-design → api-design
                     ↓              ↓
                  ui-design ←──────┘
                     ↓
            frontend-component（编码）
```

> **衔接规则**:
> - `ui-design` 与 `api-design` **并行执行**，两者都依赖 `system-design` 的架构和数据库设计
> - `ui-design` 的每个页面必须对应 `api-design` 的接口（数据来源）
> - `frontend-component` 编码时以 `ui-design` 输出的线框图为依据

## 执行流程

### Phase 1: 页面规划

**目标**: 确定所有页面及其路由、权限和依赖关系。

#### Step 1: 页面清单

基于 `system-design` 的架构设计和 `brainstorming` 的功能需求，列出所有页面：

| 路径 | 页面名 | 说明 | 需登录 | 权限 | 数据来源（API） |
|------|--------|------|--------|------|----------------|
| / | 首页 | 产品介绍 | 否 | — | — |
| /login | 登录页 | 用户登录 | 否 | — | POST /auth/login |
| /register | 注册页 | 用户注册 | 否 | — | POST /auth/register |
| /dashboard | 仪表盘 | 数据概览 | 是 | — | GET /users/me |
| /projects | 项目列表 | 查看所有项目 | 是 | — | GET /projects |
| /projects/new | 创建项目 | 新建项目表单 | 是 | — | POST /projects |
| /projects/:id | 项目详情 | 项目信息和任务 | 是 | 项目成员 | GET /projects/:id |
| /projects/:id/edit | 编辑项目 | 修改项目信息 | 是 | 项目管理员 | PATCH /projects/:id |
| /tasks | 任务列表 | 查看所有任务 | 是 | — | GET /tasks |
| /settings | 设置页 | 个人设置 | 是 | — | GET + PATCH /users/me |
| /404 | 404 页面 | 页面不存在 | 否 | — | — |

> **交叉校验**: 每个页面至少对应 1 个 API 接口；每个需要数据的页面必须有数据来源。

#### Step 2: 全局布局定义

**导航结构**:

```
顶部导航（TopNav）: [Logo] [首页] [功能] [定价]    [登录] [注册]  ← 未登录
顶部导航（TopNav）: [Logo] [仪表盘] [项目] [任务]  [头像▼]       ← 已登录

侧边导航（SideNav，仅管理后台）:
├── 仪表盘
├── 项目管理
│   ├── 项目列表
│   └── 新建项目
├── 任务管理
│   ├── 任务列表
│   └── 我的任务
└── 设置
```

**响应式断点**:

| 断点名 | 宽度 | 布局变化 |
|--------|------|----------|
| sm | < 640px | 单列布局，隐藏侧边栏，汉堡菜单 |
| md | 640px - 1024px | 双列布局，侧边栏可折叠 |
| lg | > 1024px | 三列布局，固定侧边栏 |

**主题配置**:

```yaml
# 色彩系统
colors:
  primary: "#6366f1"      # 品牌色（Indigo-500）
  secondary: "#8b5cf6"    # 辅助色（Violet-500）
  background: "#0f172a"   # 深色背景（Slate-900）
  surface: "#1e293b"      # 卡片背景（Slate-800）
  text: "#f8fafc"         # 主文字（Slate-50）
  textMuted: "#94a3b8"    # 次要文字（Slate-400）
  border: "#334155"       # 边框（Slate-700）
  success: "#22c55e"      # 成功（Green-500）
  warning: "#eab308"      # 警告（Yellow-500）
  error: "#ef4444"        # 错误（Red-500）

# 圆角
radius:
  sm: 4px
  md: 8px
  lg: 12px
  full: 9999px

# 字体
font:
  sans: "Inter, system-ui, sans-serif"
  mono: "JetBrains Mono, monospace"
```

---

### Phase 2: 页面线框设计

**目标**: 为每个页面设计线框图，明确内容区块和交互行为。

#### Step 3: 用 AI 做 UI 设计

**Prompt 模板（给 v0.dev / Bolt / Cursor）**:

```
设计一个 [页面名称] 页面：

页面用途：[一句话]
包含区块：
顶部：[导航/面包屑/标题]
主体：[列表/表单/卡片/表格]
侧边：[筛选器/详情面板]（如有）
底部：[分页/操作栏]

数据字段：[列出要展示的字段]
交互行为：[点击/拖拽/搜索/筛选]
风格：简洁现代 / 参考 [某产品]
组件库：shadcn/ui
响应式：需要适配移动端
```

#### Step 4: 各页面线框说明

为每个核心页面编写线框说明：

```markdown
### 项目列表页 (/projects)

**布局结构**:
```
[TopNav]
[页面标题: 我的项目] [新建项目按钮]
[筛选栏: 全部 | 进行中 | 已完成 | 搜索框]
[项目卡片网格]
  ┌─────────────┐  ┌─────────────┐
  │ 项目名称     │  │ 项目名称     │
  │ 描述...      │  │ 描述...      │
  │ 状态: 进行中 │  │ 状态: 已完成 │
  │ 更新时间     │  │ 更新时间     │
  └─────────────┘  └─────────────┘
[分页: < 1 2 3 ... 10 >]
```

**包含组件**:
- ProjectCard（项目卡片）
- StatusBadge（状态标签）
- Pagination（分页器）
- SearchInput（搜索输入框）

**数据来源**:
- GET /api/v1/projects?page=1&status=active

**交互说明**:
- 点击卡片 → 跳转 /projects/:id
- 点击新建按钮 → 跳转 /projects/new
- 筛选状态 → 触发重新请求
- 搜索 → 防抖 300ms 后请求

**空态**: 无项目时显示空状态插画 + "创建你的第一个项目"按钮
```

---

### Phase 3: 组件与状态设计

**目标**: 定义可复用组件和全局状态处理方案。

#### Step 5: 组件复用清单

| 组件名 | 用途 | 使用页面 | Props |
|--------|------|----------|-------|
| TopNav | 顶部导航 | 全部 | user, onLogout |
| ProjectCard | 项目卡片 | /projects, /dashboard | project, onClick |
| StatusBadge | 状态标签 | /projects, /tasks | status |
| EmptyState | 空状态 | /projects, /tasks | title, description, action |
| LoadingSkeleton | 加载骨架 | 全部 | rows |
| ErrorBoundary | 错误边界 | 全部 | fallback |
| Pagination | 分页器 | /projects, /tasks | page, total, onChange |
| SearchInput | 搜索输入 | /projects, /tasks | value, onChange, placeholder |

#### Step 6: 状态/空态/加载态/错误态处理

**状态矩阵**:

| 场景 | 加载中 | 空数据 | 错误 | 正常 |
|------|--------|--------|------|------|
| **项目列表** | Skeleton 骨架屏 | 空状态插画 + CTA | Toast 错误提示 + 重试按钮 | 卡片网格 |
| **项目详情** | 页面级 Spinner | — | 错误页面（返回按钮） | 详情面板 |
| **表单提交** | 按钮 Loading | — | 字段级错误提示 | 成功 Toast + 跳转 |
| **搜索** | 输入框 Loading | "无搜索结果" | — | 搜索结果列表 |

**统一状态组件**:

```typescript
// 推荐封装方式
interface AsyncState<T> {
  data: T | null;
  isLoading: boolean;
  isError: boolean;
  error: Error | null;
}

// 使用 Suspense + ErrorBoundary
<ErrorBoundary fallback={<ErrorPage />}>
  <Suspense fallback={<LoadingSkeleton />}>
    <ProjectList />
  </Suspense>
</ErrorBoundary>
```

---

### Phase 4: 移动端适配

**目标**: 确保核心功能在移动端可用。

#### Step 7: 移动端适配说明

**优先保障**:
- [ ] 所有页面不崩、不溢出
- [ ] 核心流程可用（登录 → 创建 → 查看）
- [ ] 触摸目标 ≥ 44x44px
- [ ] 字体大小 ≥ 14px

**移动端特殊处理**:

| 页面 | 桌面端 | 移动端 |
|------|--------|--------|
| 项目列表 | 3 列卡片网格 | 单列卡片，全宽 |
| 项目详情 | 左右分栏（详情+任务） | 上下堆叠，Tab 切换 |
| 表单 | 多列布局 | 单列，全宽输入框 |
| 导航 | 固定顶部 + 侧边栏 | 固定底部 Tab 栏 |

**移动端组件调整**:
- 表格 → 卡片列表
- 侧边筛选 → 底部抽屉
- 悬停提示 → 点击弹窗
- 多级菜单 → 面包屑 + 返回

---

### Phase 5: 输出 ui-wireframe.md

文件保存到 `docs/ui-wireframe.md`:

```markdown
# UI 设计: [项目名称]

## 1. 页面路由清单
（Phase 1 Step 1 的表格）

## 2. 全局布局说明
### 2.1 导航结构
### 2.2 响应式断点
### 2.3 主题配置（色彩/字体/圆角）

## 3. 各页面线框说明
### 3.1 首页 (/)
### 3.2 登录页 (/login)
### 3.3 仪表盘 (/dashboard)
### 3.4 项目列表 (/projects)
### 3.5 项目详情 (/projects/:id)
### 3.6 ...

## 4. 组件复用清单

## 5. 状态/空态/加载态/错误态处理

## 6. 移动端适配说明
```

---

## UI 设计检查清单

- [ ] 所有页面路由已列出
- [ ] 每个页面知道数据从哪来（对应 API）
- [ ] 空状态有设计（无数据时显示什么）
- [ ] 加载状态有设计（Skeleton / Spinner）
- [ ] 错误状态有设计（网络失败/404/500）
- [ ] 表单有校验提示
- [ ] 操作有反馈（Toast / 按钮 loading）
- [ ] 移动端可用（至少不崩）
- [ ] 色彩对比度达标（可访问性）
- [ ] 暗色模式是否支持（可选）

## 硬性规则

- ✅ **每个页面必须对应至少一个 API 接口** — UI 不凭空产生数据
- ✅ **空状态必须有设计** — 无数据时不允许空白页面
- ✅ **加载状态必须有设计** — 不允许无反馈的等待
- ✅ **错误状态必须有设计** — 网络失败、404、500 都有处理
- ✅ **表单必须有校验提示** — 前端校验 + 后端校验双重保障
- ✅ **操作必须有反馈** — Toast、Loading、成功/失败提示
- ✅ **移动端至少可用** — 不追求完美，但核心功能不崩
- ✅ **可复用组件必须抽离** — 不重复造轮子
- ❌ **禁止设计无法实现的交互** — 超出技术栈能力范围
- ❌ **禁止忽略暗色模式** — 如项目支持暗色，必须同步设计
- ❌ **禁止页面超过一屏无滚动提示** — 用户需要知道下方有内容

## 反模式

- ❌ "请设计师画高保真" — 个人项目用 AI 工具快速生成即可
- ❌ "纠结像素级细节" — MVP 阶段功能优先，视觉其次
- ❌ "每个页面都独一无二" — 统一布局框架，保持体验一致
- ❌ "只在桌面端设计" — 移动端流量占比高，必须考虑
- ❌ "忽略空状态" — 空白页面是最差体验
- ❌ "表单无校验提示" — 用户不知道哪里填错了
- ❌ "操作无反馈" — 用户不知道是否成功
