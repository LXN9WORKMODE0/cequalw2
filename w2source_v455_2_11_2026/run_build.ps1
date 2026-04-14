$proc = Start-Process -FilePath "cmd.exe" -ArgumentList "/c", "C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\do_build.cmd" -NoNewWindow -Wait -PassThru
$stdout = $proc.ExitCode
Write-Host "Exit code: $stdout"