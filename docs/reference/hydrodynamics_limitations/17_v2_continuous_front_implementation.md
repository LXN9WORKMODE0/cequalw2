# V2 连续前沿实现记录
本页回答什么问题：在 `V0 + 保守 V1` 之后，这一版到底给 W2 增加了什么“连续前沿”能力、验证上通过了什么、以及它距离真正连续 wetting/drying 还差什么。

Updated: 2026-04-18

## 1. 这一版的定位

这一版不是完整 wetting/drying 求解器，也不是 partial-cell。

它做的是一个更保守、但逻辑完整的过渡层：

- 给受保护的库尾前沿段定义一个 `front buffer segment`
- 在 `layeraddsub` 的真实 candidate-add 路径上引入前沿状态机
- 让这个前沿段不再只是“被压住的 Add segments 请求”
- 而是变成一个有 `state / depth / wet_count / dry_count` 的连续前沿对象

所以，`V2` 的真实意义是：

把“离散的想加段事件”提升成“可跟踪的连续前沿状态”。

## 2. 新增的共享状态

本版新增了这些全局状态：

- `FRONT_SEG(JB)`
- `FRONT_STATE(JB)`
- `FRONT_WET_COUNT(JB)`
- `FRONT_DRY_COUNT(JB)`
- `FRONT_WSE(JB)`
- `FRONT_DEPTH(JB)`

以及一组保守阈值：

- `FRONT_STATE_DRY = 0`
- `FRONT_STATE_WETTING = 1`
- `FRONT_STATE_BUFFER_WET = 2`
- `FRONT_H_ON = 0.50 m`
- `FRONT_H_OFF = 0.10 m`
- `FRONT_H_MIN = 0.05 m`
- `FRONT_WET_STEPS = 3`
- `FRONT_DRY_STEPS = 6`

文件位置：

- [w2modules.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/w2modules.F90:122)
- [input.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/input.F90:314)
- [init.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/init.F90:53)

## 3. 前沿段是如何定义的

对受保护主干分支，如果：

- `CUSMIN(JB) > IUPHYS(JB)`

就定义：

- `FRONT_SEG(JB) = CUSMIN(JB) - 1`

在当前 XLD smoke case 里，主干结果就是：

- `IUPHYS = 2`
- `CUSMIN = 3`
- `FRONT_SEG = 2`

也就是说，`SEG 2` 现在第一次被正式表达成“前沿缓冲段”，而不只是“以后可能被加回来的段”。

对应初始化日志：

- `[V2_FRONT_SETUP] JB=1 FRONT_SEG=2 IUPHYS=2 CUSMIN=3`

实现位置：

- [init-geom.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/init-geom.F90:483)

## 4. 状态机挂载的位置

这次没有去碰 `w2_main.f90` 主求解顺序，也没有去碰真正的 `ADD_LAYER/SUB_LAYER` 几何更新体。

状态机只挂在真正的 protected candidate-add 共享路径上，也就是：

- 先算出 `IUCAND`
- 再用 `CUSMIN` 保护把 `IUT` 钳回
- 然后就在进入 `Add segments` 判断之前更新前沿状态

这样做的好处是：

- 逻辑位置准确
- 不会漏掉真正导致 `SEG 2` 晚激活的路径
- 又不会去碰后面一整片几何和质量守恒更新代码

核心实现位置：

- [layeraddsub.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/layeraddsub.F90:1190)

## 5. 状态机实际做了什么

在 protected front path 上：

1. 用当前活动起点 `IU` 的 `ELWS(IU)` 作为前沿代理水面。
2. 结合 `FRONT_SEG` 局部床面高程，算出 `FRONT_DEPTH`。
3. 根据：
   - `IUCAND < IU`
   - 或 `FRONT_DEPTH >= FRONT_H_ON`
   判断前沿是否在“变湿”。
4. 根据：
   - `IUCAND >= IU`
   - 且 `FRONT_DEPTH <= FRONT_H_OFF`
   判断前沿是否在“变干”。
5. 更新 `wet_count / dry_count`。
6. 把状态从：
   - `DRY`
   - 切到 `WETTING`
   - 再切到 `BUFFER_WET`

同时，这一版仍然保持：

- `SEG 2` 不进入主活动求解域
- `Add segments 2 through 2` 继续被抑制

所以它是“连续前沿表达层”，不是“完整前沿激活层”。

## 6. 新增日志

这一版新增并稳定保留了两类日志：

- `[V2_FRONT_SETUP]`
- `[V2_FRONT_STATE]`

当前扩展 smoke 窗口里的典型记录是：

- `STATE=1 DEPTH=4.640 WET_COUNT=2`
- `STATE=2 DEPTH=4.943 WET_COUNT=3`
- `STATE=2 DEPTH=5.689 WET_COUNT=4`

这说明：

- `SEG 2` 虽然还没变成活动求解段
- 但它已经不再是纯离散开关
- 而是在日志和状态上表现成一个逐步变湿的连续前沿

## 7. 验证结果

这次通过的 smoke 结果是：

- [smoke-summary-20260418-103621.csv](/C:/Users/NING/Desktop/v455/analysis/verification/w2_v0_v1_smoke/results/smoke-summary-20260418-103621.csv)
- [smoke-summary-20260418-103713.csv](/C:/Users/NING/Desktop/v455/analysis/verification/w2_v0_v1_smoke/results/smoke-summary-20260418-103713.csv)

它们都满足：

- `missing_markers` 为空
- `has_late_seg2_add = 0`
- `has_runtime_error = 0`
- `has_v2_front_state = 1`
- `has_required_outputs = 1`

也就是说，这一版同时保住了：

- V0/V1 的基础诊断
- `SEG 2` 晚激活抑制
- 无 `w2.err`
- 新的 V2 前沿状态日志

## 8. 这版的提升与上限

### 已经提升的地方

- `SEG 2` 不再只是“被压住的 candidate-add”
- 库尾前沿第一次被正式表达成连续状态对象
- 迟滞和最小湿润保护已经有了稳定框架

### 还没做到的地方

- `SEG 2` 还没有进入主水动力活动求解域
- `FRONT_DEPTH` 仍是代理深度，不是完整活动单元几何
- 还没有真正连续化 `A(h) / V(h) / R(h)`
- 还没有把前沿状态反馈进主自由液面/速度耦合

所以，这一版仍然属于：

- `连续前沿表达`

而不是：

- `连续前沿动力响应`

## 9. 对下一版的含义

`V2` 完成后，下一步最自然的方向不是再堆日志，而是进入更强的数值耦合层：

- 要么把 front buffer 的代理状态更深地接入求解
- 要么进入 `V3`，做每步内更强的水位-流量-源汇迭代

当前这版已经把“前沿对象”建立起来了，后续版本终于有东西可以耦合，而不再只是围着 `CUS` 一个整数做文章。
