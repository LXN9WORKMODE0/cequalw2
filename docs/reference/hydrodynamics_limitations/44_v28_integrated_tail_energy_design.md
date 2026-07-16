# V28 Integrated Tail Energy Design

本页回答什么问题：V27 已闭合总储量和域所有权后，为什么 SEG 2/head 的 stage–Q 响应仍只有观测约四成，以及怎样在不改 Manning 参数的情况下，让 momentum closure 真正使用 segment 2:6 的中间断面。

Updated: 2026-07-16

## 1. 触发证据

V27 extended：

- 模拟/观测 SEG 2 stage–Q slope 为 `0.000750/0.001844 m/(m3/s)`；
- 模拟/观测 head slope 为 `0.000648/0.001706`；
- error–Q correlation 仍为 `-0.9500/-0.9408`；
- 试算态 `WSE_HYD` 的 slope 约 `0.000680`，与接受态同样偏弱。

因此剩余缺口不是 storage inversion 独有。当前 `TAIL_STANDARD_RESIDUAL` 只取 segment 2 和6 的 friction slope 平均后乘全长；`COMPUTE_TAIL_LINK_FLOW` 更只使用 segment 2 conveyance 和总体水面坡度。segment 3:5 的实际断面与摩阻没有进入能量损失。

## 2. 最小物理闭合

保持 V27 的线性距离 profile 和总储量不变。对 profile center `i=2:6`：

```text
Sf_i(Q) = [Q * fmanning_i / (A_i * R_i^(2/3))]^2
dx_i   = 0.5 * [DLX(i) + DLX(i+1)]
hf(Q)  = sum_{i=2..5} 0.5 * [Sf_i(Q) + Sf_{i+1}(Q)] * dx_i
```

能量 residual：

```text
Renergy = (WSE_up + V_up^2/2g) - (WSE_dn + V_dn^2/2g + hf)
```

由于固定 stage/profile 下 `Sf` 与 velocity head 都正比于 `Q^2`，可写成：

```text
Renergy = delta_stage - Q^2 * (K_friction - K_velocity)
Qeq     = sqrt(delta_stage / (K_friction - K_velocity))
```

这使 standard-step 的“已知 Q 求 WSE_up”和 link-flow 的“已知 stages 求 Q”严格共享同一个能量式。

## 3. 链路检查

输入：V27 profile stages、各断面 area/hydraulic radius、原始 Manning/friction 输入。

处理：

- 遍历 segment 2:6；
- 按 center spacing 梯形积分 friction slope；
- endpoint velocity head 只计 segment 2/6；
- denominator 非正时返回未闭合状态并由硬诊断暴露，不使用旧 upstream-only 公式兜底。

状态：不新增守恒状态，不改 `TAIL_STORAGE_VOL`、`TAIL_Q_LINK` 或 interface commit 语义。

输出：新增 `[V28_ENERGY_CLOSURE]`，用由同一系数反演出的 `Qeq` 回代能量 residual。

上下游：physical inflow、reservoir matrix、temperature/volume boundary consumer 均保持 V27 contract。

## 4. 验收

- V24–V27 所有门继续通过。
- `Qeq` 回代的 `max|Renergy|` 在数值容差内。
- 无 runtime/computational warning，主水体 volume error 保持 V27 量级。
- short/extended 对比 stage–Q slope 和三站 RMSE；不以单个 slope 改善换取守恒或明显 RMSE 退化。

## 5. 未验证前提

- 线性 stage profile 只用于在中间断面取几何；它还不是逐段 standard-step 解。若积分摩阻有效但仍不足，下一步才迭代 profile 本身。
- friction integration 可能因中间窄断面显著降低相同 stage difference 下的 Q，从而提高上游响应；方向是物理推断，运行前不视为已确认。
- 本步不做 Manning 校准。若结构闭合后仍需决定摩阻率定范围或拟合权重，那将是需要用户给出物理/验收偏好的决策点。

## 6. Short-window result — rejected

实现后的能量回代在 20 个样本上全部 valid，最大 residual `1.7764e-15 m`；V24–V27 的 mass/domain/profile/volume 门也继续通过。因此 V28 的数值实现本身闭合。

但当前 geometry 下，中间断面总体比 upstream endpoint 更具输水能力，积分后的 `Qeq` 多次达到约 `12000–24000 m3/s`。结果是：

- SEG 2/head slope 从 V27 的 `0.000673/0.001000` 提高到 `0.001229/0.001561`；
- 同时 bias 变为 `-3.453268/-3.641449 m`；
- RMSE 从 `1.059306/1.243497 m` 恶化到 `3.531463/3.739521 m`。

这说明 slope 改善由过强排水造成，不能接受。V28 在 short gate 止损，没有运行 extended，源码恢复到 V27；本页作为已否证方案保留，避免后续重复尝试相同集成方式。
