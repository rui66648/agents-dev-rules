# system-design 交接与 HTML 报告参考（brainstorming 步骤 7 / 8 配套）

> 本文档按需加载。包含设计文档批准后进入 system-design 的完整流程，以及 HTML 可视化报告生成规范。

## 1. 进入 system-design 阶段

设计文档经用户批准后，**自动进入 system-design 阶段**，而非直接调用 writing-plans。

```
brainstorming 完成（设计文档批准）
    ↓
system-design 阶段（并行执行 3 个子流程）
    ├── → 架构设计（architect 代理）→ architecture.md
    ├── → API 接口设计（api-design 技能）→ api-design.md
    └── → 前端 UI 设计（ui-design 技能）→ ui-wireframe.md
    ↓
四份设计文档全部完成后
    ↓
writing-plans 阶段
    ↓
executing-plans 阶段
```

> **关键规则**：
> - `initiative` 级别设计需分解为子 phase，每个 phase 独立走 brainstorming → system-design → writing-plans 循环
> - system-design 阶段必须输出 `architecture.md`、`database-schema.md`、`api-design.md`、`ui-wireframe.md` 四份文档
> - 四份文档全部完成后，才能进入 writing-plans

### 1.1 system-design 阶段执行顺序

| 步骤 | 执行内容 | 负责人/技能 | 输出文件 |
|------|---------|------------|---------|
| 1 | 架构设计（技术选型、模块划分、目录结构） | `architect` 代理 | `docs/architecture.md` |
| 2 | 数据库设计（ER 图、表结构、索引） | `architect` 代理 | `docs/database-schema.md` |
| 3 | API 接口设计（路由、Schema、契约） | `api-design` 技能 | `docs/api-design.md` |
| 4 | 前端 UI 设计（页面路由、线框图、组件） | `ui-design` 技能 | `docs/ui-wireframe.md` |

> **并行规则**：步骤 1-2 可串行执行（架构依赖数据库），步骤 3-4 可与步骤 1-2 并行执行。

### 1.2 模块化 system-design（按功能模块拆分，大型项目/initiative）

**模块划分参考模板**：

| 模块 | 设计内容 | 负责代理 | 依赖上游 |
|------|---------|---------|---------|
| **M1** | 架构总览、技术选型、模块边界 | `architect` | —（先执行） |
| **M2** | 数据库 ER 图、表结构、索引 | `architect` | M1 |
| **M3** | 核心业务引擎（Agent/Skill/功能模块） | `backend-developer` | M1 + M2 |
| **M4** | 前端 UI / IDE 组件设计 | `frontend-developer` | M1 + M3 |
| **M5** | 代码执行 / 沙箱 / 任务队列 | `backend-developer` | M1 + M2 |
| **M6** | 通信同步（WebSocket / 推送 / 实时） | `backend-developer` | M1 + M5 |
| **M7** | 第三方服务集成（LLM / 存储 / 通知） | `backend-developer` | M1 + M3 |
| **M8** | 安全策略（认证 / 授权 / 审计 / 白名单） | `security-auditor` | M1 + M5 + M6 |

**模块化执行原则**：

1. **M1 必须最先执行** — 架构决策是后续所有模块的基础
2. **按依赖顺序执行** — 后序模块依赖前序模块的输出（architecture.md → database-schema.md）
3. **同 Phase 可并行** — 同一 Phase 内无依赖关系的模块可并行执行
4. **每 Phase 完成后进入 writing-plans** — 每个 Phase 独立产出实施计划，可逐步验证

**典型 Phase 拆分示例**：

```
Phase 1: M1（架构）→ writing-plans → executing-plans（先跑通）
Phase 2: M2（数据库）+ M3（核心引擎）→ writing-plans → executing-plans
Phase 3: M4（前端）+ M5（代码执行）→ writing-plans → executing-plans
Phase 4: M6（同步）+ M8（安全）→ writing-plans → executing-plans
Phase 5: M7（模型管理）→ writing-plans → executing-plans
```

> **brainstorming 阶段需确认**：输出设计文档时，明确 system-design 将按哪些模块、分哪些 Phase 执行。用户可选择最小可用集（M1+M2+M3）或完整集（M1-M8）。

## 2. HTML 可视化报告（可选但推荐）

**system-design 阶段四份设计文档全部完成后**，**自动**调用 `docs-author` 代理（负责技能：`html-document-center`，含 HTML 报告生成能力）将设计文档关键内容生成为交互式 HTML 报告。

