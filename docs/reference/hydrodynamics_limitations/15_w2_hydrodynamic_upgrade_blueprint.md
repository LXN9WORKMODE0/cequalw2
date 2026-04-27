# W2 水动力升级蓝图
本页回答什么问题：如果继续沿 CE-QUAL-W2 路线推进，而不是立刻换成别的模型，那么应该按什么逻辑、什么版本节奏、什么成组修改原则去升级水动力求解器，才能尽量避免半改半留导致的新 bug，并逐步逼近“库尾河流态-回水态-淹没态”连续过渡的真实表达。
Updated: 2026-04-17

## 1. 蓝图目标

- 目标不是把 W2 变成 3D 模型，而是在保留 `laterally averaged + hydrostatic` 主框架的前提下，把库尾过渡带从“活动域管理问题”升级成“连续自由液面过渡问题”。
- 目标也不是靠再调一次 `distributed`、糙率或固定坡度去贴合单点水位，而是让 `SEG 2`、`SEG 222` 及其间水面线更符合物理。
- 本蓝图默认：这些改动**不能拆成彼此独立的小补丁直接混进主线**。必须按版本束成组落地，因为它们共享同一套拓扑语义、源汇语义和求解时序。

## 2. 当前问题的结构性根源

根据前面专题档案与 3 个小组的并行审查，当前 W2 在库尾过渡带的主要短板来自 4 个层面：

1. `CUS(JB)` 同时承担“活动上游边界”和“物理上游边界”的角色，导致物理河段会数值化后退。[init-geom.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/init-geom.F90:476) [layeraddsub.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/layeraddsub.F90:53)
2. `Add/Subtract segments` 与 `ADD_LAYER/SUB_LAYER` 把连续干湿前沿做成整段/整层开关。[layeraddsub.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/layeraddsub.F90:240) [layeraddsub.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/layeraddsub.F90:1021)
3. 支流、主入流和 distributed 的放置位置跟着 `CUS` 变化，而不是固定在物理断面。[hydroinout.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/hydroinout.F90:858)
4. 河流态前推部分依赖固定 `branch slope -> GRAV`，而不是让过渡带局部有效能量坡降完全由当前状态自发决定。[w2_main.f90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/w2_main.f90:827) [13_channel_slope_and_river_mode_limitations.md](/C:/Users/NING/Desktop/v455/docs/reference/hydrodynamics_limitations/13_channel_slope_and_river_mode_limitations.md:1)

因此，本蓝图的核心不是“多加几个参数”，而是逐层重构这 4 个根问题。

## 3. 总体原则

### 3.1 先改语义，再改数值

- 先把“物理河段是否存在”“入流从哪里进”“前沿是否连续”这些语义改对。
- 再去增强时步内耦合、几何精度和状态闭合。
- 如果反过来先加内迭代、先调糙率、先弱化 `GRAV`，往往只会把旧语义算得更稳定，而不是更真实。

### 3.2 版本束必须整体合并，不能半套上线

下列组合必须打包：

- `物理边界固定` 必须和 `入流位置固定` 一起上。
- `连续 wetting/drying` 必须和 `最小几何保护 + 迟滞` 一起上。
- `每步内迭代` 必须和 `结构物/边界重复更新 + 收敛判据` 一起上。
- `弱化固定 GRAV 主导` 必须放在 `连续前沿` 之后，最好放在 `partial-cell` 之后。

### 3.3 版本管理以“整包回归”而不是“单开关试错”为主

- 每个版本束单独建分支，不在主线里穿插半成品。
- 每个版本束可以有运行时总开关用于 A/B 对照，但不要把同一束再拆成很多细碎开关长期共存。
- 每个版本束都必须通过同一套回归案例后再进入下一束。

## 4. 版本管理方案

建议采用如下分支与里程碑命名：

- `codex/w2-hydro-v0-baseline`
- `codex/w2-hydro-v1-domain-foundation`
- `codex/w2-hydro-v2-continuous-front`
- `codex/w2-hydro-v3-inner-coupling`
- `codex/w2-hydro-v4-partial-cell`
- `codex/w2-hydro-v5-transition-physics`
- `codex/w2-hydro-v6-hybrid-tailreach`

