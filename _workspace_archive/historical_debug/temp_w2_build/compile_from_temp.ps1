$env:PATH = "C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\bin;" + $env:PATH
Set-Location "C:\temp_w2_build"
$moddir = "C:\temp_w2_build"

$ifxArgs = @(
    "/nologo",
    "/fpp",
    "/module:$moddir\",
    "/object:$moddir\",
    "/Qm64",
    "w2_4_win.f90",
    "w2modules.f90",
    "input.f90",
    "init.f90",
    "init-geom.f90",
    "init-cond.f90",
    "init-u-elws.f90",
    "waterbody.f90",
    "hydroinout.f90",
    "az.f90",
    "transport.f90",
    "layeraddsub.f90",
    "temperature.f90",
    "heat-exchange.f90",
    "density.f90",
    "water-quality.f90",
    "wqconstituents.f90",
    "gas-transfer.f90",
    "balances.f90",
    "shading.f90",
    "withdrawal.f90",
    "gate-spill-pipe.f90",
    "systdg.f90",
    "tdg.f90",
    "update.f90",
    "output.f90",
    "restart.f90",
    "time-varying-data.f90",
    "endsimulation.f90",
    "screen_output_intel.f90",
    "aerate.f90",
    "date.f90",
    "particle.f90",
    "Plunge_Point.f90",
    "preprocessor_definitions.fpp",
    "MetFileRegion.f90",
    "outputinitw2tools.f90",
    "outputa2w2tools.f90",
    "macrophyte-aux.f90"
)

& "C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\bin\ifx.exe" @ifxArgs

if ($LASTEXITCODE -eq 0) {
    Write-Host "BUILD SUCCESSFUL"
} else {
    Write-Host "BUILD FAILED"
}