# References And Evidence Map

本页回答什么问题：这批专题文档中的来源编号分别指向什么材料、引用时应该怎样使用、哪些结论对应哪些源码和文献证据。

## 使用约定

- 文献编号使用 `L1` 到 `L8`。

- 源码编号使用 `C1` 到 `C7`。

- 文档正文中若写“代码证据：`C1`、`C3`；文献支撑：`L1`、`L5`”，表示该判断至少由这些来源共同支撑。

- 后续若继续补充文献，优先延续现有编号规则，不要随意改动已引用编号。

## 摘录限制

- 对手册和论文的直接引文应保持极短，只在确实需要保留原词时引用。

- 后续扩写报告时，优先用自己的话概括，不要长段复制官方手册或论文原文。

- 如果要保留英文原词，优先保留模型假设、变量名和公式名称，其他部分尽量中文转述。

## 文献来源

| 编号 | 类型 | 来源 | 链接或路径 | 在本专题中的用途 |
| --- | --- | --- | --- | --- |
| `L1` | 官方手册 | CE-QUAL-W2 v4.5 Part 1 Intro | [online PDF](https://cee.pdx.edu/w2/W2manual45_Part1_Intro_rev9.pdf) | 说明模型定位、典型适用对象和总体限制 |
| `L2` | 官方手册 | CE-QUAL-W2 v4.5 Part 2 Theory | `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\User Manual\W2manual455_Part2_Theory_rev0.pdf` | 说明自由液面、静压、输运与理论框架 |
| `L3` | 官方资料 | USACE ERDC CE-QUAL-W2 fact sheet (2014) | [ERDC fact sheet](https://www.erdc.usace.army.mil/Media/Fact-Sheets/Fact-Sheet-Article-View/Article/554171/ce-qual-w2/) | 作为工程能力边界和定位说明 |
| `L4` | 原始手册 | Cole & Wells (2003) CE-QUAL-W2 manual v3.1 | [PDX Scholar](https://pdxscholar.library.pdx.edu/cengin_fac/140/) | 作为早期理论和局限性说明 |
| `L5` | 方法论文 | Zhang et al. (2020), Applied Mathematical Modelling | [ScienceDirect](https://www.sciencedirect.com/science/article/pii/S0307904X20301049) | 支撑局部耦合迭代和结构物平滑切换 |
| `L6` | 扩展论文 | Almeida et al. (2015), Ecological Modelling | [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0304380014004943) | 支撑“保留主框架、局部补强过程模块”的思路 |
| `L7` | 工程应用 | Kim & Chung (2024), Journal of Hydrology: Regional Studies | [ScienceDirect](https://www.sciencedirect.com/science/article/pii/S2214581824004130) | 支撑“边界输入质量先决定预测上限” |
| `L8` | 系统综述 | Mota Benicio et al. (2024), Water | [MDPI](https://www.mdpi.com/2073-4441/16/24/3556) | 支撑 laterally averaged 模型的系统性能力边界判断 |

## 源码来源

| 编号 | 文件 | 路径 | 在本专题中的用途 |
| --- | --- | --- | --- |
| `C1` | `w2_main.f90` | `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\w2_main.f90` | 主循环、自由液面解、`U` 更新、`QC` 校正、`W` 诊断 |
| `C2` | `hydroinout.F90` | `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\hydroinout.F90` | 源汇、结构物、内外边界入口 |
| `C3` | `gate-spill-pipe.f90` | `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\gate-spill-pipe.f90` | 自由/淹没出流分段切换 |
| `C4` | `waterbody.f90` | `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\waterbody.f90` | 内部水头和跨水体传播 |
| `C5` | `az.f90` | `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\az.f90` | 垂向混合闭合、上下限和稳定度响应 |
| `C6` | `layeraddsub.F90` | `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\layeraddsub.F90` | 活动层增减阈值与离散调整 |
| `C7` | `init-u-elws.f90` | `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\init-u-elws.f90` | 正常水深初始化和起始流速设置 |

## 结论映射

| 结论主题 | 主要代码证据 | 主要文献证据 |
| --- | --- | --- |
| W2 更像 laterally averaged、hydrostatic、自由液面隐式解加速度后校正的框架 | `C1` `C2` `C7` | `L1` `L2` `L4` |
| 回水区强切换是模型短板而非完全失效 | `C1` `C3` `C4` | `L1` `L4` `L8` |
| 纵向前沿推进偏快与分裂推进、边界传播、结构物切换有关 | `C1` `C2` `C3` `C4` | `L2` `L5` `L8` |
| 垂向响应偏硬与诊断式 `W`、`AZ` 闭合、层调整阈值有关 | `C1` `C5` `C6` | `L1` `L2` `L4` |
| 单个中间水库最值得优先补强边界、结构物和局部耦合 | `C1` `C2` `C3` | `L5` `L7` `L8` |

## 后续补充建议

- 如果后续继续扩展文献，优先补方法论文和工程应用，不必重复堆叠一般性综述。

- 如果后续进入源码实现阶段，可在本页后续追加“参数接口映射”和“测试案例映射”两张表，继续复用当前编号体系。
