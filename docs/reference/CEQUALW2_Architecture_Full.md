# CE-QUAL-W2 完整代码架构文档

## 项目信息

| 属性 | 值 |
|------|-----|
| **名称** | CE-QUAL-W2 |
| **版本** | 4.5.5 |
| **类型** | 二维侧向平均水动力与水质模型 |
| **维护者** | Portland State University |
| **开发语言** | Fortran 90/95 |
| **构建系统** | Visual Studio + Intel Fortran |

---

# 第一部分：文件总览

## 1.1 项目文件统计

| 类别 | 数量 |
|------|------|
| `.F90` 核心模块 | 16 |
| `.f90` 专用模块 | 29 |
| `Diagenesis*` (沉积物成岩) | 7 |
| **总计** | **52** |

## 1.2 文件分组

| 组别 | 内容 | 文件数 |
|------|------|--------|
| A | 核心框架 | 4 |
| B | 初始化模块 | 4 |
| C | 水动力核心 | 4 |
| D | 热力学与密度 | 3 |
| E | 水质模块 | 5 |
| F | 建筑物与结构 | 3 |
| G | 生态与生物 | 4 |
| H | 沉积物成岩模型 | 7 |
| I | 辅助模块 | 8 |
| J | 其他工具 | 2 |

---

# 第二部分：核心框架 (Group A)

---

## w2_4_win.f90

- **路径**: `w2source_v455_2_11_2026/w2_4_win.f90`
- **行数**: 1743
- **功能**: Windows GUI应用程序的主入口点函数CE_QUAL_W2，包含完整的2D水动力和水质模拟主循环
- **模块定义**: `MSCLIB`, `MAIN`, `GLOBAL`, `NAMESC`, `GEOMC`, `LOGICC`, `PREC`, `SURFHE`, `KINETIC`, `SHADEC`, `EDDY`, `STRUCTURES`, `TRANS`, `TVDC`, `SELWC`, `GDAYC`, `SCREENC`, `TDGAS`, `RSTART`, `INITIALVELOCITY`
- **入口点/子程序**:
  - `CE_QUAL_W2(DLG)`: 主函数，接收Dialog参数用于GUI交互
  - `RESTART_OUTPUT` (external): 输出重启数据
- **关键局部变量**:
  - `DLG`: TYPE(DIALOG) - Windows对话框句柄
  - `DEPTH`, `RESULT`, `CSVFORMAT`, `CHAR30`, `CHAR8`: 临时计算变量
  - `DIRC`, `LENGTH`, `ISTATUS`: 目录路径处理
  - `END_RUN`, `STOP_PUSHED`, `ERROR_OPEN`: 程序控制标志
- **调用关系**:
  - 被 Windows GUI 调用
  - 调用: `INPUT`, `INIT`, `INITIAL_WATER_LEVEL`, `INITGEOM`, `INITIAL_U_VELOCITY`, `OUTPUTINIT`, `SELECTIVEINIT`, `SELECTIVE`, `HYDROINOUT`, `TEMPERATURE`, `wqconstituents`, `BALANCES`, `UPDATE`, `SCREEN_UPDATE`, `RESTART_OUTPUT`, `ENDSIMULATION`, `CEMA_W2_Input`, `ReadMetRegions`, `MetRegionsWB`, `SetupCEMASedimentModel`, `CEMAFFTLayerCode` 等
- **核心算法/公式**:
  - 主时间循环: `DO WHILE (.NOT. END_RUN.AND. .NOT. STOP_PUSHED)`
  - Task 2.2: 水动力计算 - 包含边界条件处理、动量项计算、水面高程求解(隐式Tridiagonal解)、纵向/垂向速度计算
  - 水平对流: `ADMX(K,I)` - 使用上风/中心差分
  - 垂直涡粘性: `IMPLICIT_VISC` 隐式求解
  - 水面高程隐式解: Tridiagonal方程组 `A(I)*Z(I-1) + V(I)*Z(I) + C(I)*Z(I+1) = D(I)`
- **与其他模块的接口**: 通过 `USE` 语句引入所有主要模块

---

## w2modules.F90

- **路径**: `w2source_v455_2_11_2026/w2modules.F90`
- **行数**: 906
- **功能**: 定义CE-QUAL-W2模型的所有25个模块，包含变量声明、参数定义和函数接口
- **模块定义** (25个模块):
  1. `MSCLIB` - Windows线程库接口
  2. `PREC` - 精度参数 (R8=double precision, I2=integer)
  3. `RSTART` - 重启相关变量
  4. `GLOBAL` - 全局变量 (U,W,T1,T2,C1,C2,EL,DLX等)
  5. `GEOMC` - 几何计算变量 (B,EL,H,DLX,SLOPE等)
  6. `NAMESC` - 名称和字符变量
  7. `STRUCTURES` - 水利结构物(堰、闸门、管道等)
  8. `TRANS` - 输移变量
  9. `SURFHE` - 表面热交换
  10. `TVDC` - 时间变化数据控制
  11. `KINETIC` - 动力学参数和变量
  12. `SELWC` - 选择性水位输出
  13. `GDAYC` - 日期和时间
  14. `SCREENC` - 屏幕输出控制
  15. `TRIDIAG_V` - Tridiagonal求解器
  16. `TDGAS` - 总溶解气体
  17. `LOGICC` - 逻辑控制标志
  18. `SHADEC` - 阴影计算
  19. `EDDY` - 涡流相关(粘度、扩散)
  20. `MACROPHYTEC` - 大型植物
  21. `POROSITYC` - 孔隙率
  22. `ZOOPLANKTONC` - 浮游动物
  23. `INITIALVELOCITY` - 初始流速
  24. `ENVIRPMOD` - 环境绩效模块
  25. `ALGAE_TOXINS` - 藻类毒素
  26. `MAIN` - 主模块(大量变量声明)
  27. `BIOENERGETICS` - 生物能量学
  28. `CEMAVars` - CEMA沉积物相关
  29. `Selective1TDGtarget` - 选择性TDG目标
  30. `AlgaeReduceGasTransfer` - 藻类减少气体传输
