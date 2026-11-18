---
name: schema-as-code
version: v4.0.1
type: rule
enabled: true
mode: [standard, creator]
updated: 2026-11-05
description: Schema-As-Code 范式 — Pydantic API Schema + SQL Migration 双契约（RULE-030~033）
applies_to:
  agents: ['architect', 'backend-developer', 'frontend-developer', 'ui-designer']
  phases: ['design', 'implementation', 'review']
  project_types: ['全部']
  tech_stacks: ['全部']
---
# Schema-As-Code 范式 — 个人开发者精简版
> **本文件落实**: RULE-030（设计文档必须产出机器可读 Schema）、RULE-032（AI 生成代码前必须通过 Schema 校验）、RULE-033（任何 Schema 变更必须记录 ADR 和 Migration）

> **版本**: v4.0.1 | **更新**: 2026-11-05
> **变更说明**: 移除设计令牌语义约束、多 Schema 同步验证、复杂校验工作流，保留 Pydantic Schema + SQL Migration 核心要求。

---

## 核心规则

| 编号 | 规则 | Enforcement 路径 |
|------|------|------------------|
| RULE-030 | 设计文档必须产出机器可读 Schema | `hooks/schema-validator.py`（简化版） |
| RULE-031 | ~~设计令牌必须定义 domains/forbidden_domains~~ | **已废弃**（个人项目无需语义约束） |
| RULE-032 | AI 生成代码前必须通过 Schema 校验 | `hooks/scripts/schema-gate.py`（简化版） |
| RULE-033 | 任何 Schema 变更必须记录 ADR 和 Migration | 人工审查 + Git commit 检查 |

### 已废弃规则

| 废弃编号 | 废弃原因 |
|---------|---------|
| RULE-031 | 设计令牌语义约束对个人项目过度工程化 |

---

## 简化后的 Schema 要求

个人项目仅需维护两类 Schema：

### 1. API Schema（Pydantic）

所有 API 请求/响应必须定义 Pydantic BaseModel：

```python
from pydantic import BaseModel, Field
from typing import Optional, List

class ModelRequest(BaseModel):
    """模型选择请求"""
    provider: str = Field(..., description="提供商名称")
    model_name: str = Field(..., description="模型名称")
    api_key: str = Field(..., description="API 密钥")
    
    class Config:
        json_schema_extra = {
            "example": {
                "provider": "openai",
                "model_name": "gpt-4o",
                "api_key": "sk-..."
            }
        }
```

### 2. Database Schema（SQL Migration）

所有数据库变更必须通过 Alembic 迁移：

```bash
# 生成迁移
alembic revision --autogenerate -m "add user profile table"

# 应用迁移
alembic upgrade head

# 回滚（必须测试）
alembic downgrade -1
```

### 3. 可选：JSON Schema 导出

如果需要前端类型同步，可从 Pydantic 导出 JSON Schema：

```python
import json
from fastapi import FastAPI

app = FastAPI()

@app.post("/api/models")
async def create_model(req: ModelRequest):
    return {"status": "ok"}

# 导出 Schema
schema = json.dumps(ModelRequest.model_json_schema(), indent=2, ensure_ascii=False)
```

---

## 取消的复杂功能

| 原功能 | 简化后 |
|--------|--------|
| 设计令牌定义（domains/forbidden_domains） | 无需定义，直接写 Pydantic Schema |
| 多 Schema 一致性验证 | 人工检查，无自动验证 |
| CI Schema 门禁 | pre-commit hook 可选检查 |
| Schema 变更审计日志 | Git commit 记录即可 |

---

## 强制执行路径

### 简化版 Enforcement

```yaml
# .pre-commit-config.yaml（可选）
repos:
  - repo: local
    hooks:
      - id: schema-check
        name: Check Pydantic Schema
        entry: python hooks/schema-validator.py --all --fail-on-violation
        language: python
        files: \.py$
```

### 手动验证清单

提交前检查：
- [ ] 新增 API 端点有对应 Pydantic Schema
- [ ] 数据库变更有对应 Alembic 迁移
- [ ] Migration 包含 downgrade 逻辑
- [ ] Schema 变更已记录在 ADR 或 commit message 中

---

## 与 v3.x 的主要差异

| 差异项 | v3.x | v4.0（个人版） |
|--------|------|---------------|
| 设计令牌 | 必须定义 domains/forbidden_domains | **无需定义** |
| 多 Schema 同步 | 强制 AI/Backend/Frontend 三方一致 | **仅保留 Backend Schema** |
| CI 门禁 | schema-gate.py 强制阻断 | **可选 pre-commit hook** |
| Schema 验证 | hooks/schema-validator.py | **简化为手动清单** |
| ADR 要求 | 所有 Schema 变更必须写 ADR | **仅架构级变更需 ADR** |
