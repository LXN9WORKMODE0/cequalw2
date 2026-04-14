$env:PATH = "C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\bin;" + $env:PATH
$moddir = "C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\W2 model\x64\Release"
$srcdir = "C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026"
$ifx = "C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\bin\ifx.exe"

$proc = Start-Process -FilePath $ifx -ArgumentList "/nologo","/fpp","/module:`"$moddir`"",`
    "/object:`"$moddir`"",`
    "/Qm64",`
    "$srcdir\w2_4_win.f90",`
    "$srcdir\w2modules.f90",`
    "$srcdir\input.f90",`
    "$srcdir\init.f90",`
    "$srcdir\init-geom.f90",`
    "$srcdir\init-cond.f90",`
    "$srcdir\init-u-elws.f90",`
    "$srcdir\waterbody.f90",`
    "$srcdir\hydroinout.f90",`
    "$srcdir\az.f90",`
    "$srcdir\transport.f90",`
    "$srcdir\layeraddsub.f90",`
    "$srcdir\temperature.f90",`
    "$srcdir\heat-exchange.f90",`
    "$srcdir\density.f90",`
    "$srcdir\water-quality.f90",`
    "$srcdir\wqconstituents.f90",`
    "$srcdir\gas-transfer.f90",`
    "$srcdir\balances.f90",`
    "$srcdir\shading.f90",`
    "$srcdir\withdrawal.f90",`
    "$srcdir\gate-spill-pipe.f90",`
    "$srcdir\systdg.f90",`
    "$srcdir\tdg.f90",`
    "$srcdir\update.f90",`
    "$srcdir\output.f90",`
    "$srcdir\restart.f90",`
    "$srcdir\time-varying-data.f90",`
    "$srcdir\endsimulation.f90",`
    "$srcdir\screen_output_intel.f90",`
    "$srcdir\aerate.f90",`
    "$srcdir\date.f90",`
    "$srcdir\particle.f90",`
    "$srcdir\Plunge_Point.f90",`
    "$srcdir\preprocessor_definitions.fpp",`
    "$srcdir\MetFileRegion.f90",`
    "$srcdir\outputinitw2tools.f90",`
    "$srcdir\outputa2w2tools.f90",`
    "$srcdir\macrophyte-aux.f90",`
    "/exe:`"$moddir\w2_v455_ifx.exe`"" -Wait -NoNewWindow -PassThru

Write-Host "Exit code: $($proc.ExitCode)"