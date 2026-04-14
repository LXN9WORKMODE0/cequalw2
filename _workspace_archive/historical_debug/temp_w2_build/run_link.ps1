$env:PATH = "C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\bin;C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\VC\Tools\MSVC\14.29.30133\bin\Hostx64\x64;C:\Windows\System32;C:\Windows"
$env:LIB = "C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\lib;C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\VC\Tools\MSVC\14.29.30133\lib\x64;C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\VC\Tools\MSVC\14.29.30133\lib\onecore\x64"
$objFiles = Get-ChildItem -Path "C:\temp_w2_build" -Filter "*.obj" | ForEach-Object { $_.FullName }
$processInfo = New-Object System.Diagnostics.ProcessStartInfo
$processInfo.FileName = "C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\bin\ifx.exe"
$processInfo.Arguments = "/nologo /Qm64 " + ($objFiles -join " ") + " /exe:C:\temp_w2_build\w2_v455_ifx.exe"
$processInfo.UseShellExecute = $false
$processInfo.RedirectStandardOutput = $true
$processInfo.RedirectStandardError = $true
$process = New-Object System.Diagnostics.Process
$process.StartInfo = $processInfo
$process.Start() | Out-Null
$stdout = $process.StandardOutput.ReadToEnd()
$stderr = $process.StandardError.ReadToEnd()
$process.WaitForExit()
Write-Host "Exit code: $($process.ExitCode)"
if ($stdout) { Write-Host "STDOUT: $stdout" }
if ($stderr) { Write-Host "STDERR: $stderr" }
