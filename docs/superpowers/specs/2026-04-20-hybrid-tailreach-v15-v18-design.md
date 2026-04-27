# Hybrid Tailreach V15-V18 Design

本页回答什么问题：在 `V11-V14` 已经证明“库尾需要单独计算”之后，如何把当前的单段 `tailreach prototype` 推进成一个真正的多段局部 reach，并与主库区 W2 形成更完整、更可验证的 hybrid water-surface solver。

Updated: 2026-04-20

## 1. 背景与本设计要解决的真实问题

当前代码已经完成了两件重要的事情：

- 它不再让 `SEG 2` 在数值上彻底消失，`SEG 2` 与 `SEG 222` 都已经可以稳定输出并做双站点对比。
- 它已经证明了“尾段单独算、再与主库区拼接”这个方向是正确的，因为一旦尾段 `stage/discharge` 真正开始参与主库区入流闭合，`SEG 2-SEG 222` 的水面差就开始出现可测的改善。

但 review 也说明了当前原型的上限：

- `V11` 名义上引入了 `fixed tail domain`，但当前案例里实际仍退化成 `US=2, DS=2, NSEG=1`。
- `V13` 的 transition-state 还没有真实覆盖河流控制态，当前长窗里 `TAIL_CONTROL_MODE` 只有 `1` 和 `2`。
- `V14` 虽然已经有 predictor/corrector 和 rollback-safe tail state，但 transition-dependent closure 还没有完整进入同一步耦合。

因此，下一阶段的核心任务不是“再加反馈项”，而是把当前的单段 `tailreach sidecar` 推进成一个真正的多段局部 reach。

## 2. 设计目标

本设计的目标分成三个层次。

### 2.1 物理目标

在一个固定的尾段物理域中，连续表达这三种状态，而不是用拓扑开关去近似它们：

- 河流控制态
- 回水过渡态
- 淹没库区态

这里的“过渡段”不是固定长度的一小段，而是固定物理域中的一个动态状态带。

### 2.2 数值目标

让尾段域内部拥有自己的空间分布和时间记忆：

- 不再只有一个 `TAIL_WSE_UP` 和一个 `TAIL_Q_LINK`
- 而是拥有逐段的 `stage / depth / area / storage / discharge / transition-state`

同时保持当前已经验证过的稳定性特征：

- 与 autostep 兼容
- timestep 被拒绝时主库区和 tailreach 一起 rollback
- 能继续沿用 `analysis/run_w2_v0_v1_smoke.py` 做短窗、延长窗、长窗验证

### 2.3 工程目标

后续的每一步实现都必须继续围绕三项指标同时验收，而不再回到单点校准：

- `SEG 2`
- `SEG 222`
- `SEG 2 - SEG 222`

## 3. 方案比较

### 方案 A：继续扩展单段 sidecar

做法：

- 继续保留单段 `TAIL_UPSEG / TAIL_DNSEG`
- 增加更多闭合项和更多松弛反馈

优点：

- 侵入小
- 开发成本最低

缺点：

- 仍然没有空间分布
- 仍然无法让河流段长度、过渡段长度、库区段长度在固定物理域中自然变化
- 很容易继续停在“能解释一点，但做不准水面线”的层面

### 方案 B：固定多段尾段 reach + 主库区 hybrid coupling

做法：

- 在 `IUPHYS` 下游定义一个固定长度的尾段物理域
- 在该物理域内用多段 `1D laterally-averaged reach` 表达 `stage / discharge / transition-state`
- 下游与主库区通过接口水位和接口出流耦合

优点：

- 能同时解决“单段 tail domain”与“过渡态只是外挂分类器”这两个核心短板
- 和当前 `V11-V14` 的实现路径连续
- 风险可控，适合在现有 W2 主求解器外侧渐进推进

缺点：

- 会新增一批逐段状态数组
- 需要重新定义 `tail domain`、`front semantics` 与 `reservoir interface` 的边界

### 方案 C：直接嵌入完整 1D dynamic-wave tail solver

做法：

- 在当前 W2 里直接嵌入更完整的 1D 动波尾段求解器
- 更强地重写主库区上游边界求解链

优点：

- 理论潜力最高

缺点：

- 风险最大
- 很容易破坏当前已经得到的稳定性和 rollback 语义
- 在当前阶段会把 review 发现的两个具体问题和更大范围的重构风险混在一起

### 推荐方案

推荐方案 B。

原因是：它足够解决当前最真实的结构性短板，又不需要推翻已经通过验证的 `V11-V14` 骨架。

