---
name: integration-design
version: v1.1.0
type: skill
enabled: true
mode: [standard, creator]
description: "设计阶段进行第三方服务集成设计 — 外部 API 对接、OAuth 登录、Webhook 回调、超时重试熔断降级、费用与限制评估。外部服务超过 2 个时必须触发。触发词: 第三方集成、外部API、Webhook、OAuth、支付集成、短信、邮件、推送、云存储、AI服务。"
updated: 2026-09-11
depends_on: [system-design]
composes: [writing-plans]
---

# Integration Design

## 负责代理

`architect` — 第三方服务集成设计由架构师代理负责，确保集成方案安全、可容错。

## 何时使用

- 需要集成**第三方 API 服务**（支付、短信、邮件、地图、AI 等）时
- 需要设计**Webhook 回调**（接收第三方事件推送）时
- 需要集成**OAuth 第三方登录**（Google / GitHub / 微信等）时
- 需要定义**外部服务容错策略**（超时、重试、熔断、降级）时
- 需要评估**第三方服务费用和限制**（Rate Limit、配额、成本）时
- **外部服务超过 2 个时必须触发本技能**，不可跳过

**触发关键词**: "第三方集成"、"外部API"、"Webhook"、"OAuth"、"支付集成"、"短信"、"邮件"、"推送"、"云存储"、"AI服务"

## 与其他技能的关系

```text
brainstorming → system-design → api-design
                     ↓              ↓
              integration-design ←──┘
                     ↓
              writing-plans → executing-plans
```

> **衔接规则**:
> - `integration-design` 依赖 `system-design` 的架构设计（技术选型、部署方案）
> - `integration-design` 与 `api-design` **并行执行**，集成设计中的接口契约直接影响 API 封装层
> - `integration-design` 的容错策略必须与 `system-design` 的架构约束一致
> - `integration-design` 的 Webhook 设计必须与 `api-design` 的回调接口定义一致

## 设计阶段总体流程

```text
需求确认 → 架构设计 → 集成设计 → API设计 → UI设计
              ↑           ↓          ↓
              └─── 互相校验、迭代调整 ──┘
```

**输出文件清单**:

```text
docs/
├── architecture.md          ← 架构设计（system-design 技能输出）
├── database-schema.md       ← 数据库设计（system-design 技能输出）
├── integration-design.md    ← 集成设计（本技能输出）
├── api-design.md            ← 接口设计（api-design 技能输出）
├── ui-wireframe.md          ← UI/页面设计（ui-design 技能输出）
```

> **校验关系**: 集成设计中的第三方服务 → 架构设计中的外部依赖清单；接口契约 → API 封装层；Webhook URL → API 路由定义，三者必须一致。

## 执行流程（骨架）

> 各 Phase 的详细模板、表格与代码见文末参考文档，按需加载。

### Phase 1: 集成清单梳理

- 从 brainstorming 需求和 system-design 架构中提取**全部第三方服务清单**（用途/费用/替代方案/风险等级）
- 必要性评估：必要性/成本/可靠性/迁移成本/文档质量 5 维打分，总分 < 15 需评估替代方案
- 关键服务做选型对比（≥2 个候选，含手续费、地区支持、MoR、开发复杂度）

评估矩阵与选型示例 → [references/service-contracts.md](references/service-contracts.md) Phase 1。

### Phase 2: 接口契约定义

- 每个服务定义契约：文档/SDK/环境（沙箱 vs 生产密钥分离）、认证方式、核心接口 + 超时、Rate Limit、错误处理表、费用
- 认证方式汇总（API Key / OAuth 2.0 / Basic / HMAC / mTLS）
- OAuth 集成：授权码流程时序图 + 安全要点（State 防 CSRF、PKCE、Token 不回传前端、Scope 最小化、账户合并）

契约模板与 OAuth 时序图 → [references/service-contracts.md](references/service-contracts.md) Phase 2。

### Phase 3: 容错与重试设计

- 分层超时（连接 3s / 读取 10s / 总 15s / 用户感知 5s），各服务按特性调整
- 指数退避重试（区分可重试/不可重试错误），支付/AI 保守 2 次
- 熔断器状态机（CLOSED → OPEN → HALF_OPEN），按服务配置失败阈值与冷却时间
- 降级方案矩阵 + 降级优先级（核心支付不可降级 → 可选统计可关闭）

