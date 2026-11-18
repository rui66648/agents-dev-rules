---
name: open-source-first
version: v3.7.0
type: rule
enabled: true
mode: [standard, creator]
updated: 2026-11-11
description: "开源优先规则 — 选型决策、License 合规、ADR 模板、AI 自主选型边界、插件组装原则、Cordis 框架优先（RULE-051）；原第 9–15 节参考资料已拆出至 docs/reference/open-source-catalog.md"
applies_to:
  agents: ['architect', 'backend-developer', 'frontend-developer', 'database-expert']
  phases: ['design', 'implementation']
  project_types: ['全部']
  tech_stacks: ['全部']
---

# 开源优先与插件组装规则 (Open Source First & Plugin Assembly)

> **本文件落实**: RULE-017（优先采用开源优秀方案，禁止无理由自研）、RULE-018（引入新依赖前必须检查 License 合规）、RULE-019（选型决策必须写 ADR 记录"为什么不选其他方案"）、RULE-042（插件组装优先）、**RULE-051（Cordis 框架优先）**
> **另引用** RULE-043（插件清单合规）——其落点是 `docs/guides/plugin-manifest-standard.md`，本文件只提供选型侧要求

> **核心理念**：凡能用开源组件或插件解决的能力，禁止自研。通过配置组装能力，而非修改代码扩展能力。
>
> **框架基座优先（RULE-051）**：涉及 Agent 运行时能力（插件挂载/卸载、工具注册与路由、沙箱执行、会话与 Trajectory 日志、多模式 presets、子代理编排）时，**优先采用 DeepSeek Harness 的 Cordis 框架及其官方 `@deepseek-ai/dsh-*` 插件**，不得无理由自建等价内核。详见下文总纲与 14.2 节。

## Cordis 框架优先总纲（RULE-051）

> **决策**见 `docs/decisions/ADR-005-cordis-framework-first.md`。本节约束"优先"的边界，避免与"薄封装"策略（13 节）冲突。

### 适用能力域（必须优先 Cordis）

| 能力域 | 优先方案 | 说明 |
|--------|---------|------|
| 插件挂载/卸载/依赖管理 | `dsh-cordis`（Cordis kernel） | 取代自建 `plugin_manager.py` 类实现 |
| 工具注册 + 路由 + 审批 | Cordis ToolRegistry 机制 | 取代自建注册表 |
| 沙箱执行 | `dsh-sandbox`（bwrap / Landlock / Seatbelt） | 取代自研 `safe_bash` 白名单方案 |
| 会话持久化 + 轨迹 | `dsh-session` + `dsh-trajectory`（append-only, Resume/Fork/Search/Replay） | 取代自建 JSONL 日志 |
| 多模式运行 | `dsh-preset`（Standard / Code / Minimal / Creator） | 与本项目 `presets/` 目录同构，直接对齐 |
| 子代理编排 | `dsh-subagent` | 取代自建 spawn/wait 逻辑 |
| 插件打包分发 | `dsh-bundle` | 取代自建 bundle 格式 |

### 允许自建（不视为违反 RULE-051）的情形

1. **技术栈不兼容**：目标组件为纯 Python/其他语言服务进程，无法承载 Node/TS 运行时 → 记录 ADR 后沿用 13 节"薄封装"策略。
2. **Cordis 无对应能力**：查 `plugins/registry.yaml` 与官方 42 包清单后确认缺口 → 按 L2/L3 选开源库，并写 ADR。
3. **Preview 稳定性风险实测命中**：`@deepseek-ai/dsh-*` 仍处 developer preview，若升级造成破坏性变更且无法通过版本固定规避 → 记录 ADR 后可临时退回自建，并标注 `@deprecated` 待回收。

> **强制规则**：跳过 Cordis 直接自建上述任一能力域，必须在 `docs/decisions/` 写 ADR 说明理由。**当前无自动阻断**：`plugin-validator.py` 只校验插件清单，不检查 ADR；由 code review 人工核对，PR 描述须附 ADR 链接。

## 1. 决策层级（优先级从高到低）

