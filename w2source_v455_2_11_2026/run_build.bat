@echo off
set IFORT_BIN=C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\bin
set PATH=%IFORT_BIN%;%PATH%
set SRC=C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026
set OUT=C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\W2 model\x64\Release

echo Building W2 model...
ifx /nologo /fpp /module:"%OUT%\" /object:"%OUT%\" /list:"%OUT%\build.log" /Qm64 ^
    "%SRC%\w2_4_win.f90" ^
    "%SRC%\w2modules.F90" ^
    "%SRC%\input.F90" ^
    "%SRC%\init.F90" ^
    "%SRC%\init-geom.F90" ^
    "%SRC%\init-cond.F90" ^
    "%SRC%\init-u-elws.f90" ^
    "%SRC%\waterbody.f90" ^
    "%SRC%\hydroinout.F90" ^
    "%SRC%\az.f90" ^
    "%SRC%\transport.f90" ^
    "%SRC%\layeraddsub.F90" ^
    "%SRC%\temperature.F90" ^
    "%SRC%\heat-exchange.f90" ^
    "%SRC%\density.f90" ^
    "%SRC%\water-quality.f90" ^
    "%SRC%\wqconstituents.F90" ^
    "%SRC%\gas-transfer.f90" ^
    "%SRC%\balances.F90" ^
    "%SRC%\shading.f90" ^
    "%SRC%\withdrawal.f90" ^
    "%SRC%\gate-spill-pipe.f90" ^
    "%SRC%\systdg.f90" ^
    "%SRC%\tdg.f90" ^
    "%SRC%\update.F90" ^
    "%SRC%\output.f90" ^
    "%SRC%\restart.f90" ^
    "%SRC%\time-varying-data.f90" ^
    "%SRC%\endsimulation.F90" ^
    "%SRC%\screen_output_intel.f90" ^
    "%SRC%\aerate.f90" ^
    "%SRC%\date.f90" ^
    "%SRC%\envir_perf.f90" ^
    "%SRC%\particle.f90" ^
    "%SRC%\Plunge_Point.f90" ^
    "%SRC%\preprocessor_definitions.fpp" ^
    "%SRC%\MetFileRegion.f90" ^
    "%SRC%\outputinitw2tools.F90" ^
    "%SRC%\outputa2w2tools.F90" ^
    "%SRC%\macrophyte-aux.f90" ^
    /exe:"%OUT%\w2_v455_ifx.exe"

if %errorlevel% equ 0 (
    echo.
    echo BUILD SUCCESSFUL
    echo Output: %OUT%\w2_v455_ifx.exe
) else (
    echo.
    echo BUILD FAILED
    echo Check %OUT%\build.log for errors
)
pause