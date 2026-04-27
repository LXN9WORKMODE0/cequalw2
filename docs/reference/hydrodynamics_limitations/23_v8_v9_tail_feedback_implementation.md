# V8/V9 尾段语义同步与主边界反馈实现记录
本页回答什么问题：`V8` 和 `V9` 具体做了什么、验证结果怎样、以及为什么它们虽然稳定却没有明显改善双站点指标。

Updated: 2026-04-18

## 1. 这两版的定位

`V7` 已经让 `SEG 2` 有了可输出的最小尾段 stage，但问题仍然是：

- 尾段 stage 和 front-state 还是分离的。
- 尾段 stage 对主边界动力学几乎没有反馈。

所以这一步顺着总蓝图继续做了两层弱耦合：

- `V8`：把 `TAIL_WSE_UP/TAIL_DEPTH_UP` 接入 `FRONT_WSE/FRONT_DEPTH`
- `V9`：把 `TAIL_WSE_UP` 以松弛 ghost-head 的方式接入主水面方程入口

## 2. V8 做了什么

在 [layeraddsub.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/layeraddsub.F90:608) 中：

- 如果 `TAIL_STAGE_VALID(JB)` 且 `TAIL_UPSEG(JB) == FRONT_SEG(JB)`，则不再用 `ELWS(IU)` 当作前沿 stage
- 改用：
  - `FRONT_WSE = TAIL_WSE_UP`
  - `FRONT_DEPTH = TAIL_DEPTH_UP`

同时新增诊断：

- `[V8_FRONT_SYNC]`

对应 smoke harness 也提升为硬要求，见：

- [run_w2_v0_v1_smoke.py](/C:/Users/NING/Desktop/v455/analysis/run_w2_v0_v1_smoke.py:1)

## 3. V9 做了什么

在 [w2modules.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/w2modules.F90:148) 中新增：

- `TAIL_HEAD_FEEDBACK_RELAX = 0.25`

在 [w2_main.f90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/w2_main.f90:883) 和 [w2_main.f90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/w2_main.f90:974) 中：

- 对 protected upstream-flow branch，用 `TAIL_WSE_UP` 构造一个 ghost-head 对应的 `TAIL_Z_UP`
- 以松弛系数 `0.25` 进入：
  - `D(IU)` 的自由液面方程入口
  - `Z(IU-1)` 的边界水位更新

新增诊断：

- `[V9_TAIL_FEEDBACK]`

## 4. 验证结果

### 4.1 通过的 smoke

短窗：

- [smoke-summary-20260418-212400.csv](/C:/Users/NING/Desktop/v455/analysis/verification/w2_v0_v1_smoke/results/smoke-summary-20260418-212400.csv)
- [smoke-summary-20260418-213635.csv](/C:/Users/NING/Desktop/v455/analysis/verification/w2_v0_v1_smoke/results/smoke-summary-20260418-213635.csv)

延长窗：

- [smoke-summary-20260418-212450.csv](/C:/Users/NING/Desktop/v455/analysis/verification/w2_v0_v1_smoke/results/smoke-summary-20260418-212450.csv)
- [smoke-summary-20260418-213725.csv](/C:/Users/NING/Desktop/v455/analysis/verification/w2_v0_v1_smoke/results/smoke-summary-20260418-213725.csv)

长窗：

- [smoke-summary-20260418-213131.csv](/C:/Users/NING/Desktop/v455/analysis/verification/w2_v0_v1_smoke/results/smoke-summary-20260418-213131.csv)
- [smoke-summary-20260418-214404.csv](/C:/Users/NING/Desktop/v455/analysis/verification/w2_v0_v1_smoke/results/smoke-summary-20260418-214404.csv)

长窗继续满足：

- `seg2_valid_count = 281`
- `seg222_valid_count = 281`
- `has_runtime_error = 0`
- `has_late_seg2_add = 0`
- `has_v8_front_sync = 1`
- `has_v9_tail_feedback = 1`

### 4.2 指标结果

`V7` 长窗：

- `SEG 2`: `RMSE = 5.235 m`，`Bias = -4.875 m`
- `SEG 222`: `RMSE = 0.795 m`，`Bias = -0.600 m`
- `SEG 2 - SEG 222`: `RMSE = 4.604 m`，`Bias = -4.275 m`

`V8/V9` 长窗：

- `SEG 2`: `RMSE = 5.243 m`，`Bias = -4.877 m`
- `SEG 222`: `RMSE = 0.798 m`，`Bias = -0.614 m`
- `SEG 2 - SEG 222`: `RMSE = 4.602 m`，`Bias = -4.263 m`

## 5. 结论

这一步给了一个很重要的负结果：

- `V8` 和 `V9` 证明了尾段语义同步和主边界弱反馈都可以稳定落地。
- 但它们没有把双站点指标明显往前推。

这意味着：

- 问题已经不是“尾段 stage 没被看见”
- 而是“当前这种单点 stage + 弱反馈”的级别，已经不足以改变真实水面线

## 6. 对总蓝图的含义

这一步实际上强化了总蓝图里的判断：

- 小步补丁已经走到了有效上限附近
- 下一阶段不该再继续堆弱反馈
- 而应进入真正的局部 1D tailreach reach solver

也就是说，从证据上看，现在已经更接近蓝图里的：

- `Hybrid Tailreach` 真正实现阶段

而不是继续停留在：

- `front buffer + ghost-head patch`
