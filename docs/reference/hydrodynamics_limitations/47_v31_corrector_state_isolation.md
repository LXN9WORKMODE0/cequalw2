# V31 Corrector State Isolation

本页回答什么问题：predictor/corrector 是否把 tail storage 在同一 W2 时间步推进两次，以及 corrector 应从哪一组状态开始重算。

Updated: 2026-07-16

## 1. 初始假设与更正

初次代码审查看到：

1. 步初调用 `SAVE_TAIL_DYNAMIC_STATE`；
2. predictor 调用 `UPDATE_TAIL_STAGE`；
3. reservoir 求解后，corrector 再调用一次 `UPDATE_TAIL_STAGE`。

这表面上像是同一时间步推进两次。V31 short 通过后，extended 的 stage/storage 结果却与 V30 逐项相同。沿 save/restore 逐变量复核后，初始“双推进持久储量”假设被证伪：`RUN_TAIL_PREDICTOR` 在试算结束时先完整恢复步初 tail state，随后只复制 predictor 的 `WUP/Qlink/depth/segment-derived arrays`，并没有复制 `TAIL_STORAGE_VOL`、`TAIL_Q_STATE` 或 `TAIL_Q_TARGET`。

因此旧代码的实际状态是：

- reservoir 使用 predictor 给出的接口 stage/Q；
- corrector 调用前，persistent storage/Q state 仍是步初值；
- 但全局 `WUP/Qlink` 已是 predictor 值，形成“步初持久态 + predictor 派生态”的混合输入。

这不是 storage 双推进，但状态所有权不清晰，且会使 corrector 的第一个 hydraulic target 依赖 predictor 派生态。

## 2. 最小正确改动

第二次 `HYDROINOUT` 和 reservoir 求解完成后、逐 branch 调用 `COMMIT_TAIL_INTERFACE` 之前，统一执行一次 `RESTORE_TAIL_DYNAMIC_STATE`。

该 restore：

- 把 corrector 的 WUP/Qlink/storage/Q state/segment arrays 全部恢复到同一个步初快照；
- 不恢复 `TAIL_IFACE_ETA_PRED/TAIL_IFACE_Q_PRED`，所以 predictor 接口证据仍可用于 residual 诊断；
- 不恢复 `TAIL_RESERVOIR_Q_USED`，所以 corrector 仍强制采用 reservoir 实际消费的 committed Q；
- 对所有 branch 只执行一次，避免逐 branch restore 擦除已经完成的 corrector。

## 3. 整步身份门禁

在 autostep rollback 检查之后，只对真正接受且步初已初始化的 tail 状态写出：

```text
[V31_SINGLE_STEP] JB=... VPRE=... VFINAL=... RATE=... RTAIL=... RATEGAP=...
```

定义：

```text
RATE    = (Vfinal - Vpre) / dt
RTAIL   = RATE - (Qphysical - Qinterface)
RATEGAP = RATE - TAIL_STORAGE_CHANGE_RATE
```

初始化步不参与该门禁，因为其步初 storage 尚不存在；试算失败步也不会进入 marker。

## 4. 链路检查

输入：步初 tail snapshot、predictor interface stage/Q、reservoir committed Q。

处理：reservoir 继续使用 predictor；corrector 从完整步初 tail snapshot 以 committed interface 条件重算一次。

状态：没有新增物理状态；新增的 full-step rate/residual 只是接受态诊断。

输出：V24 local mass identity 继续保留，V31 再证明它与整个接受步的 `Vfinal−Vpre` 相同。

上下游：reservoir matrix 与 temperature/volume boundary consumers 不变。

## 5. 验证与不变性结果

Short：

- 989 个 V31 接受态样本；
- `max|RTAIL_full|=3.8835e-10 m3/s`；
- `max|RATEGAP|=0`。

Extended：

- 5926 个 V31 样本；
- `max|RTAIL_full|=3.8835e-10 m3/s`；
- `max|RATEGAP|=0`；
- 17 项 Python tests、reduced build、完整 `assert_pass` 和 V24–V31 独立门禁全部通过；
- profile gap max `0.0010486 m3`；
- computational warning `0`；
- `flowbal %VOLerror=-0.00005456%`。

对外水位指标与 V30 相同：

- SEG 2 bias/RMSE `-0.648357/1.257266 m`；
- SEG 222 bias/RMSE `0.160542/0.226510 m`；
- head bias/RMSE `-0.808898/1.326409 m`；
- SEG 2/head slope `0.000717/0.000614`。

只有内部 target 诊断发生小变化：`Qstate–Qtarget` RMSE 从约 `108.12` 降到 `99.80 m3/s`。这符合“移除 corrector 混合派生态”的预期，但不构成精度修复。

## 6. 审视结论

V31 固定的是状态隔离契约，并同时记录了对初始双推进判断的更正。当前剩余精度缺口不能归因于 corrector 重复累计 storage。源汇、单步连续方程、Q target 和 fixed Manning 也已基本排除；下一步若继续改变模型，应针对单一线性 profile/单控制体表达能力，而不是再调整 predictor/corrector 次序。
