# V13 Transition-State Reach 实现记录
本页回答什么问题：`V13` 如何把河流态-过渡态-库区态的控制状态从外挂 front-state 逻辑转移到 tailreach 内部，以及这一步对结果和架构分别带来了什么影响。

Updated: 2026-04-20

## 1. 这版的定位

`V12` 之后，tailreach 已经具备：

- 固定尾段物理域
- 带时间记忆的 `QSTATE`

但“过渡状态”仍然主要挂在 reach 外部：

- `FRONT_STATE`
- `FRONT_TRANSITION`

虽然 `V8` 以后这些量已经能同步部分 tailreach 信息，但它们还不是由 tailreach 内部直接主导。

`V13` 的目标就是：

- 让 tailreach 自己计算当前更偏向河流控制、过渡回水还是淹没库区
- 再把这个内部状态同步给现有 closure

换句话说：

- `FRONT_STATE` 继续保留作为加减段语义
- 但不再承担主要物理过渡状态来源

## 2. 新增的内部状态量

新增了：

- `TAIL_TRANSITION_STATE`
- `TAIL_SUBMERGENCE`
- `TAIL_LOCAL_SLOPE`
- `TAIL_FROUDE`
- `TAIL_CONTROL_MODE`

位置：

- [w2modules.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/w2modules.F90:140)
- [input.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/input.F90:318)
- [init.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/init.F90:60)
- [init-geom.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/init-geom.F90:506)

## 3. 新的过渡状态逻辑

在 [w2_main.f90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/w2_main.f90:1765) 中新增了：

- `UPDATE_TAIL_TRANSITION_STATE`

它基于以下量构造内部过渡状态：

1. **局部坡降**
   - `TAIL_LOCAL_SLOPE = (WSE_UP - WSE_DN) / LENGTH`

2. **submergence**
   - 用下游水深相对上游水深的比例近似

3. **Froude-like 行为**
   - 用 `QSTATE / area / sqrt(g * depth)` 近似

然后把这些量组合成一个连续控制变量：

- `TAIL_TRANSITION_STATE`

取值范围为 `0..1`：

- 接近 `0`：更偏河流控制
- 接近 `1`：更偏库区/淹没控制

同时为了日志和调试，派生出：

- `TAIL_CONTROL_MODE`

其中：

- `0 = river`
- `1 = transition`
- `2 = reservoir`

## 4. 与旧 front-state 路径的关系

这一步最关键的改动不在 `w2_main.f90`，而在 [layeraddsub.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/layeraddsub.F90:608)：

以前：

- `FRONT_TRANSITION` 主要由 `FRONT_STATE` 离散映射得出

现在：

- 如果 tailreach 有效，则 `FRONT_TRANSITION = TAIL_TRANSITION_STATE`
- 旧的 `FRONT_STATE -> FRONT_TRANSITION` 逻辑只作为 fallback

所以 `V13` 的核心变化是：

- front-state 还在
- 但 front-transition 的物理来源已经转到 reach 内部

## 5. 新增诊断

新增 marker：

- `[V13_TRANSITION_REACH]`

内容包括：

- `TRANS`
- `SLOPE`
- `SUB`
- `FR`
- `MODE`

对应 smoke harness 已提升为硬要求：

- [run_w2_v0_v1_smoke.py](/C:/Users/NING/Desktop/v455/analysis/run_w2_v0_v1_smoke.py:1)

## 6. smoke 验证

通过结果：

- 短窗：[smoke-summary-20260420-181734.csv](/C:/Users/NING/Desktop/v455/analysis/verification/w2_v0_v1_smoke/results/smoke-summary-20260420-181734.csv)
- 延长窗：[smoke-summary-20260420-181834.csv](/C:/Users/NING/Desktop/v455/analysis/verification/w2_v0_v1_smoke/results/smoke-summary-20260420-181834.csv)
- 长窗：[smoke-summary-20260420-182703.csv](/C:/Users/NING/Desktop/v455/analysis/verification/w2_v0_v1_smoke/results/smoke-summary-20260420-182703.csv)

三组都满足：

- `has_v13_transition_reach = 1`
- `has_runtime_error = 0`
- `seg2_valid_count > 0`
- `seg222_valid_count > 0`

## 7. 长窗结果

长窗 `44430-44458`：

- `SEG 2 RMSE = 5.005`
- `SEG 2 Bias = -4.464`
- `SEG 222 RMSE = 0.797`
- `SEG 222 Bias = -0.612`
- `SEG 2 - SEG 222 RMSE = 4.324`
- `SEG 2 - SEG 222 Bias = -3.853`

和 `V12` 相比，差异很小：

- `SEG 2` 基本同级
- `SEG 222` 基本同级
- `DIFF` 也基本同级

这说明：

- `V13` 对当前数值结果不是一次大跳变
- 但它把过渡状态的物理来源真正搬进了 reach 内部

## 8. transition-state 本身的行为

从日志看：

- `TAIL_TRANSITION_STATE` 大致在 `0.45 ~ 0.945`
- `TAIL_CONTROL_MODE` 出现了 `1` 和 `2`
- 没有出现大量 `0`

这说明对当前长窗工况来说，tailreach 大部分时间被识别为：

- 过渡态
- 或偏库区态

这和你这个时段本身的回水背景是相符的。

## 9. 这版真正的意义

`V13` 的意义主要是架构性的，而不是指标性的：

### 架构上

- 过渡状态已经从外挂 front patch 转入 tailreach 内部
- 现在可以说 tailreach 已经同时拥有：
  - fixed domain
  - discharge state
  - internal transition state

### 指标上

- 指标没有明显跃迁
- 但也没有因为状态内化而恶化

所以这是一个典型的“为下一步铺路”的版本。

## 10. 对 V14 的含义

现在 tailreach 内部已经具备三层东西：

1. 固定物理域
2. discharge state
3. internal transition state

这意味着下一步 `V14` 可以更合理地去做：

- stronger coupled hybrid

也就是：

- 不再只是弱耦合地把 tailreach 的结果喂给主库区
- 而是更系统地推进 reach 与主库区的强耦合顺序
