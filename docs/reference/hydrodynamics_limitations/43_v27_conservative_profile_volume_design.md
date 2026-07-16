# V27 Conservative Profile-Volume Design

本页回答什么问题：V26 已建立 tail 2:5 与 reservoir 6+ 的独占所有权后，为什么上游水位在 short window 内下降过快，以及怎样在不直接引入四个独立界面流量的前提下，建立最小闭合的总河段储量模型。

Updated: 2026-07-16

## 1. 触发证据

V26 short 满足接口和主水体守恒，但：

- SEG 2/head RMSE 为 `2.912052/3.021638 m`；
- 到 `JDAY=44431` 的最小误差约为 `-8.70/-8.84 m`；
- 模拟 SEG 2/head stage–Q slope 达到 `0.002824/0.003135 m/(m3/s)`，已略高于观测 `0.002237/0.002700`。

代码链显示 `TAIL_STORAGE_VOL` 仍由：

```text
TAIL_VOLUME_FROM_STAGE(TAIL_UPSEG, WSE_UP)
```

计算，即只包含 segment 2 的 `area * DLX`。但同一个 storage state 承担整个 tail-owned domain 2:5 的 `Qphysical-Qinterface`。在 V26 消除重叠 reservoir volume 后，这个过小的等效储量直接表现为过强水位变化。

## 2. 状态契约

V27 保留一个低维 reach state：

```text
dynamic storage = sum(volume of tail-owned segments 2:5)
dynamic flux    = one committed tail/reservoir interface Q
boundary stage  = reservoir ELWS at segment 6 center
reported stages = one internally consistent profile over segment 2:5
```

不在本步引入：

- segment 之间互不相同的四个 Q；
- 经验 Q attenuation；
- 为拟合 bias 添加的 stage offset；
- 新的摩阻参数。

## 3. 几何映射

stage 定义在 segment center。对相邻 segment `i` 与 `i+1`：

```text
dx_center = 0.5 * (DLX(i) + DLX(i+1))
```

当前案例 segment 2 center 到 segment 6 center 的距离为：

```text
0.5*DLX2 + DLX3 + DLX4 + DLX5 + 0.5*DLX6 = 3855 m
```

这取代 V25/V26 的 tail cell-length sum `3770 m`，使 momentum distance 与 stage endpoints 的位置语义一致。

对 tail cell center `i=2:5`：

```text
fraction(i) = distance(center 2, center i) / distance(center 2, center 6)
stage(i)    = WSE_up + fraction(i) * (WSE_dn - WSE_up)
```

profile volume：

```text
Vprofile(WSE_up,WSE_dn) = sum_i Area_i(stage(i)) * DLX_i
```

## 4. 处理链

输入：physical `QIN`、committed `Qinterface`、reservoir boundary `WSE_dn`、旧总储量。

处理：

1. 用 `Vnew = Vold + dt*(QIN-Qinterface)` 更新总储量。
2. 对给定 `WSE_dn`，用单调二分反演 `Vprofile(WSE_up,WSE_dn)=Vnew`。
3. 用同一个距离 fraction 构造 segment 2:5 stage/area/volume 输出。
4. available-water cap 使用同一 profile 的最小可行总储量，不再使用 segment 2 单元体积。
5. predictor cache recheck 和 matrix 前 re-cap 使用同一个最小储量函数。

状态变化：只有总 `TAIL_STORAGE_VOL` 和既有 interface Q 是守恒状态；segment arrays 是由接受态 profile 唯一派生的视图。

输出：新增 `[V27_PROFILE_STORAGE]`，记录 scalar storage、由输出 profile 重算的 volume 和二者 gap。

## 5. 验收

- V24 interface conservation、V25 boundary alignment、V26 domain ownership 三组断言继续通过。
- 无 runtime/computational warning；`flowbal` 保持 V26 量级。
- `max|TAIL_STORAGE_VOL - sum(profile cell volumes)|` 在数值反演容差内。
- `TAIL_REACH_LENGTH=3855 m`。
- short window 的 SEG 2/head 过度下降应明显减弱；即使精度未改善，也不得回退 V26 所有权或 V24 single-flux。

## 6. 上下游影响与未验证前提

上游 forcing 与 physical `QIN` 不变。reservoir 仍只接收 committed interface Q。温度仍以同一个 Q 进入 reservoir；V27 暂不求解 tail 内温度滞后。

未验证：

- 线性距离 profile 是闭合低维几何，不是完整 standard-step profile；如果总储量闭合后仍有系统性 profile 误差，再把 profile 生成器替换为逐段能量积分。
- downstream stage 快速上升可能使最小可行 profile volume 上升；V24 mass residual 会检测任何未经通量解释的强制加水，不能静默 clamp。
- short 通过后仍需 extended window 才能接受 V27 为新基线。

## 7. Short-window result

V27 fresh short (`TMEND=44431`) 已通过全部结构门：

- profile storage identity 最大 gap `0.0011204 m3`；
- center-distance reach length 始终为 `3855 m`；
- tail/combined residual 最大 `7.0031e-11 m3/s`；
- reservoir、temperature、volume 与 tail committed flux gap 均为 0；
- computational warning 为 0，`flowbal %VOLerror=-0.00005456%`。

SEG 2/head RMSE 从 V26 的 `2.912052/3.021638 m` 改善到 `1.059306/1.243497 m`，证实 total profile volume 是必要结构修复。与 V25 short 相比仍分别高 `0.107128/0.069053 m`，但 V25 存在 `-127.24%` 主水体 volume error，不能作为物理精度基线。

首次试算中旧的 `WSE_up <= WSE_dn+25 m` cap 造成 `6.96e6 m3` stage/volume gap；移除该无守恒含义的接受态 cap 后，profile identity 恢复并由 autostep 正常处理高水位试算。