| 层级           | 策略                                      | 适用场景           | 示例                         |
| ------------ | --------------------------------------- | -------------- | -------------------------- |
| **L1: 复用已有** | 复用项目内已有的 skill/rule/plugin（含 `cordis.yaml` 已启用插件） | 内部能力已满足需求      | 复用 `skills/code-review`    |
| **L2: 开源组件** | 引入成熟开源库/框架                              | 无内部能力，开源方案成熟   | 引入成熟的追踪/观测库（示例仅示意，不指定产品） |
| **L3: 开源插件** | **优先 DeepSeek Harness / Cordis 插件（`@deepseek-ai/dsh-*`，MIT）**；其次其他开源插件系统（MCP Servers、LangChain Tools） | 需要标准化接口、或命中 RULE-051 总纲 Agent 运行时能力域 | 用 `dsh-sandbox` 做沙箱、`dsh-cordis` 做挂载 |
| **L4: 自建插件** | 自研但遵循插件接口规范                             | 无开源方案，必须自研     | 自定义 `brainstorming` 技能     |
| **L5: 硬编码**  | 直接在代码中实现                                | 以上均不可行，且为一次性逻辑 | 临时脚本                       |

> **强制规则**：必须按 L1→L5 顺序评估，跳过任意层级必须记录 ADR 理由。Agent 运行时能力域（见上文 RULE-051 总纲）跳过 L3 的 Cordis/DSH 直接进 L4 自建，同样必须记录 ADR。

## 2. 插件组装原则

### 2.1 插件定义

**插件（Plugin）** 是具备以下特征的能力单元：

- ✅ 有明确的输入/输出接口（Interface）

- ✅ 可独立安装/卸载（Mount/Unmount）

- ✅ 可通过配置启用/禁用（Config-driven）

- ✅ 不修改核心代码即可扩展（Extensible without Forking）

### 2.2 组装 vs 修改

| 方式                   | 定义         | 适用场景         | 示例                                          |
| -------------------- | ---------- | ------------ | ------------------------------------------- |
| **组装（Assembly）**     | 通过配置组合现有插件 | 能力需求可由现有插件满足 | `cordis.yaml` 启用 `fs-local` + `shell-local` |
| **修改（Modification）** | 修改核心代码添加能力 | 无现有插件，必须自研   | 修改 `agent-loop.py` 添加新功能                    |

> **强制规则**：优先组装，禁止修改。仅在 L1-L3 均不可行时允许 L4/L5。

### 2.3 插件发现机制

开发新能力时，按以下顺序搜索：

```
1. 项目内已有插件（skills/, plugins/）
   ↓ 未找到
2. 开源插件市场（GitHub Topics、PyPI、npm）
   ↓ 未找到
3. MCP Server Registry（modelcontextprotocol.io）
   ↓ 未找到
4. LangChain Tool 生态
   ↓ 未找到
5. 自建插件（遵循插件接口规范）
```

## 3. License 合规（强制）

### 白名单（可放心使用）

| License          | 商用 | 修改 | 分发      | 备注           |
| ---------------- | -- | -- | ------- | ------------ |
| MIT              | ✅  | ✅  | ✅       | 最宽松，首选       |
| Apache-2.0       | ✅  | ✅  | ✅       | 含专利授权        |
| BSD-2/3-Clause   | ✅  | ✅  | ✅       | 与 MIT 几乎等价   |
| MPL-2.0          | ✅  | ✅  | ✅（修改部分） | 文件级 Copyleft |
| ISC              | ✅  | ✅  | ✅       | 与 BSD 等价     |
| Unlicense / 0BSD | ✅  | ✅  | ✅       | 公有领域         |

### 黑名单（禁止引入）

| License                    | 风险         | 替代                                |
| -------------------------- | ---------- | --------------------------------- |
| **AGPL-3.0**               | 网络服务也须开源   | Apache-2.0 / MIT 同类               |
| **SSPL**                   | 服务端也须开源    | MongoDB→PostgreSQL；搜索→Meilisearch |
| **BSL / Source-Available** | 非 OSI 认可   | 评估商业版或换替代                         |
| **GPL-2.0/3.0（未隔离）**       | 强 Copyleft | 隔离为独立进程或换替代                       |

> **Rule 强制**：引入任何依赖前，CI 中执行 License 扫描（`pip-licenses` + `license-checker`），发现黑名单 License **必须阻断合并**。

## 4. AI 自主选型边界

> **核心原则**：规则只定**边界**与**流程**，**不指定具体技术**。具体选型由 AI 在框架内判断。

### 4.1 选型决策流程（强制）

```
需求分析 → L1-L5 评估 → 候选方案 ≥ 2 → ADR 记录 → 人工审批 → 实施
    ↓           ↓           ↓           ↓           ↓
 明确需求    按优先级搜索   对比优劣    说明取舍    记录偏差
```

### 4.2 AI 必须自主决定的（规则不写死）

- 设计系统（shadcn/ui / Ant / Material 3 / Chakra / Radix / HeroUI / Mantine 等）

