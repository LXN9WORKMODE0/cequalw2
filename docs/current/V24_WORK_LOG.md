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

## Step 7 — V25 extended-window validation

Status: complete; V25 result not accepted as the next baseline

Run record:

- 首次 fresh extended run 在 `JDAY=44432.4` 后随执行终端异常退出，进程返回 `0x40010004`；模型没有留下 runtime error、computational warning、NaN 或 Infinity，最后一条完整守恒记录为 `RTAIL=-6.3665e-12`、`RFLUX=0`、`SEGLOSS=0`。
- 操作系统中已无该模型或包装进程；Git 工作树保持干净。该次输出不足以覆盖目标窗口，不能用于接受 V25。
- 随后从干净 case 重跑相同的 `alpha=0`、`scope=bht`、`TMEND=44436.5`，正常退出，用时约 33.6 分钟。

Extended-window metrics (157 accepted samples):

- SEG 2 bias/RMSE：`0.987561/1.820609 -> -0.673884/1.271940 m`。
- SEG 222 bias/RMSE：`0.158152/0.236300 -> 0.157403/0.232841 m`。
- head bias/RMSE：`0.829409/1.713617 -> -0.831287/1.346190 m`。
- 模拟 SEG 2 stage–Q slope：`0.000226 -> 0.000722 m/(m3/s)`；观测为 `0.001844`。
- 模拟 head stage–Q slope：`0.000117 -> 0.000615 m/(m3/s)`；观测为 `0.001706`。
- 模拟 SEG 222 stage–Q slope：`0.000108 -> 0.000107 m/(m3/s)`；观测为 `0.000138`。

Interface checks:

- `LINK_DN=COUPLE=6`，边界索引断言通过。
- 1128 次 commit 全部 `EVALUATED=T`；commit Q gap 为 0。
- `max|RTAIL|=1.1642e-10`，`RFLUX/SEGLOSS=0`。

Blocking finding:

- `JDAY=44430.0034` 出现一次主水体体积 `COMPUTATIONAL WARNING`：spatial change `-947755.54 m3`、temporal change `116524.66 m3`、volume error `-1064280.2 m3`。
- `flowbal.csv` 同时报告初始 `%VOLerror=-127.24044`。原 smoke/scan 验收器只检查 runtime error，没有检查该 warning，因而出现“脚本通过但物理验收不通过”的缺口。
- 已新增 `computational_warning_count` 和硬断言；9 项相关单元测试及 2 项残差分析测试通过。现有 V25 extended 输出在新门禁下明确为 `FAIL (1 warning)`。

Review:

- 边界对齐确实恢复了一部分上游流量响应并显著改善 SEG 2/head RMSE；该索引修复本身应保留。
- 但 V25 还不能作为新基线：主矩阵从 segment 6 求解，`CUS`/volume balance/output ownership 仍可能从 segment 3 开始；hydro 使用 `TAIL_Q_LINK`，temperature/`VOLIN` 仍使用物理 `QIN`。同一接口被不同下游消费者按不同域和流量解释。
- `TAIL_REACH_LENGTH=3770 m` 是 segment 2:5 的单元长度和；segment 2 中心到 segment 6 中心的几何距离为 `3855 m`。这个 2.2% 语义差异须独立修复，但不是百万立方米体积误差的主因。

Next action:

- 先实施 V26 domain-ownership contract：tail 独占 2:5，reservoir 的 `CUS`、主矩阵、balance、water-level output 和 boundary transport 统一从 6 开始，reservoir 所有消费者统一使用 committed interface flux。
- V26 先以“主水体无 computational warning + V24/V25 断言继续通过”为结构门；之后再重构 lumped reach 的总储量/动量闭合。

## Step 8 — V26 domain ownership

Status: complete for short-window structural acceptance

Design:

- 见 `42_v26_tail_reservoir_domain_ownership_design.md`。
- 不把 V25 的精度改善当作接受依据；先消除已确认的状态所有权和边界通量分叉。

Changes:

