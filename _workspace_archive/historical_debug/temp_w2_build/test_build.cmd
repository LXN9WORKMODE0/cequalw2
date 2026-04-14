@echo off
set IFORT_BIN=C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\bin
set PATH=%IFORT_BIN%;%PATH%
cd /d C:\temp_w2_build
echo Running simple test...
"C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\bin\ifx.exe" /nologo /fpp /module:C:\temp_w2_build\ /object:C:\temp_w2_build\ /c /Qm64 w2modules.F90
echo Exit code: %errorlevel%