@echo off
setlocal
set PATH=C:\Windows\System32;C:\Windows;C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\bin;C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\VC\Tools\MSVC\14.29.30133\bin\Hostx64\x64
set LIB=C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\lib;C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\VC\Tools\MSVC\14.29.30133\lib\x64;C:\Program Files (x86)\Windows Kits\10\Lib\10.0.19041.0\um\x64;C:\Program Files (x86)\Windows Kits\10\Lib\10.0.19041.0\ucrt\x64
pushd "C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026"
"C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\bin\ifx.exe" /nologo /fpp /module:W2~1 /object:W2~1 /Qm64 w2_4_win.f90 w2modules.F90 input.F90 init.F90 init-geom.F90 init-cond.F90 init-u-elws.f90 waterbody.f90 hydroinout.F90 az.f90 transport.f90 layeraddsub.F90 temperature.F90 heat-exchange.f90 density.f90 water-quality.f90 wqconstituents.F90 gas-transfer.f90 balances.F90 shading.f90 withdrawal.f90 gate-spill-pipe.f90 systdg.f90 tdg.f90 update.F90 output.f90 restart.f90 time-varying-data.f90 endsimulation.F90 screen_output_intel.f90 aerate.f90 date.f90 particle.f90 Plunge_Point.f90 preprocessor_definitions.fpp MetFileRegion.f90 outputinitw2tools.F90 outputa2w2tools.F90 /exe:W2~1/w2_v455_ifx.exe
echo Exit code: %errorlevel%
popd
endlocal