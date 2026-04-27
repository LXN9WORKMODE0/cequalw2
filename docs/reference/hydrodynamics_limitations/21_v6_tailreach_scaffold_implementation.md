# V6 尾段耦合脚手架实现记录
本页回答什么问题：在 `V5` 之后，这一版到底怎样把“尾段独立动力学表达”从概念推进到代码接口、目前这个 `V6` 脚手架真实做了什么、以及它距离真正的 1D 尾段子求解器还差什么。

Updated: 2026-04-18

## 1. 这一版的定位

这次的 `V6` 不是完整的 1D Saint-Venant 尾段求解器。

它做的是更小、但真正迈进 V6 的第一步：

- 把 `tailreach <-> W2 reservoir` 的液位/流量耦合面，正式变成代码里的交换对象

也就是说，当前 `V6` 已经不再只是文档里的“以后要接 1D 子模型”，而是：

- 有了明确的上游尾段截面
- 有了明确的下游库区活动截面
- 有了耦合液位
- 有了耦合流量

所以，这一版的真实意义是：

- `hybrid coupling seam scaffold`

而不是：

- `hybrid tailreach solver`

## 2. 新增的耦合面状态

本版新增：

- `TAIL_COUPLED(JB)`
- `TAIL_UPSEG(JB)`
- `TAIL_DNSEG(JB)`
- `TAIL_WSE_UP(JB)`
- `TAIL_WSE_DN(JB)`
- `TAIL_Q_LINK(JB)`

定义位置：

- [w2modules.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/w2modules.F90:122)
- [input.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/input.F90:314)
- [init.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/init.F90:53)

## 3. 当前耦合面是如何定义的

在当前 front-buffer 语义下，如果：

- `UPSTREAM_DOMAIN_LOCK(JB) = TRUE`
- 且 `FRONT_SEG(JB) > 0`

则定义一条最小 hydraulic-only coupling seam：

- `TAIL_UPSEG = FRONT_SEG`
- `TAIL_DNSEG = CUSMIN`

对当前主干来说，就是：

- `UPSEG = 2`
- `DNSEG = 3`

这和我们一直在讨论的物理图景是一致的：

- `SEG 2` 是尾段/库尾前沿侧
- `SEG 3` 是当前 W2 主活动求解域的最上游活动段

## 4. 当前 V6 真正输出了什么

在主水动力解之后，当前版本会更新：

- `TAIL_WSE_UP = FRONT_WSE`
- `TAIL_WSE_DN = ELWS(TAIL_DNSEG)`
- `TAIL_Q_LINK = QC(TAIL_DNSEG)`

也就是说，它现在已经能在每个时间步给出一个稳定的 coupling state：

- 尾段侧水位
- 库区侧水位
- 跨界交换流量

这正是未来 1D 尾段子求解器真正要吃进去/吐出来的第一批变量。

## 5. 新增日志

这版新增：

- `[V6_COUPLING]`

当前 smoke 窗口里已经能看到类似记录：

- `UPSEG=2 DNSEG=3 WSE_UP=580.149 WSE_DN=580.346 QLINK=3857.560`

这说明：

- coupling seam 已经从“抽象概念”变成了可观测、可验证的代码对象

## 6. 验证结果

通过的 smoke 结果：

- [smoke-summary-20260418-160712.csv](/C:/Users/NING/Desktop/v455/analysis/verification/w2_v0_v1_smoke/results/smoke-summary-20260418-160712.csv)
- [smoke-summary-20260418-160803.csv](/C:/Users/NING/Desktop/v455/analysis/verification/w2_v0_v1_smoke/results/smoke-summary-20260418-160803.csv)

两组都满足：

- `missing_markers` 为空
- `has_late_seg2_add = 0`
- `has_runtime_error = 0`
- `has_v2_front_state = 1`
- `has_v3_inner_iter = 1`
- `has_v4_front_geom = 1`
- `has_v5_transition = 1`
- `has_v6_coupling = 1`

也就是说，这一版 `V6` 脚手架在不破坏 `V0-V5` 的前提下，已经把混合尾段求解器最关键的接口面立起来了。

## 7. 这版已经做到什么

### 已经做到的

- 未来 1D 尾段子模型需要的最小 hydraulic-only interface 已经存在
- 交换面不再隐含在 `CUS/front buffer` 语义里，而是显式变量
- `WSE/Q` 这两个最关键交换量已经稳定可输出

### 还没有做到的

- 没有 1D 尾段内部网格
- 没有 Saint-Venant 动量/连续方程
- 没有尾段内部摩阻传播
- 没有把尾段回算结果反馈回 W2 边界

所以，这一版属于：

- `tailreach coupling scaffold`

而不是：

- `hybrid tailreach simulation`

## 8. 到这里意味着什么

从 `V0` 到 `V6` 现在已经形成了完整的演进链：

- `V0`: 诊断
- `V1`: 物理头段/活动边界语义分离
- `V2`: 连续前沿状态
- `V3`: 第二次源汇刷新与步内诊断
- `V4`: 连续代理几何
- `V5`: 局部状态相关底摩阻闭合
- `V6`: 尾段混合求解接口脚手架

也就是说，当前已经把“纯 W2 内部渐进增强”的路径，完整推进到了“可以真正接一个独立尾段子模型”的入口处。

下一步如果还要继续往前走，就不再是小步补丁，而是：

- 真正开始实现局部 1D 尾段子求解器
- 并把它通过 `TAIL_UPSEG/TAIL_DNSEG/WSE/Q` 这条 seam 接回 W2

这已经是一个新的阶段了。 
