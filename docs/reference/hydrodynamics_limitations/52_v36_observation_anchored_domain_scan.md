# V36 Observation-Anchored Domain Scan

本页检查 V35 新水位约束所指向的宏观控制域，回答“只扩大现有单状态 tail domain”是否足以修复空间水位响应。

Updated: 2026-07-19

## 1. 候选域与源汇链

- 当前基线：owned segment 2:5，coupling segment 6，长度 3.855 km；域内只有 BHT 站。
- 止于 BR2 汇口前：owned segment 2:27，coupling segment 28，长度 23.830 km；包含 BHT、SJ，BR2 恰好位于 coupling boundary。
- 扩到 YMT 前：owned segment 2:56，coupling segment 57，长度 47.165 km；跨过 BR2@28，必须把 BR2 的流量、温度和组分全部纳入控制体，并至少使用两个独立状态区。

候选域、测站、汇流点和 source contract 的完整表保存在 `analysis/verification/v36_macro_domain_preflight/domain_candidates.csv`。

## 2. 可回退实现

- `TAIL_FIXED_MIN_NSEG` 改为逐 branch 数组，默认仍为 4。
- 支持可选 `tail_domain.opt`，每行是 `JB NSEG`；允许范围为 4–64。
- 不存在配置文件时行为不变；存在时输出 `[V36_TAIL_DOMAIN_CONFIG]`。
- 修改只提供实验域开关，不改变守恒方程、接口通量或支流处理语义。

## 3. 扫描结果

扫描 `NSEG=4/8/12/16/20/24/25/26`。所有案例均满足 V24、V25、V26、V27、V31、V32 和 V33 门禁，无 computational warning；最大控制体残差为 `3.57e-9 m3/s`，最大 segment/total volume gap 为 `0.0086 m3`。

| NSEG | Couple | BHT RMSE (m) | SJ RMSE (m) | YMT→SJ head RMSE (m) | SJ→BHT head RMSE (m) |
|---:|---:|---:|---:|---:|---:|
| 4 | 6 | 1.257 | 0.867 | 0.811 | 0.908 |
| 8 | 10 | 1.198 | 0.891 | 0.813 | 1.473 |
| 16 | 18 | 1.649 | 0.963 | 0.814 | 2.315 |
| 24 | 26 | 2.314 | 1.098 | 0.795 | 3.181 |
| 25 | 27 | 2.369 | 0.726 | 0.409 | 2.891 |
| 26 | 28 | 2.374 | 0.500 | 0.204 | 2.668 |

扩大到 segment 28 确实把 YMT→SJ 静态 head bias 从 `-0.783 m` 改到 `-0.125 m`，但同时把 BHT bias 从 `-0.648 m` 推到 `+1.882 m`，SJ→BHT head bias 从 `+0.156 m` 推到 `+2.306 m`。动态 slope 比率也没有形成一致改善。

## 4. 基线不变性

最新编译后的无配置 fresh extended run 完整通过既有门禁，且保持：

- segment 2 bias/RMSE：`-0.648357/1.257266 m`；
- segment 222 bias/RMSE：`0.160542/0.226510 m`；
- 总 head bias/RMSE：`-0.808898/1.326409 m`；
- `CUS=COUPLE=6`，reach length `3855 m`；
- computational warning 为 0。

## 5. 审视结论

不存在一个可同时改善 BHT、SJ、YMT 和相邻水头差的单状态 `NSEG`。因此不能从扫描中挑一个“最佳 NSEG”直接写回模型；那会把空间误差从一个区间搬到另一个区间。

V35 所支持的最小结构仍是以 SJ 为中间接口的两状态架构：BHT–SJ 与 SJ–YMT 分别拥有独立 volume 和守恒通量。由于 BR2 在 segment 28 汇入，第一步应先在 BR2 之前完成 BHT–SJ 宏接口动量闭合预检，再决定是否跨越汇口。
