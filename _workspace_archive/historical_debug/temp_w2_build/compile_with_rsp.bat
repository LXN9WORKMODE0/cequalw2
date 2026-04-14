@echo off
setlocal
set PATH=C:\Windows\System32;C:\Windows;C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\bin;C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\VC\Tools\MSVC\14.29.30133\bin\Hostx64\x64
set LIB=C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\lib;C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\VC\Tools\MSVC\14.29.30133\lib\x64;C:\Program Files (x86)\Windows Kits\10\Lib\10.0.19041.0\um\x64;C:\Program Files (x86)\Windows Kits\10\Lib\10.0.19041.0\ucrt\x64
cd /d "C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026"
"C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\bin\ifx.exe" @C:\temp_w2_build\compile_args.txt
echo Exit code: %errorlevel%
endlocal