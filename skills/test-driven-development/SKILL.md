---
name: test-driven-development
version: v1.1.1
type: skill
enabled: true
mode: [standard, creator]
description: "实现任何新功能或修复任何 Bug 前使用。强制执行 RED -> GREEN -> REFACTOR 循环，测试先行。触发词: TDD、测试先行、先写测试。"
updated: 2026-10-01
depends_on: [executing-plans]
composes: [refactoring, systematic-debugging, test-strategy]
interface:
  inputs: [feature_spec, tests]
  outputs: [passing_code, test_report]
---

# Test-Driven Development (TDD)


## 负责代理

`test-engineer` — TDD 测试驱动开发由测试工程师代理负责，确保 RED→GREEN→REFACTOR 循环。

## 何时使用

- 实现**任何新功能**之前
- 修复**任何 Bug**之前 (除 `systematic-debugging` 流程外)
- 需要为现有代码补充测试覆盖时
- 用户明确要求"写测试"、"TDD"时

**触发关键词**: "新功能"、"修复Bug"、"写测试"、"TDD"、"加个测试"

## 执行流程

### Phase 1: RED — 编写失败测试

**目标**: 写一个能编译/运行但会**失败**的测试，明确预期行为。

后端 (Pytest) 示例:

```python
# tests/test_skill_tree.py
import pytest

async def test_create_skill_node_should_return_created_node(
    async_session: AsyncSession,
):
    """创建技能节点应返回包含正确名称和路径的节点"""
    # Arrange
    payload = CreateSkillNodeRequest(name="Python基础", path="/python/basics")

    # Act
    result = await create_node(async_session, payload)

    # Assert
    assert result.name == "Python基础"
    assert result.path == "/python/basics"
    assert result.id is not None
```

前端 (React Testing Library + Vitest) 示例:

```typescript
// src/components/__tests__/SkillTree.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { SkillTree } from '../SkillTree';

describe('SkillTree', () => {
  it('应渲染技能节点并支持点击展开', async () => {
    render(<SkillTree nodes={mockNodes} />);

    const node = screen.getByText('Python基础');
    expect(node).toBeInTheDocument();

    fireEvent.click(node);
    const childNode = await screen.findByText('数据类型');
    expect(childNode).toBeInTheDocument();
  });
});
```

### Phase 2: GREEN — 最小实现

**目标**: 用**最少**的代码使测试通过，不追求完美。

> **UI 变更**：设计令牌语义校验（原 `design-token-linter`）已在 v4.0.0 随设计令牌约束一并简化；当前 UI 一致性由 RULE-036 的 `component-validator.py --full-check` 在生成后校验，不需要在 TDD 循环里额外运行令牌门禁。

**规则**:
- 只写刚好让测试通过的代码
- 可以写"丑"代码 (硬编码、重复) — Phase 3 会清理
- 禁止在此阶段重构
- **禁止跳过设计令牌校验**（UI 变更）

```python
# services/skill_tree_service.py — 最小实现
async def create_node(
    db: AsyncSession,
    payload: CreateSkillNodeRequest,
) -> SkillNode:
    node = SkillNode(name=payload.name, path=payload.path)
    db.add(node)
    await db.commit()
    return node
```

### Phase 3: REFACTOR — 重构

**目标**: 在测试全绿的前提下，改善代码质量。

检查清单:
- 消除重复代码
- 改善命名
- 提取公共方法
- 添加类型注解
- 优化数据库查询 (e.g. `selectinload`)
- 确保测试仍然全部通过

```python
# 重构后: 提取验证逻辑、添加日志、使用 selectinload
async def create_node(
    db: AsyncSession,
    payload: CreateSkillNodeRequest,
) -> SkillNode:
    _validate_node_path(payload.path)
    node = SkillNode(name=payload.name, path=payload.path)
    db.add(node)
    await db.flush()
    logger.info("Created skill node", node_id=node.id, path=payload.path)
    return node
```

### 循环

对每个功能点重复 RED -> GREEN -> REFACTOR:
1. 新功能点 -> RED (写失败测试)
2. 最小实现 -> GREEN
3. 测试全绿 -> REFACTOR
4. 回到步骤 1

## 硬性规则

- ✅ **先写测试，再写实现** — 顺序不可颠倒
- ✅ 每个功能至少对应**一个测试用例**
- ✅ **边界条件必须覆盖** (空值、越界、并发)
- ✅ 每次重构后确保**测试仍然全部通过**
- ✅ 测试命名遵循 `test_<行为>_<预期结果>` 格式
- ❌ **禁止先写实现再补测试** — 这不是 TDD
- ❌ 禁止跳过 RED 阶段直接写实现
- ❌ 禁止在 GREEN 阶段进行重构
- ❌ 禁止忽略失败的测试继续开发

## 测试生成 Prompt 模板

> 以下 Prompt 模板可在 RED 阶段使用，帮助快速生成高质量测试。

### 单元测试生成模板

```
帮我给以下 [函数/组件/接口] 写单元测试（用 [Pytest/Vitest]）：

[粘贴代码]

要求：
1. 覆盖正常路径（Happy Path）
2. 覆盖边界条件（空值、越界、零值）
3. 覆盖异常情况（参数错误、权限不足、超时）
4. 使用 describe/it 组织
5. 加上中文注释说明每个用例测什么
```

### 个人项目测试策略（务实版）

| 测试类型 | 覆盖要求 | 说明 |
|----------|----------|------|
| 核心业务逻辑 | **必须**写单测 | 支付、认证、数据处理等关键路径 |
| API 接口 | 手动测试 + 关键接口单测 | Postman/Thunder Client 手动验证 |
| 前端页面 | 手动点一遍关键流程 | 核心用户路径必须走通 |
| 工具函数 | 推荐写单测 | 纯函数测试成本低、价值高 |

> **不必追求覆盖率**：个人项目抓住核心路径即可，覆盖率 60%+ 已优于大多数团队项目。

## 反模式

- ❌ "先写完功能再补测试" — 丧失了 TDD 的设计驱动价值
- ❌ 测试只覆盖 happy path — 边界条件是 Bug 的温床
- ❌ 写了 10 个实现才写 1 个测试 — 覆盖率严重不足
- ❌ 测试与实现高度耦合 (mock 了所有依赖) — 重构时测试跟着碎
- ❌ 不运行测试就声称"应该没问题" — 假设不是证据
