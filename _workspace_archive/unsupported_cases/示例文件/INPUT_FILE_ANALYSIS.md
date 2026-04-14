# CE-QUAL-W2 输入文件分析文档

## 概述

本分析文档描述 `v455/示例文件/InputFiles/` 目录下各输入文件的作用，以及它们如何被代码读取、与 `w2_con.csv` 主配置文件的互动关系。

---

## 一、文件分类总览

### 1.1 地形与几何文件

| 文件名 | w2_con.csv 变量 | 代码读取位置 | 用途描述 |
|--------|----------------|-------------|---------|
| bth1.csv | BTHFN(JW) | input.F90:2252 | 水体地形/深度数据 |
| Detroit.w2l | (内嵌) | init-geom.F90:314 | 湖库几何构型 |

### 1.2 气象强迫文件

| 文件名 | w2_con.csv 变量 | 代码读取位置 | 用途描述 |
|--------|----------------|-------------|---------|
| metDetroit2002.csv | METFN(JW) | input.F90 (MetFileRegion) | 气象数据：气温、露点、风速、云量、辐射 |

### 1.3 流量边界文件

| 文件名 | w2_con.csv 变量 | 代码读取位置 | 用途描述 |
|--------|----------------|-------------|---------|
| 2002_NSant_Q_corr.npt | QINFN(1) | hydroinout.F90 | 支流1 入流流量 |
| 2002_BreiBu_Q.npt | QINFN(2) | hydroinout.F90 | 支流2 入流流量 |
| 2002_Blowout_Q.npt | QINFN(3) | hydroinout.F90 | 支流3 入流流量 |
| 2002_Kinney_Q_est.npt | QINFN(4) | hydroinout.F90 | 支流4 入流流量 |
| q3.npt | (湿地) | hydroinout.F90 | 湿地流量 |
| qwd_dss.npt | QWDFN | hydroinout.F90 | 侧向入流/分布式入流 |

### 1.4 水温边界文件

| 文件名 | w2_con.csv 变量 | 代码读取位置 | 用途描述 |
|--------|----------------|-------------|---------|
| 2002_NSant_T.npt | TINFN(1) | hydroinout.F90 | 支流1 水温 |
| 2002_BreiBu_T.npt | TINFN(2) | hydroinout.F90 | 支流2 水温 |
| 2002_Blowout_T.npt | TINFN(3) | hydroinout.F90 | 支流3 水温 |
| 2002_Kinney_T_est.npt | TINFN(4) | hydroinout.F90 | 支流4 水温 |
| 2002_tdt_br1-4F.npt | TDTFN(JB) | hydroinout.F90 | 指定时间水温 |

### 1.5 水质边界文件

| 文件名 | w2_con.csv 变量 | 代码读取位置 | 用途描述 |
|--------|----------------|-------------|---------|
| 2002_NSant_wq.npt | CINFN(1) | hydroinout.F90 | 支流1 水质(溶解氧、营养物等) |
| 2002_BreiBu_wq.npt | CINFN(2) | hydroinout.F90 | 支流2 水质 |
| 2002_Blowout_wq.npt | CINFN(3) | hydroinout.F90 | 支流3 水质 |
| 2002_Kinney_estBBr_wq.npt | CINFN(4) | hydroinout.F90 | 支流4 水质 |
| 2002_qdt_wq1-4BBr.npt | CDTFN(JB) | hydroinout.F90 | 指定时间水质 |

### 1.6 水平通量文件

| 文件名 | w2_con.csv 变量 | 代码读取位置 | 用途描述 |
|--------|----------------|-------------|---------|
| euh_br1-4.npt | EUHFN(JB) | hydroinout.F90 | 上游能量通量 |
| tuh_br1-4.npt | TUHFN(JB) | hydroinout.F90 | 上游水温通量 |
| cuh_br1-4.npt | CUHFN(JB) | hydroinout.F90 | 上游水质通量 |
| edh_br1-4.npt | EDHFN(JB) | hydroinout.F90 | 下游能量通量 |
| tdh_br1-4.npt | TDHFN(JB) | hydroinout.F90 | 下游水温通量 |
| cdh_br1-4.npt | CDHFN(JB) | hydroinout.F90 | 下游水质通量 |

### 1.7 结构物控制文件

| 文件名 | w2_con.csv 变量 | 代码读取位置 | 用途描述 |
|--------|----------------|-------------|---------|
| 2002_tpr_detroit1-4.npt | TPRFN(JB) | gate-spill-pipe.f90 | 斗门/泵时序控制 |
| 2002_qdt_br1-4.npt | QDTFN(JB) | hydroinout.F90 | 指定日期流量 |
| 2002_pre_detroit1-4.npt | (前置) | gate-spill-pipe.f90 | 前置水位条件 |

