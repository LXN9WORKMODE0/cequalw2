# V10 尾段有效出流耦合计划
本页回答什么问题：在 `V7-V9` 已经证明“尾段 stage 可输出、可同步、可弱反馈”之后，如何把尾段 reach 的有效出流真正接进主库区入流闭合。

Updated: 2026-04-18

## 目标

- 让 protected tailreach 不只产出 `TAIL_WSE_UP`，还产出 `TAIL_Q_LINK`。
- 让主库区 `SEG 3` 的有效入流开始受尾段 reach 控制，而不是继续直接吃原始 `QIN(JB)`。
- 保持 `SEG 2` 连续有值，同时检验水面差是否得到实质改善。

## 任务

1. 给尾段新增 storage / inflow / outflow 状态量。
2. 用 storage continuity + 局部 hydraulic link 计算 `TAIL_Q_LINK`。
3. 在主水面方程和上游边界速度里，用尾段有效出流替换原始入库流量。
4. 跑长窗验证并检查是否出现量级发散。
5. 对耦合强度做最小范围试探，找出更平衡的候选值。

## 验收

- smoke 需要 `[V10_TAIL_REACH]`
- `SEG 2` 和 `SEG 222` 必须继续有值
- 不允许再次出现 `WSE/Q` 量级爆炸
- 双站点和两点水面差要比 `V7-V9` 更接近物理，至少在某一维度上出现清晰改进
