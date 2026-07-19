# V37 BHT–SJ Macro-Interface Preflight

本页在不改变模型状态的前提下，检查以 SJ（segment 26）作为 BHT–SJ 宏接口时，现有动量闭合能否直接成为第二个控制体通量。

Updated: 2026-07-19

## 1. 输入、处理与状态契约

- 可选 `tail_macro.opt` 每行写 `JB SEG`；本次为 `1 26`。
- 物理输入仍为 BHT `QIN`，已提交通量仍为基线 `TAIL_Q_LINK`。
- 同时计算两个只读目标：以 BHT 单断面代表全长的现有 local closure，以及沿 segment 2:26 逐断面积分摩阻和端点速度头的 aggregate closure。
- 两个目标均只写入 `[V37_MACRO_TARGET]`，不拥有 volume、不进入 continuity、不改变 stage、Q 或 reservoir consumer。
- 对观测重叠时刻，再仅用实测 BHT–SJ head 替换总水头；内部断面 conveyance 仍来自模拟状态，因此该步骤是边界敏感性检查，不是独立率定。

## 2. 模拟状态结果

5927 个 accepted states 全部得到有效 aggregate target：

| 闭合 | Target/commit 中位数 | P10–P90 | ±20% 比例 |
|---|---:|---:|---:|
| BHT 单断面 local | 0.452 | 0.439–0.479 | 0.051% |
| segment 2:26 aggregate | 1.537 | 1.337–1.752 | 0% |

local closure 把 22.510 km 河段视为 BHT 单断面，显著低估 conveyance；aggregate closure 使用所有断面后又显著高估。两者从相反方向夹住物理流量，但都不能直接激活。

## 3. 实测水头核对

accepted-state 范围内共有 145 个未插值逐时观测可对齐：

- 实测 BHT–SJ 平均 head：`10.676 m`；同刻模拟：`10.560 m`。
- 只替换实测 head 后，local target/physical 中位数为 `0.436`，aggregate 为 `1.626`；两者 ±20% 比例均为 0。
- 在“内部断面状态可信、所有 segment 共用一个工程等效 Manning n”的假设下，使 aggregate energy 与物理流量闭合所需 `n` 中位数为 `0.04577`，P10/P90 为 `0.04270/0.05053`；现有输入为 `0.03`。

这个 `n` 是 bathymetry、未解析局部损失、内部 profile 和糙率的合并等效量，不能表述为已验证的物理糙率。原工作簿未确认统一高程基准，也进一步限制其物理解读。

## 4. 不变性与门禁

- V37 run 继续通过 V24–V33 全部门禁，无 computational warning。
- V37 与无 `tail_macro.opt` 的 fresh baseline 输出逐字节一致：
  - `wl.csv` SHA-256：`4BF244290DFB8AC38965F4E2A69FA06CE6A2D4EE339250B55494F7280AD3D9FE`；
  - `flowbal.csv` SHA-256：`020705597433EDBA2F228DEB6E051177DD05D31D7998FC829E9C4E0CDE614FBE`。

## 5. 审视结论与决策点

路线 A 有明确帮助：它把可辨识尺度从 segment 2:5 的三个局部阻力，提升为 BHT–SJ 宏观总阻力，并给出了相对稳定的工程等效范围。但数据仍不能区分该阻力来自真实糙率、断面误差、局部损失还是内部水面 profile。

因此当前不能无条件激活任何一个 V37 target。下一步需要在以下两条物理语义中选择：

1. 接受 `n≈0.046` 作为 BHT–SJ aggregate closure 的工程等效先验，并以多站水位、守恒和跨窗口验证约束两状态实现；
2. 继续补充高程基准、断面来源、糙率/局部损失先验或 BHT–SJ 内部站点，再把等效阻力拆成物理参数。

无论选择哪条，直接扩大单状态 domain、直接启用 local target、或把 `0.046` 写回全库统一 Manning 均已被现有证据否定。
