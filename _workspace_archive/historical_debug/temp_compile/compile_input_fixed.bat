@echo off
setlocal
set PATH=C:\Windows\System32;C:\Windows;C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\bin;C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\VC\Tools\MSVC\14.29.30133\bin\Hostx64\x64
set LIB=C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\lib;C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\VC\Tools\MSVC\14.29.30133\lib\x64;C:\Program Files (x86)\Windows Kits\10\Lib\10.0.19041.0\um\x64;C:\Program Files (x86)\Windows Kits\10\Lib\10.0.19041.0\ucrt\x64
cd /d C:\Users\NING\Desktop\v455\temp_compile
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

echo Compiling input.f90 with NO_ZOOPLANKTONC flag...
"C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\bin\ifx.exe" /nologo /fpp /module:moddir /object:objdir\ /c /Qm64 /define:NO_ZOOPLANKTONC /define:NO_MACROPHYTEC /define:NO_BIOENERGETICS input.f90
if errorlevel 1 goto error

echo input.f90 compiled successfully
exit /b 0

:error
echo Compilation failed
exit /b 1
endlocal
