#!/usr/bin/env node
// hooks/scripts/post-test.js
// 确定性强制：RULE-013（禁止跳过测试声称"完成"）
// 在 pytest / vitest / jest / unittest 命令执行后校验结果，失败则阻断
// （PostToolUse 非零退出即阻止会话继续声明完成）。
//
// 判定策略（按优先级）：
//   1. 从 hook 上下文 tool_response 中读取输出文本，解析失败标记
//   2. 从 tool_response 的 exit code / is_error 判定
//   3. 仅当以上均无法判定且命令确实为测试命令时，才兜底重跑一次确认
// 对非测试命令（未匹配 matcher）直接放行，零副作用。

const { execSync } = require('child_process');
const fs = require('fs');

function readContext() {
  try {
    const raw = fs.readFileSync(0, 'utf-8');
    return raw ? JSON.parse(raw) : {};
  } catch (e) {
    return {};
  }
}

// 从任意层级的对象中提取所有字符串值（用于扫描失败标记）
function collectStrings(obj, acc) {
  if (obj == null) return acc;
  if (typeof obj === 'string') { acc.push(obj); return acc; }
  if (typeof obj === 'number' || typeof obj === 'boolean') { acc.push(String(obj)); return acc; }
  if (Array.isArray(obj)) { obj.forEach((x) => collectStrings(x, acc)); return acc; }
  if (typeof obj === 'object') {
    Object.values(obj).forEach((x) => collectStrings(x, acc));
  }
  return acc;
}

// 识别测试失败标记（pytest / vitest / jest / unittest 通用）
const FAILURE_PATTERNS = [
  /(\d+)\s+failed\b/i,          // pytest: "3 failed" / vitest: "1 failed"
  /FAILURES/i,                  // pytest: "== FAILURES =="
  /\bFAIL\b/i,                  // pytest 单测行 / jest
  /Tests:\s+\d+\s+failed/i,     // vitest 汇总
  /(\d+)\s+failing\b/i,         // jest: "1 failing"
  /AssertionError/i,
  /Traceback \(most recent call last\)/i,
  /^E\s+/,                      // pytest 断言错误行
  /ERROR:\s+\d+\s+failed/i,
];

function detectFailure(text) {
  if (!text) return false;
  return FAILURE_PATTERNS.some((re) => re.test(text));
}

function resolveExitCode(obj) {
  // 常见字段名：exit_code / exitCode / exit / code / status
  for (const k of ['exit_code', 'exitCode', 'exit', 'code', 'status']) {
    if (obj && obj[k] !== undefined && typeof obj[k] === 'number') return obj[k];
  }
  return null;
}

function main() {
  const ctx = readContext();
  const cmd = (ctx.tool_input && ctx.tool_input.command) || ctx.command || '';
  if (!/pytest|vitest|unittest|jest/.test(cmd)) process.exit(0);

  const resp = ctx.tool_response || {};

  // 1) 失败标记显式存在
  if (resp.is_error === true || resp.isError === true) {
    process.stderr.write('\n[Hook] 测试失败，禁止声称"完成"。RULE-013\n');
    process.exit(2);
  }

  // 2) 从输出文本解析失败标记
  const strings = collectStrings(resp, []);
  if (strings.some(detectFailure)) {
    process.stderr.write('\n[Hook] 测试输出含失败标记，禁止声称"完成"。RULE-013\n');
    process.exit(2);
  }

  // 3) 非零退出码
  const code = resolveExitCode(resp);
  if (code !== null && code !== 0) {
    process.stderr.write('\n[Hook] 测试以非零退出码结束，禁止声称"完成"。RULE-013\n');
    process.exit(2);
  }

  // 4) 兜底：无任何输出/无法判定时，仅对确定性测试命令重跑一次确认
  //    标记为幂等短命令（如 pytest 单模块）才重跑，避免有副作用的长测试被重复执行
  if (strings.length === 0 && /pytest\s+\S+\.py|pytest\s+-q/i.test(cmd)) {
    try {
      execSync(cmd, { stdio: 'inherit' });
    } catch (e) {
      process.stderr.write('\n[Hook] 测试失败，禁止声称"完成"。RULE-013\n');
      process.exit(2);
    }
  }

  process.exit(0);
}

main();