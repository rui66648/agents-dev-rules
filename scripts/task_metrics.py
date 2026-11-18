#!/usr/bin/env python3
"""
scripts/task_metrics.py - L2 执行指标采集

在 SPEC 任务完成时记录执行指标（耗时 / Token / 通过率）到
docs/metrics/task-metrics.jsonl，供执行链路量化与复盘。

用法：
  python scripts/task_metrics.py record \
      --task TASK-20260811-001 \
      --title "阶段2 验证闭环" \
      --duration-sec 1200 \
      --token-in 15000 --token-out 3000 \
      --tests-total 12 --tests-passed 12
  python scripts/task_metrics.py report [--task TASK-xxx]

退出码：0 = 成功；2 = 参数错误 / 写入失败
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Windows GBK 控制台兼容：强制 UTF-8 输出，避免打印 ⚠/✗/✓/中文时 UnicodeEncodeError
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

_METRICS_FILE = Path(__file__).resolve().parent.parent / 'docs' / 'metrics' / 'task-metrics.jsonl'


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()


def record(args) -> int:
    entry = {
        'timestamp': _ts(),
        'task_id': args.task,
        'title': args.title,
        'status': 'done',
        'duration_sec': args.duration_sec,
        'token_in': args.token_in,
        'token_out': args.token_out,
        'tests_total': args.tests_total,
        'tests_passed': args.tests_passed,
        'pass_rate': round((args.tests_passed / args.tests_total), 4) if args.tests_total else 0.0,
    }
    _METRICS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(_METRICS_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    print(f'[metrics] 已记录任务指标: {args.task} '
          f'(耗时 {args.duration_sec}s, 通过率 {entry["pass_rate"]:.0%})')
    return 0


def report(args) -> int:
    if not _METRICS_FILE.exists():
        print('[metrics] 暂无任务指标数据')
        return 0
    rows = []
    for line in _METRICS_FILE.read_text(encoding='utf-8').splitlines():
        if line.strip():
            rows.append(json.loads(line))
    if args.task:
        rows = [r for r in rows if r['task_id'] == args.task]
    if not rows:
        print(f'[metrics] 未找到任务 {args.task} 的指标')
        return 0
    print(f'[metrics] 共 {len(rows)} 条任务指标：')
    for r in rows:
        print(f"  - {r['task_id']} | {r['title']} | 耗时 {r['duration_sec']}s | "
              f"Token {r['token_in']}/{r['token_out']} | 通过率 {r['pass_rate']:.0%}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description='L2 执行指标采集')
    sub = parser.add_subparsers(dest='cmd')
    r = sub.add_parser('record', help='记录一条任务指标')
    r.add_argument('--task', required=True)
    r.add_argument('--title', default='')
    r.add_argument('--duration-sec', type=int, default=0)
    r.add_argument('--token-in', type=int, default=0)
    r.add_argument('--token-out', type=int, default=0)
    r.add_argument('--tests-total', type=int, default=0)
    r.add_argument('--tests-passed', type=int, default=0)
    r.set_defaults(func=record)

    p = sub.add_parser('report', help='导出任务指标')
    p.add_argument('--task', default=None)
    p.set_defaults(func=report)

    args = parser.parse_args()
    if not hasattr(args, 'func'):
        parser.print_help()
        return 2
    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())