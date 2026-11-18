# 爆炸半径评估脚本
# 用于 writing-plans 阶段自动评估改动影响范围
# 执行方式: uv run python scripts/estimate_change.py

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

# Windows GBK 控制台兼容：强制 UTF-8 输出，避免打印 ⚠/✗/✓/中文时 UnicodeEncodeError
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# 爆炸半径分类阈值
CLASSIFICATION_THRESHOLDS = {
    "micro": {"max_files": 2, "max_time_min": 15},
    "small": {"max_files": 5, "max_time_min": 45},
    "medium": {"max_files": 10, "max_time_min": 120},
    "large": {"max_files": float('inf'), "max_time_min": float('inf')}
}


def get_changed_files(base: str = "HEAD~1", head: str = "HEAD") -> list[str]:
    """获取变更文件列表"""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", base, head],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip().split("\n") if result.stdout.strip() else []
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] 获取变更文件失败: {e}")
        return []


def estimate_time(files: list[str]) -> int:
    """
    估算变更所需时间（分钟）
    
    经验法则：
    - 简单改动：10 分钟/文件
    - 复杂改动：30 分钟/文件
    - 重构/新增：60 分钟/文件
    """
    if not files:
        return 0
    
    # 根据文件类型估算
    total_time = 0
    for file_path in files:
        if file_path.endswith(('.py', '.ts', '.tsx')):
            # 代码文件
            if "test" in file_path.lower():
                total_time += 10  # 测试文件
            elif "schema" in file_path.lower() or "model" in file_path.lower():
                total_time += 30  # 数据模型
            else:
                total_time += 20  # 普通代码
        elif file_path.endswith(('.yml', '.yaml')):
            total_time += 15  # 配置文件
        elif file_path.endswith(('.md', '.txt')):
            total_time += 5   # 文档
        else:
            total_time += 10
    
    # 根据文件数量调整
    if len(files) > 10:
        total_time *= 1.5  # 大量文件增加复杂度
    
    return total_time


def classify_blast_radius(files: list[str], estimated_time: int) -> dict[str, Any]:
    """
    分类爆炸半径
    
    Returns:
        爆炸半径分类结果
    """
    file_count = len(files)
    
    # 判断分类
    if file_count <= CLASSIFICATION_THRESHOLDS["micro"]["max_files"] and \
       estimated_time <= CLASSIFICATION_THRESHOLDS["micro"]["max_time_min"]:
        classification = "micro"
        strategy = "单任务直接执行"
    elif file_count <= CLASSIFICATION_THRESHOLDS["small"]["max_files"] and \
         estimated_time <= CLASSIFICATION_THRESHOLDS["small"]["max_time_min"]:
        classification = "small"
        strategy = "拆分为 2-3 个子任务，逐个验证"
    elif file_count <= CLASSIFICATION_THRESHOLDS["medium"]["max_files"] and \
         estimated_time <= CLASSIFICATION_THRESHOLDS["medium"]["max_time_min"]:
        classification = "medium"
        strategy = "必须写 SPEC 拆解，每步验证"
    else:
        classification = "large"
        strategy = "拆分为多个独立功能点，分批次执行"
    
    return {
        "file_count": file_count,
        "estimated_time_min": estimated_time,
        "classification": classification,
        "strategy": strategy,
        "requires_spec": classification in ["medium", "large"],
        "requires_split": classification in ["large"]
    }


def generate_split_tasks(files: list[str], classification: str) -> list[dict[str, Any]]:
    """
    为大型变更生成拆分任务
    
    Returns:
        拆分后的子任务列表
    """
    if classification != "large":
        return []
    
    # 按文件类型分组
    groups: dict[str, list[str]] = {}
    for file_path in files:
        if file_path.endswith('.py'):
            group = "backend"
        elif file_path.endswith(('.ts', '.tsx')):
            group = "frontend"
        elif file_path.endswith('.yml') or file_path.endswith('.yaml'):
            group = "config"
        else:
            group = "other"
        
        if group not in groups:
            groups[group] = []
        groups[group].append(file_path)
    
    # 生成子任务
    tasks = []
    for i, (group, group_files) in enumerate(groups.items(), 1):
        tasks.append({
            "task_id": f"task-{i}",
            "group": group,
            "files": group_files,
            "description": f"处理 {group} 相关文件 ({len(group_files)} 个文件)"
        })
    
    return tasks


def main():
    # 获取变更文件
    base = sys.argv[1] if len(sys.argv) > 1 else "HEAD~1"
    head = sys.argv[2] if len(sys.argv) > 2 else "HEAD"
    
    files = get_changed_files(base, head)
    
    if not files:
        print("[INFO] 没有检测到变更文件")
        sys.exit(0)
    
    print(f"[INFO] 检测到 {len(files)} 个变更文件")
    
    # 估算时间
    estimated_time = estimate_time(files)
    print(f"[INFO] 预估耗时: {estimated_time} 分钟")
    
    # 分类爆炸半径
    result = classify_blast_radius(files, estimated_time)
    
    # 生成拆分任务（如果是大型变更）
    if result["requires_split"]:
        result["split_tasks"] = generate_split_tasks(files, result["classification"])
    
    # 保存报告
    report_path = Path("docs/blast-radius-report.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(result, indent=2))
    
    # 输出结果
    print("\n" + json.dumps(result, indent=2))
    
    # 根据分类输出建议
    if result["classification"] in ["medium", "large"]:
        print(f"\n[WARNING] 爆炸半径为 '{result['classification']}'，建议:")
        print(f"  - 执行策略: {result['strategy']}")
        if result["requires_split"]:
            print(f"  - 已生成 {len(result['split_tasks'])} 个拆分任务")
        print(f"  - 必须: {'是' if result['requires_spec'] else '否'} 编写 SPEC 拆解")
    
    # 返回退出码
    sys.exit(0)


if __name__ == "__main__":
    main()