## 4. 目标架构

目标架构由两层求解器组成。

### 4.1 主库区求解器

主库区继续保留现有的 W2 主链：

- laterally averaged
- hydrostatic
- 自由水面隐式求解
- 纵向速度更新
- `QC` 修正
- 垂向速度诊断

这部分不在本阶段重写。

### 4.2 尾段 reach 求解器

新增一个固定多段局部 reach。它不是完全独立的模型文件，而是嵌入当前代码中的一个局部子系统。

它应满足：

- 物理域固定存在
- 不再依赖 `CUS` 或 `FRONT_SEG` 的移动来决定 reach 是否存在
- 内部按段保存状态
- 下游通过接口与主库区交换 `stage` 和 `discharge`

### 4.3 主库区与 tailreach 的接口

接口必须最少交换三类量：

- `tail -> reservoir`: 尾段末端有效出流
- `reservoir -> tail`: 主库区接口水位
- `tail -> front semantics`: 尾段内部的过渡状态，用于替代当前 front patch 的主要物理来源

## 5. 固定尾段物理域的定义

本设计采用“固定连续尾段域”的表达，不使用离散的 segment 列表。

### 5.1 域的边界

对每个耦合分支定义：

- `TAIL_DOMAIN_US(JB)`：尾段物理域上边界
- `TAIL_DOMAIN_DS(JB)`：尾段物理域下边界
- `TAIL_DOMAIN_NSEG(JB)`：尾段段数
- `TAIL_COUPLE_SEG(JB)`：尾段与主库区的接口段，下游紧邻 `TAIL_DOMAIN_DS`

设计约束：

- `TAIL_DOMAIN_US(JB) = IUPHYS(JB)` 保持不变
- `TAIL_DOMAIN_DS(JB)` 不再由 `FRONT_SEG(JB)` 驱动，而由一个固定的尾段长度规则决定
- `TAIL_COUPLE_SEG(JB) = TAIL_DOMAIN_DS(JB) + 1`

### 5.2 固定长度策略

本设计采用“固定尾段段数”策略，而不是“跟随当前活动段动态裁切”策略。

首版建议引入：

- `TAIL_FIXED_MIN_NSEG`

默认行为：

- `TAIL_DOMAIN_DS(JB) = MIN(IUPHYS(JB) + TAIL_FIXED_MIN_NSEG - 1, DS(JB) - 1)`
- `TAIL_DOMAIN_NSEG(JB) >= 2`

这样做的意义是：

- 先强制让 tail domain 摆脱 `NSEG=1`
- 让多段 reach 有一个稳定、可验证的最小工作域
- 后续再根据指标决定是否需要更长的固定域

### 5.3 与 `CUSMIN` 的关系

本设计要求：

- `CUSMIN(JB)` 不再只表示“语义上的保护活动起点”
- 它必须被约束到 `TAIL_COUPLE_SEG(JB)` 下游

换句话说，尾段 reach 负责固定域内的 prefix，主库区从 `TAIL_COUPLE_SEG` 开始进入自己的主求解域。

## 6. 尾段内部状态设计

### 6.1 逐段状态

每个 tail segment 都需要逐段状态，而不是 branch-level 单值。

建议新增的逐段数组如下，统一采用 `(MAX_TAIL_SEG, NBR)` 维度：

- `TAIL_SEG_INDEX`
- `TAIL_STAGE_SEG`
- `TAIL_DEPTH_SEG`
- `TAIL_AREA_SEG`
- `TAIL_HRAD_SEG`
- `TAIL_VOL_SEG`
- `TAIL_Q_SEG`
- `TAIL_Q_TARGET_SEG`
- `TAIL_TRAVEL_TIME_SEG`
- `TAIL_CELERITY_SEG`
- `TAIL_TRANSITION_SEG`
- `TAIL_SUBMERGENCE_SEG`
- `TAIL_LOCAL_SLOPE_SEG`
- `TAIL_FROUDE_SEG`
- `TAIL_MODE_SEG`

其中：

- `TAIL_STAGE_SEG` 和 `TAIL_DEPTH_SEG` 是几何/水位主状态
- `TAIL_Q_SEG` 是逐段下泄流量状态
- `TAIL_TRANSITION_SEG` 是逐段控制状态

### 6.2 聚合状态

为了兼容现有输出和接口，保留少量 branch-level 聚合状态：

- `TAIL_WSE_UP`
- `TAIL_WSE_DN`
- `TAIL_Q_LINK`
- `TAIL_STORAGE_VOL`

