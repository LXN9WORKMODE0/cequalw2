# V5 状态相关闭合实现记录
本页回答什么问题：在 `V4` 前沿代理几何之后，这一版到底怎样把 front buffer 的状态/几何轻量反馈进局部动力闭合、实际改了哪些力学项、以及为什么这一步仍然是保守版本。

Updated: 2026-04-18

## 1. 这一版的定位

这次的 `V5` 没有把 front buffer 的状态和几何全面反馈进主动量方程。

我把它收成了一个最保守、最稳的版本：

- 根据 front state 生成 `transition`、`drag factor`、`grav factor`
- 但**真正反馈进求解器的只有局部底摩阻闭合**
- `GRAV` 目前只记录为诊断因子，没有直接写回主求解

这样做的理由很简单：

- 从前面几版的稳定性来看，直接碰 `GRAV/ADMX/ADMZ/DM/AZ` 的风险太高
- 当前最安全的第一步，是先让 front buffer 影响“第一个活动段”的局部底摩阻

所以这一版的真实意义是：

- `state-dependent local drag closure`

而不是：

- `full transition-aware hydrodynamic closure`

## 2. 新增的状态相关因子

本版新增：

- `FRONT_TRANSITION(JB)`
- `FRONT_DRAG_FACTOR(JB)`
- `FRONT_GRAV_FACTOR(JB)`

定义位置：

- [w2modules.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/w2modules.F90:122)
- [input.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/input.F90:314)
- [init.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/init.F90:53)

## 3. 因子的定义方式

当前采用的是保守的状态映射：

- `DRY -> TRANSITION = 0.0`
- `WETTING -> TRANSITION = 0.5`
- `BUFFER_WET -> TRANSITION = 1.0`

然后派生出：

- `FRONT_DRAG_FACTOR = 1.0 + 0.20 * TRANSITION`
- `FRONT_GRAV_FACTOR = 1.0 - 0.40 * TRANSITION`

并做范围约束：

- `DRAG` 限制在 `[1.0, 1.2]`
- `GRAV` 限制在 `[0.6, 1.0]`

也就是说，当 front buffer 更接近库区淹没态时：

- 局部阻力更强
- 坡降驱动倾向更弱

## 4. 当前真正反馈进了哪里

这版**真正反馈进求解器**的只有一处：

- [w2_main.f90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/w2_main.f90:744)

更具体地说，是在底摩阻系数 `GC2` 计算完之后，对受保护主干的第一个活动段 `I == IU` 做：

- `GC2 = GC2 * FRONT_DRAG_FACTOR(JB)`

这意味着：

- 只有紧邻 front buffer 的第一个活动段会受到状态相关闭合影响
- 影响的是底摩阻项
- 不碰 wind shear 单独项
- 不碰全库 ADMX/ADMZ/DM/AZ

这也正是这版能稳定通过 smoke 的主要原因：影响面非常小。

## 5. 这版没有真正反馈的地方

虽然本版计算了：

- `FRONT_GRAV_FACTOR`

但它目前仍是诊断量，还没有直接乘到：

- `GRAV`
- `ADMX`
- `ADMZ`
- `DM`
- `AZ`

原因是当前阶段更重要的是先确认：

- 状态相关闭合在局部底摩阻上是稳定可行的

而不是一步跨到全套状态相关动力闭合。

## 6. 新增日志

这版新增并稳定保留：

- `[V5_TRANSITION]`

当前 smoke 窗口里已经能看到典型记录：

- `TRANS=.500 DRAG=1.100 GRAV=.800`
- `TRANS=1.000 DRAG=1.200 GRAV=.600`

这说明：

- front state 的确在驱动状态相关因子变化
- 因子不是死常数
- 并且它们和 `V2_FRONT_STATE`、`V4_FRONT_GEOM` 是同步出现的

## 7. 验证结果

通过的 smoke 结果：

- [smoke-summary-20260418-155740.csv](/C:/Users/NING/Desktop/v455/analysis/verification/w2_v0_v1_smoke/results/smoke-summary-20260418-155740.csv)
- [smoke-summary-20260418-155826.csv](/C:/Users/NING/Desktop/v455/analysis/verification/w2_v0_v1_smoke/results/smoke-summary-20260418-155826.csv)

两组都满足：

- `missing_markers` 为空
- `has_late_seg2_add = 0`
- `has_runtime_error = 0`
- `has_v2_front_state = 1`
- `has_v3_inner_iter = 1`
- `has_v4_front_geom = 1`
- `has_v5_transition = 1`

也就是说，`V5` 已经在不破坏 `V0-V4` 的前提下，真正把状态相关闭合接进来了。

## 8. 这一版的提升与边界

### 已经提升的地方

- front buffer 不再只是状态对象和几何对象
- 它已经开始对局部动力闭合产生真实影响
- 这种影响是状态相关的，而不是固定参数

### 还没做到的地方

- 还没有形成 branch-wide 状态相关闭合
- 还没有把 `GRAV` 真正按状态缩放写回主求解
- 还没有把 `FRONT_AREA / FRONT_VOLUME / FRONT_HRAD` 更深地接入动量和连续方程

所以，这一版属于：

- `local transition-aware closure`

而不是：

- `fully transition-aware hydrodynamic closure`

## 9. 对下一步的含义

走到这一步以后，蓝图里的下一个大方向已经比较明确了：

- 如果继续沿 W2 内部推进，就该进入更重的结构改造
- 那个方向其实已经接近蓝图里的 `V6`

因为从现在开始，再往前每一步都会越来越接近：

- 局部 1D 尾段/回水子求解器
- 或者 front buffer 真正进入主动力方程

也就是说，`V5` 基本已经把“纯 W2 内部渐进增强”的保守路径走到边界了。  
再往前，就开始进入“承认尾段需要独立动力学表达”的阶段。 
