# w2_con.csv 逐行参数分析

## 概述

本文档详细分析 `w2_con.csv` 中每一行参数与 `input.F90` 代码中变量的对应关系。修改 input.F90 后，可根据此文档调整 CSV 结构。

---

## w2_con.csv 行号与变量对应表

### 文件头部 (Lines 1-14)

| CSV 行号 | CSV 内容 | 参数名称 | 代码变量 | input.F90 位置 | 说明 |
|----------|----------|----------|----------|---------------|------|
| 1 | CE-QUAL-W2 Version | - | - | - | 文件标识 |
| 2 | Control File version | 版本 | CONFN | - | 检测文件格式 |
| 3-12 | Title comments | 标题10行 | TITLE(J) | L26-36 | 模型标题 |
| 13-14 | (blank) | - | - | - | 空白行 |

---

### 维度参数 (Lines 15-25)

| CSV 行号 | CSV 标题行 | CSV 数据行 | 代码变量 | input.F90 位置 | 说明 |
|----------|-----------|-----------|----------|---------------|------|
| 15 | NWB, NBR, IMX, KMX, NPROC, CLOSEC | 值 | NWB, NBR, IMX, KMX, NPROC, CLOSEC | L27(旧格式)/L40(csv格式) | 水体数、分支数、水平段数、层数、处理器数、关闭控制 |
| 17 | NTR, NST, NIW, NWD, NGT, NSP, NPI, NPU | 值 | NTR, NST, NIW, NWD, NGT, NSP, NPI, NPU | L28/L43 | 支流数、闸数、入流数、出流数、闸门数、堰数、管数、泵数 |
| 19 | NGC, NSS, NAL, NEP, NBOD, NMC, NZP | 值 | NGC, NSS, NAL, NEP, NBOD, NMC, NZP | L29/L46 | 藻类、悬浮物、藻类种数、底栖藻类、BOD类、沉水植物、浮游动物 |
| 21 | NDAY,SELECTC,HABTATC,ENVIRPC,AERATEC,INITUWL,ORGCC,SED_DIAG,DZMAX | 值 | NOD,SELECTC,HABTATC,ENVIRPC,AERATEC,INITUWL,ORGCC,SED_DIAG,DZMAX | L30/L49 | 运行天数、选择控制、生境控制、环境控制、曝气控制、初始条件、有机碳计算、沉积物诊断、层厚最大乘子 |
| 23 | (blank) | - | - | - | 空白行 |

---

### 时间参数 (Lines 27-53)

| CSV 行号 | CSV 标题行 | 代码变量 | input.F90 位置 | 说明 |
|----------|-----------|----------|---------------|------|
| 27 | TMSTRT, TMEND, YEAR | TMSTRT, TMEND, YEAR | L689(旧)/L719(csv) | 模拟开始/结束时间、年份 |
| 29 | NDLT, DLTMIN, DLTINTER | NDLT, DLTMIN, DLTINTER | L690(旧)/L722(csv) | 时间步长段数、最小步长、步长间隔标志 |
| 31 | DLTD (数组) | DLTD(J), J=1,NDLT | L691(旧)/L725(csv) | 时间步长乘子 |
| 33 | DLTMAX (数组) | DLTMAX(J), J=1,NDLT | L692(旧)/L728(csv) | 时间步长最大值 |
| 35 | DLTF (数组) | DLTF(J), J=1,NDLT | L693(旧)/L731(csv) | 时间步长乘子 |
| 37 | (blank) | - | - | - | 空白行 |
| 39 | WB1-WB10 | (VISC等) | VISC(JW), CELC(JW), DLTADD(JW) | L694(旧)/L734-736(csv) | 水体粘度、蒸发系数、附加步长 |

---

### 分支参数 (Lines 47-55)