- tail defined 时 `CUS=TAIL_COUPLE_SEG=6`，tail 2:5 与 reservoir 6+ 不再重叠。
- `layeraddsub` 的四条 upstream-lock 路径均以 `TAIL_COUPLE_SEG` 为下界，不再退回 `CUSMIN=3`。
- reservoir boundary 的 hydrodynamics、temperature source、heat balance 和 `VOLIN` 统一使用 `TAIL_RESERVOIR_Q_USED`。
- 新增 `[V26_DOMAIN_OWNER]`、`[V26_BOUNDARY_CONSUMER]` 及可解析硬断言。
- 第二次 `HYDROINOUT` 可能在 predictor 后刷新物理 Q；新增 matrix 消费前 available-water re-cap，使 reservoir Q 与 tail commit 仍是同一通量。
- exclusive tail domain 下，旧 V2/V4/V5/V6/V8 front markers 不再是必需门；它们描述的是被 V26 所有权契约取代的重叠 front 路径。

Verification:

- Python syntax、2 项 residual tests、10 项 conservation/domain tests：通过。
- reduced console build：通过。
- fresh `TMEND=44431`：正常退出，用时约 `8.5 s`。
- `CUS=6`、`COUPLE=6`、exclusive `T`；12 次 boundary-consumer 样本最大 flux gap 为 0。
- `max|RTAIL|=5.457e-12`，`RFLUX/RCOMB/SEGLOSS/commit gap=0`。
- runtime/computational warning 均为 0；完整 `assert_pass` 通过。
- `flowbal.csv` `%VOLerror` 从 V25 的 `-127.24044%` 降到 `-0.00006133%`。

Short-window accuracy:

- SEG 2 bias/RMSE：`-1.745776/2.912052 m`。
- SEG 222 bias/RMSE：`0.172456/0.272047 m`。
- head bias/RMSE：`-1.918232/3.021638 m`。
- SEG 2/head 模拟 stage–Q slope：`0.002824/0.003135 m/(m3/s)`，观测为 `0.002237/0.002700`。

Review:

- V26 达到结构目标：主水体 balance、输出域和 boundary consumers 终于与接口契约一致；不能为了恢复 V25 较好的 short RMSE 而退回重叠所有权。
- 精度显著退化揭示下一层已知问题：当前只用 segment 2 体积承受整个 2:5 reach 的 `Qin-Qout`，导致一天内 stage 过度下降；V25 较好的结果部分依赖不一致的 reservoir volume/temperature 路径。
- 这不是摩阻或截距校准问题。下一步应把 `TAIL_STORAGE_VOL` 改为整个 tail-owned domain 的 profile volume，并让反演与输出 profile 使用同一几何定义。

Next action:

- 设计 V27 conservative profile-volume closure：保持一个 committed interface flux 和一个总 reach storage，自下游 stage 与上游 stage 构造一致 profile，按 segment 2:5 总体积反演上游 stage。
- 先做几何/反演纯函数与短窗；不直接跳到四个独立 flux 的显式多单元求解器。

## Step 9 — V27 conservative profile volume

Status: complete for short-window acceptance

Changes:

- `TAIL_STORAGE_VOL` 改为 segment 2:5 的 profile volume 总和。
- stage profile 按 segment center distance 插值；segment 2 center 到 segment 6 center 的 `TAIL_REACH_LENGTH=3855 m`。
- minimum storage、predictor cache recheck、matrix 前 re-cap、storage inversion 使用同一个 profile geometry。
- segment 5 stage 不再覆盖 reservoir boundary stage；local transition slope 使用相邻 center spacing。
- 新增 `[V27_PROFILE_STORAGE]` 和 storage/profile identity 硬断言。
- 首次试算暴露旧 `WSE_up<=WSE_dn+25 m` cap 会使 volume 与 stage 分叉；移除接受态 cap，由 autostep 与守恒门处理试算高水位。

Verification:

- 11 项 conservation/domain/profile tests、2 项 residual tests：通过。
- reduced console build：通过。
- fresh `TMEND=44431` 正常退出，用时约 `8.6 s`；完整 `assert_pass` 通过。
- 21 个 profile identity 样本，`max|Vstate-Vprofile|=0.0011204 m3`。
- reach length 全部为 `3855 m`。
- `max|RTAIL|=7.0031e-11`；reservoir/tail、boundary consumer、segment Q gap 均为 0。
- computational warning 为 0；`flowbal %VOLerror=-0.00005456%`。

Short-window comparison:

- V26 -> V27 SEG 2 bias/RMSE：`-1.745776/2.912052 -> -0.893248/1.059306 m`。
- V26 -> V27 SEG 222：`0.172456/0.272047 -> 0.186067/0.277360 m`。
- V26 -> V27 head：`-1.918232/3.021638 -> -1.079315/1.243497 m`。
- V27 SEG 2/head stage–Q slope：`0.000673/0.001000 m/(m3/s)`；观测为 `0.002237/0.002700`。
- 与 V25 short 相比，V27 的 SEG 2/head RMSE 分别高约 `0.107/0.069 m`，但 V27 同时满足 V25 未满足的主水体 volume balance 和全消费者 flux contract。

