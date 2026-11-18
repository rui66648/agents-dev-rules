---
name: systematic-debugging
version: v1.0.0
type: skill
enabled: true
mode: [standard, creator]
description: "遇到 Bug、测试失败或异常行为时使用。强制执行四阶段调试法，确认根因后再修复。触发词: bug、报错、调试、排查、测试失败。"
updated: 2026-08-13
depends_on: [test-driven-development]
composes: []
---
# Systematic Debugging


## 负责代理

`architect` — 系统化调试由架构师代理负责，确保调试过程遵循四阶段法，根因明确。

## 何时使用

- 遇到**任何 Bug**或异常行为时
- **测试失败**需要诊断时
- 用户报告"这个不对"、"报错了"、"有问题"时
- 性能异常需要定位时

**触发关键词**: "Bug"、"报错"、"测试失败"、"不对劲"、"debug"、"排查"

## 执行流程

### Phase 1: Observe — 观察

**目标**: 收集关于问题的准确信息，而非猜测。

检查清单:
1. **错误信息**: 完整的错误堆栈、HTTP 状态码、日志输出
2. **复现条件**: 什么操作触发了问题？是否可以稳定复现？
3. **影响范围**: 影响哪些模块/接口/页面？是局部还是全局？
4. **时间线**: 是新引入的问题还是已有问题？最近有哪些变更？
5. **环境信息**: 本地/开发/生产？Python/Node 版本？数据库版本？

```bash
# 收集信息的常用命令
git log --oneline -10                    # 最近变更
git diff HEAD~1                          # 最近一次提交的变更
pytest tests/test_xxx.py -v --tb=long   # 详细测试输出
docker compose logs app --tail 50       # 应用日志
```

### Phase 2: Hypothesize — 假设

**目标**: 基于观察结果，列出可能的根因假设。

要求:
- 列出 **2-5 个**可能的根因假设
- 每个假设必须**可验证**
- 按可能性从高到低排序
- 标注每个假设的验证方法

示例:
1. **假设**: 数据库查询缺少 `selectinload`，导致 N+1 查询超时
   - 验证: 检查 SQLAlchemy 日志，确认查询次数
2. **假设**: Pydantic Schema 缺少必填字段验证
   - 验证: 检查 Schema 定义，用无效 payload 测试
3. **假设**: 前端状态更新竞态条件
   - 验证: 检查 useEffect 依赖数组，模拟快速连续操作

### Phase 3: Test — 验证假设

**目标**: 逐一验证假设，确认根因。

对每个假设:
1. 写一个**最小化复现测试** (如尚不存在)
2. 添加**诊断日志**或断点
3. 运行测试，观察结果
4. 记录: 确认 / 排除

```python
# 诊断示例: 添加日志确认假设
logger.debug("Query count: %d", len(queries))
logger.debug("Payload: %s", payload.model_dump())
```

**关键**: 验证结果必须明确排除或确认假设，不可模棱两可。

### Phase 4: Fix — 修复

**目标**: 仅针对已确认的根因进行修复。

修复原则:
- **最小修复**: 只修改确认有问题的代码
- **回归测试**: 修复后运行完整测试套件
- **编写回归测试**: 为此次 Bug 添加测试用例，防止回归
- **记录根因**: 在代码注释或 PR 中说明 Bug 根因

```python
# 修复后必须添加回归测试
@pytest.mark.asyncio
async def test_create_node_with_duplicate_path_should_raise_error(
    async_session: AsyncSession,
):
    """回归测试: 重复路径应抛出 409 错误"""
    await create_node(async_session, CreateSkillNodeRequest(name="A", path="/a"))
    with pytest.raises(AppException) as exc_info:
        await create_node(async_session, CreateSkillNodeRequest(name="B", path="/a"))
    assert exc_info.value.status_code == 409
```

## 硬性规则

- ✅ **先观察，再假设，再验证，最后修复** — 顺序不可颠倒
- ✅ 假设必须**可验证**且有明确的验证方法
- ✅ 修复后**必须编写回归测试**
- ✅ 修复后**必须运行完整测试套件**
- ✅ 必须记录 Bug 的**根因** (不仅仅是症状)
- ❌ **禁止试错式随机修改** (改改看、试试看)
- ❌ **禁止未确认根因就修复** (治标不治本)
- ❌ 禁止修复后不写回归测试
- ❌ 禁止在多个假设未验证时就修改代码

## 调试 Prompt 模板

> 以下 Prompt 模板可在调试阶段使用，帮助结构化问题排查。

### 标准报错分析模板

当遇到 Bug 或报错时，使用此模板收集信息：

```
我在 [技术栈] 项目中遇到以下报错：

错误信息：
[粘贴完整报错]

相关代码：
[粘贴相关代码片段]

我已经尝试过：
- [尝试1]
- [尝试2]

环境信息：[Node 20 / Next.js 15 / Python 3.13 等]

请帮我分析原因并给出解决方案。
```

### 最小复现模板

当问题难以定位时，要求 AI 帮助构建最小复现：

```
这个 Bug 的现象是：[描述现象]
期望行为：[期望什么]
实际行为：[实际发生了什么]

请帮我：
1. 写一个最小复现示例
2. 分析可能的原因（列出 2-5 个假设）
3. 给出验证每个假设的方法
```

### 调试节奏建议

个人项目推荐调试节奏：
1. **报错直接复制给 AI** — 完整错误堆栈比口头描述有效 10 倍
2. **说清"期望 vs 实际"** — 缩小 AI 的猜测范围
3. **让 AI 建议诊断手段** — 如"帮我加几个 console.log 确认数据流到哪一步"
4. **复杂问题让 AI 写最小复现** — 隔离问题，排除环境干扰

## 反模式

- ❌ "让我试试改这个" — 试错式调试，效率极低
- ❌ 看到报错直接 Google 粘贴答案 — 不理解根因
- ❌ 修了一个地方，另一个地方又坏了 — 没找到真正的根因
- ❌ Bug 修好了但不写回归测试 — 同样的 Bug 会再次出现
- ❌ 修改了 10 个文件才修好 — 修复范围过大，说明根因未确认
