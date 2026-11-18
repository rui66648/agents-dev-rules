---
name: database-migration
version: v1.0.0
type: skill
enabled: true
mode: [standard, creator]
description: "需要修改数据库 Schema（加表、加字段、改索引）时使用。严格遵循 Alembic 迁移流程，禁止手动改表，迁移必须含 downgrade。触发词: 迁移、migration、加字段、改表、alembic。"
updated: 2026-08-13
depends_on: [api-design]
composes: []
---
# Database Migration


## 负责代理

`database-expert` — 数据库 Schema 变更和迁移由数据库专家代理负责，确保迁移脚本安全可回滚。

## 何时使用

- 需要新增、修改或删除**数据库表**时
- 需要新增、修改或删除**表字段**时
- 需要创建/删除**索引**或**约束**时
- 需要执行任何**数据库 Schema 变更**时

**触发关键词**: "改表"、"加字段"、"数据库变更"、"migration"、"alembic"

## 执行流程

### Step 1: 修改 Model

在 SQLAlchemy Model 中进行变更:

```python
# models/skill_node.py
from sqlalchemy import String, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import AsyncAttrs
from uuid import UUID, uuid4
from typing import List

class Base(AsyncAttrs, DeclarativeBase):
    pass

class SkillNode(Base):
    __tablename__ = "skill_nodes"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    path: Mapped[str] = mapped_column(String(1024), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    difficulty: Mapped[int] = mapped_column(Integer, default=0)
    # 关系定义
    children: Mapped[List["SkillNode"]] = relationship(back_populates="parent")
    parent: Mapped["SkillNode | None"] = relationship(back_populates="children", remote_side=[id])
```

### Step 2: 生成迁移脚本

```bash
alembic revision --autogenerate -m "add description and difficulty to skill_nodes"
```

### Step 3: 检查生成的迁移脚本

**必须打开并审查生成的迁移文件**:

```python
# migrations/versions/xxxx_add_description_and_difficulty.py
from sqlalchemy import Text, Integer

def upgrade() -> None:
    op.add_column('skill_nodes', sa.Column('description', Text(), nullable=True))
    op.add_column('skill_nodes', sa.Column('difficulty', Integer(), server_default='0'))

def downgrade() -> None:
    op.drop_column('skill_nodes', 'difficulty')
    op.drop_column('skill_nodes', 'description')
```

检查清单:
- ✅ 变更范围是否符合预期 (有无多余变更)
- ✅ `upgrade` 逻辑正确
- ✅ `downgrade` 逻辑正确且可执行
- ✅ 无硬编码数据库连接字符串
- ✅ 字段类型、约束、默认值正确

### Step 4: 执行迁移

```bash
# 先备份数据 (生产环境)
pg_dump -U user -d dbname > backup_before_migration.sql

# 执行迁移
alembic upgrade head
```

### Step 5: 验证迁移结果

```bash
# 检查数据库 Schema
alembic current
alembic history --verbose

# 通过 Pytest 验证数据操作正常
pytest tests/models/test_skill_node.py -v
```

### Step 6: 编写测试

- 为新增字段编写 Model 测试
- 为涉及新字段的查询编写测试
- 确保 downgrade 也可正常工作

### Step 7: pgvector 向量索引 (PostgreSQL 17+)

对于向量检索场景，使用 pgvector 扩展:

```python
# 向量表定义
from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column

class Document(Base):
    __tablename__ = "documents"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float]] = mapped_column(type_="vector(1024)")
```

**迁移脚本中创建向量索引**:

```python
def upgrade() -> None:
    op.create_index(
        "idx_doc_embedding",
        "documents",
        ["embedding"],
        postgresql_using="hnsw",
        postgresql_ops={"embedding": "vector_cosine_ops"}
    )

def downgrade() -> None:
    op.drop_index("idx_doc_embedding")
```

**索引策略选择**:

| 索引类型 | 适用场景 | 参数建议 |
|----------|----------|----------|
| **HNSW** | 数据量 < 100万、查询频繁 | m=16, ef_construction=200 |
| **IVFFlat** | 数据量 > 100万、内存敏感 | lists=sqrt(行数) |

## 硬性规则

- ✅ **所有 Schema 变更必须通过 Alembic 迁移**
- ✅ 迁移脚本**必须包含 downgrade 逻辑**
- ✅ 生成迁移后**必须人工审查 SQL**
- ✅ 生产环境迁移前**必须备份数据**
- ✅ 迁移后**必须运行测试验证**
- ❌ **禁止手动改表** (直接 SQL ALTER TABLE)
- ❌ **禁止硬编码数据库连接字符串**在迁移脚本中
- ❌ 禁止跳过审查直接执行迁移
- ❌ 禁止在生产环境直接运行未测试的迁移
- ❌ 禁止修改迁移脚本后不更新对应 Model

## 反模式

- ❌ 直接用 `psql` 执行 ALTER TABLE — 绕过了版本控制
- ❌ 迁移脚本写死 `postgres://user:pass@host/db` — 安全漏洞
- ❌ 不写 downgrade — 出问题时无法回滚
- ❌ 一个迁移脚本包含 10 个不相关的变更 — 应拆分为多个迁移
- ❌ 在 migration 里写业务逻辑 — 迁移只应处理 Schema 变更
