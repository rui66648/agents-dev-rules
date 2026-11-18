"""
RULES_ROOT 解析器
当 AI 加载 AGENTS.md 时，自动将 <<RULES_ROOT>> 替换为实际路径
"""
import os
import re
import sys

# Windows GBK 控制台兼容：强制 UTF-8 输出，避免打印 ⚠/✗/✓/中文时 UnicodeEncodeError
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# 默认规则库位置：本脚本所在仓库根（不依赖任何绝对路径，可随仓迁移）
DEFAULT_RULES_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 环境变量优先级最高
ENV_VAR = "RULES_ROOT"

def resolve_rules_root():
    """解析 RULES_ROOT 路径"""
    # 1. 检查环境变量
    env_path = os.environ.get(ENV_VAR)
    if env_path and os.path.exists(env_path):
        return env_path

    # 2. 检查父目录（规则库常与项目仓同级存放）
    parent = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for name in ("agents-dev-rules", "开发流程规则"):
        candidate = os.path.join(parent, name)
        if os.path.exists(candidate):
            return candidate

    # 3. 使用默认路径（仓库自身根）
    return DEFAULT_RULES_ROOT

def substitute_placeholders(content, rules_root=None):
    """将 <<RULES_ROOT>> 替换为实际路径"""
    if rules_root is None:
        rules_root = resolve_rules_root()
    return content.replace("<<RULES_ROOT>>", rules_root)

def load_agents_md(filepath, rules_root=None):
    """加载并解析 AGENTS.md"""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    return substitute_placeholders(content, rules_root)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
        if os.path.exists(filepath):
            content = load_agents_md(filepath)
            print(content)
        else:
            print(f"Error: File not found: {filepath}", file=sys.stderr)
            sys.exit(1)
    else:
        print(f"RULES_ROOT: {resolve_rules_root()}")
        print(f"Usage: python resolve-rules-root.py <AGENTS.md>")
