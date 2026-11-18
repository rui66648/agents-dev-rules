---
name: security-design
version: v1.0.0
type: skill
enabled: true
mode: [standard, creator]
description: "system-design 阶段进行安全方案设计 — 认证授权、数据加密、输入校验、常见漏洞防护，输出安全设计文档。触发词: 安全、认证、授权、加密、漏洞、渗透。"
updated: 2026-08-13
depends_on: [system-design]
composes: [ai-safety-check]
---
# Security Design


## 负责代理

`security-auditor` — 安全方案设计由安全审计员代理负责，确保认证、授权、加密方案完整。

## 何时使用

- 需要设计**认证方案**（JWT / Session / OAuth2 / SSO）时
- 需要设计**权限模型**（RBAC / ABAC / ReBAC）时
- 需要制定**数据加密策略**（传输加密、存储加密、敏感字段脱敏）时
- 需要定义**输入校验规则**（SQL注入防护、XSS防护、CSRF防护）时
- 需要规划**安全审计**（操作日志、登录日志、异常行为检测）时
- 涉及支付、用户隐私数据、合规要求（GDPR等）的功能时

**触发关键词**: "安全设计"、"认证方案"、"权限模型"、"加密策略"、"OWASP"、"数据安全"、"安全审计"、"输入校验"

## 与其他技能的关系

```
brainstorming → system-design → api-design
                     ↓              ↓
              security-design ←─────┘
                     ↓
              writing-plans → executing-plans
```

> **衔接规则**:
> - `security-design` 依赖 `system-design` 的架构设计（技术选型、部署方案）
> - `security-design` 与 `api-design` **并行执行**，安全设计中的认证方案直接影响 API 的认证中间件设计
> - `security-design` 的权限模型必须与 `api-design` 的接口权限标注一致
> - `security-design` 的输入校验策略必须与 `api-design` 的 Pydantic Schema 一致
> - **高风险功能**（安全/认证/支付/隐私）必须触发本技能，不可跳过

## 设计阶段总体流程

```
需求确认 → 架构设计 → 安全设计 → API设计 → UI设计
              ↑           ↓          ↓
              └─── 互相校验、迭代调整 ──┘
```

**输出文件清单**:

```
docs/
├── architecture.md          ← 架构设计（system-design 技能输出）
├── database-schema.md       ← 数据库设计（system-design 技能输出）
├── security-design.md       ← 安全设计（本技能输出）
├── api-design.md            ← 接口设计（api-design 技能输出）
├── ui-wireframe.md          ← UI/页面设计（ui-design 技能输出）
```

> **校验关系**: 安全设计中的认证方案 → API 设计中的认证中间件；权限模型 → API 接口权限标注；输入校验规则 → Pydantic Schema 校验器，三者必须一致。

---

## 执行流程

### Phase 1: 认证方案设计

**目标**: 确定用户身份认证的技术方案和 Token 管理策略。

#### Step 1: 认证方式选型

**必须回答的决策点**:

| 决策项 | 要回答的问题 | 个人项目推荐 |
|--------|-------------|-------------|
| **认证方式** | JWT / Session / OAuth2 / SSO / Magic Link？ | JWT（无状态，适合前后端分离） |
| **Token 存储** | 前端存在哪？（localStorage / httpOnly Cookie / 内存） | httpOnly Cookie（防 XSS 窃取） |
| **Token 刷新** | Access Token 过期后如何刷新？Refresh Token 存在哪？ | Refresh Token 存 httpOnly Cookie + 路径限制 |
| **Token 过期** | Access Token 有效期？Refresh Token 有效期？ | Access: 15min / Refresh: 7d |
| **多设备登录** | 允许几个设备同时登录？踢下线策略？ | 允许 3 设备，新设备登录可踢最旧设备 |
| **第三方登录** | 支持哪些？（Google / GitHub / 微信 / Apple） | 按用户群体选择，初期 1-2 个即可 |
| **MFA 2FA** | 是否需要双因素认证？ | 涉及支付/隐私时必须支持 |

