import { appendFileSync, mkdirSync } from 'node:fs';
import { hostname } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

// hooks/scripts/lib → hooks/scripts → hooks → 规则库根
const HERE = dirname(fileURLToPath(import.meta.url));
const RULES_ROOT = resolve(HERE, '..', '..', '..');

/** 记录 schema 的唯一文字定义见 scripts/gate_runs.py 顶部注释；此处字段必须保持一致。 */
export const GATE_LOG_DIR = join(RULES_ROOT, 'logs', 'gate-runs');

export function utcNow() {
  return new Date().toISOString().replace(/\.\d{3}Z/, 'Z');
}

/**
 * 追加一条门禁运行记录。写失败时抛出异常 —— 调用方必须捕获、写 stderr 并按 FAIL 退出。
 * @param {object} input
 * @param {string} input.gateId
 * @param {'dry-run'|'apply'} input.mode
 * @param {'scheduled'|'manual'|'hook'} [input.trigger]
 * @param {'PASS'|'FAIL'|'ERROR'} input.result
 * @param {string[]} [input.ruleIds]
 * @param {object} [input.evidence]
 * @param {string} [input.startedAt]
 * @param {number} input.exitCode
 * @returns {string} 记录文件路径
 */
export function recordGateRun({
  gateId,
  mode,
  trigger = 'manual',
  result,
  ruleIds = [],
  evidence = {},
  startedAt,
  exitCode,
}) {
  const now = utcNow();
  const record = {
    gate_id: gateId,
    mode,
    trigger,
    result,
    rule_ids: ruleIds,
    evidence,
    started_at: startedAt || now,
    finished_at: now,
    exit_code: Number(exitCode),
    host: hostname(),
  };
  mkdirSync(GATE_LOG_DIR, { recursive: true });
  const file = join(GATE_LOG_DIR, `${now.slice(0, 7).replace('-', '')}.jsonl`);
  appendFileSync(file, `${JSON.stringify(record)}\n`, 'utf8');
  return file;
}
