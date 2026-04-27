# V20 Interface Iteration Implementation

本页回答什么问题：`V20` 是否已经把 `V19` 暴露出来的接口残差推进成同一步内的 interface iteration，以及这一步在当前代码结构下究竟做到什么程度。

Updated: 2026-04-24

## 这一步实际做了什么

`V20` 没有直接把整个 reservoir 主求解器改成多次重算，而是先在当前 W2 结构下实现了一版“固定 reservoir 侧接口水位、在 tailreach 侧做同一步内界面 guess 迭代”的强耦合近似。

本次实际新增了：

- 在 `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\w2modules.F90` 中加入：
  - `TAIL_IFACE_ITER_COUNT`
  - `TAIL_IFACE_CONVERGED`
  - `TAIL_IFACE_RELAX`
  - `TAIL_IFACE_MAX_ITERS = 4`
  - `TAIL_IFACE_ETA_TOL = 0.01`
  - `TAIL_IFACE_Q_TOL = 10`
  - `TAIL_IFACE_RELAX_MIN/MAX`
- 在 `input.F90` 和 `init.F90` 中完成这些状态的分配与初始化。
- 在 `w2_main.f90` 中把原来单次 corrector 的：
  - `CALL UPDATE_TAIL_STAGE(JB, JW)`

  改成：

  - `CALL RUN_TAIL_INTERFACE_ITERATION(JB, JW)`

  由它在同一步内做最多 4 次界面迭代。

## 求解逻辑现在是什么

当前 `V20` 的界面迭代逻辑是：

1. `RUN_TAIL_PREDICTOR()` 给出 predictor 界面 guess。  
2. reservoir 主库区仍按当前 W2 主链只解一次。  
3. hydro 解完以后，`RUN_TAIL_INTERFACE_ITERATION()` 固定 reservoir 侧真实接口水位 `ELWS(TAIL_DNSEG)`。  
4. tailreach 侧用当前 `ETA/Q` guess 作为界面猜测，反复：
   - 恢复该 branch 的 tail 基态
   - 用 guess 重新推进 tailreach
   - 计算 `DETA/DQ`
   - 用 under-relaxation 更新下一轮 guess
5. 若 `|DETA| < ETA_TOL` 且 `|DQ| < Q_TOL`，则认为该步界面迭代收敛。

所以这一步的本质是：

- 已经不是 `V18` 的 one-pass predictor/corrector
- 但也还不是“reservoir + tailreach 在同一步内一起多次重算”的完整强耦合

更准确地说，它是：

**固定 reservoir 侧背景解的 tail-side interface iteration。**

## 新增诊断

新 marker 为：

```text
[V20_INTERFACE_ITER] JB=... ITER=... DETA=... DQ=... RELAX=... CONV=...
```

对应 smoke harness 里新增：

- `has_v20_interface_iter`
- `tail_iface_iter_max`
- `tail_iface_iter_converged_count`

## 调试与验证

### 1. 红灯确认

在 harness 里先加入 `V20` gate 后，对现有 case 重评估，确认得到：

- `has_v19 = 1`
- `has_v20 = 0`

也就是红灯确实只缺 `V20_INTERFACE_ITER`，不是别的 marker。

### 2. 编译

重新构建成功：

- `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\build_console\w2_v455_console.exe`

### 3. 新鲜扩展窗验证

实际 fresh rerun 的验证窗是：

- `TMEND = 44436.5`

结果文件：

- `C:\Users\NING\Desktop\v455\analysis\verification\w2_v0_v1_smoke\results\smoke-summary-20260424-131047.csv`

关键字段：

- `missing_markers = 空`
- `has_runtime_error = 0`
- `has_v19_interface_residual = 1`
- `has_v20_interface_iter = 1`
- `tail_iface_resid_max_eta = 0.81905`
- `tail_iface_resid_max_q = 1985.8`
- `tail_iface_iter_max = 4`
- `tail_iface_iter_converged_count = 441651`
- `seg2_valid_count = 66`
- `seg222_valid_count = 66`

这说明三件事：

1. `V20` marker 已经真实进入运行链。  
2. `V20` 不是只跑 1 次，它确实会用满 4 次上限。  
3. 在大量时间步里，界面迭代最终能打到当前定义下的收敛条件。

## 当前效果怎么理解

和 `V19` 相比，这一步最直接的变化是：

- `tail_iface_resid_max_eta` 从 `1.3552` 降到了 `0.81905`
- `tail_iface_resid_max_q` 从 `5851.6` 降到了 `1985.8`

所以从“界面 guess 与 corrector 结果的最终不一致量级”看，`V20` 是有效的。

但也要诚实说明：

- 这一步还不是全量隐式界面求解
- 它降低的是 tail-side 界面残差
- 还没有证明主库区的时间步刚性已经根本解决

## 这一步的边界

`V20` 现在的强项是：

- 把接口 mismatch 从单次 handoff 推进成了显式的多次界面修正
- 不用重写主水面矩阵就能先验证“界面收敛”这条路线

`V20` 现在的上限也很明确：

- reservoir 主库区在同一步里仍然只解一次
- 所以它还不是“真正的双向同一步收敛”
- 更像是朝 `V21` 低维隐式界面校正迈出的中间层

## 当前结论

`V20` 可以记成：

- 功能上已落地
- fresh 扩展窗 smoke 已通过
- 界面残差量级明显缩小
- 但求解结构仍然是“single reservoir solve + tail-side interface iteration”

因此，`V20` 是一个成立的中间版本，但还不是最终成熟形态。  
它已经足够支撑下一步进入 `V21`：把当前的界面更新从 under-relaxed fixed-point 继续推进到低维 secant / quasi-Newton 风格的 reduced implicit correction。
