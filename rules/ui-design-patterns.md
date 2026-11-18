---
name: ui-design-patterns
version: v1.0.1
type: rule
enabled: true
mode: [standard, creator]
updated: 2026-11-05
description: UI 设计模式 — 布局、组件、交互、可访问性、响应式规范
applies_to:
  agents: ['ui-designer', 'frontend-developer']
  phases: ['design']
  project_types: ['web', 'mobile']
  tech_stacks: ['typescript', 'kotlin', 'js']
---
## 前端开源 UI 工具链（AI 自主选型参考）

> **核心原则**：本节**不指定具体技术**，仅给出选型方向与质量约束。具体选型由 AI 在 `rules/open-source-first.md` 框架内判断，并通过 ADR 记录决策过程。

### 选型方向（按 UI 维度）

| 维度 | 选型方向 | 约束 |
|------|----------|------|
| **设计系统** | 从 shadcn/ui / Ant Design / Material Design 3 / Chakra UI / Radix UI / HeroUI / Mantine / Park UI 中选 | 必须支持暗色模式；必须支持 WCAG 2.1 AA |
| **原子级 UI 素材库** | [Uiverse.io](https://uiverse.io) | 本仓库 `components/` 已落地 10 个组件（MIT）；网站 7300+ 元素可复用 |
| **CSS 方案** | 从 Tailwind CSS / UnoCSS / Vanilla Extract 中选 | 默认 Tailwind；零运行时需求选 UnoCSS |
| **图标** | 从 Lucide / Tabler / Phosphor / Hugeicons 中选 | 同一项目禁止混用 ≥ 2 个图标库 |
| **字体（中英混排）** | Noto Sans CJK SC（中文）+ Inter / Geist（西文） | 通过 Fontsource 自托管；禁止 Google Fonts 外链 |
| **图表** | Recharts（简单） / Apache ECharts（复杂） / AntV G2/G6（数据大屏） / DataV-React（炫酷大屏） | 同一项目禁止混用 ≥ 2 个图表库 |
| **表单** | React Hook Form + Zod 优先 | 后端校验与前端 Schema 同源（Zod 兼容 OpenAPI） |
| **状态（服务端）** | TanStack Query v5+ | 对象式调用语法 |
| **状态（客户端）** | Zustand / Jotai | 简单场景用 Zustand；原子化场景用 Jotai |
| **动画** | motion（原 Framer Motion）/ CSS-only | 必须尊重 `prefers-reduced-motion` |
| **表格** | TanStack Table | 与设计系统配套使用 |
| **富文本** | TipTap（默认） / Lexical（极致性能） | 禁止使用已不维护的 Quill / Slate v1 |
| **拖拽** | dnd-kit / Swapy | 禁止 react-beautiful-dnd（已不维护） |
| **PDF** | react-pdf（基于 pdf.js） | 服务端生成用 WeasyPrint（Python） |
| **Markdown** | react-markdown + remark-gfm / MDX | 长文档用 MDX |
| **二维码 / 条码** | qrcode.react / JsBarcode | 体积小、按需引入 |
| **时间日期** | date-fns / Day.js / Luxon | 默认 date-fns；中文场景 Day.js |
| **国际化** | react-i18next / Lingui / Intlayer | TypeScript 友好首选 Lingui 或 Intlayer |
| **Mock** | MSW（Mock Service Worker） | 替代 json-server |
| **可视化大屏** | AntV G6 / DataV-React | 3D 场景用 React Three Fiber |
| **图片处理** | react-image-crop（裁剪）+ sharp（服务端） | 服务端用 Pillow（Python） |

### 场景化推荐（AI 参考，非强制）

| 场景 | 推荐组合方向 |
|------|--------------|
| 管理后台 / CRM / ERP | shadcn/ui + TanStack Table + Recharts + TipTap |
| AI Chat / 流式输出 | shadcn/ui + AI Elements + OpenAI Assistants API（开源协议） |
| 数据大屏 / 看板 | AntV G6 / DataV-React + Gridstack（拖拽布局） |
| 富文本编辑器 | TipTap + ProseMirror + Y.js（实时协作） |
| 移动端 PWA | shadcn/ui + Tailwind 响应式 |
| 文档站点 | shadcn/ui + MDX + react-markdown |
| 知识图谱可视化 | React Three Fiber / AntV G6 + dnd-kit |

### Uiverse.io 原子级 UI 素材库（MIT）

> **定位**：Uiverse.io 不是设计系统或组件库，而是**社区驱动的原子级 UI 元素素材库**，提供可直接复制粘贴的 HTML/CSS/React/Tailwind/Figma 片段。与设计系统互补，用于快速获取单点样式灵感或落地元素。

**本仓库已落地一套复用工作流**（务必优先走这套，而非重新引入）：
- 组件库：`components/`（当前 10 个组件，MIT，`manifest.json` 登记元数据）
- 获取记录：`archive/crawling-2026-11-04/crawling-process.md`（8 个首批 + 1 个新增组件的完整爬取过程）
- 复用指南：`docs/ui-component-guide.md`（复用已有组件 + 按标准流程获取新组件）
- 复制脚本：`scripts/fetch-ui-component.py`（`--list` / `--name` / `--category` / `--all`）
- 展示页：历史产物已按 RULE-052 从仓根清理，不再维护；需要预览时用 `fetch-ui-component.py --all` 复制后在本地打开

**关键事实（License 合规）**
- License：**MIT**（GitHub 仓库 `uiverse-io/galaxy`，882 贡献者）—— 符合白名单，可个人与商业使用。
- 网站规模：7300+ 社区元素；本仓库已落地其中 10 个。
- 格式：HTML / CSS / Tailwind / React / Figma 五种。
- **仓库活跃度**：`uiverse-io/galaxy` 仓库**已于 2024-09-02 停止更新**，2024 年 9 月后发布的新组件仅存在于 uiverse.io 网站，需用浏览器工具从网站提取（见 `ui-component-guide.md` 常见问题）。
- 归属（非强制但鼓励）：使用时建议注明原始创作者与 Uiverse.io。

**使用建议（AI 选型提示）**
- **适用**：单点元素（按钮、加载动画、表单、卡片、开关、复选框）的快速选型与样式复用。
- **不适用**：需要响应式布局、状态管理、可访问性契约的整页或复杂业务组件 —— 这些应交给设计系统（shadcn/ui 等）。
- **约束**：复制而来的元素必须通过可访问性检查（WCAG 2.1 AA）、暗色模式适配，并纳入组件库统一命名（如 `ui/` 目录）。
- **一律优先复用 `components/`**：需要 Uiverse 元素时，先查 `components/manifest.json` 是否已有，有则用 `fetch-ui-component.py` 复制；没有才按 `ui-component-guide.md` 的流程获取新组件。
- **与设计系统关系**：优先用设计系统解决 80% 基础组件；用 Uiverse.io 填补设计系统未覆盖的创意单点元素（如特效按钮、玻璃态卡片、加载动画）。

### AI 选型流程

1. **识别场景** — 管理后台 / 大屏 / 编辑器 / 移动端 / 实时协作？
2. **从维度表中选型** — 每个维度给出 1-2 个候选
3. **评估 License 与成熟度** — 参考 `rules/open-source-first.md`
4. **写 ADR** — 在 `docs/decisions/NNN-ui-stack.md` 记录决策
5. **同步到 tech-stack.md** — 把最终选型固化到项目根目录

### 与 `tech-stack.md` 的关系

- `tech-stack.md` 只记录**本项目最终选定的**技术栈（已落地的）
- `rules/ui-design-patterns.md` 提供**选型方向与约束**（跨项目通用）
- AI 在新项目中选型时，参考本文件，写 ADR，最终结果写入 `tech-stack.md`

