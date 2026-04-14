@echo off
cd /d C:\temp_w2_build
"C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\bin\ifx.exe" /nologo /Qm64 *.obj /exe:C:\temp_w2_build\w2_v455_ifx.exe
echo Exit code: %errorlevel%
