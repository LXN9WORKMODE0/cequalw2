# 方法论小组 3：借鉴 EFDC/MIKE 思想但尽量保留 W2 laterally averaged 框架的升级路线
本页回答什么问题：如果借鉴 EFDC、MIKE 等更精细自由液面模型的思想，但仍尽量保留本地这套 CE-QUAL-W2 的 laterally averaged 框架，最值得借哪些数值机制；哪些可以低成本移植，哪些属于中等成本框架升级，哪些已经接近重写求解器或做混合模型；以及对当前库尾 case 最现实的升级顺序是什么。

Updated: 2026-04-17

## 1. 先给总判断

- 本地这套 W2 的主要短板，不只是“维度不够”，而是它把一个本应连续移动的库尾过渡区，做成了几个离散开关：`CUS(JB)` 活动段、`Add/Subtract segments`、固定 `branch slope -> GRAV`、以及“水面先算、速度后修正”的分裂推进。
- 因此，最值得向 EFDC、MIKE 这类模型借的，不是 3D 本身，而是 4 类数值思想：
  - 固定物理域，前沿移动靠连续 wetting/drying。
  - 单元可以部分湿润，几何与库容响应连续，不靠整段整层开关。
  - 同一时间步内自由液面、流量、动量更强耦合。
  - 过渡带的位置由方程和状态变量决定，不由拓扑开关和固定 branch slope 主导。
- 这与前面专题档案的判断一致：[11_hydrodynamic_design_and_tailriver_limitations.md](/C:/Users/NING/Desktop/v455/docs/reference/hydrodynamics_limitations/11_hydrodynamic_design_and_tailriver_limitations.md:1)、[12_submergence_transition_and_refinement_options.md](/C:/Users/NING/Desktop/v455/docs/reference/hydrodynamics_limitations/12_submergence_transition_and_refinement_options.md:1)、[13_channel_slope_and_river_mode_limitations.md](/C:/Users/NING/Desktop/v455/docs/reference/hydrodynamics_limitations/13_channel_slope_and_river_mode_limitations.md:1)。

## 2. 当前本地 W2 最需要被“借鉴式改造”的地方

### 2.1 活动段机制过强，物理域不固定

- `init-geom` 会根据活动层判定上游活动段，`KB(I)-KT < NL(JB)-1` 时直接把 `CUS(JB)` 下推。[init-geom.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/init-geom.F90:476) [init-geom.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/init-geom.F90:484)
- `layeraddsub` 在运行中继续 `Add segments / Subtract segments`，并反复重设 `CUS(JB)`。[layeraddsub.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/layeraddsub.F90:53) [layeraddsub.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/layeraddsub.F90:60) [layeraddsub.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/layeraddsub.F90:1024)
- 实际 case 日志也证明确实发生了这种拓扑式变化，`SEG 2` 是被“加回来”的，而不是始终参与求解。[w2.wrn](/C:/Users/NING/Desktop/v455/实际案例/w2.wrn:6)

### 2.2 入流位置依赖 `CUS`，不是固定物理断面

- 上游边界和部分水动力循环都从 `IU = CUS(JB)` 开始。[hydroinout.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/hydroinout.F90:819) [w2_main.f90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/w2_main.f90:895)
- 支流入流位置也被硬钳制到 `MAX(ITR(JT),IU)`。[hydroinout.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/hydroinout.F90:858)
- 这意味着一旦活动段后退，物理入流位置也跟着后退。这与更精细自由液面模型通常采用的“物理域固定、局部单元可浅可干”的思想不同。

### 2.3 河流驱动部分依赖固定 branch slope 重力项

- 本地输入文件把它明确写成 `Gravity term channel slope [GRAV]`。[w2_con.csv](/C:/Users/NING/Desktop/v455/实际案例/w2_con.csv:306)
- `SLOPE/SLOPEC` 被转成 `SINAC`，再进入 `GRAV` 项。[input.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/input.F90:648) [init.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/init.F90:438) [init.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/init.F90:442)
- 主水动力中 `GRAV` 被直接加入水面方程右端和纵向速度更新。[w2_main.f90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/w2_main.f90:827) [w2_main.f90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/w2_main.f90:855) [w2_main.f90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/w2_main.f90:1237)
- 这说明 W2 的河流态表达，本质上是“固定 branch 级重力驱动 + reservoir-style 自由液面”的混合框架，而不是让局部能量坡降和前沿位置完全由连续方程自然涌现。[13_channel_slope_and_river_mode_limitations.md](/C:/Users/NING/Desktop/v455/docs/reference/hydrodynamics_limitations/13_channel_slope_and_river_mode_limitations.md:1)

### 2.4 时间步内耦合偏弱

