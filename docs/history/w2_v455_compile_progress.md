# CE-QUAL-W2 v4.5.5 编译与配置问题处理进度

## 日期：2026-04-01

---

## 一、问题描述

运行 `w2_v455_ifx.exe` 时出现 Error 59（list-directed I/O syntax error），程序无法正确读取配置文件 `w2_con.csv`。

```
forrtl: severe (59): list-directed I/O syntax error, unit 10, file C:\Users\NING\Desktop\v455\temp_compile\w2_con.csv
```

---

## 二、根本原因分析

### 2.1 CSV文件结构

`w2_con.csv` 的维度参数部分结构（L14-L25）：

```
L14: (空白行)
L15: NWB, NBR, IMX, KMX, NPROC, CLOSEC    ← 标题行（注释，给人看）
L16: 1,1,77,56,1,ON                        ← NWB数据
L17: (空白行)
L18: NTR, NST, NIW, NWD, NGT, NSP, NPI, NPU  ← 标题行
L19: 0,0,0,0,20,0,0,0                       ← NTR数据
L20: (空白行)
L21: NGC, NSS, NAL, NEP, NBOD, NMC, NZP    ← 标题行
L22: 0,0,0,0,0,0,0                          ← NGC数据
L23: (空白行)
L24: NDAY,SELECTC,HABTATC,ENVIRPC,AERATEC,INITUWL,ORGCC,SED_DIAG,DZMAX  ← 标题行
L25: 100,OFF,OFF,OFF,OFF,OFF,OFF,OFF,1000    ← NDAY数据
```

**关键发现**：CSV的`NDAY`就是代码中的`NOD`变量（最大输出日期数）。

### 2.2 代码读取逻辑

`input.f90` 中的CSV读取部分（行38-51）：

```fortran
  DO J=1,10
    READ (CON,*)TITLE(J)      ! 读取10行标题
  ENDDO
  READ (CON,*)                 ! 跳过1行 ← 这里少了！
  READ (CON,*)
  READ (CON,*)
  READ (CON,*) NWB, NBR, IMX, KMX, NPROC, CLOSEC
  READ (CON,*)
  READ (CON,*)
  READ (CON,*) NTR, NST, NIW, NWD, NGT, NSP, NPI, NPU
  READ (CON,*)
  READ (CON,*)
  READ (CON,*) NGC, NSS, NAL, NEP, NBOD, NMC, NZP
  READ (CON,*)
  READ (CON,*)
  READ (CON,*) NOD,SELECTC,HABTATC,ENVIRPC,AERATEC,INITUWL,ORGCC,SED_DIAG,DZMAX
```

### 2.3 错位原因

代码期望的读取顺序：
1. 跳过 L14 空白
2. 跳过 L15 NWB标题
3. 读取 L16 NWB数据

但代码只有1个skip（READ CON,*），导致：
1. 跳过 L14 空白
2. 读取 L15 NWB标题 → **错误！应该是跳过**
3. 读取 L16 NWB数据 → **错误！应该是读取**
4. ...后续全部错位

**正确结构应该是**（对比示例文件中的原始input.F90）：
- 10个标题读取后，需要**2个skip**（跳过空白+跳过标题）
- 然后读取NWB数据

---

## 三、已完成的修改

### 3.1 修改1：添加缺失的skip行

**文件**: `C:\Users\NING\Desktop\v455\temp_compile\input.f90`

**位置**: 第41-43行

**修改前**：
```fortran
  READ (CON,*)
  READ (CON,*) NWB, NBR, IMX, KMX, NPROC, CLOSEC
```

**修改后**：
```fortran
  READ (CON,*)
  READ (CON,*)
  READ (CON,*)
  READ (CON,*) NWB, NBR, IMX, KMX, NPROC, CLOSEC
```

**说明**：在NWB读取前添加了1个额外的`READ (CON,*)`，使skip总数从2个变为3个。

### 3.2 修改2：移除预处理块

