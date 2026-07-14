# V24 Work Log

Updated: 2026-07-15

## Goal

以提交 `1859ee8` 为干净起点，建立并验证 tailreach/reservoir 守恒接口，持续推进到出现必须由用户确定的物理目标或验收取舍。

## Step 0 — Workspace baseline

Status: complete

- 唯一 Git 跟踪案例：`cases/xld_2021_base/`。
- 活动运行目录：`analysis/.runs/`。
- pre-V24 本地结果：`analysis/.runs/archive_pre_v24/`，不作为新实验完成状态复用。
- 当前分支：`codex/w2-hydro-v24-interface-conservation`。

Review:

- 工作目录与远端在 `1859ee8` 同步，适合作为 V24 起点。
- 构建产物保留在本地但不再进入 Git。

## Step 1 — V21–V23 evidence audit

Status: complete

Confirmed:

- distributed 路径不是 `10255 m3/s` 启动尖峰的直接原因。
- unconditional Q secant 是尖峰的直接放大器，RELAX 将其降至 `1985.8 m3/s`。
- 当前实现还存在三类更基础的不一致：接口通量 blend、无去向的 segment Q attenuation、最大迭代后的未求值 guess。
- branch storage 使用的 outflow 与最终写入 `TAIL_Q_LINK` 的 outflow 不同。

Review:

- 只把默认模式改为 RELAX 会降低尖峰，但不会修复质量守恒。
- 下一步应先增加不改变物理的 V24 守恒诊断，再冻结可重复基线。

Next action:

- 实现 `V24_INTERFACE_MASS` marker、解析器和单元测试。
- 重建 V23 行为的控制台程序，运行 short baseline，记录守恒残差。

## Step 2 — Conservation diagnostics and pre-refactor baseline

Status: complete

Changes:

- 新增 `[V24_INTERFACE_MASS]` 诊断，逐样本记录 `QPHYS`、`QIFACE`、`QRES`、`DSTORAGE`、`RTAIL`、`RFLUX`、`RCOMB` 和 `SEGLOSS`。
- smoke/scan 解析器新增对应统计量；诊断阶段只要求标记存在，不预设残差已经为零。
- 新增 branch 过滤和绝对最大值解析测试。

Verification:

- `build_reduced_console.bat`：通过，生成 `build_console/w2_v455_console.exe`。
- `python -B analysis/test_v21_bht_redistribution_scan.py`：7 项通过。沙箱内临时目录写入被 Windows ACL 拒绝，沙箱外同一命令通过；这不是代码测试失败。
- baseline：`W2_TAIL_Q_UPDATE_MODE=SECANT`，`alpha=0`，`scope=bht`，`tmend=44431.0`。
- 结果：`tail_q_max=10255`、`max|RTAIL|=10309`、`max|RFLUX|=9619.6`、`max|RCOMB|=2732.4`、`max|SEGLOSS|=171.45`。
- 首个诊断样本：`QPHYS=5360`、`QIFACE=15937`、`QRES=6317.2`，确认同一接口在同一时刻使用了两个相差约 `9619.6 m3/s` 的流量。

Review:

- 新诊断复现 V23 的 `10255 m3/s` 启动 Q 残差，没有改变基线行为。
- `RTAIL` 与 `SEGLOSS` 显示尾段储量更新和最终分段出流并非同一通量闭合；首步还叠加了迭代提交不一致。
- `RFLUX` 直接证明 reservoir 的 relaxed effective inflow 破坏了 tail/reservoir 共享界面的单值通量契约。
- 因此 BHT 重分配不是当前优先方向；核心修复必须先消除状态提交、界面 flux 和内部无来源衰减三类结构误差。

Next action:

- 添加针对“最后一次求值状态”“单值界面通量”“无来源分段不衰减”的特征断言。
- 实施最小守恒重构，保留 V23 模式标记用于对照，但让默认路径满足守恒契约。

## Step 3 — Single-flux interface refactor

Status: complete

Changes:

- 删除 tail corrector 中四轮 SECANT/RELAX 伪隐式循环，改为 `COMMIT_TAIL_INTERFACE` 单次提交。
- predictor 生成本步唯一 `QIFACE`；reservoir 直接使用该流量；corrector 用同一流量和已求解的 downstream stage 更新 tail storage。
- `[V24_INTERFACE_COMMIT]` 记录 `QRES/QCOMMIT`、提交前后 stage 和 `EVALUATED` 状态。
- segment state 暂作为同一 committed flux 的守恒派生视图；删除没有 storage/source 对应项的逐段 Q attenuation。
- 新增可用水量上界：`QIFACE <= QPHYS + (VOLD-VMIN)/DT`；predictor cache 复用前也重新检查该边界。
- smoke 解析器把 V24 守恒验收收敛为独立 `assert_v24_conservation`；redistribution scan 调用该断言，不再把短窗状态覆盖要求混入守恒判断。

