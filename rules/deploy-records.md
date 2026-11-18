---
name: deploy-records
version: v1.1.0
type: rule
enabled: true
mode: [standard, creator]
updated: 2026-08-08
description: 部署记录规范 — 每次部署必须记录版本/变更/回滚点
applies_to:
  agents: ['backend-developer', 'architect']
  phases: ['deploy']
  project_types: ['全部']
  tech_stacks: ['全部']
---
# 部署记录规范 (Deploy Records)

> **核心原则**: 首次部署写详细（含凭证占位符），后续部署只更新版本号/时间/URL。其他 AI 读 `.deployed.json` 即可，无需翻阅文档。

---

## 两种模式

| 模式 | 触发条件 | 操作 |
|------|---------|------|
| **首次详细** | `.deployed.json` 不存在 | 写完整记录 + 凭证占位符 + 回滚命令 |
| **后续极简** | `.deployed.json` 已存在 | 只更新 version/deployedAt/healthCheck |

---

## 首次详细格式（含凭证占位符）

```json
{
  "version": "1.5.5",
  "deployedAt": "2026-08-08T10:30:00+08:00",
  "deployedBy": "human",
  "environment": "production",
  "credentials": {
    "cloudflare": {
      "accountId": "<<CLOUDFLARE_ACCOUNT_ID>>",
      "apiToken": "<<CLOUDFLARE_API_TOKEN>>"
    }
  },
  "build": {
    "tag": "v1.5.5",
    "commitSha": "abc1234",
    "artifacts": {
      "apk": {
        "filename": "PulseBreath-v1.5.5.apk",
        "size": 14538537,
        "url": "https://pub-xxx.r2.dev/PulseBreath-v1.5.5.apk",
        "latestAlias": "https://pub-xxx.r2.dev/PulseBreath-latest.apk"
      }
    }
  },
  "deployedTo": {
    "cloudflare": {
      "pages": {
        "site": "lifestyle-assistant",
        "url": "https://lifestyle-assistant.pages.dev"
      },
      "r2": {
        "bucket": "lifestyle-assistant-apk",
        "publicUrl": "https://pub-xxx.r2.dev"
      }
    }
  },
  "previousVersion": null,
  "rollback": {
    "command": "wrangler pages deployment rollback --site=lifestyle-assistant --deployment-id=PREV_ID",
    "artifactBackup": "git tag v1.5.4"
  },
  "healthCheck": {
    "url": "https://lifestyle-assistant.pages.dev/",
    "status": "pending",
    "checkedAt": null
  }
}
```

### 凭证占位符规则

- 格式：`<<PLACEHOLDER_NAME>>`
- **禁止**写入真实密码/Token
- 首次部署时由人工填入真实值，或通过 `wrangler secret` 管理
- 常见占位符：
  - `<<CLOUDFLARE_ACCOUNT_ID>>` — Cloudflare 账户 ID
  - `<<CLOUDFLARE_API_TOKEN>>` — Cloudflare API Token
  - `<<R2_PUBLIC_URL>>` — R2 公开访问域名
  - `<<DATABASE_URL>>` — 数据库连接串
  - `<<JWT_SECRET>>` — JWT 密钥

---

## 后续极简格式（仅更新字段）

```json
{
  "version": "1.5.6",
  "deployedAt": "2026-08-09T14:00:00+08:00",
  "previousVersion": "1.5.5"
}
```

只更新这 3 个字段，其余保持不变。

---

## 按部署类型的最小字段

### Cloudflare Pages + R2

```json
{
  "version": "1.5.5",
  "deployedAt": "2026-08-08T10:30:00+08:00",
  "deployedTo": {
    "cloudflare": {
      "pages": { "url": "https://app.pages.dev" },
      "r2": { "bucket": "app-apk", "publicUrl": "https://pub-xxx.r2.dev" }
    }
  },
  "previousVersion": null,
  "rollback": { "command": "wrangler pages deployment rollback --site=app --deployment-id=PREV" }
}
```

### Cloudflare Workers

```json
{
  "version": "2.0.0",
  "deployedAt": "2026-08-08T10:30:00+08:00",
  "deployedTo": {
    "cloudflare": {
      "workers": { "script": "my-worker", "url": "https://my-worker.xxx.workers.dev" }
    }
  },
  "previousVersion": "1.9.0",
  "rollback": { "command": "wrangler deploy --name my-worker --older-version" }
}
```

### Docker Compose（服务器部署）

```json
{
  "version": "3.1.0",
  "deployedAt": "2026-08-08T10:30:00+08:00",
  "deployedTo": {
    "server": { "host": "your-server.com", "url": "https://your-server.com" }
  },
  "previousVersion": "3.0.0",
  "rollback": { "command": "docker compose down && docker compose up -d --no-build" }
}
```

---

## 其他 AI 识别流程

```
1. 检查项目根目录 .deployed.json
   ├── 存在 → 读取 version/deployedTo/rollback，5 秒内了解部署状态
   └── 不存在 → 检查 docs/deployment-design.md / .github/workflows/*.yml
                 → 仍无则标记"部署状态未知"，提示用户补充

2. 需要继续部署时：
   ├── 有 .deployed.json → 读取 rollback.command 作为回滚参考
   ├── 有 credentials → 检查是否需要更新凭证
   └── 无 → 按首次详细格式创建
```

---

## 强制规则

| 编号 | 规则 |
|------|------|
| DR-001 | 首次部署必须写完整 `.deployed.json`（含凭证占位符） |
| DR-002 | 后续部署只更新 version/deployedAt/previousVersion |
| DR-003 | 禁止在 `.deployed.json` 中写入真实密码，用 `<<PLACEHOLDER>>` |
| DR-004 | `.deployed.json` 必须提交到仓库，禁止加入 `.gitignore` |

---

## tech-stack.md 中的部署记录章节

每个项目的 `tech-stack.md` 末尾添加：

```markdown
## 部署记录

- 记录文件: `.deployed.json`
- 格式版本: v1.1.0
- 上次部署: 2026-08-08 (v1.5.5 → Cloudflare Pages + R2)
- 回滚方式: `wrangler pages deployment rollback --site=lifestyle-assistant`
```

---

## 禁止事项

- ❌ 部署后不写 `.deployed.json`
- ❌ 在 `.deployed.json` 中写入真实密码/Token
- ❌ `.deployed.json` 中加入 `.gitignore`
- ❌ 版本超过 30 天未更新（需人工确认）
