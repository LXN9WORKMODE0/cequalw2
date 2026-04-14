@echo off
cd /d C:\Users\NING\Desktop\v455\temp_compile
"C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\bin\ifx.exe" /nologo /fpp /module:moddir /object:objdir\ /c /Qm64 /define:NO_ZOOPLANKTONC /define:NO_MACROPHYTEC /define:NO_BIOENERGETICS input.f90
echo Exit code: %ERRORLEVEL%
