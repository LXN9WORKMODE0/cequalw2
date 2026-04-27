# V15 Multi-Segment Tail Domain 实现记录
本页回答什么问题：`V15` 到底把 tail domain 从“单段可见”的结构推进成了什么样的多段物理域，它和 `V14` 的区别是什么，这一版真正解决了什么、还没有解决什么，以及它对后续 `V16` 的意义是什么。
Updated: 2026-04-21

## 1. 这版的定位
到 `V14` 为止，tailreach 已经具备了：
- 固定尾段物理域
- 带记忆的 `QSTATE`
- 内部 transition state
- 同步主线程 predictor/corrector 的耦合语义

但 tail domain 在结构上仍然偏向“单段可见”的实现，很多尾段内部信息仍然容易退化成只剩 `TAIL_UPSEG` 可见的语义。

`V15` 的目标就是把这件事往前推进一步：
- 把 tail domain 从 `NSEG=1` 推到固定的多段域
- 让尾段内部的物理域在代码里真正按多段展开
- 让接口段和尾段域之间的语义关系变得明确

换句话说，`V15` 不是再加一个 marker，而是把 tail domain 从“单点/单段链接”推进成“固定多段物理域”。

## 2. 这版解决了什么
### 2.1 tail domain 变成固定多段域
当前案例里，tail domain 已经推进到：
- `US = 2`
- `DS = 5`
- `NSEG = 4`

这说明尾段域不再只是一个抽象链接点，而是一个真正可展开的多段物理域。

### 2.2 引入 `TAIL_COUPLE_SEG` 语义
这版把 tail coupling 的接口语义补成了更明确的“段落定位”。

当前日志证据是：
- `[V15_TAIL_DOMAIN_MULTI] JB=1 US=2 DS=5 NSEG=4 COUPLE=6`

其中 `COUPLE=6` 表明接口段已经落到尾段域下游一侧，tail domain 与主线程耦合的落点不再只是“某个单点”，而是有了清晰的多段域定位。

### 2.3 让尾段域内部各段都能被看见
`outputa2w2tools.F90` 这次的改动，核心是让 tail domain 内各段不再只剩 `TAIL_UPSEG` 可见。

这一步很关键，因为它把 tail domain 的输出语义从：
- “只有入口/上游段有意义”

推进成：
- “域内各段都可以被识别、输出和校验”

## 3. 代码层面做了什么
本版的关键改动点主要有四个：

- tail domain 从 `NSEG=1` 推进为固定多段域
- 增加 `TAIL_COUPLE_SEG` 语义，明确接口段与尾段域的耦合落点
- smoke harness 新增 `V15` marker 与 `tail_domain_nseg_min` 校验
- `outputa2w2tools.F90` 调整尾段输出可见性，避免只剩 `TAIL_UPSEG`

这版的重点不是引入新的动力学方程，而是把 tail domain 的结构边界补实。

## 4. smoke 和 build 验证
### 4.1 build
主线程独立执行：
- `cmd /c "C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\build_reduced_console.bat"`

结果：
- `BUILD SUCCESSFUL`

### 4.2 smoke
三组 smoke 都已通过，对应结果文件是：
- [smoke-summary-20260420-213627.csv](C:/Users/NING/Desktop/v455/analysis/verification/w2_v0_v1_smoke/results/smoke-summary-20260420-213627.csv)
- [smoke-summary-20260420-213726.csv](C:/Users/NING/Desktop/v455/analysis/verification/w2_v0_v1_smoke/results/smoke-summary-20260420-213726.csv)
- [smoke-summary-20260420-214619.csv](C:/Users/NING/Desktop/v455/analysis/verification/w2_v0_v1_smoke/results/smoke-summary-20260420-214619.csv)

最新长窗 summary 的关键字段是：
- `has_v15_tail_domain_multi = 1`
- `tail_domain_nseg_min = 4`
- `seg2_valid_count = 281`
- `seg222_valid_count = 281`

这说明 `V15` 的 marker 已经被 harness 识别，而且尾段多段结构在长窗里也真的成立。

## 5. 长窗结果
主线程重算的 `44430-44458` 指标如下：
- `SEG2 RMSE = 4.9894486317276305`
- `SEG2 Bias = -4.432531531531543`
- `SEG222 RMSE = 0.79209404301065`
- `SEG222 Bias = -0.5973153153153073`
- `SEG2-SEG222 RMSE = 4.313339199976532`
- `SEG2-SEG222 Bias = -3.8352162162162364`

这些数值的意义是：
- `SEG2` 仍然处于明显受耦合影响的区间
- `SEG222` 保持在和前面版本一致的低误差水平
- 差值项没有失控，说明多段域展开没有破坏已有主结果

## 6. 这版没解决什么
`V15` 不是终局版，所以它没有解决这些事：

- 没有补成完整的 1D momentum equation
- 没有把多段域做成真正的全域传播求解
- 没有把所有尾段内部状态都提升成完整的动态子系统

也就是说，`V15` 解决的是“尾段域结构显式多段化”，还不是“尾段域完整动力学闭环化”。

## 7. 对后续 V16 的意义
`V15` 的价值在于，它把后续版本最需要的前提先打稳了：

- 先有真正的多段尾段域
- 再谈域内状态传播和更完整的耦合
- 先让接口段落点稳定可见
- 再去扩展更细的内部传输和局部求解

所以 `V16` 如果继续往前走，重点就不会再是“tail domain 到底算不算一个域”，而是：
- 如何在这个固定多段域里做更完整的状态演化
- 如何把尾段内部段间传播做得更自然
- 如何让多段 tail domain 真正成为后续局部 1D 求解的承载体

## 8. 这版的阶段性结论
如果把 `V11-V15` 连起来看，路径已经很清楚了：

- `V11`: fixed tail domain
- `V12`: discharge state with memory
- `V13`: internal transition-state logic
- `V14`: same-step stronger coupling + rollback
- `V15`: multi-segment tail domain visible in structure and output

这意味着第二阶段的骨架已经从“单段链接”走到了“固定多段物理域”。

`V15` 不是最终答案，但它把下一步该做什么变得更明确了。
