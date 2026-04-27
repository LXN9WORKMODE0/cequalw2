# V17 Segmentwise Transition Closure 实现记录
本页回答什么问题：`V17` 如何把尾段域里的 transition-state 从 branch-level 推到 segmentwise，并让长窗运行里真实覆盖 `river / transition / reservoir` 三种模式，同时保持当前案例的数值稳定性。

Updated: 2026-04-21

## 1. 这版的定位

到 `V16` 为止，tailreach 已经拥有了：

- 固定多段尾段域
- 逐段 state 数组
- 逐段 `Q` 差异

但 transition-state 仍然主要是 branch-level 语义，`FRONT_TRANSITION` 和 `TAIL_CONTROL_MODE` 也还没有真正由尾段域内部的逐段状态来主导。  
`V17` 的目标就是把这件事补上：

- 每一段都有自己的 `TRANS / SUB / SLOPE / FR / MODE`
- 局部 transition-state 真正进入 closure
- 长窗 smoke 不只检查 marker，而是检查 `tail_mode_set` 能否覆盖 `0,1,2`

这意味着 `V17` 是第一次真正从“段级状态存在”推进到“段级控制状态存在”。

## 2. 这版做了什么

### 2.1 新增逐段 transition-state 数组

在 [w2modules.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/w2modules.F90) 中新增：

- `TAIL_TRANSITION_SEG`
- `TAIL_SUBMERGENCE_SEG`
- `TAIL_LOCAL_SLOPE_SEG`
- `TAIL_FROUDE_SEG`
- `TAIL_MODE_SEG`

因此，transition-state 不再只是一个 branch-level 单值，而是尾段域内每段都可单独保存和演化的控制状态。

### 2.2 新增逐段 transition 更新入口

在 [w2_main.f90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/w2_main.f90) 中补了：

- `UPDATE_TAIL_SEGMENT_TRANSITION(JB_IN, JW_IN, IS)`

每个 tail segment 都会计算自己的：

- `SUB`
- `SLOPE`
- `FR`
- `TRANS`
- `MODE`

这让 `mode 0/1/2` 不再只是 branch-level 推断，而是逐段求出来的状态。

### 2.3 逐段 transition-state 进入局部 closure

这版不只是“多打一条日志”，而是让逐段 transition-state 真正调制局部量：

- `TAIL_AREA_SEG`
- `TAIL_HRAD_SEG`
- `TAIL_CELERITY_SEG`

也就是说，segmentwise transition 已经开始影响局部过水断面、水力半径和传播速度，而不是只停留在诊断层。

### 2.4 `layeraddsub` 同步来源改变

在 [layeraddsub.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/layeraddsub.F90) 中，`FRONT_TRANSITION` 和 `TAIL_CONTROL_MODE` 的主来源已经改成：

- 尾段域下游端 segmentwise state

而不是继续主要依赖旧的 `FRONT_STATE` 物理映射。  
这一步很关键，因为它把“前沿语义层”和“尾段内部物理层”的主从关系真正调整过来了。

## 3. smoke 与 build 验证

### 3.1 build

`V17` 的 build 已通过：

- `cmd /c "C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\build_reduced_console.bat"`

结果：

- `BUILD SUCCESSFUL`

### 3.2 smoke

`V17` 的 smoke gate 新增了两项关键要求：

- `has_v17_segment_transition = 1`
- 长窗 `tail_mode_set` 必须覆盖 `0,1,2`

三组通过结果为：

- [smoke-summary-20260421-181648.csv](/C:/Users/NING/Desktop/v455/analysis/verification/w2_v0_v1_smoke/results/smoke-summary-20260421-181648.csv)
- [smoke-summary-20260421-181734.csv](/C:/Users/NING/Desktop/v455/analysis/verification/w2_v0_v1_smoke/results/smoke-summary-20260421-181734.csv)
- [smoke-summary-20260421-182435.csv](/C:/Users/NING/Desktop/v455/analysis/verification/w2_v0_v1_smoke/results/smoke-summary-20260421-182435.csv)

最新长窗 summary 的关键字段是：

