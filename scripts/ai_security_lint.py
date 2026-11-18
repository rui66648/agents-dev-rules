#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ai_security_lint.py — AI 安全扫描器（RULE-008 / RULE-016）

真正执行的扫描（非演示数据）：
  - 硬编码密钥/凭据赋值（password/secret/token/api_key = "字面量"）
  - 私钥块（-----BEGIN ... PRIVATE KEY-----）
  - 已知密钥格式（OpenAI sk-、GitHub ghp_、AWS AKIA、Slack xox*）
  - 不可信执行/反序列化（eval/exec/pickle.loads/yaml.load 无 Loader）
  - Prompt 注入标记（ignore previous instructions 等）

用法：
    python scripts/ai_security_lint.py                     # 扫描默认范围（源码+配置）
    python scripts/ai_security_lint.py --path <dir|file>   # 扫描指定路径
    python scripts/ai_security_lint.py --include-docs      # 连同 docs/ 一起扫（默认排除，避免示例误报）
    python scripts/ai_security_lint.py --format json       # JSON 输出
    python scripts/ai_security_lint.py --ci                # CI 模式（FAIL 时退出码 1，默认相同）

退出码：
    0 = PASS（无 CRITICAL/HIGH 违规）
    1 = FAIL（存在 CRITICAL/HIGH 违规，阻断提交/合并）
    2 = 脚本执行错误
