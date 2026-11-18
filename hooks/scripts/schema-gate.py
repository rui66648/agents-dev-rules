#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
schema-gate.py — 确定性强制 RULE-032：AI 生成代码前必须通过 Schema 校验

在 Write/Edit/生成代码的工具调用前执行：
1. 若改动涉及 schemas/ 下的契约文件，先校验其语法/语义（复用 schema-validator.py）
2. 若改动涉及 src/api/ 代码，检查是否与 API Schema 契约一致
3. 任一校验失败即阻断（退出码 2），迫使先修复契约再写代码

用法（由 hooks.json 调用，无需手动运行）：
    python hooks/scripts/schema-gate.py <changed_file_1> [changed_file_2 ...]

退出码：
    0 = 放行（无 Schema 相关改动，或校验通过）
    2 = 阻断（Schema 校验失败）
"""

import json
import subprocess
import sys
from pathlib import Path

# Windows GBK 控制台兼容：强制 UTF-8 输出，避免打印 ⚠/✗/✓/中文时 UnicodeEncodeError
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


HOOKS_DIR = Path(__file__).parent          # hooks/scripts/
PROJECT_ROOT = HOOKS_DIR.parent.parent     # 仓库根目录
# schema-validator.py 位于 hooks/ 顶层（而非 scripts/）。此前路径错误拼成
# hooks/hooks/schema-validator.py，Windows 下子进程以退出码 2（无法打开脚本）
# 失败，被门禁误判为"契约校验不通过"
SCHEMA_VALIDATOR = HOOKS_DIR.parent / "schema-validator.py"


def changed_files() -> list:
    """从 stdin 或 argv 读取本次改动的文件列表"""
    if len(sys.argv) > 1:
        return sys.argv[1:]

    # 尝试从 stdin 读取（hook 上下文可能传入 JSON）
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


def is_schema_related(path: str) -> bool:
    """是否为 Schema 契约相关文件"""
    p = Path(path)
    parts = set(p.parts)
    if "schemas" in parts:
        return True
    if p.suffix in (".jsonschema", ".sql") and ("schema" in str(p).lower() or "contract" in str(p).lower()):
        return True
    return False


def is_api_code(path: str) -> bool:
    """是否为 API 代码（需与契约对齐）"""
    p = Path(path)
    return p.suffix == ".py" and "api" in str(p).lower()


def main():
    files = changed_files()
    if not files:
        sys.exit(0)

    changed = [f for f in files if is_schema_related(f) or is_api_code(f)]
    if not changed:
        # 无 Schema 相关改动，放行
        sys.exit(0)

    # 复用 schema-validator.py 做整库校验
    cmd = [
        sys.executable,
        str(SCHEMA_VALIDATOR),
        "--all",
        "--fail-on-violation",
    ]
    try:
        # v4.10.1：显式 utf-8 解码 —— text=True 默认用 locale（GBK）读取子进程的
        # UTF-8 中文输出（✓/✗）会 UnicodeDecodeError，校验输出丢失
        result = subprocess.run(cmd, capture_output=True, text=True,
                                encoding="utf-8", errors="replace", timeout=60)
    except FileNotFoundError:
        # 无 Python 环境，放行交由 CI 兜底
        sys.exit(0)

    if result.returncode != 0:
        sys.stderr.write(
            "\n[Hook] Schema 校验失败，代码生成被阻断。RULE-032\n"
        )
        sys.stderr.write("[Hook] 请先修复 schemas/ 契约文件后再生成 API 代码。\n")
        sys.stderr.write(result.stdout[-2000:] if result.stdout else "")
        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()