# Model Artifact Generator
# 用于生成和注册模型 artifact
# 执行方式: uv run python scripts/generate_model_artifact.py

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Windows GBK 控制台兼容：强制 UTF-8 输出，避免打印 ⚠/✗/✓/中文时 UnicodeEncodeError
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

def generate_model_artifact(
    git_hash: str,
    test_result: dict[str, Any],
    model_path: str = None
) -> dict[str, Any]:
    """
    生成模型 artifact 元数据
    
    Args:
        git_hash: Git commit hash
        test_result: 模型测试结果
        model_path: 模型文件路径（可选）
    
    Returns:
        模型元数据字典
    """
    artifact_id = f"model-v{git_hash[:8]}"
    created_at = datetime.utcnow().isoformat() + "Z"
    
    metadata = {
        "artifact_id": artifact_id,
        "model_version": artifact_id,
        "git_hash": git_hash,
        "created_at": created_at,
        "model_path": model_path or f"models/{artifact_id}",
        "test_result": test_result,
        "dependencies": [
            {"name": "fastapi", "version": "0.115+"},
            {"name": "pydantic", "version": "2.10+"},
            {"name": "sqlalchemy", "version": "2.0+"}
        ],
        "prompt_examples": [
            "List all skills in the knowledge graph",
            "Find the shortest path between node A and node B",
            "Extract entities from the following text: {text}"
        ],
        "tags": ["ai-model", "fastapi", "pydantic"],
        "status": "published" if test_result.get("status") == "PASS" else "failed"
    }
    
    return metadata


def save_artifact(metadata: dict[str, Any], output_dir: Path) -> Path:
    """
    保存模型 artifact 到指定目录
    
    Args:
        metadata: 模型元数据
        output_dir: 输出目录
    
    Returns:
        保存的文件路径
    """
    artifact_dir = output_dir / metadata["artifact_id"]
    artifact_dir.mkdir(parents=True, exist_ok=True)
    
    # 保存元数据文件
    metadata_path = artifact_dir / "metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2))
    
    # 保存测试报告
    test_report_path = artifact_dir / "test-report.json"
    test_report_path.write_text(json.dumps(metadata["test_result"], indent=2))
    
    return metadata_path


def main():
    # 模拟输入（实际应从环境变量获取）
    git_hash = "abc1234def5678"
    model_path = "models/skill-tree-agent-v1"
    test_result = {
        "total": 5,
        "passed": 5,
        "failed": 0,
        "hallucination_ratio": 0.02,
        "status": "PASS"
    }
    
    # 生成 artifact
    metadata = generate_model_artifact(git_hash, test_result, model_path)
    
    # 保存 artifact
    output_dir = Path("artifacts")
    artifact_path = save_artifact(metadata, output_dir)
    
    # 输出结果
    print(json.dumps(metadata, indent=2))
    print(f"\n[INFO] 模型 artifact 已保存到: {artifact_path}")
    
    if metadata["status"] == "failed":
        print("[WARN] 模型测试未通过，artifact 状态为 failed")
        sys.exit(1)
    else:
        print("[OK] 模型 artifact 生成成功")
        sys.exit(0)


if __name__ == "__main__":
    main()