- 组件库、图标库、字体、图表库

- 状态管理、表单方案、动画方案

- 数据库、ORM、缓存、消息队列

- 测试框架、Mock 工具、CI/CD 平台

- **可观测性栈**（OpenTelemetry / Jaeger / Prometheus / Grafana 等）

- **工作流引擎**（Prefect / Airflow / Luigi 等）

- **插件系统**（MCP / LangChain Tools / 自研插件等）

### 4.3 AI 必须遵守的硬性约束

1. **必须按 L1-L5 顺序评估** — 不得跳过层级直接自研
2. **必须用开源方案** — 不得默认推荐商业 SaaS（除非用户明确指定）
3. **必须记录 ADR** — 选型落地前在 `docs/decisions/NNN-xxx.md` 写决策记录
4. **必须评估 License** — 黑名单禁止；白名单放心；其他需人工审查
5. **必须考虑成熟度** — 首发 < 6 个月的项目不得作为核心依赖
6. **不得指定单一方案** — 必须给出 ≥ 2 个候选并说明取舍
7. **必须优先组装** — 能通过配置组合现有插件解决的问题，不得修改核心代码

## 5. ADR（Architecture Decision Record）模板

```markdown
# ADR-NNN: [决策标题]

## 状态
Proposed | Accepted | Deprecated | Superseded by ADR-XXX

## 背景
[什么问题需要决策？约束是什么？]

## 候选方案（L1-L5 评估）
| 层级 | 方案 | License | 成熟度 | 优势 | 劣势 |
|------|------|---------|--------|------|------|
| L1 | 复用已有 xxx | MIT | 高 | 无新依赖 | 能力不匹配 |
| L2 | 引入开源库 yyy | Apache-2.0 | 高 | 社区活跃 | 学习成本 |
| L3 | MCP Server zzz | MIT | 中 | 标准化接口 | 生态不成熟 |
| L4 | 自建插件 | MIT | — | 完全可控 | 维护成本 |
| L5 | 硬编码 | — | — | 快速实现 | 不可复用 |

## 决策
选择 [方案 X]（L[X]），理由：...

## 组装 vs 修改
- 方式：组装 / 修改
- 说明：通过配置组合现有插件，无需修改核心代码

## 后果
- 正面：...
- 负面：...
- 风险：...
```

## 6. 前端 UI 选型专项（参考 `rules/ui-design-patterns.md`）

AI 在做前端 UI 选型时，必须遵守：

### 6.1 UI 专项 ADR 模板

```markdown
# ADR-NNN: [决策标题]

## 状态
Proposed | Accepted | Deprecated | Superseded by ADR-XXX

## 背景
[什么问题需要决策？约束是什么？]

## 候选方案
| 方案 | License | 成熟度 | 优势 | 劣势 |
|------|---------|--------|------|------|
| A | MIT | 高 | ... | ... |
| B | Apache-2.0 | 中 | ... | ... |
| C（商业 SaaS） | 专有 | — | ... | ... |

## 决策
选择 [方案 X]，理由：...

## 后果
- 正面：...
- 负面：...
- 风险：...
```

### 6.2 选型约束

