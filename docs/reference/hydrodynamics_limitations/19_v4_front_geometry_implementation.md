# V4 前沿代理几何实现记录
本页回答什么问题：在 `V3` 稳定下来以后，这一版到底给 front buffer 增加了哪些连续几何量、这些几何量目前起什么作用、以及它们还没有真正反馈进主水动力矩阵的边界在哪里。

Updated: 2026-04-18

## 1. 这一版的定位

这次的 `V4` 没有去改全库的主几何表示，也没有把 CE-QUAL-W2 的整个断面离散直接改成真正的 partial-cell。

这一版只做一件更保守但更稳的事：

- 给 `V2` 已经建立起来的 front buffer，增加连续代理几何

也就是说，现在 front buffer 不再只有：

- `STATE`
- `DEPTH`

还会连续维护：

- `AREA`
- `VOLUME`
- `HRAD`

这让它从“连续前沿状态对象”，进一步变成“连续前沿几何对象”。

## 2. 新增的几何量

本版新增：

- `FRONT_AREA(JB)`
- `FRONT_VOLUME(JB)`
- `FRONT_HRAD(JB)`

定义位置：

- [w2modules.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/w2modules.F90:122)
- [input.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/input.F90:314)
- [init.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/init.F90:53)

初始化时这些量都置零，随后在 protected front candidate-add 路径上与 `FRONT_DEPTH` 同步更新。

## 3. 当前的代理几何定义

对 `FRONT_SEG(JB)`，当前使用的保守代理定义是：

- `FRONT_AREA = width * FRONT_DEPTH`
- `FRONT_VOLUME = FRONT_AREA * DLX`
- `FRONT_HRAD = FRONT_AREA / (width + 2 * FRONT_DEPTH)`

其中：

- `width` 取当前 front segment 顶层有效宽度的保守近似
- `DLX` 取该 segment 的长度

所以这仍然是“front buffer 的连续代理几何”，不是“完整断面真实 partial-cell 积分几何”。

但它已经把最关键的 3 个连续量补上了：

- 面积
- 体积
- 水力半径

## 4. 日志与当前表现

这版新增了：

- `[V4_FRONT_GEOM]`

在当前 smoke 窗口里，可以看到类似记录：

- `AREA=281.602`
- `VOLUME=188673.064`
- `HRAD=4.045`

配合已有的：

- `[V2_FRONT_STATE]`

现在 front buffer 的信息已经从“状态”扩展到“状态 + 连续几何”。

## 5. 验证结果

这次通过的 smoke 结果是：

- [smoke-summary-20260418-153431.csv](/C:/Users/NING/Desktop/v455/analysis/verification/w2_v0_v1_smoke/results/smoke-summary-20260418-153431.csv)
- [smoke-summary-20260418-153527.csv](/C:/Users/NING/Desktop/v455/analysis/verification/w2_v0_v1_smoke/results/smoke-summary-20260418-153527.csv)

两组结果都满足：

- `missing_markers` 为空
- `has_late_seg2_add = 0`
- `has_runtime_error = 0`
- `has_v2_front_state = 1`
- `has_v3_inner_iter = 1`
- `has_v4_front_geom = 1`

也就是说，这一版没有破坏 `V0-V3` 的基础行为，同时把 front geometry 的连续量稳定接进来了。

## 6. 这版已经做到什么

### 已经做到的

- `SEG 2` 作为 front buffer 已经有连续几何量
- `AREA/VOLUME/HRAD` 会跟着 `FRONT_DEPTH` 连续变化
- `w2.wrn` 里已经能把前沿状态和前沿几何一起看出来

### 还没有做到的

- 这些几何量还没有反馈进主水面方程
- 还没有反馈进摩阻闭合
- 还没有反馈进质量守恒矩阵
- 还没有把 main branch 的真实活动单元几何改成 partial-cell

所以，这一版仍然属于：

- `front-buffer geometry representation`

而不是：

- `partial-cell hydrodynamic geometry solver`

## 7. 对下一步的意义

到这一版为止，front buffer 已经具备了三层信息：

1. `V2`：连续前沿状态
2. `V3`：更新水位后的第二次源汇刷新
3. `V4`：连续前沿几何

这意味着下一步如果继续往前走，真正值得做的就不再是继续堆状态量，而是把这些量更深地反馈进主方程，例如：

- 用 `FRONT_AREA / FRONT_VOLUME / FRONT_HRAD` 影响摩阻或局部几何响应
- 或者进入更强的 `V5` 状态相关闭合

从现在开始，后续每前进一步都应该更接近“把 front buffer 真正接入动力学”，而不是继续只做观察层和代理层。 
