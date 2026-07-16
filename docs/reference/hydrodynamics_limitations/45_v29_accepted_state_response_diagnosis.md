# V29 Accepted-State Response Diagnosis

本页回答什么问题：V27 剩余的上游水位响应偏弱，究竟主要来自接受步流量状态滞后、可用水量限流、Manning 闭合偏差，还是来自储量剖面对上下游水位的响应链。

Updated: 2026-07-16

## 1. 原始问题与边界

V27 extended 已同时满足 tail 质量守恒、reservoir 接口通量一致、主水体体积平衡和 profile volume identity，但模拟/观测的 SEG 2 stage–Q slope 仍为 `0.000750/0.001844 m/(m3/s)`。

V28 已证伪“直接把 segment 2:6 断面摩阻作梯形积分即可修复响应”的假设。因此 V29 不改物理状态更新，只在所有 autostep rollback 检查之后记录真正接受的 tail 状态，避免把试算步混入诊断。

## 2. 链路检查

输入：物理入流 `QIN`、接受步长、tail committed Q、当前 hydraulic target、上下游水位和总 profile storage。

处理：

- 每个接受步写出 `[V29_ACCEPTED_TAIL]`；
- 记录 `QPHYS/QSTATE/QTARGET/QMAX/STORAGE/WUP/WDN`；
- 用 `+0.01 m` 数值扰动计算 `dV/dWup` 和 `dV/dWdn`；
- 用接受步长累计时间，不依赖低精度时间戳判断 hold duration；
- 在观测采样时刻把 segment 2→6 与 segment 6→222 的水头响应分解开。

状态：V29 不新增守恒状态，不改 `TAIL_STORAGE_VOL`、`TAIL_Q_LINK`、接口 commit 或 reservoir consumer。

输出：`v29_accepted_tail_samples.csv` 和 `v29_qstate_response_summary.csv`，均写入被 Git 忽略的 fresh run 目录。

上下游影响：已有 V24–V27 断言继续生效；smoke/scan 新增“至少存在一个接受步 marker”的门禁。

## 3. Extended 证据

Fresh `TMEND=44436.5` 共得到 `6010` 个接受步：

- `Qstate/Qphysical` slope `1.001734`，相关系数 `0.960788`；
- 最佳日尺度 response lag 为 `0.0 day`；
- available-water cap 仅触发 `1/6010` 次；
- predictor cache 使 `89.60%` 的相邻微步保持同一 Q，但最长连续保持仅 `0.030804 day`；
- `Qtarget/Qphysical` slope `1.005868`；
- 在当前 stage 下使 `Qtarget=Qstate` 所需的 `FMANN` 倍率中位数为 `0.999197`，P10/P90 为 `0.917768/1.069918`，`91.51%` 位于 `0.8–1.2`。

这些结果排除了两个简单解释：容量限流不是主要约束；固定 Manning 倍率也不是缺失响应的直接答案。当前摩阻闭合在绝大多数接受步已经围绕 committed Q 波动，整体调粗糙率只会制造新的系统偏移。

## 4. 水头与储量分解

接受步全样本：

- `WUP/Qphysical` slope `0.000736`；
- `WDN/Qphysical` slope `0.000804`；
- segment 2→6 local head slope `-0.0000679 m/(m3/s)`。

在 157 个观测采样时刻：

- 观测 SEG 2 slope `0.001844`；
- 接受态 WUP slope `0.000706`；
- 接口 WDN slope `0.000770`；
- segment 6→222 reservoir-head slope `0.000668`；
- segment 2→6 tail-head slope `-0.0000636`。

也就是说，当前模拟的总水头响应主要由 segment 6→222 提供，tail 自身反而抵消了一小部分。V29 没有 segment 6 的实测水位，因此不能把 tail/reservoir 两部分的物理归属当成已确认事实；但 SEG 2 与 SEG 222 的总缺口是已验证的。

剖面偏导均值为：

- `dV/dWup = 382,663 m2`；
- `dV/dWdn = 224,366 m2`；
- 固定 storage 时，`dWup/dWdn ≈ -0.588`。

实际 `storage/Qphysical` slope 为 `475.740 m3/(m3/s)`。由同一 profile chain 回代得到的 WUP slope 为 `0.000772`，与直接统计的 `0.000736` 同量级，说明诊断链闭合。若保持当前接口 WDN 响应而达到观测 WUP slope，所需 storage slope 约为 `878.411 m3/(m3/s)`；当前只有该需求的 `54.16%`。

## 5. 审视结论

V29 支持的最小结论是：V27 的弱上游响应主要表现为“随流量建立的 tail profile storage 不足以抵消下游边界对线性剖面的牵引”，而不是 Q cap 或一个固定 Manning 系数错误。

这仍然不是对根因的最终证明。缺少 segment 6 实测水位时，不能仅凭结果决定应修改 profile shape、Q-state 动态还是物理粗糙率。下一项无参数结构检查应先验证 predictor cache 是否改变接受态；缓存本应只影响性能，若关闭缓存会显著改变 storage/stage 结果，就说明数值捷径进入了物理状态路径。

## 6. 验证

- Python parser/statistics tests：通过；
- reduced console build：通过；
- fresh extended：正常退出，6010 个接受步；
- `max|RTAIL|=3.1105e-10 m3/s`；
- profile gap max `0.0011204 m3`；
- computational warning `0`；
- `flowbal %VOLerror=-0.00005456%`；
- V24–V27 所有 conservation/domain/profile 门禁继续通过。