- 主流程顺序是 `Task 2.2.3 Water surface elevation -> Task 2.2.4 Longitudinal velocities -> Task 2.2.5 Vertical velocities`。[w2_main.f90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/w2_main.f90:843) [w2_main.f90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/w2_main.f90:1129) [w2_main.f90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/w2_main.f90:1335)
- 这种分裂推进在库区是高效的，但在库尾过渡带更容易出现“总体量级守恒了，坡降被做平了”的现象。[11_hydrodynamic_design_and_tailriver_limitations.md](/C:/Users/NING/Desktop/v455/docs/reference/hydrodynamics_limitations/11_hydrodynamic_design_and_tailriver_limitations.md:1)

## 3. 可以低成本移植的机制

这里的“低成本”指：仍保持 laterally averaged、hydrostatic、现有主方程组织方式不变，只在活动段、源汇布置和时间步控制层面做增强。

### 3.1 固定物理边界段，不再让关键库尾段随 `CUS` 后退

- 借鉴思想：固定物理域。
- W2 可移植形式：
  - 新增“永久活动河段”或“physical upstream reach”标记。
  - 对指定区间禁止 `CUS(JB)` 裁到其下游。
  - 允许 very shallow but active，而不是 shallow then removed。
- 适配本地代码的原因：
  - 直接针对 `init-geom.F90` 与 `layeraddsub.F90` 的活动段逻辑。
  - 不需要推翻 laterally averaged 主框架。
- 对当前 case 的收益：
  - 至少保证 `SEG 2` 到库尾过渡带始终在求解域里。
  - 避免“河流段消失以后再补回来”的数值假象。

### 3.2 加入带迟滞的连续 wetting/drying，而不是只做整段开关

- 借鉴思想：moving front 通过湿润/干涸状态连续推进，而不是拓扑开关。
- W2 可移植形式：
  - 设置 `h_on / h_off` 两套阈值。
  - 对极浅单元保留最小湿润厚度、最小面积、最小水力半径。
  - 将“激活/失活”从布尔量改为带迟滞的状态量。
- 适配本地代码的原因：
  - 仍然可以在 `layeraddsub.F90` 为主的层/段管理模块内实现。
  - 是对现有机制的连续化，不是重写整个自由液面方程。
- 局限：
  - 如果仍保留“入流位置跟着 `CUS` 走”，收益会被削弱。

### 3.3 固定物理入流位置，浅水时做局部分配而不是整体下移

- 借鉴思想：边界位置固定，单元状态变化由内部湿润率承担。
- W2 可移植形式：
  - 上游主边界和关键支流保存 `physical_segment_index`。
  - 当目标单元极浅时，在邻近湿润单元之间做局部分配，不再用 `MAX(ITR, IU)` 整体下移。
- 适配本地代码的原因：
  - 可直接作用于 `hydroinout.F90` 的入流布置逻辑。[hydroinout.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/hydroinout.F90:858)
- 理论上为什么合理：
  - 在自由液面欧拉框架里，边界断面本来就是物理固定的；变化的是该断面的水深、面积和流速，而不是边界位置本身。

### 3.4 每步内增加 2 到 4 次 hydro inner iterations

- 借鉴思想：更强的 pressure/free-surface and velocity coupling。
- W2 可移植形式：
  - 每步内循环执行 `HYDROINOUT -> water surface solve -> U/QC update`。
  - 以 `ELWS`、`Q`、结构物流量变化量作为收敛判据。
- 适配本地代码的原因：
  - 不改变主方程类型，只增强步内自洽性。
  - 适合从 `w2_main.f90` 主循环直接切入。
- 预期收益：
  - 减少步内不同步造成的坝前贴合但坡降失真。
- 局限：
  - 不能单独解决拓扑开关和固定 slope 的根问题。

## 4. 中等成本框架升级

这里的“中等成本”指：仍保留 laterally averaged、主水动力仍然是 W2，但已经开始改变几何表达和河流态闭合方式。

### 4.1 partial-cell / subgrid 几何

- 借鉴思想：单元可部分湿润，`A(h)`、`V(h)`、`R(h)` 连续变化。
- W2 可升级形式：
  - 在库尾过渡带引入“部分湿润层/部分湿润段”。
  - 让断面面积、体积、湿周和摩阻随局部水深连续变化，而不是整层整段 0/1 切换。
- 这是比单纯加密网格更值钱的改造，因为它改的是几何响应机制，而不是只减小离散尺度。

### 4.2 弱化固定 branch slope 的主导地位

- 借鉴思想：局部有效能量坡降应更多由当前自由液面、局部几何和流动状态决定。
- W2 可升级形式：
  - 将 `GRAV` 从固定 branch 参数弱化为“背景驱动项”。
  - 在库尾过渡带引入局部或状态相关的 slope blending，而不是全段统一 `SINAC(JB)`。