#### Step 2: JWT Token 设计

**Access Token Payload**:

```json
{
  "sub": "user-uuid",
  "role": "user",
  "iat": 1753958400,
  "exp": 1753959300,
  "jti": "unique-token-id",
  "type": "access"
}
```

**Refresh Token 设计**:

| 属性 | 要求 | 说明 |
|------|------|------|
| 存储位置 | httpOnly Cookie | 禁止 JS 访问 |
| 路径限制 | `/api/v1/auth/refresh` | 仅刷新接口可携带 |
| 有效期 | 7 天 | 过期需重新登录 |
| 轮换策略 | 每次刷新后颁发新 Refresh Token | 旧 Token 立即失效 |
| 撤销机制 | 服务端维护 Token 黑名单 | 用户登出/修改密码时撤销 |

#### Step 3: Session 管理（如使用 Session 方案）

| 属性 | 要求 |
|------|------|
| Session ID 长度 | >= 128 位随机数 |
| 存储后端 | Redis（分布式）或数据库 |
| 空闲超时 | 30 分钟无操作自动过期 |
| 绝对超时 | 8 小时强制重新登录 |
| 并发控制 | 按用户限制最大并发 Session 数 |

---

### Phase 2: 权限模型设计

**目标**: 定义完整的权限体系，确保最小权限原则。

#### Step 4: 权限模型选型

| 模型 | 适用场景 | 复杂度 | 个人项目推荐 |
|------|----------|--------|-------------|
| **RBAC**（角色-权限） | 角色固定、权限按角色划分 | 低 | 首选 |
| **ABAC**（属性-权限） | 权限依赖多个属性动态判断 | 高 | 仅在需要细粒度控制时 |
| **ReBAC**（关系-权限） | 权限依赖资源关系（如"项目成员"） | 中 | 协作文档类项目考虑 |

#### Step 5: 角色定义

**标准角色层级**（从低到高）:

```
guest（访客）
  └─ user（注册用户）
       └─ member（项目成员）
            └─ admin（项目管理员）
                 └─ super_admin（系统管理员）
```

**角色权限矩阵**:

| 权限 | guest | user | member | admin | super_admin |
|------|-------|------|--------|-------|-------------|
| 查看公开内容 | V | V | V | V | V |
| 注册/登录 | | V | V | V | V |
| 创建项目 | | V | V | V | V |
| 编辑自己的项目 | | | V | V | V |
| 管理项目成员 | | | | V | V |
| 删除项目 | | | | V | V |
| 系统管理 | | | | | V |

#### Step 6: 权限实现策略

**API 层权限控制**:

```markdown
### 权限中间件设计

1. **认证中间件**（所有需认证接口）:
   - 解析 JWT Token
   - 验证 Token 有效性（签名、过期、黑名单）
   - 将用户信息注入请求上下文

2. **授权中间件**（按角色/资源）:
   - 检查用户角色是否满足接口要求
   - 检查资源所有权（用户只能操作自己的资源）
   - 检查项目成员关系（项目内部权限）

3. **权限装饰器**（FastAPI 实现）:
   - `@require_auth` — 需登录
   - `@require_role("admin")` — 需特定角色
   - `@require_ownership("project")` — 需资源所有权
```

**数据层权限控制**:

- 查询时自动过滤：`WHERE user_id = current_user.id`
- 行级安全（RLS）：如在 Supabase 中启用（可选，推荐使用应用层权限控制）
- 敏感字段脱敏：在 Repository 层统一处理

---

### Phase 3: 数据安全设计

**目标**: 确保数据在传输、存储、处理全链路的安全性。

#### Step 7: 传输安全

| 措施 | 要求 | 说明 |
|------|------|------|
| HTTPS | 全站强制 HTTPS，HSTS 头 | 禁止 HTTP 明文传输 |
| TLS 版本 | >= TLS 1.2，推荐 TLS 1.3 | 禁用 SSL/TLS 1.0/1.1 |
| 证书管理 | 自动续期（Let's Encrypt） | 避免证书过期 |
| API 通信 | 内网服务间也使用 HTTPS | 零信任网络原则 |

