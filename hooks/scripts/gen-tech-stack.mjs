#!/usr/bin/env node
/**
 * tech-stack.md §3 结构树生成器（RULE-053 §3：清单必须派生 + --check 漂移门禁）
 * =====================================================================
 * 真源：<repo>/tools/root-structure.json（机器清单，每项含 class + reason）
 * 产出：<repo>/tech-stack.md 的 §3 结构树区块（**人读索引**，由脚本派生，不得手改）
 *
 * 为什么需要它：RULE-053 §3 要求「每仓 tech-stack.md §3 是该仓结构树在项目内的唯一描述，
 * 内容必须能由磁盘核对得出」，同时 §3.2 要求「清单类产物必须由脚本从代码/磁盘派生，并提供
 * --check 漂移门禁」。本生成器把两者接起来：机器清单 → 人读索引 → 漂移检查。
 *
 * 用法：
 *   node gen-tech-stack.mjs --root <repo> --check     # 漂移检查（退出码 1 = 漂移）
 *   node gen-tech-stack.mjs --root <repo> --apply     # 写入/更新 §3 区块
 *   node gen-tech-stack.mjs --root <repo> --init      # 创建 tech-stack.md 骨架（仅当不存在）
 *   node gen-tech-stack.mjs --selftest                # 正负例自证（临时目录，不碰工作区）
 *
 * 安全边界：只改 tech-stack.md 中两个标记之间的区块；标记外的正文（§1/§2/§4…）**一律不动**。
 */
import { existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { tmpdir } from 'node:os';

const BEGIN = '<!-- generated:tech-stack-structure begin -->';
const END = '<!-- generated:tech-stack-structure end -->';
const MANIFEST = join('tools', 'root-structure.json');
const DOC = 'tech-stack.md';

const HELP = `gen-tech-stack (RULE-053 §3 派生 + 漂移门禁)
  --root <dir>   仓根目录（默认 cwd）
  --check        只校验 §3 区块与清单一致（退出码 1 = 漂移）
  --apply        把 §3 区块写回 tech-stack.md
  --init         tech-stack.md 不存在时创建骨架
  --selftest     临时目录构造正/负例自证
  -h, --help     显示本帮助`;

function parseArgs(argv) {
  const a = { root: process.cwd(), mode: 'check', selftest: false, help: false };
  for (let i = 0; i < argv.length; i++) {
    const v = argv[i];
    if (v === '--root' && argv[i + 1]) a.root = resolve(argv[++i]);
    else if (v === '--check') a.mode = 'check';
    else if (v === '--apply') a.mode = 'apply';
    else if (v === '--init') a.mode = 'init';
    else if (v === '--selftest') a.selftest = true;
    else if (v === '-h' || v === '--help') a.help = true;
  }
  return a;
}

function readManifest(root) {
  const p = join(root, MANIFEST);
  if (!existsSync(p)) return { error: `机器清单不存在：${MANIFEST}` };
  try {
    const j = JSON.parse(readFileSync(p, 'utf8'));
    if (!j.dirs || typeof j.dirs !== 'object') return { error: `${MANIFEST} 缺少 dirs 段` };
    return { manifest: j };
  } catch (e) {
    return { error: `${MANIFEST} 解析失败：${e.message}` };
  }
}

/** 由清单生成 §3 结构树文本（人读索引） */
function buildBlock(root, manifest) {
  const names = Object.keys(manifest.dirs).sort((a, b) => a.localeCompare(b));
  const repoName = root.split(/[\\/]/).filter(Boolean).pop() || 'repo';
  const lines = [];
  lines.push(BEGIN);
  lines.push('<!-- 本区块由共享规则 hooks/scripts/gen-tech-stack.mjs 从 tools/root-structure.json 派生，勿手改。');
  lines.push('     真源 = tools/root-structure.json（机器清单，门禁判据）；改目录请同批改该清单并重跑生成器。 -->');
  lines.push(`<!-- 机器清单 generator: ${String(manifest.generator || '（未注明）').replace(/--+/g, '-')} -->`);
  lines.push('');
  lines.push('```text');
  lines.push(`${repoName}/`);
  names.forEach((name, i) => {
    const entry = manifest.dirs[name] || {};
    const cls = entry.class || 'engineering';
    const reason = String(entry.reason || '').replace(/\s+/g, ' ').trim();
    const branch = i === names.length - 1 ? '└── ' : '├── ';
    const label = `${branch}${name}${name.endsWith('/') ? '' : '/'}`;
    const pad = Math.max(2, 30 - label.length);
    lines.push(`${label}${' '.repeat(pad)}# ${cls}${reason ? '｜' + reason : ''}`);
  });
  lines.push('```');
  lines.push('');
  lines.push(`> 共 ${names.length} 个一级目录，class ∈ engineering / artifact / data / external。`);
  lines.push('> 新增或移除一级目录：改 `tools/root-structure.json` → 重跑 `node tools/gen-tech-stack.mjs --apply` → 跑根目录门禁。');
  lines.push(END);
  return lines.join('\n');
}

function replaceBlock(text, block) {
  const s = text.indexOf(BEGIN);
  const e = text.indexOf(END);
  if (s < 0 || e < s) return null;
  return text.slice(0, s) + block + text.slice(e + END.length);
}

function applyTo(root, mode) {
  const { manifest, error } = readManifest(root);
  if (error) return { ok: false, error };
  const docPath = join(root, DOC);
  if (!existsSync(docPath)) {
    if (mode !== 'init') return { ok: false, error: `${DOC} 不存在（先建文件或用 --init）` };
    mkdirSync(root, { recursive: true });
    writeFileSync(docPath, `# tech-stack.md\n\n## 3. 项目目录结构\n\n${BEGIN}\n${END}\n`, 'utf8');
  }
  const text = readFileSync(docPath, 'utf8');
  const block = buildBlock(root, manifest);
  const next = replaceBlock(text, block);
  if (next === null) return { ok: false, error: `${DOC} 缺少生成区标记（${BEGIN} / ${END}）` };
  if (next === text) return { ok: true, changed: false, docPath };
  if (mode === 'apply') {
    writeFileSync(docPath, next, 'utf8');
    return { ok: true, changed: true, docPath };
  }
  return { ok: true, changed: true, drift: true, docPath };
}

function selftest() {
  const t = mkdtempSync(join(tmpdir(), 'gentechstack-'));
  const passed = [];
  try {
    mkdirSync(join(t, 'tools'), { recursive: true });
    writeFileSync(
      join(t, MANIFEST),
      JSON.stringify({ schema: 1, generator: 'test', dirs: { worker: { class: 'engineering', reason: 'Worker 源码' }, docs: { class: 'engineering', reason: '文档' } } }, null, 2),
      'utf8',
    );
    writeFileSync(join(t, DOC), `# tech-stack.md\n\n## 3. 项目目录结构\n\n${BEGIN}\n${END}\n`, 'utf8');

    const assert = (cond, msg) => {
      if (!cond) throw new Error(msg);
      passed.push(msg);
    };

    const r1 = applyTo(t, 'apply');
    assert(r1.ok && r1.changed, '--apply 写入 §3 区块');
    const r2 = applyTo(t, 'check');
    assert(r2.ok && !r2.drift, '写入后 --check 无漂移');
    const body = readFileSync(join(t, DOC), 'utf8');
    assert(body.includes('worker/'), '生成的区块包含清单中的目录');
    assert(body.includes('Worker 源码'), '生成的区块包含 reason');

    // 清单改动 → 漂移
    writeFileSync(
      join(t, MANIFEST),
      JSON.stringify({ schema: 1, generator: 'test', dirs: { worker: { class: 'engineering', reason: 'Worker 源码' }, docs: { class: 'engineering', reason: '文档' }, tools: { class: 'engineering', reason: '工具' } } }, null, 2),
      'utf8',
    );
    const r3 = applyTo(t, 'check');
    assert(r3.ok && r3.drift, '清单新增目录后 --check 报漂移');

    // 标记缺失 → 明确报错而不是静默破坏
    writeFileSync(join(t, DOC), '# tech-stack.md\n\n## 3. 项目目录结构\n\n没有标记\n', 'utf8');
    const r4 = applyTo(t, 'apply');
    assert(!r4.ok && /标记/.test(r4.error), '缺标记时明确报错，不破坏文件');

    console.log('[selftest] PASS');
    for (const m of passed) console.log('  + ' + m);
    return 0;
  } catch (e) {
    console.error('[selftest] FAIL: ' + e.message);
    return 1;
  } finally {
    rmSync(t, { recursive: true, force: true });
  }
}

function main() {
  const a = parseArgs(process.argv.slice(2));
  if (a.help) { console.log(HELP); return 0; }
  if (a.selftest) return selftest();
  if (!existsSync(a.root)) {
    console.error(`[gentechstack] root 不存在: ${a.root}`);
    return 2;
  }
  const r = applyTo(a.root, a.mode);
  if (!r.ok) {
    console.error(`[gentechstack] ${r.error}`);
    return 2;
  }
  if (r.drift) {
    console.error(`[gentechstack] DRIFT — ${DOC} 的 §3 区块与 ${MANIFEST} 不一致；跑 --apply 更新`);
    return 1;
  }
  console.log(`[gentechstack] ${a.mode === 'apply' ? (r.changed ? '已更新' : '无变化') : 'OK'} — ${DOC} §3 与 ${MANIFEST} 一致`);
  return 0;
}

process.exitCode = main();
