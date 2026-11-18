---
name: api-design
version: v1.0.0
type: skill
enabled: true
mode: [standard, creator]
description: "system-design 完成后设计 API 接口时使用。确保 RESTful 风格、统一响应格式、Pydantic Schema 同步更新，输出接口设计文档。触发词: API、接口设计、端点、REST、Schema。"
updated: 2026-08-13
depends_on: [system-design]
composes: [database-migration, writing-plans]
---
# API Design

## 负责代理

`backend-developer` — API 接口设计涉及后端架构、路由定义和 Pydantic Schema，由后端开发工程师代理负责。

## 何时使用

- 需要设计**新的 API 接口**时
- 需要修改**现有接口**的请求/响应格式时
- 需要新增**路由端点**时
- 需要定义或更新 **Pydantic Schema** 时

**触发关键词**: "新接口"、"加个API"、"设计接口"、"路由"、"endpoint"

## 执行流程

### Phase 1: 设计阶段（输出 api-design.md）

**目标**: 在编码前完成完整的 API 接口设计文档。

#### Step 1: 接口清单总表

基于 `system-design` 输出的架构和数据库设计，梳理所有接口：

| 模块 | 路径 | 方法 | 说明 | 认证 | 权限 |
|------|------|------|------|------|------|
| 认证 | /api/v1/auth/login | POST | 用户登录 | 否 | — |
| 认证 | /api/v1/auth/register | POST | 用户注册 | 否 | — |
| 用户 | /api/v1/users/me | GET | 获取当前用户 | 是 | — |
| 项目 | /api/v1/projects | GET | 项目列表 | 是 | 用户只能看自己 |
| 项目 | /api/v1/projects | POST | 创建项目 | 是 | — |
| 项目 | /api/v1/projects/:id | GET | 项目详情 | 是 | 项目成员 |
| 项目 | /api/v1/projects/:id | PATCH | 更新项目 | 是 | 项目管理员 |
| 项目 | /api/v1/projects/:id | DELETE | 删除项目 | 是 | 项目所有者 |

> **交叉校验**: 每个数据库表至少对应 CRUD 4 个接口；每个业务流程至少对应 1 个接口。

#### Step 2: 通用规范定义

**Base URL**: `https://api.example.com/api/v1`

**认证方式**: Bearer Token（`Authorization: Bearer <token>`）

**统一响应格式**:

```json
{
  "code": 200,
  "message": "success",
  "data": { }
}
```

**分页参数约定**:

| 参数 | 类型 | 说明 |
|------|------|------|
| page | int | 页码，从 1 开始 |
| page_size | int | 每页条数，默认 20，最大 100 |

**错误码表**:

| 错误码 | 说明 | HTTP 状态码 |
|--------|------|-------------|
| 400 | 参数校验失败 | 400 |
| 401 | 未认证 | 401 |
| 403 | 无权限 | 403 |
| 404 | 资源不存在 | 404 |
| 409 | 资源冲突 | 409 |
| 429 | 请求过于频繁 | 429 |
| 500 | 服务器内部错误 | 500 |

**版本策略**: URL 路径版本控制（`/api/v1/`），v1 稳定后通过 v2 迭代。

#### Step 3: 接口详细定义

每个接口必须定义：

```markdown
### GET /api/v1/projects/:id

**说明**: 获取项目详情

**认证**: 是

**请求参数**:
| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| id | Path | string | 是 | 项目 ID |

**响应示例（成功）**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": "uuid",
    "name": "项目名称",
    "createdAt": "2026-07-24T10:00:00Z"
  }
}
```

**响应示例（失败）**:
```json
{
  "code": 404,
  "message": "项目不存在",
  "data": null
}
```

**业务规则**:
- 用户只能访问自己有权限的项目
- 项目不存在返回 404

**错误码**:
- 404: 项目不存在
- 403: 无权访问该项目
```

#### Step 4: 接口依赖关系

定义接口的调用顺序和依赖：

```
用户注册 → 用户登录 → 获取 Token
     ↓
创建项目 → 查询项目列表 → 查询项目详情
     ↓
