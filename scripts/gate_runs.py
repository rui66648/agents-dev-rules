#!/usr/bin/env python3
"""
门禁运行记录（append-only）与查询入口
=====================================

记录字段（唯一 schema 定义；Node/PowerShell 侧按此字段写入）：
  gate_id    门禁标识（与 hooks/configs/gate-inventory.yaml 对齐）
  mode       dry-run | apply
  trigger    scheduled | manual | hook
   result     PASS | FAIL | ERROR | NOT_VERIFIED（放行但未真正执行，如 linter 工具缺失跳过）
  rule_ids   该门禁覆盖的 RULE 编号（可为空数组）
  evidence   证据：至少含文件路径，以及行号或计数
  started_at / finished_at   ISO-8601 UTC（YYYY-MM-DDTHH:MM:SSZ）
  exit_code  进程退出码
  host       主机名

落点：logs/gate-runs/<YYYYMM>.jsonl（按月分片，追加写，不改写历史行）。
logs/ 已在 .gitignore 中（运行遥测按主机本地保留，不进版本库）。

查询：
  python scripts/gate_runs.py --last [n]          # 每个门禁最近 n 条（默认 1）
  python scripts/gate_runs.py --unverified --since 14   # 最近 N 天无 PASS 的门禁

写失败纪律：调用方必须把 write_record() 返回的 False 当作 FAIL 处理（退出码非 0），
并把 stderr 上的 [gate-runs] 报错原样暴露——记录写失败不得静默通过。
"""

from __future__ import annotations

import argparse
import json
import os
import socket
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Windows GBK 控制台兼容：强制 UTF-8 输出
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

SCRIPT_DIR = Path(__file__).resolve().parent
RULES_ROOT = SCRIPT_DIR.parent
DEFAULT_LOG_DIR = RULES_ROOT / "logs" / "gate-runs"
INVENTORY = RULES_ROOT / "hooks" / "configs" / "gate-inventory.yaml"

MODES = {"dry-run", "apply"}
TRIGGERS = {"scheduled", "manual", "hook"}
# NOT_VERIFIED（v4.16.1 新增）：门禁**放行但未真正执行**——如 linter 工具缺失时
# agent-linter 跳过 ruff/mypy/bandit。它与 PASS 的区别必须落进记录：
# 把"未验证"记成 PASS，记录本身就是假的（--unverified 也就失去了意义）。
RESULTS = {"PASS", "FAIL", "ERROR", "NOT_VERIFIED"}


def utc_now() -> str:
    """当前 UTC 时间，精确到秒（与 Node/PowerShell 写入格式一致）。"""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write_record(
    *,
    gate_id: str,
    mode: str,
    trigger: str = "manual",
    result: str,
    rule_ids: list[str] | None = None,
    evidence: dict | None = None,
    started_at: str | None = None,
    exit_code: int = 0,
    log_dir: Path | None = None,
) -> bool:
    """追加一条门禁运行记录。

    Returns:
        True 写入成功；False 写入失败（已向 stderr 说明，调用方必须按 FAIL 处理）。
    """
    now = utc_now()
    if mode not in MODES:
        _stderr(f"非法 mode={mode!r}（允许 {sorted(MODES)}）")
        return False
    if trigger not in TRIGGERS:
        _stderr(f"非法 trigger={trigger!r}（允许 {sorted(TRIGGERS)}）")
        return False
    if result not in RESULTS:
        _stderr(f"非法 result={result!r}（允许 {sorted(RESULTS)}）")
        return False

    record = {
        "gate_id": gate_id,
        "mode": mode,
        "trigger": trigger,
        "result": result,
        "rule_ids": list(rule_ids or []),
        "evidence": evidence or {},
        "started_at": started_at or now,
        "finished_at": now,
        "exit_code": int(exit_code),
        "host": socket.gethostname(),
    }
    try:
        target_dir = Path(log_dir) if log_dir else DEFAULT_LOG_DIR
        target_dir.mkdir(parents=True, exist_ok=True)
        path = target_dir / f"{now[:7].replace('-', '')}.jsonl"
        with open(path, "a", encoding="utf-8", newline="") as fh:
            fh.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
        return True
    except Exception as exc:  # 含序列化失败：记录写失败一律降级 FAIL，不得静默
        _stderr(f"记录写入失败：{exc} → 本次运行按 FAIL 处理")
        return False


def _stderr(msg: str) -> None:
    print(f"[gate-runs] {msg}", file=sys.stderr)


def read_records(log_dir: Path | None = None) -> list[dict]:
    """读取全部分片；坏行只告警跳过，不影响其它记录。"""
    directory = Path(log_dir) if log_dir else DEFAULT_LOG_DIR
    if not directory.exists():
        return []
    out: list[dict] = []
    for path in sorted(directory.glob("*.jsonl")):
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            _stderr(f"读取 {path} 失败：{exc}")
            continue
        for lineno, line in enumerate(lines, 1):
            if not line.strip():
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                _stderr(f"{path.name}:{lineno} 不是合法 JSON，已跳过（不影响其它记录）")
    out.sort(key=lambda r: str(r.get("finished_at") or ""))
    return out


