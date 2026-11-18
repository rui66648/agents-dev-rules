---
name: cloudbox-rules
version: v1.0.0
type: rule
enabled: true
mode: [standard, creator]
updated: 2026-11-16
description: 云电脑（InstaBox）接入与开发流程规范（RULE-059）
applies_to:
  agents: ['all']
  phases: ['implementation', 'testing', 'deploy']
  project_types: ['全部']
  tech_stacks: ['全部']
---

# 云电脑（InstaBox）接入与开发流程规范

> **本文件落实**: RULE-059（云电脑接入遵循 cloudbox-rules.md）

> **版本**: v1.0.0 | **更新**: 2026-11-16

---

## 0. 适用边界

本规则约束所有在 InstaBox（instabox.sh）云电脑上进行的开发、测试、部署、数据处理任务。适用于 `agent-browser`、`universal`、`t3`、`android`、`omarchy`、`ci` 等模板；不约束本地开发环境。

核心前提（已实测）：你的云电脑 `rui`（4 vCPU / 8 GiB，Debian 13，Firecracker 微 VM）出口 IP 位于**美国俄勒冈州（AWS us-west-2）**，可直达 ChatGPT、GitHub 等海外服务；免费档 1 台机器、30 分钟空闲自动暂停、单次运行上限约 480 分钟、暂停/停止不收费。

---

## 1. 适合 / 不适合的任务（先判，再开机）

| 类型 | 适合在云电脑跑 | 不适合在云电脑跑 |
|------|----------------|------------------|
| AI 编码 Agent（Claude Code / Codex / OpenCode） | ✅ 预装，可长期挂云端执行 | |
| 远程开发（拉代码、装依赖、跑单测、编译构建） | ✅ Node 22 / Go / Rust / Python / Java 21 全预装 | |
| Web 前端开发 + 预览（端口发布 HTTPS URL） | ✅ `instabox port publish` 直接给外网 URL | |
| 浏览器自动化（Playwright / Puppeteer / Selenium） | ✅ 预装 Chromium + Xfce 桌面 + VNC | |
| 需要美国 IP 的网络任务（海外 API、地区差异测试） | ✅ 出口 IP 美国 | |
| 临时/一次性算力（`instabox run` 用完即删） | ✅ 免费档 1 台，跑完删除 | |
| 环境隔离实验（装不确定软件、跑陌生脚本） | ✅ 删机重建，不污染本地 | |
| Windows 桌面软件 / Microsoft Store 应用 | | ❌ Linux 系统，无 Windows |
| 3A 游戏 / 游戏直播 | | ❌ 无独立显卡，图形性能有限 |
| WSL2 / Docker 嵌套虚拟化 / 安卓模拟器 | | ❌ 机器本身即 VM，不支持二次虚拟化 |
| 24/7 常驻服务器 | | ❌ 免费档 30 分钟空闲自暂停，单次运有时长上限 |
| 大模型训练 / 显卡密集型任务 | | ❌ 8 GiB 内存，免费档无 GPU |
| 大文件长期存储 / 当网盘 | | ❌ 20 GiB 磁盘固定，免费档存储上限 200 GiB |

---

## 2. 连接云电脑（标准流程）

### 2.1 前置：确认机器存在且可达

```powershell
# 在本地（有 instabox CLI 的机器上）执行
instabox whoami
instabox ls
```

预期看到名为 `rui` 的机器，`state` 为 `suspended` 或 `running`。

### 2.2 唤醒 / 启动机器

```powershell
instabox wake rui        # 被自动暂停的机器唤醒（约几秒）
# 或若机器是 stopped / suspended 且非你手动暂停：
instabox resume rui
instabox start rui
```

### 2.3 进入桌面（推荐）

