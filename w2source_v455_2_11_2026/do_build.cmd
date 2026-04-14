@echo off
set IFORT_BIN=C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\bin
set PATH=%IFORT_BIN%;%PATH%
cd /d C:\temp_w2_build

echo === STAGE 1: Compile module files ===
"C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\bin\ifx.exe" /nologo /fpp /module:C:\temp_w2_build\ /object:C:\temp_w2_build\ /c /Qm64 w2modules.F90
"C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\bin\ifx.exe" /nologo /fpp /module:C:\temp_w2_build\ /object:C:\temp_w2_build\ /c /Qm64 MetFileRegion.f90
"C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\bin\ifx.exe" /nologo /fpp /module:C:\temp_w2_build\ /object:C:\temp_w2_build\ /c /Qm64 preprocessor_definitions.fpp
echo Stage 1 exit code: %errorlevel%

echo.
echo === STAGE 2: Compile main source files ===
"C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\bin\ifx.exe" /nologo /fpp /module:C:\temp_w2_build\ /object:C:\temp_w2_build\ /c /Qm64 w2_4_win.f90 input.F90 init.F90 init-geom.F90 init-cond.F90 init-u-elws.f90 waterbody.f90 hydroinout.F90 az.f90 transport.f90 layeraddsub.F90 temperature.F90 heat-exchange.f90 density.f90 water-quality.f90 wqconstituents.F90 gas-transfer.f90 balances.F90 shading.f90 withdrawal.f90 gate-spill-pipe.f90 systdg.f90 tdg.f90 update.F90 output.f90 restart.f90 time-varying-data.f90 endsimulation.F90 screen_output_intel.f90 aerate.f90 date.f90 particle.f90 Plunge_Point.f90 outputinitw2tools.F90 outputa2w2tools.F90
echo Stage 2 exit code: %errorlevel%

echo.
echo === STAGE 3: Link ===
"C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\bin\ifx.exe" /nologo /Qm64 C:\temp_w2_build\*.obj /exe:C:\temp_w2_build\w2_v455_ifx.exe
echo Stage 3 exit code: %errorlevel%

echo.
echo Build complete!