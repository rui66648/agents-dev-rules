"""
部署状态检查脚本
检查所有项目的 AGENTS.md 部署状态
"""
import os
import re
import sys

# Windows GBK 控制台兼容：强制 UTF-8 输出，避免打印 ⚠/✗/✓/中文时 UnicodeEncodeError
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# 仓库根目录 = 本脚本所在目录的上一级；扫描范围 = 其父目录（通常是多仓工作区容器根）
RULES_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECTS_ROOT = os.path.dirname(RULES_ROOT)

def get_version(filepath):
    """获取文件版本号"""
    if not os.path.exists(filepath):
        return None
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    match = re.search(r"v\d+\.\d+\.\d+", content)
    return match.group(0) if match else None

def check_deployment():
    """检查部署状态"""
    print("=" * 60)
    print("部署状态检查报告")
    print("=" * 60)

    # 1. 规则库状态
    print(f"\n1. 规则库状态:")
    rules_agents = os.path.join(RULES_ROOT, "AGENTS.md")
    if os.path.exists(rules_agents):
        version = get_version(rules_agents)
        print(f"   位置: {RULES_ROOT}")
        print(f"   版本: {version}")
        print(f"   状态: OK")
    else:
        print(f"   状态: MISSING")

    # 2. 项目部署状态
    print(f"\n2. 项目部署状态:")
    ok_count = 0
    warn_count = 0
    info_count = 0

    for item in sorted(os.listdir(PROJECTS_ROOT)):
        agents_path = os.path.join(PROJECTS_ROOT, item, "AGENTS.md")
        tech_path = os.path.join(PROJECTS_ROOT, item, "tech-stack.md")

        if not os.path.exists(agents_path):
            print(f"   [SKIP] {item}: 无 AGENTS.md")
            continue

        is_link = os.path.islink(agents_path)
        version = get_version(agents_path)
        has_shared = "<<RULES_ROOT>>" in open(agents_path, "r", encoding="utf-8").read()
        tech_ok = os.path.exists(tech_path)

        if is_link:
            status = "OK (符号链接)"
            ok_count += 1
        elif has_shared and version:
            status = f"OK (占位符, v{version})"
            ok_count += 1
        elif has_shared:
            status = "WARN (占位符但无版本)"
            warn_count += 1
        else:
            status = "INFO (无共享规则引用)"
            info_count += 1

        print(f"   [{status.split()[0]}] {item}: {status.split()[1]}")

    # 3. AI 工具兼容性
    print(f"\n3. AI 工具兼容性:")
    tools = [
        ("Trae SOLO", ".trae"),
        ("Claude Code", ".claude"),
        ("Cursor", ".cursorrules"),
        ("GitHub Copilot", ".github/copilot-instructions.md"),
    ]
    for tool_name, config_path in tools:
        # 检查规则库
        root_config = os.path.join(RULES_ROOT, config_path.lstrip("."))
        if os.path.exists(root_config):
            print(f"   [OK] {tool_name}: 规则库中有配置")
        else:
            # 检查项目
            found = False
            for item in os.listdir(PROJECTS_ROOT):
                proj_config = os.path.join(PROJECTS_ROOT, item, config_path.lstrip("."))
                if os.path.exists(proj_config):
                    found = True
                    break
            if found:
                print(f"   [OK] {tool_name}: 项目中有配置")
            else:
                print(f"   [INFO] {tool_name}: 未配置（需手动设置）")

    # 4. 建议
    print(f"\n4. 建议:")
    print(f"   - 当前使用占位符方式，跨机器无需修改")
    print(f"   - 可通过设置环境变量 RULES_ROOT 指定规则库位置")
    print(f"   - 或使用符号链接实现自动同步")
    print(f"   - 运行以下命令设置环境变量:")
    print(f"     Windows: [Environment]::SetEnvironmentVariable('RULES_ROOT', '{RULES_ROOT}', 'User')")
    print(f"     macOS/Linux: export RULES_ROOT='{RULES_ROOT}'")

    print(f"\n" + "=" * 60)
    print(f"检查完成: OK={ok_count}, WARN={warn_count}, INFO={info_count}")
    print("=" * 60)

if __name__ == "__main__":
    check_deployment()