详细配置表与代码 → [references/resilience-webhooks.md](references/resilience-webhooks.md) Phase 3。

### Phase 4: Webhook 设计

- 端点规范 `/webhooks/{provider}/{event}` + 端点清单
- **必须签名验证**（HMAC-SHA256 / RSA，防重放 + `compare_digest` 防时序攻击）
- **必须幂等处理**（唯一事件 ID + 去重存储 + 处理状态机）

签名验证代码与幂等要素 → [references/resilience-webhooks.md](references/resilience-webhooks.md) Phase 4。

### Phase 5: 输出 integration-design.md

保存到 `docs/integration-design.md`，章节结构模板 → [references/resilience-webhooks.md](references/resilience-webhooks.md) Phase 5。

## 参考文档（一层深，按需加载）

| 文档 | 内容 | 何时读 |
|------|------|--------|
| [references/service-contracts.md](references/service-contracts.md) | 服务清单、评估矩阵、选型对比、契约模板、认证方式、OAuth 设计 | 执行 Phase 1-2 时 |
| [references/resilience-webhooks.md](references/resilience-webhooks.md) | 超时/重试/熔断/降级、Webhook 端点/签名/幂等、输出结构 | 执行 Phase 3-5 时 |

## 集成设计检查清单

- [ ] 所有第三方服务已列出（含用途、费用、替代方案）
- [ ] 服务必要性已评估（评分 >= 15 方可采用）
- [ ] 关键服务有选型对比（>= 2 个候选）
- [ ] 每个服务的接口契约已定义
- [ ] 每个服务的认证方式已明确
- [ ] OAuth 流程已完整设计（含 State 防 CSRF）
- [ ] 每个服务有超时设置
- [ ] 每个服务有重试策略（含指数退避参数）
- [ ] 每个服务有熔断器配置
- [ ] 每个服务有降级方案
- [ ] Webhook 端点已定义
- [ ] Webhook 签名验证已实现
- [ ] Webhook 幂等处理已实现
- [ ] 每个服务的费用和 Rate Limit 已记录
- [ ] 敏感数据不通过第三方传输明文
- [ ] 沙箱/生产密钥已分离
- [ ] 第三方服务密钥通过环境变量管理

## 硬性规则

- **外部服务超过 2 个时必须设计集成方案** — 系统化设计，避免散落各处
- **所有外部调用必须有超时设置** — 不可无限制等待
- **所有外部调用必须有重试策略** — 网络抖动是常态，不是异常
- **所有外部调用必须有熔断器** — 防止级联故障
- **所有外部调用必须有降级方案** — 外部服务不可用不能拖垮系统
- **Webhook 必须验证签名** — 防止伪造请求
- **Webhook 必须幂等处理** — 第三方可能重复推送
- **敏感数据不得通过第三方传输明文** — 脱敏后再发送
- **必须记录每个第三方服务的费用和限制** — 避免意外账单
- **沙箱密钥和生产密钥必须分离** — 不可混用
- **OAuth State 参数必须随机生成并验证** — 防 CSRF 攻击
- **第三方服务密钥必须通过环境变量管理** — 不可硬编码

## 反模式

- **禁止在生产环境使用第三方沙箱密钥** — 沙箱密钥仅用于测试
- **禁止无超时等待外部响应** — 可能导致请求堆积和资源耗尽
- **禁止忽略 Rate Limit 导致服务被封** — 必须实现限流和排队
- **禁止信任外部服务永远可用** — 没有 SLA 100% 的服务
- **禁止 Webhook 不做签名验证** — 任何人都能伪造 Webhook 请求
- **禁止 Webhook 不做幂等处理** — 重复推送是常见行为
- **禁止在代码中直接使用第三方 SDK 而不封装** — 封装一层便于切换服务商
- **禁止"第三方服务挂了就挂了"的心态** — 必须有降级方案
- **禁止忽略第三方服务的费用增长** — 监控月度费用，设置预算告警
- **禁止在日志中输出第三方 API 密钥** — 过滤敏感信息
- **禁止同步调用耗时第三方服务** — 支付确认、AI 推理等必须异步化
- **禁止不验证第三方返回数据的合法性** — 假设第三方返回的数据可能是恶意的
