# V12 Reach State Evolution 实现记录
本页回答什么问题：`V12` 如何让 tailreach 真正拥有带时间记忆的 discharge state，它和 `V10` 的区别是什么，以及它是否对双站点指标带来了实质改善。

Updated: 2026-04-20

## 1. 这版的定位

`V10` 已经让 tailreach 具备了：

- `stage`
- `storage`
- `effective discharge`
- 与主库区入流的松弛耦合

但它本质上仍然是：

- `storage + algebraic target outflow + relaxed coupling`

也就是说，尾段出流虽然已经能影响主库区，但它本身还没有真正的“状态记忆”。

`V12` 的目标就是补上这一层：

- 让 tailreach 拥有一个真实的 `QSTATE`
- 不再每步直接采用即时代数出流
- 而是让 `QSTATE` 以 reach 尺度、局部波速和时间步共同决定的响应速度去演化

## 2. 新增的状态量

新增了：

- `TAIL_Q_STATE`
- `TAIL_Q_TARGET`
- `TAIL_TRAVEL_TIME`
- `TAIL_WAVE_CELERITY`
- `TAIL_REACH_LENGTH`
- `TAIL_Q_STATE_INITIALIZED`

位置：

- [w2modules.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/w2modules.F90:140)
- [input.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/input.F90:318)
- [init.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/init.F90:60)
- [init-geom.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/init-geom.F90:506)

## 3. 新的计算逻辑

### 3.1 `V10` 的旧逻辑

旧逻辑是：

1. 先算一个 hydraulic target discharge
2. 直接把这个 target 与当前出流做 relaxed blending
3. 用这个 blended outflow 更新 storage

这意味着出流虽然有“平滑”，但本质仍然是每步就地响应。

### 3.2 `V12` 的新逻辑

现在在 [w2_main.f90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/w2_main.f90:1692) 中，tailreach 会经历两步状态演化：

1. 先根据当前 stage 计算 `QTARGET_OLD`
2. 用当前 `QSTATE`、reach 长度、局部水深和波速，推进到一个新的 `QSTATE`
3. 用这个 `QSTATE` 更新 storage
4. 再由 storage 反解新的 stage
5. 再根据新的 stage 计算 `QTARGET_NEW`
6. 再做一次 `QSTATE` 修正

新增的关键 helper 是：

- `ADVANCE_TAIL_Q_STATE`
- `COMPUTE_TAIL_REACH_LENGTH`

其中响应时间尺度的构造是：

- `TAIL_REACH_LENGTH / (wave celerity + local velocity)`

并且做了安全约束：

- `alpha` 下限 `0.05`
- `alpha` 上限 `0.25`

这保证 tailreach 的 discharge 演化不会重新退回“即时 target 代换”。

## 4. smoke 验证

新增 smoke 硬门槛：

- `[V12_Q_STATE]`

对应脚本：

- [run_w2_v0_v1_smoke.py](/C:/Users/NING/Desktop/v455/analysis/run_w2_v0_v1_smoke.py:1)

通过结果：

- 短窗：[smoke-summary-20260420-102016.csv](/C:/Users/NING/Desktop/v455/analysis/verification/w2_v0_v1_smoke/results/smoke-summary-20260420-102016.csv)
- 延长窗：[smoke-summary-20260420-102112.csv](/C:/Users/NING/Desktop/v455/analysis/verification/w2_v0_v1_smoke/results/smoke-summary-20260420-102112.csv)
- 长窗：[smoke-summary-20260420-102838.csv](/C:/Users/NING/Desktop/v455/analysis/verification/w2_v0_v1_smoke/results/smoke-summary-20260420-102838.csv)

三组都满足：

- `has_v12_q_state = 1`
- `seg2_valid_count > 0`
- `has_runtime_error = 0`
- `has_late_seg2_add = 0`

## 5. 结果变化

长窗 `44430-44458` 下，`V12` 的关键结果是：

- `SEG 2 RMSE = 4.990`
- `SEG 2 Bias = -4.448`
- `SEG 222 RMSE = 0.797`
- `SEG 222 Bias = -0.606`
- `SEG 2 - SEG 222 RMSE = 4.309`
- `SEG 2 - SEG 222 Bias = -3.842`

和 `V10` 当前保留的 `TAIL_FLOW_COUPLING_RELAX = 0.15` 基线相比：

- `SEG 2` 明显改善
- `SEG 222` 基本回到 `V7-V9` 水平
- 两点水面差没有恶化，反而略有改善

这是到目前为止最重要的正结果之一。

## 6. V12 的物理含义

`V12` 第一次让 tailreach 具备了：

- “有自己的 discharge state”

而不是仅仅：

- “根据当前 stage 算一个出流值”

这使得 tailreach 在架构上更像一个真正的 reach，而不只是一个 storage-discharge patch。

## 7. 还没做到什么

`V12` 仍然没有做到：

- 完整动量方程
- 多断面内部传播
- 过渡状态在 reach 内部连续分布

也就是说，`V12` 已经是 `V10` 的明显升级，但它还不等于完整的 1D 局部河段模型。

## 8. 对后续 V13 的意义

现在可以更清楚地说：

- `V11` 把尾段对象从“单链接”提升成“固定物理域”
- `V12` 把尾段动力从“代数出流”提升成“有记忆的 discharge state”

所以下一步 `V13` 最自然的方向就是：

- 不再把过渡状态挂在 reach 外部
- 而是让河流态-过渡态-库区态成为 fixed tail domain 内部的连续状态
