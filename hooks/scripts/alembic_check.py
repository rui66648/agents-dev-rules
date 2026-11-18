#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
alembic_check.py — 确定性强制 RULE-005：DB Schema 变更必须通过迁移工具

替代原 pre-commit 中的 bash -c 'alembic check' 写法（bash 在 Windows 无 WSL 时
解析到 WSL stub，无法运行）。行为：
  1. alembic 未安装 → 警告并放行（exit 0，非 Python 栈项目不阻断）
  2. alembic 已安装且检测到待生成迁移 → 阻断（exit 1）
  3. 其它执行失败（如无 alembic.ini）→ 警告并放行，避免非迁移项目被阻断

用法（由项目根 .pre-commit-config.python.yaml 调用；模板见 templates/pre-commit/python.yaml）：
    python hooks/scripts/alembic_check.py

退出码：
    0 = 放行（alembic 不可用，或无待生成迁移）
    1 = 阻断（检测到待生成的数据库迁移）
"""

import shutil
import subprocess
import sys
from pathlib import Path

# Windows GBK 控制台兼容：强制 UTF-8 输出，避免打印 ⚠/✗/✓/中文时 UnicodeEncodeError
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

NEW_OPS_MARKERS = ("new upgrade operations", "Migration needed", "there are new operations")


def main() -> int:
    if not shutil.which("alembic"):
        print("⚠ 未安装 alembic，跳过迁移检查（非 Python 栈项目可忽略）")
        return 0

    root = Path.cwd()
    try:
        out = subprocess.run(
            ["alembic", "check"],
            cwd=str(root), capture_output=True, text=True, timeout=120, check=False,
        )
    except Exception as e:
        print(f"⚠ alembic check 无法执行（{e}），放行")
        return 0

    output = (out.stdout or "") + (out.stderr or "")
    if out.returncode == 0:
        print("✓ alembic check 通过（无待生成迁移）")
        return 0

    if any(marker in output for marker in NEW_OPS_MARKERS):
        print("✗ 检测到待生成的数据库迁移（RULE-005）：请先运行 alembic revision --autogenerate 并评审")
        return 1

    print(f"⚠ alembic check 未能执行（exit {out.returncode}），放行：{output.strip()[:120]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