Verification and iterations:

- 第一次 exact-flux 运行得到 `RFLUX=0`、`SEGLOSS=0`，但 `max|RTAIL|=89979`。原始首步证明 storage 被 `VMIN` 截断而 outflow 未截断，因此补入可用水量上界；该次运行不计为通过。
- 第二次同参数 short run 完成，无 runtime error，SEG 2 有 11 个有效输出。
- 守恒结果：`max|RTAIL|=1.1642e-10`、`max|RFLUX|=0`、`max|RCOMB|=1.1642e-10`、`max|SEGLOSS|=0`。
- 178 次 interface commit 全部 `EVALUATED=T`，`max|QRES-QCOMMIT|=0`。
- 重构后 `V19` committed ETA/Q residual 均为 0；非零 predictor correction 另由 `V24_INTERFACE_COMMIT` 的 `DETA_APPLIED` 表达。
- Python 契约测试：8 项通过；Fortran reduced console build：通过。

Short-window comparison (`alpha=0`, `TMEND=44431.0`):

- SEG 2 RMSE：`1.205873 -> 1.115465`。
- SEG 222 RMSE：`0.346438 -> 0.350562`。
- head RMSE：`1.100896 -> 1.028123`。
- 结论：短窗内守恒修复没有以明显水位退化换取数值闭合；SEG 222 有 `0.004124 m` 的小幅 RMSE 增加，需在 extended window 复核。

Review:

- exact flux 只是必要条件；第一次失败说明 storage lower bound 也是控制体方程的一部分，不能只修接口等式。
- 当前实现是明确的 partitioned explicit commit，不再宣称 reservoir 未重算时存在隐式收敛。
- 缓存只在 reused flux 对当前可释放水量仍可行时保留，因此性能优化不能绕过质量约束。
- full smoke 的前沿状态 marker 覆盖仍作为单独场景测试；它不定义 V24 守恒是否通过。

Next action:

- 运行 `TMEND=44436.5` fresh extended window，并以同一守恒断言和双站水位指标审查。
- 若 extended window 通过，整理设计页实施状态，提交并推送阶段检查点；再判断是否进入逐段 continuity/momentum 子问题。

## Step 4 — Extended-window validation

Status: complete

Run:

- fresh case：`alpha=0`、`scope=bht`、`TMEND=44436.5`。
- scan 进程正常退出，`assert_v24_conservation` 通过。
- 无 runtime error、computational warning、NaN 或 Infinity；SEG 2 有 66 个有效输出。

Conservation:

- 1129 次 interface commit 全部 `EVALUATED=T`。
- `max|QRES-QCOMMIT|=0`。
- `max|RTAIL|=1.1642e-10`。
- `max|RFLUX|=0`。
- `max|RCOMB|=1.1642e-10`。
- `max|SEGLOSS|=0`。

Extended-window water-level metrics:

- SEG 2：bias `0.987561 m`，RMSE `1.820609 m`。
- SEG 222：bias `0.158152 m`，RMSE `0.236300 m`。
- head：bias `0.829409 m`，RMSE `1.713617 m`。

Comparison with V23 RELAX at the same window:

- SEG 2 bias：`1.116332 -> 0.987561`，改善 `0.128771 m`。
- SEG 222 bias：`0.149106 -> 0.158152`，增加 `0.009046 m`。
- head bias：`0.967227 -> 0.829409`，改善 `0.137818 m`。
- V23 的 ETA/Q residual 是 tail-side fixed-point mismatch；V24 的 committed residual 是已求值状态一致性，语义不同，不能把 `0` 直接当成精度提升倍数。

Review:

- 守恒修复在 extended window 内持续成立，不是启动期特例。
- exact interface 没有重现历史上的长窗明显刚性或超时退化；predictor pass 58 次、corrector commit 1129 次、cache reuse 27544 次。
- 上游与 head bias 明显改善，SEG 222 的变化仅为约 `9 mm`；当前没有证据表明守恒修复以整体水位精度为代价。
- 仍存在约 `0.83–0.99 m` 的上游正偏差。下一步应先定位其空间/时间结构和控制量敏感性，再决定是否需要真正的逐段 continuity/momentum 联立。

Next action:

- 建立 V24 剩余水位误差的空间/时间诊断，区分边界 stage、tail storage geometry、摩阻/坡度与 segment 派生状态的影响。
- 只有证据指向 segment 内部动力学缺失时，才设计 V25 逐段连续方程；不恢复任何非守恒 Q attenuation。

