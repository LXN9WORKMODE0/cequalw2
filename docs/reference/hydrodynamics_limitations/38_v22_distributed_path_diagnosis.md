# V22 Distributed Path Diagnosis

本页回答什么问题：`distributed` 补流从库区内部源项移到 BHT 库尾物理入流以后，是否能解释或修复 `V21` 的尾段-库区接口流量残差问题。

Updated: 2026-04-27

## 原始问题

用户确认：

- `distributed` 主要服务于补缺测入流总量。
- `BHT` 是上游大坝出流，应当只在库尾进入。
- 如果去掉 distributed，`seg222` 以及呈现库区特征的所有 segment 水位会受明显影响。

因此本轮不把 `distributed` 当作真实河道边界，而是验证一个更窄的问题：

> 当前 `tail_q_max = 10255` 是否主要由 distributed 补流没有在库尾和 BHT/1D 尾段衔接导致？

## 输入检查

`distributed` 在当前 W2 路径中进入 `QSS`：

```fortran
QDT(I)=QDTR(JB)*BI(KT,I)*DLX(I)/AKBR
QSS(KT,I)=QSS(KT,I)+QDT(I)
```

这表示它是库区内部分布源项，不等价于 BHT 边界入流。

BHT 物理入流进入 `QIN(JB)`，在 tailreach active 时通过：

```fortran
EFFECTIVE_UPSTREAM_INFLOW=(1-relax)*QPHYS + relax*TAIL_Q_LINK
```

进入主库区水面矩阵。因此，把 distributed 移到 BHT 会改变两个入口：

- 减少库区内部 `QSS/QDT`
- 增加尾段/库尾侧 `QIN/QEFF`

## 诊断实现

`V22` 没有改变求解逻辑，只增加通量诊断：

```text
[V22_BOUNDARY_FLUX] JB=1 QIN=... QEFF=... QDT_SUM=... QSS_SUM=... TAIL_Q=...
```

字段含义：

- `QIN`: BHT 物理入流读取值。
- `QEFF`: reservoir 主矩阵实际使用的上游有效入流。
- `QDT_SUM`: branch 1 active distributed 分布流量合计。
- `QSS_SUM`: branch 1 源汇项合计。
- `TAIL_Q`: tailreach 反馈到库区接口的流量。

为避免日志过大，只记录 `JB=1` 的前 10 次和每 500 次水动力步。

对应代码：

- `w2source_v455_2_11_2026/w2_main.f90`
- `analysis/run_v21_bht_redistribution_scan.py`
- `analysis/test_v21_bht_redistribution_scan.py`

## 实验流程

使用固定格式后的 `analysis/run_v21_bht_redistribution_scan.py` 重跑完整窗口：

```text
TMEND = 44436.5
```

三条完整窗口 case：

1. `redistribute_bht_a00_case`: 不移动 distributed，作为 baseline。
2. `redistribute_bht_a100_case`: 只把 BHT active distributed 正值全部移入 BHTOUTFLOW。
3. `redistribute_all_a100_case`: 把 BHT + 五条支流 active distributed 正值全部移入 BHTOUTFLOW。

过程中发现并修正了一个实验脚本问题：

- 原脚本把 `.npt` 整数写成 `5360` 而不是 `5360.`
- W2 对这一路输入格式敏感，会把部分值误读成约 1/10
- 已新增 `trim_npt_float()`，确保 `.npt` 整数保留小数点

## 完整窗口结果

| case | scope | moved mean | tail_eta_max | tail_q_max | seg2 bias | seg222 bias | head bias | QIN mean | QEFF mean | QDT_SUM mean | QSS_SUM mean | TAIL_Q mean |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| bht_a00 | bht | 0 | 0.45645 | 10255 | 1.120442 | 0.149213 | 0.971229 | 4858.225460 | 4853.884803 | 154.24 | 897.914960 | 4829.287699 |
| bht_a100 | bht | 154.24 | 0.46499 | 10255 | 1.162380 | 0.148938 | 1.013442 | 5012.214830 | 5007.738403 | 0 | 743.466888 | 4982.371931 |
| all_a100 | all | 82.789002 | 0.59738 | 10255 | 1.243587 | 0.152591 | 1.090996 | 5351.201774 | 5346.337973 | 0 | 405.668304 | 5318.776385 |

## 最大 Q 残差定位

对三条完整窗口 `w2.wrn` 逐行扫描后，最大 `Q` 残差都发生在同一个启动初期接口事件：

```text
line 99
[V19_INTERFACE_RESIDUAL] JB=1 DETA=0.0000E+00 DQ=1.0255E+04
ETA_P=588.210 ETA_C=588.210 Q_P=7315.457 Q_C=15936.757
```

对应前序迭代链条为：

```text
ITER=1: QOUT=7624.849  -> Q guess=10239.914
ITER=2: QOUT=5682.252  -> Q guess=7624.849
ITER=3: QOUT=5682.252  -> Q guess=5682.252
ITER=4: QOUT=15936.757 -> Q guess=7315.457
```

三条 case 中这一段的关键差别只有 `QPHYS`：

- `bht_a00`: `QPHYS=5360.000`
- `bht_a100`: `QPHYS=5514.200`
- `all_a100`: `QPHYS=5514.200`

但最大残差对应的 `Q_P/Q_C/DQ` 完全相同。这说明 `tail_q_max=10255` 是启动初期 tailreach/interface 状态共同产生的尖峰，不是 distributed 迁移造成的 case-specific 水量路径差异。

## 链路判断

### 输入

移动动作已生效：

- `bht_a00`: `QDT_SUM mean = 154.24`
- `bht_a100`: `QDT_SUM mean = 0`
- `all_a100`: `QDT_SUM mean = 0`

同时 `QIN/QEFF` 随移动而抬高，说明不是脚本没有改到输入。

### 处理流程

移动 distributed 后，通量路径确实从库区内部源项转移到库尾/尾段侧：

- `QSS_SUM` 明显下降
- `QIN/QEFF/TAIL_Q` 明显上升

这符合物理预期，也说明 V22 诊断能看到上游边界和库区内源项的差别。

### 状态变化

水位响应存在，但方向不是修复：

- `bht_a100` 相对 baseline 抬高 `seg2/head` bias
- `all_a100` 抬高更明显，`tail_eta_max` 也变差

### 输出

关键输出没有改变：

- 三条完整窗口 `tail_q_max` 都是 `10255`

这说明 `tail_q_max` 的最大残差不是由 active distributed 是否放在 BHT 库尾这个单一因素控制。

### 上下游影响

`distributed` 仍然是重要水量补偿项，不能简单删除。它的位置会影响库区水位和内部分布源汇，但当前证据不支持把 `V21` 的最大接口流量残差归因于“BHT distributed 没有在库尾进入”。

## 当前结论

`V22` 固定了一个关键事实：

> moving distributed to the BHT tail changes the mass-entry path, but does not remove the V21 interface Q residual peak.

因此下一步应把注意力从输入流量路径转向接口求解本身，尤其是：

- `TAIL_Q_LINK` 初始高峰如何进入 `QEFF`
- `V21` reduced implicit solve 对 `Q` 的 step 限幅与残差定义
- `ETA` 和 `Q` 是否仍被近似成两个弱耦合的一维校正，而不是一个真正的二维界面问题
- 初始几轮 tailreach 体积/水位状态为什么会在 `QOUT=5682.252 -> 15936.757` 之间跳变

未验证前提：

- 当前结论只覆盖 `TMEND=44436.5` 的完整窗口。
- 还没有验证如果禁用 V21 的 Q secant update、只保留 ETA correction，`tail_q_max` 是否回落。
