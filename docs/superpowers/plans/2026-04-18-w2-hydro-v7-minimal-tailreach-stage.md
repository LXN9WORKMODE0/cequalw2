# V7 最小尾段水位闭环计划
本页回答什么问题：在 `V6` 之后，怎样用最小改动把 protected tailreach 从“只有耦合诊断”推进到“`SEG 2` 能输出真实可对比水位”的第一版闭环。

Updated: 2026-04-18

## 目标

- 让 `SEG 2` 在 `wl.csv` 中不再是 `-999`。
- 保持 `V0-V6` 已有 smoke 稳定性，不把主求解器重新拉回失稳状态。
- 优先形成双站点验证能力，而不是一步到位重写完整 1D Saint-Venant 子模型。

## 范围

- 在 `w2_main.f90` 增加最小尾段水位求解器，只求 `TAIL_UPSEG -> TAIL_DNSEG` 的局部 stage。
- 在 `outputa2w2tools.F90` 对 `wl.csv` 增加 protected tailreach override。
- 在 smoke harness 中把“`SEG 2` 有有效水位”提升为硬验收条件。

## 任务

1. 先把 smoke harness 改成红灯。
2. 在 `GLOBAL` 中增加尾段 stage 有效性和模式状态量。
3. 在 `w2_main.f90` 落一个最小尾段 stage 计算：
   - 用 `QC(TAIL_DNSEG)` 作为链接流量。
   - 用 `ELWS(TAIL_DNSEG)` 作为下游边界水位。
   - 用局部断面几何 + Manning/标准步思路给出 `TAIL_WSE_UP`。
   - 加入物理范围保护，避免 stage 爆炸。
4. 在 `outputa2w2tools.F90` 输出 `TAIL_WSE_UP` 到 `SEG 2`。
5. 重新跑短窗、延长窗、长窗三组验证。

## 验收

- `smoke-summary` 必须包含 `[V7_TAIL_STAGE]`。
- `seg2_valid_count > 0`，且短窗、延长窗、长窗都成立。
- `has_runtime_error = 0`，`has_late_seg2_add = 0`。
- 长窗中 `SEG 2` 与 `SEG 222` 都能进入双站点误差计算。

## 非目标

- 这版不把尾段 stage 反馈回主水动力矩阵。
- 这版不尝试完整 1D 动波。
- 这版不承诺立刻把 `SEG 2` RMSE 调到工程可接受范围。
