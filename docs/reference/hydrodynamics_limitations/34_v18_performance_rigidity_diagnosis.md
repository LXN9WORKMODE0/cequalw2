# V18 性能与刚性诊断
本页回答什么问题：`V18` 为什么在功能链已经接通的情况下，运行时间会显著变长，当前证据更支持“日志过多”还是“时间步刚性变强”，以及下一步最小减载应该优先打哪里。

Updated: 2026-04-22

## 1. 诊断对象

诊断对象是当前 `V18: Multi-Segment Stronger Hybrid Coupling`。

到这一版为止，功能上已经确认成立的部分包括：

- `V18` marker 已经真实进入运行日志
- predictor / corrector 两个 pass 都能在日志中出现
- tail domain 内部输出已切换到 `TAIL_STAGE_SEG(IS,JB)`

但在完整验证阶段，运行时间明显增长，已经影响到了 smoke 级别的可执行性。

## 2. 已确认的事实

### 2.1 功能链已经接通

当前 `w2.wrn` 中已经能看到：

```text
[V18_MULTI_HYBRID] JB=1 PASS=1 COMMIT=F ...
[V18_MULTI_HYBRID] JB=1 PASS=2 COMMIT=T ...
```

这说明：

- 不是“V18 没有实现”
- 也不是“V18 只是代码里写了 marker 但没有运行”

### 2.2 `tail_mode_set` 不是当前主 blocker

短窗 `tail_mode_set` 为 `1,2` 是正常现象，长窗才要求 `0,1,2`。  
这个门槛已经在 smoke harness 中修正为只在长窗检查。

所以当前性能问题不是由错误的短窗门槛本身导致的。

### 2.3 日志抽样后仍然明显变慢

已经做过一个最小减载尝试：

- 将 `V18` 的高频日志改为抽样输出
- 同时也将 `V16`、`V17` 的高频日志做了抽样

但结果表明：

- 运行时间仍然非常长
- 说明日志量是放大器，但不是唯一根因

## 3. 当前最强证据

### 3.1 短窗 smoke 已能在新 harness 下通过

对应结果：

- [smoke-summary-20260421-215853.csv](/C:/Users/NING/Desktop/v455/analysis/verification/w2_v0_v1_smoke/results/smoke-summary-20260421-215853.csv)

这个 short-window summary 表明：

- `has_v18_multi_hybrid = 1`
- `tail_predictor_pass_count = 461874`
- `tail_corrector_pass_count = 461874`

也就是说，`V18` 的 predictor/corrector 的确在大规模地执行。

### 3.2 由 pass count 反推，平均时间步非常小

在短窗 `TMEND=44435.4` 的情况下：

- 时间跨度约为 `5.4` 天，即 `466560` 秒
- 即便按抽样后的计数粗略反推，平均步长也已经落到了秒级

这说明当前主问题更像是：

- stronger hybrid coupling 使得求解器在接口附近变得非常刚
- autostep 被迫采用大量极小步推进

### 3.3 当前日志也支持“很多小修正”

在当前 `w2.wrn` 尾部，可以看到 `V18` 的 `QLINK` 在围绕相近数值缓慢调整，而 `WSE_DN` 基本变化很小，例如：

```text
... QLINK=4700.053 WSE_DN=589.068
... QLINK=4699.135 WSE_DN=589.068
... QLINK=4698.269 WSE_DN=589.068
... QLINK=4697.453 WSE_DN=589.068
```

这类模式非常像：

- 接口量每一步都在微调
- 系统在进行大量小修正而不是较大步推进

## 4. 根因判断

当前更可信的根因排序是：

### 第一主因：时间步刚性显著增强

证据：

- `tail_predictor_pass_count` / `tail_corrector_pass_count` 极大
- 日志中接口量在做大量小幅调整
- 短窗运行时间仍然很长，即使日志已经做过抽样

因此最主要的根因不是 IO，而是：

- `V18` 的更强耦合让 reservoir/tailreach 接口处变得更难推进