| CSV 行号 | CSV 标题 | 代码变量 | input.F90 位置 | 数组维度 | 说明 |
|----------|---------|----------|---------------|----------|------|
| 47 | BR1-BR10 | US(JB), DS(JB), UHS(JB), DHS(JB), NL(JB), SLOPE(JB), SLOPEC(JB) | L698(旧)/L742-748(csv) | JB=1,NBR | 上/下游断面位置、水平/对角断面距离、分段数、坡度 |
| 49 | LAT, LONGIT, ELBOT, BS, BE, JBDN | LAT(JW), LONGIT(JW), ELBOT(JW), BS(JW), BE(JW), JBDN(JW) | L699(旧)/L753-758(csv) | JW=1,NWB | 纬度、经度、底部高程、起始/结束分支、下游分支 |

---

### 水体初始化 (Lines 57-67)

| CSV 行号 | CSV 标题 | 代码变量 | input.F90 位置 | 说明 |
|----------|---------|----------|---------------|------|
| 57 | T2I, ICETHI, WTYPEC, GRIDC | T2I(JW), ICETHI(JW), WTYPEC(JW), GRIDC(JW) | L703(旧)/L764-767(csv) | 初始温度、冰厚、水体类型、网格类型 |
| 59 | VBC, EBC, MBC, PQC, EVC, PRC | VBC(JW), EBC(JW), MBC(JW), PQC(JW), EVC(JW), PRC(JW) | L704(旧)/L771-776(csv) | 垂向边界条件(蒸发、降水、蒸散发等) |
| 61 | WINDC, QINC, QOUTC, HEATC | WINDC(JW), QINC(JW), QOUTC(JW), HEATC(JW) | L705(旧)/L780-783(csv) | 风、流入、流出、热交换控制 |
| 63 | QINIC, DTRIC, HDIC | QINIC(JB), DTRIC(JB), HDIC(JB) | L706(旧)/L787-789(csv) | 初始入流、水温、深度 |

---

### 湖泊参数 (Lines 69-77)

| CSV 行号 | CSV 标题 | 代码变量 | input.F90 位置 | 说明 |
|----------|---------|----------|---------------|------|
| 69 | SLHTC, SROC, RHEVC, METIC, FETCHC, AFW, BFW, WINDH | SLHTC(JW), SROC(JW), RHEVC(JW), METIC(JW), FETCHC(JW), AFW(JW), BFW(JW), WINDH(JW) | L707(旧)/L793-801(csv) | 热通量、辐射、相对湿度、气象、吹程、风应力系数 |
| 71 | ICEC, SLICEC, ALBEDO, HWI, BETAI, GAMMAI, ICEMIN, ICET2 | ICEC(JW), SLICEC(JW), ALBEDO(JW), HWI(JW), BETAI(JW), GAMMAI(JW), ICEMIN(JW), ICET2(JW) | L709(旧)/L805-812(csv) | 冰盖参数 |
| 73 | SLTRC, THETA | SLTRC(JW), THETA(JW) | L711(旧)/L816-817(csv) | 散射辐射系数、温度系数 |
| 75 | AX, DXI, CBHE, TSED, FI, TSEDF, FRICC, Z0 | AX(JW), DXI(JW), CBHE(JW), TSED(JW), FI(JW), TSEDF(JW), FRICC(JW), Z0(JW) | L712(旧)/L821-828(csv) | 涡流扩散、糙率 |

---

### 垂向混合参数 (Lines 79-87)

| CSV 行号 | CSV 标题 | 代码变量 | input.F90 位置 | 说明 |
|----------|---------|----------|---------------|------|
| 79 | AZC, AZSLC, AZMAX, TKEBC, EROUGH, ARODI, STRICK, TKELATPRDCONST, IMPTKE | AZC(JW), AZSLC(JW), AZMAX(JW), TKEBC(JW), EROUGH(JW), ARODI(JW), STRICK(JW), TKELATPRDCONST(JW), IMPTKE(JW) | L714(旧)/L832-840(csv) | 垂向涡流粘度参数 |
| 81 | (blank) | - | - | - | 空白行 |

---

### 结构物控制 - 管道 (Lines 89-97)

