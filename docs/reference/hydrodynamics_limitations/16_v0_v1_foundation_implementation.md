# V0/V1 基础实现记录
本页回答什么问题：`15_w2_hydrodynamic_upgrade_blueprint.md` 里的第一版基础升级，实际在源码里落成了什么、验证通过了什么、还没有解决什么。

Updated: 2026-04-18

## 1. 本次实现的真正目标

这次没有直接去做完整的连续 wetting/drying，也没有把库尾物理河段直接并入主水动力求解域。

本次实现只完成了两件基础工作：

1. `V0`：把库尾相关的边界/活动段诊断链打通。
2. `V1`：把“物理上游头段”和“活动求解上游起点”这两个概念正式拆开，并给主干分支加上一个保守的“活动起点上限”。

这一版的设计原则是：

- 不破坏当前求解器稳定性。
- 不让 `CUS` 再无约束地向上游推进到物理库尾头段。
- 先把语义和验证工具立起来，再进入下一版的连续前沿改造。

## 2. 实现后的语义

本次新增了三组关键状态量：

- `IUPHYS(JB)`：物理上游头段，当前初始化为 `US(JB)`。
- `CUSMIN(JB)`：该分支在本版里允许的最上游活动求解起点。
- `UPSTREAM_DOMAIN_LOCK(JB)`：是否对该分支启用主干保护。

当前保护策略是保守的：

- 只对“主干分支且存在上游来流/坝前来流”的分支启用保护。
- `CUSMIN(JB)` 取初始化阶段原始求解逻辑算出来的活动起点。
- 后续运行中，如果某次 layer/segment 更新想把 `CUS(JB)` 推到更上游，就把它钳回 `CUSMIN(JB)`。

这意味着：

- `IUPHYS` 已经把“物理库尾头段”记录下来了。
- `CUS` 仍然保留为“活动求解起点”。
- 当前版本并没有声称“库尾物理段已经被完整参与水动力求解”。
- 当前版本做的是：先阻止活动起点在涨水过程中继续向上游吃掉物理库尾头段。

## 3. 实际改动的文件

源码：

- [w2modules.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/w2modules.F90:122)
- [input.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/input.F90:314)
- [init.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/init.F90:53)
- [init-geom.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/init-geom.F90:461)
- [hydroinout.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/hydroinout.F90:23)
- [layeraddsub.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/layeraddsub.F90:19)

验证：

- [run_w2_v0_v1_smoke.py](/C:/Users/NING/Desktop/v455/analysis/run_w2_v0_v1_smoke.py:1)
- [2026-04-18-w2-hydro-v0-v1-foundation.md](/C:/Users/NING/Desktop/v455/docs/superpowers/plans/2026-04-18-w2-hydro-v0-v1-foundation.md:1)

## 4. 新增诊断标记

这版会在 `w2.wrn` 写出以下标记：

- `[V0_BOUNDARY_INIT]`
- `[V0_BOUNDARY_SHIFT]`
- `[V0_SOURCE_PLACE]`
- `[V0_SEGMENT_ADD_CHECK]`

其中最重要的解释是：

- `IUPHYS`：物理上游头段
- `CUS`：当前活动求解起点
- `CUSMIN`：本版允许的最上游活动求解起点

这让我们第一次能够明确区分：

- “物理库尾头段在哪里”
- “求解器现在从哪里开始算”
- “某次涨水想把活动起点往上推时，被拦在了哪里”

## 5. 验证结果

短窗 smoke test 已固定在：

- `TMSTRT = 44430`
- `TMEND = 44435.4`
- 延长验证再跑到 `TMEND = 44436.5`

通过的结果文件：

- [smoke-summary-20260418-005512.csv](/C:/Users/NING/Desktop/v455/analysis/verification/w2_v0_v1_smoke/results/smoke-summary-20260418-005512.csv)
- [smoke-summary-20260418-005559.csv](/C:/Users/NING/Desktop/v455/analysis/verification/w2_v0_v1_smoke/results/smoke-summary-20260418-005559.csv)

通过标准是：

- 新诊断标记存在。
- 不再出现 `Add segments 2 through 2`。
- 不产生 `w2.err`。
- `model.log` 能持续推进到短窗终点。

当前版本满足了这些条件。

## 6. 调试中确认过的关键事实

这次实现过程中有两条很重要的经验，后续必须继承：

1. 不能把 `CUS` 直接钳到 `IUPHYS`。
   这样会把活动求解起点直接推到物理库尾头段，导致初始化后立刻出现自由液面不稳定。

2. “活动起点保护”必须覆盖真正触发 `Add segments` 的那条 `layeraddsub` 路径。
   只在部分分支逻辑里钳制 `IUT` 是不够的，真正触发晚激活的路径如果没被拦住，`SEG 2` 还是会在涨水时被重新加回活动域。

## 7. 这版还没有解决什么

这版并没有解决以下更难的问题：

- `SEG 2` 在物理上始终有水，但当前版本仍没有让它完整参与主水动力求解。
- `SEG 2 - SEG 222` 的真实天然水面线还没有被重建。
- 物理库尾段的连续 wetting/drying 还没做。
- “河流态 -> 回水态 -> 淹没态”的连续过渡还没做。

所以，这一版是“稳定的语义基础版”，不是“库尾水动力最终版”。

## 8. 下一步

下一步应该进入 `V2`，重点不再是继续硬改 `CUS`，而是：

- 给 `IUPHYS:CUS-1` 这段物理库尾缓冲带建立连续湿润表达。
- 让物理库尾段可以存在，但不强迫它立刻成为完整活动求解起点。
- 逐步把“物理存在”和“活动求解”的差距缩小到连续前沿，而不是离散开关。
