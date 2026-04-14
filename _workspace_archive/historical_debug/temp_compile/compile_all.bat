@echo off
setlocal
set PATH=C:\Windows\System32;C:\Windows;C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\bin;C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\VC\Tools\MSVC\14.29.30133\bin\Hostx64\x64
set LIB=C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\lib;C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\VC\Tools\MSVC\14.29.30133\lib\x64;C:\Program Files (x86)\Windows Kits\10\Lib\10.0.19041.0\um\x64;C:\Program Files (x86)\Windows Kits\10\Lib\10.0.19041.0\ucrt\x64
cd /d C:\temp_compile
if not exist moddir mkdir moddir
if not exist objdir mkdir objdir

echo Compiling preprocessor_definitions.fpp...
"C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\bin\ifx.exe" /nologo /fpp /module:moddir /object:objdir\ /c /Qm64 preprocessor_definitions.fpp
if errorlevel 1 goto error

echo Compiling w2modules.f90...
"C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\bin\ifx.exe" /nologo /fpp /module:moddir /object:objdir\ /c /Qm64 w2modules.f90
if errorlevel 1 goto error

echo Compiling MetFileRegion.f90...
"C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\bin\ifx.exe" /nologo /fpp /module:moddir /object:objdir\ /c /Qm64 MetFileRegion.f90
if errorlevel 1 goto error

echo Compiling systdg.f90...
"C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\bin\ifx.exe" /nologo /fpp /module:moddir /object:objdir\ /c /Qm64 systdg.f90
if errorlevel 1 goto error

echo Compiling tdg.f90...
"C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\bin\ifx.exe" /nologo /fpp /module:moddir /object:objdir\ /c /Qm64 tdg.f90
if errorlevel 1 goto error

echo Compiling TDGtarget.f90...
"C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\bin\ifx.exe" /nologo /fpp /module:moddir /object:objdir\ /c /Qm64 TDGtarget.f90
if errorlevel 1 goto error

echo Compiling ReduceReaerAlgae.f90...
"C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\bin\ifx.exe" /nologo /fpp /module:moddir /object:objdir\ /c /Qm64 ReduceReaerAlgae.f90
if errorlevel 1 goto error

echo Compiling w2_4_win.f90...
"C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\bin\ifx.exe" /nologo /fpp /module:moddir /object:objdir\ /c /Qm64 w2_4_win.f90
if errorlevel 1 goto error

echo Compiling input.f90...
"C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\bin\ifx.exe" /nologo /fpp /module:moddir /object:objdir\ /c /Qm64 input.f90
if errorlevel 1 goto error

echo Compiling init.f90...
"C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\bin\ifx.exe" /nologo /fpp /module:moddir /object:objdir\ /c /Qm64 init.f90
if errorlevel 1 goto error

echo Compiling init-geom.f90...
"C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\bin\ifx.exe" /nologo /fpp /module:moddir /object:objdir\ /c /Qm64 init-geom.f90
if errorlevel 1 goto error

echo Compiling init-cond.f90...
"C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\bin\ifx.exe" /nologo /fpp /module:moddir /object:objdir\ /c /Qm64 init-cond.f90
if errorlevel 1 goto error

echo Compiling init-u-elws.f90...
"C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\bin\ifx.exe" /nologo /fpp /module:moddir /object:objdir\ /c /Qm64 init-u-elws.f90
if errorlevel 1 goto error

echo Compiling waterbody.f90...
"C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\bin\ifx.exe" /nologo /fpp /module:moddir /object:objdir\ /c /Qm64 waterbody.f90
if errorlevel 1 goto error

echo Compiling hydroinout.f90...
"C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\bin\ifx.exe" /nologo /fpp /module:moddir /object:objdir\ /c /Qm64 hydroinout.f90
if errorlevel 1 goto error

echo Compiling az.f90...
"C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\bin\ifx.exe" /nologo /fpp /module:moddir /object:objdir\ /c /Qm64 az.f90
if errorlevel 1 goto error

echo Compiling transport.f90...
"C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\bin\ifx.exe" /nologo /fpp /module:moddir /object:objdir\ /c /Qm64 transport.f90
if errorlevel 1 goto error

echo Compiling layeraddsub.f90...
"C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\bin\ifx.exe" /nologo /fpp /module:moddir /object:objdir\ /c /Qm64 layeraddsub.f90
if errorlevel 1 goto error

echo Compiling temperature.f90...
"C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\bin\ifx.exe" /nologo /fpp /module:moddir /object:objdir\ /c /Qm64 temperature.f90
if errorlevel 1 goto error

