@echo off
cd /d C:\Users\NING\Desktop\v455\temp_compile
"C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\bin\ifx.exe" /nologo /fpp /module:moddir /object:objdir /c input.f90
if errorlevel 1 goto error
echo input.f90 compiled successfully
exit /b 0
:error
echo Compilation failed
exit /b 1