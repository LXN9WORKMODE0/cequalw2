@echo off
setlocal

set "IFX_BIN=C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\bin"
set "IFX_LIB=C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\lib"
set "VS_BIN=C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\VC\Tools\MSVC\14.29.30133\bin\Hostx64\x64"
set "MSVC_LIB=C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\VC\Tools\MSVC\14.29.30133\lib\x64"
set "UM_LIB=C:\Program Files (x86)\Windows Kits\10\Lib\10.0.19041.0\um\x64"
set "UCRT_LIB=C:\Program Files (x86)\Windows Kits\10\Lib\10.0.19041.0\ucrt\x64"
set "SRC_DIR=%~dp0"
set "BUILD_DIR=%~dp0build_console"
set "MOD_DIR=%BUILD_DIR%\moddir"
set "OBJ_DIR=%BUILD_DIR%\objdir"
set "BUILD_LOG=%BUILD_DIR%\build.log"
set "EXE_PATH=%BUILD_DIR%\w2_v455_console.exe"

set "PATH=C:\Windows\System32;C:\Windows;%IFX_BIN%;%VS_BIN%;%PATH%"
set "LIB=%IFX_LIB%;%MSVC_LIB%;%UM_LIB%;%UCRT_LIB%;%LIB%"

where ifx >nul 2>&1
if errorlevel 1 goto no_ifx

if not exist "%BUILD_DIR%" mkdir "%BUILD_DIR%"
if not exist "%MOD_DIR%" mkdir "%MOD_DIR%"
if not exist "%OBJ_DIR%" mkdir "%OBJ_DIR%"

if exist "%MOD_DIR%\*.mod" del /q "%MOD_DIR%\*.mod"
if exist "%OBJ_DIR%\*.obj" del /q "%OBJ_DIR%\*.obj"
if exist "%EXE_PATH%" del /q "%EXE_PATH%"
if exist "%BUILD_LOG%" del /q "%BUILD_LOG%"

cd /d "%SRC_DIR%"

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
    w2_main.f90 ^
    /exe:"%EXE_PATH%" > "%BUILD_LOG%" 2>&1

if %errorlevel% equ 0 (
    echo BUILD SUCCESSFUL
    echo Output: %EXE_PATH%
) else (
    echo BUILD FAILED
    if exist "%BUILD_LOG%" (
        powershell -Command "Get-Content '%BUILD_LOG%' -Tail 40"
    )
    exit /b 1
)

endlocal
exit /b 0

:no_ifx
echo ERROR: Intel Fortran (ifx) not found in PATH
echo Expected location: %IFX_BIN%
endlocal
exit /b 1