#### Step 8: 存储加密

| 数据类型 | 加密方式 | 说明 |
|----------|----------|------|
| 密码 | bcrypt（cost=12）或 argon2id | 不可逆哈希，禁止 MD5/SHA1 |
| 手机号 | AES-256-GCM 加密存储 | 可逆加密，密钥从环境变量读取 |
| 身份证号 | AES-256-GCM 加密存储 | 合规要求 |
| API 密钥 | 环境变量 / 密钥管理服务 | 禁止硬编码 |
| 数据库连接串 | 环境变量 / 密钥管理服务 | 禁止硬编码 |
| JWT 签名密钥 | 环境变量，>= 256 位 | 定期轮换 |

#### Step 9: 敏感字段脱敏

**脱敏规则**:

| 字段类型 | 脱敏规则 | 示例 |
|----------|----------|------|
| 手机号 | 中间 4 位替换 | `138****1234` |
| 邮箱 | 用户名部分隐藏 | `u***r@example.com` |
| 身份证号 | 中间 8 位替换 | `320***********1234` |
| 银行卡号 | 仅显示后 4 位 | `****1234` |
| IP 地址 | 最后一段替换 | `192.168.*.*` |

**脱敏时机**:
- 日志输出前（通过 logging filter 自动脱敏）
- API 响应返回前（在 Response Schema 中标记敏感字段）
- 第三方服务调用前（只传递必要信息）

#### Step 10: 密钥管理

| 密钥类型 | 存储位置 | 轮换周期 | 访问控制 |
|----------|----------|----------|----------|
| JWT 签名密钥 | 环境变量 / KMS | 90 天 | 仅后端服务 |
| 数据库密码 | 环境变量 / KMS | 90 天 | 仅后端服务 |
| 第三方 API Key | 环境变量 / KMS | 按服务商要求 | 最小权限 |
| 加密密钥 | KMS（如 AWS KMS / Vault） | 1 年 | 仅安全模块 |
| 会话密钥 | 内存（不持久化） | 每次重启生成 | 不暴露 |

---

### Phase 4: 输入校验策略

**目标**: 建立多层防护体系，防止常见 Web 攻击。

#### Step 11: 注入防护

**SQL 注入防护**:

| 措施 | 说明 |
|------|------|
| 强制使用 ORM 参数化查询 | 禁止拼接 SQL 字符串 |
| 存储过程使用参数化 | 禁止动态 SQL |
| 最小数据库权限 | 应用账户仅授予必要权限（CRUD，无 DDL） |
| 输入长度限制 | 所有字符串字段设置 max_length |

**命令注入防护**:
- 禁止将用户输入直接传递给系统命令
- 如需执行外部命令，使用参数列表而非字符串拼接

#### Step 12: XSS 防护

**前端防护**:

| 措施 | 说明 |
|------|------|
| React 默认转义 | React JSX 自动转义 `{}` 中的内容 |
| 禁止 `dangerouslySetInnerHTML` | 除非内容经过 DOMPurify 清洗 |
| CSP 头 | `Content-Security-Policy: default-src 'self'` |
| 输入转义 | 用户输入的 HTML 标签必须转义 |

**后端防护**:

| 措施 | 说明 |
|------|------|
| 响应头 | `X-Content-Type-Options: nosniff` |
| 响应头 | `X-XSS-Protection: 1; mode=block` |
| 输出编码 | JSON 响应自动转义特殊字符 |

#### Step 13: CSRF 防护

| 措施 | 说明 |
|------|------|
| SameSite Cookie | `SameSite=Strict`（或 `Lax`） |
| CSRF Token | 状态变更操作（POST/PUT/DELETE）需要 CSRF Token |
| Origin 检查 | 验证 `Origin` / `Referer` 头 |
| 双重提交 Cookie | 作为 SameSite 的补充方案 |