Review:

- V27 证明 V26 的精度退化主要来自单 segment storage，而不是独占域本身。
- 目前 short 精度已回到 V25 附近，但流量响应幅度仍偏弱；这可能来自线性 profile/上游断面 Manning closure，而不是总储量大小。
- 初始 rejected trial 可出现高 `WSE_up`，但 profile identity、autostep 和最终接受态均成立；extended 需继续观察运行刚性。

Next action:

- 提交并同步 V27 short 检查点。
- 运行 fresh `TMEND=44436.5` extended，要求 V24/V25/V26/V27 与 no-warning 全部门同时通过。
- extended 后再决定是否把线性 profile 换为逐段 standard-step profile；不提前调参。

## Step 10 — V27 extended-window acceptance

Status: complete; V27 accepted as the new structural baseline

Run:

- fresh `alpha=0`、`scope=bht`、`TMEND=44436.5`。
- 正常退出，用时约 `28 s`；完整 `assert_pass` 与 V24/V25/V26/V27 独立断言均通过。

Structural evidence:

- 26 次 interface commit 全部 evaluated；`RFLUX/SEGLOSS/commit gap=0`。
- `max|RTAIL|=3.1105e-10 m3/s`。
- 23 次 reservoir boundary-consumer 样本最大 flux gap 为 0。
- 44 次 profile identity 样本，`max|Vstate-Vprofile|=0.0011204 m3`。
- `CUS=COUPLE=6`，reach length 始终 `3855 m`。
- runtime/computational/fatal marker 均为 0；`flowbal %VOLerror=-0.00005456%`。

Extended metrics (157 accepted samples):

- SEG 2 bias/RMSE：`-0.671199/1.258642 m`。
- SEG 222 bias/RMSE：`0.163293/0.229205 m`。
- head bias/RMSE：`-0.834492/1.332942 m`。
- 模拟/观测 SEG 2 stage–Q slope：`0.000750/0.001844 m/(m3/s)`。
- 模拟/观测 head slope：`0.000648/0.001706 m/(m3/s)`。
- 模拟/观测 SEG 222 slope：`0.000102/0.000138 m/(m3/s)`。

Comparison:

- 相对 V24，SEG 2/SEG 222/head RMSE 分别改善 `0.561967/0.007095/0.380675 m`。
- 相对 V25，三项 RMSE 分别改善 `0.013298/0.003636/0.013248 m`；同时消除了 V25 的 `-127.24%` volume error。
- corrector commit 数从 V25 的 1128 降至 26，运行时间从约 33.6 分钟降至 28 秒。该差异主要来自 active domain 所有权收口后不再反复推进悬空 segment 3:5。

Review:

- V27 同时满足局部 tail mass、reservoir boundary flux、主水体 volume balance、profile geometry identity 和三站精度对照，可以作为后续唯一基线。
- SEG 2/head error–Q correlation 仍为 `-0.9500/-0.9408`，流量响应仅约为观测的 `40.7%/38.0%`。
- `WSE_HYD` 的 Q slope 约 `0.000680`，与接受态同样偏弱；说明剩余缺口不是 profile storage 反演造成，而在 momentum/friction closure。

Next action:

- 用 segment 2:6 各断面上的 friction slope 梯形积分替代当前仅上下游端点平均的能量损失。
- 同一个积分能量式同时用于 `TAIL_STANDARD_RESIDUAL` 和已知 stage 下的 link-flow 反演，避免两个 momentum consumer 再次分叉。
- 不改变 V27 total storage 或任何 Manning 输入参数。

## Step 11 — V28 integrated-energy falsification

Status: rejected at short window; implementation removed

Experiment:

- 在线性距离 profile 的 segment 2:6 断面上计算 `Sf`，按 center spacing 梯形积分能量损失。
- standard-step residual 与 stage-to-Q inversion 共用同一系数式。
- 新增 energy closure 回代诊断；12 项门禁测试和 reduced build 通过。

Short evidence (`TMEND=44431`):

