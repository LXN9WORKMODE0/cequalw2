# V18 Multi-Segment Hybrid Coupling 实现记录
本页回答什么问题：`V18` 如何把多段 tailreach 的 predictor/corrector 更强地接回 reservoir 接口、当前已经做成了什么、又为什么在完整验证阶段暴露出明显的性能回退。

Updated: 2026-04-21

## 1. 这版的目标

到 `V17` 为止，tailreach 已经具备了：

- 固定多段尾段域
- 逐段 state
- 逐段 transition-state
- 长窗 `tail_mode_set = "0,1,2"`

`V18` 的目标不是再扩状态，而是把这些多段状态更强地并入 reservoir/tailreach 的同一步接口耦合。  
也就是说，这一版要解决的是：

- predictor/corrector 不再只围绕 branch-level 单值运转
- segmentwise state 要进入 save/restore/predictor 链
- tail domain 内部输出不再只是 placeholder，而是直接输出 `TAIL_STAGE_SEG(IS,JB)`

## 2. 已经实现的东西

### 2.1 `V18` 日志与 smoke 入口已经打通

当前运行日志里已经真实出现：

```text
[V18_MULTI_HYBRID] JB=1 PASS=1 COMMIT=F ...
[V18_MULTI_HYBRID] JB=1 PASS=2 COMMIT=T ...
```

也就是说，`V18` 已经不是“代码里写了但没进运行链”，而是 predictor/corrector 两个 pass 都真实进入了运行日志。

### 2.2 segmentwise state 已进入 predictor/corrector 框架

当前 `w2_main.f90` 里，`SAVE_TAIL_DYNAMIC_STATE / RESTORE_TAIL_DYNAMIC_STATE / RUN_TAIL_PREDICTOR` 已经扩展到覆盖多段 state，包括：

- `TAIL_STAGE_SEG`
- `TAIL_DEPTH_SEG`
- `TAIL_AREA_SEG`
- `TAIL_HRAD_SEG`
- `TAIL_VOL_SEG`
- `TAIL_Q_SEG`
- `TAIL_TRANSITION_SEG`
- `TAIL_MODE_SEG`

这说明 `V18` 的主方向是成立的：多段 tail state 确实开始进入更强的耦合主链。

### 2.3 tail-domain 输出路径已经切到逐段 stage

在 [outputa2w2tools.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/outputa2w2tools.F90) 中，tail domain 内各段已经从 domain-wide placeholder 切到：

```fortran
IS = I - TAIL_DOMAIN_US(JB) + 1
ELKT(I) = TAIL_STAGE_SEG(IS,JB)
```

这意味着：

- V18 的输出语义已经更接近真正的多段 tailreach
- 耦合做了以后，输出上也能看到段内差异

## 3. 已有验证结果

### 3.1 功能性短窗验证

已经有一组短窗通过结果表明：

- `V18` marker 已被 smoke 识别
- predictor/corrector 计数为正
- `SEG 2`、`SEG 222` 仍然可测

对应 summary 为：

- [smoke-summary-20260421-215853.csv](/C:/Users/NING/Desktop/v455/analysis/verification/w2_v0_v1_smoke/results/smoke-summary-20260421-215853.csv)

这说明 `V18` 的功能方向不是空的，至少在短窗功能性层面已经接通。

### 3.2 当前日志证据

当前 `w2.wrn` 中可以看到：

```text
[V18_MULTI_HYBRID] JB=1 PASS=1 COMMIT=F QLINK=...
[V18_MULTI_HYBRID] JB=1 PASS=2 COMMIT=T QLINK=...
```

这说明：

- `tail_predictor_pass_count > 0`
- `tail_corrector_pass_count > 0`

## 4. 当前 blocker

`V18` 目前还不能算完全通过，原因不是功能逻辑没接上，而是：

- 更强耦合引入了非常明显的运行时性能回退

最直接的证据是：

- `V18` 的短窗运行时间显著拉长
- 在尝试继续做更完整验证时，短窗本身就已经接近半小时量级
- 继续推进到 extended / long-window 验证会变得非常昂贵

换句话说，当前 blocker 不是：

- “没有 marker”
- “没有 predictor/corrector”
- “没有段内输出”

而是：

- stronger hybrid coupling 让运行成本显著上升，已经影响到 smoke 级验证的可执行性

## 5. 已做过的性能缓解尝试

为了确认问题是不是纯日志 IO 导致的，已经做过一个最小缓解：

- 将 `V18` 的高频日志改为抽样输出
- 并进一步对 `V16` / `V17` 的高频日志也做了抽样控制

但结果表明：

- 这能减少日志风暴
- 却不能根本消除 `V18` 的运行时间回退

因此当前判断是：

- 日志量是放大器
- 但不是唯一根因

## 6. 当前阶段结论

最准确的结论不是“V18 失败了”，而是：

- `V18` 的功能方向已经成立
- `V18` 的完整 smoke 验证被明显的性能回退卡住了

所以它当前更适合被定义为：

- `DONE_WITH_CONCERNS`

而不是无保留的完成。

## 7. 对后续工作的意义

`V18` 之后，问题已经从“怎么把多段状态并入耦合”转向了更工程化的一层：

- 更强耦合为什么会让推进代价大幅上升
- 是 predictor/corrector 增加了过多状态复制
- 还是 autostep 在更强耦合下明显缩小了步长
- 或者两者兼有

因此，后续如果继续推进，最自然的下一步不再是再加新物理机制，而是：

- 专门做一次 `V18` 性能/刚性诊断
- 区分 “日志 IO 问题” 和 “时间步刚性问题”
- 在不回退 `V18` 功能的前提下，把 smoke 级运行时间压回到可接受范围

## 8. 阶段性结论

如果把 `V15-V18` 串起来看，第二阶段已经完成了从：

- 多段尾段结构
- 到逐段状态
- 到逐段模式
- 再到更强的多段接口耦合

`V18` 的下一步已经不是“继续补功能”，而是“让已经接上的功能变得可验证、可负担”。  
也就是说，当前最需要的不是再加一个版本束，而是把 `V18` 做成一个运行代价合理的版本。 
