# V24 Interface Conservation Design

本页回答什么问题：V21–V23 已经定位了 Q secant 的启动放大，但为什么 V24 不能只把默认模式改成 `RELAX`，以及 tailreach/reservoir 接口在继续优化前必须满足哪些守恒契约。

Updated: 2026-07-15

## 1. 原始目标

当前目标仍是改善 XLD 2021 工况中库尾河流态、过渡态和库区回水态之间的连续响应。V24 不增加新的业务工况，也不调参贴合单点水位；它先修复现有 hybrid tailreach 原型中已经能够由代码直接证明的状态与通量不一致。

## 2. V21–V23 已确认的证据

- V21 的 ETA secant 降低了最大水位残差，但 Q secant 把启动期最大流量残差从 V20 的 `1985.8 m3/s` 放大到 `10255 m3/s`。
- V22 把 distributed 从内部源项移动到 BHT 物理入流，改变了水量入口和水位响应，却没有改变 `10255 m3/s` 尖峰，因此 distributed 位置不是该尖峰的直接原因。
- V23 的 `RELAX` 模式把尖峰恢复到 `1985.8 m3/s`，且短窗和扩展窗水位指标与 SECANT 接近。因此 Q secant 是直接放大器，但这不等于接口已经守恒。

## 3. 当前链路审计

### 3.1 输入

- 外部物理入流：`QPHYS = QIN(JB)`。
- tailreach 向 reservoir 的内部接口流量：`QIFACE = TAIL_Q_LINK(JB)`。
- reservoir 主矩阵实际使用的边界流量：`QRES = EFFECTIVE_UPSTREAM_INFLOW(JB)`。

### 3.2 处理流程

当前每个时间步先运行 tail predictor，reservoir 主矩阵使用 predictor 产生的接口量求解一次，之后再运行最多四轮 tail-side interface iteration。reservoir 不会在这些 corrector 迭代中重算。

### 3.3 状态变化

`UPDATE_TAIL_STAGE` 先按 branch-level `Q_STATE` 更新 `TAIL_STORAGE_VOL`，随后 `ADVANCE_TAIL_SEGMENT_STATES` 又逐段衰减流量，并把最终衰减值写回 `TAIL_Q_LINK/Q_STATE/Q_OUTFLOW`。后一步没有对同一流量差增加 segment storage 或显式源汇。

### 3.4 输出与上下游影响

reservoir 入口当前使用：

```text
QRES = 0.85 * QPHYS + 0.15 * QIFACE
```

因此 tail 控制体的出口流量与 reservoir 控制体的入口流量不是同一个量。该差值会直接进入 reservoir 水面方程，并影响后续水位、自动时间步和下一步 predictor。

## 4. 已确认的结构性缺口

### 4.1 接口两侧使用不同通量

只要 tail domain 已接管物理上游段，内部接口必须满足 `QRES = QIFACE`。当前 blend 是稳定化手段，但稳定化被放在了物理通量上，因此破坏组合控制体守恒。

### 4.2 segment Q 衰减没有守恒去向

`QDN = QUP * (1 - SEG_LOSS)` 产生的差值没有进入 segment storage，也没有成为显式侧向源汇或损失项。摩阻可以改变动量和水位坡降，不能直接消灭质量流量。

### 4.3 storage 与最终接口流量不同步

branch storage 依据 segment 推进前的 outflow 更新，segment 推进后又覆盖最终 outflow。因而日志中的 `TAIL_STORAGE_VOL` 与最终 `TAIL_Q_LINK` 并不满足同一条连续方程。

### 4.4 最大迭代后保存未求值 guess

第 4 轮未收敛时仍计算下一步 secant/relax guess，循环随即结束；该 guess 没有经过 `UPDATE_TAIL_STAGE` 求值，却被保存为下一次 interface predictor。已记录的 `Q_P=7315.457`、`Q_C=15936.757` 正是这一时序的直接表现。

### 4.5 多段 volume 目前不是控制体状态