1. 打开 [dashboard.instabox.sh](https://dashboard.instabox.sh)
2. 进入 `rui` 机器详情 → **Computer** 标签
3. 点击屏幕即可接管鼠标键盘（约 1 分钟无操作后控制权归还机器）
4. 在桌面 Chromium 里打开 `chatgpt.com`，登录账号即可

### 2.4 进入终端（脚本 / API 调用）

```powershell
instabox ssh rui                      # 交互式 shell
instabox ssh rui -- uname -a          # 执行一条命令并返回
instabox exec rui -- "curl -s https://api.ipify.org"   # 无需 SSH 客户端
```

### 2.5 端口转发 / 发布（给服务一个可访问的 URL）

```powershell
# 本地访问机器内服务（私密，仅你可见）
instabox port-forward rui 5901        # 本地 5901 ↔ 机器 5901（VNC）

# 给机器内 Web 服务一个公网 HTTPS URL（需先在机器内启动服务）
instabox port publish rui 3000 --name "Web app"
```

> **禁止**：不要 `instabox port publish rui 5901` 把 VNC 端口发布为公网 URL——等于把桌面裸奔到公网。

---

## 3. 在云电脑上开发的标准流程

以下流程适用于在 `rui` 上进行代码开发、测试、提交：

### 3.1 进入机器并准备工作区

```bash
# 在机器内（ssh 后执行）
cd /data                    # 持久化盘，家目录 /data/home
mkdir -p /data/workspace
cd /data/workspace
```

### 3.2 拉取 / 推送代码

优先使用机器内预装的 `gh`（GitHub CLI）或 `git`：

```bash
git clone <仓库地址>        # 或 git pull / git fetch
# 提交后推送（注意：机器内 git 需要你的 GitHub 凭据，建议用个人访问 token，不要硬编码密码）
git push origin <分支>
```

### 3.3 安装依赖与构建

```bash
# 示例：Node.js 项目（Node 22 + npm/pnpm/yarn 均预装）
npm install
npm run build
npm run typecheck
npm test
```

### 3.4 预览前端（端口发布）

```bash
# 在机器内启动前端服务（监听 3000）
npm run dev -- --host 0.0.0.0 --port 3000

# 在另一终端（本地）发布公网 URL
instabox port publish rui 3000 --name "前端预览"
```

### 3.5 提交与收尾

1. 所有代码变更必须通过 `typecheck` + 测试（与本地开发标准一致）
2. commit 信息按共享规则 `rules/git-conventions.md` 编写，并带 `Agent: <工具>-<角色>` trailer（若由 AI 工具提交）
3. `git push` 仅作代码备份，**不触发部署**；部署仍走项目各自的 `deploy/deploy.ps1`（或 `deploy/cloudflare/deploy.ps1`）

---

## 4. 免费档限制与避坑

| 限制 | 说明 | 应对 |
|------|------|------|
| 30 分钟空闲自动暂停 | 无操作 30 分钟机器自暂停 | `instabox wake rui` 恢复，进程与登录态保留 |
| 单次运行上限约 480 分钟 | 运行满自暂停 | 同上，重新 `wake` / `resume` |
| 1 台机器上限 | 免费档同一时间仅 1 台 | 不需要新机时 `rm` 旧机再建新机 |
| 20 GiB 磁盘固定 | `/data` 持久，不可扩容 | 大文件传完处理后删除，不当长期存储 |
| VNC 仅监听 127.0.0.1 | 桌面端口不向公网暴露 | 用 `instabox port-forward` 或 Dashboard Computer 标签访问 |
| 不支持二次虚拟化 | 无 WSL2 / Docker 嵌套 / 安卓模拟器 | 需容器能力用机器内预装的 Docker（非嵌套） |

---

## 5. 安全与合规

1. **不要硬编码密钥**：OpenAI Key、GitHub Token 等凭据不得写入代码，使用机器环境变量或 `.env`（`.gitignore` 排除）。
2. **账号地区一致**：OpenAI ToS 要求账号地区与使用地一致；云电脑出口 IP 为美国，登录 ChatGPT 时若账号绑定为其他地区可能触发验证或风控，风险自行承担。
3. **不跨境传输敏感数据**：不得在云电脑上处理含个人隐私、商业机密、受出口管制的数据，除非已完成合规评估。
4. **及时暂停/停机**：不用时 `instabox suspend rui` 或 `instabox stop rui`，避免无意义运行消耗免费时长。

---

## 6. Enforcement（门禁）

| 检查点 | 执行方式 | 不通过后果 |
|--------|----------|------------|
| 开机前任务适配性 | 人工核对 §1 适合/不适合列表 | 不适合的任务不得在云电脑执行 |
| 连接后桌面/终端可达 | `instabox exec rui -- curl chatgpt.com` 返回 HTTP 200 | 无法访问即不继续后续开发任务 |
| 代码变更验证 | `npm run typecheck` + `npm test`（或项目等价命令） | 任一 FAIL 不声称完成 |
| 提交规范 | commit 信息含 `Agent:` trailer（AI 工具提交时） | 缺失 trailer 视为归因缺失，人工补登 |

---

## 7. 相关引用

- InstaBox 官方文档：https://instabox.sh/docs（`/docs/llms.txt` 为完整索引）
- CLI 参考：https://instabox.sh/docs/reference/cli.md
- 桌面/端口：https://instabox.sh/docs/desktop.md、https://instabox.sh/docs/access/ports.md
- 共享规则入口：`<RULES_ROOT>\AGENTS.md`
- 项目部署纪律：各项目 `deploy/cloudflare/deploy.ps1` 或 `deploy/deploy.ps1`
