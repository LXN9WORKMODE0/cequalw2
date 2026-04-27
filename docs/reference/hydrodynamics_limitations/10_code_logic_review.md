# W2 水动力代码逻辑审查
本页回答什么问题：针对当前中间水库 case，CE-QUAL-W2 的源码里哪些具体逻辑会导致 `SEG 2` 晚激活、`SEG 2-SEG 222` 坡降塌缩，以及为什么这些问题不能简单归咎为输入流量不完整。
Updated: 2026-04-16

## Findings

### 1. `SEG 2` 被当成“当前无活动层的段”从主求解域里裁掉，这是本 case 最核心的结构性问题

- 在初始化几何阶段，代码先检查每个段当前是否还有活动层；若 `KBi(I) < KT`，就把 `KB(I)` 压到 `KT`，随后再依据 `KB(I)-KT < NL(JB)-1` 更新 `IUT`，并把 `CUS(JB)` 直接改成 `IUT`。[init-geom.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/init-geom.F90:466) [init-geom.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/init-geom.F90:470) [init-geom.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/init-geom.F90:476) [init-geom.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/init-geom.F90:484)
- 你的主支 `BR1` 在控制文件里 `US=2, DS=222, NL=1`，因此这里不是“要求多层才算活跃”，而是更直接地把“当前没有活动层”的上游段从计算域里裁掉。[w2_con.csv](/C:/Users/NING/Desktop/v455/实际案例/w2_con.csv:47)
- 运行过程中，`layeraddsub.F90` 继续沿用这套机制动态加减段，并反复重设 `CUS(JB)`。[layeraddsub.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/layeraddsub.F90:53) [layeraddsub.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/layeraddsub.F90:60) [layeraddsub.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/layeraddsub.F90:1024)
- 实际 case 的日志明确表明 `SEG 2` 直到 `JDAY 44435.183` 才被重新加入；无 distributed 且支流放大的 `Q200` case 也只是把这个时刻提前到了 `44434.256`，并没有让 `SEG 2` 从一开始就始终参与演化。[w2.wrn](/C:/Users/NING/Desktop/v455/实际案例/w2.wrn:4) [w2.wrn](/C:/Users/NING/Desktop/v455/analysis/structural_minimal/cases/Q200/w2.wrn:4)
- 对这个 case 来说，这意味着 W2 并没有持续求解“始终有水的库尾天然河流段”，而是在求解一个会被干化/激活机制裁切的上游过渡段。只要这一点不变，自然水面线就很难稳定再现。

### 2. 一旦 `CUS` 下移，上游边界和来水位置也随之下移，物理上的库尾河流段会在计算上直接消失

- 初始化水位时，`initial_water_level` 从 `IU = CUS(JB)` 开始，并在 `I == IU` 时把上游来水 `QIN(JB)` 加到 `QSSI(I)`；也就是说，初始化的正常水深和水面线估算本身就是从当前 `CUS` 而不是固定的 `US` 开始的。[init-u-elws.f90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/init-u-elws.f90:26) [init-u-elws.f90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/init-u-elws.f90:29)
- 主求解时，水面方程的上游流量项也是直接作用在 `D(IU)` 上；上游 ghost cell 的自由液面和边界速度也都绑定在当前 `IU` 上。[w2_main.f90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/w2_main.f90:903) [w2_main.f90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/w2_main.f90:966) [w2_main.f90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/w2_main.f90:1216)
- 支流位置也受同样约束。对于普通 tributary inflow，代码用 `I = MAX(ITR(JT), IU)` 来确定入流放置段；如果某个支流名义上落在 `CUS` 上游，它会被整体推到 `CUS` 处再注入 `QSS`。[hydroinout.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/hydroinout.F90:858) [hydroinout.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/hydroinout.F90:931)
- 这条逻辑解释了为什么“把总量补回来”可以改善整体水位量级，却仍修不好天然水面线：因为当 `CUS` 已经下移时，物理上应存在于 `SEG 2` 的那段河流边界，在数值上已经被整体下推了。