| CSV 行号 | CSV 标题 | 代码变量 | input.F90 位置 | 数组维度 | 说明 |
|----------|---------|----------|---------------|----------|------|
| 89 | IUPI, IDPI, EUPI, EDPI, WPI, DLXPI, FPI, FMINPI, LATPIC, DYNPIPE | IUPI(JP), IDPI(JP), EUPI(JP), EDPI(JP), WPI(JP), DLXPI(JP), FPI(JP), FMINPI(JP), LATPIC(JP), DYNPIPE(JP) | L881(旧)/L929-937(csv) | JP=1,NPI | 管道上下游位置、管道直径、摩阻系数、控制类型 |
| 91 | PUPIC, ETUPI, EBUPI, KTUPI, KBUPI | PUPIC(JP), ETUPI(JP), EBUPI(JP), KTUPI(JP), KBUPI(JP) | L883(旧)/L940-944(csv) | JP=1,NPI | 管道上游高程、控制类型 |
| 93 | PDPIC, ETDPI, EBDPI, KTDPI, KBDPI | PDPIC(JP), ETDPI(JP), EBDPI(JP), KTDPI(JP), KBDPI(JP) | L884(旧)/L946-950(csv) | JP=1,NPI | 管道下游高程、控制类型 |

---

### 结构物控制 - 堰 (Lines 99-107)

| CSV 行号 | CSV 标题 | 代码变量 | input.F90 位置 | 数组维度 | 说明 |
|----------|---------|----------|---------------|----------|------|
| 99 | IUSP, IDSP, ESP, A1SP, B1SP, A2SP, B2SP, LATSPC, PUSPC, PDSPC | IUSP(JS), IDSP(JS), ESP(JS), A1SP(JS), B1SP(JS), A2SP(JS), B2SP(JS), LATSPC(JS), PUSPC(JS), PDSPC(JS) | L885(旧)/L954-969(csv) | JS=1,NSP | 堰上下游位置、堰顶高程、系数、侧向控制 |
| 101 | GASSPC, EQSP, AGASSP, BGASSP, CGASSP | GASSPC(JS), EQSP(JS), AGASSP(JS), BGASSP(JS), CGASSP(JS) | L889(旧)/L975-979(csv) | JS=1,NSP | 气体过流类型、方程系数 |

---

### 结构物控制 - 闸门 (Lines 109-117)

| CSV 行号 | CSV 标题 | 代码变量 | input.F90 位置 | 数组维度 | 说明 |
|----------|---------|----------|---------------|----------|------|
| 109 | IUGT, IDGT, EGT, A1GT, B1GT, G1GT, A2GT, B2GT, G2GT, LATGTC | IUGT(JG), IDGT(JG), EGT(JG), A1GT(JG), B1GT(JG), G1GT(JG), A2GT(JG), B2GT(JG), G2GT(JG), LATGTC(JG) | L890-891(旧)/L983-992(csv) | JG=1,NGT | 闸门位置、高程、流量系数 |
| 111 | GTA1, GTB1, GTA2, GTB2, DYNGTC, GTIC | GTA1(JG), GTB1(JG), GTA2(JG), GTB2(JG), DYNGTC(JG), GTIC(JG) | L892(旧)/L994-999(csv) | JG=1,NGT | 闸门动态控制类型 |
| 113 | PUGTC, ETUGT, EBUGT, KTUGT, KBUGT | PUGTC(JG), ETUGT(JG), EBUGT(JG), KTUGT(JG), KBUGT(JG) | L893(旧)/L1001-1005(csv) | JG=1,NGT | 闸门上/下游高程 |
| 115 | PDGTC, ETDGT, EBDGT, KTDGT, KBDGT | PDGTC(JG), ETDGT(JG), EBDGT(JG), KTDGT(JG), KBDGT(JG) | L894(旧)/L1006-1010(csv) | JG=1,NGT | 闸门下/下游高程 |
| 117 | GASGTC, EQGT, AGASGT, BGASGT, CGASGT | GASGTC(JG), EQGT(JG), AGASGT(JG), BGASGT(JG), CGASGT(JG) | L895(旧)/L1012-1016(csv) | JG=1,NGT | 气体流量参数 |

---

