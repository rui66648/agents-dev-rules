---
name: security-rules
version: v1.1.2
type: rule
enabled: true
mode: [standard, creator]
updated: 2026-11-04
description: 安全规则 — 密钥管理、输入校验、SQL/代码注入防护、认证授权、线上环境安全、日志规范（RULE-008/009/010）
applies_to:
  agents: ['security-auditor', 'backend-developer', 'frontend-developer']
  phases: ['全程']
  project_types: ['全部']
  tech_stacks: ['全部']
---
# 安全规则 (Security Rules)
> **本文件落实**: RULE-008（严禁硬编码密钥/URL）、RULE-009（所有用户输入必须经过校验）、RULE-010（禁止 eval/exec/不可信反序列化）、RULE-016（代码提交前必须进行安全检查）

> **适用范围**: 本文包含通用安全原则（密钥管理、输入校验、注入防护、认证授权）和 **FastAPI + SQLAlchemy 后端实现子集**。通用原则适用于所有项目；以 `<!-- [项目特定] -->` 标注的段落为 FastAPI+React 项目的具体落地示例，其他技术栈应参照 `tech-stack.md` 等价映射。

本文件定义项目中必须遵守的安全规范，AI 编码代理生成的代码必须严格遵循。

> **确定性强制现状**：RULE-008/009/010 目前**没有自动阻断**。`hooks/scripts/pre-commit-secret-scan.js` 是 Agent 工具调用前钩子（PreToolUse），不是 git pre-commit，且四仓均未挂载 `hooks.json`；`eval`/`exec`/SQL 拼接拦截依赖项目已配置的 Linter，未配置即不生效。状态以 `rules/cicd-rules.md §门禁现状` 为准，发布前必须手动执行安全扫描。

## 密钥与敏感信息管理

<!-- [项目特定] -->
- **禁止**硬编码任何密钥、密码、URL 或 Token
- 所有配置项**必须**通过 `pydantic-settings` 读取环境变量
- 敏感配置（数据库密码、API Key、JWT Secret）**必须**存储在 `.env` 文件中
- `.env` 文件**必须**在 `.gitignore` 中，禁止提交到仓库

## 输入校验

<!-- [项目特定] -->
- 所有用户输入**必须**经过 Pydantic Model 校验
- **禁止**信任任何来自客户端的数据
- 文件上传必须校验文件类型、大小和内容

## 文件上传规范

### 文件类型白名单
| 类型 | 允许的扩展名 | MIME 类型 |
|------|-------------|-----------|
| 图片 | `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp` | `image/jpeg`, `image/png`, `image/gif`, `image/webp` |
| 文档 | `.pdf`, `.txt`, `.md` | `application/pdf`, `text/plain`, `text/markdown` |
| 压缩包 | `.zip`, `.tar`, `.gz` | `application/zip`, `application/x-tar`, `application/gzip` |

### 文件大小限制
- **图片**: 最大 5MB
- **文档**: 最大 10MB
- **压缩包**: 最大 50MB

### 文件存储策略
- 文件名**必须**经过安全清理，移除特殊字符和路径遍历字符
- 上传的文件**必须**重命名为 UUID，避免文件名冲突和路径遍历攻击
- 文件存储在项目根目录外的独立存储目录（如 `/var/uploads/`）
- 禁止将文件存储在 Web 可访问的目录中（除非通过 API 控制访问）

### 文件内容校验
- **必须**校验文件的实际内容，不依赖扩展名或 MIME 类型
- **必须**使用文件魔数（Magic Number）验证文件类型
- **禁止**直接执行或解析上传的可执行文件

### 示例
<!-- [项目特定] -->
```python
import uuid
import os
from pathlib import Path

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024

async def save_uploaded_file(file: UploadFile) -> str:
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise AppException("不支持的文件类型")
    
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise AppException("文件大小超过限制")
    
    new_filename = f"{uuid.uuid4()}{ext}"
    storage_path = Path("/var/uploads") / new_filename
    
    with open(storage_path, "wb") as f:
        f.write(content)
    
    return new_filename
```

## SQL 注入防护

<!-- [项目特定] -->
- **必须**使用 SQLAlchemy ORM 或参数化查询
- **禁止**拼接 SQL 字符串
- **禁止**使用原始 SQL 除非经过安全审查

## 代码注入防护

- **禁止**使用 `eval()`、`exec()`
- **禁止**动态导入不可信代码
- **禁止**使用 `pickle` 反序列化不可信数据

## 认证与授权

- JWT Token 必须设置合理的过期时间
- 密码**必须**使用 `bcrypt` 哈希存储
- **禁止**明文存储密码
- 公开端点必须实施 Rate Limiting

## 网络安全

- CORS **必须**配置白名单，禁止使用 `*` 通配符
- API 端点必须正确配置 HTTP 方法限制
- 敏感端点必须实施认证中间件保护