- **入口点/子程序**:
  - `MODULE KINETIC` 包含内部函数:
    - `SATO(T,SAL,P,SALT_WATER)`: 溶解氧饱和度
    - `FR(TT,TT1,TT2,SK1,SK2)`: 温度函数
    - `FF(TT,TT3,TT4,SK3,SK4)`: 温度函数

---

## input.F90

- **路径**: `w2source_v455_2_11_2026/input.F90`
- **行数**: 2584
- **功能**: 读取控制文件(w2_con.npt或w2_con.csv)，解析模型配置参数，分配所有数组内存
- **入口点/子程序**:
  - `INPUT()`: 主输入解析子程序
- **关键局部变量**:
  - `NWB, NBR, IMX, KMX` - 水体、支流、水平段数、垂向层数
  - `NCT` - 总constituents数量
  - `DZMAX` - 垂向扩散系数限制
- **核心算法/公式**:
  - 支持两种控制文件格式: NPT (固定列格式) 和 CSV (逗号分隔)
  - 成分编号自动计算 (第72-150行)
  - 大规模内存分配: 400+ 行ALLOCATE语句

---

## init.F90

- **路径**: `w2source_v455_2_11_2026/init.F90`
- **行数**: 819
- **功能**: 模型变量初始化主程序，零化变量、设置逻辑控制、准备计算
- **入口点/子程序**:
  - `INIT()`: 主初始化子程序
- **核心算法/公式**:
  - Task 1.1.1 Zero Variables: 初始化所有数组为0或默认值
  - Task 1.1.2 Miscellaneous Variables: 设置逻辑控制标志
  - 斜率转换为角度: `ALPHA = ATAN(SLOPE)`, `SINA = SIN(ALPHA)`, `COSA = COS(ALPHA)`
  - 动力学速率从 per-day 转换为 per-second: `AE = AE/DAY` 等

---

# 第三部分：初始化模块 (Group B)

---

## init-geom.F90

- **路径**: `w2source_v455_2_11_2026/init-geom.F90`
- **行数**: 642
- **功能**: 初始化水体的几何参数，包括层高、底面高程、宽度、水面高程、段长度等
- **入口点/子程序**:
  - `INITGEOM()`: 几何初始化主程序
- **关键局部变量**:
  - `Z(I)`: 水面偏差
  - `KTWB(JW)`: 每个水体的顶部活跃层
  - `KTI(I)`: 每个段的水面层索引
- **核心算法/公式**:
  - 零坡度情况: `EL(K,I) = EL(K+1,I) + H(K,JW)`
  - 有坡度情况: 追踪连接点，使用 `SINA(JB)*DLX` 计算高程差
  - 层高计算: `HMIN = MIN(H(K,JW))`, `HMAX = MAX(H(K,JW))`
  - 水面层确定: 迭代找到 `EL(KTI(I),I) > ELWS(I)` 的层

---

## init-cond.F90

- **路径**: `w2source_v455_2_11_2026/init-cond.F90`
- **行数**: 511
- **功能**: 初始化水温、水质成分、沉积物、冰盖等初始条件
- **入口点/子程序**:
  - `INITCOND()`: 初始条件设置主程序
- **核心算法/公式**:
  - 垂向剖面: 从 `VPRFN(JW)` 文件读取温度和水质垂向分布
  - 温度初始化:
    - `LONG_TEMP`: 从LPR文件读取
    - `ISO_TEMP`: `T1(K,I) = T2I(JW)` (均匀)
    - `VERT_TEMP`: `T1(K,I) = TVP(K,JW)` (垂向变化)
  - 沉积物初始化: `SED`, `SEDP`, `SEDn`, `SEDc` 分别处理
  - 冰盖初始化: `ICETH(I) = ICETHI(JW)`

---

## init-u-elws.f90

- **路径**: `w2source_v455_2_11_2026/init-u-elws.f90`
- **行数**: 428
- **功能**: 初始化水平流速和水位，基于估计流量使用正常水深方程计算初始水位
- **入口点/子程序**:
  - `INITIAL_WATER_LEVEL()`: 主程序，估计流量并计算水位
  - `NORMAL_DEPTH(FLOW)`: 使用Manning方程的正常水深计算
  - `MANNINGS_EQN(FLOW, DEPTH, FUNCVALUE)`: Manning方程求根函数
  - `XSECTIONAL_AREA(WSURF, XAREA)`: 横截面面积计算
  - `INITIAL_U_VELOCITY()`: 基于估计流量初始化水平流速
- **核心算法/公式**:
  - **正常水深计算**: 使用 bisection 法求解 Manning 方程 `Q - A*R^(2/3)*S^(1/2)/n = 0`
  - **Manning方程**: `FUNCVALUE = FLOW - A*R^(2/3)*S^(1/2)/n`

---

## waterbody.f90

