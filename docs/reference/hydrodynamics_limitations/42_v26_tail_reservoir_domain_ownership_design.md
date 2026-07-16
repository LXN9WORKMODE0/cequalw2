# V26 Tail–Reservoir Domain Ownership Design

本页回答什么问题：V25 已把 tail downstream stage 对齐到 reservoir segment 6，为什么主水体仍出现百万立方米级 volume error，以及下一步怎样用最小完整改动把同一接口的状态和通量语义统一起来。

Updated: 2026-07-16

## 1. 触发证据

V25 extended (`TMEND=44436.5`) 的 tail interface 自身满足：

```text
LINK_DN = COUPLE = 6
max|RTAIL| = 1.1642e-10 m3/s
max|RFLUX| = 0
SEGLOSS = 0
```

但主水体在 `JDAY=44430.0034` 报告：

```text
SPATIAL CHANGE  = -947755.54 m3
TEMPORAL CHANGE =  116524.66 m3
VOLUME ERROR    = -1064280.2 m3
```

因此问题不在 V24 的 tail-local continuity，而在接口之外仍有消费者使用另一套域或流量定义。

## 2. 已确认的分叉链

输入：

- 物理入流是 `QIN`，进入 tail continuity。
- committed interface flux 是 `TAIL_Q_LINK`，应进入 reservoir。

处理：

- reservoir hydrodynamic matrix 使用 `IU=max(CUS,TAIL_COUPLE_SEG)=6` 和 `TAIL_Q_LINK`。
- `CUS` 本身仍可为 `CUSMIN=3`；balance、部分 source/sink 循环和 water-level output 仍按 `CUS` 划分。
- `temperature.F90` 的 `TSS/TSSIN/VOLIN` 继续乘 `QIN`，与 hydrodynamic boundary velocity 使用的 `TAIL_Q_LINK` 不同。

状态：

- tail arrays 声称拥有 segment 2:5。
- reservoir 主矩阵只更新 segment 6+。
- 但全局 active-domain 状态仍可能把 segment 3:5 算作 reservoir，形成重叠/悬空所有权。

输出：

- 仅 `I<CUS` 的水位取自 tail arrays；当 `CUS=3` 时，segment 3:5 输出仍取未由 reservoir 主矩阵正常推进的 `ELWS`。
- branch volume balance 使用另一域起点和另一 inflow，不能证明 reservoir 或全系统守恒。

## 3. V26 所有权契约

当 `TAIL_DOMAIN_DEFINED(JB)`：

```text
tail-owned state       = TAIL_DOMAIN_US : TAIL_DOMAIN_DS   (2:5)
reservoir-owned state  = TAIL_COUPLE_SEG : DS              (6:DS)
active CUS             = TAIL_COUPLE_SEG                    (6)
physical tail inflow   = QIN
reservoir boundary Q   = TAIL_Q_LINK = TAIL_RESERVOIR_Q_USED
```

契约要求：

- hydrodynamics、temperature/volume boundary、branch balance 和 output 用相同 active-domain 起点。
- reservoir 的所有水量消费者使用同一 committed interface flux。
- tail continuity 继续单独核算 `QIN-Qinterface`；不把 physical `QIN` 同时注入 reservoir。
- 不通过修改 `VTOL`、关闭 `VOLUME_WARNING` 或忽略启动期来消除报警。

## 4. 最小实施

1. 初始化 tail domain 后，将 active `CUS` 设置为 `TAIL_COUPLE_SEG`；保留 `CUSMIN` 只作为原始湿润候选/诊断，不再作为 reservoir 所有权边界。
2. `layeraddsub` 的 upstream lock 不允许 `IUT` 回退到 tail domain 内；已定义 tail 时下界为 `TAIL_COUPLE_SEG`。
3. water-level output 因 `I<CUS` 自动从 tail arrays输出完整 2:5。
4. `temperature.F90` 为 upstream boundary 计算唯一的 reservoir inflow；tail valid 时使用 `TAIL_RESERVOIR_Q_USED`，否则使用 `QIN`。同一值用于 `TSS`、`TSSIN` 和 `VOLIN`。
5. 新增可解析诊断，证明 `CUS=COUPLE=6` 且 temperature/volume boundary 使用 committed Q。
6. 保持 V24 single-flux、available-water cap 和 V25 boundary alignment 不变。

## 5. 验收链

输入：物理 `QIN` 与 committed `Qinterface` 同时保留，二者差值只能进入 tail storage。

处理：

- `CUS=TAIL_COUPLE_SEG=6`。
- reservoir hydro/temperature/volume boundary Q 相等。
- main branch balance 不再包含 tail-owned segment 2:5。

状态：

- V24 `RTAIL/RFLUX/RCOMB/SEGLOSS` 继续在 `1e-6` 容差内。
- V25 `LINK_DN=COUPLE` 继续成立。

输出：

- `wl.csv` 中 segment 2:5 均来自有效 tail state，segment 6+ 来自 reservoir `ELWS`。
- short window 不含 runtime error 或 computational warning。
- `flowbal.csv` volume error 回到既有容差范围。

上下游影响：

- upstream forcing 文件和 physical `QIN` 不改。
- reservoir 的热量/质量入口通量将与水动力水量通量一致；这可能改变温度/水质结果，是纠正同一水体体积与标量通量不一致的必需影响，不是额外业务扩展。
- 本步不改变 tail lumped storage 的物理形式；profile-volume/continuity 仍是后续独立重构。

## 6. 未验证前提

- 需要编译和 short run 验证把 `CUS` 提到 6 不会触发 layer add/sub 的其他历史路径。
- 当前仅确认 upstream temperature/`VOLIN` 直接使用 raw `QIN`；若运行诊断显示还有其他 reservoir boundary consumer 分叉，再按同一契约收口，不新增替代通量。
- V25 的百万立方米 volume error 很可能由域/通量分叉共同导致；在 V26 运行前，不能把其中某一项单独表述为唯一根因。