- 这样做的目标不是删掉 `GRAV`，而是减少它对过渡带前推的强行主控，让前沿更多由当前状态决定。[13_channel_slope_and_river_mode_limitations.md](/C:/Users/NING/Desktop/v455/docs/reference/hydrodynamics_limitations/13_channel_slope_and_river_mode_limitations.md:1)

### 4.3 过渡带状态指标与状态相关闭合

- 借鉴思想：transition reach 不是纯河流态，也不是纯库区态。
- W2 可升级形式：
  - 定义一个连续状态指标，综合水深、流速、Froude 数、水面坡降和下游顶托强度。
  - 让局部摩阻、混合、局部重力驱动权重、甚至边界处理方式随状态连续变化。
- 这相当于给 W2 增加一个“river-like to pool-like” 的 blending layer。

### 4.4 仅对过渡带做局部高分辨率离散

- 借鉴思想：把精度花在前沿移动带，而不是全域均匀加密。
- W2 可升级形式：
  - `SEG 2` 到回水末端摆动带显著缩短 `DLX`。
  - 提高这一区间垂向分辨率，尽量减少 layer add/sub 的必要性。
- 这属于配套增强，不是第一性改造，但与 partial-cell 和 wetting/drying 协同后很有价值。

## 5. 已接近重写求解器或混合模型的思路

### 5.1 库尾局部 1D 非恒定河道/回水子求解器 + 主库区 W2

- 借鉴思想：在最难的过渡带，用更适合河流/回水切换的求解器；主库区仍保留 laterally averaged reservoir logic。
- 形式：
  - 库尾过渡段单独用 1D Saint-Venant / dynamic wave / backwater solver。
  - 下游主库区继续用 W2。
  - 在连接断面交换水位、流量，必要时交换温度或密度信息。
- 这已经不是“小改 W2”，而是“承认单一求解框架不够用”。

### 5.2 局部重写自由液面与纵向动量的统一求解

- 借鉴思想：用更接近精细自由液面模型的统一耦合求解器来替换现有分裂推进。
- 形式：
  - 重组 `water surface + U + source/sink` 的主方程组。
  - 将过渡带做成真正的非线性统一求解，而非先后更新。
- 一旦做到这一步，虽然仍可保留 laterally averaged 假设，但本质上已经接近“重写 W2 水动力核心”。

## 6. 对当前 case 最现实的升级顺序

按“收益/代价比”和与你当前 case 的针对性，我的排序是：

1. `固定物理边界段 + 入流位置固定`
   - 这是最直接对准 `SEG 2` 与库尾过渡带物理存在性的改造。
2. `连续 wetting/drying + 迟滞`
   - 这是把离散前沿改成连续前沿的核心步骤。
3. `每步 hydro inner iterations`
   - 这是提升步内自洽性的必要配套。
4. `partial-cell / subgrid 几何`
   - 这是把几何、储量、摩阻响应从 0/1 切换改成连续变化的关键升级。
5. `弱化固定 branch slope 主导 + 引入过渡态闭合`
   - 这是把 W2 从“库区逻辑为主、河流态工程化补强”向“连续过渡逻辑”推进的一步。
6. `局部 1D 子求解器 + 主库区 W2`
   - 只有当 1 到 5 做完后，库尾坡降仍系统性塌缩，才值得认真进入这一层。

## 7. 结论

- 对当前本地 W2 来说，最值得借鉴 EFDC、MIKE 等模型的，不是 3D 维度，而是：
  - 固定物理域。
  - 连续 wetting/drying。
  - partial-cell 几何。
  - 更强的步内耦合。
  - 过渡带状态连续化。
- 其中最现实、最应该先做的，并不是“全面重写求解器”，而是先把 `CUS` 主导的活动段逻辑和固定入流位置问题解开，再把 segment/layer 开关改成连续湿润逻辑。
- 如果这些改造后，库尾过渡带的天然坡降仍明显塌缩，那就说明问题已经超出“保留 W2 框架的小修小补”范围，下一步应认真考虑局部 1D 子求解器或混合模型。

## 8. 关联文件

- 水动力设计与库尾局限：[11_hydrodynamic_design_and_tailriver_limitations.md](/C:/Users/NING/Desktop/v455/docs/reference/hydrodynamics_limitations/11_hydrodynamic_design_and_tailriver_limitations.md:1)
- 淹没切换与精细化方向：[12_submergence_transition_and_refinement_options.md](/C:/Users/NING/Desktop/v455/docs/reference/hydrodynamics_limitations/12_submergence_transition_and_refinement_options.md:1)
- 河道坡度项与河流态局限：[13_channel_slope_and_river_mode_limitations.md](/C:/Users/NING/Desktop/v455/docs/reference/hydrodynamics_limitations/13_channel_slope_and_river_mode_limitations.md:1)
