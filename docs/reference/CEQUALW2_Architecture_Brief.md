# CE-QUAL-W2 代码架构文档

## Context

用户要求深入调查 `w2source_v455_2_11_2026` 项目（水动力模拟软件），梳理其架构、原理、变量函数组成和引用关系，方便后续阅读。

---

# 1. 项目概述

## 1.1 软件信息

| 属性 | 值 |
|------|-----|
| **名称** | CE-QUAL-W2 |
| **版本** | 4.5.5 |
| **类型** | 二维侧向平均水动力与水质模型 |
| **维护者** | Portland State University (Dr. Scott A. Wells) |
| **开发语言** | Fortran 90/95 |
| **构建系统** | Visual Studio + Intel Fortran 编译器 |
| **目标平台** | Windows (x64) |

## 1.2 模型能力

CE-QUAL-W2 是一个二维侧向平均（laterally averaged）模型，适用于：
- 河流（Rivers）
- 湖泊（Lakes）
- 水库（Reservoirs）
- 河口（Estuaries）

---

# 2. 目录结构

```
w2source_v455_2_11_2026/
│
├── 根目录（约50个Fortran源文件）
│   ├── w2_4_win.f90              # 主程序入口 (CE_QUAL_W2函数)
│   ├── w2modules.F90              # 全局模块定义 (907行, 25个模块)
│   ├── input.F90                  # 控制文件解析
│   ├── init*.F90                  # 初始化模块群
│   ├── hydroinout.F90             # 水动力源汇项
│   ├── transport.f90              # 物质输移 (ULTIMATE/TVD方案)
│   ├── temperature.F90            # 热交换计算
│   ├── az.f90                     # 垂向湍流 (AZ/DZ)
│   ├── water-quality.f90          # 水质动力学 (38个入口点)
│   ├── balances.F90               # 水量/质量守恒
│   ├── withdrawal.f90             # 取水建筑
│   ├── gate-spill-pipe.f90       # 闸门/溢洪道/管道
│   └── Diagenesis*               # 沉积物成岩模型 (CEMA)
│       ├── Diagenesis FFT Layer 01.f90
│       ├── Diagenesis Sediment Model 03.f90
│       ├── Diagenesis Sediment Flux Model 05.f90
│       ├── Diagenesis Input 02.f90
│       ├── Diagenesis Input Files Read 01.f90
│       ├── Diagenesis Output 02.f90
│       └── Diagenesis Bubbles Code 01.f90
│
├── User Manual/                  # PDF手册 (5份)
│   ├── W2manual455_Part1_Intro_rev0.pdf
│   ├── W2manual455_Part2_Theory_rev0.pdf
│   ├── W2manual455_Part3_InputOutputFiles_rev0.pdf
│   ├── W2manual455_Part4_ModelExamples_rev0.pdf
│   └── W2manual455_Part5_ModelUtilities_rev0.pdf
│
└── W2 model/                     # Visual Studio项目
    ├── W2 model.vfproj            # Intel Fortran项目文件
    ├── W2 model_PAR.sln           # 解决方案文件
    └── x64/Release/               # 编译产物
```

---

# 3. 核心模块详解 (w2modules.F90)

共定义 **25个模块**，按依赖关系排列：

## 3.1 基础模块

### `PREC` (精度定义)
```fortran
INTEGER, PARAMETER :: I2 = SELECTED_INT_KIND(3)   ! 2字节整数
INTEGER, PARAMETER :: R8 = SELECTED_REAL_KIND(15) ! 双精度实数
```
**用途**: 被18个其他模块引用，是所有数值计算的基础。

---

### `GLOBAL` (全局核心变量)
这是模型最核心的模块，定义所有状态变量。

**命名常量 (PARAMETER)**:
| 常量 | 值 | 说明 |
|------|-----|------|
| `DAY` | 86400.0D0 | 每天秒数 |
| `NONZERO` | 1.0D-20 | 最小非零值 |
| `RHOW` | 1000.0D0 | 水密度 (kg/m³) |
| `G` | 9.81D0 | 重力加速度 |
| `PI` | 3.14159265359D0 | 圆周率 |
| `DZMIN` | 1.4D-7 | 最小层厚 |
| `AZMIN` | 1.4D-6 | 最小垂向涡粘度 |

**网格维度变量**:
| 变量 | 说明 |
|------|------|
| `IMX` | 水平方向最大网格数 |
| `KMX` | 垂向最大层数 |
| `NBR` | 支流数量 |
| `NWB` | 水体数量 |
| `NCT` | 物质数量 |

**状态变量 (2D: IMX × KMX)**:
| 变量 | 维度 | 说明 |
|------|------|------|
| `U(KMX,IMX)` | 2D | 水平速度 (m/s) |
| `W(KMX,IMX)` | 2D | 垂向速度 (m/s) |
| `T1, T2(KMX,IMX)` | 2D | 温度 (当前/上一 timestep) |
| `AZ(KMX,IMX)` | 2D | 垂向涡粘度 (m²/s) |
| `RHO(KMX,IMX)` | 2D | 水密度 (kg/m³) |
| `VOL(KMX,IMX)` | 2D | 单元格体积 (m³) |