1. **设计系统**：从开源设计系统中选择（shadcn/ui / Ant Design / Material Design 3 / Chakra UI / Radix UI / HeroUI / Mantine / Park UI）
2. **原子级 UI 素材库**：[Uiverse.io](https://uiverse.io)（MIT，7300+ 元素，支持 HTML/CSS/Tailwind/React/Figma）可用于快速复用单点元素（按钮、卡片、加载器、表单等）。**本仓库** **`components/`** **已落地 10 个组件并配套** **`docs/ui-component-guide.md`** **复用/获取流程，应优先复用而非重新引入**（注意 galaxy 仓库 2024-09 已停止更新，新组件需从网站提取）
3. **图标**：从开源图标库中选择（Lucide / Tabler / Phosphor / Hugeicons），不得混用多个图标库
4. **字体**：中文项目必须包含 Noto Sans CJK SC；西文优先 Inter / Geist
5. **图表**：简单场景用 Recharts；复杂场景用 Apache ECharts 或 AntV G2/G6；不得混用 ≥ 2 个图表库
6. **表单**：React Hook Form + Zod 是默认基线
7. **状态**：服务端状态用 TanStack Query；客户端状态用 Zustand / Jotai
8. **动画**：motion（原 Framer Motion）或 CSS-only；必须尊重 `prefers-reduced-motion`
9. **Mock**：MSW 优先于 json-server
10. **可访问性**：所选方案必须支持 WCAG 2.1 AA（对比度 ≥ 4.5:1、键盘导航）

> **执行原则**：以上是"方向"，不是"清单"。AI 应基于**项目具体场景**（管理后台 / 数据大屏 / 移动端 / 富文本编辑器 / 实时协作等）从开源生态中选型，并在 ADR 中说明理由。

## 7. 反模式

- ❌ 在规则中钉死单一技术栈（"必须用 React"）—— 规则只定原则，不指定实现

- ❌ AI 直接自研组件库 / 工具函数 / 工具库 —— 优先引入成熟开源方案

- ❌ 选型时只给"为什么选 X"，不写"为什么不选 Y/Z" —— 必须有对比

- ❌ 把商业 SaaS 当默认推荐（个人项目优先自托管开源）

- ❌ 引入 License 不明或黑名单依赖

- ❌ 在没有评估替代的情况下重复造轮子

## 8. 禁止事项

- ❌ 禁止引入 AGPL / SSPL / BSL / 非 OSI License 依赖（除非用户明确豁免）

- ❌ 禁止在 ADR 中省略"为什么不选其他方案"

- ❌ 禁止把"将来可能用到"作为选型理由（违反 YAGNI，见 `engineering-principles.md`）

- ❌ 禁止自研已有 ≥ 3 个成熟开源方案的能力（优先复用）
## 9. 参考资料（已拆出）

> 原第 9–15 节（开源替代速查表、文档站点、备份灾备、图计算栈、原子级开源库推荐、Codex CLI / DeepSeek Harness 评估、技术选型 ADR 模板）已拆分为参考文档：[docs/reference/open-source-catalog.md](../docs/reference/open-source-catalog.md)。
>
> 本规则正文只保留**强制决策层级、License 合规、AI 选型边界、ADR 模板与禁止事项**。

## 16. 版本历史

| 版本         | 日期             | 变更内容                                                                                                                                          |
| ---------- | -------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| **v3.6.2** | **2026-11-05** | **版本历史表补记 v3.6.0/v3.6.1 条目（此前漏记，变更正文未逐条留痕以当日 git diff 为准）；frontmatter 随本轮一致性修复批升至 v3.6.2（正文无语义变更）** |
| **v3.6.1** | **2026-11-04** | **frontmatter 版本同步（本表此前漏记 v3.6.x 条目，2026-11-05 补记；变更正文未逐条留痕，以该日 git diff 为准）** |
| **v3.6.0** | **2026-10-01** | **第 9–15 节参考资料拆出至 docs/reference/open-source-catalog.md（ADR-007 精简批次），正文收敛为决策层级/License/ADR 模板**                        |
| **v3.5.0** | **2026-09-13** | **新增 RULE-051「Cordis 框架优先」：Agent 运行时能力域（插件挂载/工具路由/沙箱/会话+Trajectory/presets/子代理/bundle）优先直接采用 DeepSeek Harness 的 Cordis 框架与 `@deepseek-ai/dsh-*` 插件；修订 14.2/14.3/14.4 旧"仅供学习、不推荐套用"口径；配套 ADR-005** |
| v2.0.0     | 2026-08-15     | 新增 RULE-042 插件组装优先、L1-L5 决策层级                                                                                                                 |
| v3.0.0     | 2026-08-28     | 新增"原子级开源库推荐"章节（13 节），18 个决策问题，禁止引入清单                                                                                                          |
| **v3.4.0** | **2026-08-30** | **新增 DeepSeek Harness 工具写入问题排查指南；补充 Codex CLI 28 个原子工具完整清单（修正从 18 到 28 个）；新增工具写入问题排查步骤（权限/只读/Git 占用）**                                        |
| **v3.3.0** | **2026-08-30** | **新增 Codex CLI 28 个原子级工具清单（v0.136）：文件 I/O/编辑/搜索/执行/网络/多智能体等完整分类；补充架构亮点（ToolRegistry+ToolRouter、V4A Patch、Multi-Agent v2）；更正开源协议为 Apache-2.0** |
| v3.2.0     | 2026-08-30     | 新增 DeepSeek Harness 42 个原子级 npm 包清单：按 9 大能力域分类，每个包标注核心职责与对应项目实现；新增循环守卫借鉴点                                                                     |
| v3.1.0     | 2026-08-29     | 新增"框架级参考实现评估"章节（14 节）：Codex CLI + DeepSeek Harness 完整评估；新增技术选型 ADR 记录模板（15 节）；更正 DeepSeek Harness 开源状态（MIT，2026-08-13 发布）                     |

