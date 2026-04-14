# Run link using VS Developer Command Prompt environment
$vsDevCmd = "C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\Common7\Tools\VsDevCmd.bat"
$buildDir = "C:\temp_w2_build"
$output = "C:\temp_w2_build\w2_v455_ifx.exe"

# Get all object files
$objFiles = (Get-ChildItem -Path $buildDir -Filter "*.obj").Name -join " "

# Create a temporary batch file that sets up VS env and runs ifx
$tempBat = @"
@echo off
call "$vsDevCmd" -arch=x64
cd /d $buildDir
ifx /nologo /Qm64 $objFiles /exe:$output
echo Exit code: %errorlevel%
"@

$tempBat | Out-File -FilePath "$buildDir\link_vsenv.bat" -Encoding ASCII

# Run the batch file
$processInfo = New-Object System.Diagnostics.ProcessStartInfo
$processInfo.FileName = "cmd.exe"
$processInfo.Arguments = "/C `"$buildDir\link_vsenv.bat`""
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
