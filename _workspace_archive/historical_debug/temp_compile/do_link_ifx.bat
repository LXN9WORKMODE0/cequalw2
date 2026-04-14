@echo off
set "PATH=C:\Windows\System32;C:\Windows;C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\VC\Tools\MSVC\14.29.30133\bin\Hostx64\x64;C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\bin"
set "IFX_PATH=C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\bin"
set "IFX_LIB=C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\lib"
set "LIB=%IFX_LIB%;C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\VC\Tools\MSVC\14.29.30133\lib\x64;C:\Program Files (x86)\Windows Kits\10\Lib\10.0.19041.0\um\x64;C:\Program Files (x86)\Windows Kits\10\Lib\10.0.19041.0\ucrt\x64"

cd /d C:\Users\NING\Desktop\v455\temp_compile

echo Linking with ifx (VS link in PATH)...
"%IFX_PATH%\ifx.exe" /nologo /Qm64 ^
  objdir\MetFileRegion.obj ^
  objdir\Plunge_Point.obj ^
  objdir\ReduceReaerAlgae.obj ^
  objdir\TDGtarget.obj ^
  objdir\aerate.obj ^
  objdir\az.obj ^
  objdir\balances.obj ^
  objdir\date.obj ^
  objdir\density.obj ^
  objdir\endsimulation.obj ^
  objdir\gas-transfer.obj ^
  objdir\gate-spill-pipe.obj ^
  objdir\heat-exchange.obj ^
  objdir\hydroinout.obj ^
  objdir\init-cond.obj ^
  objdir\init-geom.obj ^
  objdir\init-u-elws.obj ^
  objdir\init.obj ^
  objdir\input.obj ^
  objdir\layeraddsub.obj ^
  objdir\metfileregion.obj ^
  objdir\output.obj ^
  objdir\outputa2w2tools.obj ^
  objdir\outputinitw2tools.obj ^
  objdir\preprocessor_definitions.obj ^
  objdir\restart.obj ^
  objdir\screen_output_intel.obj ^
  objdir\shading.obj ^
  objdir\systdg.obj ^
  objdir\tdg.obj ^
  objdir\temperature.obj ^
  objdir\time-varying-data.obj ^
  objdir\transport.obj ^
  objdir\update.obj ^
  objdir\w2_4_win.obj ^
  objdir\w2_main.obj ^
  objdir\w2modules.obj ^
  objdir\water-quality.obj ^
  objdir\waterbody.obj ^
  objdir\withdrawal.obj ^
  objdir\wqconstituents.obj ^
  /exe:w2_v455_ifx.exe
echo Link exit code: %ERRORLEVEL%