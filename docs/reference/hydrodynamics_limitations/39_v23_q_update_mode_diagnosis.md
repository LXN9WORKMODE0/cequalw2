# V23 Q Update Mode Diagnosis

本页回答什么问题：`V21` 的 `tail_q_max=10255` 是否由 Q 方向 secant 更新放大，以及把 Q 更新退回保守 relaxation 后会发生什么。

Updated: 2026-04-28

## 原始问题

`V22` 已经排除了一个重要假设：

- 把 BHT 或所有正 distributed 移到 BHT 库尾入流，会改变水量入口路径；
- 但不会解除 `tail_q_max=10255`；
- 三条 distributed 对照的最大 Q 残差都发生在同一个启动初期接口事件。

因此本轮改查接口求解本身，尤其是 `V21` 的 Q secant 更新。

## 实验开关

新增环境变量：

```text
W2_TAIL_Q_UPDATE_MODE
```

模式：

- `SECANT`: 默认模式，保持 V21 当前 Q secant 更新。
- `RELAX`: Q 不做 secant 外推，只用当前残差 relaxation 更新。
- `HOLD`: 接口迭代内不更新 Q guess，只更新 ETA。

新增诊断标记：

```text
[V23_Q_UPDATE_MODE] MODE=...
```

该开关是诊断用，不是最终算法承诺。

## 短窗口对照

短窗口使用：

```text
TMEND = 44431.0
scope = bht
alpha = 0
```

| mode | tail_eta_max | tail_q_max | QIN mean | QDT_SUM mean |
|---|---:|---:|---:|---:|
| SECANT | 0.31978 | 10255 | 5078.498653 | 154.24 |
| RELAX | 0.30270 | 1985.8 | 5078.500733 | 154.24 |
| HOLD | 0.39031 | 3002.6 | 5078.498761 | 154.24 |

短窗口结论：

- `RELAX` 直接把启动尖峰从 `10255` 降到 `1985.8`。
- `HOLD` 也消除了 `10255`，但残差仍有 `3002.6`，且 ETA 更差。
- 因此问题不是“Q 不能更新”，而是 `V21` 的 Q secant 更新在启动初期放大了不稳定步。

## 完整窗口确认

完整窗口使用：

```text
TMEND = 44436.5
scope = bht
alpha = 0
```

| mode | tail_eta_max | tail_q_max | seg2 bias | seg222 bias | head bias | QIN mean | QDT_SUM mean |
|---|---:|---:|---:|---:|---:|---:|---:|
| SECANT | 0.45645 | 10255 | 1.120442 | 0.149213 | 0.971229 | 4858.225460 | 154.24 |
| RELAX | 0.45858 | 1985.8 | 1.116332 | 0.149106 | 0.967227 | 4858.224028 | 154.24 |

完整窗口结论：

- `RELAX` 保留了和 baseline 接近的水位误差。
- `RELAX` 把最大 Q 残差降回 `1985.8`。
- `tail_eta_max` 只从 `0.45645` 到 `0.45858`，差异很小。

## 链路判断

### 输入

本轮没有改变 distributed，也没有改变 BHT 输入。

`QIN mean` 和 `QDT_SUM mean` 在 SECANT/RELAX/HOLD 间保持一致，因此差异来自接口 Q 更新策略。

### 处理流程

启动初期第一组接口迭代中：

- `SECANT` 在第 4 次迭代出现 `Q_C=15936.757` 与 `Q_P=7315.457` 的大残差；
- `RELAX` 把同一阶段控制为 `Q_P=6800.272`、`Q_C=5807.380`，最大残差为 `1985.8`；
- `HOLD` 不更新 Q，因此第一阶段残差为 `3002.6`。

### 状态变化

`RELAX` 没有明显破坏水位指标：

- `seg2/head` bias 略低于 SECANT；
- `seg222` bias 基本不变；
- `ETA` 残差基本同量级。

### 输出

`RELAX` 是当前最小正确方向：

- 保留 Q 的反馈更新；
- 避免启动期 secant 外推；
- 明显降低最大 Q 残差。

## 当前结论

`V23` 固定了一个关键事实：

> V21 的最大 Q 残差不是 distributed 路径导致的，而是 Q secant 更新在启动初期放大了 tailreach/interface transient。

下一步不应简单采用 `HOLD`，也不应回到无接口 Q 更新。更合理的方向是：

- 默认用 `RELAX` 作为 Q 方向更新；
- 或只在通过稳定性条件后启用 Q secant；
- 例如要求 DQ 连续同号、残差下降、且不处于前几轮启动迭代。

未验证前提：

- 还没有测试“ETA 保持 secant、Q 使用 gated secant”的折中模式。
- 还没有测试更长窗口或其他入流时期。
- 还没有把 `RELAX` 作为默认算法，只是通过环境变量进行了诊断验证。
