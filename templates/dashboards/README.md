# docs/dashboards/ — 项目图形资产（RULE-054）

**这一目录是全项目唯一的「活图」落点。** 十个槽位固定，一图一决策，**只更新不重生成**。

## 采用（一次性）

```powershell
node "<RULES_ROOT>\hooks\scripts\dashboard-registry-check.mjs" --root <仓根> --init
```

`--init` 发现任何槽位文件已存在就整体拒绝，不会覆盖在用的图；只补缺失槽位时，从本模板目录手工复制**单个文件**。

## 十槽

| 槽位 | 文件 | 决策动作 | 节奏 |
|---|---|---|---|
| 00 | `00-cockpit.md` | 继续 / 加人 / 收缩 / 暂停 | 周 + 月 |
| 01 | `01-scope-wbs.md` | 接受或拒绝范围变更 | 立项 + 变更 |
| 02 | `02-milestone-critical-path.md` | 延期时砍范围还是加资源 | 周 |
| 03 | `03-flow-board-cfd.md` | 调 WIP 上限 / 拆阻塞 | 日 + 周 |
| 04 | `04-resource-load-heat.md` | 调人 / 外购能力 / 收敛并行 | 周 |
| 05 | `05-evm-s-curve.md` | 追加预算还是降档交付 | 月 |
| 06 | `06-risk-issue-matrix.md` | 关闭 / 升级 / 显式接受 | 周 |
| 07 | `07-architecture-dependency.md` | 拆分 / 合并 / 加隔离 / 排技术债 | 季度 + 变更 |
| 08 | `08-code-health.md` | 评审加人 / 技术债排期 / 分支收口 | 周 |
| 09 | `09-env-release-dora-slo.md` | 放行 / 回滚 / 冻结发布窗口 | 发布时 + 周 |

先跑 7 张：`00` `02` `03` `05` `06` `07` `09`；软件项目优先补 `08`。其余槽位置 `status: deferred` + `revisit`，**槽位本身不许消失**。

## 四条硬纪律

1. **文件名 = 槽位号 + 固定 slug，永不含日期 / v2 / final / 副本。** 要新读数就改这张表，历史交给 git。
2. **每槽位一份源文件**；需要可视化产物时只允许同名的唯一一份 `<id>-<slug>.render.html`，且它不得反向成为真源。
3. **红黄绿必须由 `thresholds.md` 的指标名推导**。没有指标名的颜色即 FAIL。
4. **`registry.json` 由 `--emit-registry` 派生**，提交前跑 `--check`；清单不许手写（同 RULE-053 §3）。

## 每日 / 每周收尾

```powershell
node tools/dashboard-check.mjs          # 各仓启动器，转发到共享根 canonical 实现
node tools/dashboard-check.mjs --check  # 顺带对账 registry.json
```

FAIL 即任务未完成，不得宣布「图已更新」。宣布更新时必须附门禁输出与 `last_updated` 读数。
