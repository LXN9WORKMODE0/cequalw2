# V8/V9 尾段语义同步与主边界反馈计划
本页回答什么问题：在 `V7` 之后，如何继续沿总蓝图推进，先验证“尾段 stage 进入前沿语义”和“尾段 stage 进入主边界弱反馈”这两条路径是否真能改善双站点水面线。

Updated: 2026-04-18

## 目标

- `V8`：让 `TAIL_WSE_UP` 不再只是输出值，而是真正进入 front-state 语义。
- `V9`：让 `TAIL_WSE_UP` 以受控松弛方式进入主水面方程的上游 ghost-head 反馈。
- 在不破坏稳定性的前提下，检验这两类“弱耦合反馈”是否足以改善 `SEG 2`、`SEG 222` 和两点水面差。

## 任务

1. 先把 smoke harness 提升到需要 `[V8_FRONT_SYNC]`、`[V9_TAIL_FEEDBACK]`。
2. 在 `layeraddsub.F90` 中把 `TAIL_WSE_UP/TAIL_DEPTH_UP` 接入 `FRONT_WSE/FRONT_DEPTH`。
3. 在 `w2_main.f90` 中把 `TAIL_WSE_UP` 通过松弛 ghost-head 的方式接入自由液面求解入口。
4. 跑短窗、延长窗、长窗三组回归。
5. 和 `V7` 做同口径双站点对比。

## 验收

- `smoke-summary` 必须含有 `[V8_FRONT_SYNC]` 和 `[V9_TAIL_FEEDBACK]`。
- 三组窗口都必须继续满足 `seg2_valid_count > 0`、`has_runtime_error = 0`、`has_late_seg2_add = 0`。
- 如果双站点指标仍无实质改善，则明确记录：弱反馈已被验证但不足，下一步应进入真正局部 1D reach。
