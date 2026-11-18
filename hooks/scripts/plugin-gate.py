#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
plugin-gate.py — 确定性强制 RULE-043：插件清单合规校验

在 Write/Edit 涉及插件体系文件（rules/ commands/ agents/ plugins/ presets/
skills/、cordis.yaml）时执行 plugin-validator 全量校验：
  - 清单必填字段（name/version/type）
  - 注册表与磁盘一致性
  - depends_on / composes / owns 引用完整性
任一失败即阻断（退出码 2），迫使先修复清单再继续。

用法（由 hooks.json 调用，无需手动运行）：
    python hooks/scripts/plugin-gate.py

退出码：
    0 = 放行（无插件相关改动，或校验通过）
    2 = 阻断（清单校验失败）
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

SCRIPTS_DIR = Path(__file__).parent
VALIDATOR = SCRIPTS_DIR / "plugin-validator.py"

WATCHED_PARTS = {"rules", "commands", "agents", "plugins", "presets", "skills"}
WATCHED_FILES = {"cordis.yaml"}


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


def is_plugin_related(path: str) -> bool:
    """是否属于插件体系文件"""
    p = Path(path)
    if p.name in WATCHED_FILES:
        return True
    return bool(WATCHED_PARTS & set(p.parts))


def main() -> int:
    files = [f for f in changed_files() if is_plugin_related(f)]
    if not files:
        sys.exit(0)

    cmd = [sys.executable, str(VALIDATOR), "--check-all"]
    try:
        # v4.10.1：显式 utf-8 解码 —— text=True 默认用 locale（GBK）读取子进程的
        # UTF-8 中文输出（✓/✗）会 UnicodeDecodeError，校验输出丢失
        result = subprocess.run(cmd, capture_output=True, text=True,
                                encoding="utf-8", errors="replace", timeout=60)
    except FileNotFoundError:
        # 无 Python 环境，放行交由 CI 兜底
        sys.exit(0)

    if result.returncode != 0:
        sys.stderr.write("\n[Hook] 插件清单校验失败，写入被阻断。RULE-043\n")
        sys.stderr.write("[Hook] 请先修复 frontmatter 必填字段或 plugins/registry.yaml 后重试。\n")
        out = result.stdout or ""
        sys.stderr.write(out[-2000:])
        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    sys.exit(main())