建议保留如下基线标记：

- `baseline-xld-current`: 当前可运行版本
- `baseline-xld-no-distributed`: 去掉分布式修正的参考版本
- `baseline-river-example`: 纯 sloping river 参考版本

每个版本束都必须输出同一套指标：

- `SEG 2` 水位误差
- `SEG 222` 水位误差
- `SEG 2 - SEG 222` 水面差误差
- 关键时段活动段/湿润状态日志
- `flowbal` 体积误差
- `w2.wrn` 中 layer/segment 事件

## 5. 回归案例集

建议固定 4 组回归工况，后续每一版都跑：

1. `纯河道态`: 低水位、明显坡降、库尾应始终有水。
2. `纯淹没态`: 高水位、整体平缓、库尾应进入库区式响应。
3. `过渡切换态`: 你当前最关注的 XLD 2021 时段。
4. `结构物切换态`: 自由出流与淹没出流交替出现的窗口。

只有 4 组都不过分恶化，下一版才继续。

## 6. 升级路线

## 6.1 V0: Baseline 与诊断层

### 目标

- 不改物理，只把后续所有版本需要的诊断量固定下来。

### 必须一起做的内容

- 明确区分并输出：`physical upstream segment`、`active upstream segment`、`wet/dry state`。
- 在日志里补充：每次 `CUS` 变化、每次 layer/segment 加减、每次主入流和支流实际注入位置。
- 固定回归脚本和评价指标。

### 涉及文件

- [w2_main.f90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/w2_main.f90:843)
- [hydroinout.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/hydroinout.F90:819)
- [layeraddsub.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/layeraddsub.F90:53)

### 验收

- 不改变当前解，但能完整解释 `SEG 2` 何时被裁掉、何时被加回。

## 6.2 V1: Domain Foundation

### 目标

- 把“物理河段存在性”和“活动求解起点”解耦。

### 这一个版本束必须整体落地

1. 新增物理边界段概念，例如 `IUPHYS(JB)`。
2. `CUS(JB)` 保留为活动求解起点，但不再允许把指定库尾过渡带整体裁出物理域。
3. 主入流、关键支流、关键取水口位置改为锚定物理断面，而不是 `MAX(ITR, IU)`。
4. 所有边界循环同时知道 `physical span` 与 `active span`。

### 为什么不能拆开做

- 如果只固定边界段，不改入流放置，来水仍会数值化后退。
- 如果只固定入流，不改活动域语义，边界和 ghost cell 仍会断裂。

### 涉及文件

- [init-geom.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/init-geom.F90:476)
- [layeraddsub.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/layeraddsub.F90:60)
- [hydroinout.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/hydroinout.F90:858)
- [w2_main.f90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/w2_main.f90:895)

### 验收

- `SEG 2` 不再作为物理河段“消失”。
- 主入流和关键支流始终从物理位置入流。

## 6.3 V2: Continuous Front

### 目标

- 把整段整层开关改成连续湿润前沿。

### 这一个版本束必须整体落地

1. 引入 `wet state` 状态机，而不是单一 active/inactive 布尔语义。
2. 引入 `h_on / h_off` 迟滞。
3. 对极浅单元引入最小湿润厚度、最小面积、最小水力半径保护。
4. `ADD_LAYER/SUB_LAYER` 和 `Add/Subtract segments` 由“开关动作”改成“状态更新 + 必要时才拓扑调整”。

### 为什么不能拆开做

- 如果只有迟滞没有几何保护，会出现极浅单元数值不稳定。
- 如果只有最小厚度没有状态机，前沿仍会抖动。

### 涉及文件

- [layeraddsub.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/layeraddsub.F90:240)
- [layeraddsub.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/layeraddsub.F90:1021)
- [init-geom.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/init-geom.F90:464)

### 验收

- 过渡带前沿移动变连续。
- `w2.wrn` 中不再频繁出现库尾段反复“减掉再加回”。

## 6.4 V3: Inner Coupling

### 目标

- 让同一步内的水位、速度、结构物流量更自洽。

### 这一个版本束必须整体落地

