@echo off
setlocal

set "IFX_BIN=C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\bin"
set "IFX_LIB=C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\lib"
set "VS_BIN=C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\VC\Tools\MSVC\14.29.30133\bin\Hostx64\x64"
set "MSVC_LIB=C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\VC\Tools\MSVC\14.29.30133\lib\x64"
set "UM_LIB=C:\Program Files (x86)\Windows Kits\10\Lib\10.0.19041.0\um\x64"
set "UCRT_LIB=C:\Program Files (x86)\Windows Kits\10\Lib\10.0.19041.0\ucrt\x64"
set "SDK_INCLUDE=C:\Program Files (x86)\Windows Kits\10\Include\10.0.19041.0"
set "RC_BIN=C:\Program Files (x86)\Windows Kits\10\bin\10.0.19041.0\x64\rc.exe"

set "SRC_DIR=%~dp0"
set "PROJ_DIR=%~dp0W2_model"
set "BUILD_DIR=%~dp0build_gui"
set "MOD_DIR=%BUILD_DIR%\moddir"
set "OBJ_DIR=%BUILD_DIR%\objdir"
set "BUILD_LOG=%BUILD_DIR%\build.log"
set "EXE_PATH=%BUILD_DIR%\w2_v455_reduced_gui.exe"
set "RES_PATH=%OBJ_DIR%\w2.res"

set "PATH=C:\Windows\System32;C:\Windows;%IFX_BIN%;%VS_BIN%;%PATH%"
set "LIB=%IFX_LIB%;%MSVC_LIB%;%UM_LIB%;%UCRT_LIB%;%LIB%"
set "INCLUDE=%SDK_INCLUDE%\um;%SDK_INCLUDE%\shared;%SDK_INCLUDE%\ucrt;%INCLUDE%"

if not exist "%IFX_BIN%\ifx.exe" goto no_ifx
if not exist "%RC_BIN%" goto no_rc

if not exist "%BUILD_DIR%" mkdir "%BUILD_DIR%"
if not exist "%MOD_DIR%" mkdir "%MOD_DIR%"
if not exist "%OBJ_DIR%" mkdir "%OBJ_DIR%"

if exist "%MOD_DIR%\*.mod" del /q "%MOD_DIR%\*.mod"
if exist "%OBJ_DIR%\*.obj" del /q "%OBJ_DIR%\*.obj"
if exist "%RES_PATH%" del /q "%RES_PATH%"
if exist "%EXE_PATH%" del /q "%EXE_PATH%"
if exist "%BUILD_LOG%" del /q "%BUILD_LOG%"

cd /d "%SRC_DIR%"

powershell -Command "$env:INCLUDE='%SDK_INCLUDE%\um;%SDK_INCLUDE%\shared;%SDK_INCLUDE%\ucrt;' + $env:INCLUDE; & '%RC_BIN%' /nologo /r /i '%SRC_DIR%' /i '%PROJ_DIR%' '/fo%RES_PATH%' '%SRC_DIR%w2.rc'" > "%BUILD_LOG%" 2>&1
if errorlevel 1 goto build_failed

ifx /nologo /fpp /module:"%MOD_DIR%\\" /object:"%OBJ_DIR%\\" /Qm64 ^
    preprocessor_definitions.fpp ^
    w2modules.F90 ^
    MetFileRegion.f90 ^
    input.F90 ^
    init.F90 ^
    init-geom.F90 ^
    init-cond.F90 ^
    init-u-elws.f90 ^
    waterbody.f90 ^
    hydroinout.F90 ^
    az.f90 ^
    transport.f90 ^
    layeraddsub.F90 ^
    temperature.F90 ^
    heat-exchange.f90 ^
    density.f90 ^
    balances.F90 ^
    shading.f90 ^
    withdrawal.f90 ^
    gate-spill-pipe.f90 ^
    update.F90 ^
    output.f90 ^
    restart.f90 ^
    time-varying-data.f90 ^
    endsimulation.F90 ^
    date.f90 ^
    outputinitw2tools.F90 ^
    outputa2w2tools.F90 ^
    screen_output_intel.f90 ^
    w2_4_win.f90 ^
    "%RES_PATH%" ^
    /exe:"%EXE_PATH%" /link /SUBSYSTEM:WINDOWS >> "%BUILD_LOG%" 2>&1

if errorlevel 1 goto build_failed

echo BUILD SUCCESSFUL
echo Output: %EXE_PATH%
endlocal
exit /b 0

:build_failed
echo BUILD FAILED
if exist "%BUILD_LOG%" powershell -Command "Get-Content '%BUILD_LOG%' -Tail 60"
endlocal
exit /b 1

:no_ifx
echo ERROR: Intel Fortran (ifx) not found at %IFX_BIN%
endlocal
exit /b 1

:no_rc
echo ERROR: rc.exe not found at %RC_BIN%
endlocal
exit /b 1
