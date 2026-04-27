# V14 Stronger Coupled Hybrid 实现记录
本页回答什么问题：`V14` 如何把 tailreach 从“步后处理的弱耦合对象”推进成“时步内 predictor/corrector 的强耦合对象”，以及这种更强耦合是否继续改善了双站点结果。

Updated: 2026-04-20

## 1. 这版的定位

到 `V13` 为止，tailreach 已经具备：

- fixed physical domain
- discharge state
- internal transition state

但它仍然主要是：

- 主库区先完整求解
- 然后 tailreach 在步后更新一次

也就是说，tailreach 虽然已经开始影响主库区，但还没有真正作为“同一步内的耦合对象”参与进去。

`V14` 的目标就是补上这一层：

- 在同一时间步内，先做 tail predictor
- 让主库区吃到这个 predictor
- 主解之后再做 tail corrector
- 如果 autostep 拒绝该时间步，则 tail 状态跟着一起 rollback

## 2. 新增的核心机制

### 2.1 predictor / corrector 顺序

当前 `V14` 的时步顺序变成了：

1. `CALL HYDROINOUT`
2. `CALL SAVE_TAIL_DYNAMIC_STATE()`
3. `CALL RUN_TAIL_PREDICTOR()`
4. 主库区 W2 水动力求解
5. `CALL UPDATE_TAIL_STAGE(...)` 作为 corrector/commit
6. 如果 timestep 被拒绝，`CALL RESTORE_TAIL_DYNAMIC_STATE()`

这意味着 tailreach 终于不是单纯“上一时步遗留边界 + 本时步步后处理”的关系了。

### 2.2 rollback-safe tail state

新增了动态 tail state 的本地备份和恢复逻辑，覆盖的内容包括：

- `TAIL_WSE_UP/DN`
- `TAIL_Q_LINK`
- `TAIL_DEPTH_UP`
- `TAIL_STORAGE_VOL`
- `TAIL_Q_STATE`
- `TAIL_Q_TARGET`
- `TAIL_TRAVEL_TIME`
- `TAIL_WAVE_CELERITY`
- `TAIL_REACH_LENGTH`
- `TAIL_TRANSITION_STATE`
- `TAIL_SUBMERGENCE`
- `TAIL_LOCAL_SLOPE`
- `TAIL_FROUDE`
- 以及相关 mode / valid / initialized flags

这一步很重要，因为到了更强耦合阶段，如果 timestep 被拒绝而 tail state 不回滚，后面会越来越不一致。

## 3. 代码位置

主要实现都在：

- [w2_main.f90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/w2_main.f90:210)
- [w2_main.f90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/w2_main.f90:1399)
- [w2_main.f90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/w2_main.f90:1526)
- [w2_main.f90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/w2_main.f90:1719)

新增的 smoke 门槛在：

- [run_w2_v0_v1_smoke.py](/C:/Users/NING/Desktop/v455/analysis/run_w2_v0_v1_smoke.py:1)

## 4. 新增诊断

新增 marker：

- `[V14_COUPLED_HYBRID]`

它会在两个 pass 都输出：

- `PASS=1, COMMIT=F`：predictor
- `PASS=2, COMMIT=T`：corrector

从长窗日志看，`PASS=1` 和 `PASS=2` 都出现了，说明这一步不是形式上的改动，而是实际进了运行链路。

## 5. smoke 验证

通过结果：

- 短窗：[smoke-summary-20260420-192004.csv](/C:/Users/NING/Desktop/v455/analysis/verification/w2_v0_v1_smoke/results/smoke-summary-20260420-192004.csv)
- 延长窗：[smoke-summary-20260420-192109.csv](/C:/Users/NING/Desktop/v455/analysis/verification/w2_v0_v1_smoke/results/smoke-summary-20260420-192109.csv)
- 长窗：[smoke-summary-20260420-192947.csv](/C:/Users/NING/Desktop/v455/analysis/verification/w2_v0_v1_smoke/results/smoke-summary-20260420-192947.csv)

三组都满足：

- `has_v14_coupled_hybrid = 1`
- `has_runtime_error = 0`
- `seg2_valid_count > 0`
- `seg222_valid_count > 0`

## 6. 长窗结果

`44430-44458`：

- `SEG 2 RMSE = 4.957`
- `SEG 2 Bias = -4.403`
- `SEG 222 RMSE = 0.793`
- `SEG 222 Bias = -0.602`
- `SEG 2 - SEG 222 RMSE = 4.280`
- `SEG 2 - SEG 222 Bias = -3.800`

与 `V13` 相比：

- `SEG 2` 继续略有改善
- `SEG 222` 继续保持
- `DIFF` 继续略有改善

这说明：

- `V14` 并不是一次巨大跳变
- 但 stronger hybrid coupling 继续把结果往对的方向推了一小步

## 7. 这一版最重要的意义

`V14` 的最大意义其实不是某个 RMSE 数字，而是：

- tailreach 终于具备了时步内 predictor/corrector 参与能力
- tail dynamic state 终于和 reservoir state 一样具备 rollback 语义

这意味着 Hybrid Tailreach 已经从：

- “弱耦合外挂”

进一步变成：

- “有时步内交互的 hybrid 子系统”

## 8. 还没有做到什么

即便到了 `V14`，仍然还有两个明显缺口：

1. 还没有完整的 1D momentum equation
2. 还没有真正的多断面 tailreach propagation

所以 `V14` 仍然不是终局版本，它只是把“耦合顺序和数值语义”补强了。

## 9. 当前阶段结论

如果把 `V11-V14` 放在一起看，当前阶段已经完成了这条链：

- `V11`: fixed tail domain
- `V12`: discharge state with memory
- `V13`: internal transition-state logic
- `V14`: same-step stronger coupling + rollback

这意味着：

第二阶段的基础骨架已经基本齐了。

后面如果继续深推，就会越来越接近：

- 更完整的 local 1D reach solver

而不是继续在“外挂 patch”层面打转。