### 第二主因：segmentwise predictor/corrector 带来的单步成本提高

`V18` 将更多数组纳入：

- `SAVE_TAIL_DYNAMIC_STATE`
- `RESTORE_TAIL_DYNAMIC_STATE`
- `RUN_TAIL_PREDICTOR`

这会增加每一步的内存复制和数组处理成本。  
但从当前证据看，这更像“放大器”，不是决定性主因。

### 第三主因：高频诊断日志

日志抽样已经说明：

- 高频日志会放大运行时间
- 但日志减载后问题依旧明显

所以日志不是主因，只是次要负担。

## 5. 当前不支持的判断

当前证据并不支持把主因归结为：

- `outputa2w2tools.F90` 的逐段输出
- 单纯的 smoke harness 逻辑错误
- 单纯的 marker 统计逻辑

这些都不是本轮性能回退的核心。

## 6. 下一步最小减载方向

如果要在不回退 `V18` 功能的前提下做最小减载，优先级建议如下。

### 6.1 第一优先：降低 predictor/corrector 触发频率

当前最可疑的点是：

- 每个 timestep 都做完整的 tail predictor + corrector

可以优先尝试：

- 只有当 `TAIL_WSE_DN` 或 `TAIL_Q_LINK` 的变化超过阈值时，才触发完整 predictor
- 小变化时复用上一步 predictor 结果

### 6.2 第二优先：缩小 save/restore 的数组范围

当前 `V18` 将大量 segmentwise state 纳入回滚链。  
可以优先检查是否真的所有数组都必须每步复制。

如果某些数组可以：

- 由主状态重新计算
- 或只在 corrector 提交时更新

就可以减少大量单步复制成本。

### 6.3 第三优先：接口迟滞/松弛

接口上现在的行为看起来像“每一步都追着小差异跑”。  
可以优先尝试：

- 给 `QLINK` 与 `WSE_DN` 加变化阈值
- 小于阈值时不重新刷新 predictor/corrector

### 6.4 第四优先：继续压缩高频日志

这不是主因，但仍然值得保留为附属优化项。

## 7. 阶段性结论

当前对 `V18` 的最准确判断是：

- 功能方向已经成立
- 主 blocker 不是“功能没接上”，而是“更强耦合显著增强了时间步刚性”

因此后续最合理的工作，不是再继续加新功能，而是：

- 做一轮专门的 `V18` 刚性减载
- 先把 predictor/corrector 的触发与状态复制减下来
- 再重新验证 short / extended / long smoke

换句话说，下一步的关键词不再是“更强功能”，而是“更轻耦合成本”。 

## 8. 方案 3 的第一次试验结果

根据前面的判断，已经先试了一轮“方案 3：最小减载”，具体动作是：

- 在 `RUN_TAIL_PREDICTOR()` 中加入 branch-level predictor reuse 机制
- 当接口变化足够小且 skip 次数未超上限时，直接复用当前 committed tail state，不再每步都做完整 predictor
- 新增日志标记：
  - `[V18_PREDICT_REUSE]`

同时在 smoke harness 中新增了：

- `has_v18_predict_reuse`
- `tail_predictor_skip_count`

### 8.1 试验结论

这轮试验的结论不是“完全失败”，而是：

- predictor reuse 机制已经真实生效
- 但它还不足以把运行时间压回可接受范围

### 8.2 证据

当前 `w2.wrn` 中已经可以看到：

```text
[V18_PREDICT_REUSE] JB=1 SKIP=1 ...
[V18_PREDICT_REUSE] JB=1 SKIP=2 ...
[V18_PREDICT_REUSE] JB=1 SKIP=3 ...
```

也就是说，`V18` 的 predictor 不再是绝对每步全跑。

但是，即便在：

- `V18` 高频日志抽样
- `V16/V17` 高频日志抽样
- predictor reuse 已经触发

这些减载动作都存在的情况下，short-window 运行时间仍然长得不合理。

### 8.3 对主因判断的影响

