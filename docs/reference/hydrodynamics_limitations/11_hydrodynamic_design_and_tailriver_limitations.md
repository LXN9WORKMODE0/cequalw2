# W2 水动力设计特征与库尾河流段失效机理
本页回答什么问题：CE-QUAL-W2 的水动力代码在设计上到底是怎样组织的，这种组织方式为什么适合库区和缓变回水，却不适合你这个“上游坝下天然河流段 + 回水末端迁移 + 坝前库区态”的库尾过渡段，以及后续应该从什么方向改。
Updated: 2026-04-16

## 1. 先给结论

- CE-QUAL-W2 不是“把整条河库系统当成一个始终完整、始终湿润的非恒定回水通道去联立求解”的模型。
- 它更像一个“laterally averaged、hydrostatic、自由液面先解、速度后修正、活动段可增减”的库区型水动力框架。
- 这套设计对细长水库、河道型水库、缓变回水很有效，因为它把主要精力放在自由液面、体积守恒和分层上。
- 但对你这个库尾问题，短板恰好暴露出来：物理上始终存在的河流段，在数值上会被当成可退出活动域的浅水段；一旦退出，边界和来水位置也跟着下移；等它重新加入时，模型更像是在“补一个新储水段”，而不是连续传播天然河流态。

## 2. W2 水动力设计的几个核心特征

## 2.1 laterally averaged + hydrostatic

- W2 从理论上就不是完整 3D 动量框架，而是 laterally averaged 模型。
- 手册 Part 2 明确采用 hydrostatic 假设，并明确写到垂向速度很小、垂向加速度不显式求解。[W2manual455_Part2_Theory_rev0.pdf](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/User%20Manual/W2manual455_Part2_Theory_rev0.pdf)
- 对应到代码上，主循环先解自由液面和纵向速度，再由连续方程诊断 `W`。[w2_main.f90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/w2_main.f90:843) [w2_main.f90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/w2_main.f90:1129) [w2_main.f90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/w2_main.f90:1335)
- 这意味着模型天生更擅长描述“沿纵向-垂向缓慢调整的水体”，而不是上游局部河道段那种强局部惯性、强河槽控制的流态。

## 2.2 自由液面优先，速度后校正

- 在主循环中，`Task 2.2.3` 先解自由液面；`Task 2.2.4` 再解纵向速度 `U`；之后再用 `QC-Q` 进行连续性修正。[w2_main.f90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/w2_main.f90:937) [w2_main.f90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/w2_main.f90:1276) [w2_main.f90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/w2_main.f90:1317) [w2_main.f90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/w2_main.f90:1323)
- 这类分裂推进在库区很实用，因为自由液面和体积响应是主导。
- 但在库尾河流段，它有一个代价：模型很容易把“先把量级守恒做对”放在“沿程坡降是否物理正确”之前。
- 这正是你现在看到的现象：整体水位量级可以被修近，但 `SEG 2-SEG 222` 的坡降却持续偏小。

## 2.3 初始场是 Manning 正常水深，不是非恒定回水场

- 手册 Part 2 明确说 initial water levels and horizontal velocities are computed using Manning’s normal depth equation。[W2manual455_Part2_Theory_rev0.pdf](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/User%20Manual/W2manual455_Part2_Theory_rev0.pdf)
- 代码也是这样做的：先按 `QSSI` 估算各段流量，再用 normal depth 反推初始水面和流速。[init-u-elws.f90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/init-u-elws.f90:26) [init-u-elws.f90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/init-u-elws.f90:159)
- 对库区这通常没问题。
- 但对你这个“汛期期间频繁在河流态和回水态之间切换”的段落，它会先天把问题往“常流/缓变回水”的方向初始化，而不是从一个天然河流段稳定演化到回水段。

## 2.4 活动段不是固定的，`CUS(JB)` 会移动

- 这是你这个问题最关键的结构特征。
- `init-geom` 会根据当前活动层状态计算 `CUS(JB)`。[init-geom.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/init-geom.F90:476) [init-geom.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/init-geom.F90:484)
- `layeraddsub` 在计算过程中还会继续动态地“Add segments / Subtract segments”，并重设 `CUS(JB)`。[layeraddsub.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/layeraddsub.F90:53) [layeraddsub.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/layeraddsub.F90:60) [layeraddsub.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/layeraddsub.F90:1024)
- 也就是说，对 W2 来说，主支上游前几段不是“永远存在的河流段”，而是“当前如果没有活动层就可以退出计算域，之后再回来”的段。
- 这和你的工程认识直接冲突。你这里的 `SEG 2` 不是可有可无的浅滩，它是上游大坝下的第一个断面，物理上始终有水。

## 2.5 来水位置依赖 `CUS`，不是固定物理边界

