@echo off
setlocal

set "ROOT=%~dp0"
set "BUILD_SCRIPT=%ROOT%build_reduced_gui.bat"
set "BUILD_DIR=%ROOT%build_gui"
set "DIST_DIR=%ROOT%dist\ReducedGUI"
set "APP_DIR=%DIST_DIR%\app"
set "CASE_ROOT=%DIST_DIR%\cases"
set "CASE_INPUTS_DIR=%CASE_ROOT%\minimal_case_inputs"
set "CASE_VERIFIED_DIR=%CASE_ROOT%\minimal_case_verified"
set "DOC_DIR=%DIST_DIR%\docs"
set "ZIP_PATH=%ROOT%dist\ReducedGUI.zip"
set "CASE_INPUTS_SOURCE=%ROOT%packaging\cases\minimal_case_inputs"
set "CASE_VERIFIED_SOURCE=%ROOT%packaging\cases\minimal_case_verified"

call "%BUILD_SCRIPT%"
if errorlevel 1 exit /b 1

if not exist "%CASE_INPUTS_SOURCE%\w2_con.csv" (
    echo PACKAGE FAILED
    echo Missing case source: %CASE_INPUTS_SOURCE%
    exit /b 1
)

if not exist "%CASE_VERIFIED_SOURCE%\w2_con.csv" (
    echo PACKAGE FAILED
    echo Missing case source: %CASE_VERIFIED_SOURCE%
    exit /b 1
)

if exist "%DIST_DIR%" rmdir /s /q "%DIST_DIR%"
if exist "%ZIP_PATH%" del /q "%ZIP_PATH%"

mkdir "%APP_DIR%"
mkdir "%CASE_INPUTS_DIR%"
mkdir "%CASE_VERIFIED_DIR%"
mkdir "%DOC_DIR%"

copy "%BUILD_DIR%\w2_v455_reduced_gui.exe" "%APP_DIR%\" >nul
xcopy "%CASE_INPUTS_SOURCE%\*" "%CASE_INPUTS_DIR%\" /E /I /Y >nul
xcopy "%CASE_VERIFIED_SOURCE%\*" "%CASE_VERIFIED_DIR%\" /E /I /Y >nul
copy "%ROOT%packaging\README.txt" "%DOC_DIR%\README.txt" >nul
copy "%ROOT%packaging\PREREQUISITES.txt" "%DOC_DIR%\PREREQUISITES.txt" >nul
copy "%ROOT%packaging\SUPPORTED_CASES.txt" "%DOC_DIR%\SUPPORTED_CASES.txt" >nul

powershell -NoProfile -Command "$ErrorActionPreference='Stop'; $attempt = 0; while ($true) { try { Start-Sleep -Milliseconds 500; Compress-Archive -Path '%DIST_DIR%\*' -DestinationPath '%ZIP_PATH%' -Force; break } catch { $attempt++; if ($attempt -ge 5) { throw }; Start-Sleep -Seconds 1 } }"
if errorlevel 1 (
    echo PACKAGE FAILED
    exit /b 1
)

echo PACKAGE SUCCESSFUL
echo Output: %ZIP_PATH%
endlocal
exit /b 0
