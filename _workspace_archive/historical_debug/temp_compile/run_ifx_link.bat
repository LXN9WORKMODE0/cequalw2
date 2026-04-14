@echo off
cd /d C:\Users\NING\Desktop\v455\temp_compile
set "PATH=C:\Windows\System32;C:\Windows;%VS_DIR%;C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\bin"
set "VS_DIR=C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\VC\Tools\MSVC\14.29.30133\bin\Hostx64\x64"
set "IFX_DIR=C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0"
set "LIB=%IFX_DIR%\lib;%VS_DIR%\lib;C:\Program Files (x86)\Windows Kits\10\Lib\10.0.19041.0\um\x64;C:\Program Files (x86)\Windows Kits\10\Lib\10.0.19041.0\ucrt\x64"

echo Attempting link with ifx (VS link should be in PATH)...
"%IFX_DIR%\bin\ifx.exe" /nologo /Qm64 objdir\input.obj /exe:w2_v455_ifx.exe
echo Exit code: %ERRORLEVEL%