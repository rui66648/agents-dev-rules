---
name: environment-isolation
version: v1.0.1
type: rule
enabled: true
mode: [standard, creator]
updated: 2026-11-11
description: 环境隔离规范 — 多环境配置分离、启动参数切换、部署前配置校验（RULE-048）
applies_to:
  agents: ['architect', 'backend-developer', 'security-auditor']
  phases: ['implementation', 'deploy']
  project_types: ['全部']
  tech_stacks: ['全部']
---
# 环境隔离规范 (Environment Isolation)
> **本文件落实**: RULE-048（环境隔离）
> **延伸参考** RULE-008（严禁硬编码密钥/URL，落点见 `rules/security-rules.md`）

> **核心目标**: 消除「本地能跑、线上缺变量」的隐性差异，确保本地与线上配置一致、可复现。

---

## 核心规则

| 编号 | 规则 | Enforcement 路径 |
|------|------|------------------|
| RULE-048 | 环境隔离遵循本规则 | pydantic-settings + 启动时配置校验（fail-fast） |

---

## 多环境配置分离

| 环境 | 配置文件 | 用途 |
|------|---------|------|
| 开发 | `.env.development` | 本地日常开发 |
| 测试 | `.env.test` | 自动化测试 |
| 生产 | `.env.production` | 线上部署 |

- 所有环境文件必须提供 `.env.example` 模板（含全部键，值为占位符）
- 环境文件必须加入 `.gitignore`，仅 `.env.example` 入库
- 禁止在代码中硬编码环境值（RULE-008）

---

## 启动参数切换环境

- 通过环境变量 `APP_ENV`（或 `ENVIRONMENT`）选择环境：`development` / `test` / `production`
- 后端：`pydantic-settings` 的 `SettingsConfigDict(env_file=f".env.{APP_ENV}")`
- 前端：Vite 的 `import.meta.env.MODE` 或 `VITE_APP_ENV`
- 默认值：本地未设置时回退到 `development`

---

## 部署前配置校验（必须）

- 应用启动时必须校验必需环境变量是否存在，**缺失即报错退出（fail-fast）**
- 必需变量清单在 `tech-stack.md` 中声明
- 校验逻辑示例（后端）：

```python
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=f".env.{APP_ENV}", extra="ignore")
    database_url: str = Field(..., description="数据库连接串")
    jwt_secret: str = Field(..., description="JWT 密钥")
    # 缺失时启动即抛 ValidationError，杜绝线上缺变量
```

---

## 环境差异最小化

- 依赖版本锁定：`requirements.txt` / `package-lock.json` 必须提交
- 构建可复现：Docker 镜像使用固定 tag，禁止 `latest`
- 本地与线上使用同一套 Docker Compose 配置（仅环境变量不同）

---

## 禁止事项

- ❌ 本地使用未提交的 `.env` 配置而线上缺少对应变量
- ❌ 在代码中硬编码环境地址/密钥（RULE-008）
- ❌ 提交 `.env.*` 环境文件到仓库
- ❌ 线上使用 `latest` 镜像 tag