但它们不再是基础状态，而是逐段状态的聚合结果。

## 7. 过渡态设计

### 7.1 基本原则

过渡态不再是单个 `FRONT_STATE -> FRONT_TRANSITION` 的外挂映射，而是 tail domain 内每一段的内部状态。

### 7.2 逐段 transition-state

每一段计算：

- `TAIL_TRANSITION_SEG(IS, JB) in [0, 1]`

建议综合以下量：

- `TAIL_SUBMERGENCE_SEG`
- `TAIL_LOCAL_SLOPE_SEG`
- `TAIL_FROUDE_SEG`

但与当前 `V13` 的区别是：

- submergence 不再直接用作全段主导项
- 必须允许在长窗里真实出现 `river / transition / reservoir` 三类模式

### 7.3 transition-state 对闭合的控制

逐段 transition-state 应连续影响：

- 有效过水断面
- 水力半径
- 局部阻力
- 波速/传播时间
- 接口出流释放关系

这意味着：

- `FRONT_TRANSITION` 将退化为一个输出给旧语义层的映射量
- 真正的控制逻辑转移到 `TAIL_TRANSITION_SEG`

## 8. 求解顺序

目标求解顺序如下。

### 8.1 Predictor

在每个 timestep 内：

1. 读取上一步 tailreach 已提交状态
2. 使用当前物理来流和上一时步主库区接口水位，推进 tailreach predictor
3. 得到 predictor 版本的：
   - `TAIL_STAGE_SEG`
   - `TAIL_Q_SEG`
   - `TAIL_TRANSITION_SEG`
   - `TAIL_Q_LINK`
   - `TAIL_WSE_DN`

### 8.2 Reservoir solve

主库区用 predictor 后的：

- 尾段末端接口水位
- 尾段有效出流

推进本步主水动力。

### 8.3 Corrector

主库区求解结束后：

1. 用新的主库区接口水位重算 tailreach corrector
2. 更新并提交逐段 tail state

### 8.4 Rollback

若 timestep 被 autostep 拒绝：

- 主库区状态回滚
- tailreach 逐段状态也必须一起回滚

现有 `V14` 的 rollback 语义要完整继承到逐段数组。

## 9. 与现有前沿状态机的关系

当前 `layeraddsub.F90` 里的前沿状态机不会被立即删除，但职责会收缩。

它继续负责：

- 最小湿润厚度
- 最小几何保护
- 与现有 segment add/sub 机制的兼容

它不再负责：

- 主要的过渡物理判断
- 主要的 river/reservoir 控制分类

换句话说，`FRONT_STATE` 留作语义层，`TAIL_TRANSITION_SEG` 接管物理层。

## 10. 验收标准

### 10.1 结构验收

必须满足：

- `TAIL_DOMAIN_NSEG(JB) > 1`
- `TAIL_STAGE_SEG / TAIL_Q_SEG / TAIL_TRANSITION_SEG` 已真实参与运行
- rollback 对逐段 tail state 生效

### 10.2 运行验收

必须继续满足：

- 短窗 smoke 通过
- 延长窗 smoke 通过
- 长窗 smoke 通过
- `has_runtime_error = 0`

### 10.3 物理验收

必须同时关注：

- `SEG 2`
- `SEG 222`
- `SEG 2 - SEG 222`

而且 transition-state 的模式集必须在代表性长窗中覆盖：

- `0 = river`
- `1 = transition`
- `2 = reservoir`

如果仍然只有 `[1, 2]`，说明 reach 还没有真正进入河流控制表达。

## 11. 非目标

本阶段明确不做以下事情：

- 不重写整个 W2 主库区自由水面求解器
- 不把库区整体切换成完整 1D/2D/3D 动波
- 不把 `distributed` 或全局糙率调参重新变回主路线
- 不以单点 `SEG 222` 水位贴合为阶段目标

## 12. 成功标准

本设计完成后，代码应从现在的：

- `hybrid tailreach prototype`

推进成：

- `multi-segment hybrid tailreach solver skeleton`

这不等于最终问题全部解决，但它应至少做到：

- 尾段不再是单段 sidecar
- 过渡态不再只是外挂分类器
- 主库区和 tailreach 的耦合不再只交换单一 `stage/link flow`

达到这个状态之后，后续优化才真正有希望回答你最初的问题：W2 在保持 laterally averaged 框架下，到底能被改造到什么程度，才能更真实地模拟库尾河流态到淹没态的连续切换。