- **路径**: `w2source_v455_2_11_2026/waterbody.f90`
- **行数**: 704
- **功能**: 计算水体边界的水动力学和水质交换，包含多个ENTRY点的复杂子程序
- **入口点/子程序** (9个ENTRY):
  - `WATERBODY`: 主程序框架
  - `UPSTREAM_VELOCITY`: 上游边界速度
  - `UPSTREAM_WATERBODY`: 上游边界水温水质
  - `DOWNSTREAM_WATERBODY`: 下游边界水温水质
  - `UPSTREAM_BRANCH`: 支流汇入速度
  - `DOWNSTREAM_BRANCH`: 支流分出速度
  - `UPSTREAM_FLOW`: 上游边界流量
  - `DOWNSTREAM_FLOW`: 下游边界流量
  - `UPSTREAM_CONSTITUENT(C,SS)`: 上游边界成分
  - `DOWNSTREAM_CONSTITUENT(C,SS)`: 下游边界成分
  - `DEALLOCATE_WATERBODY`: 释放内存

---

# 第四部分：水动力核心 (Group C)

---

## hydroinout.F90

- **路径**: `w2source_v455_2_11_2026/hydroinout.F90`
- **行数**: ~1427
- **功能**: 处理水动力源汇项，包括入库、出库、退水、溢洪道、泵、管道、闸门和总溶解气体(TDG)计算
- **入口点/子程序**:
  - `HYDROINOUT`: 主子程序
  - `DOWNSTREAM_WITHDRAWAL`: 取水口计算
  - `LATERAL_WITHDRAWAL`: 侧向取水
  - `SPILLWAY_FLOW`: 溢洪道流量
  - `PIPE_FLOW`: 管道流量
  - `GATE_FLOW`: 闸门流量
  - `TOTAL_DISSOLVED_GAS`: TDG饱和计算
- **关键局部变量**:
  - `QINSUM`, `TINSUM`, `CINSUM`: 累计入库体积、温度、物质质量
  - `QSUM(JB)`: 支流总出流量
  - `QTR(JT)`, `TTR(JT)`, `CTR(CN,JT)`: 支流流量、温度、浓度
- **核心算法/公式**:
  - 基于密度的层分配: `RHOTR = DENSITY(TTR(JT),CTR(NTDS,JT),SSTOT)`
  - TDG计算: `CALL TOTAL_DISSOLVED_GAS(itype,PALT,sg,JG,T,C)`

---

## az.f90

- **路径**: `w2source_v455_2_11_2026/az.f90`
- **行数**: 595
- **功能**: 计算垂向湍流(AZ/DZ涡粘度/扩散率)，使用多种湍流模型求解TKE方程
- **模块定义**: `MODULE AZ_LOCAL` (lines 5-13)
- **入口点/子程序**:
  - `CALCULATE_AZ`: 主入口 - 根据AZC(JW)设置选择湍流模型
  - `CALCULATE_AZ0`: 非TKE模型的基涡粘度AZ0
  - `CALCULATE_TKE`: 标准k-epsilon模型
  - `CALCULATE_TKE1`: 带壁面函数的替代k-epsilon模型
  - `WALLFUNCTION`: 使用对数壁定律计算摩擦速度
  - `SEMILOG`: 壁函数迭代辅助函数
  - `RTBIS`: 壁函数的二分法求根
  - `CALCFRIC`: 从TKE计算Manning's n或Darcy-Weisbach摩擦
- **关键局部变量**:
  - `TKEMIN1=1.25D-7`, `TKEMIN2=1.0D-9`: 最小TKE和epsilon值
  - `VSH(K,I)`: 垂直剪切平方
  - `AZT(K,I)`: 基于TKE的单元格中心涡粘度
  - `DZ(K,I)`: 涡扩散率
- **核心算法/公式** - 湍流模型选择 (通过AZC(JW)):

  **1. TKE - 标准k-epsilon (Rodi):**
  - TKE输运: `TKE(K,I,1)+DLT*(UNST+PRHK-BOUK)`
  - Epsilon输运: `TKE(K,I,2)+DLT*(UNSE+PRHE)`
  - `AZT(K,I) = 0.09*TKE(K,I,1)*TKE(K,I,1)/TKE(K,I,2)` (k^3/2 / epsilon)

  **2. TKE1 - 带壁面函数的替代k-epsilon:**
  - 使用壁函数计算底部摩擦速度
  - 三种边界条件选项 (TKEBC=1,2,3)

  **3. NICK - Nickerson (简化):**
  ```fortran
  SLM = ((DEPTHR+DEPTHL)*0.5*(0.14-0.08*(1.0-ZD)**2-0.06*(1.0-ZD)**4))**2
  AZ0 = MAX(AZMIN, SLM*SQRT(VSH(K,I)))
  ```

  **4. RNG - Renormalization Group:**
  ```fortran
  VISCK = EXP(-(T2(K,I)+495.691)/37.3877)
  VISCF = (1+0.08477*((ZDLR*0.5*USTAR/VISCK)**3)*(...))^1/3
  AZ0 = MAX(AZMIN, VISCK*VISCF)
  ```

  **5. PARAB - 抛物线:**
  ```fortran
  AZ0 = MAX(AZMIN, 0.41*USTAR*ZDLR*0.5*(1.0-ZD))
  ```

  **6. W2N - W2特定:**
  ```fortran
  AZ0 = 0.4*SLM*SQRT(VSH+((FRICBR+WSHY*DECAY)/(AZ+NONZERO))**2)+AZMIN
  ```

---

## transport.f90

- **路径**: `w2source_v455_2_11_2026/transport.f90`
- **行数**: 548
- **功能**: 实现ULTIMATE (Universally Limiter with Total Variation Diminishing)物质输移方案
- **入口点/子程序**:
  - `TRANSPORT`: 主子程序
  - `INTERPOLATION_MULTIPLIERS`: 计算几何插值因子SF1X-SF13X, SF1Z-SF10Z
  - `HORIZONTAL_MULTIPLIERS1`: 第一遍水平乘子
  - `HORIZONTAL_MULTIPLIERS`: 第二遍水平乘子(含TVD限制)
  - `VERTICAL_MULTIPLIERS1`: 第一遍垂直乘子
  - `VERTICAL_MULTIPLIERS`: 第二遍垂直乘子(含TVD限制)
  - `TRIDIAG`: 三对角矩阵求解器 (Thomas算法)
