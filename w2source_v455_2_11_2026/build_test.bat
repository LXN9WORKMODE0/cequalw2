@echo off
REM ============================================================================
REM W2 Model Build Script - CEMA Module Removed Version
REM ============================================================================
REM This script compiles the CE-QUAL-W2 model without the CEMA sediment diagenesis module
REM
REM Requirements: Intel Fortran oneAPI (ifx) installed
REM ============================================================================

setlocal

REM --- Intel Fortran Path Configuration ---
REM Edit this path if your Intel Fortran installation is different
set IFORT_BIN=C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\bin
set PATH=%IFORT_BIN%;%PATH%

REM --- Configuration ---
set SOURCE_DIR=%~dp0
set BUILD_DIR=%~dp0W2 model
set OUTPUT_DIR=%BUILD_DIR%\x64\Release
set BUILD_LOG=%OUTPUT_DIR%\build.log

REM --- Check if Intel Fortran is available ---
where ifx >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Intel Fortran (ifx) not found in PATH
    echo Expected location: %IFORT_BIN%
    echo.
    echo Please verify your Intel oneAPI installation path and update this script
    exit /b 1
)

echo ============================================================================
echo W2 Model Build - CEMA Module Removed
echo ============================================================================
echo Using Intel Fortran from: %IFORT_BIN%
echo.

REM --- Create build directory if needed ---
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"

REM --- Clean old object files ---
echo Cleaning old build files...
if exist "%OUTPUT_DIR%\*.obj" del /q "%OUTPUT_DIR%\*.obj"
if exist "%OUTPUT_DIR%\*.mod" del /q "%OUTPUT_DIR%\*.mod"
if exist "%OUTPUT_DIR%\*.exe" del /q "%OUTPUT_DIR%\*.exe"

REM --- Get list of source files ---
echo Gathering source files...
cd /d "%SOURCE_DIR%"

REM Files to compile (excluding Diagenesis files and unused modules)
set SOURCES=^
    w2_4_win.f90 ^
    w2modules.F90 ^
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
    water-quality.f90 ^
    wqconstituents.F90 ^
    gas-transfer.f90 ^
    balances.F90 ^
    shading.f90 ^
    withdrawal.f90 ^
    gate-spill-pipe.f90 ^
    systdg.f90 ^
    tdg.f90 ^
    update.F90 ^
    output.f90 ^
    restart.f90 ^
    time-varying-data.f90 ^
    endsimulation.F90 ^
    screen_output_intel.f90 ^
    aerate.f90 ^
    date.f90 ^
    envir_perf.f90 ^
    waterbody.f90 ^
    particle.f90 ^
    Plunge_Point.f90 ^
    preprocessor_definitions.fpp ^
    MetFileRegion.f90 ^
    outputinitw2tools.F90 ^
    outputa2w2tools.F90 ^
    macrophyte-aux.f90

REM --- Compile ---
echo.
echo Compiling...
echo.

ifx /nologo /fpp /module:"%OUTPUT_DIR%\" /object:"%OUTPUT_DIR%\" /list:"%BUILD_LOG%" ^
    %SOURCES% ^
    /exe:"%OUTPUT_DIR%\w2_v455_ifx.exe" ^
    /Qm64 ^
    2>>"%BUILD_LOG%"

if %errorlevel% equ 0 (
    echo.
    echo ============================================================================
    echo BUILD SUCCESSFUL
    echo ============================================================================
    echo Output: %OUTPUT_DIR%\w2_v455_ifx.exe
    echo Log:    %BUILD_LOG%
    echo ============================================================================
) else (
    echo.
    echo ============================================================================
    echo BUILD FAILED
    echo ============================================================================
    echo Check %BUILD_LOG% for errors
    echo.
    echo Last 20 lines of build log:
    echo.
    powershell -Command "Get-Content '%BUILD_LOG%' -Tail 20"
    exit /b 1
)

endlocal