### 结构物控制 - 泵 (Lines 119-127)

| CSV 行号 | CSV 标题 | 代码变量 | input.F90 位置 | 数组维度 | 说明 |
|----------|---------|----------|---------------|----------|------|
| 119 | IUPU, IDPU, EPU, STRTPU, ENDPU, EONPU, EOFFPU, QPU, LATPUC, DYNPUMP | IUPU(JP), IDPU(JP), EPU(JP), STRTPU(JP), ENDPU(JP), EONPU(JP), EOFFPU(JP), QPU(JP), LATPUC(JP), DYNPUMP(JP) | L897(旧)/L1021-1030(csv) | JP=1,NPU | 泵的上下游位置、运行控制 |
| 121 | PPUC, ETPU, EBPU, KTPU, KBPU | PPUC(JP), ETPU(JP), EBPU(JP), KTPU(JP), KBPU(JP) | L1045(旧)/L1161-1165(csv) | JP=1,NPU | 泵的控制类型、高程 |

---

### 入流/出流/ Withdrawal (Lines 129-137)

| CSV 行号 | CSV 标题 | 代码变量 | input.F90 位置 | 说明 |
|----------|---------|----------|---------------|------|
| 129 | IWR, EKTWR, EKBWR | IWR(JW), EKTWR(JW), EKBWR(JW) | L1046-1048(旧)/L1169-1171(csv) |  withdrawal 位置 |
| 131 | WDIC, IWD, EWD, KTWD, KBWD | WDIC(JW), IWD(JW), EWD(JW), KTWD(JW), KBWD(JW) | L1049-1052(旧)/L1175-1179(csv) | withdrawal 控制 |
| 133 | TRC, TRIC, ITR, ELTRT, ELTRB | TRC(JT), TRIC(JT), ITR(JT), ELTRT(JT), ELTRB(JT) | L1054-1058(旧)/L1183-1187(csv) | 支流配置 |
| 135 | DTRC | DTRC(JB) | L1059(旧)/L1194(csv) | 支流日期类型 |

---

### 输出控制 - 水质变量 (Lines 139-157)

| CSV 行号 | CSV 标题 | 代码变量 | input.F90 位置 | 说明 |
|----------|---------|----------|---------------|------|
| 139 | HNAME, FMTH, HMULT, HPRWBC (NHY行) | HNAME(JH), FMTH(JH), HMULT(JH), HPRWBC(JH,JW) | L1064-1065(旧)/L1200-1201(csv) | 水质变量输出控制 |
| 141 | SNPC, NSNP, NISNP | SNPC(JW), NSNP(JW), NISNP(JW) | L1067(旧)/L1206-1209(csv) | 快照输出控制 |
| 143 | SNPD (NSNP个) | SNPD(J,JW) | L1070(旧)/L1222(csv) | 快照日期 |
| 145 | SNPF (NSNP个) | SNPF(J,JW) | L1074(旧)/L1223(csv) | 快照频率 |
| 147 | ISNP (NISNP个) | ISNP(I,JW) | L1078(旧)/L1217-1221(csv) | 快照断面位置 |
| 149 | SCRC, NSCR | SCRC(JW), NSCR(JW) | L1080(旧)/L1231-1232(csv) | 屏幕输出控制 |
| 151 | SCRD, SCRF | SCRD(J,JW), SCRF(J,JW) | L1083-1087(旧)/L1233-1234(csv) | 屏幕输出日期/频率 |
| 153 | PRFC, NPRF, NIPRF | PRFC(JW), NPRF(JW), NIPRF(JW) | L1089(旧)/L1248-1260(csv) | 剖面输出控制 |
| 155 | PRFD, PRFF, IPRF | PRFD(J,JW), PRFF(J,JW), IPRF(J,JW) | L1092-1100(旧)/L1252-1283(csv) | 剖面输出日期/频率/位置 |
| 157 | SPRC, NSPR, NISPR | SPRC(JW), NSPR(JW), NISPR(JW) | L1102(旧)/L1286-1316(csv) | 特殊输出控制 |

---

