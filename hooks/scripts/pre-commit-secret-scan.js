#!/usr/bin/env node
// hooks/scripts/pre-commit-secret-scan.js
// 确定性强制：RULE-008（严禁硬编码密钥）/ RULE-016（提交前安全检查）
// 在 git commit 前扫描暂存区 diff，命中疑似密钥即阻断提交。
// 退出码 2 = 阻断（PreToolUse 非零退出即阻止工具执行）。

const { execSync } = require('child_process');

// 疑似密钥：key/secret/token/password/private_key 后跟 >=8 位引号包裹的密文
const SECRET_RE = /(api[_-]?key|secret|token|access[_-]?token|password|passwd|私钥|private[_-]?key)\s*[:=]\s*['"][^'"]{8,}/i;
// 排除明显的占位/示例值，避免误伤
const PLACEHOLDER_RE = /(your[_-]?|example|sample|xxxx|change[_-]?me|placeholder|<|>|\\$\{)/i;

function main() {
  let diff = '';
  try {
    diff = execSync('git diff --cached', { encoding: 'utf-8' });
  } catch (e) {
    // 非 git 仓库或 git 不可用：放行，交由 CI 兜底
    process.exit(0);
  }
  if (!diff) process.exit(0);

  for (const line of diff.split('\n')) {
    if (!line.startsWith('+')) continue; // 仅检查新增行
    const text = line.slice(1);
    if (SECRET_RE.test(text) && !PLACEHOLDER_RE.test(text)) {
      const masked = text.replace(/(.{4}).*(.{4})/, '$1****$2');
      process.stderr.write(
        '\n[Hook] 检测到疑似硬编码密钥，提交被阻断。RULE-008/016\n' +
        '[Hook] 命中行（已脱敏）: ' + masked + '\n' +
        '[Hook] 请将密钥移入环境变量 / 密钥管理服务，并提交 .env.example。\n'
      );
      process.exit(2);
    }
  }
  process.exit(0);
}

main();