echo Compiling heat-exchange.f90...
"C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\bin\ifx.exe" /nologo /fpp /module:moddir /object:objdir\ /c /Qm64 heat-exchange.f90
if errorlevel 1 goto error

echo Compiling density.f90...
"C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\bin\ifx.exe" /nologo /fpp /module:moddir /object:objdir\ /c /Qm64 density.f90
if errorlevel 1 goto error

echo Compiling water-quality.f90...
"C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\bin\ifx.exe" /nologo /fpp /module:moddir /object:objdir\ /c /Qm64 water-quality.f90
if errorlevel 1 goto error

echo Compiling wqconstituents.f90...
"C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\bin\ifx.exe" /nologo /fpp /module:moddir /object:objdir\ /c /Qm64 wqconstituents.f90
if errorlevel 1 goto error

echo Compiling gas-transfer.f90...
"C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\bin\ifx.exe" /nologo /fpp /module:moddir /object:objdir\ /c /Qm64 gas-transfer.f90
if errorlevel 1 goto error

echo Compiling balances.f90...
"C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\bin\ifx.exe" /nologo /fpp /module:moddir /object:objdir\ /c /Qm64 balances.f90
if errorlevel 1 goto error

echo Compiling shading.f90...
"C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\bin\ifx.exe" /nologo /fpp /module:moddir /object:objdir\ /c /Qm64 shading.f90
if errorlevel 1 goto error

echo Compiling withdrawal.f90...
"C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\bin\ifx.exe" /nologo /fpp /module:moddir /object:objdir\ /c /Qm64 withdrawal.f90
if errorlevel 1 goto error

echo Compiling gate-spill-pipe.f90...
"C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\bin\ifx.exe" /nologo /fpp /module:moddir /object:objdir\ /c /Qm64 gate-spill-pipe.f90
if errorlevel 1 goto error

echo Compiling update.f90...
"C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\bin\ifx.exe" /nologo /fpp /module:moddir /object:objdir\ /c /Qm64 update.f90
if errorlevel 1 goto error

echo Compiling output.f90...
"C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\bin\ifx.exe" /nologo /fpp /module:moddir /object:objdir\ /c /Qm64 output.f90
if errorlevel 1 goto error

echo Compiling restart.f90...
"C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\bin\ifx.exe" /nologo /fpp /module:moddir /object:objdir\ /c /Qm64 restart.f90
if errorlevel 1 goto error

echo Compiling time-varying-data.f90...
"C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\bin\ifx.exe" /nologo /fpp /module:moddir /object:objdir\ /c /Qm64 time-varying-data.f90
if errorlevel 1 goto error

echo Compiling endsimulation.f90...
"C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\bin\ifx.exe" /nologo /fpp /module:moddir /object:objdir\ /c /Qm64 endsimulation.f90
if errorlevel 1 goto error

echo Compiling screen_output_intel.f90...
"C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\bin\ifx.exe" /nologo /fpp /module:moddir /object:objdir\ /c /Qm64 screen_output_intel.f90
if errorlevel 1 goto error

echo Compiling aerate.f90...
"C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\bin\ifx.exe" /nologo /fpp /module:moddir /object:objdir\ /c /Qm64 aerate.f90
if errorlevel 1 goto error

echo Compiling date.f90...
"C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\bin\ifx.exe" /nologo /fpp /module:moddir /object:objdir\ /c /Qm64 date.f90
if errorlevel 1 goto error

echo Compiling Plunge_Point.f90...
"C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\bin\ifx.exe" /nologo /fpp /module:moddir /object:objdir\ /c /Qm64 Plunge_Point.f90
if errorlevel 1 goto error

echo Compiling outputinitw2tools.f90...
"C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\bin\ifx.exe" /nologo /fpp /module:moddir /object:objdir\ /c /Qm64 outputinitw2tools.f90
if errorlevel 1 goto error

echo Compiling outputa2w2tools.f90...
"C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\bin\ifx.exe" /nologo /fpp /module:moddir /object:objdir\ /c /Qm64 outputa2w2tools.f90
if errorlevel 1 goto error

echo Compiling w2_main.f90...
"C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\bin\ifx.exe" /nologo /fpp /module:moddir /object:objdir\ /c /Qm64 w2_main.f90
if errorlevel 1 goto error


echo.
echo ========== COMPILATION SUCCESSFUL ==========
echo Exit code: %errorlevel%
exit /b 0

:error
echo.
echo ========== COMPILATION FAILED ==========
echo Exit code: %errorlevel%
exit /b 1
endlocal