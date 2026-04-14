# 基于原版源码的删除优先级清单

Updated: 2026-04-12

## 1. 适用范围

本清单的判断基于原版源码目录：

- `C:\Users\NING\Desktop\v455\w2source_v455_原版`

不是基于已经精简过的当前源码树做反推。

目标是给“只保留天气 + 水温 + 基础水动力”的后续精简工作提供更可靠的删除顺序参考，避免误删仍属于主求解链或当前支持案例边界的文件。

## 2. 排序原则

删除优先级按下面四条规则排序：

1. 是否完全不在主程序常规求解链上
2. 是否只在显式开关打开时才被调用
3. 是否只服务于水质、鱼类、沉积成岩、环境评估等扩展功能
4. 是否仍被当前 Bonneville 支持边界的结构物/边界条件逻辑依赖

## 3. 优先级 0：不在删除队列中的文件

这些文件不能再按“水质模块”思路误删。

### 3.1 基础水动力 + 温度主链

- `w2_4_win.f90`
- `w2modules.F90`
- `input.F90`
- `waterbody.f90`
- `init.F90`
- `init-geom.F90`
- `init-cond.F90`
- `init-u-elws.f90`
- `time-varying-data.f90`
- `transport.f90`
- `hydroinout.F90`
- `density.f90`
- `az.f90`
- `heat-exchange.f90`
- `shading.f90`
- `temperature.F90`
- `layeraddsub.F90`
- `balances.F90`
- `update.F90`
- `output.f90`
- `outputinitw2tools.F90`
- `outputa2w2tools.F90`
- `restart.f90`
- `date.f90`
- `endsimulation.F90`
- `MetFileRegion.f90`
- `screen_output_intel.f90`

关键理由：

- 原版主程序直接调用 `CALCULATE_AZ`、`temperature`、`LAYERADDSUB`、`BALANCES`、`UPDATE`、`OUTPUTA`
- `temperature.F90` 明确调用 `SHADING`、`SURFACE_TERMS`、`EQUILIBRIUM_TEMPERATURE`
- `SURFACE_TERMS` / `EQUILIBRIUM_TEMPERATURE` 在 `heat-exchange.f90` 中
- `density.f90` 的 `DENSITY` 直接参与主水动力计算

### 3.2 当前支持案例边界内暂不能删的结构/边界模块

- `withdrawal.f90`
- `gate-spill-pipe.f90`
- `systdg.f90`
- `tdg.f90`
- `TDGtarget.f90`

关键理由：

- 原版 `hydroinout.F90` 会调用结构流量与 TDG 相关逻辑
- 当前支持的 Bonneville 基线仍有闸门/泄洪/TDG 形态
- 这组不是水质主反应模块

结论：

- 这组文件可以在以后“改变支持案例契约”后再讨论
- 但不属于当前这轮优先删除对象

## 4. 优先级 1：第一批删除候选

这一组与基础水动力主链无关，且原版源码已经显示出它们是诊断、评估或明显的外部附加功能。

### 4.1 `Plunge_Point.f90`

判断：

- 优先级最高

理由：

- 原版主程序中的调用是注释掉的
- 子程序只读取 `RHO`、`T2`、`U`、`W` 等状态
- 只输出 `Plunge_Point_Estimate.csv`
- 不修改主求解状态

工程含义：

- 它是一个诊断工具，不是求解器组成部分

### 4.2 `fishhabitat.f90`

判断：

- 第一批删除候选

理由：

- 原版只在 `HABTATC == ON` 时于输出阶段调用
- 功能是鱼类栖息地评估与输出
- 不属于基础水动力或温度求解

### 4.3 `envir_perf.f90`

判断：

- 第一批删除候选

理由：

- 原版只在 `ENVIRPC == ON` 时调用
- 功能是环境绩效评估/输出
- 不属于基础水动力或温度求解

### 4.4 `fish-particle.f90`

判断：

- 第一批删除候选

理由：

- 这是鱼类/粒子行为模拟的另一套扩展文件
- 不在原版 `.vfproj` 主文件列表中
- 不应进入“基础水动力 + 温度”目标边界

说明：

- 这个文件更像历史/替代版本参考件

## 5. 优先级 2：第二批删除候选

这一组逻辑上不属于最终的 hydro + temperature 基线，但技术上还不能“直接删文件”，需要先切掉明确的入口点或功能开关。

### 5.1 `particle.f90`

判断：

- 第二批删除候选

理由：

- 原版只有在检测到 `w2_particle.csv` 且 `FISH_PARTICLE_EXIST` 为真时才运行
- 主程序中存在显式条件调用 `CALL FISH` 和 `call fishoutput`
- 它是鱼/粒子代理行为模拟，不是基础水动力求解

先做什么：

- 删除主程序里的 `FISH_PARTICLE_EXIST` 检查与相关调用
- 再移除 `particle.f90`

### 5.2 `aerate.f90`

判断：

- 第二批删除候选

理由：

- 原版只在 `AERATEC == ON` 且 `oxygen_demand` 为真时启用
- 它不是基础主链
- 但它不只是输出模块
- 它既会通过 `AERATEMASS` 改变 DO 源汇，也会通过 `DZMULT` 乘到 `DZ` 上，影响局部混合

结论：

- 可以从最终精简目标中移除
- 但不能把它简单表述成“与水动力完全无关”

先做什么：

- 删掉 `AERATE`、`AERATEMASS`、`AERATEOUTPUT`、`DEALLOCATE_AERATE` 的调用
- 清理 `HYPOAERATION` 模块依赖
- 再删文件

