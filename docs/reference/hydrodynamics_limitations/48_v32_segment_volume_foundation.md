# V32 Conservative Segment-Volume Foundation

本页回答什么问题：在引入多控制体连续方程之前，现有 `TAIL_VOL_SEG/AREA/HRAD` 是否真实表示 segment 2:5 的几何控制体，并且其体积和是否等于 V27 的守恒总 storage。

Updated: 2026-07-16

## 1. 发现的问题

V27 的真实守恒状态是 `TAIL_STORAGE_VOL`，由未缩放的 bathymetry/profile geometry 计算。现有 segment arrays 虽然也先按同一 stage profile 计算 area、hydraulic radius 和 volume，但 `UPDATE_TAIL_SEGMENT_TRANSITION` 随后又按 transition score 执行：

```text
AREA_SEG *= 1 - 0.18 * transition
HRAD_SEG *= 1 - 0.12 * transition
CELERITY *= 1 - 0.08 * transition
VOL_SEG   = AREA_SEG * DLX
```

这些缩放没有进入当前 V27 物理连续方程，只用于历史 V17 transition scaffold；但它使 `VOL_SEG` 不再是 bathymetry 控制体，不能作为后续逐段守恒状态的起点。

## 2. 最小正确改动

- 保留 transition score、submergence、local slope、Froude 和 mode 诊断；
- 删除 transition 对 `TAIL_AREA_SEG/HRAD_SEG/CELERITY_SEG/VOL_SEG` 的覆盖；
- segment geometry 始终保留 `TAIL_SECTION_PROPS` 和 `AREA*DLX` 的真实值；
- 接受步新增 `[V32_SEGMENT_VOLUME]`：

```text
VTOTAL = TAIL_STORAGE_VOL
VSEG   = sum(TAIL_VOL_SEG(1:NSEG))
VGAP   = VTOTAL - VSEG
```

V32 不新增持久物理状态，不改变 Q、stage profile、interface commit 或 reservoir consumer。

## 3. 链路检查

输入：V27 接受态 WUP/WDN、segment 2:5 bathymetry 和 cell length。

处理：在相同线性 profile stage 下逐 segment 计算 area、hydraulic radius 和 volume；transition 仅输出分类指标。

状态：`TAIL_STORAGE_VOL` 仍是唯一守恒总状态；segment arrays 是与它一致的可加几何分解。

输出：water-level output 仍来自同一 `TAIL_STAGE_SEG`，因此应保持完全不变。

上下游：无影响。

## 4. 验证

Short：

- 990 个 V32 接受步；
- `max|VTOTAL−sum(VSEG)|=0.00099947 m3`；
- SEG 2/SEG 222/head 指标与 V31 short 完全相同。

Extended：

- 5927 个 V32 接受步；
- `max|VTOTAL−sum(VSEG)|=0.0010273 m3`；
- V31 full-step residual `3.8835e-10 m3/s`，V24–V31 门禁继续通过；
- 18 项 Python tests、reduced build、完整 `assert_pass`：通过；
- computational warning `0`；
- `flowbal %VOLerror=-0.00005456%`。

外部指标与 V31 完全相同：

- SEG 2 bias/RMSE `-0.648357/1.257266 m`；
- SEG 222 bias/RMSE `0.160542/0.226510 m`；
- head bias/RMSE `-0.808898/1.326409 m`；
- SEG 2/head slope `0.000717/0.000614`。

## 5. 审视结论

V32 是无行为变化的状态语义修复。现在 segment 2:5 的每个 `VOL_SEG` 都是真实几何体积，且可加回唯一守恒总 storage；这满足实施 multi-control-volume continuity 的首要前提。

下一步不能简单让各段 Q 再次独立衰减，否则会重现 V24 发现的无 storage sink。最小正确方案必须同时定义：每个 cell 的持久 volume、每个内部界面的唯一 flux、逐 cell `dVi/dt=Qi−1−Qi`，以及所有 cell residual 求和后严格回到现有 branch-level V24/V31 identity。