### 1.8 输出配置/其他

| 文件名 | w2_con.csv 变量 | 代码读取位置 | 用途描述 |
|--------|----------------|-------------|---------|
| snp1.opt | SNPFN(JW) | outputa2w2tools.F90 | 快照输出控制 |
| prf1.opt | PRFFN(JW) | outputa2w2tools.F90 | 剖面输出控制 |
| cpl1.opt | CPLFN(JW) | outputa2w2tools.F90 | 耦合输出控制 |
| spr1.opt | SPRFN(JW) | outputa2w2tools.F90 | 特殊输出控制 |
| wsc.npt | WSCFN | input.F90 | 蒸发/降水输入 |
| shade.npt | SHDFN | shading.f90 | 遮荫系数 |
| 2002_detroit_met.npt | (气象) | MetFileRegion.f90 | 分区气象数据 |
| metDetroit2002.csv | METFN | heat-exchange.f90 | 主气象文件 |

---

## 二、w2_con.csv 文件名区块解析

根据 `w2_con.csv` 第861-897行，文件名定义区块结构如下：

### 2.1 全局文件 (第862-866行)
```
Line 862: QWDFN = ".\InputFiles\qwd_dss.npt"        ! 侧向入流
Line 863: QGTFN = "qgt.npt"                          ! 闸门流量(未使用)
Line 864: WSCFN = ".\InputFiles\wsc.npt"            ! 蒸发/降水
Line 865: SHDFN = ".\InputFiles\shade.npt"          ! 遮荫数据
Line 866: (其他) = "Detroit.w2l"                     ! 湖库几何
```

### 2.2 Waterbody 文件 (第869-878行)
```
Line 869: BTHFN(1) = ".\InputFiles\bth1.csv"        ! 地形
Line 870: METFN(1) = ".\InputFiles\metDetroit2002.csv" ! 气象
Line 871: EXTFN(1) = "ext_wb1.npt"                  ! 扩展(未使用)
Line 872: ATMDEPFN = "ATM_DEP.CSV"                  ! 大气沉降
Line 873: VPRFN(1) = "vpr00wb1.npt"                 ! 蒸发皿(未使用)
Line 874: LPRFN(1) = "lpr_wb1.npt"                  ! 降水(未使用)
Line 875: SNPFN(1) = "snp1.opt"                     ! 快照输出
Line 876: PRFFN(1) = "prf1.opt"                     ! 剖面输出
Line 877: CPLFN(1) = "cpl1.opt"                     ! 耦合输出
Line 878: SPRFN(1) = "spr1.opt"                     ! 特殊输出
```

### 2.3 Branch 文件 (第882-897行)
```
Line 882: QINFN(1-4) = 2002_NSant_Q_corr.npt, 2002_BreiBu_Q.npt, ...
Line 883: TINFN(1-4) = 2002_NSant_T.npt, 2002_BreiBu_T.npt, ...
Line 884: CINFN(1-4) = 2002_NSant_wq.npt, 2002_BreiBu_wq.npt, ...
Line 885: QOTFN(1) = q3.npt                          ! 主支流出流
Line 886: QDTFN(1-4) = 2002_qdt_br1-4.npt           ! 指定日期流量
Line 887: TDTFN(1-4) = 2002_tdt_br1-4F.npt          ! 指定日期水温
Line 888: CDTFN(1-4) = 2002_qdt_wq1-4BBr.npt        ! 指定日期水质
Line 889-890: TPRFN(1-4) = 2002_tpr_detroit*.npt    ! 斗门时序
Line 892: EUHFN(1-4) = euh_br1-4.npt                ! 上游能量通量
Line 893: TUHFN(1-4) = tuh_br1-4.npt                ! 上游水温通量
Line 894: CUHFN(1-4) = cuh_br1-4.npt                ! 上游水质通量
Line 895: EDHFN(1-4) = edh_br1-4.npt                ! 下游能量通量
Line 896: TDHFN(1-4) = tdh_br1-4.npt                ! 下游水温通量
Line 897: CDHFN(1-4) = cdh_br1-4.npt                ! 下游水质通量
```

---

## 三、代码读取流程

### 3.1 主控制文件读取 (input.F90)

```
1. 打开 w2_con.csv (CON 文件单元)
2. 读取基本维度参数 (NWB, NBR, IMX, KMX, NTR, NST, NIW, NWD, NGT, NSP, NPI, NPU 等)
3. 读取文件名定义区块 (第1603-1640行 / 第2103-2137行)
4. 根据文件名打开各个输入文件
```