创建任务 → 查询任务列表 → 更新任务状态
```

#### Step 5: 限流与缓存策略

**限流策略**:

| 接口类型 | 限流规则 | 说明 |
|----------|----------|------|
| 认证接口 | 5 次/分钟 | 防止暴力破解 |
| 普通接口 | 100 次/分钟 | 按用户维度限流 |
| 文件上传 | 10 次/分钟 | 防止资源滥用 |

**缓存策略**:

| 数据类型 | 缓存方式 | TTL | 说明 |
|----------|----------|-----|------|
| 用户基础信息 | Redis | 5 分钟 | 频繁读取，很少变更 |
| 项目列表 | Redis | 1 分钟 | 中等变更频率 |
| 配置项 | 应用内存 | 永久 | 启动时加载 |

#### Step 6: 输出 api-design.md

文件保存到 `docs/api-design.md`:

```markdown
# API 设计: [项目名称]

## 1. 通用规范
### 1.1 Base URL
### 1.2 认证方式
### 1.3 统一响应格式
### 1.4 分页参数约定
### 1.5 错误码表
### 1.6 版本策略

## 2. 接口清单总表

## 3. 接口详细定义
### 3.1 认证模块
### 3.2 用户模块
### 3.3 项目模块
...

## 4. 接口依赖关系

## 5. 限流 / 缓存策略
```

---

### Phase 2: 实现阶段（编码）

#### Step 1: 定义 Pydantic Schema

先定义请求和响应的 Schema，确保类型安全:

```python
# schemas/skill_node.py
from datetime import datetime
from typing import Annotated
from pydantic import BaseModel, Field

class CreateSkillNodeRequest(BaseModel):
    """创建技能节点请求"""
    name: Annotated[str, Field(min_length=1, max_length=255, description="节点名称")]
    path: Annotated[str, Field(pattern=r"^/[a-z0-9\-/]+$", description="节点路径")]
    description: Annotated[str | None, Field(max_length=2000, description="节点描述")] = None

class SkillNodeResponse(BaseModel):
    """技能节点响应"""
    id: str
    name: str
    path: str
    description: str | None
    created_at: datetime
```

### Step 2: 设计路由

遵循 RESTful 规范和项目约定:

```python
# routers/skill_tree.py
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/api/v1", tags=["skill-tree"])

@router.get("/skill-tree/nodes", response_model=ListResponse[SkillNodeResponse])
async def list_skill_nodes(...):
    """获取技能节点列表"""

@router.post("/skill-tree/nodes", response_model=SkillNodeResponse, status_code=201)
async def create_skill_node(payload: CreateSkillNodeRequest, ...):
    """创建技能节点"""

@router.get("/skill-tree/nodes/{node_id}", response_model=SkillNodeResponse)
async def get_skill_node(node_id: UUID, ...):
    """获取单个技能节点"""
```

### Step 3: 统一响应格式

所有接口必须遵循统一响应格式:

```python
# 成功响应
{
    "code": 200,
    "data": { ... },
    "message": "success"
}

# 分页响应
{
    "code": 200,
    "data": {
        "items": [...],
        "total": 42,
        "page": 1,
        "page_size": 20
    },
    "message": "success"
}

# 错误响应
{
    "code": 400,
    "data": null,
    "message": "参数校验失败: path 格式不正确"
}
```

### Step 4: 分页标准

列表接口必须实现分页，根据数据量选择合适的分页策略:

| 策略 | 适用场景 | 优点 | 缺点 |
|------|----------|------|------|
| **Offset 分页** | 数据量较小 (<10万)、需要跳页 | 简单直观、支持跳页 | 深分页性能差 |
| **Cursor 分页** | 数据量较大、流式加载 | 性能稳定、支持无限滚动 | 不支持跳页 |

**Offset 分页参数**:

```python
class PaginationParams(BaseModel):
    page: Annotated[int, Field(gt=0, description="页码，从 1 开始")] = 1
    page_size: Annotated[int, Field(gt=0, le=100, description="每页条数，最大 100")] = 20
```

**Offset 分页响应**:

```python
class ListResponse[T](BaseModel, generic=True):
    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int
```

**Cursor 分页参数**:

```python
class CursorPaginationParams(BaseModel):
    cursor: Annotated[str | None, Field(description="游标，首次请求不传")] = None
    limit: Annotated[int, Field(gt=0, le=100, description="每页条数，最大 100")] = 20