- 20 个 energy samples 全部 valid，`max|Renergy|=1.7764e-15 m`。
- V24–V27 守恒、profile、domain、volume balance 仍全部通过；无 computational warning。
- 但积分后的平衡流量 `Qeq` 多次达到约 `12000–24000 m3/s`，显著高于 committed Q。
- SEG 2/head stage–Q slope 提高到 `0.001229/0.001561`，但 bias/RMSE 恶化为 `-3.453268/3.531463 m` 和 `-3.641449/3.739521 m`。
- V27 同窗 SEG 2/head RMSE 为 `1.059306/1.243497 m`；V28 分别恶化 `2.472157/2.496024 m`。

Review:

- 能量式在数值上闭合，否证的是“中间断面会增加总体阻力”这一物理推断：按当前 bathymetry/profile，中间断面总体更具输水能力，积分反而降低等效阻力。
- slope 改善来自过强排水和整体负偏，不是可接受的响应修复。
- short 已提供明确止损证据，无需运行 extended；V28 源码和验收器均恢复到已提交 V27 基线，仅保留设计与否证记录。

Next action:

- 在 V27 上诊断 `Qstate/Qtarget/Qphysical` 的时间响应、available cap 占比与误差相位，区分弱 slope 是流量状态滞后、线性 profile 形状还是物理 Manning 率定问题。
- 在完成该诊断前不再改变 momentum closure。

## Step 12 — V29 accepted-state response diagnosis

Status: complete; diagnostic accepted, V27 physics unchanged

Changes:

- 在所有 autostep rollback 检查之后写出 `[V29_ACCEPTED_TAIL]`，只采真正接受的 tail 状态。
- 记录 `QPHYS/QSTATE/QTARGET/QMAX/STORAGE/WUP/WDN` 以及 profile 的 `dV/dWup`、`dV/dWdn` 数值偏导。
- 新增接受态解析、累计步长时间、lag/hold、Manning 等效倍率和 segment 2→6→222 水头分解。
- smoke/scan 增加接受态 marker 门禁；不改变任何物理状态、接口通量或 reservoir consumer。

Extended evidence:

- 6010 个接受步；`Qstate/Qphysical` slope/correlation 为 `1.001734/0.960788`，最佳日尺度 lag 为 `0 day`。
- available-water cap 仅 `1/6010`；cache hold fraction `89.60%`，最长 `0.030804 day`。
- 使瞬时 `Qtarget=Qstate` 所需 `FMANN` 倍率中位数 `0.999197`，P10/P90 `0.917768/1.069918`，`91.51%` 在 `0.8–1.2`。
- tail local head slope `-0.0000679`；观测采样对齐后 segment 6→222 与 segment 2→6 head slope 分别为 `0.000668/-0.0000636`。
- `dV/dWup=382663 m2`、`dV/dWdn=224366 m2`；固定 storage 时 `dWup/dWdn≈-0.588`。
- 实际/观测所需 storage–Q slope 为 `475.740/878.411 m3/(m3/s)`，当前响应约为需求的 `54.16%`。

Verification:

- Python tests、reduced build、fresh `TMEND=44436.5`：通过。
- V24–V27 全部门禁继续通过；`max|RTAIL|=3.1105e-10 m3/s`，profile gap max `0.0011204 m3`。
- computational warning 为 0；`flowbal %VOLerror=-0.00005456%`。

Review:

- cap 和单一固定 Manning 倍率不是主要根因；当前摩阻目标在多数接受步已围绕 committed Q 闭合。
- 弱上游响应的直接机制是 profile storage 随流量建立不足，且线性 profile 使下游边界上升对 WUP 产生显著反向牵引。
- segment 6 没有实测水位，尚不能把缺口唯一归因到 tail 或 reservoir；不能据此直接率定粗糙率。

Next action:

- 做 predictor-cache invariance 检查。cache 只应影响性能；若关闭 cache 会显著改变接受态 storage/stage，则先移除这条进入物理状态路径的数值捷径。
- 只有 cache invariance 通过后，才比较 Q-state 动态与 profile shape 两种解释；不提前调 Manning。

## Step 13 — V30 predictor cache removal

Status: complete; accepted as a numerical-correctness cleanup

Invariance experiment:

- 单独令 `TAIL_PREDICT_MAX_SKIP=0`，其余方程和输入不变。
- `Qstate–Qtarget` correlation `0.7804 -> 0.9938`，RMSE `746.14 -> 108.12 m3/s`。
- equivalent `FMANN` P10/P90 `0.9178/1.0699 -> 0.9948/1.0043`。
- hold fraction `89.60% -> 0.0169%`；runtime 仍约 `25 s`。
- SEG 2/SEG 222/head RMSE 只从 `1.258642/0.229205/1.332942` 变为 `1.257266/0.226510/1.326409 m`。

