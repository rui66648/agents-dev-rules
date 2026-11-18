---
name: testing-rules
version: v1.1.4
type: rule
enabled: true
mode: [standard, creator]
updated: 2026-11-11
description: 测试规则 — TDD 强制（RULE-003）、覆盖率目标、测试编写规范（RULE-013；RED 用例译自 spec 验收场景）
applies_to:
  agents: ['test-engineer', 'code-reviewer']
  phases: ['5', '6']
  project_types: ['全部']
  tech_stacks: ['全部']
---
# 测试规则 (Testing Rules)
> **本文件落实**: RULE-003（TDD 强制：RED → GREEN → REFACTOR）、RULE-013（不要跳过测试声称"完成"）

> **适用范围**: 本文包含通用架构原则和 FastAPI+React 项目特定实践。通用原则适用于所有项目，项目特定实践以 `[项目特定]` 标注，具体配置以项目根目录 `tech-stack.md` 为准。

本文件定义项目中必须遵守的测试规范，AI 编码代理必须为所有新功能编写测试。

> **确定性强制现状**：RULE-013 目前**没有自动阻断**。`hooks/scripts/post-test.js` 只是 PostToolUse 钩子（且在四仓均未挂载），PostToolUse 退出码不能回滚已执行的测试命令；它最多把失败输出回传给 Agent，不构成"禁止声称完成"的强制。实际约束靠人工核对 CI/本地测试结果，覆盖率阈值由 `--cov-fail-under` 在 CI 中强制；状态以 `rules/cicd-rules.md §门禁现状` 为准。

## TDD 的输入来自规格（v1.1.3，ADR-008）

RED 阶段写测试时，**测试用例直接翻译自 spec 的 Acceptance 场景**，不再由实现者自行脑补：

| spec 元素 | 变成什么 |
|-----------|---------|
| 验收场景（Given/When/Then 或 EARS） | 一个或多个测试用例（正例） |
| `Edge Cases` / 边界描述 | 异常路径与边界测试 |
| FR-001 的 "MUST/SHALL" | 断言的具体期望值 |
| 可度量成功标准 | 性能/契约测试的阈值 |

> 这条同时修掉一个老问题：以前 TDD 的"先写测试"缺少确定输入，测试容易写成对实现的复述。
> 现在**测试是 spec 的可执行投影**——spec 改了，测试必须同批改（RULE-055 §4）。

## 基本原则

- 所有新功能**必须**配备对应测试
- 代码覆盖率目标：**个人项目 ≥ 60%，团队项目 ≥ 80%**（RULE-013 注释以本文为准）
- 测试是代码完成的标准之一，**禁止**跳过测试声称"完成"

## 后端测试 (Pytest)

<!-- [项目特定] -->
- 使用 `pytest` 作为测试框架
- 异步代码使用 `pytest-asyncio`
- 测试文件命名为 `test_xxx.py`
- 测试函数命名为 `test_xxx`
- **必须**覆盖：正常路径 (happy path) + 异常路径 (error path) + 边界情况 (edge cases)
- Mock 所有外部依赖（数据库、API 调用、文件系统）

### 边界测试要求（按实际风险决定）

**不要机械套用固定清单**。是否测试空值、极值、类型错误、并发、网络异常，取决于被测逻辑**是否真的存在该边界**：

- 有外部输入/解析 → 覆盖空值与类型错误
- 有算术/容量约束 → 覆盖极值
- 有共享状态/并发写 → 覆盖并发
- 有外部依赖调用 → 覆盖超时与失败路径

无对应风险的函数不必为凑清单编写无意义测试（RULE-015 YAGNI）。

## 前端测试 (React Testing Library + Vitest)

<!-- [项目特定] -->
- 使用 `React Testing Library` 测试组件行为
- 使用 `Vitest` 作为测试运行器
- 测试文件放置在 `__tests__/` 目录或与源文件同目录下，命名为 `.test.ts` / `.test.tsx`
- **必须**测试用户交互行为，而非实现细节
- Mock API 调用和外部模块

## 测试编写规范

- 测试名称**必须**描述行为，而非实现细节

```
# 正确
def test_user_login_with_valid_credentials_returns_token():
    ...

def test_user_login_with_wrong_password_returns_401():
    ...

# 错误
def test_login_function():
    ...
```

