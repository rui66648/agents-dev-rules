---
name: coding-standards
version: v1.1.0
type: rule
enabled: true
mode: [standard, creator]
updated: 2026-08-04
description: 编码规范 + 示例代码驱动模式
applies_to:
  agents: ['全部 Agent']
  phases: ['implementation']
  project_types: ['全部']
  tech_stacks: ['全部']
---
# 编码规范 (Coding Standards)

> **适用范围**: 通用编码原则 + **FastAPI/Python + React/TypeScript 实现子集**。框架无关原则（命名、函数长度、拆分阈值）适用于所有项目；具体语法示例（Pydantic、React Hooks、Tailwind）面向 FastAPI+React 技术栈，其他栈参照 `tech-stack.md` 等价映射。

本文件为 AI 编码代理的强制性编码规范，所有生成的代码必须严格遵守。

## Python 规范

- 严格遵循 PEP 8，使用 Ruff 格式化
- 所有公共函数和类**必须**声明 Type Hints
- 所有公共函数和类**必须**编写 Google Style Docstring
- 变量和函数命名使用 `snake_case`
- 类和异常命名使用 `PascalCase`
- 函数长度建议不超过 50 行
- 文件长度超过 300 行**必须**拆分

## TypeScript / React 规范

- **必须**开启 strict 模式
- **严禁**使用 `any` 类型，必须定义 Interface 或 Type
- 组件**必须**使用函数式组件 + Hooks，禁止 Class 组件
- **不使用 `React.FC` 类型**（React 19 已移除，纯函数组件即可）
- 变量和函数命名使用 `camelCase`
- 组件、接口、Type 命名使用 `PascalCase`
- 优先使用 `const` 而非 `let`
- 优先使用 Optional Chaining `?.` 和 Nullish Coalescing `??`
- 组件超过 300 行**必须**拆分为更小的子组件
- 样式优先使用 Tailwind 原子类

## 命名规范

- API 路由：`kebab-case`（如 `/skill-tree/path`）
- 数据库表名和列名：`snake_case`（如 `knowledge_relationships`）
- 环境变量：`UPPER_SNAKE_CASE`
- API JSON 字段：`camelCase`（如 `nodeName`、`createdAt`）

## 格式化工具

- 后端：Ruff（提交前自动检查，内置格式化功能）
- 前端：Prettier + ESLint（提交前自动检查）

---


## 示例代码驱动模式

> 用示例代码代替自然语言描述，是投入产出比最高的编码规范传递方式。以下为各层标准模板，AI 应优先参考这些模板而非文字描述。

### 前端页面组件模板

```tsx
// 1. 类型导入
import type { UserProfile } from '../types';

// 2. 组件导入
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../lib/api';

// 3. 组件定义（React 19 已废弃 React.FC，使用纯函数组件）
const UserProfilePage = () => {
  // 4. API 数据获取（API 集成层）
  const { data, isLoading, error } = useQuery({
    queryKey: ['user', 'profile'],
    queryFn: () => apiClient.get('/api/user/profile'),
  });

  // 5. 状态处理
  if (isLoading) return <div className="text-gray-400">加载中...</div>;
  if (error) return <div className="text-red-400">加载失败</div>;
  if (!data) return <div className="text-gray-400">暂无数据</div>;

  // 6. 渲染
  return <div className="p-4">{/* 页面内容 */}</div>;
};

export default UserProfilePage;
```

### 后端 API 路由模板

```python
# 1. 路由定义
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/example", tags=["example"])

@router.get("/items")
async def list_items(db: AsyncSession = Depends(get_db)):
    """获取所有项目"""
    service = ItemService(db)
    items = await service.get_all()
    return {"code": 0, "msg": "success", "data": items}
```

### 模板使用规则

- 每个项目可根据 tech-stack.md 中的技术栈修改模板细节
- 模板中的"API 集成层"部分是强制保留的，不可省略
- 前端组件模板中的"状态处理"（loading / error / empty）是强制保留的
- 后端模板中的标准 JSON 返回格式 {"code", "msg", "data"} 是强制保留的


## 禁止事项

- ❌ 提交未经格式化的代码
- ❌ 在 Python 中省略公共函数的 Type Hints 或 Docstring
- ❌ 在 TypeScript 中使用 `any` 类型
- ❌ 编写超过 300 行的单文件而不拆分
- ❌ 在 React 中使用 Class 组件
- ❌ 使用 `React.FC` 类型注解（React 19 已废弃）
- ❌ 命名风格混用（如 API 路由使用 camelCase）