Review:

- cache 不是剩余水位精度的主因，但显著改变接受态 Q 与自适应步进，且没有当前可见的性能收益；作为性能优化的不变性检查失败。
- 不接受只把 `MAX_SKIP` 设为 0 的死代码方案。

Changes:

- 完整删除 predictor cache arrays、flags、skip counter、tolerances 和 reuse 分支。
- `RUN_TAIL_PREDICTOR` 每次都重新执行 `UPDATE_TAIL_STAGE`，之后按原有 save/restore/commit 契约提交 predictor 状态。
- 删除 `[V18_PREDICT_REUSE]` 及 smoke/scan 的旧 skip 门禁；V18 predictor/corrector 和 V24–V29 门禁继续保留。

Verification:

- 16 项 Python tests、reduced build、fresh extended：通过。
- 完整 `assert_pass`、V24–V29 独立门禁：通过。
- `max|RTAIL|=3.8835e-10 m3/s`；profile gap max `0.0010486 m3`。
- computational warning 为 0；`flowbal %VOLerror=-0.00005456%`。

Post-removal metrics:

- SEG 2 bias/RMSE `-0.648357/1.257266 m`。
- SEG 222 bias/RMSE `0.160542/0.226510 m`。
- head bias/RMSE `-0.808898/1.326409 m`。
- 模拟/观测 SEG 2 slope `0.000717/0.001844`；head slope `0.000614/0.001706`。
- storage response fraction of observed requirement `53.45%`。

Next action:

- 复核 V26 exclusive domain 后，tail-owned segment 2:5 的分布源汇是否被遗漏；若源汇链完整，则转向 profile/control-volume geometry。
- 不再把 Q-state lag 或固定 Manning 调整列为当前首要解释。

## Step 14 — V31 corrector state isolation

Status: complete; state-isolation cleanup accepted, initial double-storage hypothesis rejected

Initial hypothesis:

- 从调用顺序看，predictor 与 corrector 都调用 `UPDATE_TAIL_STAGE`，一度怀疑 persistent storage 在同一 W2 timestep 被推进两次。

Variable-level audit:

- `RUN_TAIL_PREDICTOR` 在试算后先恢复完整步初 tail state，只复制 predictor 的 WUP/Qlink/depth 和 segment-derived arrays。
- `TAIL_STORAGE_VOL/Q_STATE/Q_TARGET` 没有从 predictor 复制回来，因此持久 storage 实际没有双推进。
- 旧 corrector 的真实起点是“步初 persistent storage/Q + predictor WUP/Qlink”的混合态；初始双推进判断被 extended 不变性证据和变量链共同证伪。

Changes:

- reservoir 求解后、所有 branch corrector 之前统一恢复一次完整步初 tail state。
- predictor interface arrays 与 reservoir committed Q 不在该 restore 中，接口校正证据和单一通量契约保持不变。
- 新增接受态 `[V31_SINGLE_STEP]`：用 `(Vfinal−Vpre)/dt` 独立验证整步 `Qin−Qinterface`，并比较局部 storage rate。
- 初始化步和 rollback trial 不进入 V31 门禁。

Verification:

- short：989 个样本，`max|RTAIL_full|=3.8835e-10 m3/s`，`max|RATEGAP|=0`。
- extended：5926 个样本，同样的 residual 上限与零 rate gap。
- 17 项 Python tests、reduced build、完整 `assert_pass`、V24–V31 独立门禁：通过。
- profile gap max `0.0010486 m3`；computational warning 0；`flowbal %VOLerror=-0.00005456%`。

Extended review:

- SEG 2/SEG 222/head bias、RMSE 和 slope 与 V30 相同；V31 不是精度修复。
- `Qstate–Qtarget` RMSE `108.12 -> 99.80 m3/s`，只说明 corrector 内部 target 不再读 predictor 派生态。
- tail 2:5 的 distributed 源汇没有遗漏：V26 的 `CUS=6` 使 reservoir 源项从 6 开始分配，tail 控制体只包含物理上游入流与接口出流。

Next action:

