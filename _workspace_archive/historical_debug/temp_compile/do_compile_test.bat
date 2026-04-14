@echo off
set "PATH=C:\Windows\System32;C:\Windows;C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\bin"
set "VS_DIR=C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\VC\Tools\MSVC\14.29.30133\bin\Hostx64\x64"
cd /d C:\Users\NING\Desktop\v455\temp_compile

echo Compiling test program...
"IFX_PATH\bin\ifx.exe" /nologo /Qm64 test.f90 /exe:test_simple.exe
echo Compile exit code: %ERRORLEVEL%