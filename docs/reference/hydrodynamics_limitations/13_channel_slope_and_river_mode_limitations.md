# W2 河道坡度项与河流态局限
本页回答什么问题：W2 在纯天然河道模拟里为什么要额外输入 `channel slope`，这是否说明它并不是完全依靠自由液面方程去表达斜坡河道的前推趋势；以及这一点对库尾河流态-回水态过渡问题意味着什么。
Updated: 2026-04-17

## 1. 先给结论

- 是的，这个现象非常重要，而且它确实说明 W2 的河流态表达并不是“完全由自由液面和动量方程自然涌现出来”的那一类。
- 但更准确的说法不是“W2 不会解坡降带来的水向前走”，而是：W2 在河流态下把一部分沿程重力驱动显式写成了 `channel slope` 对应的 `GRAV` 项，而不是只让它通过连续变化的水面坡降自行出现。
- 这种设计对长条形河道和较稳定的 sloping river 很实用，但对你这种“库尾河流态-回水态-淹没态反复切换”的过渡区不够自然，因为这里真正变化的不是一个固定 branch slope，而是控制流动的能量坡降、回水顶托和局部惯性关系。

## 2. 这个坡度在 W2 里到底是什么

- 输入文件里这个量不是简单几何描述，而是明确命名为 `Gravity term channel slope [GRAV]`。[w2_con.csv](/C:/Users/NING/Desktop/v455/实际案例/w2_con.csv:306)
- 源码里 `SLOPE` 和 `SLOPEC` 被读入 branch 参数，并进一步转成 `ALPHA / SINA / SINAC / COSA`。[input.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/input.F90:648) [input.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/input.F90:697) [input.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/init.F90:438)
- 在主水动力里，`GRAV` 被单独组装为纵向动量项：
  - `GRAV(KT,I) = ... * G * SINAC(JB)`
  - `GRAV(K,I)  = ... * G * SINAC(JB)`  
  然后直接加进水面方程右端项和纵向速度更新项。[w2_main.f90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/w2_main.f90:827) [w2_main.f90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/w2_main.f90:855) [w2_main.f90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/w2_main.f90:1237) [w2_main.f90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/w2_main.f90:1250)

这说明对 W2 来说，河道纵向加速并不只是“水面解出来后自然形成的压力梯度”，而是有一个单独的、按 branch slope 投影进去的重力驱动分量。

## 3. 官方手册是怎么定义它的

- Part 2 手册在 `Computation of Initial Water Surface Slope and Velocity Field for River Simulation` 一节里明确写到：河流模拟的初始水位和初始速度是按 Manning 正常水深方程内部计算的，而且公式中的 `S` 就是 `Branch slope`。[W2manual455_Part2_Theory_rev0.pdf](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/User%20Manual/W2manual455_Part2_Theory_rev0.pdf)
- Part 4 手册在 `River` 和 `Channel Slope` 章节里进一步明确指出：
  - `Channel slopes accelerate the fluid`
  - `The channel slope is used to compute the gravity force of the channel`
  - 这个 slope 应该取水面坡或能量坡降线，而不是逐段底坡。[W2manual455_Part4_ModelExamples_rev0.pdf](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/User%20Manual/W2manual455_Part4_ModelExamples_rev0.pdf)
- 手册还特别解释了为什么不推荐 segment-by-segment slope：噪声太大，而且模型的 surface layer / waterbody 组织方式不适合按每段独立坡降连续求解；当上游段保不住水时，模型会减层、减段，甚至把上游段从活动网格里移除。[W2manual455_Part4_ModelExamples_rev0.pdf](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/User%20Manual/W2manual455_Part4_ModelExamples_rev0.pdf)

所以这个问题不是偶然实现细节，而是 W2 官方河流模式的一部分设计思想。

## 4. 这说明了什么

## 4.1 它说明 W2 的河流态支持是“工程化增强”，不是完整的动波河道解法

- W2 为了让 sloping river 能跑起来，显式引入了 branch slope 重力项，并用 Manning normal depth 来构造初始水面和初始速度。
- 这很实用，也很符合它“laterally averaged reservoir-river model”的定位。
- 但这意味着它并不是那种“只靠自由液面、底床几何、动量方程和 wetting/drying，自然把河流态与回水态统一解出来”的模型。

## 4.2 在纯河道里它可以工作，但前提是你愿意提供一个代表性的能量坡降

- 对较稳定、较长、控制关系比较清晰的 sloping river，这种做法是合理的。
- 因为在那种场景里，branch 级别的代表坡降本来就能概括主要重力驱动。
- 手册示例甚至建议按一段河流的回归水面坡或能量坡降来给 branch slope，而不是逐断面底坡。

## 4.3 但在库尾过渡区，这种做法会变得不自然

- 你这里的库尾不是一个坡降基本稳定的纯河流 branch。
- 真正控制水流前推和水面线弯折的位置，会随：
  - 上游来流
  - 下游顶托
  - 库区水位
  - 局部流速和摩阻
  - 结构物出入流
  连续变化。
- 这意味着真正的“有效能量坡降”不是固定 branch 参数，而是一个随时间和空间变化的场。
- 如果模型仍用固定 branch slope 去表示一大段河道重力驱动，再叠加活动段增减和分裂推进，就很容易出现：
  - 河流态阶段需要的前推和输水趋势表达不够自然
  - 过渡态阶段的回水前沿位置更多受拓扑和阈值控制
  - 高水位淹没后又重新表现成较平缓的库区逻辑

## 5. 这对我们前面讨论的“如何改 W2”意味着什么

这说明改造级别可能确实比“修补几个边界判断”更大。

### A. 小改级别

- 固定物理边界
- 连续 wetting/drying
- 每步内迭代

这些都很有价值，但它们主要是在修复“离散开关过强”和“时步内不同步”。

### B. 中改级别

- 把 `channel slope` 从固定 branch 参数，升级成更局部、甚至状态相关的驱动表达
- 让库尾过渡带的有效坡降更多来自局部自由液面和局部几何，而不是大段统一 `SLOPE/SLOPEC`

这已经开始触及 W2 河流模式的设计核心了。

### C. 大改级别

- 不再把河流态主要建立在“显式 branch gravity term + reservoir-style free surface solve”上
- 而是把库尾过渡带改造成更接近 1D 非恒定河道/回水求解的局部子求解器，再与 W2 主库区耦合

这实际上就接近“保留 W2 作为主库区模型，但重写库尾求解思想”了。

## 6. 对你当前问题的最重要判断

- 你提出这个坡度问题之后，我们对 W2 的判断需要再推进一步。
- 现在不能只说“W2 在库尾过渡区用了过强的活动段开关”。
- 还应该再补上一句：W2 的河流态本身就是建立在一个显式 `channel slope -> gravity term` 的工程化表达上，因此它并不是天然围绕“过渡区位置由方程完全自发决定”来设计的。

所以你前面那句判断是成立的：

- 如果目标真的是让“过渡区的位置主要由当前水位、来流、出流、流速和顶托自发决定”，
- 那么现有这套偏深水库、偏 branch-slope 驱动的 W2 水动力设计，确实需要比较大的改动。

## 7. 最后一句话

W2 不是不会做河流，也不是不会做坡降；  
但它做河流的方式，是“给河流态额外加一个 branch-scale 的重力驱动框架”，而不是“把河流态到回水态的连续变化完整统一地求出来”。

这正是它在你这个库尾问题上显得先天吃力的原因之一。
