# V11 固定尾段物理域实现记录
本页回答什么问题：`V11` 这一版具体把什么从“隐含语义”改成了“显式结构”，它和 `V10` 的关系是什么，以及它为什么属于第二阶段的结构性起步而不是新的物理改造。

Updated: 2026-04-20

## 1. 这版的定位

`V10` 已经让 tailreach 具备了：

- `stage`
- `storage`
- `effective discharge`
- 与主库区入流的松弛耦合

但它仍然有一个结构问题：

- 尾段物理域实际上还隐含在 `FRONT_SEG / TAIL_UPSEG / TAIL_DNSEG` 这些“单链接变量”里

这会带来两个后续开发问题：

1. 继续做 `V12/V13` 时，很难把尾段当成一个真正固定的物理域来扩展
2. 容易把“尾段的物理域”与“当前 reach 的耦合截面”混在一起

所以 `V11` 的目标不是改方程，而是先把“域”这件事从隐式改成显式。

## 2. 代码上做了什么

### 2.1 新增显式域元数据

新增了四个核心变量：

- `TAIL_DOMAIN_US`
- `TAIL_DOMAIN_DS`
- `TAIL_DOMAIN_NSEG`
- `TAIL_DOMAIN_DEFINED`

位置：

- [w2modules.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/w2modules.F90:126)
- [input.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/input.F90:316)
- [init.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/init.F90:57)

### 2.2 在 `init-geom.F90` 中显式定义尾段域

现在对 protected upstream branch，会显式定义：

- `TAIL_DOMAIN_US = IUPHYS`
- `TAIL_DOMAIN_DS = MAX(FRONT_SEG, IUPHYS)`
- `TAIL_DOMAIN_NSEG = DS - US + 1`

这一步的重点不是扩长尾段，而是把当前已有的尾段物理范围正式命名出来。

位置：

- [init-geom.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/init-geom.F90:483)

### 2.3 新增 V11 诊断

新增日志：

- `[V11_TAIL_DOMAIN]`

内容包括：

- `JB`
- `US`
- `DS`
- `NSEG`
- `LINK_US`
- `LINK_DN`
- `DEFINED`

这样以后再做 `V12/V13` 时，可以直接看出“尾段物理域”和“当前耦合链接”是不是还一致。

## 3. 输出语义的改动

在 [outputa2w2tools.F90](/C:/Users/NING/Desktop/v455/w2source_v455_2_11_2026/outputa2w2tools.F90:136) 里，`SEG 2` 的输出覆盖不再只依赖：

- `TAIL_COUPLED`
- `TAIL_STAGE_VALID`
- `I == TAIL_UPSEG`

现在还显式要求：

- `TAIL_DOMAIN_DEFINED`
- `I` 落在 `[TAIL_DOMAIN_US, TAIL_DOMAIN_DS]` 内

也就是说，尾段输出语义开始从“单点链接驱动”变成“域内链接驱动”。

## 4. smoke 验证

`analysis/run_w2_v0_v1_smoke.py` 已提升为要求：

- `[V11_TAIL_DOMAIN]`

短窗：

- [smoke-summary-20260420-085922.csv](/C:/Users/NING/Desktop/v455/analysis/verification/w2_v0_v1_smoke/results/smoke-summary-20260420-085922.csv)

延长窗：

- [smoke-summary-20260420-090020.csv](/C:/Users/NING/Desktop/v455/analysis/verification/w2_v0_v1_smoke/results/smoke-summary-20260420-090020.csv)

长窗：

- [smoke-summary-20260420-090652.csv](/C:/Users/NING/Desktop/v455/analysis/verification/w2_v0_v1_smoke/results/smoke-summary-20260420-090652.csv)

三组都满足：

- `has_v11_tail_domain = 1`
- `seg2_valid_count > 0`
- `has_runtime_error = 0`
- `has_late_seg2_add = 0`

## 5. 这版没有做什么

`V11` 明确没有做这些事：

- 没有改变 `V10` 的 tailreach 方程
- 没有改变 current coupling strength
- 没有引入新的 discharge / momentum 状态
- 没有扩大当前实际参与求解的 tailreach reach 长度

所以它不是“新的物理版本”，而是“第二阶段的域结构基线”。

## 6. 为什么这版仍然重要

这版的重要性在于：

- 以后谈 `V12`，不再是“在 `TAIL_UPSEG/TAIL_DNSEG` 上继续打补丁”
- 而是“在一个显式的 fixed tail domain 上扩展内部 reach 状态”

换句话说，`V11` 是把第二阶段的讨论对象正式从：

- `single tail link`

换成：

- `fixed tail physical domain`

## 7. 对后续版本的含义

从 `V11` 开始，后续版本的重点就应该转向：

- `V12`: 在固定尾段域上建立真正的 reach state evolution
- `V13`: 让过渡状态成为 reach 内部动态状态，而不是外挂状态机

这也意味着：

- 当前最值得继续推进的，不再是再加一个 marker 或再包一层弱反馈
- 而是让 fixed tail domain 内部真正有自己的 discharge / momentum 结构