**问题**：input.f90中保留了`#ifdef ZOOPLANKTONC`、`#ifdef MACROPHYTEC`、`#ifdef BIOENERGETICS`预处理块，但这些模块已被移除，导致编译失败。

**已移除的块**：

| 行号 | 类型 | 内容 |
|------|------|------|
| 435-451 | ZOOPLANKTONC #ifdef-#else-#endif | 浮游动物ALLOCATE语句 |
| 1421-1423 | ZOOPLANKTONC #ifdef-#endif | EXZ数组读取 |
| 1424-1426 | MACROPHYTEC #ifdef-#endif | EXM数组读取 |
| 1455-1469 | ZOOPLANKTONC #ifdef-#endif | 浮游动物参数读取（20+行） |
| 1511-1513 | ZOOPLANKTONC #ifdef-#endif | O2ZR读取 |
| 1514-1516 | MACROPHYTEC #ifdef-#endif | O2MR/O2MG读取 |
| 1609-1617 | ZOOPLANKTONC/MACROPHYTEC #ifdef-#endif | EXZ/EXM读取 |
| 1758-1791 | ZOOPLANKTONC #ifdef-#endif | 浮游动物参数读取（35+行） |
| 1763-1813 | MACROPHYTEC #ifdef-#endif | 大型植物参数读取（50+行） |
| 2188-2198 | BIOENERGETICS #ifdef-#endif | 生物能量学输出文件编号 |
| 2270-2274 | MACROPHYTEC #ifdef-#endif | MACROPHYTE条件判断 |

---

## 四、当前状态

| 项目 | 状态 |
|------|------|
| input.f90 skip逻辑修改 | ✅ 完成 |
| input.f90 预处理块移除 | ✅ 完成 |
| input.f90 编译 | ✅ 成功 (`objdir/input.obj` 时间戳 23:34) |
| 链接生成exe | ⚠️ 未完成（链接命令执行但exe未更新） |
| 运行测试 | ⚠️ 待验证 |

---

## 五、编译与链接方法

### 5.1 编译命令

```batch
cd C:\Users\NING\Desktop\v455\temp_compile

"C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\bin\ifx.exe" /nologo /fpp /module:moddir /object:objdir\ /c /Qm64 /define:NO_ZOOPLANKTONC /define:NO_MACROPHYTEC /define:NO_BIOENERGETICS input.f90
```

### 5.2 链接命令

```batch
cd C:\Users\NING\Desktop\v455\temp_compile

"C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\bin\ifx.exe" /nologo /Qm64 @objfiles.txt /exe:w2_v455_ifx.exe
```

其中 `objfiles.txt` 包含所有 .obj 文件路径。

### 5.3 运行命令

```batch
cd C:\Users\NING\Desktop\v455\temp_compile
w2_v455_ifx.exe
```

---

## 六、下一步工作

1. **完成链接**：执行链接命令，生成更新后的 `w2_v455_ifx.exe`
2. **测试运行**：执行 `./w2_v455_ifx.exe` 验证 Error 59 是否解决
3. **验证结果**：如果仍有问题，检查CSV结构是否与代码完全匹配

---

## 七、相关文件路径

| 文件 | 路径 |
|------|------|
| input.f90 | `C:\Users\NING\Desktop\v455\temp_compile\input.f90` |
| w2_con.csv | `C:\Users\NING\Desktop\v455\temp_compile\w2_con.csv` |
| w2_v455_ifx.exe | `C:\Users\NING\Desktop\v455\temp_compile\w2_v455_ifx.exe` |
| 原始input.F90(参考) | `C:\Users\NING\Desktop\v455\示例文件\input.F90` |
| 原始w2_con.csv(参考) | `C:\Users\NING\Desktop\v455\示例文件\w2_con.csv` |

---

## 八、注意事项

1. **跳过逻辑**：CSV的每一行数据前都有"空白行+标题行"，代码需要跳过这两行才能正确读取数据
2. **预处理块**：移除模块后，必须同步移除对应的 `#ifdef` 预处理块
3. **模块依赖**：修改模块相关代码时，需要确保所有引用该模块的地方都已处理