### 3.2 关键读取代码位置

| 功能 | 文件位置 | 说明 |
|-----|---------|-----|
| Bathymetry | input.F90:2252 | 读取 BTHFN(JW) |
| SYSTDG | input.F90:2322 | 读取 w2_systdg.npt (可选) |
| pH Buffering | input.F90:2491 | 读取 ph_buffering.npt (可选) |
| Graph | input.F90:2364 | 读取 graph.npt |
| Met Files | MetFileRegion.f90:22 | 读取 W2_MetRegions.csv |
| Aeration | aerate.f90:24 | 读取 W2_AERATE.NPT |

### 3.3 流量数据读取 (hydroinout.F90)

流量数据通过以下流程读取：
1. 在 INPUT 子程序中读取文件名
2. 在后续模拟循环中读取实际流量数据
3. 使用插值和时间步长处理

---

## 四、文件格式说明

### 4.1 .npt 格式 (NPT 文件)
- 文本格式
- 通常包含时间序列数据
- 第一行为表头，后续行为数据
- 时间格式：Julian day 或绝对日期

### 4.2 .csv 格式
- 逗号分隔值
- bth1.csv: 地形数据
- metDetroit2002.csv: 气象时间序列

### 4.3 .opt 格式
- 输出控制选项文件
- 定义输出变量、频率、位置等

---

## 五、InputFiles 目录完整文件清单

```
InputFiles/
├── 2002_Blowout_Q.npt          # 支流3 流量
├── 2002_Blowout_T.npt          # 支流3 水温
├── 2002_Blowout_wq.npt         # 支流3 水质
├── 2002_BoxCan_Q_est.npt       # (未使用)
├── 2002_BoxCan_T_est.npt       # (未使用)
├── 2002_BoxCan_estBBr_wq.npt   # (未使用)
├── 2002_BreiBu_Q.npt           # 支流2 流量
├── 2002_BreiBu_T.npt           # 支流2 水温
├── 2002_BreiBu_wq.npt          # 支流2 水质
├── 2002_detroit_met.npt        # 分区气象
├── 2002_French_Q.npt           # (未使用)
├── 2002_French_T.npt           # (未使用)
├── 2002_French_wq.npt          # (未使用)
├── 2002_Kinney_Q_est.npt       # 支流4 流量
├── 2002_Kinney_T_est.npt       # 支流4 水温
├── 2002_Kinney_estBBr_wq.npt   # 支流4 水质
├── 2002_NSant_Q.npt           # (旧版)
├── 2002_NSant_Q_corr.npt       # 支流1 流量(校正版)
├── 2002_NSant_T.npt            # 支流1 水温
├── 2002_NSant_wq.npt           # 支流1 水质
├── 2002_pre_detroit*.npt       # 前置水位条件
├── 2002_qdt_br1-4.npt         # 指定日期流量
├── 2002_qdt_wq1-4BBr.npt      # 指定日期水质
├── 2002_tdt_br1-4F.npt        # 指定日期水温
├── 2002_tpr_detroit*.npt      # 斗门时序控制
├── bth1.csv                    # 水体地形数据
├── metDetroit2002.csv          # 主气象数据
├── q3.npt                      # 湿地/主支流入流
├── qwd_dss.npt                 # 侧向分布式入流
├── shade.npt                   # 遮荫系数
└── wsc.npt                     # 蒸发/降水
```

---

## 六、数据流程图

```
w2_con.csv
    │
    ├── 基本参数 ──────────────────> input.F90 解析
    │     (NWB, NBR, IMX, KMX, etc.)
    │
    ├── 文件名定义 ────────────────> input.F90 存储到变量
    │     (BTHFN, METFN, QINFN, etc.)
    │
    └── 各输入文件
          │
          ├── bth1.csv ────────────> input.F90:2252 ────> B, H 数组
          ├── metDetroit2002.csv ──> heat-exchange.f90 ──> 气象变量
          ├── *Q.npt ──────────────> hydroinout.F90 ────> QIN, QTR 数组
          ├── *T.npt ──────────────> hydroinout.F90 ────> TIN, TRC 数组
          ├── *wq.npt ─────────────> hydroinout.F90 ────> CIN, TRC 数组
          └── *dt*.npt ───────────> hydroinout.F90 ────> 时序控制
```

---

## 七、生成时间

2026-03-31

## 八、相关文件

- 主配置文件: `w2_con.csv`
- 输入处理代码: `input.F90`
- 水动力输入: `hydroinout.F90`
- 气象数据: `heat-exchange.f90`, `MetFileRegion.f90`
- 输出配置: `outputa2w2tools.F90`
