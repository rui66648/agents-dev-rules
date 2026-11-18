# 脚本目录说明

> 本目录包含项目开发、测试、监控相关的自动化脚本。

---

## 脚本分类

### 质量保障
| 脚本 | 用途 | 触发时机 |
|------|------|----------|
| `ai_model_test.py` | AI 模型测试与幻觉检测 | CI/CD 流水线 |
| `ai_security_lint.py` | 代码安全扫描 | 提交前 |
| `test-audit.py` | 测试用例审计 | 部署前 |
| `doc_review_llm.py` | 设计文档自动审查 | 文档更新后 |

### 性能与成本
| 脚本 | 用途 | 触发时机 |
|------|------|----------|
| `span_monitor.py` | Span 消耗监控 | 每日定时 |
| `cost_monitor.py` | 成本分析 | 每日定时 |
| `agent_slo_monitor.py` | Agent 服务质量监控 | 每日定时 |
| `debt_metrics.py` | 技术债务指标 | 定期执行 |

### 运维与部署
| 脚本 | 用途 | 触发时机 |
|------|------|----------|
| `check-deployment.py` | 部署健康检查 | 部署后 |
| `agent_audit_worker.py` | Agent 变更审计 | 变更触发 |
| `estimate_change.py` | 变更影响评估 | 开发中 |

### 工具类
| 脚本 | 用途 | 触发时机 |
|------|------|----------|
| `rules-audit.py` | 规则库引用审计 | 规则更新后 |
| `resolve-rules-root.py` | 规则路径解析 | 工具调用 |
| `generate_model_artifact.py` | 模型产物生成 | 按需执行 |
| `fetch-ui-component.py` | UI 组件获取 | 按需执行 |

---

## 运行方式

### 直接运行
```bash
python scripts/<script-name>.py
```

### 通过命令调用
```bash
/ai-test        # 运行 AI 模型测试
/security-lint  # 运行安全扫描
/cost-report    # 生成成本报告
```

### 定时执行
通过 `Schedule` 工具配置定时任务，详见 [rules/cicd-rules.md](../rules/cicd-rules.md)。

---

## 脚本编写规范

1. **输出格式**：所有脚本输出必须是结构化的（JSON 或 Markdown）
2. **错误处理**：使用 try-catch，错误信息必须包含上下文
3. **日志记录**：使用标准 `logging` 模块，禁止使用 `print()`
4. **参数校验**：所有输入参数必须经过校验
5. **超时控制**：网络请求必须设置超时

---

*最后更新：2026-08-10*