### 3. `distributed` 在代码里就是面源式表层补偿，只能修 storage/common-mode，不能修河流态水面线

- 初始化阶段，distributed 只是均匀分摊到当前活动河段，用于估算初始流量和 Manning 正常水深。[init-u-elws.f90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/init-u-elws.f90:51)
- 运行阶段，它被明确实现为按表层面积 `BI(KT,I)*DLX(I)` 分配到顶层 `QSS(KT,I)` 的源项。[hydroinout.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/hydroinout.F90:942) [hydroinout.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/hydroinout.F90:943)
- 手册也把 distributed tributary 定义成“equivalent to a non-point source loading”，并明确说明它是按各段表面积分配、用于 accounting for ungaged flows for the water budget。[W2manual455_Part3_InputOutputFiles_rev0.pdf](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/User%20Manual/W2manual455_Part3_InputOutputFiles_rev0.pdf)
- 所以，对这个 case 而言，用 distributed 去贴坝前水位是可以理解的工程补偿，但从源码和手册定义上，它都不是一个能够恢复天然河流态纵向坡降的机制。

### 4. 水面、纵向速度和垂向速度是分裂推进的，连续性修正发生在水面解之后，这会放大“总量对了但水面线不对”的风险

- 主循环里，`Task 2.2.3` 先解自由液面，`Task 2.2.4` 再解纵向速度，`Task 2.2.5` 最后再由连续方程诊断垂向速度。[w2_main.f90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/w2_main.f90:843) [w2_main.f90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/w2_main.f90:1129) [w2_main.f90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/w2_main.f90:1335)
- 速度场不是和自由液面一次联立收敛，而是在水面解完后，再按 `QC(I)` 与 `Q(I)` 的差额做连续性修正：`U = U + (QC-Q)/BHRSUM`。[w2_main.f90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/w2_main.f90:1317) [w2_main.f90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/w2_main.f90:1323)
- 垂向速度 `W` 也不是独立动量变量，而是事后由连续方程诊断出来。[w2_main.f90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/w2_main.f90:1342)
- Part 2 Theory 手册也明确说明模型采用 hydrostatic 假设，并指出“vertical velocities are very small”，不求解完整的垂向加速度过程；同时初始水位和速度用 Manning normal depth 估算。[W2manual455_Part2_Theory_rev0.pdf](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/User%20Manual/W2manual455_Part2_Theory_rev0.pdf)
- 对这个 case 的含义是：模型可以把总体量级和连续性做顺，但并不保证 `SEG 2-SEG 222` 这种强过渡段的天然水面坡降会自然保持正确。这和我们最小实验集里“`common-mode` 可以改善、`differential-mode` 依然很差”的结果是吻合的。[09_structural_minimal_test_set.md](/C:/Users/NING/Desktop/v455/docs/reference/hydrodynamics_limitations/09_structural_minimal_test_set.md:1)

## Open Questions

- 目前最需要继续细查的是：你这个库尾 `SEG 2` 在物理上始终有水，但为什么当前几何和层高组合会让它在数值上频繁落到“无活动层”状态。
- 这更可能是“活动段干湿阈值与网格/层高组合不适配”的问题，而不是简单的糙率过小或支流总量过少。
- 如果后续继续做源码级改造，最应该优先盯的不是 distributed，而是 `init-geom.F90`/`layeraddsub.F90` 的活动段机制，以及主循环中自由液面和速度的分裂推进。

## Related Files

- 对话发现记录：[08_conversation_findings_log.md](/C:/Users/NING/Desktop/v455/docs/reference/hydrodynamics_limitations/08_conversation_findings_log.md:1)
- 结构性最小实验集：[09_structural_minimal_test_set.md](/C:/Users/NING/Desktop/v455/docs/reference/hydrodynamics_limitations/09_structural_minimal_test_set.md:1)
- 双站点水面线复核：[dual_station_review.md](/C:/Users/NING/Desktop/v455/analysis/xld_multifactor/dual_station_review/dual_station_review.md:1)
