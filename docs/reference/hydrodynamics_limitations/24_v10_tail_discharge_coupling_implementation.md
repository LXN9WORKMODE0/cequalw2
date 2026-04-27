# V10 尾段有效出流耦合实现记录
本页回答什么问题：`V10` 如何把尾段 reach 的有效出流真正接进主库区入流，过程中遇到了什么数值问题，最后留下了什么可用结论。

Updated: 2026-04-18

## 1. 这版的定位

`V7-V9` 的共同问题是：

- 尾段 stage 已经存在
- front-state 已经看见它
- 主边界也收到了一点弱反馈

但主库区 `SEG 3` 仍然直接吃原始 `QIN(JB)`。

所以 `V10` 的核心不是再补一个日志，而是：

- 让 tailreach 输出真正的 `TAIL_Q_LINK`
- 让主库区入流开始吃这个有效出流

这使得 `V10` 成为当前总蓝图里第一版真正碰到“质量通量闭合”的尾段子求解器雏形。

## 2. 代码改动

### 2.1 新增尾段 reach 状态

新增了：

- `TAIL_STORAGE_VOL`
- `TAIL_Q_INFLOW`
- `TAIL_Q_OUTFLOW`
- `TAIL_REACH_INITIALIZED`

位置：

- [w2modules.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/w2modules.F90:140)
- [input.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/input.F90:318)
- [init.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/init.F90:60)
- [init-geom.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/init-geom.F90:506)

### 2.2 `w2_main.f90` 中的 reach 计算

新增和扩展的逻辑包括：

- `EFFECTIVE_UPSTREAM_INFLOW`
- `TAIL_VOLUME_FROM_STAGE`
- `INVERT_TAIL_STORAGE_STAGE`
- `COMPUTE_TAIL_LINK_FLOW`
- 扩展版 `UPDATE_TAIL_STAGE`

核心流程是：

1. 用物理上游来流 `QIN(JB)` 作为尾段物理入流。
2. 用尾段 stage 和下游 stage 计算局部 hydraulic link 出流。
3. 用 continuity 更新尾段 storage。
4. 从 storage 反解新的尾段 stage。
5. 再把尾段有效出流按耦合强度送入主库区入流。

实现位置：

- [w2_main.f90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/w2_main.f90:906)
- [w2_main.f90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/w2_main.f90:1204)
- [w2_main.f90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/w2_main.f90:1692)

### 2.3 smoke 新门槛

新增硬门槛：

- `[V10_TAIL_REACH]`

位置：

- [run_w2_v0_v1_smoke.py](/C:/Users/NING/Desktop/v455/analysis/run_w2_v0_v1_smoke.py:1)

## 3. 第一次实现暴露的问题

第一次把 `TAIL_Q_LINK` 直接接进主库区后，长窗超时。排查 `w2.wrn` 发现：

- `QOUT` 飙到 `1.5e5 m3/s` 量级
- `WSE_HYD` 飙到 `900+ m`
- `WSE_STOR` 仍然只在 `600 m` 左右

这说明根因不是“尾段控制主入流这条路线错了”，而是：

- 我给 `COMPUTE_TAIL_LINK_FLOW` 加了固定坡度底线
- 局部 reach 在回水很平的时候仍被迫释放过大的出流
- `WSE_HYD` 又用 `MAX()` 主导了最终 stage

于是形成了：

- 大出流
- 大入库
- 大下游水位
- 更大 hydraulic stage

的正反馈。

## 4. 根因修正

针对根因做了两条修正：

1. 去掉 `COMPUTE_TAIL_LINK_FLOW` 里的固定坡度底线  
   现在如果 `WSE_UP - WSE_DN` 没有形成正的局部坡降，则尾段 link 出流直接退到 `0`

2. 把最终尾段 stage 改成 `storage stage` 主导  
   不再让 `WSE_HYD` 用 `MAX()` 把最终 stage 顶飞

这样之后：

- `QOUT` 最大值回到 `16507 m3/s`
- `WSE_HYD/WSE_STOR` 都回到 `590-596 m` 量级
- 长窗重新稳定

## 5. 耦合强度试探

`TAIL_FLOW_COUPLING_RELAX` 先后测了：

- `0.50`
- `0.25`
- `0.15`

结果表明：

### `0.50`

- 水面差改善最明显
- 但两端绝对水位恶化也最明显

指标：

- `SEG 2 RMSE = 6.050`
- `SEG 222 RMSE = 2.453`
- `DIFF RMSE = 4.248`

### `0.25`

- 绝对水位有所回拉
- 水面差仍明显优于 `V7-V9`

指标：

- `SEG 2 RMSE = 5.818`
- `SEG 222 RMSE = 2.021`
- `DIFF RMSE = 4.319`

### `0.15`

- 当前测试里更平衡
- 两端绝对水位继续改善
- 水面差改善略弱于 `0.25`，但仍优于 `V7-V9`

指标：

- `SEG 2 RMSE = 5.598`
- `SEG 222 RMSE = 1.675`
- `DIFF RMSE = 4.340`

## 6. 目前最重要的结论

`V10` 给出了一个很关键的正结果和一个很关键的限制：

### 正结果

- 只要让尾段 effective discharge 真正控制主库区入流，水面差确实开始往真实方向改善。

### 限制

- 当前这还是“storage + rating + relaxed coupling”级别的尾段 reach。
- 它已经能改善坡降，但还做不到同时把 `SEG 2`、`SEG 222`、两点水面差三者一起做好。

这说明总蓝图的判断仍然成立：

- 已经越过了“弱补丁”阶段
- 但还没到“完整局部 1D reach solver”

## 7. 当前建议

如果继续推进，下一步不该再只是调单个系数，而应进入：

- 真正的 local 1D reach momentum / discharge evolution

也就是：

- 让尾段不只靠 storage continuity 和 rating curve
- 而是开始有自己的 discharge state / momentum state

当前保留下来的更平衡候选值是：

- `TAIL_FLOW_COUPLING_RELAX = 0.15`
