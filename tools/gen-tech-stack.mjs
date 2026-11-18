#!/usr/bin/env node
/**
 * RULE-053 §3 tech-stack 结构树生成器 · 启动器（本仓不留第二份实现）
 * ============================================================
 * 规范唯一实现：**本仓** `hooks/scripts/gen-tech-stack.mjs`
 *   —— 真源 = 本仓 `tools/root-structure.json`（机器清单，class + reason）
 *   —— 产出 = 本仓 `tech-stack.md` 的 §3 结构树区块（人读索引，由脚本派生，勿手改）
 *   —— 自带 `--selftest` 正负双向自证，防止门禁给出假绿
 *
 * 其他仓（<repo-a>、<repo-b> 等）用同名 `tools/gen-tech-stack.mjs` 启动器
 * 委派到**共享规则根**的同一份实现，避免第二份实现漂移。
 *
 * 用法：node tools/gen-tech-stack.mjs [--check|--apply|--init|--selftest]
 */
import { spawnSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const candidates = [
  process.env.RULES_ROOT && join(process.env.RULES_ROOT, 'hooks', 'scripts', 'gen-tech-stack.mjs'),
  join(resolve(here, '..'), 'hooks', 'scripts', 'gen-tech-stack.mjs'),
].filter(Boolean);
const impl = candidates.find((p) => existsSync(p));

if (!impl) {
  console.error('[gentechstack] FAIL — 未找到规则库根实现（hooks/scripts/gen-tech-stack.mjs）');
  process.exit(1);
}

const r = spawnSync(process.execPath, [impl, '--root', resolve(here, '..'), ...process.argv.slice(2)], { stdio: 'inherit' });
process.exit(r.status ?? 1);