- **核心算法/公式** - ULTIMATE方案 (Leonard 1991):

  **Courant数:**
  `COUR = U(K,I)*DLT/DLXR(I)`

  **TVD Flux Limiting算法:**
  ```fortran
  IF (ACURZ <= 0.6*ADELC) THEN
     FLUX = AD1X*C1X+AD2X*C2X+AD3X*C3X      ! 低曲率：中心差分
  ELSE IF (ACURZ >= ADELC) THEN
     FLUX = C2X                            ! 高曲率：上风
  ELSE
     ! 限制器区域：在上风和平滑之间混合
     FTEMP = AD1X*C1X+AD2X*C2X+AD3X*C3X
     CREF  = CALF+(C2X-CALF)/ABS(COUR)
     IF (DELC > 0) THEN
        CMAX1 = MIN(CREF, CART)
        FLUX  = 0.5*(C2X+CMAX1)
     ELSE
        CMIN1 = MAX(CREF, CART)
        FLUX  = 0.5*(C2X+CMIN1)
     END IF
  END IF
  ADX = (DX1*C1X+DX2*C2X+DX3*C3X) - U*FLUX
  ```

---

## layeraddsub.F90

- **路径**: `w2source_v455_2_11_2026/layeraddsub.F90`
- **行数**: 1295
- **功能**: 通过层的增加/减少以及支流的激活/关闭来管理动态垂直网格调整
- **入口点/子程序**:
  - `LAYERADDSUB`: 主子程序 - 唯一的入口点
- **关键局部变量**:
  - `KTWB(JW)`: 水体JW的顶部活跃层
  - `ZMIN(JW)`: 相对于层顶的最小水面高程
  - `ADD_LAYER`: 添加层标志
  - `SUB_LAYER`: 减少层标志
- **核心算法/公式**:

  **层添加触发:**
  `ADD_LAYER = ZMIN(JW) < -0.85*H(KT-1,JW) .AND. KT /= 2`
  当水面下降到当前顶层层下方层厚的85%时，添加新的表层。

  **层减少触发:**
  `SUB_LAYER = ZMIN(JW) > 0.60*H(KT,JW) .AND. KT < KTMAX`
  当水面上升到当前顶层层厚的60%以上时，移除顶层。

  **层添加过程:**
  1. `KTWB(JW) = KTWB(JW) - 1`
  2. 重新计算Z: `Z(I) = H(KT,JW) + Z(I)`
  3. 新表层厚度: `H1(KT,I) = H(KT,JW) - Z(I)`
  4. 从KT+1传播变量到KT: T1, T2, C1, C2, SED*等
  5. 新表层的AZ, TKE设为最小值

---

# 第五部分：热力学与密度 (Group D)

---

## temperature.F90

- **路径**: `w2source_v455_2_11_2026/temperature.F90`
- **行数**: 597
- **功能**: 计算热交换，包括表面热通量、沉积物热交换、结冰/融冰，以及求解温度输运方程
- **入口点/子程序**:
  - `TEMPERATURE`: 主子程序
  - 调用: `SHORT_WAVE_RADIATION`, `EQUILIBRIUM_TEMPERATURE`, `SURFACE_TERMS`, `SHADING`, `HORIZONTAL_MULTIPLIERS1`, `VERTICAL_MULTIPLIERS1`, `HORIZONTAL_MULTIPLIERS`, `VERTICAL_MULTIPLIERS`
- **关键局部变量**:
  - `BTA1(1000), GMA1(1000)`: 三对角求解器工作数组
  - `TSS(K,I)`: 温度源汇数组
  - `SROOUT`: 到达层的光短波辐射
  - `ICETH(I)`: 冰厚度
- **核心算法/公式**:

  **热交换方法1 - 逐项法** (`TERM_BY_TERM(JW)`):
  ```fortran
  RN(I) = RS(I) + RANLW(JW) - RB(I) - RE(I) - RC(I)
  RS(I) = SRON(JW)*SHADE(I)
  HEATEX = RN(I)/RHOWCP*BI(KT,I)*DLX(I)
  TSS(KT,I) = TSS(KT,I) + HEATEX
  ```

  **热交换方法2 - 平衡温度法:**
  ```fortran
  HEATEX = (ET(I)-T2(KT,I))*CSHE(I)*BI(KT,I)*DLX(I)
  ```

  **冰形成 (DETAILED_ICE):**
  - 检查表面T < ICET2: `IF (T2(KT,I) < 0.0) THEN`
  - 从热量内容计算冰厚度: `ICETH2 = -T2(KT,I)*RHO(KT,I)*CP*H2(KT,I)/RHOIRL1`

---

## heat-exchange.f90

- **路径**: `w2source_v455_2_11_2026/heat-exchange.f90`
- **行数**: 497
- **功能**: 计算表面热交换，包括短波辐射(Bird-Meeus模型)、平衡温度法和表面通量项
- **模块定义**: `MODULE Bird_Meeus` (lines 183-197)
- **入口点/子程序**:
  - `HEAT_EXCHANGE`: 主子程序(多入口)
  - `SHORT_WAVE_RADIATION`: 计算日短波辐射
  - `EQUILIBRIUM_TEMPERATURE`: 计算平衡温度和热交换系数
  - `SURFACE_TERMS(TSUR)`: 给定表面温度计算表面通量
  - `MEEUS`: 完整太阳位置和辐射模型
  - `Ozone`: 使用Van Heuklon (1979)计算臭氧浓度
  - `BirdModel`: Bird宽带辐射模型
