@echo off
echo ========================================
echo CE-QUAL-W2 v4.5.5 Rebuild Script
echo ========================================
echo.

cd /d C:\Users\NING\Desktop\v455\temp_compile

echo [Step 1] Compiling input.f90...
"C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\bin\ifx.exe" /nologo /fpp /module:moddir /object:objdir\ /c /Qm64 /define:NO_ZOOPLANKTONC /define:NO_MACROPHYTEC /define:NO_BIOENERGETICS input.f90
if errorlevel 1 (
    echo Compile FAILED!
    pause
    exit /b 1
)
echo Compile successful!

echo.
echo [Step 2] Linking...
call link.bat
if errorlevel 1 (
    echo Link FAILED!
    pause
    exit /b 1
)
echo Link successful!

echo.
echo ========================================
echo Build complete! Run w2_v455_ifx.exe to test.
echo ========================================
pause