### 5.3 `Diagenesis*` / `CEMA*` 组

包括：

- `Diagenesis Bubbles Code 01.f90`
- `Diagenesis FFT Layer 01.f90`
- `Diagenesis Input 02.f90`
- `Diagenesis Input Files Read 01.f90`
- `Diagenesis Output 02.f90`
- `Diagenesis Sediment Flux Model 05.f90`
- `Diagenesis Sediment Model 03.f90`

判断：

- 第二批删除候选

理由：

- 它们属于沉积成岩扩展，不属于基础水动力 + 温度基线
- 但原版主程序里直接调用了 `CEMA_W2_Input`
- 原版 `wqconstituents.F90` 里条件调用了 `SedimentFlux`
- 原版还通过 `USE CEMAVars`、`USE CEMASedimentDiagenesis` 建立了模块依赖

结论：

- 逻辑上应删除
- 技术上必须先断开输入、模块 `USE` 和通量调用，再删文件

## 6. 优先级 3：第三批删除候选

这一组确实是水质主链，但必须先处理“原版中隐藏的入口依赖”，否则直接删会误伤温度初始化和派生量输出。

### 6.1 `wqconstituents.F90`

判断：

- 第三批删除候选

理由：

- 它是原版的水质主求解入口
- 主程序中通过 `IF (CONSTITUENTS) CALL wqconstituents` 进入

### 6.2 `water-quality.f90`

判断：

- 第三批删除候选

理由：

- 它包含大量水质速率、派生量、气体交换、pH、藻类、营养盐、BOD 等入口
- 但原版里 `temperature.F90` 会在初始输出路径调用：
  - `TEMPERATURE_RATES`
  - `KINETIC_RATES`
  - `DERIVED_CONSTITUENTS`
  - 条件下还会调用 `PH_CO2`
- 这些入口都定义在 `water-quality.f90`

这意味着：

- `water-quality.f90` 不是零依赖删除件
- 必须先把 `temperature.F90` 对这些入口的依赖处理掉

### 6.3 `gas-transfer.f90`

判断：

- 第三批删除候选

理由：

- 它计算 `REAER`
- 原版调用点位于 `water-quality.f90` 的 `KINETIC_RATES`
- 它不在主水动力主循环中独立承担基础求解职责

结论：

- 应该跟随水质主链一起删除
- 但顺序在 `water-quality.f90` 之后更稳妥

### 6.4 `ReduceReaerAlgae.f90`

判断：

- 第三批删除候选

理由：

- 原版只在 `water-quality.f90` 的 `KINETIC_RATES` 中，通过 `REDUCE_GAS_TRANSFER` 条件使用
- 功能是藻类表层累积对复氧系数的修正
- 不属于基础水动力 + 温度基线

### 6.5 这一批的正确处理顺序

建议顺序：

1. 先去掉 `temperature.F90` 对 `water-quality.f90` 中 ENTRY 的依赖
2. 再切断主程序中的 `CONSTITUENTS -> wqconstituents` 路径
3. 再删除 `wqconstituents.F90`
4. 再删除 `water-quality.f90`
5. 最后删除 `gas-transfer.f90` 和 `ReduceReaerAlgae.f90`

## 7. 优先级 4：延后处理，不属于当前这轮删除

这一组不是基础水动力核，但它们会改变当前支持案例边界或碰到仍保留的物理功能，应该延后。

### 7.1 `withdrawal.f90`

理由：

- 不只是“取水附属件”
- 包含选择性取水温控逻辑
- 原版主程序对 `SELECTIVEINIT` / `SELECTIVEUSGS` 有明确调用

### 7.2 `gate-spill-pipe.f90`

理由：

- 负责闸门、溢洪道、管道结构流量
- 当前 Bonneville 支持案例仍依赖结构物边界

### 7.3 `systdg.f90` / `tdg.f90` / `TDGtarget.f90`

理由：

- 这组主要属于 TDG/结构物运行控制
- 不是水质主反应链
- 但当前支持案例边界仍可能依赖

### 7.4 `macrophyte-aux.f90`

理由：

- 原版并不只是“纯水质植物模块”
- 主程序和 `az.f90` 里有 `MACROPHYTE_FRICTION` 路径
- 启用时会影响摩阻/水动力

结论：

- 除非你明确决定把大型水生植物相关水动力影响也全部拿掉
- 否则不要把它和纯水质文件放在同一批次

## 8. 一句话版排序

按原版源码重新排序后，最合理的删除波次是：

1. `Plunge_Point.f90`、`fishhabitat.f90`、`envir_perf.f90`、`fish-particle.f90`
2. `particle.f90`、`aerate.f90`、全部 `Diagenesis*` / `CEMA*`
3. `wqconstituents.F90`、`water-quality.f90`、`gas-transfer.f90`、`ReduceReaerAlgae.f90`
4. `withdrawal.f90`、`gate-spill-pipe.f90`、`systdg.f90`、`tdg.f90`、`TDGtarget.f90`、`macrophyte-aux.f90`

## 9. 对后续四阶段讨论最重要的提醒

基于原版源码，后续讨论四阶段边界时必须记住三件事：

1. `shading.f90`、`az.f90`、`heat-exchange.f90` 仍是主链，不能误删
2. `water-quality.f90` 虽然属于水质主链，但删除前必须先处理 `temperature.F90` 对其 ENTRY 的依赖
3. `aerate.f90` 是可选功能，但启用时会碰 `DZ`，不能被错误归类为“完全不碰水动力”