- **核心算法/公式**:

  **Meeus太阳位置模型:**
  - Julian日期: `jd = FLOOR(365.25*(year+4716)) + ...`
  - 太阳高度角: `SINAL = SIN(LAT)*SIN(DECL) + COS(LAT)*COS(DECL)*COS(HH)`
  - 辐射: `SRON = globalHz*(1-CC_SW*CLOUD^2)*0.94`

  **平衡温度法:**
  ```fortran
  ET = TDEW_F  ! 初始猜测
  ! 迭代求解 (最多10次, 容差0.05 F)
  BETA = 0.255 - 0.0085*TSTAR + 0.000204*TSTAR^2
  FW = ACONV*AFW + BCONV*BFW*WIND2M^CFW
  CSHE = 15.7 + (0.26+BETA)*FW
  ET = ((SRO_BR + RA - 1801)/CSHE + ...)/conversion
  ```

---

## density.f90

- **路径**: `w2source_v455_2_11_2026/density.f90`
- **行数**: 28
- **功能**: 计算水密度作为温度(T)、溶解性固体(TDS)和悬浮固体(SS)的函数
- **入口点/子程序**:
  - `DENSITY(T, TDS, SS)`: 返回水密度 (kg/m³)
- **核心算法/公式**:

  **UNESCO/Chen-Miller方程 (T > 0):**
  ```fortran
  DENSITY = (((((6.536332D-9*T - 1.120083D-6)*T + 1.001685D-4)*T
              - 9.09529D-3)*T + 6.793952D-2)*T + 0.842594D0
  ! 展开后:
  ! 0.842594 + 6.793952E-2*T - 9.09529E-3*T^2 + 1.001685E-4*T^3
  ! - 1.120083E-6*T^4 + 6.536332E-9*T^5
  ```

  **悬浮固体校正 (SUSP_SOLIDS):**
  `+ 6.2E-4 * SS`

  **淡水TDS校正 (FRESH_WATER):**
  `+ TDS * (8.221E-4 + 4.99E-8*T^2 - 3.87E-6*T)`

  **盐水TDS校正 (SALT_WATER):**
  使用完整的UNESCO盐度方程

---

# 第六部分：水质模块 (Group E)

---

## water-quality.f90

- **路径**: `w2source_v455_2_11_2026/water-quality.f90`
- **行数**: 3165
- **功能**: 主水质量动力学计算模块，包含38个入口点，处理所有水质组分的生化反应动力学
- **入口点/子程序** (38个ENTRY POINTS):
  1. `KINETICS` - 主入口
  2. `TEMPERATURE_RATES` - 温度速率乘数
  3. `KINETIC_RATES` - 动力学速率计算
  4. `GENERIC_CONST(JG)` - 通用示踪剂
  5. `SUSPENDED_SOLIDS(J)` - 悬浮固体沉降
  6. `WATER_AGE` - 水龄
  7. `BACTERIA` - 细菌动力学
  8. `DISSOLVED_GAS` - 溶解气体
  9. `DISSOLVED_N2` - 溶解氮气
  10. `SULFIDE` - 硫化物(H2S)
  11. `METHANE` - 甲烷(CH4)
  12. `SULFATE` - 硫酸盐
  13-16. `FERROUS`, `OXIDIZEDFE`, `BIVALENTMN`, `OXIDIZEDMN` - 铁/锰循环
  17. `PHOSPHORUS` - 磷循环
  18. `AMMONIUM` - 氨氮
  19. `NITRATE` - 硝酸盐
  20-21. `DISSOLVED_SILICA`, `PARTICULATE_SILICA` - 硅循环
  22-25. `LABILE_DOM`, `REFRACTORY_DOM`, `LABILE_POM`, `REFRACTORY_POM` - 有机质
  26. `ALGAE(J)` - 藻类动力学
  27-28. `INTRACELLULAR_TOXIN`, `EXTRACELLULAR_TOXIN` - 毒素
  29-31. `BIOCHEMICAL_O2_DEMAND*` - BOD
  32. `DISSOLVED_OXYGEN` - 溶解氧
  33. `INORGANIC_CARBON` - 无机碳
  34-37. `SEDIMENT*` - 沉积物通量
  38. `EPIPHYTON(J)` - 附生植物
  39-43. 有机P/N/C组分
  44. `MACROPHYTE` - 大型植物
  45. `KINETIC_FLUXES` - 动力学通量
  46-47. `PH_CO2`, `PH_CO2_NEW` - pH计算
  48. `ZOOPLANKTON` - 浮游动物
  49. `DERIVED_CONSTITUENTS` - 导出变量
  50. `ALKALINITY` - 碱度
- **核心算法/公式**:

  **温度响应:**
  `FR(T,T1,T2,K1,K2) = 1/(1+exp(-K1*(T-T1))*exp(K2*(T-T2)))`

  **光限制:**
  `ALLIM = (exp(-LAM2)-exp(-LAM1))/(GAMMA*H2)`

  **藻类生长:**
  `AGR = ATRM*AG*LIMIT`

---

## wqconstituents.F90

- **路径**: `w2source_v455_2_11_2026/wqconstituents.F90`
- **行数**: 588
- **功能**: 水质组分的主封装程序，协调沉积物、动力学、宏观植物和传输计算
- **入口点/子程序**:
  - `WQCONSTITUENTS` - 主入口
- **核心算法/公式**:
  - 质量平衡: `TP = ALG*AP + PO4 + DOM + POM`
  - 沉积物-水界面通量
  - 三对角矩阵求解用于传输

