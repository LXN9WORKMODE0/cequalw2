@echo off
cd /d C:\Users\NING\Desktop\v455\temp_compile
"C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\bin\ifx.exe" /nologo /fpp /module:moddir /object:objdir\ /c /Qm64 input.f90
if errorlevel 1 (
    echo Compilation failed
) else (
    echo Compilation succeeded
)
pause