这轮试验反而进一步强化了前面的判断：

- `V18` 的主问题不是“日志太多”
- 也不是“predictor 每步都跑”这一个因素
- 更深层的主因仍然是接口刚性本身

换句话说：

- 方案 3 已经证明“轻量减载机制可以生效”
- 但目前这版减载还不够

### 8.4 下一步意味着什么

这意味着后续如果继续沿方案 3 走，必须再更进一步，而不只是停在“skip predictor 一部分步”：

- 需要更强的接口触发阈值
- 需要更严格的接口迟滞
- 或者需要缩小 save/restore 的状态复制范围

如果这些继续做下去仍然不足以把 short-window 拉回合理时间，那么就说明：

- 方案 3 只能缓解，不足以根治
- 后续就应该正式转入方案 1，也就是更成熟的整体隐式/强收敛接口处理路线

## 9. 方案 3 的第二次试验结果

在第一次试验之后，又继续做了第二轮更激进的减载：

- 不仅在 predictor 上启用 reuse
- 还在同一时间步内让 predictor reuse 时连 corrector 也一起跳过

这相当于把耦合从：

- “每步都 predictor + corrector”

进一步减到：

- “接口变化足够小时，这一时间步只复用旧接口状态，不再完整刷新 tail predictor/corrector”

### 9.1 结果

这轮试验的结论非常关键：

- predictor / corrector 的日志计数显著下降了
- 但短窗总运行时间几乎没有改善

### 9.2 定量证据

用 `TMEND=44431.0` 做 1 天 profiling window 对比：

第一轮减载后的运行时间：

- `ELAPSED_SECONDS = 352.35`

第二轮减载后的运行时间：

- `ELAPSED_SECONDS = 352.897`

两者几乎相同。

而在第二轮减载后，对应 summary 为：

- [smoke-summary-20260422-235818.csv](/C:/Users/NING/Desktop/v455/analysis/verification/w2_v0_v1_smoke/results/smoke-summary-20260422-235818.csv)

其中：

- `tail_predictor_pass_count = 10`
- `tail_corrector_pass_count = 10`
- `tail_predictor_skip_count = 4058`

这和前一轮相比，说明：

- predictor/corrector 的实际触发次数已经被明显压低
- 但 wall-clock 时间几乎没动

### 9.3 这说明什么

这轮结果对根因判断非常重要，因为它直接排除了两个常见怀疑：

1. **不是 predictor/corrector 调度频率本身造成的主耗时**
2. **也不是日志输出频率本身造成的主耗时**

如果 main cost 主要来自 tail predictor/corrector 本身，那么在它们的触发次数大幅下降后，运行时间理应同步显著下降。  
但现在没有发生这一点。

因此更可信的解释是：

- 真正的主成本已经转移到了主库区 W2 水动力解本身
- 更强耦合改变了接口条件，使主库区自由液面/连续方程推进变得更“硬”
- 即使 tail predictor/corrector 跳过了，主库区仍然在大量小步推进

### 9.4 现阶段对方案 3 的判断

到这一步为止，可以更明确地说：

- 方案 3 不是完全无效
- 它确实能让“tail 子系统自己的工作量”下降
- 但它对总耗时的主导因素没有形成实质打击

所以当前对方案 3 的最准确定位是：

- **它能缓解外围开销，但不能触及主刚性来源**

这意味着如果继续沿方案 3 深挖，边际收益很可能会继续变小。

## 10. 更新后的阶段性结论

综合两轮方案 3 试验，当前结论可以收敛成：

- 日志风暴：不是主因
- predictor/corrector 调度频率：不是主因
- 主库区在更强接口条件下的时间步刚性：最可能的主因

因此，下一步如果还想继续优化，最合理的顺序应当是：

1. 先承认方案 3 已经试到了一个有信息量的边界
2. 不再继续在 skip/reuse 这种外围减载上反复打转
3. 正式转入方案 1，也就是更成熟的整体隐式/强收敛接口处理思路