- 当前可验证的源汇、整步连续、Q-state、Manning 和 corrector 顺序均已闭合；剩余缺口收敛到“单一线性 profile + 单总 storage”的模型表达能力。
- 下一步先设计可回退的 conservative multi-control-volume 实验；若需要选择 profile 参数、粗糙率率定范围或以 RMSE/流量响应何者优先，则转为用户物理决策点。

## Step 15 — V32 conservative segment-volume foundation

Status: complete; accepted as a no-behavior-change foundation

Problem:

- segment arrays 先按真实 bathymetry/profile 计算几何，随后又被 V17 transition score 缩放 area、hydraulic radius、celerity 和 volume。
- 这些缩放不进入 V27 守恒方程，却使 `TAIL_VOL_SEG` 不能与 `TAIL_STORAGE_VOL` 相加，无法作为多控制体状态起点。

Changes:

- transition 继续记录 score/submergence/slope/Froude/mode，但不再覆盖 segment geometry。
- `TAIL_AREA_SEG/HRAD_SEG/VOL_SEG` 始终保存未缩放 `TAIL_SECTION_PROPS` 与 `AREA*DLX`。
- 新增接受态 `[V32_SEGMENT_VOLUME]` 和硬门：`sum(VSEG)=TAIL_STORAGE_VOL`。

Verification:

- 18 项 Python tests、reduced build、fresh short/extended：通过。
- short 990 个样本，segment/total volume gap max `0.00099947 m3`。
- extended 5927 个样本，gap max `0.0010273 m3`。
- V24–V31 全部门禁继续通过；computational warning 0；`flowbal %VOLerror=-0.00005456%`。
- SEG 2/SEG 222/head bias、RMSE、slope 与 V31 完全相同。

Review:

- V32 没有改善精度，也不应改善；它修复的是 segment state 的语义，使各段 volume 成为唯一总 storage 的真实可加分解。
- 下一步若加入内部 Q，必须同步加入每段 `dVi/dt=Qin_i−Qout_i`；禁止恢复 V16–V18 曾出现的“Q 逐段变化但 storage 不接收差额”。

Next action:

- 设计 V33 conservative multi-control-volume continuity：持久 cell volume、唯一内部界面 flux、局部 available-water cap、逐 cell residual 与 telescoping branch residual。
- 先以 short 结构门判断稳定性；若需要任意 profile exponent 或粗糙率倍率才能成立，停止并请求物理选择。

## Step 16 — V33 local-target preflight

Status: diagnostic complete; direct local-flux activation rejected before implementation

Experiment:

- 不启用多控制体状态；在每个接受步旁路计算 segment 2:5 各下游界面的局部 Manning `Qtarget`。
- 输入只使用 V32 接受态 stage、真实断面、center spacing 和活动算例统一 Manning `n=0.03`。
- 新增 `[V33_LOCAL_TARGET]`、按界面分析器、2 项单元测试及 smoke/scan marker 门禁。
- 诊断不写入 stage、storage、Q state、interface commit 或 reservoir consumer。

Extended evidence:

- 每个界面 5927 个样本，共 23708 个 marker。
- interface 1（segment 2）`Qtarget/Qcommit` 中位数 `0.999903`，P10/P90 `0.994234/1.005544`，`99.865%` 在 ±20%。
- interface 2（segment 3）中位数 `2.325206`，P10/P90 `1.916184/2.489710`，±20% 一致率 `0%`。
- interface 3（segment 4）中位数 `1.543939`，P10/P90 `1.411247/1.738744`，±20% 一致率 `0%`。
- interface 4（segment 5）中位数 `2.535427`，P10/P90 `2.168839/2.951035`，±20% 一致率 `0%`。
- 后三界面的平均 `Qtarget-Qcommit` 分别为 `6094.661/2748.020/7476.003 m3/s`。

Verification:

- 21 项 Python tests、reduced build、fresh short/extended、完整 `assert_pass`：通过。
- V24–V32 全部门禁继续通过；computational warning 0。
- segment/total volume gap max `0.0010273 m3`；`flowbal %VOLerror=-0.00005456%`。
- SEG 2/SEG 222/head bias、RMSE 和 slope 与 V32 完全相同。

Review:

- V32 证明了 cell volume 可守恒；V33 证明了当前局部动量闭合不能直接推广为 cell interface flux。
- 若直接激活，后三个内部界面会从当前 throughflow 的 `1.54–2.54` 倍启动，不能保持已验证基线，并有重现 V28 过度导流的风险。
- 按当前 stage 反推的中位等效 Manning `n` 约为 `0.070/0.046/0.076`；这只是等效阻力需求，不是可直接采用的物理糙率。
- 缺少 segment 3:6 同步水位或独立阻力证据，不能把 profile、几何和局部损失的不可辨识性用自动率定掩盖。

