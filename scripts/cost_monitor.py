# Cost Monitor Script
# 监控 Span 和计算资源成本
# 执行方式: uv run python scripts/cost_monitor.py

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
SPAN_LIMIT = int(os.getenv("SPAN_LIMIT", "5000000"))  # 每日 Span 上限
CPU_LIMIT_PERCENT = int(os.getenv("CPU_LIMIT_PERCENT", "80"))  # CPU 使用率上限
GITHUB_PROJECT_ID = os.getenv("GITHUB_PROJECT_ID", "")  # GitHub Project ID（可选）


def load_metrics() -> dict[str, Any]:
    """加载监控指标"""
    metrics_path = Path("docs/otel-metrics.json")
    if not metrics_path.exists():
        return {
            "daily_span_count": 0,
            "cpu_usage_percent": 0.0,
            "memory_usage_percent": 0.0,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    try:
        content = metrics_path.read_text()
        return json.loads(content)
    except Exception as e:
        print(f"[WARN] 读取指标文件失败: {e}")
        return {
            "daily_span_count": 0,
            "cpu_usage_percent": 0.0,
            "memory_usage_percent": 0.0,
            "timestamp": datetime.utcnow().isoformat()
        }


def analyze_costs(metrics: dict[str, Any]) -> dict[str, Any]:
    """分析成本指标"""
    daily_span_count = metrics.get("daily_span_count", 0)
    cpu_usage = metrics.get("cpu_usage_percent", 0.0)
    
    # 计算成本估算（简化版，实际需根据 Cloudflare 定价）
    # Span 费用：超过 20万/天后，$0.6 / 百万 span
    free_span_limit = 200000
    if daily_span_count > free_span_limit:
        extra_spans = daily_span_count - free_span_limit
        estimated_cost = (extra_spans / 1_000_000) * 0.6
    else:
        estimated_cost = 0.0
    
    # 月度成本估算
    monthly_cost = estimated_cost * 30
    
    # 检查阈值
    span_alert = daily_span_count >= SPAN_LIMIT
    cpu_alert = cpu_usage >= CPU_LIMIT_PERCENT
    
    return {
        "daily_span_count": daily_span_count,
        "cpu_usage_percent": cpu_usage,
        "estimated_daily_cost": round(estimated_cost, 4),
        "estimated_monthly_cost": round(monthly_cost, 2),
        "span_alert": span_alert,
        "cpu_alert": cpu_alert,
        "overall_status": "ALERT" if (span_alert or cpu_alert) else "OK",
        "analyzed_at": datetime.utcnow().isoformat()
    }


def generate_cost_report(analysis: dict[str, Any]) -> str:
    """生成成本报告"""
    report = f"""## Cost Analysis Report

**分析时间**: {analysis['analyzed_at']}

| 指标 | 当前值 | 阈值 | 状态 |
|------|--------|------|------|
| 每日 Span 消耗 | {analysis['daily_span_count']:,} | {SPAN_LIMIT:,} | {'⚠️ 超限' if analysis['span_alert'] else '✅ 正常'} |
| CPU 使用率 | {analysis['cpu_usage_percent']:.1f}% | {CPU_LIMIT_PERCENT}% | {'⚠️ 高负载' if analysis['cpu_alert'] else '✅ 正常'} |

### 成本估算
- 每日预估费用: ${analysis['estimated_daily_cost']:.4f}
- 月度预估费用: ${analysis['estimated_monthly_cost']:.2f}

### 建议措施
"""
    
    if analysis["overall_status"] == "ALERT":
        report += """1. 立即检查高消耗 Span 来源
2. 优化 Agent 会话逻辑，减少重复调用
3. 考虑使用缓存减少模型调用
4. 评估是否需要升级 Cloudflare Observability 套餐
"""
    else:
        report += """成本处于正常范围，继续保持当前使用模式。
定期监控趋势，预防潜在成本爆炸。
"""
    
    return report


def main():
    # 加载指标
    metrics = load_metrics()
    
    # 分析成本
    analysis = analyze_costs(metrics)
    
    # 生成报告
    report_content = generate_cost_report(analysis)
    
    # 保存报告
    report_path = Path("docs/cost-analysis-report.md")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report_content)
    
    # 保存 JSON 报告
    json_report_path = Path("docs/cost-analysis-report.json")
    json_report_path.write_text(json.dumps(analysis, indent=2))
    
    # 输出结果
    print(json.dumps(analysis, indent=2))
    
    # 根据状态执行操作
    if analysis["overall_status"] == "ALERT":
        print(f"\n[ALERT] 成本监控发现异常，请查看报告: {report_path}")
        print(f"  - Span: {analysis['daily_span_count']:,} (阈值: {SPAN_LIMIT:,})")
        print(f"  - CPU: {analysis['cpu_usage_percent']:.1f}% (阈值: {CPU_LIMIT_PERCENT}%)")
        
        # 创建 GitHub Issue（如果配置了 Project ID）
        if GITHUB_PROJECT_ID:
            import urllib.request
            url = f"https://api.github.com/repos/{os.getenv('GITHUB_REPOSITORY', '')}/issues"
            data = json.dumps({
                "title": "[Cost-Alert] 成本监控异常",
                "body": report_content,
                "labels": ["Cost-Alert"]
            }).encode("utf-8")
            
            req = urllib.request.Request(
                url,
                data=data,
                headers={
                    "Authorization": f"token {os.getenv('GITHUB_TOKEN', '')}",
                    "Content-Type": "application/json"
                },
                method="POST"
            )
            
            try:
                urllib.request.urlopen(req)
                print("[INFO] GitHub Issue 已创建")
            except Exception as e:
                print(f"[WARN] Issue 创建失败: {e}")
        
        sys.exit(1)
    else:
        print(f"\n[OK] 成本监控正常")
        sys.exit(0)


if __name__ == "__main__":
    main()