**物质变量 (3D: IMX × KMX × NDC)**:
| 变量 | 说明 |
|------|------|
| `C1(KMX,IMX,NDC)` | 当前物质浓度 |
| `C2(KMX,IMX,NDC)` | 上一timestep物质浓度 |

---

### `KINETIC` (水质动力学)
最大模块之一，约1500行声明。

**水质变量 (2D指针: IMX × KMX)**:
| 变量 | 说明 |
|------|------|
| `TDS` | 溶解性固体 |
| `NH4, NO3` | 氨氮、硝氮 |
| `PO4` | 磷酸盐 |
| `O2` | 溶解氧 |
| `CBOD(IMX,KMX,NBOD)` | 碳生化需氧量 |
| `ALG(IMX,KMX,NAL)` | 藻类 |

---

# 4. 主程序流程 (w2_4_win.f90)

## 4.1 初始化阶段

```
CE_QUAL_W2
  ├── INPUT                    # 读取w2_con.npt/csv控制文件
  ├── CEMA_W2_Input            # CEMA沉积物模型输入
  ├── ReadMetRegions           # 气象分区
  ├── INIT                     # 变量初始化
  ├── initgeom                 # 几何初始化
  ├── initial_water_level      # 初始水位
  ├── initial_u_velocity       # 初始水平速度
  └── OUTPUTINIT               # 输出初始化
```

## 4.2 主时间循环

```fortran
DO WHILE (.NOT. END_RUN .AND. .NOT. STOP_PUSHED)
```

### 每个时间步的执行顺序：

| 步骤 | subroutine/区域 | 说明 |
|------|----------------|------|
| 1 | `READ_INPUT_DATA` | 读取时变边界数据 |
| 2 | `INTERPOLATE_INPUTS` | 插值计算 |
| 3 | `HYDROINOUT` | 水动力源汇项 |
| 4 | `ComputeCEMARelatedSourceSinks` | CEMA沉积物源汇 |
| 5 | **水动力计算** (Task 2.2) | 水面高程、速度 |
| 6 | `temperature` | 热交换 |
| 7 | `wqconstituents` | 水质反应 |
| 8 | `LAYERADDSUB` | 动态层加减 |
| 9 | `BALANCES` | 守恒检查 |
| 10 | `UPDATE` | 状态更新 |
| 11 | `OUTPUTA` | 写输出文件 |

---

# 5. 核心算法详解

## 5.1 水面高程求解 (Task 2.2.3)
**方法**: 隐式三对角矩阵求解 (Thomas算法)

## 5.2 垂向湍流 (az.f90)
- Richardson数方法 (默认)
- k-epsilon模型 (`CALCULATE_TKE`)

## 5.3 物质输移 (transport.f90)
- ULTIMATE方案 (TVD)
- 有限体积法

## 5.4 热交换 (temperature.F90)
- Bowen's ratio方法
- Beer-Lambert太阳辐射穿透

## 5.5 水质动力学 (water-quality.f90)
- 38个入口点
- 氮/磷/碳循环
- DO平衡

## 5.6 沉积物成岩模型 (CEMA)
- 双层模型 (好氧表层 + 厌氧深层)
- 甲烷/硫化氢气泡动力学

---

# 6. 模块依赖关系图

```
PREC (基础)
   │
   ├── GLOBAL ──► w2_4_win.f90 (主程序)
   │              │
   │              ├── hydroinout.F90
   │              ├── temperature.F90
   │              ├── transport.f90
   │              ├── water-quality.f90
   │              ├── az.f90
   │              └── Diagenesis* (CEMA)
```

---

# 7. 关键数值常数

| 常量 | 值 | 说明 |
|------|-----|------|
| `DAY = 86400.0D0` | 每天秒数 | GLOBAL |
| `G = 9.81D0` | 重力加速度 | GLOBAL |
| `RHOW = 1000.0D0` | 水密度 | GLOBAL |
| `DZMIN = 1.4D-7` | 最小层厚 | GLOBAL |
| `AZMIN = 1.4D-6` | 最小涡粘度 | GLOBAL |

---

# 8. 总结

CE-QUAL-W2 是一个高度模块化的二维侧向平均水动力水质模型：

1. **数据管理**: `w2modules.F90` 集中定义25个模块
2. **求解策略**: 半隐式有限差分 + TVD限制器 + 三对角矩阵求解
3. **物理过程**: 水动力、热交换、物质输移、水质反应、沉积物成岩
4. **沉积物CEMA**: 完整的沉积物-水界面通量计算，支持甲烷/硫化氢气泡

此文档为简要版，详细梳理版请参考 `CEQUALW2_Architecture_Full.md`
