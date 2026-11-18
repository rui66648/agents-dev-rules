#!/usr/bin/env python3
"""组件库清理脚本 v4 - 精确保留 153 个核心组件"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Set, Tuple

# Windows GBK 控制台兼容：强制 UTF-8 输出，避免打印 ⚠/✗/✓/中文时 UnicodeEncodeError
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "components" / "manifest.json"
BACKUP_PATH = ROOT / "components" / "manifest.json.bak"


def flatten_categories(categories: List[Dict]) -> List[Dict]:
    """展平 categories 结构"""
    all_components = []
    for category in categories:
        for comp in category.get("components", []):
            comp["_category"] = category.get("name", "unknown")
            all_components.append(comp)
    return all_components


def load_manifest() -> Dict:
    """加载 manifest.json"""
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_backup(manifest: Dict) -> None:
    """创建备份"""
    with open(BACKUP_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(f"✓ 备份已创建: {BACKUP_PATH}")


def analyze_and_filter(manifest: Dict, target_count: int = 153) -> Tuple[Dict, List[Dict]]:
    """分析并过滤组件，精确保留目标数量"""
    
    categories = manifest.get("categories", [])
    all_components = flatten_categories(categories)
    original_count = len(all_components)
    
    # 评分系统：根据多个维度计算组件价值
    def score_component(comp: Dict) -> int:
        score = 0
        name = comp.get("name", "").lower()
        usage = comp.get("usage", "")
        views = comp.get("views", "0")
        
        # 解析 views
        try:
            view_count = int(views.replace("K", "000").replace("M", "000000"))
        except:
            view_count = 0
        
        # 1. 使用场景权重 (0-40分)
        b2b_keywords = ["B 端", "后台", "表单", "表格", "数据", "列表", "详情", "设置", "配置", "管理", "系统"]
        c2c_keywords = ["C 端", "营销", "landing", "展示", "动画", "特效"]
        
        for kw in b2b_keywords:
            if kw in usage:
                score += 10  # B2B 核心场景最高权重
        for kw in c2c_keywords:
            if kw in usage:
                score += 5   # C2C 场景中等权重
        
        # 2. 浏览量权重 (0-30分)
        if view_count > 100000:
            score += 30
        elif view_count > 50000:
            score += 25
        elif view_count > 20000:
            score += 20
        elif view_count > 10000:
            score += 15
        elif view_count > 5000:
            score += 10
        elif view_count > 1000:
            score += 5
        
        # 3. 组件类型权重 (0-20分)
        essential_types = ["button", "input", "form", "table", "card", "modal", "dialog", 
                          "drawer", "tooltip", "badge", "avatar", "skeleton", "spinner",
                          "progress", "switch", "checkbox", "radio", "select", "navigation",
                          "tab", "menu", "sidebar", "breadcrumb", "pagination", "alert", "toast",
                          "empty", "error", "loading", "state"]
        for t in essential_types:
            if t in name:
                score += 10
                break
        
        # 4. 性能风险惩罚 (0到-50分)
        risky_keywords = ["3d", "particle", "liquid", "glitch", "matrix", "hacker"]
        for kw in risky_keywords:
            if kw in name:
                score -= 50  # 高风险，大幅降权
        
        # 5. 复杂效果惩罚 (0到-30分)
        complex_keywords = ["glassmorphism", "neumorphism", "cyberpunk", "retro", "vaporwave"]
        for kw in complex_keywords:
            if kw in name:
                score -= 30  # 复杂风格降权
        
        return score
    
    # 计算所有组件的分数
    scored_components = []
    for comp in all_components:
        score = score_component(comp)
        scored_components.append((score, comp))
    
    # 按分数排序
    scored_components.sort(key=lambda x: -x[0])
    
    # 精确选取目标数量的组件
    kept_components = [comp for score, comp in scored_components[:target_count]]
    removed_components = [comp for score, comp in scored_components[target_count:]]
    
    # 为删除的组件添加删除原因
    for comp in removed_components:
        name = comp.get("name", "").lower()
        reasons = []
        
        # 判断删除原因
        if any(k in name for k in ["3d", "particle", "liquid", "glitch"]):
            reasons.append("性能风险")
        elif any(k in name for k in ["glassmorphism", "neumorphism", "cyberpunk"]):
            reasons.append("复杂效果")
        elif comp.get("views", "0") == "0":
            reasons.append("无浏览数据")
        else:
            reasons.append("评分较低")
        
        comp["_remove_reason"] = "、".join(reasons) if reasons else "未进入前 153 名"
    
    # 重新组织 categories 结构
    kept_by_category = {}
    for comp in kept_components:
        cat = comp.get("_category", "other")
        if cat not in kept_by_category:
            kept_by_category[cat] = []
        kept_by_category[cat].append(comp)
    
    # 重建 categories
    new_categories = []
    for cat_name, comps in kept_by_category.items():
        new_categories.append({
            "name": cat_name,
            "label": cat_name.replace("-", " ").title(),
            "components": comps
        })
    
    # 更新 manifest
    manifest["categories"] = new_categories
    manifest["version"] = "2.2.0"
    manifest["updated"] = datetime.now().strftime("%Y-%m-%d")
    manifest["description"] = f"精简版组件库元数据（机器可读），保留 {target_count} 个核心组件。RULE-035 强制引用。"
    
    # 添加清理记录
    manifest["cleanup_history"] = {
        "timestamp": datetime.now().isoformat(),
        "original_count": original_count,
        "kept_count": len(kept_components),
        "removed_count": len(removed_components),
        "strategy": f"基于多维度评分的精确筛选，保留 Top {target_count} 组件"
    }
    
    return manifest, removed_components


def main():
    """主函数"""
    
    print("=" * 60)
    print("组件库清理脚本 - 方案 A (v4 - 精确 153 个)")
    print("=" * 60)
    
    # 加载 manifest
    print("\n[1/4] 加载 manifest.json...")
    manifest = load_manifest()
    original_count = len(flatten_categories(manifest.get("categories", [])))
    print(f"  当前组件数: {original_count}")
    
    if original_count == 0:
        print("\n❌ 错误: manifest.json 中没有组件数据")
        return 1
    
    # 创建备份
    print("\n[2/4] 创建备份...")
    save_backup(manifest)
    
    # 过滤组件
    print("\n[3/4] 执行清理（保留 153 个核心组件）...")
    manifest, removed_components = analyze_and_filter(manifest, target_count=153)
    kept_count = len(flatten_categories(manifest.get("categories", [])))
    removed_count = len(removed_components)
    
    print(f"  ✓ 保留组件数: {kept_count}")
    print(f"  ✓ 删除组件数: {removed_count}")
    print(f"  ✓ 删除比例: {removed_count / original_count * 100:.1f}%")
    
    # 保存清理后的 manifest
    print("\n[4/4] 保存清理后的 manifest...")
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(f"  ✓ 已保存到: {MANIFEST_PATH}")
    
    # 输出统计
    print("\n" + "=" * 60)
    print("清理完成！")
    print("=" * 60)
    print(f"\n组件数变化: {original_count} → {kept_count} ({removed_count} 个已删除)")
    
    # 按类别统计
    by_category = {}
    for comp in removed_components:
        cat = comp.get("_category", "unknown")
        if cat not in by_category:
            by_category[cat] = 0
        by_category[cat] += 1
    
    print(f"\n按类别统计:")
    for cat, count in sorted(by_category.items(), key=lambda x: -x[1])[:10]:
        print(f"  {cat}: 删除 {count} 个")
    
    print(f"\n下一步:")
    print(f"  1. 运行 component-validator.py 验证清理结果")
    print(f"  2. 检查 git diff 确认变更")
    print(f"  3. 提交变更: git add components/manifest.json")
    
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"\n❌ 错误: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
