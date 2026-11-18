#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
model-gateway-gate.py — 确定性强制 RULE-041：模型网关强制接入

在 Write/Edit 涉及代码文件（.py/.js/.ts/.tsx/.jsx）时，仅对本次改动文件做
直连模型 API 特征扫描（复用 model_gateway_lint 的黑名单规则），发现即阻断，
迫使统一走 LiteLLM/OpenRouter 网关。

用法（由 hooks.json 调用，无需手动运行）：
    python hooks/scripts/model-gateway-gate.py

退出码：
    0 = 放行（非代码文件，或无直连特征）
    2 = 阻断（存在直连模型 SDK / endpoint）
"""

import json
import sys
from pathlib import Path

# Windows GBK 控制台兼容：强制 UTF-8 输出，避免打印 ⚠/✗/✓/中文时 UnicodeEncodeError
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

HOOKS_DIR = Path(__file__).parent
SCRIPTS_DIR = HOOKS_DIR / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from model_gateway_lint import scan_file  # noqa: E402

CODE_SUFFIXES = {".py", ".js", ".ts", ".tsx", ".jsx"}


def changed_files() -> list:
    """从 argv 或 stdin 的 hook JSON（tool_input.file_path/path）读取改动文件"""
    if len(sys.argv) > 1:
        return sys.argv[1:]
    try:
        raw = sys.stdin.read()
        if raw:
            data = json.loads(raw)
            if isinstance(data, dict):
                tool_input = data.get("tool_input", {})
                fp = tool_input.get("file_path") or tool_input.get("path")
                if fp:
                    return [fp]
    except Exception:
        pass
    return []


def main() -> int:
    findings_all = []
    for f in changed_files():
        p = Path(f)
        if p.suffix not in CODE_SUFFIXES or not p.is_file():
            continue
        findings_all.extend(scan_file(p))

    if not findings_all:
        sys.exit(0)

    sys.stderr.write("\n[Hook] 检测到直连模型 API，写入被阻断。RULE-041\n")
    sys.stderr.write("[Hook] 请改用统一网关（LiteLLM/OpenRouter），详见 rules/adlc-lifecycle.md。\n")
    for f in findings_all[:10]:
        sys.stderr.write(f"  - {f['file']}:{f['line']} [{f['category']}] {f['message']}\n")
    if len(findings_all) > 10:
        sys.stderr.write(f"  ... 其余 {len(findings_all) - 10} 处省略\n")
    sys.exit(2)


if __name__ == "__main__":
    sys.exit(main())