### 输出控制 - 其他 (Lines 159-175)

| CSV 行号 | CSV 标题 | 代码变量 | input.F90 位置 | 说明 |
|----------|---------|----------|---------------|------|
| 159 | VPLC, NVPL | VPLC(JW), NVPL(JW) | L1115(旧)/L1318-1323(csv) | 垂向剖面输出 |
| 161 | VPLD, VPLF | VPLD(J,JW), VPLF(J,JW) | L1118-1122(旧)/L1322-1323(csv) | 垂向剖面日期/频率 |
| 163 | CPLC, NCPL, TECPLOT | CPLC(JW), NCPL(JW), TECPLOT(JW) | L1124(旧)/L1327-1333(csv) | 耦合输出/Tecplot控制 |
| 165 | CPLD, CPLF | CPLD(J,JW), CPLF(J,JW) | L1127-1131(旧)/L1334-1341(csv) | 耦合输出日期/频率 |
| 167 | FLXC, NFLX | FLXC(JW), NFLX(JW) | L1133(旧)/L1343-1355(csv) | 通量输出控制 |
| 169 | FLXD, FLXF | FLXD(J,JW), FLXF(J,JW) | L1136-1140(旧)/L1348-1355(csv) | 通量输出日期/频率 |
| 171 | TSRC, NTSR, NIKTSR | TSRC, NTSR, NIKTSR | L1142(旧)/L1357-1359(csv) | 时间序列输出 |
| 173 | TSRD, TSRF, ITSR, ETSR | TSRD(J), TSRF(J), ITSR(J), ETSR(J) | L1143-1146(旧)/L1363-1366(csv) | 时间序列日期/频率/位置 |
| 175 | WLC, WLF | WLC, WLF | L1148(旧)/L1369-1370(csv) | 水位输出控制 |
| 177 | FLOWBALC, FLOWBALF | FLOWBALC, FLOWBALF | L1149(旧)/L1375-1376(csv) | 流量平衡输出 |
| 179 | NPBALC, NPBALF | NPBALC, NPBALF | L1150(旧)/L1381-1382(csv) | 数值平面平衡输出 |
| 181 | WDOC, NWDO, NIWDO, WDOFN | WDOC, NWDO, NIWDO, WDOFN | L1152(旧)/L1387-1395(csv) | withdrawal 输出 |
| 183 | WDOD, WDOF, IWDO | WDOD(J), WDOF(J), IWDO(J) | L1154-1155(旧)/L1393-1395(csv) | withdrawal 输出日期/频率 |
| 185 | RSOC, NRSO, RSIC, RSIFN | RSOC, NRSO, RSIC, RSIFN | L1156(旧)/L1399-1402(csv) | 重启输出控制 |
| 187 | RSOD, RSOF | RSOD(J), RSOF(J) | L1157-1158(旧)/L1405-1406(csv) | 重启输出日期/频率 |

---

### 水质参数 - 基础配置 (Lines 189-197)

| CSV 行号 | CSV 标题 | 代码变量 | input.F90 位置 | 说明 |
|----------|---------|----------|---------------|------|
| 189 | CCC, LIMC, CUF, PCO2ATMPPM, CO2YEARLYPPM | CCC, LIMC, CUF, PCO2ATMPPM, CO2YEARLYPPM | L1428(旧) | 水质计算开关、限制符、CO2 |
| 191 | ATM_DEPOSITIONC, ATM_DEPOSITION_INTERPOLATION | ATM_DEPOSITIONC(JW), ATM_DEPOSITION_INTERPOLATION(JW) | L1430-1433(旧) | 大气沉降控制 |
| 193 | CNAME2, CAC (NCT行) | CNAME2(JC), CAC(JC) | L1435(旧) | 组分名称和开关 |
| 195 | CDNAME2, CDWBC (NDC行) | CDNAME2(JD), CDWBC(JD,JW) | L1438-1441(旧) | 输出变量名和开关 |
| 197 | KFNAME2, KFWBC (72行) | KFNAME2(JF), KFWBC(JF,JW) | L1444-1448(旧) | 动力学变量名和开关 |