- `has_v17_segment_transition = 1`
- `tail_domain_nseg_min = 4`
- `tail_segment_state_count = 564656`
- `tail_mode_set = "0,1,2"`
- `seg2_valid_count = 281`
- `seg222_valid_count = 281`

这说明：

- V17 marker 已经真实进入长窗运行链
- 模式覆盖不是概念上的，而是 smoke 已经硬性校验过

## 4. 日志证据

主线程复查到的代表性日志包括：

```text
[V17_SEGMENT_TRANSITION] JB=1 IS=1 MODE=2 TRANS=.740 SUB=1.000 SLOPE=.000 FR=.801
[V17_SEGMENT_TRANSITION] JB=1 IS=2 MODE=2 TRANS=.763 SUB=.802 SLOPE=.000 FR=.454
[V17_SEGMENT_TRANSITION] JB=1 IS=3 MODE=2 TRANS=.880 SUB=1.000 SLOPE=.000 FR=.435
[V17_SEGMENT_TRANSITION] JB=1 IS=4 MODE=2 TRANS=.860 SUB=.771 SLOPE=.000 FR=.244
```

以及另一个时段：

```text
[V17_SEGMENT_TRANSITION] JB=1 IS=1 MODE=1 TRANS=.400 SUB=1.000 SLOPE=.000 FR=66947.969
[V17_SEGMENT_TRANSITION] JB=1 IS=2 MODE=0 TRANS=.224 SUB=.476 SLOPE=.000 FR=10.504
[V17_SEGMENT_TRANSITION] JB=1 IS=3 MODE=1 TRANS=.467 SUB=1.000 SLOPE=.000 FR=24.233
[V17_SEGMENT_TRANSITION] JB=1 IS=4 MODE=0 TRANS=.320 SUB=.550 SLOPE=.000 FR=3.503
```

这些日志说明：

- 模式 `0/1/2` 确实都真实出现了
- 不是只有一段在切换，而是不同 segment 在同一阶段就能表现出不同控制态

## 5. 长窗结果

主线程重算 `44430-44458` 的双站点指标如下：

- `SEG2 RMSE = 4.962126130213028`
- `SEG2 Bias = -4.3945357142857215`
- `SEG222 RMSE = 0.8465337042906159`
- `SEG222 Bias = -0.645294642857136`
- `SEG2-SEG222 RMSE = 4.235400897073226`
- `SEG2-SEG222 Bias = -3.7492410714285853`

这些数值说明：

- `SEG2` 与两点差相对 `V16` 继续小幅改善
- `SEG222` 误差仍在可接受量级，没有因为模式覆盖而明显失控
- `V17` 的主要价值不只是“模式更多”，而是在保持长窗稳定的情况下做到了模式扩展

## 6. 这版没有解决什么

尽管 `V17` 已经让 `tail_mode_set` 达到 `0,1,2`，但它仍然不是完整的 local 1D tail solver：

- 还没有完整的段级 momentum 方程
- 还没有更强的段间联立传播
- transition closure 仍然是保守的、稳定优先的近似

换句话说，`V17` 已经把“段级控制模式”做出来了，但还没有把“段级动力学闭环”做完整。

## 7. 对后续 V18 的意义

`V17` 的意义在于，它把后续 `V18` 最需要的两件事真正准备好了：

- 多段尾段域已经有逐段状态
- 多段尾段域已经有逐段模式

因此 `V18` 可以把重点真正放到：

- 多段 tailreach 与主库区更强的同一步耦合
- predictor/corrector 层面如何利用 segmentwise state
- 如何把当前 segmentwise transition closure 更深地反馈进主库区接口

## 8. 阶段性结论

如果把 `V15-V17` 连起来看，当前第二阶段已经从：

- “固定多段尾段结构”

推进到了：

- “固定多段尾段 + 逐段状态 + 逐段控制模式”

`V17` 不是终局，但它已经把问题推进到了更像真正 hybrid tailreach solver 的层面。  
现在后续最大的增量，不再是“要不要多段、要不要多模式”，而是“如何把这些多段、多模式状态更强地并入 reservoir/tailreach 接口耦合”。 
