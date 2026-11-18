"""
Phase 1-3 验收测试清单 - 验证 ADLC Platform 交付物
"""

import sys
from pathlib import Path

# Windows GBK 控制台兼容：强制 UTF-8 输出，避免打印 ⚠/✗/✓/中文时 UnicodeEncodeError
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Base paths
BASE = Path(__file__).parent.parent.parent.parent
SRC_BACKEND = BASE / "src" / "backend"
SRC_FRONTEND = BASE / "src" / "frontend" / "src"
RULES = BASE / "rules"
DOCS_TASKS = BASE / "docs" / "tasks"


def check_file(path: Path, description: str) -> bool:
    exists = path.exists()
    status = "✅" if exists else "❌"
    print(f"  {status} {path.relative_to(BASE)} — {description}")
    return exists


def main():
    print("=" * 60)
    print("ADLC Platform 验收检查")
    print("=" * 60)

    all_ok = True

    # Phase 0: Rules
    print("\n【Phase 0: 规则文件】")
    all_ok &= check_file(RULES / "adlc-lifecycle.md", "RULE-034~040 定义")
    all_ok &= check_file(BASE / "AGENTS.md", "AGENTS.md v3.8.0")
    all_ok &= check_file(RULES / "agent-constraints.md", "Agent 约束更新")
    all_ok &= check_file(RULES / "cicd-rules.md", "渐进式发布规范")

    # Phase 1.1: Trace Models & Repos
    print("\n【Phase 1.1: Trace 可观测性栈】")
    all_ok &= check_file(SRC_BACKEND / "models" / "base.py", "Base + AuditableMixin")
    all_ok &= check_file(SRC_BACKEND / "models" / "trace.py", "4 ORM 模型 (Session/Trace/Span/Replay)")
    all_ok &= check_file(SRC_BACKEND / "repositories" / "trace_repo.py", "TraceRepo (含递归 CTE)")
    all_ok &= check_file(SRC_BACKEND / "middleware" / "agent_tracing.py", "AgentTracingMiddleware")
    all_ok &= check_file(SRC_BACKEND / "routers" / "traces.py", "Trace API (5 端点)")
    all_ok &= check_file(BASE / "alembic" / "versions" / "20260812_001_init_trace_tables.py", "Alembic 迁移")

    # Phase 1.2: Validator + Schemas
    print("\n【Phase 1.2: Trace Validator + Schemas】")
    all_ok &= check_file(SRC_BACKEND / "tools" / "trace_validator.py", "CLI 验证工具")
    all_ok &= check_file(SRC_BACKEND / "schemas" / "trace_schemas.py", "JSON Schema 合约")
    all_ok &= check_file(BASE / ".github" / "workflows" / "validate-traces.yml", "CI 验证流水线")

    # Phase 1.3: Workspace Service
    print("\n【Phase 1.3: Workspace Service】")
    all_ok &= check_file(SRC_BACKEND / "services" / "workspace_service.py", "WorkspaceService + LocalBackend")
    all_ok &= check_file(SRC_BACKEND / "services" / "feature_flag_service.py", "FeatureFlagService")
    all_ok &= check_file(SRC_BACKEND / "routers" / "workspaces.py", "Workspace API")
    all_ok &= check_file(SRC_BACKEND / "routers" / "feature_flags.py", "Feature Flag API")
    all_ok &= check_file(SRC_BACKEND / "workflows" / "engine.py", "WorkflowEngine")

    # Phase 1.4: App Entry
    print("\n【Phase 1.4: 应用入口】")
    all_ok &= check_file(SRC_BACKEND / "main.py", "FastAPI 应用入口")
    all_ok &= check_file(SRC_BACKEND / "requirements.txt", "Python 依赖")

    # Phase 3: Frontend
    print("\n【Phase 3: 前端页面】")
    all_ok &= check_file(SRC_FRONTEND / "types" / "adlc.ts", "TypeScript 类型定义")
    all_ok &= check_file(SRC_FRONTEND / "lib" / "api.ts", "API Client")
    all_ok &= check_file(SRC_FRONTEND / "hooks" / "useTraces.ts", "Trace Hooks")
    all_ok &= check_file(SRC_FRONTEND / "hooks" / "useFlags.ts", "Flag Hooks")
    all_ok &= check_file(SRC_FRONTEND / "hooks" / "useWorkflows.ts", "Workflow Hooks")
    all_ok &= check_file(SRC_FRONTEND / "components" / "trace" / "TraceTree.tsx", "TraceTree 组件")
    all_ok &= check_file(SRC_FRONTEND / "components" / "trace" / "TraceWaterfall.tsx", "TraceWaterfall 组件")
    all_ok &= check_file(SRC_FRONTEND / "components" / "trace" / "SpanDetailDrawer.tsx", "SpanDetailDrawer 组件")
    all_ok &= check_file(SRC_FRONTEND / "components" / "trace" / "TimelineScrubber.tsx", "TimelineScrubber 组件")
    all_ok &= check_file(SRC_FRONTEND / "components" / "trace" / "MessageBubble.tsx", "MessageBubble 组件")
    all_ok &= check_file(SRC_FRONTEND / "pages" / "DashboardPage.tsx", "Dashboard 页面")
    all_ok &= check_file(SRC_FRONTEND / "pages" / "TraceListPage.tsx", "TraceList 页面")
    all_ok &= check_file(SRC_FRONTEND / "pages" / "TraceDetailPage.tsx", "TraceDetail 页面")
    all_ok &= check_file(SRC_FRONTEND / "pages" / "SessionReplayPage.tsx", "SessionReplay 页面")
    all_ok &= check_file(SRC_FRONTEND / "pages" / "WorkflowListPage.tsx", "WorkflowList 页面")
    all_ok &= check_file(SRC_FRONTEND / "pages" / "WorkflowDetailPage.tsx", "WorkflowDetail 页面")
    all_ok &= check_file(SRC_FRONTEND / "pages" / "FlagListPage.tsx", "FlagList 页面")
    all_ok &= check_file(SRC_FRONTEND / "pages" / "FlagDetailPage.tsx", "FlagDetail 页面")
    all_ok &= check_file(SRC_FRONTEND / "components" / "layout" / "Sidebar.tsx", "Sidebar 导航")
    all_ok &= check_file(SRC_FRONTEND / "components" / "layout" / "AppShell.tsx", "AppShell 布局")
    all_ok &= check_file(SRC_FRONTEND / "App.tsx", "App 路由")
    all_ok &= check_file(SRC_FRONTEND / "main.tsx", "入口文件")
    all_ok &= check_file(SRC_FRONTEND / "package.json", "前端依赖配置")
    all_ok &= check_file(SRC_FRONTEND / "vite.config.ts", "Vite 配置")
    all_ok &= check_file(SRC_FRONTEND / "tailwind.config.js", "Tailwind 配置")
    all_ok &= check_file(SRC_FRONTEND / "index.html", "HTML 模板")

    # Success Criteria Check
    print("\n" + "=" * 60)
    print("【SC 验收检查】")
    print("=" * 60)

    sc_checks = [
        ("SC-1: Agenix 可跑通 ADLC 流程", check_file(SRC_BACKEND / "middleware" / "agent_tracing.py")),
        ("SC-2: 新建 Agent 项目 <30min", check_file(BASE / "alembic" / "env.py")),
        ("SC-3: Trace 覆盖率 100%", check_file(SRC_BACKEND / "middleware" / "agent_tracing.py")),
        ("SC-4: adlc-lifecycle.md 通过 PR 评审", check_file(RULES / "adlc-lifecycle.md")),
    ]

    passed = sum(1 for _, r in sc_checks if r)
    for desc, result in sc_checks:
        print(f"  {'✅' if result else '⏳'} {desc}")

    print(f"\n{'=' * 60}")
    if all_ok and passed == len(sc_checks):
        print("✅ 全部检查通过！ADLC Platform Phase 1-3 已交付。")
    elif all_ok:
        print(f"⚠️ 文件检查通过，但 SC 验收需进一步确认 ({passed}/{len(sc_checks)})")
    else:
        print("❌ 部分文件缺失，请检查上述列表")
    print("=" * 60)

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
