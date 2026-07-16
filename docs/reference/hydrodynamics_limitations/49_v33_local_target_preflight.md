# V33 Local-Target Preflight

本页回答一个实施前问题：V32 已经建立可加的 segment 体积后，能否直接把现有局部 Manning 流量公式推广到 segment 2:5 的每个界面，并据此启用多控制体连续方程？

Updated: 2026-07-16

## 1. 实验范围

V33 是 shadow diagnostic，不是新的水动力求解器。它在每个已接受时间步，用 V32 的既有 stage profile、真实断面几何和当前 Manning 输入，分别计算 segment 2、3、4、5 下游界面的局部水力目标：

```text
Qtarget = Aup * Rhup^(2/3) * sqrt((Wup - Wdn) / dx) / nup
```

其中最后一个界面的 `Wdn` 是既有下游边界水位，其他界面使用下一 segment 的既有水位。`Qcommit` 仍是 V32 已提交给 reservoir 的唯一边界流量。

接受步新增 `[V33_LOCAL_TARGET]`，记录 `IS/ISEG/QCOMMIT/QTARGET/WUP/WDN/DX/STORAGE`。分析脚本按界面汇总目标流量与已提交流量的相关性、斜率、差值、比率分位数和 ±20% 一致率；门禁要求每个 V32 接受步至少覆盖 active domain 的每个 segment，不能用少量 marker 冒充完整样本。

V33 不写入任何持久状态，不改变 stage、storage、Q state、interface commit、reservoir consumer 或 autostep 判定。

## 2. 链路检查

- 输入：已接受的 V32 `TAIL_STAGE_SEG`、segment 2:5 bathymetry、cell length，以及活动 bathymetry 文件 `DIXING20250226.csv` 中统一的 Manning `n=0.03`。
- 处理：只在接受态对每个局部界面调用与既有 link-flow 同型的 Manning 计算；不参与 predictor、corrector 或 reservoir matrix。
- 状态：V27/V31 的唯一总 storage 和唯一已提交边界 Q 保持不变；V32 segment volumes 仍只是该总 storage 的可加几何分解。
- 输出：`[V33_LOCAL_TARGET]` 与两个被 `.gitignore` 排除的派生 CSV；源码提交中只保留可复现分析器和测试。
- 上游影响：无。
- 下游影响：无。V33 只判断下一步方案是否具备基线兼容性。

## 3. Extended 证据

每个界面均有 5927 个接受态样本：

| 界面 | 上游 segment | `Qtarget/Qcommit` 中位数 | P10–P90 | ±20% 一致率 | 平均 `Qtarget-Qcommit` (m3/s) | RMSE (m3/s) |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 2 | 0.999903 | 0.994234–1.005544 | 99.865% | 4.180 | 113.626 |
| 2 | 3 | 2.325206 | 1.916184–2.489710 | 0% | 6094.661 | 6101.860 |
| 3 | 4 | 1.543939 | 1.411247–1.738744 | 0% | 2748.020 | 2772.608 |
| 4 | 5 | 2.535427 | 2.168839–2.951035 | 0% | 7476.003 | 7505.365 |

界面 1 是当前整体 link closure 的入口，因此闭合在预期之内。界面 2–4 在当前 profile 上均显著高于唯一已提交通过流量；没有一个样本落入 ±20%。这与 V28 “按当前几何推广局部输水能力后过度导流”的否证方向一致。

若只在同一 stage profile 下反推保持 `Qcommit` 所需的阻力，因为 `Q ∝ 1/n`，界面 2–4 对应的中位等效 Manning `n` 约为 `0.070 / 0.046 / 0.076`。这些数值大且不均匀，只是当前几何、stage profile 和简化局部公式共同产生的**等效阻力需求**，不是经过观测验证的河道糙率。

## 4. 回归验证

- reduced build：通过；
- fresh short 与 fresh extended：通过；
- 21 项 Python tests：通过；
- 完整 `assert_pass`：通过；
- V24–V32 守恒、domain、profile、single-step 和 segment-volume 门禁：全部通过；
- computational warning：0；
- `max|VTOTAL-sum(VSEG)|=0.0010273 m3`；
- `flowbal %VOLerror=-0.00005456%`；
- SEG 2 / SEG 222 / head bias、RMSE 和 slope 与 V32 完全相同。

## 5. 审视结论

“直接把现有局部 Manning 目标作为四个界面的真实 flux”没有通过实施前检查。它会从一个内部界面出流为当前通过流量 1.54–2.54 倍的状态启动，不能保持 V32 基线，并有重现 V28 过度导流的明确风险。因此 V33 不启用多控制体状态，也不把错误闭合包装成数值求解问题。

这项证据没有否定多控制体连续方程本身；它否定的是“用当前局部闭合、当前 profile 和未经约束的统一 `n=0.03` 直接激活”的具体方案。真正的下一步必须先确定局部动量/阻力闭合如何被物理约束。

## 6. 需要的物理选择

当前数据只有 segment 2 与 segment 222 水位，缺少 segment 3:6 的同步水位、断面校核或独立糙率证据，无法区分以下解释：

1. 中间断面或 reach length 仍有几何代表性误差；
2. 局部损失、结构物和非均匀流需要额外的有效阻力；
3. 当前线性 stage profile 本身不是内部真实水面线；
4. 应保留 W2 主体并把这段河道交给外部一维非恒定流求解器。

因此不能继续自动率定 segment-specific resistance。继续施工前需要用户选择验收目标和物理约束：以现有端点水位误差为工程率定目标，还是先补充中间观测/几何证据，或停止在 V32/V33 结构基线并采用外部河道求解器。