Decision required:

- 选择以现有端点水位 RMSE/slope 为目标进行工程等效阻力率定；或
- 先补充中间水位、断面与糙率约束后再实现多控制体；或
- 保留 V32/V33 结构基线，把该河段交给外部一维非恒定流求解器。

## Step 17 — V34 physical-constraint inventory

Status: complete; repository evidence exhausted, physical decision remains

Inventory:

- Git 中 12 个 `el_obs*.npt` 文件只有两个唯一 SHA-256：坝前与上游各 1 条，其他均为验证 case 的逐字节副本。
- 没有 segment 3:6 的第三个同步水位站；现有观测文件头也不包含测站链桩、高程基准或 segment 映射元数据。
- 8 套 bathymetry 中 6 套为 268 segments、2 套为 284 segments；它们共享主干编号约定和 segment 2:6 `DLX`，主要变化是 `0.25/0.5/2 m` 层厚、初始 `ELWS`、统一 `n=0.03/0.035` 与支流分区。
- 候选 bathymetry 没有附带 segment 3:6 独立断面校核、survey metadata、局部损失系数或分段糙率来源；其中两份还是逐字节重复文件。
- Git 中常见外部一维模型工程文件数量为 0。

Historical check:

- 旧基线 `G5/G6` 的 `MANN x1.2 + AREA x0.9` 曾使坝前 RMSE 恶化到 `10–11 m`，说明盲调面积/糙率有明显 common-mode 副作用。
- 该结果来自 V24 前状态，只作为风险证据，不能直接替代 V33 上的率定或确定有效阻力。

Review:

- 仓库现有两端水位只能约束总 head，不能唯一分配 segment 2:6 的局部坡降，也不能区分 profile、几何与局部损失。
- 因此不能自动把 V33 反推的 `n≈0.070/0.046/0.076` 写回模型。
- 数据优先路线至少需要一个中间水位站及其链桩/高程基准、segment 2:6 断面来源校核和阻力先验；分别识别三个内部阻力则需要更多空间观测或明确正则化。
- 无新增数据时，继续工作必须由用户授权工程等效闭合及其验收目标；外部求解器路线则需选择求解器与耦合语义。

Decision required:

- A：补充/指定物理数据；
- B：授权以端点观测为目标的工程等效闭合；
- C：选择外部一维求解器耦合。

## Step 18 — V35 multi-station waterline validation

Status: complete; route A is useful, original V33 activation path remains rejected

Input QA:

- 2021/2023 共 12 个 NPT 通过文件头、8760 点时间轴、单调 JDAY、逐时步长和 500–650 m 数值门禁。
- 10 个内部站的处理分类、gap 小时数、区间数和最大区间全部对账；2021 XLD/BHT 与既有端点文件逐字节一致。
- extended 窗口 JDAY 44430.0–44436.5 内五个新增站均为 157 个未处理原始点；与 2021 工作簿逐点复核共 785 点，0.01 m 精度下差异为 0。
- 全年自动处理尚不能直接视为物理验收：2021/2023 分别插值 293/885 点，最长连续 68/74 h，且工作簿未明确给出高程基准元数据。

Mapping review:

- 转换包映射为 XLD/SS/HH/SLB/YMT/SJ/BHT → segment 222/215/168/116/57/26/2。
- XLD 0 km 的边界/中心参考差异会使 SS 改到 segment 214；两种映射 RMSE 只差 `0.000016 m`，不影响结论。

Extended evidence:

- XLD、SS、HH、SLB、YMT、SJ、BHT bias 为 `0.161/0.298/0.276/0.075/-0.022/-0.804/-0.648 m`。
- 模拟/观测 stage–Q slope 比率沿上游依次为 `0.738/0.699/0.664/0.625/0.573/0.409/0.389`。
- YMT→SJ 观测/模拟平均 head 为 `0.900/0.118 m`，bias `-0.783 m`，head–Q slope 比率 `0.252`。
- SJ→BHT 观测/模拟平均 head 为 `10.667/10.823 m`，bias `0.156 m`，但动态 slope 比率仍只有 `0.383`。
- 用观测 BHT/YMT 端点构造单线性 profile，在 SJ 处仍高估 `5.137 m`，RMSE `5.211 m`。

Review:

