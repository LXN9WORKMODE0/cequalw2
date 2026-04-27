# V16 Segmentwise Reach State 实现记录
本页回答什么问题：`V16` 如何把 `V15` 的固定多段尾段域，从“只有多段结构”推进到“开始拥有逐段状态演化”，它真正做到了什么、还没做到什么，以及它对后续 `V17` 的意义是什么。

Updated: 2026-04-21

## 1. 这版的定位

到 `V15` 为止，tailreach 已经具备了：

- 固定多段尾段域
- 明确的 `TAIL_COUPLE_SEG`
- 多段可见的输出语义

但它仍然更像“多段结构外壳”，而不是“多段状态求解器”。  
`V16` 的目标就是把这一点往前推进一步：

- 给尾段域每一段都建立自己的状态数组
- 让 branch-level 的 `TAIL_Q_LINK / TAIL_WSE_UP / TAIL_WSE_DN` 不再只来自单值 tail state
- 至少在日志和求解流程上，让 tailreach 开始表现出逐段传播语义

所以这版不是完整的 1D 尾段方程，而是“逐段 reach state 骨架版”。

## 2. 这版做了什么

### 2.1 新增逐段状态数组

这版引入了 `MAX_TAIL_SEG = 16`，并新增了逐段 tail state：

- `TAIL_STAGE_SEG`
- `TAIL_DEPTH_SEG`
- `TAIL_AREA_SEG`
- `TAIL_HRAD_SEG`
- `TAIL_VOL_SEG`
- `TAIL_Q_SEG`
- `TAIL_Q_TARGET_SEG`
- `TAIL_TRAVEL_TIME_SEG`
- `TAIL_CELERITY_SEG`
- `TAIL_SEG_VALID`

这意味着尾段不再只是一个 branch-level 单值对象，而是拥有了段内可展开的状态容器。

### 2.2 新增逐段初始化与推进入口

在 [w2_main.f90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/w2_main.f90) 里新增了两层入口：

- `INITIALIZE_TAIL_SEGMENT_STATE(JB_IN)`
- `ADVANCE_TAIL_SEGMENT_STATES(JB_IN, JW_IN)`

其中：

- 初始化负责把 `US..DS` 的固定尾段域铺成一个可用的逐段 stage/depth/area/profile
- 推进负责从上游到下游逐段走一遍，并把结果重新聚合回：
  - `TAIL_Q_LINK`
  - `TAIL_WSE_UP`
  - `TAIL_WSE_DN`

也就是说，branch-level tail outputs 现在已经是“逐段状态的聚合结果”，不是单值状态的原始本体。

### 2.3 逐段 `Q` 不再完全同值扇出

这版最重要的变化，不是 marker，而是：

- `[V16_SEGMENT_Q_STATE]` 日志里，同一时刻 `IS=1..4` 的 `Q` 已经不再完全相同

主线程复查的最新日志证据是：

```text
[V16_SEGMENT_Q_STATE] JB=1 IS=1 ISEG=2 Q=11823.610 STAGE=588.210
[V16_SEGMENT_Q_STATE] JB=1 IS=2 ISEG=3 Q=11799.843 STAGE=588.210
[V16_SEGMENT_Q_STATE] JB=1 IS=3 ISEG=4 Q=11771.173 STAGE=588.210
[V16_SEGMENT_Q_STATE] JB=1 IS=4 ISEG=5 Q=11741.190 STAGE=588.210
```

以及另一个时段：

```text
[V16_SEGMENT_Q_STATE] JB=1 IS=1 ISEG=2 Q=47373.539 STAGE=576.050
[V16_SEGMENT_Q_STATE] JB=1 IS=2 ISEG=3 Q=47149.551 STAGE=576.043
[V16_SEGMENT_Q_STATE] JB=1 IS=3 ISEG=4 Q=46898.170 STAGE=576.031
[V16_SEGMENT_Q_STATE] JB=1 IS=4 ISEG=5 Q=46627.915 STAGE=576.028
```

这说明 `V16` 至少已经摆脱了“把同一个 `Q` 机械拷给所有 segment”的保守骨架。

## 3. smoke 与 build 验证

### 3.1 build

主线程确认 build 通过：

- `cmd /c "C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\build_reduced_console.bat"`

结果：

- `BUILD SUCCESSFUL`

### 3.2 smoke

`V16` 的 smoke gate 新增了：

- `has_v16_segment_q_state`
- `tail_segment_state_count`

并要求：

- `has_v16_segment_q_state = 1`
- `tail_segment_state_count >= 2`

最新三组通过结果为：

- [smoke-summary-20260421-174137.csv](/C:/Users/NING/Desktop/v455/analysis/verification/w2_v0_v1_smoke/results/smoke-summary-20260421-174137.csv)
- [smoke-summary-20260421-174223.csv](/C:/Users/NING/Desktop/v455/analysis/verification/w2_v0_v1_smoke/results/smoke-summary-20260421-174223.csv)
- [smoke-summary-20260421-175803.csv](/C:/Users/NING/Desktop/v455/analysis/verification/w2_v0_v1_smoke/results/smoke-summary-20260421-175803.csv)

其中最新长窗 summary 的关键字段为：

- `has_v16_segment_q_state = 1`
- `tail_domain_nseg_min = 4`
- `tail_segment_state_count = 573976`
- `seg2_valid_count = 281`
- `seg222_valid_count = 281`

这说明：

- 逐段 state marker 已经真实进入长窗运行链
- 多段 tail domain 与 V16 逐段状态没有破坏既有稳定性

## 4. 长窗结果

主线程重算 `44430-44458` 的双站点指标如下：

- `SEG2 RMSE = 4.990122360496521`
- `SEG2 Bias = -4.429700000000008`
- `SEG222 RMSE = 0.8535467926673518`
- `SEG222 Bias = -0.6561999999999981`
- `SEG2-SEG222 RMSE = 4.2542214083083625`
- `SEG2-SEG222 Bias = -3.7735000000000105`

这些数值说明：

- `SEG2` 和两点差没有因为逐段状态化而失稳
- `SEG222` 仍保持在可接受误差量级
- `V16` 的主要价值仍然是结构推进，而不是一次大幅度数值跃迁

## 5. 这版没有解决什么

这版仍然不是完整的 local 1D reach solver，主要还缺：

- 完整的局部 1D momentum 方程
- 更强的逐段 stage/Q 联立
- 更明确的逐段 transition closure
- 更真实的段间传播，而不是当前这种保守、稳定优先的近似推进

换句话说，`V16` 已经不再是“多段空壳”，但也还没有进入“真正的逐段水动力 reach”。

## 6. 对后续 V17 的意义

`V16` 的意义在于，它把后续 `V17` 最需要的承载体真正准备好了：

- 现在已经有固定多段尾段域
- 现在已经有逐段状态数组
- 现在已经有逐段 `Q` 差异和逐段日志证据

所以 `V17` 可以把重心真正放到：

- 逐段 transition-state
- 逐段 river / transition / reservoir 控制
- 逐段 closure 对几何、阻力、传播的影响

而不必再回头证明“tailreach 到底有没有逐段状态”。

## 7. 阶段性结论

如果把 `V15-V16` 连起来看，当前第二阶段已经从：

- “固定多段尾段结构”

推进到了：

- “固定多段尾段 + 逐段状态演化骨架”

`V16` 不是终局，但它已经把下一步最关键的问题收缩到了更本质的层面：  
后续不再是“要不要多段”，而是“多段内部如何表达更真实的过渡控制和段间传播”。
