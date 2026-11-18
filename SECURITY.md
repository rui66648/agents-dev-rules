# 安全策略

## 支持版本

本仓库处于活跃维护状态，规则与门禁的修复会及时发布。

| 版本 | 状态 |
|------|------|
| 最新 `main` 分支 | ✅ 支持 |
| 更早版本 | ❌ 不支持 |

## 报告安全问题

**请勿通过公开 GitHub Issue 报告安全问题。**

请通过 GitHub 的 [Private vulnerability reporting](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability) 提交私密报告。

若该功能不可用，请通过 GitHub 用户主页的联系方式私下联系维护者。

请在报告中说明：

- 问题类型与影响范围
- 复现步骤或触发条件
- 受影响的文件 / 版本
- 你建议的修复方向（可选）

维护者会在收到报告后尽快确认，并协调修复与披露。

## 门禁脚本的安全边界

本仓库的门禁脚本是**本地开发辅助工具**，请注意以下边界：

### 明确不做的事

门禁脚本**不会**：
- 执行来自仓库内容的任意代码（不 `eval` / `exec` 仓库内文件）
- 访问网络（不联网校验、不上报数据）
- 读取仓库目录之外的文件（除显式传入的路径参数）
- 修改或删除用户文件——所有写操作均为 `--apply` 显式开启，且默认只读

### 需要注意的事

| 脚本 | 行为 | 注意 |
|------|------|------|
| `hooks/scripts/archive-scratch.ps1` | **移动**指定目录到归档区 | 需显式传 `-Root`；归档而非删除，但会影响目标路径 |
| `hooks/scripts/root-cleanliness-check.mjs --apply` | 移动根级散文件 | 仅 `--apply` 时生效，默认只读报告 |
| `hooks/scripts/creation-gate.mjs` | 校验新建文件落点 | 只读校验，不阻断文件系统 |
| `scripts/init-project-rules.ps1` | 在目标项目创建 Junction / 指针 | 需管理员权限（Windows）；目标路径由调用方指定 |

**执行前请确认参数指向的路径**。所有脚本对不存在的路径会 fail-closed（报错退出），不会静默跳过。

### 信任边界

门禁脚本运行在你的项目目录下，读取项目文件以做校验。请在可信的项目中使用——这与运行项目自身的构建脚本是同一信任级别。

## 密钥管理

本仓库**不存储任何密钥**。

- 仓库中所有配置均为占位符（`your-key-here`、`sk-change-me-to-random-string` 等）
- 需要真实密钥时，通过环境变量或项目本地的 `.env`（已被 `.gitignore` 排除）注入
- `hooks/scripts/pre-commit-secret-scan.js` 提供提交前的密钥扫描兜底

若你误提交了密钥，请立即：
1. **吊销 / 轮换该密钥**（删除 git 历史不足以止损，密钥必须作废）
2. 清理历史：`git filter-repo --path <file> --invert-paths` 或 BFG
3. 强制推送并通知协作者重新克隆
