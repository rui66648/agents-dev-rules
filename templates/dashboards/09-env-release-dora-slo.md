---
slot: 09
slug: env-release-dora-slo
title: 环境矩阵 + 发布看板 + DORA / SLO 图
decision: 放行 / 回滚 / 冻结发布窗口（拍板人：发布负责人；判据只认发布通道输出的校验信号）
cadence: daily
owner: 待指派
status: deferred
reason: 骨架由 RULE-054 建立，尚未取数；占住槽位，防止日后另起一张重复图
revisit: 2026-11-30
---
# 09 环境矩阵 + 发布看板 + DORA / SLO 图

## 决策
放行 / 回滚 / 冻结发布窗口（拍板人：发布负责人；判据只认发布通道输出的校验信号）

## 读数
（deferred：未取数。转 active 前先在 thresholds.md 补齐本图指标口径与数据源，再逐条填表；口径变更要在「变化」段留 delta。）

| ID | 环境 | 当前版本 V | 与主干是否漂移 | 部署频率 | 变更 lead time | 失败率 | 恢复时间 | SLO 达成 | 灯 |
|---|---|---|---|---|---|---|---|---|---|

## 图
本图唯一的渲染位（表格即图，或同名 `<id>-<slug>.render.html`）。禁止另存副本，历史交给 git。

## 变化
- 2026-11-01 建立骨架（deferred，无读数）

## 取数
- 数据源：发布脚本的 build-log / 审计台账 + 监控端点；DORA 四项与 SLO 定义取自 thresholds.md 的口径列。
- 负责人：待指派
- last_updated: 未更新