- 遵循 AAA 模式：**Arrange（准备） -> Act（执行） -> Assert（断言）**
- 每个测试只验证一个行为
- 测试之间**禁止**共享状态
- 测试**必须**独立，可以任意顺序运行
- 使用 Fixture 管理测试数据和测试环境

## 浏览器自动化优先级（内置 TRAE-browseruse 优先）

### RULE-BROWSER：禁用独立安装的 Playwright / puppeteer / selenium 启动外部浏览器

当涉及 E2E 浏览器交互或前端 UI 验证时，**必须优先使用内置 TRAE-browseruse**（`browser_navigate`、`browser_snapshot`、`browser_click`、`browser_type` 等工具），禁止以下做法：

| 行为 | 原因 |
|------|------|
| ❌ 使用 `npx playwright` / `npx vitest --browser` 启动独立 Chromium | 需安装浏览器二进制，跨环境不稳定，与平台内置能力重复 |
| ❌ 通过 `@playwright/test`、`selenium`、`puppeteer` 自行驱动浏览器 | 引入第三方依赖、额外安装步骤、端口占用 |
| ❌ 通过 `chrome-devtools` MCP 直接操作用户本地 Chrome 实例 | 干扰用户浏览器、污染会话状态 |
| ✅ 使用 `browser_snapshot` + `browser_click` 完成交互验证 | 平台内置、无依赖、可截图、无需安装 |
| ✅ 使用 `browser_navigate` + `browser_evaluate` 完成数据提取 | 沙箱隔离、稳定可复现 |
| ✅ 需要完整截图时使用 `browser_take_screenshot` 并调用 `image()` | 视觉验收、无障碍基线 |

**例外**（允许使用 Playwright 的场景）：
1. CI 环境无 TRAE-browseruse 可用（如外部 GitHub Actions runner）
2. 需要录制视频 / HAR 日志等高级分析能力
3. 被测应用为 Electron / PWA 等无法通过浏览器工具访问的形态

### 前端 UI 验收（替代原生 Playwright E2E）

对于涉及"测试 UI 组件渲染 / 交互反馈 / 路由跳转"的场景，**用 TRAE-browseruse 替代 Playwright E2E**：

1. `browser_navigate({ url: "http://localhost:5173" })` 启动本地 dev server
2. `browser_snapshot()` 获取页面可访问性树，定位 `[ref=N]`
3. `browser_click({ ref: "N" })` / `browser_type({ ref: "N", text: "..." })` 完成交互
4. `browser_take_screenshot()` 截取视觉基准图，后续用 `image()` 人工/自动化对比

> **成本收益**：TRAE-browseruse 每次 snapshot 极低，screenshot 较高；优先 snapshot，仅在需要视觉验收时再截图。

---

## 禁止事项

- ❌ 跳过测试声称功能"完成"
- ❌ 编写跳过断言的"空测试"
- ❌ 测试之间共享可变状态
- ❌ 一个测试验证多个不相关的行为
- ❌ 测试命名描述实现而非行为
- ❌ 在测试中硬编码不可变的外部依赖（如真实 API 地址）
- ❌ 忽略失败的测试

---

## 契约测试与 E2E

### 契约测试（后端）
- **工具**：Schemathesis（MIT）+ Pact（MIT，跨语言）
- **位置**：CI 的 test 阶段
- **职责**：基于 OpenAPI 规范进行属性化测试（fuzz）；验证微服务间契约不被破坏
- **强制级别**：涉及多服务交互或对外公开 API 时必须加入

### E2E（前端）
- **首选工具**：TRAE-browseruse（`browser_navigate` + `browser_snapshot` + `browser_click` / `browser_type`，内置、无依赖、无需安装浏览器二进制）
- **备选工具**：Playwright（Apache-2.0，微软维护），仅限 CI 外部 runner 或 Electron/PWA 等无法通过 TRAE-browseruse 访问的场景
- **位置**：CI 的 test 阶段（后端启动后执行）
- **职责**：完整用户流程（登录 → 创建 → 查看 → 编辑 → 删除）
- **强制级别**：包含关键业务路径（登录、支付、核心 CRUD）时必须加入
- **前置**：必须先评估 TRAE-browseruse 是否可用；不可用时才降级到 Playwright，并在 PR 中说明原因

### 视觉回归（可选）
- **工具**：Chromatic（MIT，Storybook 官方）或 Loki（MIT，开源版）
- **位置**：CI 的 test 阶段后
- **职责**：UI 组件截图对比，防止样式意外破坏
- **使用场景**：组件库或设计系统项目