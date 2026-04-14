@echo off
set "PATH=C:\Windows\System32;C:\Windows;C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\bin;C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\lib"
set "IFX_PATH=C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\bin"
cd /d C:\Users\NING\Desktop\v455\temp_compile

echo Running w2_v455_ifx.exe with Intel paths...
"%IFX_PATH%\ifx.exe" /exe:w2_v455_ifx.exe
echo.
echo If you see this, the program exited normally.