---

### 水质参数 - 初始条件 (Lines 199-207)

| CSV 行号 | CSV 标题 | 代码变量 | input.F90 位置 | 说明 |
|----------|---------|----------|---------------|------|
| 199 | C2I (NCT x NWB) | C2I(JC,JW) | L1452(旧) | 组分初始浓度 |
| 201 | CPRWBC (NCT x NWB) | CPRWBC(JC,JW) | L1456(旧) | 组分打印控制 |
| 203 | C_ATM_DEPOSITION (NCT x NWB) | C_ATM_DEPOSITION(JC,JW) | L1460(旧) | 大气沉降量 |
| 205 | CINBRC (NCT x NBR) | CINBRC(JC,JB) | L1464(旧) | 支流初始浓度 |
| 207 | CTRTRC (NCT x NTR) | CTRTRC(JC,JT) | L1468(旧) | 支流转化浓度 |

---

### 水质参数 - 动力学系数 (Lines 209-217)

| CSV 行号 | CSV 标题 | 代码变量 | input.F90 位置 | 说明 |
|----------|---------|----------|---------------|------|
| 209 | EXH2O, EXSS, EXOM, BETA, EXC, EXIC | EXH2O(JW), EXSS(JW), EXOM(JW), BETA(JW), EXC(JW), EXIC(JW) | L1481(旧) | 消光系数 |
| 211 | EXA (NAL个) | EXA(JA) | L1482(旧) | 藻类消光系数 |
| 213 | EXZ (NZPT个) | EXZ(JZ) | L1483(旧) | 浮游动物消光系数 |
| 215 | EXM (NMCT个) | EXM(JM) | L1484(旧) | 大型植物消光系数 |
| 217 | CGQ10, CG0DK, CG1DK, CGS, CGLDK, CGKLF, CGCS, CGR (NGC个) | CGQ10(JG), CG0DK(JG), CG1DK(JG), CGS(JG), CGLDK(JG), CGKLF(JG), CGCS(JG), CGR(JG) | L1485(旧) | 底栖藻类动力学参数 |

---

## 数组维度速查

| 维度名 | 变量 | 最小值 | 来源 |
|--------|------|--------|------|
| NWB | 水体数 | 1 | CSV L16 |
| NBR | 分支数 | 1 | CSV L16 |
| IMX | 水平段最大数 | - | CSV L16 |
| KMX | 垂向层最大数 | - | CSV L16 |
| NTR | 支流数 | 0 | CSV L18 |
| NGT | 闸门数 | 0 | CSV L18 |
| NSP | 堰数 | 0 | CSV L18 |
| NPI | 管道数 | 0 | CSV L18 |
| NPU | 泵数 | 0 | CSV L18 |
| NAL | 藻类种数 | 0 | CSV L20 |
| NEP | 底栖藻类组数 | 0 | CSV L20 |
| NBOD | BOD类数 | 0 | CSV L20 |
| NMC | 大型植物组数 | 0 | CSV L20 |
| NZP | 浮游动物组数 | 0 | CSV L20 |

---

## 修改指南

### 添加新参数步骤

1. **在 input.F90 中找到对应的 READ 语句**
2. **确定参数类型和数组维度**
3. **在 CSV 中添加对应的行**
4. **确保维度参数(NWB, NBR等)在参数之前读取**

### 常见修改场景

| 场景 | 需要修改的位置 |
|------|---------------|
| 添加新水体 | L15 (NWB), 后续参数的 NWB 维度 |
| 添加新分支 | L15 (NBR), L47-L55 (分支参数) |
| 添加新支流 | L17 (NTR), L133 (支流参数) |
| 添加新闸门 | L17 (NGT), L109-L117 (闸门参数) |
| 添加新水质变量 | L193-L197 (组分定义), L199-L207 (初始条件) |

---

## 生成信息

- **分析日期**: 2026-03-31
- **源代码版本**: CE-QUAL-W2 v4.5
- **分析文件**: `w2_con.csv` (920行), `input.F90` (~3000行)