---

## gas-transfer.f90

- **路径**: `w2source_v455_2_11_2026/gas-transfer.f90`
- **行数**: 177
- **功能**: 复氧和气体交换计算
- **入口点/子程序**:
  - `GAS_TRANSFER` - 主入口
- **核心算法/公式**:

  **河流复氧 (REAERC='RIVER') - 10种公式可选:**
  - NEQN=1: O'Connor-Dobbins: `12.96*sqrt(UAVG)/ADEPTH^1.5`
  - NEQN=2: Churchill: `11.57*UAVG^0.969/ADEPTH^1.673`
  - NEQN=4: Owens: `21.64*UAVG^0.67/ADEPTH^1.85`

  **湖泊复氧 (REAERC='LAKE') - 基于风速:**
  - NEQN=1: Broecker: `0.864*WIND10`
  - NEQN=4: Wanninkhof: `0.0986*WIND10^1.64`

---

## balances.F90

- **路径**: `w2source_v455_2_11_2026/balances.F90`
- **行数**: 222
- **功能**: 体积、能量和质量平衡计算
- **入口点/子程序**:
  - `BALANCES` - 主入口
- **核心算法/公式**:
  - 体积平衡: `DLVR = (VOLTR-VOLSR)/VOLSR * 100%`
  - 输出格式: CSV (FLOWBFN, MASSBFN)

---

## shading.f90

- **路径**: `w2source_v455_2_11_2026/shading.f90`
- **行数**: 135
- **功能**: 地形和植被阴影对水面短波辐射的影响计算
- **入口点/子程序**:
  - `SHADING` - 主入口
- **核心算法/公式**:
  - 太阳高度角: `SINAL = sin(LAT)*sin(DECL) + cos(LAT)*cos(DECL)*cos(HH)`
  - 地形阴影: 线性插值TOPO数组
  - 最终遮阴: `SHADE = max(0, min(SHADEI, 1-SFACT))`

---

# 第七部分：建筑物与结构 (Group F)

---

## withdrawal.f90

- **路径**: `w2source_v455_2_11_2026/withdrawal.f90`
- **行数**: 3876
- **功能**: 选择性取水结构计算，基于密度分层确定取水深度和流速分布
- **模块定义**: `SELECTIVE1`
- **入口点/子程序**:
  - `WITHDRAWAL` (4个ENTRY)
  - `SELECTIVEINIT` - 初始化
- **核心算法/公式**:
  - 密度频率: `RHOFT = sqrt(|RHO(K)-RHO(KSTR)|/(HT*RHO(KSTR))*g)`
  - 取水厚度(点汇): `HSWT = (COEF*QSTR/RHOFT)^0.333`
  - 速度分布: `VNORM = (1-((RHO-RHOSTR)/DLRHO)^2)*BHR2`

---

## gate-spill-pipe.f90

- **路径**: `w2source_v455_2_11_2026/gate-spill-pipe.f90`
- **行数**: 1612
- **功能**: 闸门、溢洪道、管道水力学计算
- **模块定义**: `Pipe`
- **入口点/子程序**:
  - `GATE_FLOW` - 闸门流量
  - `SPILLWAY_FLOW` - 溢洪道流量
  - `PIPE_FLOW_INITIALIZE` - 管道流初始化
  - `OPEN_CHANNEL_INITIALIZE` - 开口河道求解
  - `LUDCMP/LUBKSB` - LU矩阵求解
  - `TYPE1-TYPE7` - 管道流类型函数
- **核心算法/公式**:
  - 闸门流: `Q = A1*DLEL^B1 * BGT^G1` (自由流)
  - 管道流: 隐式有限差分求解St. Venant方程

---

## systdg.f90

- **路径**: `w2source_v455_2_11_2026/systdg.f90`
- **行数**: 442
- **功能**: 系统总溶解气体(TDG)计算
- **模块定义**: `modSYSTDG`
- **入口点/子程序**:
  - `INPUT_SYSTDG` - 读取控制文件
  - `SYSTDG_TDG` - TDG生产主计算
  - `UPDATE_TDGC` - TDG饱和计算
- **核心算法/公式**:
  - TDG饱和: `SAT = exp(7.7117-1.31403*log(T+45.93))*P` (O2)
  - TDG方程 (TDGEQ 1-5): 不同溢洪道TDG计算公式

---

# 第八部分：生态与生物 (Group G)

---

## fish-particle.f90

- **路径**: `w2source_v455_2_11_2026/fish-particle.f90`
- **行数**: 4677
- **功能**: 数值鱼类替代模型(NFS)，模拟鱼类在水体中的运动行为
- **模块定义**: `Fishy`
- **入口点/子程序**:
  - `FISH` - 主入口
  - `FIMPBR` - 分支映射
  - `SPLINE/RANDOM` - 数学工具
  - `FINDNEWBR` - 分支切换
  - `FISHPLOT` - 鱼轨迹输出
- **核心算法/公式**:
  - 刺激-响应规则: 速度梯度、温度梯度、DO梯度
  - 聚集行为: 鱼的聚集/分散规则
  - 边界处理: 反射边界条件

---

## fishhabitat.f90

- **路径**: `w2source_v455_2_11_2026/fishhabitat.f90`
- **行数**: 466
- **功能**: 鱼类栖息地指数分析
- **入口点/子程序**:
  - `FISHHABITAT(IOPENFISH)` - 主入口
- **核心算法/公式**:
  - 栖息地条件: `TEMPL < T < TEMPH .AND. DO > FDO`
  - 栖息地分数: `PHABVOL = HABVOL/VOLTOT`

---