## Step 5 — Residual structure and boundary diagnosis

Status: complete

Tooling:

- 新增 `analysis/analyze_v24_residual_structure.py`，从接受态 `wl.csv` 对齐 SEG 2/222 观测和 BHT 物理入流。
- 输出完整样本、逐日统计、流量四分位和总体相关/斜率摘要。
- 新增纯函数测试，覆盖 bias/head identity、相关和线性斜率退化边界；2 项通过。

Accepted-state evidence (`TMEND=44436.5`, 157 samples):

- SEG 2 error–Q correlation：`-0.978532`；head error–Q：`-0.979566`。
- 观测/模拟 SEG 2 stage–Q slope：`0.001844/0.000226 m/(m3/s)`。
- 观测/模拟 head–Q slope：`0.001706/0.000117 m/(m3/s)`。
- 观测/模拟 SEG 222 stage–Q slope：`0.000138/0.000108 m/(m3/s)`。
- head bias 从最低流量四分位的 `+2.162695 m` 单调变到最高流量四分位的 `-1.336115 m`。

Index-chain finding:

- tail domain 为 segment `2:5`，reservoir 主矩阵从 `TAIL_COUPLE_SEG=6` 开始。
- `TAIL_DNSEG` 却仍设置为旧 `CUSMIN=3`；`UPDATE_TAIL_STAGE` 因而用未被主矩阵更新的 segment 3 作为 downstream boundary。
- V7/V10 全窗显示 `DNSEG=3`、`WSE_DN=588.210`、`WSE_HYD=588.210`，与错误边界被锁死完全一致。
- standard-step residual 同时只用首尾两个断面的半长度之和，没有使用已经定义的 multi-segment reach length。

Review:

- 剩余误差的主要来源已从“可能缺逐段动力学”缩小为一个先验更基础的状态边界错误。
- 这不是摩阻调参或业务验收取舍；`TAIL_DNSEG` 的语义应与 `TAIL_COUPLE_SEG` 对齐。
- V10 中间态可能被 autostep 回滚，不能与观测直接回归；精度证据仅来自正式接受态输出。

Next action:

- 按文档 `41_v25_tail_boundary_alignment_design.md` 修复 `TAIL_DNSEG=TAIL_COUPLE_SEG` 和 full reach length。
- 保持 V24 守恒断言不变，先跑编译/短窗；只有短窗稳定且守恒，才进入 extended 对照。

## Step 6 — V25 boundary-aligned short window

Status: complete

Changes:

- `TAIL_UPSEG=TAIL_DOMAIN_US`。
- `TAIL_DNSEG=TAIL_COUPLE_SEG=TAIL_DOMAIN_DS+1`。
- standard-step 和 link-flow 均使用完整 `TAIL_REACH_LENGTH`。
- 修复 `[V11_TAIL_DOMAIN]` 少一个整数格式槽的问题；新增解析字段和 `assert_v25_boundary_alignment`。

Verification:

- reduced console build：通过。
- residual structure tests：2 项通过。
- redistribution/conservation tests：8 项通过。
- fresh short scan 正常退出；`LINK_DN=6`、`COUPLE=6`、alignment `1`。
- `max|RTAIL|=5.8208e-11`；`RFLUX/RCOMB/SEGLOSS/commit gap` 除舍入量外均为 0，全部 commit 已求值。

Short-window comparison with V24:

- SEG 2 bias/RMSE：`0.892568/1.115465 -> -0.745048/0.952178`。
- SEG 222 bias/RMSE：`0.219352/0.350562 -> 0.209560/0.332767`。
- head bias/RMSE：`0.673216/1.028123 -> -0.954608/1.174444`。
- 模拟 SEG 2 stage–Q slope：`0.001281 m/(m3/s)`；观测为 `0.002237`。
- 模拟 head–Q slope：`0.001457 m/(m3/s)`；观测为 `0.002700`。

Review:

- 边界对齐显著恢复了上游动态响应，并改善两个站点各自的 RMSE。
- short-window head bias 从正偏变为负偏，head RMSE 小幅增加，说明响应幅度改善但截距/时序仍未完全闭合。
- 该结果是 mixed，不能仅凭 short window 决定接受或回退；下一步必须跑同一 `TMEND=44436.5` extended window。

Next action:

- 建立 V25 short Git 检查点并同步 GitHub。
- 运行 fresh extended window，继续要求 V24 conservation + V25 boundary alignment 双断言通过。
- 对比 extended stage–Q slope、bias/RMSE 和运行刚性，再决定边界修复是否作为新基线。
