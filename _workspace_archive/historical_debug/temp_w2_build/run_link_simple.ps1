$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = "C:\temp_w2_build\do_link.bat"
$psi.UseShellExecute = $false
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
$psi.CreateNoWindow = $true
$psi.WorkingDirectory = "C:\temp_w2_build"
$proc = [System.Diagnostics.Process]::Start($psi)
$proc.WaitForExit()
$stdout = $proc.StandardOutput.ReadToEnd()
$stderr = $proc.StandardError.ReadToEnd()
Write-Host "Exit: $($proc.ExitCode)"
Write-Host "STDOUT: $stdout"
Write-Host "STDERR: $stderr"
