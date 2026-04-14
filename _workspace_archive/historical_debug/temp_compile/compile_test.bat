@echo off
cd /d C:\Users\NING\Desktop\v455\temp_compile
"C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\bin\ifx.exe" /nologo /Qm64 test_read.f90 -o test_read.exe
if errorlevel 1 goto error
test_read.exe
exit /b 0
:error
echo Compilation failed
exit /b 1