## 线上环境安全

> **核心目标**: 将「代码安全」延伸至「线上环境安全」，堵住部署后的环境级漏洞。

### HTTPS 强制

- 线上必须启用 HTTPS，禁止 HTTP 明文访问（Nginx 配置 301 跳转）
- 证书使用 Let's Encrypt 免费证书或平台托管证书
- HSTS 头：`Strict-Transport-Security: max-age=31536000; includeSubDomains`

### 反向代理安全头（Nginx 示例）

```nginx
server {
    listen 443 ssl;
    # ... ssl_certificate 配置 ...

    # 安全响应头
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'" always;

    # 限流：公开端点每 IP 每分钟 60 次
    limit_req_zone $binary_remote_addr zone=api:10m rate=60r/m;
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://app:8000;
    }
}
```

### 线上限流落地

- 公开端点必须配置 Rate Limiting（Nginx `limit_req` 或应用层）
- 登录/注册等敏感端点限流更严格（如 5r/m）
- 与 `security-rules.md` 的「公开端点必须实施 Rate Limiting」呼应，线上由反向代理强制

### 线上配置校验

- 线上启动时校验必需环境变量（见 `rules/environment-isolation.md` RULE-048）
- 线上禁止开启 Debug 模式 / 暴露 `/docs`（生产环境关闭 Swagger）
- 敏感日志脱敏：禁止在日志中记录密码、Token（见下方日志安全）

---

## 日志规范

### 日志框架
<!-- [项目特定] -->
- 必须使用 `structlog` 进行结构化日志记录
- 日志输出格式为 JSON，便于日志系统解析和查询

### 日志级别
| 级别 | 用途 | 示例 |
|------|------|------|
| `DEBUG` | 开发调试，详细信息 | SQL 查询、函数入参/返回值 |
| `INFO` | 正常业务流程 | 用户登录、数据创建、任务完成 |
| `WARNING` | 非关键异常，需要关注 | 参数校验失败、降级处理 |
| `ERROR` | 关键错误，影响功能 | 数据库连接失败、API 调用失败 |
| `CRITICAL` | 系统级严重错误 | 服务崩溃、数据丢失 |

### 日志字段标准
所有日志必须包含以下基础字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `timestamp` | ISO8601 | 日志时间戳 |
| `level` | str | 日志级别 |
| `request_id` | str | 请求追踪 ID |
| `logger` | str | 日志器名称（模块路径） |
| `message` | str | 日志消息 |
| `user_id` | str \| None | 当前用户 ID（如有） |
| `path` | str | 请求路径（API 日志） |

### 日志安全
- **禁止**在日志中记录密码、Token、密钥等敏感数据
- **禁止**在生产环境使用 `print()` 输出调试信息

### 日志配置示例
```python
import structlog

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer(),
    ]
)

logger = structlog.get_logger("api.skill_tree")
logger.info(
    "Skill node created",
    request_id=request_id,
    node_id=node.id,
    user_id=current_user.id,
    path="/api/v1/skill-tree/nodes",
)
```

---

## SBOM 与 License 扫描

### SBOM（Software Bill of Materials）
- **生成工具**：[Syft](https://github.com/anchore/syft)（Apache-2.0）
- **输出格式**：CycloneDX 或 SPDX
- **执行位置**：CI 的 build 阶段后
- **用途**：依赖清单、漏洞响应、License 合规审计

### License 合规
- **后端**：`pip-licenses --format=json --fail-on="AGPL;SSPL;BSL"` 阻断黑名单 License
- **前端**：`license-checker --failOn "AGPL*;SSPL*;BSL*"` 阻断黑名单 License
- **白名单**：MIT / Apache-2.0 / BSD-2/3 / MPL-2.0 / ISC / Unlicense / 0BSD
- **黑名单与豁免**：见 `rules/open-source-first.md` §3 License 合规章节
- **人工审查**：非 OSI 认可 License 须人工审查条款，ADR 中记录豁免理由

### 强制级别
- 个人项目：建议执行，License 黑名单阻断
- 商业项目：必须执行，CI 中阻断合并

---

## 禁止事项

- ❌ 硬编码密钥、密码、URL 或 Token
- ❌ 使用 `eval()`、`exec()` 或动态导入不可信代码
- ❌ 拼接 SQL 字符串
- ❌ 明文存储密码
- ❌ CORS 配置使用 `*` 通配符
- ❌ 在日志中记录敏感数据
- ❌ 在生产环境使用 `print()`
- ❌ 将 `.env` 文件提交到代码仓库
- ❌ 公开端点不设置 Rate Limiting
- ❌ JWT Token 不设置过期时间
- ❌ 引入 AGPL/SSPL/BSL 等黑名单 License 依赖