> **参考规范**：`skills/html-document-center/SKILL.md`、`agents/docs-author.md`、`rules/workflow-html.md`（交叉点 A）

### 2.1 触发条件

| 条件 | 执行 HTML 生成 | 说明 |
|------|--------------|------|
| scope = `initiative` | ✅ 必须 | 新产品设计需向团队/投资者展示 |
| 文档含 Market Context 章节 | ✅ 必须 | 包含竞品对比表 + 用户画像，适合可视化 |
| scope = `feature`/`phase` | ⚠️ 可选 | 用户可要求生成，或仅生成关键章节 |
| 纯内部功能迭代 | ❌ 跳过 | 无需对外展示 |

### 2.2 报告生成流程

```
设计文档 MD → 安全审查（脱敏）→ html-report 技能 → docs/designs/<slug>/index.html
```

**内容提取规则**：

| 设计文档章节 | HTML 报告呈现方式 |
|-------------|----------------|
| Intent Contract | Hero 区域 + 关键指标卡片（风险等级、复杂度） |
| Market Context（initiative） | ECharts 竞品对比柱状图 + 市场规模趋势图 |
| User Personas（initiative） | 用户画像卡片（背景/痛点/场景/付费意愿） |
| Scope | 表格形式（In / Out 对比） |
| Decisions | 决策矩阵表格（决策 / 选择 / 否定方案） |
| Surface | 组件/接口列表卡片组 |
| Risks & Open Questions | 风险等级色标 + 待确认事项列表 |

### 2.3 报告输出路径

遵循 `html-document-center` 技能规范，每个设计文档对应独立目录：

```
docs/
├── designs/
│   └── YYYY-MM-DD-<slug>/
│       ├── index.html          # 可视化报告（HTML）
│       └── assets/             # 图表/图片资源
│           └── charts.js       # ECharts 初始化脚本
└── (其他设计文档...)
```

> 原始 Markdown 设计文档保留在 `docs/designs/YYYY-MM-DD-<slug>-design.md`，HTML 报告与 Markdown 并存。

### 2.4 报告视觉风格

根据设计类型自动选择（遵循 `docs-author.md` 规范）：

| 设计类型 | 视觉风格 | 说明 |
|---------|---------|------|
| 技术架构决策 | 暗色主题（Solid，`--bg: #0B0D12`） | 技术向团队展示 |
| 产品功能设计 | Fresh Gradient（毛玻璃卡片） | 产品向团队/投资者展示 |
| 市场分析（initiative） | Fresh Gradient + ECharts 图表 | 商业向展示，含数据可视化 |

**CSS 变量主题**（暗色，默认）：

```css
:root {
  --bg: #0B0D12;
  --bg2: #111827;
  --ink: #E4E6F0;
  --muted: #989CB4;
  --rule: #2E3348;
  --accent: #34D399;
  --accent2: #60A5FA;
  --accent3: #FBBF24;
  --danger: #F87171;
}
```

### 2.5 安全审查（必须）

遵循 `docs-author.md` 文档安全审查清单，在 HTML 生成前执行：

| 检查项 | 处理方式 |
|--------|---------|
| 硬编码密钥/Token | 替换为 `<YOUR_API_KEY>` 占位符 |
| 内部 URL / localhost | 替换为 `<BASE_URL>` 占位符 |
| 个人数据（邮箱/手机） | 脱敏或使用示例数据 |
| 数据库连接串 | 密码部分替换为 `***` |
| 环境变量实际值 | 仅展示变量名，不展示值 |
| API 示例中的真实数据 | 使用 mock 数据替代 |

### 2.6 质量约束

遵循 `docs-author.md` 硬性规则：

- **单文件 < 500KB**：超过则拆分为独立文件（如 `index.html` + `assets/charts.js`）
- **独立 assets 目录**：每个文档有独立的 `assets/` 目录存放图表/图片
- **禁止 CDN 外链**：ECharts/Mermaid 优先本地引用（`_shared/js/`）
- **移动端适配**：响应式布局，表格支持横向滚动
- **版本同步**：文档版本号与代码版本保持一致，每个文档标注 `版本 + 更新日期`

### 2.7 生成后通知

HTML 报告生成完成后，告知用户报告路径，并提示：

> 设计文档 HTML 报告已生成：`docs/designs/<slug>/index.html`
> 可直接在浏览器中打开查看交互式可视化版本。