1. 在主循环内引入 `2-4` 次 `hydro inner iterations`。
2. 每次迭代都重算 `HYDROINOUT`、自由液面、`U/QC`。
3. 结构物流量也参与同一步迭代更新。
4. 增加 `ELWS/Q/structure flow` 三重收敛判据和必要的步内回退。

### 为什么不能拆开做

- 如果只迭代水面不重算结构物流量，源汇仍不同步。
- 如果只迭代 `U/QC` 不重算边界，效果会非常有限。

### 涉及文件

- [w2_main.f90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/w2_main.f90:843)
- [hydroinout.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/hydroinout.F90:819)
- [gate-spill-pipe.f90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/gate-spill-pipe.f90:524)

### 验收

- 同样边界下，`SEG 2 - SEG 222` 的水面差不再因为步内不同步而明显塌缩。

## 6.5 V4: Partial-Cell Geometry

### 目标

- 让过渡带几何响应连续化。

### 这一个版本束必须整体落地

1. 库尾过渡带引入 `partial-cell / subgrid` 思想。
2. `A(h)`、`V(h)`、`R(h)` 连续变化。
3. 对应的摩阻、库容和局部波速响应同步改成连续量。

### 为什么不能拆开做

- 如果只改面积不改库容，质量守恒与动力响应会脱节。
- 如果只改几何不改摩阻，前沿位置仍会失真。

### 涉及文件

- [init-geom.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/init-geom.F90:20)
- [w2modules.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/w2modules.F90:142)
- 预处理几何链路与相关输入文件

### 验收

- 水位抬升与库容张开过程明显更平滑。

## 6.6 V5: Transition Physics

### 目标

- 让过渡带不再只受固定 `branch slope -> GRAV` 主导。

### 这一个版本束必须整体落地

1. 定义过渡态指标，综合水深、流速、坡降、顶托强度。
2. 让局部摩阻、混合和驱动权重随状态连续变化。
3. 弱化固定 `GRAV` 对过渡带前推的支配，只保留为背景驱动。

### 为什么不能拆开做

- 如果先削弱 `GRAV`，而连续前沿和 partial-cell 还没做好，低水位河流态会直接失真。

### 涉及文件

- [w2_main.f90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/w2_main.f90:827)
- [init-u-elws.f90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/init-u-elws.f90:361)
- [az.f90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/az.f90:57)

### 验收

- 低水位河流态与高水位淹没态都不过度依赖手工设定的固定坡度。

## 6.7 V6: Hybrid Tailreach

### 目标

- 当 V1-V5 后仍无法维持真实坡降时，为库尾引入局部 1D 子求解器。

### 何时进入这一版

满足以下任一条件，就应认真进入 V6 论证：

- `SEG 2` 和 `SEG 222` 都能贴近，但两点水面差仍系统性塌缩。
- 过渡区位置仍主要由阈值和管理逻辑决定，而不是由当前流场决定。
- 为了维持两端水位，仍需大量依赖人为 `distributed` 或人为 `SLOPEC`。

### 形式

- 库尾过渡带：1D 非恒定河道/回水
- 主库区：W2
- 连接断面交换水位、流量，必要时再交换温度/密度

## 7. 实施顺序与止损点

建议顺序：

1. `V0`
2. `V1`
3. `V2`
4. `V3`
5. 回归评估一次
6. `V4`
7. `V5`
8. 再评估一次
9. 如仍失败，再进入 `V6`

止损原则：

- 如果 `V1-V3` 做完后，库尾仍经常“数值消失/重现”，说明语义层改动不完整，不能急着上 `V4-V5`。
- 如果 `V4-V5` 做完后，水面差仍显著塌缩，则应停止继续在 W2 内做小修小补，转入 `V6`。

## 8. 最终结论

- 这套升级不能按“一个 patch 一个 patch”零散推进。
- 真正合理的方式，是把它当成一组有先后依赖关系的版本束。
- 其中最关键的，不是先调 `GRAV`，也不是先调糙率，而是先把：
  - 物理边界固定
  - 连续 wetting/drying
  - 入流位置固定
  - 步内更强耦合
  这四件事做对。

只有这样，后续的 partial-cell 与过渡态闭合才有意义；否则就只是把旧框架算得更复杂而已。