#### Step 14: 文件上传安全

| 措施 | 说明 |
|------|------|
| 文件类型白名单 | 仅允许特定扩展名（jpg/png/pdf） |
| MIME 类型校验 | 通过文件魔术字节验证真实类型 |
| 文件大小限制 | 前端 + 后端双重限制 |
| 病毒扫描 | 上传后异步扫描（ClamAV 等） |
| 存储隔离 | 上传文件存储在独立域名/子域名下 |
| 文件名处理 | 重命名为 UUID，禁止保留原始文件名 |

#### Step 15: Pydantic 校验规则

```python
# 通用安全校验规则
from pydantic import BaseModel, Field, field_validator
import re

class SafeInputBase(BaseModel):
    """所有输入 Schema 的基类，包含安全校验"""

    @field_validator("*", mode="before")
    @classmethod
    def sanitize_strings(cls, v: str) -> str:
        if isinstance(v, str):
            # 移除空字节
            v = v.replace("\x00", "")
            # 去除首尾空白
            v = v.strip()
        return v

class UserCreateRequest(SafeInputBase):
    username: str = Field(min_length=3, max_length=32, pattern=r"^[a-zA-Z0-9_-]+$")
    email: str = Field(max_length=255, pattern=r"^[^@]+@[^@]+\.[^@]+$")
    password: str = Field(min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if not re.search(r"[A-Z]", v):
            raise ValueError("密码必须包含大写字母")
        if not re.search(r"[a-z]", v):
            raise ValueError("密码必须包含小写字母")
        if not re.search(r"[0-9]", v):
            raise ValueError("密码必须包含数字")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("密码必须包含特殊字符")
        return v
```

---

### Phase 5: 安全审计设计

**目标**: 建立可追溯的安全事件记录体系。

#### Step 16: 审计日志设计

**必须记录的事件**:

| 事件类型 | 记录内容 | 保留期限 |
|----------|----------|----------|
| 登录成功 | 用户ID、IP、User-Agent、时间 | 90 天 |
| 登录失败 | 用户ID（如存在）、IP、失败原因、时间 | 90 天 |
| 密码修改 | 用户ID、IP、时间 | 永久 |
| 权限变更 | 操作人、目标用户、变更内容、时间 | 永久 |
| 敏感操作 | 操作类型、资源、时间、IP | 1 年 |
| API 异常 | 接口路径、用户ID、错误信息、时间 | 30 天 |

**审计日志字段**:

```json
{
  "id": "uuid",
  "timestamp": "2026-07-24T10:00:00Z",
  "event_type": "login_success",
  "user_id": "user-uuid",
  "ip_address": "192.168.1.1",
  "user_agent": "Mozilla/5.0...",
  "resource": "/api/v1/auth/login",
  "action": "POST",
  "result": "success",
  "details": {},
  "request_id": "req-uuid"
}
```

#### Step 17: 异常行为检测

| 检测规则 | 触发条件 | 响应动作 |
|----------|----------|----------|
| 暴力破解 | 同一 IP 5 分钟内登录失败 > 10 次 | 临时封禁 IP 15 分钟 |
| 异常登录 | 新设备/新地点登录 | 发送邮件/短信通知 |
| 频率异常 | 同一用户 1 分钟内请求 > 100 次 | 触发限流 |
| 权限提升 | 非管理员尝试访问管理接口 | 记录并告警 |
| 数据泄露 | 短时间内大量数据导出 | 触发审批流程 |

---

### Phase 6: 输出 security-design.md

文件保存到 `docs/security-design.md`:

```markdown
# 安全设计: [项目名称]

## 1. 认证方案
### 1.1 认证方式选型
### 1.2 Token 设计（Access Token / Refresh Token）
### 1.3 Session 管理（如适用）
### 1.4 第三方登录集成（如适用）

## 2. 权限模型
### 2.1 权限模型选型
### 2.2 角色定义与层级
### 2.3 权限矩阵
### 2.4 API 权限控制实现
### 2.5 数据层权限控制

## 3. 数据安全
### 3.1 传输安全（HTTPS/TLS）
### 3.2 存储加密策略
### 3.3 敏感字段脱敏规则
### 3.4 密钥管理方案

## 4. 输入校验
### 4.1 SQL 注入防护
### 4.2 XSS 防护
### 4.3 CSRF 防护
### 4.4 文件上传安全
### 4.5 Pydantic 校验规则清单

## 5. 安全审计
### 5.1 审计事件定义
### 5.2 审计日志字段
### 5.3 异常行为检测规则

## 6. 安全合规
### 6.1 适用的合规要求（GDPR 等）
### 6.2 数据保留策略
### 6.3 数据删除流程
```

---

## 安全设计检查清单

- [ ] 认证方式已确定（JWT/Session/OAuth2）
- [ ] Token 过期时间已设定
- [ ] Refresh Token 轮换策略已定义
- [ ] 权限模型已选定（RBAC/ABAC/ReBAC）
- [ ] 角色定义和权限矩阵已完成
- [ ] 所有密码使用 bcrypt/argon2 哈希
- [ ] 敏感数据加密方案已确定
- [ ] 脱敏规则已定义
- [ ] 所有密钥通过环境变量管理
- [ ] SQL 注入防护措施已到位
- [ ] XSS 防护措施已到位
- [ ] CSRF 防护措施已到位
- [ ] 文件上传安全策略已定义
- [ ] Pydantic 校验规则已覆盖所有输入
- [ ] 审计日志事件列表已定义
- [ ] 异常行为检测规则已定义
- [ ] 第三方 API 密钥未硬编码
- [ ] 生产环境 CSRF 保护已启用

## 硬性规则

- **涉及安全/认证/支付时必须触发本技能** — 不可跳过
- **所有用户输入必须经过 Pydantic 校验** — 前端校验仅提升体验，不可替代后端校验
- **密码必须使用 bcrypt（cost>=12）或 argon2id 哈希** — 禁止 MD5/SHA1/SHA256
- **敏感数据不得明文存储** — 手机号、身份证号等必须加密存储
- **API 密钥必须通过环境变量管理** — 禁止硬编码在代码或配置文件中
- **所有外部通信必须使用 HTTPS** — 禁止 HTTP 明文传输
- **JWT 签名密钥必须 >= 256 位** — 且存储在环境变量中
- **Refresh Token 必须使用 httpOnly Secure SameSite Cookie** — 禁止存储在 localStorage
- **数据库查询必须使用参数化查询** — 禁止拼接 SQL 字符串
- **文件上传必须校验 MIME 类型和文件魔术字节** — 不可仅信任扩展名
- **生产环境必须启用 CSRF 保护** — 不可关闭
- **审计日志必须包含 request_id** — 用于全链路追踪
- **所有 API 响应头必须包含安全相关头** — CSP / HSTS / X-Content-Type-Options

## 反模式

- **禁止硬编码密钥** — 所有密钥、密码、Token 通过环境变量或密钥管理服务读取
- **禁止明文存储密码** — 即使"内部系统"也不行
- **禁止信任前端校验** — 前端校验可被绕过，后端必须独立校验
- **禁止在生产环境关闭 CSRF 保护** — 即使"暂时调试"也不行
- **禁止使用弱哈希算法** — MD5、SHA1 已不安全
- **禁止在日志中输出敏感信息** — 密码、Token、身份证号等必须脱敏
- **禁止在 URL 参数中传递敏感数据** — Token、密码等必须通过 Header 或 Body 传递
- **禁止使用默认密码** — 所有初始密码必须强制用户修改
- **禁止无限制的文件上传** — 必须限制文件大小、类型和数量
- **禁止忽略依赖库的安全漏洞** — 定期运行 `npm audit` / `pip audit`
- **禁止在错误消息中泄露系统信息** — 如数据库类型、框架版本、堆栈跟踪
- **禁止"安全是最后一步"的思维** — 安全设计必须在编码前完成