## macrophyte-aux.f90

- **路径**: `w2source_v455_2_11_2026/macrophyte-aux.f90`
- **行数**: 363
- **功能**: 大型植物的孔隙度计算和摩擦系数修正
- **入口点/子程序**:
  - `POROSITY` - 孔隙度计算
  - `MACROPHYTE_FRICTION` - 植物摩擦修正
- **核心算法/公式**:
  - 孔隙度: `POR = (VOL-VSTOT)/VOL`
  - 植物附加阻力: `FRIN = CDAVG*TSAREA*HRAD^(4/3)/(2*G*XSAREA*DLX*BEDFR^2)`

---

## tdg.f90

- **路径**: `w2source_v455_2_11_2026/tdg.f90`
- **行数**: 85
- **功能**: 总溶解气体(TDG)过饱和计算
- **入口点/子程序**:
  - `TOTAL_DISSOLVED_GAS(NSAT,P,NSG,N,T,C)` - FUNCTION
- **核心算法/公式**:
  - DO饱和: `SAT = exp(7.7117-1.31403*log(T+45.93))*P`
  - TDG限制: 最大145%

---

# 第九部分：沉积物成岩模型 CEMA (Group H)

## 概述

CEMA (Sediment Diagenesis Model) 是一个完整的沉积物-水界面通量模型，基于DiToro的沉积物成岩理论。

---

## Diagenesis Sediment Model 03.f90

- **路径**: `Diagenesis Sediment Model 03.f90`
- **行数**: ~680
- **功能**: 实现床层固结动力学、侵蚀/沉积过程和垂直层管理
- **入口点/子程序**:
  - `CEMASedimentModelW2`: 主入口
  - `SetupCEMASedimentModel`: 初始化床层文件
  - `CEMASedimentModel`: 核心沉积物模型
  - `CEMAUpdateVerticalLayering`: 垂直层管理
  - `ComputeCEMARelatedSourceSinks`: 源汇计算
- **核心算法/公式**:
  - 床层固结: `BedElevation = BedElevation - BedConsolidRate*dlt`
  - 孔隙度更新: `BedPorosity = 1 - VolumeofSedimentBed1/VolumeofSedimentBed2*(1-BedPorosity)`

---

## Diagenesis Sediment Flux Model 05.f90

- **路径**: `Diagenesis Sediment Flux Model 05.f90`
- **行数**: ~3000+
- **功能**: 核心沉积物成岩计算，包括有机质分解、营养盐通量、甲烷生成和沉积物-水交换
- **模块定义**: `Module CEMASedimentDiagenesis`
- **入口点/子程序**:
  - `InitCond_SedFlux`: 初始化
  - `CEMAMFTRatesandConstants`: 动力学参数
  - `CEMAMFTSedFlux`: 主沉积物通量计算
- **核心算法/公式**:
  - 双层(好氧/厌氧)成岩模型
  - POC分解: 活性、难降解和惰质组分
  - 甲烷生成: `SD_Ae_CH4_CO2` 系数

---

## Diagenesis FFT Layer 01.f90

- **路径**: `Diagenesis FFT Layer 01.f90`
- **行数**: ~119
- **功能**: 管理FFT (Fate and Transport of Fine) 沉积物层
- **入口点/子程序**:
  - `CEMAFFTLayerCode`: FFT层管理
  - `MoveFFTLayerConsolid`: 层固结时移动浓度

---

## Diagenesis Input 02.f90

- **路径**: `Diagenesis Input 02.f90`
- **行数**: ~2400+
- **功能**: 从 `W2_diagenesis.npt` 读取CEMA参数
- **入口点/子程序**:
  - `CEMA_W2_Input`: 主输入读取
  - `INIT_CEMA`: CEMA变量初始化

---

## Diagenesis Input Files Read 01.f90

- **路径**: `Diagenesis Input Files Read 01.f90`
- **行数**: ~58
- **功能**: 读取床层固结率数据文件

---

## Diagenesis Output 02.f90

- **路径**: `Diagenesis Output 02.f90`
- **行数**: ~166
- **功能**: CEMA模型输出到CSV文件
- **模块定义**: `Module CEMAOutputRoutines`

---

## Diagenesis Bubbles Code 01.f90

- **路径**: `Diagenesis Bubbles Code 01.f90`
- **行数**: ~620
- **功能**: 甲烷/硫化氢气泡形成、上升和气体交换模拟
- **入口点/子程序**:
  - `GasBubblesFormation`: 气泡核化和生长
  - `CEMACalculateRiseVelocity`: 上升速度
  - `CEMABubblesTransport`: 上升输运
  - `CEMABubblesRelease`: 表面释放
  - `CEMABubbWatTransfer`: 气泡-水气体交换
- **核心算法/公式**:
  - 气泡形核准则: `PbubbT > Pcrit`
  - 临界压力: `Pcrit = 1.32*(CritStressIF^6/(E*n*Vbub))^0.2 + P0`
  - Henry定律: `Cg = K*H` where `K = HenryConst/R/T`

---

# 第十部分：辅助模块 (Group I)

---

## update.F90

- **路径**: `w2source_v455_2_11_2026/update.F90`
- **行数**: 194
- **功能**: 更新状态变量到下一时间步
- **入口点/子程序**:
  - `UPDATE` - 主状态更新程序

---

## output.f90

- **路径**: `w2source_v455_2_11_2026/output.f90`
- **行数**: 472
- **功能**: 生成模型结果的格式化快照输出

---

## restart.f90

- **路径**: `w2source_v455_2_11_2026/restart.f90`
- **行数**: 43
- **功能**: 写模型状态到非格式化重启动文件

---

## time-varying-data.f90