- 一旦 `CUS` 下移，不只是输出里少了前几个段，连边界条件本身都跟着变。
- 初始化时，上游来水就是在 `I == IU` 处加入，而 `IU = CUS(JB)`。[init-u-elws.f90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/init-u-elws.f90:26) [init-u-elws.f90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/init-u-elws.f90:29)
- 主求解时，水面方程的上游流量项和边界自由液面也都绑定在当前 `IU` 上。[w2_main.f90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/w2_main.f90:903) [w2_main.f90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/w2_main.f90:966)
- 普通 tributary inflow 也会用 `I = MAX(ITR, IU)` 做钳制；如果某个支流名义上在 `CUS` 上游，它会被整体推到新的 `CUS` 再入流。[hydroinout.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/hydroinout.F90:858) [hydroinout.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/hydroinout.F90:931)
- 所以，对这个 case 更准确的描述不是“模型把 `SEG 2` 算错了”，而是“当 `SEG 2` 不活动时，模型已经不再从 `SEG 2` 这个物理位置开始算了”。

## 2.6 distributed 是 non-point source，不是天然河流边界

- 手册 Part 3 明确把 distributed tributary 定义成 non-point source loading，并明确说它是按表面积分配，用于 accounting for ungaged flow。[W2manual455_Part3_InputOutputFiles_rev0.pdf](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/User%20Manual/W2manual455_Part3_InputOutputFiles_rev0.pdf)
- 代码里也是这样：运行阶段直接按 `BI(KT,I)*DLX(I)` 分到顶层 `QSS(KT,I)`。[hydroinout.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/hydroinout.F90:942) [hydroinout.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/hydroinout.F90:943)
- 所以它可以补整体 storage，可以修坝前单点水位，但它不带真实河流态的沿程动量信息，也不带真实河道入流位置。
- 这就是为什么它能修 `common-mode`，却修不好 `differential-mode`。

## 3. 为什么这些特征对库区是优点，对库尾河流段却是缺点

## 3.1 对库区是优点

- 库区里最重要的是自由液面、库容、密度分层和结构物流量。
- laterally averaged + hydrostatic + free-surface-first 的架构，正好把算力和数值稳定性用在这些主控过程上。
- distributed 这种面源补偿也符合库区“总量闭合优先”的工程需求。

## 3.2 对库尾河流段是缺点

- 库尾河流段最关键的不是总 storage，而是“上游河流态如何连续地向下游回水态过渡”。
- 这里需要的是：
- 固定的物理上游边界。
- 始终存在的河道段。
- 对沿程坡降和局部惯性的持续表达。
- 对“河流态-回水态”切换过程的连续追踪。
- 但 W2 目前给你的却是：
- 可移动的活动上游边界 `CUS`。
- 可退出再加入的上游段。
- 先水位、后速度、再流量修正的分裂推进。
- 用 non-point source 去修总量。
- 这就导致它很容易在库尾做出一种“储水段逐渐被顶起来”的响应，而不是“天然河流段被逐步顶托、但仍保持明显纵向坡降”的响应。

## 4. 你这个 case 的具体失效链

## 4.1 起算时 `SEG 2` 不在活动域里

- `init_wl_u_check.dat` 从 `SEG 3` 开始，说明起算时主支的上游活动段已经推进到 `3` 之后。[init_wl_u_check.dat](/C:/Users/NING/Desktop/v455/实际案例/init_wl_u_check.dat:1)
- 实际 case 日志也显示 `SEG 2` 是到 `44435.183` 才 `Add segments 2 through 2`。[w2.wrn](/C:/Users/NING/Desktop/v455/实际案例/w2.wrn:4)

## 4.2 在这段时间里，模型并没有显式求解库尾天然河流态

- 因为几乎所有水动力循环都从 `CUS(JB)` 开始，[w2_main.f90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/w2_main.f90:895) [hydroinout.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/hydroinout.F90:24) [init-u-elws.f90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/init-u-elws.f90:26)
- 所以在 `SEG 2` 不活动时，模型不是在“一个浅但有水的河流段”里传播回水，而是在“已经后退的活动域”里重构自由液面。

## 4.3 当 `SEG 2` 重新激活时，模型更像是在补一个新储水段

- 日志里 `Add segments 2 through 2` 往往和 `Add layer` 一起出现。[w2.wrn](/C:/Users/NING/Desktop/v455/实际案例/w2.wrn:4)
- 这表明它的回归不是平滑的河流态演化，而是和层、段活动状态联动的数值重激活。
- 在这种机制下，`SEG 2` 很容易表现成“突然有水”，而不是“始终有水，只是坡降和流态在变”。

## 4.4 后续 `QC` 修正又进一步把坡降做平

