@echo off
setlocal
set "PATH=C:\Windows\System32;C:\Windows;C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\bin"
set "XILINK_PATH=C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\bin\xilink.exe"
set "OBJDIR=C:\Users\NING\Desktop\v455\temp_compile\objdir"
cd /d C:\Users\NING\Desktop\v455\temp_compile

echo Linking with xilink.exe...
"%XILINK_PATH%" /nologo /out:w2_v455_ifx.exe ^
  "%OBJDIR%\MetFileRegion.obj" ^
  "%OBJDIR%\Plunge_Point.obj" ^
  "%OBJDIR%\ReduceReaerAlgae.obj" ^
  "%OBJDIR%\TDGtarget.obj" ^
  "%OBJDIR%\aerate.obj" ^
  "%OBJDIR%\az.obj" ^
  "%OBJDIR%\balances.obj" ^
  "%OBJDIR%\date.obj" ^
  "%OBJDIR%\density.obj" ^
  "%OBJDIR%\endsimulation.obj" ^
  "%OBJDIR%\gas-transfer.obj" ^
  "%OBJDIR%\gate-spill-pipe.obj" ^
  "%OBJDIR%\heat-exchange.obj" ^
  "%OBJDIR%\hydroinout.obj" ^
  "%OBJDIR%\init-cond.obj" ^
  "%OBJDIR%\init-geom.obj" ^
  "%OBJDIR%\init-u-elws.obj" ^
  "%OBJDIR%\init.obj" ^
  "%OBJDIR%\input.obj" ^
  "%OBJDIR%\layeraddsub.obj" ^
  "%OBJDIR%\metfileregion.obj" ^
  "%OBJDIR%\output.obj" ^
  "%OBJDIR%\outputa2w2tools.obj" ^
  "%OBJDIR%\outputinitw2tools.obj" ^
  "%OBJDIR%\preprocessor_definitions.obj" ^
  "%OBJDIR%\restart.obj" ^
  "%OBJDIR%\screen_output_intel.obj" ^
  "%OBJDIR%\shading.obj" ^
  "%OBJDIR%\systdg.obj" ^
  "%OBJDIR%\tdg.obj" ^
  "%OBJDIR%\temperature.obj" ^
  "%OBJDIR%\time-varying-data.obj" ^
  "%OBJDIR%\transport.obj" ^
  "%OBJDIR%\update.obj" ^
  "%OBJDIR%\w2_4_win.obj" ^
  "%OBJDIR%\w2_main.obj" ^
  "%OBJDIR%\w2modules.obj" ^
  "%OBJDIR%\water-quality.obj" ^
  "%OBJDIR%\waterbody.obj" ^
  "%OBJDIR%\withdrawal.obj" ^
  "%OBJDIR%\wqconstituents.obj"

if errorlevel 1 goto error
echo.
echo ========== LINKING SUCCESSFUL ==========
exit /b 0

:error
echo.
echo ========== LINKING FAILED ==========
exit /b 1
endlocal