```

**Cursor 分页响应**:

```python
class CursorResponse[T](BaseModel, generic=True):
    items: list[T]
    next_cursor: str | None
    has_more: bool
```

### Step 5: JSON 字段命名规范

API 请求和响应 JSON 字段统一使用 **camelCase**，与前端 JavaScript 命名习惯一致。数据库内部保持 **snake_case**，通过 Pydantic 自动转换:

```python
class SkillNodeResponse(BaseModel):
    id: str
    node_name: str = Field(alias="nodeName")
    created_at: datetime = Field(alias="createdAt")

    model_config = ConfigDict(populate_by_name=True)
```

**转换规则**:
- 请求参数: Pydantic 自动将 camelCase 转换为 snake_case 内部使用
- 响应数据: 通过 `alias` 字段将 snake_case 转换为 camelCase 返回

### Step 6: 异步校验器 (Pydantic v2.13+)

Pydantic v2.13+ 支持异步字段校验器，适用于需要 IO 操作的校验场景:

```python
from pydantic import field_validator

class LLMInput(BaseModel):
    prompt: Annotated[str, Field(max_length=100_000)]
    max_tokens: Annotated[int, Field(gt=0, le=8192)] = 1024

    @field_validator("prompt", mode="before")
    @classmethod
    async def validate_prompt_length(cls, v: str) -> str:
        if len(v) > 100_000:
            raise ValueError("Prompt too long for context window")
        return v
```

**使用场景**:
- 需要查询数据库验证唯一性
- 需要调用外部 API 验证资源存在
- 需要读取文件验证内容格式

### Step 7: 流式响应规范

对于 AI 推理、大数据导出等场景，使用流式响应:

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator

app = FastAPI()

@app.get("/ai/chat", response_class=StreamingResponse)
async def stream_chat(prompt: str) -> StreamingResponse:
    """AI 流式聊天接口"""
    async def event_generator() -> AsyncGenerator[str, None]:
        async for token in llm.generate_stream(prompt):
            yield f"data: {token}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"X-AI-Stream-Version": "2.0"}
    )
```

**流式响应要求**:
- 使用 `StreamingResponse` + `AsyncGenerator`
- 设置 `media_type="text/event-stream"`
- 每个 chunk 使用 `data: {content}\n\n` 格式
- 添加 `X-AI-Stream-Version` 头标识协议版本

### Step 8: 实现 Router -> Service -> Repository

严格分层实现:

```
Router (路由层)     → 参数校验、调用 Service、返回响应
  └─ Service (业务层) → 业务逻辑、事务管理、调用 Repository
       └─ Repository (数据层) → 数据库操作、SQLAlchemy 查询
            └─ Model (ORM)     → 数据库表映射
```

### Step 9: 更新 Swagger 文档并编写测试

- 确认 Swagger (`/docs`) 中接口文档正确
- 编写 Pytest 测试用例覆盖正常和异常场景
- 流式接口需单独测试流中断、恢复等边界场景

## 硬性规则

- ✅ **RESTful 风格**: 正确使用 HTTP Method (GET/POST/PUT/DELETE)
- ✅ **统一响应格式**: `{code, data, message}`
- ✅ **路由使用 kebab-case**: `/skill-tree/nodes` (非 `skillTreeNodes`)
- ✅ **版本控制**: `/api/v1/` 前缀
- ✅ **Pydantic Schema**: 所有请求/响应必须有类型定义
- ✅ **严格分层**: Router -> Service -> Repository -> Model
- ❌ **禁止在 Router 层写业务逻辑或 SQL**
- ❌ 禁止在 Router 层直接操作数据库 Session
- ❌ 禁止绕过 Pydantic 校验直接接收原始参数
- ❌ 禁止路由使用驼峰命名 (`/skillTree/nodes`)
- ❌ 禁止返回非标准格式的响应

## 反模式

- ❌ Router 里直接写 `db.execute(select(...))` — 违反分层原则
- ❌ 响应格式不统一 (有时返回裸数据，有时包一层) — 前端难以处理
- ❌ POST 接口用 GET 方法 — 语义错误
- ❌ 路由 `/api/getSkillTree` — 不是 RESTful，不是 kebab-case
- ❌ 没有 Pydantic Schema 直接 `request.json()` — 无类型安全