def load_inventory() -> list[dict]:
    """门禁清单：--unverified 的基线（否则「从未跑过」的门禁永远无法被发现）。"""
    if not INVENTORY.exists():
        _stderr(f"门禁清单不存在：{INVENTORY}")
        return []
    try:
        import yaml
    except ImportError:
        _stderr("缺少 PyYAML，无法读取 gate-inventory.yaml")
        return []
    try:
        data = yaml.safe_load(INVENTORY.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        _stderr(f"gate-inventory.yaml 解析失败：{exc}")
        return []
    return list(data.get("gates") or [])


def _fmt_evidence(evidence) -> str:
    if not isinstance(evidence, dict):
        return str(evidence)
    parts = []
    for key, value in evidence.items():
        if isinstance(value, (list, tuple)):
            body = f"[{len(value)}]" + (f" {value[0]}" if value else "")
        elif isinstance(value, dict):
            body = json.dumps(value, ensure_ascii=False)
        else:
            body = str(value)
        parts.append(f"{key}={body}")
    return "; ".join(parts)[:200]


def cmd_last(records: list[dict], n: int) -> int:
    latest: list[dict] = []
    seen: set[str] = set()
    counts: dict[str, int] = {}
    for rec in reversed(records):
        gate = str(rec.get("gate_id") or "?")
        if counts.get(gate, 0) >= n:
            continue
        counts[gate] = counts.get(gate, 0) + 1
        latest.append(rec)
        seen.add(gate)
    if not latest:
        print("（无记录：gate-runs 目录为空，或门禁尚未接入记录）")
        return 0
    latest.sort(key=lambda r: str(r.get("finished_at") or ""), reverse=True)
    print(f"=== 最近门禁运行（每个门禁 {n} 条，共 {len(seen)} 个门禁） ===")
    for rec in latest:
        verdict = str(rec.get("result") or "?")
        # NOT_VERIFIED 必须在行内点名（v4.16.1）：把它显示成普通一行，读者会当成已验证。
        flag = "  ← 放行但未验证（质量未通过验证）" if verdict == "NOT_VERIFIED" else ""
        print(
            f"{rec.get('finished_at','?'):20}  {str(rec.get('gate_id')):20} "
            f"{str(rec.get('mode')):8} {verdict:13} "
            f"exit={rec.get('exit_code')}  trigger={rec.get('trigger')}  "
            f"rule_ids={','.join(rec.get('rule_ids') or []) or '—'}{flag}"
        )
        print(f"    evidence: {_fmt_evidence(rec.get('evidence'))}")
    return 0


def _parse_ts(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def cmd_unverified(records: list[dict], days: int) -> int:
    gates = load_inventory()
    if not gates:
        return 2
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    unverified: list[tuple[dict, dict | None, str]] = []
    for gate in gates:
        gate_id = str(gate.get("gate_id") or "")
        last_pass = None
        last_any = None
        for rec in records:
            if str(rec.get("gate_id")) != gate_id:
                continue
            last_any = rec
            ts = _parse_ts(str(rec.get("finished_at") or ""))
            if str(rec.get("result")) == "PASS" and ts and ts >= cutoff:
                last_pass = rec
        if last_pass is None:
            reason = "从未成功运行"
            if last_any is not None:
                reason = f"最近一次为 {last_any.get('result')}（{last_any.get('finished_at')}），{days} 天内无 PASS"
            unverified.append((gate, last_any, reason))

    print(f"=== 最近 {days} 天无 PASS 的门禁（基线：gate-inventory.yaml，共 {len(gates)} 个） ===")
    if not unverified:
        print(f"全部 {len(gates)} 个门禁在最近 {days} 天内有 PASS 记录。")
        return 0
    for gate, last_any, reason in unverified:
        integ = str(gate.get("integration") or "integrated")
        flag = "已接入" if integ == "integrated" else f"未接入：{gate.get('reason','—')}"
        print(f"  - {gate.get('gate_id'):22} {reason}  [{flag}]")
        print(f"      期望命令: {gate.get('command', '—')}")
        if last_any is not None:
            print(f"      最近记录: {last_any.get('finished_at')} {last_any.get('result')} ({last_any.get('mode')})")
    print(f"\n[FAIL] {len(unverified)}/{len(gates)} 个门禁在最近 {days} 天无 PASS 记录")
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="门禁运行记录查询（append-only JSONL）")
    parser.add_argument("--last", nargs="?", const=1, type=int, default=None,
                        help="每个门禁最近 n 条记录（默认 1）")
    parser.add_argument("--unverified", action="store_true",
                        help="列出最近 N 天没有 PASS 记录的门禁")
    parser.add_argument("--since", type=int, default=14, help="配合 --unverified 的天数窗口")
    parser.add_argument("--log-dir", type=Path, default=None, help="覆盖日志目录（调试用）")
    args = parser.parse_args(argv)

    if args.unverified:
        return cmd_unverified(read_records(args.log_dir), args.since)
    if args.last is not None:
        return cmd_last(read_records(args.log_dir), max(1, args.last))
    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
