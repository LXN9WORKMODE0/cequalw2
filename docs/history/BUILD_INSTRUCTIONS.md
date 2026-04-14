# CE-QUAL-W2 v4.5.5 - CEMA模块移除说明

## 修改概述

已从项目中完全移除CEMA (Sediment Diagenesis Model) 沉积物成岩模型模块。

## 删除的文件

| 文件 | 描述 |
|------|------|
| `Diagenesis Sediment Model 03.f90` | 床层固结模型 |
| `Diagenesis Sediment Flux Model 05.f90` | 沉积物通量模型 |
| `Diagenesis FFT Layer 01.f90` | FFT层管理 |
| `Diagenesis Input 02.f90` | 输入参数读取 |
| `Diagenesis Input Files Read 01.f90` | 床层数据读取 |
| `Diagenesis Output 02.f90` | 输出模块 |
| `Diagenesis Bubbles Code 01.f90` | 气泡模型 |
| `density - Copy.f90` | 备份文件 |
| `tdg - Copy.f90` | 备份文件 |

## 修改的源文件

| 文件 | 修改内容 |
|------|----------|
| `w2modules.F90` | 删除CEMAVars模块 (~120行) |
| `w2_4_win.f90` | 删除CEMA初始化和调用 (~20行) |
| `wqconstituents.F90` | 删除CEMA USE语句和调用 |
| `input.F90` | 删除SED_DIAG参数读取 |
| `balances.F90` | 删除CEMA相关代码 |
| `endsimulation.F90` | 删除CEMA USE和清理调用 |
| `init-cond.F90` | 删除4处CEMA条件块 |
| `init.F90` | 删除CEMA初始化调用 |
| `outputa2w2tools.F90` | 删除CEMA输出调用 |
| `outputinitw2tools.F90` | 删除CEMA USE和条件输出 |
| `update.F90` | 删除CEMA变量使用 |
| `restart.f90` | 删除CEMA相关重启代码 |
| `water-quality.f90` | 删除多处CEMA相关代码 |

## 编译测试

### 方法1: 使用Visual Studio

1. 打开 `W2 model\W2 model_PAR.sln`
2. 选择配置: `Release|x64`
3. Build > Build Solution (Ctrl+Shift+B)

### 方法2: 使用Intel Fortran命令行

```batch
cd w2source_v455_2_11_2026
ifx /fpp /module:obj\ /object:obj\ /list:build.log ^
    w2_4_win.f90 w2modules.F90 input.F90 init.F90 ^
    init-geom.F90 init-cond.F90 init-u-elws.f90 ^
    waterbody.f90 hydroinout.F90 az.f90 transport.f90 ^
    layeraddsub.F90 temperature.F90 heat-exchange.f90 ^
    density.f90 water-quality.f90 wqconstituents.F90 ^
    gas-transfer.f90 balances.F90 shading.f90 ^
    withdrawal.f90 gate-spill-pipe.f90 systdg.f90 tdg.f90 ^
    update.F90 output.f90 restart.f90 time-varying-data.f90 ^
    endsimulation.F90 screen_output_intel.f90 aerate.f90 ^
    date.f90 envir_perf.f90 particle.f90 Plunge_Point.f90 ^
    preprocessor_definitions.fpp MetFileRegion.f90 ^
    outputinitw2tools.F90 outputa2w2tools.F90 ^
    macrophyte-aux.f90 ^
    /exe:obj\w2_v455_ifx.exe
```

### 方法3: 使用编译脚本

双击运行 `build_test.bat`

## 预估删除代码量

- 删除文件: ~5000行
- 删除注释代码: ~200行
- 净删除: ~5200行

## 注意事项

1. 编译前请确保Intel Fortran环境已正确配置
2. 编译成功后，原有的CEMA相关配置文件(W2_diagenesis.npt)不再需要
3. 模型控制文件中的SED_DIAG参数已无效

## 验证编译成功

编译成功后应看到:
```
Build succeeded.
Output: W2 model\x64\Release\w2_v455_ifx.exe
```