- 在自由液面先解完以后，`U` 会再被连续性修正推一遍。[w2_main.f90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/w2_main.f90:1317) [w2_main.f90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/w2_main.f90:1323)
- 对库区这很有帮助。
- 但对库尾河流段，这意味着模型可能把原本应该表现为沿程坡降和局部惯性的差异，更多地转化成“为了守恒而做的整体速度平衡”。
- 结果就是你观察到的：整体水位量级可以接近，但 `SEG 2-SEG 222` 的水面差始终太小。

## 5. 为什么仅靠调参很难解决

## 5.1 只调支流总量

- 最小实验集中，`Q200` 已经把 `common-mode` 拉到了 `-1.53 m`，说明整体水量级别已经被明显修正。[structural_minimal_summary.csv](/C:/Users/NING/Desktop/v455/analysis/structural_minimal/results/structural_minimal_summary.csv)
- 但它的 `differential-mode` 仍是 `-4.583 m`，`2021-09-10` 的两点水面差只有 `1.397 m`，而实测是 `7.83 m`。
- 这说明“输入总量不够”不是现在的主导矛盾。

## 5.2 只调糙率和面积

- 在 `Q200` 基础上调 `SEG 2-58` 或 `2-122` 的 `MANN x1.2 + AREA x0.9`，并没有把天然坡降修出来，反而把坝前整体水位推坏了。[structural_minimal_summary.csv](/C:/Users/NING/Desktop/v455/analysis/structural_minimal/results/structural_minimal_summary.csv)
- 原因就在于：问题不是单纯的“河道太光滑”或“库容太大”，而是“活动边界、入流位置和自由液面推进逻辑本身就不对”。

## 5.3 只靠 distributed

- `D7` 可以把坝前 RMSE 压得很低，但 `differential-mode` 仍然很差。
- 这正说明 distributed 修的是 storage/common-mode，不是天然水面线。

## 6. 如果要解决，代码层面应该改什么

## 6.1 第一优先：把物理上始终有水的库尾河流段从“可裁切活动段”里解耦出来

- 这是最关键的一步。
- 对你这个 case，`SEG 2` 到某个上游控制段不应该再由 `CUS` 自由裁切，而应被定义成“永远 active 的 river reach”。
- 换句话说，要把“数值干湿段管理”与“物理上游边界”分开。

## 6.2 第二优先：边界和来水位置不能随 `CUS` 后退

- 只要物理上游边界还在 `SEG 2`，那上游坝下主流入库就应始终从 `SEG 2` 进入，而不是随着 `CUS` 跑到 `SEG 3`、`SEG 4`。
- 对支流也一样，如果某个支流物理上在库尾河流段，就不应因为 `CUS` 后退而整体下移。

## 6.3 第三优先：河流态-回水态切换需要更连续的 wetting/drying 机制

- 现在的 add/sub segment 机制更像“段是否参与计算”的开关。
- 但对库尾河流段，更需要的是：
- 最小水深阈值。
- 激活/失活迟滞。
- 对前缘推进的连续表达。
- 而不是简单从输出里变成 `-999` 再被加回来。

## 6.4 第四优先：自由液面、边界和速度需要在每步内更强耦合

- 现在“先水位、后速度、再流量修正”的分裂推进，对库尾河流段太容易把坡降做平。
- 如果继续沿 W2 框架改，最值得做的是在每步内增加 Picard 迭代，把边界源汇、水面解、`U/QC` 修正至少迭代 2 到 4 次再出步。

## 6.5 第五优先：distributed 继续保留也只能当 budget patch，不能当水动力真实性依据

- 后续如果你为了工程闭合还需要 distributed，可以保留。
- 但它的角色应明确限定为“budget closure / residual source”，而不能再用来证明库尾天然水面线是合理的。

## 7. 最终判断

- 你这个问题的根源已经基本推进到代码逻辑层面了。
- 不是简单的“支流流量偏小”。
- 也不是简单的“糙率不合适”。
- 而是 W2 当前这套水动力设计，在理念上就更接近“活动库区 + 回水水面 + 分层体积守恒”，而不是“始终完整的河流-回水过渡通道”。
- 因此，它在你的库尾天然河流段上表现不佳，不是偶然调参失败，而是设计目标与问题类型之间的错位。

## 8. 关联文件

- 代码逻辑审查：[10_code_logic_review.md](/C:/Users/NING/Desktop/v455/docs/reference/hydrodynamics_limitations/10_code_logic_review.md:1)
- 结构性最小实验集：[09_structural_minimal_test_set.md](/C:/Users/NING/Desktop/v455/docs/reference/hydrodynamics_limitations/09_structural_minimal_test_set.md:1)
- 对话发现记录：[08_conversation_findings_log.md](/C:/Users/NING/Desktop/v455/docs/reference/hydrodynamics_limitations/08_conversation_findings_log.md:1)
