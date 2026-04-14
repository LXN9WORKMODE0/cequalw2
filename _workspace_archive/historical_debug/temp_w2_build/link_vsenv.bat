@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\Common7\Tools\VsDevCmd.bat" -arch=x64
cd /d C:\temp_w2_build
ifx /nologo /Qm64 aerate.obj az.obj balances.obj date.obj density.obj endsimulation.obj gas-transfer.obj gate-spill-pipe.obj heat-exchange.obj hydroinout.obj init-cond.obj init-geom.obj init-u-elws.obj init.obj input.obj layeraddsub.obj MetFileRegion.obj output.obj outputa2w2tools.obj outputinitw2tools.obj particle.obj Plunge_Point.obj preprocessor_definitions.obj restart.obj screen_output_intel.obj shading.obj systdg.obj tdg.obj temperature.obj time-varying-data.obj transport.obj update.obj w2modules.obj w2_4_win.obj water-quality.obj waterbody.obj withdrawal.obj wqconstituents.obj /exe:C:\temp_w2_build\w2_v455_ifx.exe
echo Exit code: %errorlevel%
