---
name: test
version: v1.1.0
type: command
enabled: true
mode: [standard, creator]
updated: 2026-11-07
description: 斜杠命令：test - "运行测试"、"测试一下"、"pytest"、"vitest"；TDD 的 RED 用例译自 spec 验收场景
---
# /test - 测试流程

**触发词**: "运行测试"、"测试一下"、"pytest"、"vitest"

---

## 命令语法

```
/test [target] [--type=unit|integration|e2e|all] [--coverage=false|true] [--watch=false|true]
```

## 参数说明

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `target` | string | 否 | 全部 | 测试目标：模块路径、文件路径、或测试函数名（支持模糊匹配） |
| `--type` | enum | 否 | `all` | 测试类型：`unit`（单元）、`integration`（集成）、`e2e`（端到端）、`all`（全部） |
| `--coverage` | bool | 否 | `true` | 是否生成覆盖率报告 |
| `--watch` | bool | 否 | `false` | 是否开启监听模式（文件变更自动重跑） |

## 触发场景

- 功能开发完成后，验证代码正确性
- Bug 修复后，确认修复有效且未引入回归问题
- 代码审查前，确保所有测试通过
- 持续集成流水线中，自动化质量门禁
- 重构后，验证行为一致性
- 编写测试用例时，TDD 循环中的 RED/GREEN 阶段
- **TDD RED 阶段用例来源（ADR-008）**：直接翻译 `docs/tasks/<id>/spec.md` 的验收场景与 FR，
  不靠实现者脑补边界

## 前置条件

1. 测试依赖已安装（`pytest`、`vitest` 等）
2. 数据库（如需要）已启动且测试数据可写入
3. `.env.test` 或测试环境配置已就绪
4. 待测试代码已保存到文件系统（非仅内存中）
5. **L2/L3**：spec 的验收场景已读（本批测试要覆盖哪些场景应在动手前明确）
6. **浏览器自动化优先**：涉及 UI/E2E 验证时，必须使用内置 `TRAE-browseruse`（`browser_navigate`/`browser_snapshot`/`browser_click`），禁止启动独立 Playwright/Chromium 进程；详见 `rules/skill-discovery.md` RULE-BROWSER-EXEC

## 执行流程

1. **环境检查** — 确认测试框架、依赖、数据库状态就绪
2. **范围确定** — 根据 `target` 和 `--type` 确定测试范围
3. **测试执行** — 按层级顺序运行：单元测试 -> 集成测试 -> E2E 测试
4. **结果收集** — 收集测试结果、失败详情、执行时间
5. **覆盖率分析** — 如 `--coverage=true`，生成覆盖率报告并识别未覆盖代码
6. **失败诊断** — 对失败用例进行根因分析，输出错误堆栈与上下文
7. **报告输出** — 汇总测试通过/失败数量、覆盖率百分比、建议补充的测试项

## 产出物

- **测试结果报告**：通过/失败数量、执行时间、失败用例详情
- **覆盖率报告**：整体覆盖率、各模块覆盖率、未覆盖代码行号
- **失败诊断**：失败用例的错误信息、堆栈跟踪、建议修复方向
- **回归分析**：与上次测试结果的对比，新增失败/修复情况

## 错误处理

| 常见错误 | 处理方式 |
|----------|----------|
| 测试框架未安装 | 提示安装依赖：`pip install pytest pytest-asyncio` 或 `npm install vitest` |
| 数据库连接失败 | 检查 `.env.test` 配置，确认测试数据库已启动 |
| 测试覆盖率低于 80% | 标记为不通过，输出未覆盖代码列表，要求补充测试 |
| 测试用例执行顺序依赖失败 | 标记为测试代码问题，要求移除顺序依赖 |
| 超时（>300s） | 标记超时测试，建议优化或拆分 |
| E2E 测试浏览器启动失败 | 检查 Playwright 浏览器安装状态，提示执行 `npx playwright install` |

## 示例

### 示例 1：运行全部测试并生成覆盖率报告

```
/test --type=all --coverage=true
```

**预期输出**：
- 单元测试：45/45 通过
- 集成测试：12/12 通过
- 覆盖率：后端 87%，前端 82%
- 未覆盖代码：`src/utils/helpers.py` 第 23-30 行

### 示例 2：监听模式运行用户模块单元测试

```
/test user --type=unit --watch=true
```

**预期输出**：
- 监听 `src/modules/user/` 目录下的文件变更
- 变更后自动重跑相关测试
- 实时反馈测试结果

---

**执行流程**: 遵循 [test-driven-development 技能](skills/test-driven-development/SKILL.md`) 的完整流程

**产出物**: 测试结果报告 + 覆盖率分析 + 失败用例详情
