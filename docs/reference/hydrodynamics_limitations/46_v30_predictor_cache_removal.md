# V30 Predictor Cache Removal

本页回答什么问题：V18 遗留的 predictor reuse 是否只影响性能，还是会改变最终接受的 tail 流量、储量和水位状态；若它进入物理路径，应该如何做最小正确清理。

Updated: 2026-07-16

## 1. 触发证据

V29 的 6010 个接受步中，`89.60%` 的相邻微步保持同一 `Qstate`，最长保持 `0.030804 day`。当时 `Qstate–Qtarget` correlation 只有 `0.7804`、RMSE 为 `746.14 m3/s`。

predictor cache 的原始意图是减少重复计算。它用 `|dWSE|<=0.02 m`、`|dQ|<=25 m3/s` 和 `MAX_SKIP=20` 判断是否复用上一状态。性能优化不应显著改变接受态，因此先做单变量不变性实验：仅令 `MAX_SKIP=0`，其他源代码、输入和 extended 窗口不变。

## 2. 不变性实验结果

关闭复用后：

- 接受步数 `6010 -> 5927`；
- `Qstate–Qtarget` correlation `0.7804 -> 0.9938`；
- `Qstate–Qtarget` RMSE `746.14 -> 108.12 m3/s`；
- 等效 `FMANN` 倍率 P10/P90 从 `0.9178/1.0699` 收紧到 `0.9948/1.0043`；
- hold fraction `89.60% -> 0.0169%`；
- extended runtime 仍约 `25 s`，没有可辨识的性能收益。

外部水位结果只发生较小变化：

- SEG 2 RMSE `1.258642 -> 1.257266 m`；
- SEG 222 RMSE `0.229205 -> 0.226510 m`；
- head RMSE `1.332942 -> 1.326409 m`；
- SEG 2/head slope `0.000750/0.000648 -> 0.000717/0.000614`。

因此 cache 不是剩余精度缺口的主因，但不变性检查失败：它显著改变了接受态动量目标关系和自适应步进轨迹，同时没有带来当前基线可见的性能收益。

## 3. 最小正确重构

没有保留 `MAX_SKIP=0` 的死分支，而是完整删除：

- predictor cache 的 WSE/Q arrays、valid/reused flags、skip counter 和 tolerance constants；
- `RUN_TAIL_PREDICTOR` 中的 reuse 判定、available-water cache recheck 和状态复制分支；
- commit/rollback 中的 cache 同步与失效逻辑；
- `[V18_PREDICT_REUSE]` marker 及 smoke/scan 中要求“必须发生 skip”的旧门禁。

`RUN_TAIL_PREDICTOR` 现在每次都执行 `UPDATE_TAIL_STAGE`，然后保存 predictor 状态、恢复 trial 前状态并提交 predictor 结果。V24 的 available-water cap 和 V26 的 matrix-consumer re-cap 仍保留；删除的只是跳过物理更新的捷径。

## 4. 链路检查

输入：不变，仍为 `QIN`、reservoir interface stage 和当前 tail state。

处理：每个 predictor pass 都重新计算 storage、Q target、Q state 和 profile；不再按固定阈值复用旧状态。

状态：删除 cache 派生状态；守恒状态和 rollback save/restore 不变。

输出：不再产生 `[V18_PREDICT_REUSE]`；V18 predictor/corrector、V24–V29 诊断继续保留。

上下游：接口 commit、reservoir matrix、temperature/volume consumers 的 committed flux contract 不变。

## 5. Fresh extended 验收

- 16 项 Python tests：通过；
- reduced console build：通过；
- fresh `TMEND=44436.5`：约 `25.3 s`，正常退出；
- 完整 `assert_pass` 及 V24–V29 独立门禁：通过；
- `max|RTAIL|=3.8835e-10 m3/s`；
- profile gap max `0.0010486 m3`；
- computational warning `0`；
- `flowbal %VOLerror=-0.00005456%`。

## 6. 审视结论

V30 是数值正确性清理，不是精度优化。删除 cache 后，Q state 与同一接受态 hydraulic target 几乎闭合，但 SEG 2 响应仍只有观测约四成，storage response 仍只有观测需求的 `53.45%`。这进一步排除了 Q-state 更新频率和固定 Manning 偏差，下一步应检查 tail control-volume 的源汇与几何容量/profile shape，而不是重新引入松弛或阈值。
