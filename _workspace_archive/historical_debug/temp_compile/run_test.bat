@echo off
cd /d C:\Users\NING\Desktop\v455\temp_compile
echo Running test...
.\w2_v455_ifx.exe > run_out.txt 2>&1
echo Exit code: %ERRORLEVEL% >> run_out.txt