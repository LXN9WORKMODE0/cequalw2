# V21 Reduced Implicit Interface Implementation

本页回答什么问题：`V21` 是否已经把 `V20` 的 under-relaxed fixed-point 界面更新推进成低维的 reduced implicit correction，以及这一步在 fresh 验证里带来了什么、又没有带来什么。

Updated: 2026-04-24

## 这一步实际做了什么

`V21` 的目标不是重写整个 reservoir 主矩阵，而是在当前 `V20` 的 interface iteration 里，把简单的：

- `ETA_GUESS = ETA_GUESS + RELAX * DETA`
- `Q_GUESS   = Q_GUESS   + RELAX * DQ`

推进成一个更接近 secant / quasi-Newton 的低维界面校正。

本次新增了这些界面状态：

- `TAIL_IFACE_ETA_GUESS / Q_GUESS`
- `TAIL_IFACE_ETA_PREV / Q_PREV`
- `TAIL_IFACE_DETA_STEP / DQ_STEP`

对应文件：

- [w2modules.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/w2modules.F90:154)
- [input.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/input.F90:324)
- [init.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/init.F90:66)

## 求解逻辑现在怎么变了

`V20` 里，每轮界面迭代的更新还是纯松弛。

`V21` 里，我保留了 `V20` 的收敛判据和最大迭代数，但把更新方式改成了：

1. 先计算当前界面残差 `DETA / DQ`
2. 同时保留上一轮的：
   - `ETA_PREV_GUESS / Q_PREV_GUESS`
   - `DETA_PREV / DQ_PREV`
3. 如果历史信息不足，就退回 `RELAX * residual`
4. 如果历史信息足够，就分别对 `ETA` 和 `Q` 使用一维 secant 风格更新
5. 为了避免爆步，再对 secant step 做局部裁剪

所以这一步的本质是：

- 还不是完整 Jacobian-based implicit solve
- 但已经不再只是 fixed-point under-relaxation
- 它是一个真正的 reduced implicit / secant-style interface correction

新 marker 为：

```text
[V21_INTERFACE_SOLVE] JB=... ITER=... DETA_STEP=... DQ_STEP=... ETA=... Q=...
```

## 红灯确认

在 harness 里先加入：

- `has_v21_interface_solve`
- `tail_iface_linear_updates`

然后直接对已有 `V20` case 做重评估，得到：

- `has_v20 = 1`
- `has_v21 = 0`

也就是 `V21` 红灯先被准确钉住了。

## fresh 验证

### 1. 编译

重新构建成功：

- `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\build_console\w2_v455_console.exe`

### 2. fresh 扩展窗

本次新鲜验证使用：

- `TMEND = 44436.5`

为了避免 harness 默认 45 分钟超时误杀，这次用了更长 timeout 的同样 case 流程手动重跑。

结果文件：

- `C:\Users\NING\Desktop\v455\analysis\verification\w2_v0_v1_smoke\results\smoke-summary-20260424-195737.csv`

关键字段：

- `missing_markers = 空`
- `has_runtime_error = 0`
- `has_v19_interface_residual = 1`
- `has_v20_interface_iter = 1`
- `has_v21_interface_solve = 1`
- `tail_iface_iter_max = 4`
- `tail_iface_iter_converged_count = 527163`
- `tail_iface_linear_updates = 57033`
- `seg2_valid_count = 66`
- `seg222_valid_count = 66`

## 和 V20 的对比

对比 `V20` 的 fresh 扩展窗：

- `V20`: `tail_iface_resid_max_eta = 0.81905`
- `V21`: `tail_iface_resid_max_eta = 0.45645`

这说明 `ETA` 侧的界面 mismatch 明显减小了。

但 `Q` 侧不是单向变好：

- `V20`: `tail_iface_resid_max_q = 1985.8`
- `V21`: `tail_iface_resid_max_q = 10255.0`

所以这一步的效果是 **mixed**：

- `ETA` 方向更像在朝成熟界面校正前进
- `Q` 方向则暴露出更激进的低维更新会放大一部分流量残差峰值

## 当前判断

`V21` 现在不是失败版，但也不能说已经把接口问题彻底解决了。

更准确地说：

- 它已经把 `V20` 从 fixed-point 推进成了真正的 reduced implicit correction
- 它在 fresh 扩展窗里是稳定可运行的
- 但它目前改善的是 `ETA` 残差，不是同时改善 `ETA/Q` 两个方向

这说明当前 low-dimensional interface solve 的方向是成立的，但：

- `Q` 方程的更新尺度
- `Q` step 的裁剪策略
- 以及 `ETA/Q` 两个未知量之间的耦合方式

还需要进一步调整，不能把现在这版直接当成终局方法。

## 这一版最重要的意义

`V21` 的价值不在于“所有指标都更好”，而在于它把我们正式带入了：

**界面低维隐式求解层**

也就是说，后续如果要继续做成熟化，方向已经不再是：

- 继续堆外层减载
- 或继续只调 fixed-point relaxation

而是：

- 更认真地设计 `ETA/Q` 的 reduced Jacobian / secant 更新
- 甚至最终考虑更完整的 interface Newton 层

## 当前结论

`V21` 可以记成：

- 功能已落地
- fresh 扩展窗已通过
- `ETA` 残差改善明显
- `Q` 残差峰值变大，说明这版仍需继续调校

所以它是一个**方向成立、效果混合、但非常关键的过渡版本**。