`TAIL_VOL_SEG` 每次由几何重建，`TAIL_STORAGE_VOL` 又只通过单个代表断面的 `TAIL_VOLUME_FROM_STAGE` 更新。现有多段数组是派生状态骨架，不是逐段连续方程闭合后的持久控制体。

## 5. V24 守恒契约

对每个 active tail branch 和每个已提交时间步，必须满足：

```text
dVtail/dt = QPHYS - QIFACE
QRES_USED = QIFACE
```

组合控制体等价条件为：

```text
R_tail     = dVtail/dt - (QPHYS - QIFACE) = 0
R_flux     = QRES_USED - QIFACE            = 0
R_combined = dVtail/dt + QRES_USED - QPHYS = 0
```

同时满足两个状态条件：

- interface iteration 退出时，保存的 guess 必须是已经求值并提交的状态；不能保存未求值外推。
- segment 间的流量差必须对应 segment storage 变化或显式源汇；在逐段连续方程完成前，不保留无去向的人工流量衰减。

## 6. 最小正确实施顺序

### Step A：特征诊断，不改物理

- 记录 reservoir 本时间步实际使用的 `QRES_USED`。
- 记录 branch storage rate、最终 `QIFACE`、segment 人工衰减量。
- 输出并解析 `R_tail/R_flux/R_combined`，冻结 V23 基线。

### Step B：迭代终态一致性

- Q 默认使用已验证的 conservative relaxation。
- 只有存在下一轮求值时才生成下一 guess。
- 达到迭代上限时提交最后一个已求值 corrector 状态。

### Step C：守恒接口

- active tail domain 下 reservoir 直接使用同一 `QIFACE`。
- 松弛只能作用于 interface 求解过程，不能再混合物理边界通量。
- 去除无质量去向的 segment Q attenuation；首个守恒版本允许 segment Q 作为同一接口通量的派生视图，随后再以独立任务实现真正的逐段连续方程。

### Step D：回归与下一轮判断

- short/extended case 无 runtime error，`SEG 2/222` 均持续有效。
- `R_tail/R_flux/R_combined` 降到浮点舍入量级。
- 对比 V23 的 ETA/Q 残差、时间步数量、双站水位和水面差。
- 如果守恒成立但水面线仍系统性塌缩，再进入逐段 momentum/continuity 子求解器；不再用非守恒衰减修形。

## 7. 当前未验证前提

- V23 基线已量化：`max|R_tail|=10309`、`max|R_flux|=9619.6`、`max|R_combined|=2732.4`、`max|segment loss|=171.45`。
- V24 short window 已验证 exact interface 对守恒和 XLD 水位的影响；`TMEND=44436.5` extended window 尚未完成。
- 尚未实现真正的逐段 continuity/momentum 联立；V24 首要任务是消除已确认的非守恒路径，而不是宣称完整 1D tail solver 已完成。

## 8. 阶段判断

V24 的正确起点不是继续调 Q secant gate，而是先让同一接口只有一个已提交流量，并让这个流量与 tail storage 使用同一条连续方程。只有守恒闭合以后，残差收敛速度和水位精度的比较才具有明确物理含义。

## 9. Short-window implementation status

V24 已将 tail/reservoir coupling 明确实现为 partitioned explicit commit：reservoir 主矩阵只求解一次，因此本步使用 predictor 给出的唯一 `QIFACE`；corrector 不再生成另一个本步物理通量，而是用同一流量和已求解 downstream stage 提交 tail storage/state。

`TMEND=44431.0` fresh short run 得到：

```text
max|R_tail|     = 1.1642e-10 m3/s
max|R_flux|     = 0
max|R_combined| = 1.1642e-10 m3/s
max|segment loss| = 0
```

实现过程中还确认：storage lower bound 必须同步形成可用水量约束，不能只截断 volume。当前 predictor 使用：

```text
QIFACE <= QPHYS + max(Vold - Vmin, 0) / DT
```

该约束也应用于 predictor cache 复用判定，避免性能路径绕过守恒边界。short window 已通过，extended window 仍是下一验收步骤。