"""

import argparse
import datetime
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

# Windows GBK 控制台兼容：强制 UTF-8 输出，避免打印 ⚠/✗/✓/中文时 UnicodeEncodeError
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

SCAN_VERSION = "2.0.0"

# 扫描的文件后缀（源码 + 配置 + 环境文件）
SCAN_SUFFIXES = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".kt", ".java",
    ".yaml", ".yml", ".json", ".toml", ".ini", ".cfg", ".env", ".sh", ".bat", ".ps1",
}

# 默认排除的目录（依赖/构建产物/归档/历史文档示例，避免误报与超时）
# 注：hooks/ 为共享强制工具目录（经 Junction 部署，从不承载项目源码），
#     其源码含 lint 规则定义文本（如"检测到 eval() 使用"），扫描会自匹配误报，故排除。
EXCLUDED_DIRS = {
    "node_modules", "__pycache__", ".git", ".next", ".pytest_cache",
    ".venv", "venv", "dist", "build", "coverage",
    "archive", "docs", "html-reports", "reports", "screenshots",
    "audit-logs", "call_logs", "logs", "memory", ".trae-html-share-packages",
    "_dsh-release", ".uploads", "artifacts", "components", "hooks",
}

# ── 安全规则（severity 决定是否阻断）──────────────────────
SECURITY_RULES = [
    {
        "id": "private_key_block",
        "pattern": r"-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----",
        "severity": "CRITICAL",
        "message": "检测到私钥块，严禁提交",
    },
    {
        "id": "known_api_key_format",
        "pattern": r"\b(sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{36}|gh[ousr]_[A-Za-z0-9]{36}|AKIA[0-9A-Z]{16}|xox[baprs]-[A-Za-z0-9-]{10,})\b",
        "severity": "CRITICAL",
        "message": "检测到疑似真实 API Key 格式（OpenAI/GitHub/AWS/Slack）",
    },
    {
        "id": "hardcoded_secret",
        "pattern": r"(?i)\b(password|passwd|secret|token|api_key|apikey|access_key|private_key)\s*[:=]\s*[\"'][^\"']{8,}[\"']",
        "severity": "HIGH",
        "message": "检测到硬编码密钥/凭据赋值（应使用环境变量或密钥管理服务）",
    },
    {
        "id": "unsafe_eval",
        "pattern": r"\beval\s*\(|\bexec\s*\(",
        "severity": "HIGH",
        "message": "检测到 eval()/exec() 动态执行（RULE-010 禁止）",
    },
    {
        "id": "unsafe_deserialization",
        "pattern": r"pickle\.loads\s*\(|yaml\.load\s*\((?![^)]*Loader)",
        "severity": "HIGH",
        "message": "检测到不可信反序列化（pickle.loads / yaml.load 无 Loader）",
    },
    {
        "id": "prompt_injection_marker",
        "pattern": r"(?i)(ignore (all )?(previous|prior|above) instructions|disregard (your|the) (system )?prompt)",
        "severity": "MEDIUM",
        "message": "检测到 Prompt 注入标记文本",
    },
]


def git_hash() -> str:
    """从 git 获取当前 HEAD 哈希；非 git 目录或 git 不可用时返回 'not-in-git'。"""
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=10, check=False,
        )
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout.strip()
    except Exception:
        pass
    return "not-in-git"


def iter_target_files(root: Path, include_docs: bool) -> list[Path]:
    """收集待扫描文件：root 为文件则单扫；为目录则按后缀递归收集。"""
    if root.is_file():
        return [root]
    self_path = Path(__file__).resolve()  # 跳过扫描器自身（规则定义文本会自匹配）
    files: list[Path] = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if p == self_path:
            continue
        if p.name.endswith(".min.js"):  # 第三方压缩包（echarts/mermaid 等）误报源
            continue
        parts = set(p.parts)
        if parts & EXCLUDED_DIRS and not (include_docs and "docs" in parts):
            continue
        if p.suffix.lower() not in SCAN_SUFFIXES and p.name.lower() != ".env":
            continue
        files.append(p)
    return files


def scan_file(file_path: Path) -> list[dict[str, Any]]:
    """扫描单个文件的安全违规，返回违规列表（带行号）。"""
    violations: list[dict[str, Any]] = []
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return violations
    if not content:
        return violations

    for rule in SECURITY_RULES:
        hits = []
        for i, line in enumerate(content.splitlines(), 1):
            if re.search(rule["pattern"], line):
                hits.append({"line": i, "text": line.strip()[:120]})
        if hits:
            violations.append({
                "rule": rule["id"],
                "severity": rule["severity"],
                "message": rule["message"],
                "file": str(file_path),
                "hits": hits[:10],
                "hit_count": len(hits),
            })
    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description="AI 安全扫描器（RULE-008/016）v2.0.0")
    parser.add_argument("--path", default=None, help="扫描目标（默认：仓库根目录的源码+配置）")
    parser.add_argument("--include-docs", action="store_true", help="连同 docs/ 一起扫描")
    parser.add_argument("--ci", action="store_true", help="CI 模式（FAIL 时退出码 1）")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="输出格式")
    parser.add_argument("--output-report", default=None, help="输出 JSON 报告到指定文件")
    args = parser.parse_args()

    try:
        root = Path(args.path).resolve() if args.path else Path(__file__).resolve().parent.parent
        files = iter_target_files(root, args.include_docs)

        violations: list[dict[str, Any]] = []
        for f in files:
            violations.extend(scan_file(f))

        critical = sum(1 for v in violations if v["severity"] == "CRITICAL")
        high = sum(1 for v in violations if v["severity"] == "HIGH")
        medium = sum(1 for v in violations if v["severity"] == "MEDIUM")
        status = "FAIL" if (critical or high) else "PASS"

        report = {
            "scan_version": SCAN_VERSION,
            "git_hash": git_hash(),
            "scanned_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
            "scanned_root": str(root),
            "files_scanned": len(files),
            "total_violations": len(violations),
            "critical": critical,
            "high": high,
            "medium": medium,
            "low": 0,
            "violations": violations,
            "status": status,
        }

        if args.format == "json":
            print(json.dumps(report, ensure_ascii=False, indent=2))
        else:
            print(f"AI 安全扫描（RULE-008/016）v{SCAN_VERSION}")
            print(f"范围: {report['scanned_root']} | 文件: {len(files)} | git: {report['git_hash'][:12]}")
            if violations:
                print(f"\n⚠ 发现 {len(violations)} 项违规:")
                for v in violations[:30]:
                    loc = f"{v['file']}:{v['hits'][0]['line']}" if v.get("hits") else v["file"]
                    print(f"  [{v['severity']}] {v['rule']} — {v['message']}")
                    print(f"      {loc}")
                if len(violations) > 30:
                    print(f"  ... 其余 {len(violations) - 30} 项省略")
            else:
                print("\n✓ 未检测到安全违规")
            print(f"\n[{status}] CRITICAL={critical} HIGH={high} MEDIUM={medium}")

        if args.output_report:
            report_path = Path(args.output_report)
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(
                json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            if args.format != "json":
                print(f"报告已输出至：{report_path}")

        return 1 if status == "FAIL" else 0

    except Exception as e:
        print(f"错误：安全扫描脚本执行失败：{e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 2


if __name__ == "__main__":
    sys.exit(main())
