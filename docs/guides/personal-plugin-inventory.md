# 个人常用插件清单 (Personal Plugin Inventory) v1.0.0

> **生成时间**: 2026-08-15
> **落实规则**: RULE-042（插件组装优先）、RULE-043（插件清单合规）
> **用途**: 记录个人日常开发最常用的 MCP 服务器、开源组件和规则体系内插件，下次开发直接 L1 复用，避免重复造轮子。

---

## 一、使用方式

遇到能力需求时，**先查本清单**，按 L1→L5 顺序决策：

```
L1 本清单已有？ → 直接复用
L2 开源组件？   → 引入成熟库
L3 MCP 插件？   → 使用标准接口
L4 自建插件？   → 遵循插件接口规范
L5 硬编码？     → 一次性逻辑才允许
```

---

## 二、常用 MCP 服务器（L3 层）

| MCP 服务器 | 功能 | 安装命令 | 状态 |
|-----------|------|---------|------|
| `filesystem` | 文件系统操作 | `claude mcp add filesystem npx -y @modelcontextprotocol/server-filesystem` | 推荐 |
| `postgres` | PostgreSQL 操作 | `claude mcp add postgres npx -y @modelcontextprotocol/server-postgres` | 推荐 |
| `github` | GitHub API | `claude mcp add github npx -y @modelcontextprotocol/server-github` | 按需 |
| `chrome-devtools` | 浏览器自动化 | `claude mcp add chrome-devtools npx chrome-devtools-mcp@latest` | 按需 |
| `web-search` | 网络搜索 | `claude mcp add web-search npx -y @modelcontextprotocol/server-web-search` | 按需 |

> **配置位置**: `~/.claude/mcp.json` / `~/.cursor/mcp.json` / `~/.trae/mcp.json`

---

## 三、常用开源组件（L2 层）

### 后端（Python 3.11+ / FastAPI）

| 能力 | 首选组件 | 替代方案 | License |
|------|---------|---------|---------|
| Web 框架 | FastAPI | Flask / Django | MIT |
| ORM | SQLAlchemy 2.0 (Async) | Peewee | MIT |
| 迁移 | Alembic | — | MIT |
| 校验 | Pydantic v2 | — | MIT |
| 结构化日志 | structlog | logging | MIT/Apache-2.0 |
| 配置管理 | pydantic-settings | python-dotenv | MIT |
| 密码哈希 | argon2-cffi | bcrypt | MIT |
| 任务队列 | Celery / ARQ | Dramatiq | BSD-3 |
| 缓存 | Redis (redis-py) | Memcached | BSD-3 |
| 测试 | pytest + pytest-asyncio | unittest | MIT |
| 静态检查 | Ruff | Black + Flake8 | MIT |
| 安全扫描 | bandit | Semgrep | Apache-2.0 |
| 图计算 | NetworkX | igraph | BSD-3 |

### 前端（React 18+ / TypeScript / Vite）

| 能力 | 首选组件 | 替代方案 | License |
|------|---------|---------|---------|
| UI 组件 | shadcn/ui | Ant Design / MUI | MIT |
| 样式 | Tailwind CSS | CSS Modules | MIT |
| 状态管理 | TanStack Query + Zustand | Redux Toolkit | MIT |
| 图表 | Recharts | ECharts / Chart.js | MIT |
| 表单 | React Hook Form + Zod | Formik | MIT |
| 动画 | Framer Motion | GSAP | MIT |
| 测试 | Vitest + Testing Library | Jest | MIT |
| 构建 | Vite | Webpack / Rspack | MIT |

### 数据库与基础设施

| 能力 | 首选组件 | 替代方案 | License |
|------|---------|---------|---------|
| 数据库 | PostgreSQL 15+ | SQLite（开发） | PostgreSQL |
| 向量检索 | pgvector | — | PostgreSQL |
| 对象存储 | MinIO（自托管） | Cloudflare R2 | AGPL→Apache（注意） |
| 容器化 | Docker Compose | Podman | Apache-2.0 |
| 反向代理 | Nginx | Caddy | BSD-2 |

### AI/ML 集成

| 能力 | 首选组件 | 替代方案 | License |
|------|---------|---------|---------|
| LLM 调用 | LiteLLM Proxy | OpenAI SDK | MIT |
| RAG | LlamaIndex | LangChain | MIT |
| 本地 LLM | Ollama | llama.cpp | MIT |
| 向量库 | pgvector | Qdrant / Milvus | 混合 |

---

## 四、规则体系内高频插件（L1 层）

### 高频技能（日常必用）

| 技能 | 触发场景 | 输出 |
|------|---------|------|
| `brainstorming` | 新功能/需求探索 | 设计文档 + HOTL 合约 |
| `system-design` | 架构设计 | 设计文档 |
| `test-driven-development` | 实现新功能 | RED→GREEN→REFACTOR |
| `code-review` | 合并前审查 | 审查报告 |
| `verification` | 声称"完成"前 | 验证证据 |
| `systematic-debugging` | 遇到 Bug | 根因分析 |
| `ai-safety-check` | AI 生成代码后 | 安全扫描报告 |
| `executing-plans` | 实施计划 | 逐步执行 |

### 高频规则（铁律）

| 规则 | 落实 RULE | 内容 |
|------|----------|------|
| `security-rules` | 008/009/010/016 | 安全铁律 |
| `open-source-first` | 017/018/019/042 | 开源优先 + 插件组装 |
| `testing-rules` | 003/013 | TDD + 测试门禁 |
| `git-conventions` | 011/012 | Git 规范 |
| `hotl-contracts` | 004 | 完成前验证 |

### 高频命令

| 命令 | 映射技能 | 用途 |
|------|---------|------|
| `/brainstorm` | brainstorming | 需求探索 |
| `/plan` | writing-plans | 生成实施计划 |
| `/test` | test-driven-development | TDD 循环 |
| `/review` | code-review | 代码审查 |
| `/verify` | verification | 完成验证 |
| `/debug` | systematic-debugging | 调试 |

### 高频 Agent

| Agent | 负责领域 |
|-------|---------|
| `architect` | 架构设计、需求探索 |
| `backend-developer` | 后端开发 |
| `frontend-developer` | 前端开发 |
| `verifier` | 完成验证 |

---

## 五、新增插件登记流程

引入新的开源组件/插件后，**登记到本清单**：

1. 确认 License 合规（白名单 MIT/Apache-2.0/BSD）
2. 记录：能力 → 首选组件 → 替代方案 → License
3. 更新 `plugins/registry.yaml`（如需作为规则体系插件）
4. 运行校验：`python hooks/scripts/plugin-validator.py --check-all`

---

## 六、快速决策示例

| 需求 | 决策路径 | 结果 |
|------|---------|------|
| 需要文件操作 | L1 → 本清单 MCP filesystem | 直接用 MCP |
| 需要图表 | L1 → Recharts | 直接用组件 |
| 需要结构化日志 | L1 → structlog | 直接用库 |
| 需要工作流引擎 | L2 → Prefect / Airflow | 引入开源 |
| 需要自定义技能 | L4 → 遵循插件接口规范 | 自建插件 |

---

> **维护原则**: 本清单是动态文档，每引入一个新组件就登记一条，保持"常用即记录"。