- 新数据把主要静态坡降缺口定位在约 segment 26:57，而非当前 tail-owned 2:5；它不支持激活 V33 的 segment 2:5 局部 target。
- 现有单总 storage + 单线性 profile 不能原样扩到 YMT；至少需要 BHT–SJ、SJ–YMT 两个宏观状态区。
- segment 28 是 BR2 汇入主干的位置。若 ownership 跨过该点，必须同时接管支流水量、温度和组分，不能仅把 `TAIL_FIXED_MIN_NSEG` 从 4 改大。

Next action:

- 设计 V36 observation-anchored macro-domain preflight，先闭合候选控制域、支流源汇和接口状态，再决定是否运行可回退的域扩展实验。

## Step 19 — V36 observation-anchored domain scan

Status: complete; optional domain override accepted as infrastructure, single-state expansion rejected

Changes:

- 将 `TAIL_FIXED_MIN_NSEG` 改为逐 branch 数组，并把诊断上限扩到 64；默认值仍为 4。
- 新增可选 `tail_domain.opt`（`JB NSEG`）和 `[V36_TAIL_DOMAIN_CONFIG]`；文件缺失时不改变基线。
- 建立 current、stop-before-BR2、two-zone-to-YMT 三种候选域的 ownership、station、junction 和 source-contract 清单。
- 扫描 `NSEG=4/8/12/16/20/24/25/26`，每个案例都运行完整守恒门禁和 V35 多站指标。

Evidence:

- 所有 8 个案例均无 computational warning，V24/V31 residual 不超过 `3.57e-9 m3/s`，segment volume gap 不超过 `0.0086 m3`。
- `NSEG=26` 把 YMT→SJ head bias 从 `-0.783 m` 改为 `-0.125 m`，但 BHT bias 从 `-0.648 m` 恶化到 `+1.882 m`，SJ→BHT head bias 恶化到 `+2.306 m`。
- 各站和区间的动态 slope 没有形成一致改善；不存在稳健的单状态 `NSEG`。
- 最新无配置 fresh extended 保持 V35 基线指标和 `CUS=COUPLE=6`、reach `3855 m`。

Review:

- 不从扫描中挑选“最佳 NSEG”；单状态扩域只是搬移空间误差。
- 跨过 segment 28 会纳入 BR2 汇流，必须新增支流水量、温度和组分的守恒契约。
- 最小正确结构仍是以 SJ 为接口的 BHT–SJ、SJ–YMT 两个独立状态区。

Next action:

- 先对 BHT–SJ 宏接口做只读动量闭合预检，不激活第二状态或新通量。

## Step 20 — V37 BHT–SJ macro-interface preflight

Status: complete; direct target activation rejected, engineering-equivalent resistance identified

Changes:

- 新增可选 `tail_macro.opt`（`JB SEG`），本次以 SJ/segment 26 为只读宏接口。
- accepted state 同时记录 BHT 单断面 local target 与 segment 2:26 逐断面积分摩阻、端点速度头的 aggregate target。
- 诊断不拥有 volume、不提交 Q、不改变 stage 或 reservoir consumer；分析器同时用实测 BHT–SJ head 做边界敏感性复核。

Evidence:

- 5927 个状态中，local `Qtarget/Qcommit` 中位数 `0.452`，aggregate 为 `1.537`；两者 ±20% 一致率分别为 `0.051%/0%`。
- 145 个实测重叠时刻的 BHT–SJ 平均 head 为 `10.676 m`，模拟为 `10.560 m`；替换实测 head 后 local/aggregate target-to-physical 中位数为 `0.436/1.626`。
- 若把未解析损失合并成逐段统一工程等效 Manning，观测约束所需 `n` 中位数 `0.04577`，P10/P90 `0.04270/0.05053`；这不是已验证物理糙率。
- V37 与无诊断基线的 `wl.csv`、`flowbal.csv` SHA-256 分别逐字节相同；V24–V33 门禁继续通过，无 computational warning。

Review:

- 路线 A 已把不可辨识问题从 segment 2:5 三个局部阻力收敛为 BHT–SJ 一个宏观等效阻力，并给出稳定候选范围。
- 现有 local 与 aggregate 原始闭合都不能直接激活；`n≈0.046` 也不能写回全库统一 Manning。
- 下一步需要用户决定是否授权把该范围作为 BHT–SJ 工程等效先验，或继续补齐高程基准、断面和阻力来源后再实施两状态模型。
