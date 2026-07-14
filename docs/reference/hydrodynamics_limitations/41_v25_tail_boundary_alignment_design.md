# V25 Tail Boundary Alignment Design

本页回答什么问题：V24 守恒闭合以后，为什么 SEG 2/head 的流量响应仍明显偏弱，以及 V25 在不引入新物理模型前应先修复哪个状态边界。

Updated: 2026-07-15

## 1. V24 剩余误差的证据

`TMEND=44436.5` 接受态输出显示：

- 观测 SEG 2 stage–Q 斜率为 `0.001844 m/(m3/s)`，模拟为 `0.000226`，约为观测的 `12%`。
- 观测 head–Q 斜率为 `0.001706 m/(m3/s)`，模拟为 `0.000117`，约为观测的 `6.9%`。
- SEG 2/head error 与物理入流相关系数分别为 `-0.9785/-0.9796`。
- SEG 222 的观测/模拟 stage–Q 斜率为 `0.000138/0.000108`，远比上游接近。

流量四分位中的 head bias 从低流量组的 `+2.163 m` 单调变到高流量组的 `-1.336 m`。因此剩余误差不是统一高程偏移，也不是单个启动异常；主缺口是 tail upper stage 的流量响应幅度。

## 2. 当前索引链

XLD branch 1 初始化得到：

```text
TAIL_DOMAIN_US = 2
TAIL_DOMAIN_DS = 5
TAIL_DOMAIN_NSEG = 4
TAIL_COUPLE_SEG = 6
CUSMIN = 3
```

主库区水动力从：

```text
IU = max(CUS, TAIL_COUPLE_SEG) = 6
```

开始求解。因此 segment 2–5 已由 tail domain 接管，segment 6 才是 reservoir 侧的首个活动接口段。

但当前初始化仍设置：

```text
TAIL_UPSEG = FRONT_SEG = 2
TAIL_DNSEG = CUSMIN = 3
```

`COMMIT_TAIL_INTERFACE` 和 `UPDATE_TAIL_STAGE` 随后读取 `ELWS(TAIL_DNSEG)`，所以使用的是未被 reservoir 主矩阵更新的 domain 内部 segment 3。V24 日志中 `WSE_DN` 和 `WSE_HYD` 全窗固定为 `588.210 m`，与该索引链一致。

## 3. 状态边界契约

对已定义的 multi-segment tail domain：

```text
tail state segments       = TAIL_DOMAIN_US : TAIL_DOMAIN_DS
reservoir interface stage = ELWS(TAIL_COUPLE_SEG)
TAIL_DNSEG                = TAIL_COUPLE_SEG
```

`TAIL_DNSEG` 表示 tail momentum/stage closure 的 downstream boundary，不应再表示旧的最小活动候选 `CUSMIN`。

standard-step 的能量损失距离也必须覆盖整个 tail domain：

```text
DX_REACH = sum(DLX(TAIL_DOMAIN_US:TAIL_DOMAIN_DS))
```

不能继续使用首尾两个断面的半长度之和。

## 4. 最小实施范围

- 初始化时先确定 `TAIL_COUPLE_SEG=TAIL_DOMAIN_DS+1`，再令 `TAIL_DNSEG=TAIL_COUPLE_SEG`。
- `TAIL_UPSEG` 使用 `TAIL_DOMAIN_US`；在当前案例仍等于 segment 2。
- standard-step residual 使用已经计算的 `TAIL_REACH_LENGTH`。
- 在 standard-step 调用前初始化 reach length，避免首步使用零或旧值。
- 不改变 V24 single-flux commit、可用水量上界和质量断言。
- 不加入任何经验 stage–Q 校正或非守恒流量衰减。

## 5. 验收链

输入/边界：

- `[V11_TAIL_DOMAIN] LINK_DN=6`，`[V15_TAIL_DOMAIN_MULTI] COUPLE=6`。
- `[V7_TAIL_STAGE] DNSEG=6`，`WSE_DN` 在接受窗口内不再被错误锁死于 segment 3 初值。

状态/守恒：

- `assert_v24_conservation` 继续通过。
- `RTAIL/RFLUX/RCOMB/SEGLOSS` 保持在 V24 容差内。

输出/影响：

- short window 无 runtime error，SEG 2/222 有效。
- 重新计算 SEG 2、SEG 222、head 的 bias/RMSE 和 stage–Q 斜率。
- 如果边界对齐后上游响应仍显著不足，再进入“profile volume + continuity”闭合；不提前宣称需要完整 Saint-Venant 子求解器。

## 6. 未验证前提

- 尚未运行 boundary-aligned 版本，无法确认 segment 6 stage 反馈对自动步长的净影响。
- 当前 standard-step 仍是上下游断面能量闭合，不返回逐段 profile volume；V25 只先消除已确认的错误边界，不把它包装成完整多段动力学。
- V10 日志包含可能被 autostep 回滚的试算状态；物理精度判断只使用正式 `wl.csv` 接受态。
