# CE-QUAL-W2 对话发现记录
本页回答什么问题：到目前为止，这个专题在对话中已经确认了哪些发现，哪些结论已经被修正，哪些判断可以作为后续实验和源码改造的固定前提。
Updated: 2026-04-16

## 1. 这页怎么用

- 这页不是正式综述，也不是最终定论清单。
- 它的作用是把对话中已经形成的高价值发现按“已确认事实 / 机制判断 / 已被修正的旧判断 / 后续工作含义”保存下来。
- 后续如果继续改 case、改参数或改源码，应优先检查新结果是否推翻了这里的哪一条。

## 2. 已确认的 case 事实

- 当前研究对象是四库串联背景中的中间一个水库，但专题主对象始终是这个单库本身，不把整个四库网络作为当前主求解对象。
- `SEG 222` 是坝前观测位置，对应 [el_obs2021.npt](/C:/Users/NING/Desktop/v455/实际案例/el_obs2021.npt:1)。
- `SEG 2` 是上游大坝下的第一个断面，也就是库尾过渡段的最上游控制位置，对应 [el_obs_upstream.npt](/C:/Users/NING/Desktop/v455/实际案例/el_obs_upstream.npt:1)。
- 你已经明确指出：`SEG 2` 在物理上应始终有水，不能把它理解成“天然可以干掉的可有可无段”。
- 当前 case 中的 `distributed` 不是物理测得入流，而是基于先跑一遍模型后，再用水量平衡反推出来的补偿项，主要目的是修正坝前水位和总量闭合。

## 3. 对 W2 主水动力的已确认判断

- CE-QUAL-W2 的主水动力更接近“laterally averaged + hydrostatic + implicit free surface + post-corrected velocity”的框架，而不是全耦合的强非恒定动波网络解法。
- 它能做回水，但更擅长细长库区、河道型水库和缓变回水，不擅长频繁在“快流河道态”和“淹没库区态”之间切换的过渡段。
- 在主循环里，自由液面、水面几何、纵向速度和最终连续性修正并不是一次联立解到底，而是分步推进后再通过 `QC` 修正流量一致性。[w2_main.f90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/w2_main.f90:907) [w2_main.f90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/w2_main.f90:1300)
- 垂向速度 `W` 是由连续方程诊断出来的，不是单独求解的垂向动量变量。[w2_main.f90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/w2_main.f90:1338)
- 这套结构决定了：模型对边界切换、回水末端推进、层调整和上游浅水段活动状态都更敏感。

## 4. 关于 distributed 的已确认发现

- `distributed` 的工程意义更接近“总量补偿和局部表层水位补偿”，不能直接等价于“更真实的天然水面线”。
- 初始化阶段，distributed 先被平均分摊到活动河段，用来估算正常水深和初始水位。[init-u-elws.f90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/init-u-elws.f90:51)
- 运行阶段，distributed 是按活动河段的表层面积 `BI(KT,I)*DLX(I)` 分配到顶层 `QSS(KT,I)`，因此本质上是顶层面源补给，而不是沿真实支流位置、真实入流层位和真实纵向动量进入系统。[hydroinout.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/hydroinout.F90:936)
- 因而，distributed 能修坝前水位，不代表它修对了库尾回水传播，更不代表它修对了 `SEG 2` 到 `SEG 222` 的天然坡降。

## 5. 单站点判断后来被修正的地方

- 早期只用坝前 `SEG 222` 去评价时，很容易得出“某些 distributed case 很优”的印象。
- 这个判断后来被明确修正：坝前贴合只能说明局部水位或整体库容量级更接近，不能替代对真实水面线的评价。
- 后续所有关于“模型是否合理”的判断，都必须至少同时看 `SEG 2`、`SEG 222` 和两点水面差，而不能再只看坝前一个点。

## 6. 双站点约束下的新发现

- 实测两点水面差并不小：`2021-08-22` 为 `14.62 m`，`2021-09-05` 为 `8.53 m`，`2021-09-10` 仍有 `7.83 m`。这说明真实工况不是快速平库，而是持续存在明显纵向水面坡降。[dual_station_review.md](/C:/Users/NING/Desktop/v455/analysis/xld_multifactor/dual_station_review/dual_station_review.md:1)
- 当前 baseline `B0` 直到 `2021-08-27 04:48` 才让 `SEG 2` 成为有效连续水面；这比物理认识晚得多。
- `D1/D7` 这类 distributed 方案可以把坝前 `SEG 222` 的 RMSE 压低到约 `0.145 m`，但 `SEG 2` 的有效 RMSE 仍在 `4.6 m` 左右，而且 `2021-09-10` 的模拟两点差只有约 `1.3 m`，远低于实测 `7.83 m`。
- `G6` 这类糙率/面积方案能把两点差做大一些，但会让坝前整体水位严重失真。
- 目前已跑 case 中，没有任何一个可以同时把坝前、库尾和两点水面差三个目标一起做好。

## 7. 误差应当拆成两类

