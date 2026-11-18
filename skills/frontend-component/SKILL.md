---
name: frontend-component
version: v1.0.0
type: skill
enabled: true
mode: [standard, creator]
description: "开发新的 React 前端组件时使用。确保函数式组件、TypeScript 类型完整、样式使用 Tailwind 原子类。触发词: 组件、新建页面、写个组件、React。"
updated: 2026-08-13
depends_on: [ui-design]
composes: []
---
# Frontend Component


## 负责代理

`frontend-developer` — 前端组件开发由前端开发工程师代理负责，确保组件符合 React/TypeScript 规范。

## 何时使用

- 需要开发**新的 React 组件**时
- 需要拆分**过大的现有组件**时 (>300 行)
- 需要创建**可复用的 UI 组件**时
- 用户明确要求"写个组件"、"React 组件"时

**触发关键词**: "写组件"、"React"、"前端组件"、"UI组件"、"页面"

## 执行流程

### Step 1: 定义 Props 类型

使用 TypeScript Interface 定义组件接口，禁止使用 `any`:

```typescript
// src/components/SkillTree/SkillTree.types.ts
interface SkillNode {
  id: string;
  name: string;
  path: string;
  children?: SkillNode[];
  difficulty?: number;
}

interface SkillTreeProps {
  nodes: SkillNode[];
  onSelect?: (node: SkillNode) => void;
  selectedId?: string;
  loading?: boolean;
  className?: string;
}
```

### Step 2: 组件骨架

使用函数式组件 + Hooks，遵循单一职责:

```typescript
// src/components/SkillTree/SkillTree.tsx
import { useState, useCallback } from 'react';
import type { SkillTreeProps } from './SkillTree.types';
import { SkillTreeNode } from './SkillTreeNode';

export function SkillTree({ nodes, onSelect, selectedId, loading, className }: SkillTreeProps) {
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());

  const handleToggle = useCallback((nodeId: string) => {
    setExpandedIds(prev => {
      const next = new Set(prev);
      if (next.has(nodeId)) {
        next.delete(nodeId);
      } else {
        next.add(nodeId);
      }
      return next;
    });
  }, []);

  if (loading) {
    return <div className="animate-pulse space-y-2">加载中...</div>;
  }

  return (
    <div className={className} role="tree" aria-label="技能树">
      {nodes.map(node => (
        <SkillTreeNode
          key={node.id}
          node={node}
          expanded={expandedIds.has(node.id)}
          selected={selectedId === node.id}
          onToggle={handleToggle}
          onSelect={onSelect}
        />
      ))}
    </div>
  );
}
```

### Step 3: 样式 (Tailwind 原子类优先)

- **优先使用 Tailwind 原子类**
- 仅在复杂动画或 Tailwind 无法表达的样式时使用 CSS Module
- 禁止内联 style 对象 (除动态计算值)

```typescript
// 推荐: Tailwind 原子类
<div className="flex items-center gap-2 rounded-lg border border-gray-200 p-3 
  hover:bg-gray-50 transition-colors duration-200">

// 避免: 内联样式
<div style={{ display: 'flex', padding: '12px', borderRadius: '8px' }}>
```

### Step 4: 测试 (React Testing Library)

```typescript
// src/components/SkillTree/__tests__/SkillTree.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { SkillTree } from '../SkillTree';

const mockNodes: SkillNode[] = [
  {
    id: '1',
    name: 'Python基础',
    path: '/python/basics',
    children: [{ id: '2', name: '数据类型', path: '/python/basics/types' }],
  },
];

describe('SkillTree', () => {
  it('应渲染根节点', () => {
    render(<SkillTree nodes={mockNodes} />);
    expect(screen.getByText('Python基础')).toBeInTheDocument();
  });

  it('点击节点应触发 onSelect 回调', () => {
    const onSelect = vi.fn();
    render(<SkillTree nodes={mockNodes} onSelect={onSelect} />);
    fireEvent.click(screen.getByText('Python基础'));
    expect(onSelect).toHaveBeenCalledWith(mockNodes[0]);
  });

  it('loading 状态应显示加载指示器', () => {
    render(<SkillTree nodes={[]} loading />);
    expect(screen.getByText('加载中...')).toBeInTheDocument();
  });
});
```

