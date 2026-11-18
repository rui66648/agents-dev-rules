---
name: skill-discovery
version: v1.1.0
type: rule
enabled: true
mode: [standard, creator]
updated: 2026-11-05
description: Skill 发现与触发指南 — 浏览器自动化能力路由（RULE-BROWSER）
applies_to:
  agents: ['all']
  phases: ['全程']
  project_types: ['全部']
  tech_stacks: ['全部']
---
# Skill 发现与触发指南

> 本章定义 Agent 在收到浏览器相关任务时，应如何选择合适的工具（Skill 能力）。
> 每个 skill 的能力声明均在 `skills/<skill-name>/SKILL.md` 的 `description` 字段，
> 以该 SKILL.md 为唯一事实来源；本文件仅做聚合索引。

## 浏览器自动化能力优先级

当任务涉及**浏览器交互 / 前端验收 / 网页操作**时，**必须按以下优先级选择工具**：

| 优先级 | 能力来源 | 适用场景 | 示例触发词 |
|--------|----------|---------|-----------|
| **P0（首选）** | `TRAE-browseruse` 技能 | 所有浏览器导航、截图、元素操作、E2E 验证 | "测试页面"、"打开 URL"、"截图"、"点击按钮" |
| **P1（仅 CI/本地 Chrome）** | `mcp_chrome-devtools` MCP 工具 | CI 环境无内置浏览器；需要本地 Chrome 开发者工具调试 | "连接本地 Chrome" |
| **P2（明确要求外部 CLI）** | `agent-browser` skill | 用户明确指定"用 agent-browser CLI"或脚本批量抓取 | "用 agent-browser 抓数据" |
| ❌ 禁止 | Playwright / puppeteer / selenium | 禁止自行安装/启动独立浏览器二进制 | — |

## 决策树

```
用户提到浏览器交互?
├── 是 → 是否明确要求外部 CLI 工具?
│   ├── 是 → agent-browser（需用户明示）
│   └── 否 → TRAE-browseruse（内置、零依赖、首选）
└── 否 → 按任务类型路由到对应 skill
```

## 规则约束

- **RULE-BROWSER**（`rules/testing-rules.md`）：测试相关的浏览器验证必须使用 TRAE-browseruse，禁止启动独立 Playwright/Chromium。
- `commands/test.md` 前置条件第 5 条：E2E 验证优先使用 TRAE-browseruse。
- **RULE-BROWSER-EXEC**（本文件）：**所有浏览器交互任务**（非仅测试场景）默认路由到 TRAE-browseruse；除非用户明确指令（如"用 agent-browser CLI"或"连接本地 Chrome"），否则禁止调用 agent-browser skill 或 chrome-devtools MCP。

## 各 Skill 的浏览器相关能力

见各 SKILL.md 的 `description` 字段。当前具备浏览器操作能力的 skill：

| Skill | 涉及浏览器操作 |
|-------|--------------|
| `TRAE-browseruse` | 全部浏览器自动化能力（导航、快照、点击、输入、截图、JS 执行） |
| `webapp-testing` | Web app 功能测试、UI 验证、截图对比 |
| `frontend-component` | 组件渲染验证（配合 TRAE-browseruse 做视觉验收） |
| `html-report` | 生成并预览 HTML 报告 |
| `html-document-center` | 文档中心的可视化预览 |

> **注意**：`agent-browser` 和 `chrome-devtools-mcp` 为平台内置能力，不在本仓库 `skills/` 目录中，其能力声明以平台文档为准。本规则要求：除非用户明确指定，否则一律优先使用 TRAE-browseruse。

> **平台可用性注记（v4.10.1）**：`TRAE-browseruse` 与 `webapp-testing` 为 TRAE 平台内置能力；在 DeepSeek Harness（DSH）等无内置浏览器的平台上，P0 首选工具不可用——此时按优先级降级到 P1 `mcp_chrome-devtools`（CI/本地 Chrome）或经用户明确指令使用外部工具，不得因工具缺失而跳过浏览器验证。
