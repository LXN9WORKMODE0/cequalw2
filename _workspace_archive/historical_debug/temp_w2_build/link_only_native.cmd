@echo off
setlocal
cd /d C:\temp_w2_build
set IFORT_BIN=C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\bin
set PATH=%IFORT_BIN%;%PATH%
"C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\bin\ifx.exe" /nologo /Qm64 w2modules.obj MetFileRegion.obj preprocessor_definitions.obj w2_4_win.obj input.obj init.obj init-geom.obj init-cond.obj init-u-elws.obj waterbody.obj hydroinout.obj az.obj transport.obj layeraddsub.obj temperature.obj heat-exchange.obj density.obj water-quality.obj wqconstituents.obj gas-transfer.obj balances.obj shading.obj withdrawal.obj gate-spill-pipe.obj systdg.obj tdg.obj update.obj output.obj restart.obj time-varying-data.obj endsimulation.obj screen_output_intel.obj aerate.obj date.obj particle.obj Plunge_Point.obj outputinitw2tools.obj outputa2w2tools.obj /exe:C:\temp_w2_build\w2_v455_ifx.exe
echo Exit code: %errorlevel%
endlocal