### Step 5: Storybook (如适用)

对于可复用组件，编写 Storybook story:

```typescript
// src/components/SkillTree/SkillTree.stories.tsx
import type { Meta, StoryObj } from '@storybook/react';
import { SkillTree } from './SkillTree';

const meta: Meta<typeof SkillTree> = {
  title: 'Components/SkillTree',
  component: SkillTree,
};

export default meta;
type Story = StoryObj<typeof SkillTree>;

export const Default: Story = {
  args: { nodes: mockNodes },
};

export const Loading: Story = {
  args: { nodes: [], loading: true },
};
```

### Step 6: TanStack Query v5+ 使用规范

使用对象式调用语法，统一管理服务端状态:

```typescript
import { useQuery, useMutation, keepPreviousData } from '@tanstack/react-query';

// 查询 — 对象式参数 (v5+)
const { data, isPending, error } = useQuery({
  queryKey: ['skillNodes', { page: 1 }],
  queryFn: () => fetchSkillNodes({ page: 1 }),
  gcTime: 5 * 60 * 1000,
});

// 分页 — 使用 keepPreviousData
const { data: paginatedData, isPending: isLoading } = useQuery({
  queryKey: ['skillNodes', page],
  queryFn: () => fetchSkillNodes({ page }),
  placeholderData: keepPreviousData,
});

// 无限滚动
const { data, fetchNextPage, hasNextPage } = useInfiniteQuery({
  queryKey: ['infiniteNodes'],
  queryFn: ({ pageParam = 0 }) => fetchNodes(pageParam),
  initialPageParam: 0,
  getNextPageParam: (lastPage) => lastPage.next,
  maxPages: 5,
});

// 变更
const { mutate, isPending: isMutating } = useMutation({
  mutationFn: createSkillNode,
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['skillNodes'] });
  },
});
```

**v5+ 变更要点**:

| v4 选项 | v5+ 替代 | 说明 |
|---------|----------|------|
| `cacheTime` | `gcTime` | 更准确反映"垃圾回收时间"概念 |
| `useErrorBoundary` | `throwOnError` | 框架无关命名 |
| `keepPreviousData` | `placeholderData: keepPreviousData` | 使用内置工具函数 |
| `isLoading` | `isPending` | 状态命名更精确 |

## 硬性规则

- ✅ **函数式组件 + Hooks** — 禁止 Class 组件
- ✅ **TypeScript strict 模式** — 禁止 `any`，必须定义 Interface
- ✅ **超过 300 行必须拆分** — 单一职责原则
- ✅ **Tailwind 原子类优先** — 减少自定义 CSS
- ✅ **服务端状态**: 使用 **TanStack Query v5+** (对象式调用)
- ✅ **客户端状态**: 使用 **Zustand**
- ✅ **Props 必须定义类型** — 独立 `.types.ts` 文件
- ✅ **React 19 并发特性**: 使用 `useTransition` / `Suspense` 优化渲染（RSC 默认模式）
- ❌ 禁止使用 `any` 类型
- ❌ 禁止在 render 函数中执行副作用
- ❌ 禁止组件直接调用 API (使用 TanStack Query)
- ❌ 禁止超过 300 行不拆分
- ❌ 禁止使用 TanStack Query v4 旧版 API (位置参数)

## 反模式

- ❌ Class 组件 — 项目统一使用函数式组件
- ❌ `const props: any` — 丧失了 TypeScript 的类型保护
- ❌ 组件里 500 行代码 — 难以测试和维护
- ❌ `import './Component.css'` 全量引入 CSS — 优先使用 Tailwind
- ❌ 在组件里直接 fetch 数据 — 使用 TanStack Query 管理服务端状态
- ❌ useState 管理服务端数据 — 用 TanStack Query 代替
- ❌ useEffect 里写复杂业务逻辑 — 提取为自定义 Hook
- ❌ `useQuery(key, fn, options)` — 使用对象式调用 `useQuery({ queryKey, queryFn, ...options })