- **路径**: `w2source_v455_2_11_2026/time-varying-data.f90`
- **行数**: ~5000+
- **功能**: 读取和插值所有时变边界条件数据
- **核心算法/公式**:
  - 线性插值: `VALUE = OLD*(1-RATIO) + NEW*RATIO`

---

## endsimulation.F90

- **路径**: `w2source_v455_2_11_2026/endsimulation.F90`
- **行数**: 456
- **功能**: 处理模拟终止 - 关闭文件、释放数组

---

## screen_output_intel.f90

- **路径**: `w2source_v455_2_11_2026/screen_output_intel.f90`
- **行数**: 280
- **功能**: Windows GUI接口和实时屏幕更新

---

## aerate.f90

- **路径**: `w2source_v455_2_11_2026/aerate.f90`
- **行数**: 142
- **功能**: 实现低氧分层曝气
- **模块定义**: `MODULE HYPOAERATION`
- **核心算法/公式**:
  - DO-based on/off控制: `IF(O2 > DOON .AND. O2 > DOOFF) AERATEO2 = .FALSE.`

---

## date.f90

- **路径**: `w2source_v455_2_11_2026/date.f90`
- **行数**: 93
- **功能**: 将Julian日转换为Gregorian日历日期

---

# 第十一部分：其他工具 (Group J)

---

## envir_perf.f90

- **路径**: `w2source_v455_2_11_2026/envir_perf.f90`
- **行数**: 441
- **功能**: 环境绩效输出 - 计算温度、流速、深度的频率分布

---

## particle.f90

- **路径**: `w2source_v455_2_11_2026/particle.f90`
- **行数**: ~3800+
- **功能**: 粒子/鱼类追踪 - 模拟拉格朗日粒子运动

---

## Plunge_Point.f90

- **路径**: `w2source_v455_2_11_2026/Plunge_Point.f90`
- **行数**: 43
- **功能**: 估计水库中基于密度分层和流速的 plunge point位置

---

# 第十二部分：模块依赖关系图

```
PREC (精度基础)
   │
   ├── GLOBAL ──► w2_4_win.f90 (主程序)
   │              │
   │              ├── hydroinout.F90 ──► withdrawal.f90, gate-spill-pipe.f90, systdg.f90
   │              ├── temperature.F90 ──► heat-exchange.f90
   │              ├── transport.f90 (ULTIMATE/TVD)
   │              ├── water-quality.f90 ──► wqconstituents.F90
   │              ├── az.f90 (湍流模型)
   │              ├── layeraddsub.F90 (动态网格)
   │              ├── balances.F90
   │              ├── update.F90
   │              ├── output.f90
   │              └── Diagenesis* (CEMA沉积物模型)
```

---

# 第十三部分：核心算法总结

## 水面高程求解 (三对角)

```fortran
A(I) = -RHO(KT,I-1)*G*COSA(JB)*DLT*DLT*BHRHO(I-1)*0.5/DLXR(I-1)
V(I) = RHO(KT,I)*G*COSA(JB)*DLT*DLT*(BHRHO(I)*0.5/DLXR(I)+...) + DLX(I)*BI(KT,I)
D(I) = DLT*(D(I)+DLT*(F(I)-F(I-1))) + DLX(I)*BI(KT,I)*Z(I)
```

## 湍流模型

| 模型 | 公式 |
|------|------|
| TKE | `AZT = 0.09*k^2/epsilon` |
| NICK | `AZ = 0.4*SLM^2*sqrt(VSH)` |
| RNG | `AZ = VISCK*VISCF` |

## ULTIMATE/TVD

```fortran
IF (ACURZ <= 0.6*ADELC) THEN
   FLUX = AD1X*C1X+AD2X*C2X+AD3X*C3X
ELSE IF (ACURZ >= ADELC) THEN
   FLUX = C2X
END IF
```

---

# 附录：关键常数

| 常量 | 值 | 模块 |
|------|-----|------|
| `DAY = 86400.0D0` | 每天秒数 | GLOBAL |
| `G = 9.81D0` | 重力加速度 | GLOBAL |
| `RHOW = 1000.0D0` | 水密度 (kg/m³) | GLOBAL |
| `DZMIN = 1.4D-7` | 最小层厚 | GLOBAL |
| `AZMIN = 1.4D-6` | 最小涡粘度 | GLOBAL |
| `TKEMIN1 = 1.25D-7` | 最小TKE | az.f90 |
| `THETA_REAERATION = 1.024` | 复氧温度校正 | gas-transfer.f90 |

---

# 附录：命名约定

| 模式 | 文件类型 | 示例 |
|------|----------|------|
| `*.F90` (大写) | 核心框架模块 | `w2modules.F90`, `input.F90` |
| `*.f90` (小写) | 专用过程模块 | `water-quality.f90`, `transport.f90` |
| `Diagenesis*` | 沉积物成岩模型 | `Diagenesis Sediment Model 03.f90` |
| `init-*.F90` | 初始化模块 | `init-geom.F90`, `init-cond.F90` |

---

# 附录：入口点命名约定

| 前缀 | 含义 |
|------|------|
| `CALCULATE_*` | 计算类 |
| `INIT*` | 初始化类 |
| `READ*` | 读取数据类 |
| `WRITE*` | 写入输出类 |
| `COMPUTE*` | 计算类 |
| `UPDATE*` | 更新类 |
| `*_MULTIPLIERS` | transport.f90中的插值乘子 |

---

## 文档信息

- **生成时间**: 2026-03-29
- **源项目**: w2source_v455_2_11_2026
- **版本**: 4.5.5
- **文件总数**: 52个源文件
- **文档行数**: ~3000+
