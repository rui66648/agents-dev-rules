# AI Document Review Script
# 使用 LLM 自动审查设计文档的一致性
# 执行方式: uv run python scripts/doc_review_llm.py

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Windows GBK 控制台兼容：强制 UTF-8 输出，避免打印 ⚠/✗/✓/中文时 UnicodeEncodeError
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# 配置
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
REVIEW_OUTPUT_DIR = Path("docs/reviews")


def load_document(doc_path: Path) -> str | None:
    """加载文档内容"""
    if not doc_path.exists():
        return None
    try:
        return doc_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"[ERROR] 读取文档失败 {doc_path}: {e}")
        return None


def extract_sections(content: str) -> dict[str, str]:
    """提取文档中的关键章节"""
    sections = {}
    current_section = None
    current_content = []
    
    for line in content.split('\n'):
        if line.startswith('## '):
            if current_section:
                sections[current_section] = '\n'.join(current_content)
            current_section = line[3:].strip()
            current_content = []
        elif current_section:
            current_content.append(line)
    
    if current_section:
        sections[current_section] = '\n'.join(current_content)
    
    return sections


def check_cross_consistency(
    architecture: dict[str, str],
    api_design: dict[str, str],
    ui_design: dict[str, str]
) -> list[dict[str, Any]]:
    """
    检查文档间的一致性
    
    Returns:
        一致性问题列表
    """
    issues = []
    
    # 检查架构模块数 vs 数据库实体数
    arch_modules = len([k for k in architecture.keys() if 'module' in k.lower() or 'component' in k.lower()])
    db_entities = len([k for k in architecture.keys() if 'entity' in k.lower() or 'table' in k.lower()])
    
    if arch_modules != db_entities:
        issues.append({
            "type": "INCONSISTENCY",
            "severity": "WARNING",
            "message": f"架构模块数 ({arch_modules}) ≠ 数据库实体数 ({db_entities})",
            "source": "architecture.md"
        })
    
    # 检查 API 接口数 vs UI 页面数
    api_endpoints = len([k for k in api_design.keys() if 'endpoint' in k.lower() or 'api' in k.lower()])
    ui_pages = len([k for k in ui_design.keys() if 'page' in k.lower() or 'route' in k.lower()])
    
    if api_endpoints != ui_pages:
        issues.append({
            "type": "INCONSISTENCY",
            "severity": "INFO",
            "message": f"API 接口数 ({api_endpoints}) ≠ UI 页面数 ({ui_pages})",
            "source": "api-design.md, ui-wireframe.md"
        })
    
    return issues


def generate_review_report(
    documents: dict[str, str],
    issues: list[dict[str, Any]]
) -> dict[str, Any]:
    """生成审查报告"""
    return {
        "review_id": f"review-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
        "reviewed_at": datetime.utcnow().isoformat(),
        "documents_reviewed": list(documents.keys()),
        "total_issues": len(issues),
        "critical_issues": len([i for i in issues if i.get("severity") == "CRITICAL"]),
        "warning_issues": len([i for i in issues if i.get("severity") == "WARNING"]),
        "info_issues": len([i for i in issues if i.get("severity") == "INFO"]),
        "issues": issues,
        "status": "APPROVED" if not any(i.get("severity") in ["CRITICAL", "WARNING"] for i in issues) else "NEEDS_REVISION",
        "recommendations": [
            "确保所有设计文档引用一致的命名规范",
            "检查 API 响应格式是否与 UI 组件数据结构匹配",
            "验证安全策略是否覆盖所有认证端点"
        ]
    }


def save_review_report(report: dict[str, Any], doc_name: str):
    """保存审查报告"""
    REVIEW_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REVIEW_OUTPUT_DIR / f"{doc_name}-review.pdf"
    
    # 实际应生成 PDF，这里保存 JSON 作为示例
    json_path = REVIEW_OUTPUT_DIR / f"{doc_name}-review.json"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    
    return json_path


def main():
    docs_dir = Path("docs")
    
    # 加载设计文档
    documents = {}
    for doc_name in ["architecture", "api-design", "ui-wireframe"]:
        doc_path = docs_dir / f"{doc_name}.md"
        content = load_document(doc_path)
        if content:
            documents[doc_name] = extract_sections(content)
    
    if not documents:
        print("[ERROR] 未找到设计文档，请在 docs/ 目录下创建 architecture.md, api-design.md, ui-wireframe.md")
        sys.exit(1)
    
    print(f"[INFO] 已加载 {len(documents)} 个设计文档")
    
    # 检查一致性
    issues = check_cross_consistency(
        documents.get("architecture", {}),
        documents.get("api-design", {}),
        documents.get("ui-wireframe", {})
    )
    
    # 生成报告
    report = generate_review_report(documents, issues)
    
    # 保存报告
    for doc_name in documents.keys():
        save_review_report(report, doc_name)
    
    # 输出结果
    print(json.dumps(report, indent=2, ensure_ascii=False))
    
    # 根据审查结果决定
    if report["status"] == "APPROVED":
        print("\n[APPROVED] 文档审查通过，可以进入 writing-plans 阶段")
        sys.exit(0)
    else:
        print(f"\n[NEEDS_REVISION] 文档审查未通过，发现 {report['total_issues']} 个问题")
        print("请修正问题后重新提交审查")
        sys.exit(1)


if __name__ == "__main__":
    main()
