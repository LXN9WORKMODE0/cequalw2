# V7 最小尾段水位闭环实现记录
本页回答什么问题：`V7` 这一版到底做了什么，它和 `V6` 的差别是什么，现在是否已经能做双站点水位验证，以及它离真正的尾段 1D 子求解器还差什么。

Updated: 2026-04-18

## 1. 这版的定位

`V6` 只建立了 `tailreach <-> reservoir` 的耦合面变量，但 `SEG 2` 在 `wl.csv` 里仍然是 `-999`。

`V7` 的目标不是完整 1D Saint-Venant，而是更小的一步：

- 给 `TAIL_UPSEG -> TAIL_DNSEG` 一个最小局部水位求解。
- 把这个局部 stage 显式写进 `wl.csv`。
- 让 `SEG 2` 和 `SEG 222` 都进入同一套双站点对比。

## 2. 代码改动

### 2.1 新增状态量

新增了：

- `TAIL_STAGE_MODE`
- `TAIL_DEPTH_UP`
- `TAIL_STAGE_VALID`

对应位置：

- [w2modules.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/w2modules.F90:126)
- [input.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/input.F90:316)
- [init.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/init.F90:57)
- [init-geom.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/init-geom.F90:502)

### 2.2 `w2_main.f90` 中的最小尾段子求解

`V7` 在 `w2_main.f90` 里新增了一组内部子程序：

- `UPDATE_TAIL_STAGE`
- `COMPUTE_TAIL_NORMAL_STAGE`
- `SOLVE_TAIL_STANDARD_STEP`
- `TAIL_STANDARD_RESIDUAL`
- `TAIL_MANNING_RESIDUAL`
- `TAIL_SECTION_PROPS`
- `TAIL_FMANN`

核心逻辑是：

1. 用 `QC(TAIL_DNSEG)` 作为尾段链接流量。
2. 用 `ELWS(TAIL_DNSEG)` 作为下游边界 stage。
3. 先求一个局部 normal-stage 参考值。
4. 再用简化 standard-step 关系求 `TAIL_WSE_UP`。
5. 如果标准步无法稳定 bracket，则退回 `transition-weighted` fallback。
6. 最后对 `TAIL_WSE_UP` 做物理范围钳制，防止 stage 爆炸到不可写入 CSV 的数量级。

实现位置：

- [w2_main.f90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/w2_main.f90:1375)

### 2.3 `wl.csv` 输出覆盖

`outputa2w2tools.F90` 里的水位输出逻辑原来是：

- 只要 `I < CUS(JB)`，就直接写 `-999`

现在改成：

- 如果该段属于 protected tailreach，而且 `TAIL_STAGE_VALID(JB)` 为真，则对 `TAIL_UPSEG` 输出 `TAIL_WSE_UP(JB)`

实现位置：

- [outputa2w2tools.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/outputa2w2tools.F90:136)

## 3. 验证链路

### 3.1 先红后绿

先把 smoke harness 抬成硬门槛：

- 必须出现 `[V7_TAIL_STAGE]`
- `seg2_valid_count > 0`

改动位置：

- [run_w2_v0_v1_smoke.py](/C:/Users/NING/Desktop/v455/analysis/run_w2_v0_v1_smoke.py:1)

红灯结果：

- [smoke-summary-20260418-204613.csv](/C:/Users/NING/Desktop/v455/analysis/verification/w2_v0_v1_smoke/results/smoke-summary-20260418-204613.csv)

第一次实现后，`SEG 2` 写成了 `********`，说明 stage 数值炸到了 CSV 格式上限，随后加了物理范围钳制。

### 3.2 绿灯结果

短窗通过：

- [smoke-summary-20260418-205451.csv](/C:/Users/NING/Desktop/v455/analysis/verification/w2_v0_v1_smoke/results/smoke-summary-20260418-205451.csv)

延长窗通过：

- [smoke-summary-20260418-205544.csv](/C:/Users/NING/Desktop/v455/analysis/verification/w2_v0_v1_smoke/results/smoke-summary-20260418-205544.csv)

长窗通过：

- [smoke-summary-20260418-210301.csv](/C:/Users/NING/Desktop/v455/analysis/verification/w2_v0_v1_smoke/results/smoke-summary-20260418-210301.csv)

长窗关键结果：

- `seg2_valid_count = 281`
- `seg222_valid_count = 281`
- `has_runtime_error = 0`
- `has_late_seg2_add = 0`

## 4. 双站点初步结果

长窗 `44430-44458` 的快速对比如下：

- `SEG 2` 对库尾实测：`RMSE = 5.235 m`，`Bias = -4.875 m`
- `SEG 222` 对坝前实测：`RMSE = 0.795 m`，`Bias = -0.600 m`
- `SEG 2 - SEG 222` 水面差：`RMSE = 4.604 m`，`Bias = -4.275 m`

这说明：

- `V7` 已经把问题从“没有库尾数值”推进到“有库尾数值且能双站点验证”。
- 但它还没有把真实水面线做对。
- 当前最明显的问题是：`SEG 2` 仍然系统偏低，导致纵向水面差仍然塌缩。

## 5. 这版的真实意义

`V7` 的意义不是“问题解决了”，而是：

- 终于具备了双站点物理诊断条件。
- 后续所有尾段改造不再只能盯 `SEG 222` 单点。
- 可以开始对真正的尾段子求解器做定量改进，而不是只看 front buffer 日志。

## 6. 下一步

下一步不该再停在“让 `SEG 2` 有值”，而应转向：

1. 把 `TAIL_UPSEG -> TAIL_DNSEG` 从单步 stage 估计推进到真正的局部 1D reach。
2. 让尾段 stage 不只是输出覆盖，而是逐步反馈回主边界闭合。
3. 重新压 `SEG 2` 的负偏差和 `SEG 2 - SEG 222` 的坡降塌缩。