- 双站点下，误差至少应拆成两个部分：
- `common-mode` 偏差：两站一起偏高或偏低，更像总量、蓄量、边界来水或高程基准问题。
- `differential-mode` 偏差：`SEG 2 - SEG 222` 的水面差偏差，更像天然水面线、回水传播、摩阻和纵向动量平衡问题。
- 目前的发现很清楚：distributed 更偏向改善 `common-mode`，糙率/面积更偏向影响 `differential-mode`。
- 因而，水量不平衡问题和天然水面线问题不能混在一起讨论；前者属于输入闭合，后者更接近模型结构能力。

## 8. 最关键的结构性证据

- 当前 case 的主支在控制文件中定义为 `US=2, DS=222`。[w2_con.csv](/C:/Users/NING/Desktop/v455/实际案例/w2_con.csv:47)
- 但初始化检查文件 [init_wl_u_check.dat](/C:/Users/NING/Desktop/v455/实际案例/init_wl_u_check.dat:1) 从 `SEG 3` 开始，而不是 `SEG 2`。
- `init-u-elws.f90` 和主求解里的很多循环都从 `CUS(JB)` 开始，而不是固定从 `US(JB)` 开始。[init-u-elws.f90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/init-u-elws.f90:26) [init-u-elws.f90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/init-u-elws.f90:157)
- `layeraddsub.F90` 会根据层和活动段条件重设 `IUT` 并更新 `CUS(JB)`，因此上游浅水段可以被减掉，之后再被加回。[layeraddsub.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/layeraddsub.F90:43) [layeraddsub.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/layeraddsub.F90:60) [layeraddsub.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/layeraddsub.F90:978) [layeraddsub.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/layeraddsub.F90:1021) [layeraddsub.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/layeraddsub.F90:1079)
- 当前实际 case 的 `w2.wrn` 明确记录在 `44435.183` 才 `Add segments 2 through 2`。[w2.wrn](/C:/Users/NING/Desktop/v455/实际案例/w2.wrn:4)
- 这意味着：在当前 W2 计算逻辑和当前 case 设定下，`SEG 2` 并不是一个从始至终稳定参与演化的天然河流段，而是一个可能被活动段机制临时剔除再加回的上游过渡段。
- 这是目前最强的结构性证据之一，说明“模型无法自然再现始终存在的库尾河流态”不是纯参数问题，也不只是流量数据不完整的问题。

## 9. 到目前为止最稳妥的综合判断

- 不能再把“坝前水位拟合不错”当成“水动力就合理”的证据。
- 当前 W2 对这个 case 的主要短板，不是简单的横向平均，而是它对库尾天然河流态、回水末端迁移和库区平水化之间切换的处理方式。
- 目前看到的偏差不是一个单独问题，而是两个问题叠加：
- `SEG 2` 激活或成水过晚。
- 一旦成水，`SEG 2 - SEG 222` 的模拟水面差又塌得过快。
- 从研究策略上，应优先把“输入总量不完整”与“水面线结构性失真”分离开来，再决定是继续做 case 级校准，还是进入源码级改造。

## 10. 后续工作应继承的固定前提

- 以后任何 case 评价，都至少同时报告 `SEG 2` 水位、`SEG 222` 水位和 `SEG 2 - SEG 222` 水面差。
- 以后任何关于 distributed 的讨论，都必须明确它是在补 `common-mode`，还是在声称改善 `differential-mode`；两者不能混说。
- 以后如果继续做源码分析，优先盯 `CUS/JB` 活动段机制、`layeraddsub` 的上游段加减逻辑、以及主循环中自由液面和流速的分裂推进。
- 以后如果继续做 case 试验，应把“支流总量修正”和“天然水面线修正”看成两条不同任务线，而不是期望一个参数同时把两件事都解决。

## 11. 关联文件

- 专题索引：[README.md](/C:/Users/NING/Desktop/v455/docs/reference/hydrodynamics_limitations/README.md:1)
- 核心结论：[01_core_conclusions.md](/C:/Users/NING/Desktop/v455/docs/reference/hydrodynamics_limitations/01_core_conclusions.md:1)
- 求解原理：[02_solver_principles.md](/C:/Users/NING/Desktop/v455/docs/reference/hydrodynamics_limitations/02_solver_principles.md:1)
- 变动回水失效机理：[04_failure_mechanisms_in_variable_backwater.md](/C:/Users/NING/Desktop/v455/docs/reference/hydrodynamics_limitations/04_failure_mechanisms_in_variable_backwater.md:1)
- XLD 2021 case 水位分析：[07_xld_2021_case_waterlevel_analysis.md](/C:/Users/NING/Desktop/v455/docs/reference/hydrodynamics_limitations/07_xld_2021_case_waterlevel_analysis.md:1)
- 双站点水面线复核：[dual_station_review.md](/C:/Users/NING/Desktop/v455/analysis/xld_multifactor/dual_station_review/dual_station_review.md:1)
