# Install the tested MOSS worker as tts_worker.py before using this supervisor.
# Keeps tts_worker.py running without anyone watching:
#  - starts "tts_worker.py run --loop --config tts_config_moss.json"; when it exits or crashes, starts it again
#    (60 s after a long run; after quick repeated crashes the wait doubles, up to 15 min)
#  - when the worker's heartbeat (E:\gc-audio\worker.heartbeat, written at least every minute) is older than
#    20 min, it is treated as hung: killed (with its model processes) and started again
#  - exit code 9 = another worker already holds the lock -> this supervisor quits (no duplicate workers)
# Log: E:\gc-audio\supervisor.log   (the worker's own log: E:\gc-audio\worker.log)
$ErrorActionPreference = 'Continue'
$root  = 'E:\gc-audio'
$tools = Join-Path $root 'tools'
$py    = Join-Path $root 'venv-moss\Scripts\python.exe'
$beat  = Join-Path $root 'worker.heartbeat'
$slog  = Join-Path $root 'supervisor.log'
$env:HF_HOME = Join-Path $root 'cache\hf'
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'
$env:Path = '<HOME>\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin;' + $env:Path

function Write-Slog([string]$m) {
    $line = '[{0}] supervisor: {1}' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $m
    Add-Content -Path $slog -Value $line -Encoding UTF8      # file first: console output can block (see below)
    Write-Host $line
}

# Turn off QuickEdit for this console window. With QuickEdit on, one mouse click in the window starts a text
# selection and then EVERY program writing to the window (this supervisor and the worker) freezes until a key is
# pressed - the worker would silently stop. (This happened once on 2026-11-19.)
try {
    Add-Type -Namespace GcAudio -Name ConsoleMode -MemberDefinition @'
[DllImport("kernel32.dll")] public static extern IntPtr GetStdHandle(int nStdHandle);
[DllImport("kernel32.dll")] public static extern bool GetConsoleMode(IntPtr h, out uint mode);
[DllImport("kernel32.dll")] public static extern bool SetConsoleMode(IntPtr h, uint mode);
'@
    $hIn = [GcAudio.ConsoleMode]::GetStdHandle(-10)        # STD_INPUT_HANDLE
    $mode = [uint32]0
    if ([GcAudio.ConsoleMode]::GetConsoleMode($hIn, [ref]$mode)) {
        $null = [GcAudio.ConsoleMode]::SetConsoleMode($hIn, (($mode -band (-bnot 0x40)) -bor 0x80))   # -QUICK_EDIT +EXTENDED
    }
} catch { }

$delay = 30
while ($true) {
    $t0 = Get-Date
    Write-Slog 'starting tts_worker.py run --loop --config tts_config_moss.json'
    $p = Start-Process -FilePath $py -ArgumentList 'tts_worker.py', 'run', '--loop', '--config', 'tts_config_moss.json' -WorkingDirectory $tools -NoNewWindow -PassThru
    $null = $p.Handle                     # PowerShell 5.1: needed so ExitCode is available later
    while (-not $p.HasExited) {
        Start-Sleep -Seconds 30
        if (((Get-Date) - $t0).TotalMinutes -gt 20 -and (Test-Path $beat)) {
            $age = ((Get-Date) - (Get-Item $beat).LastWriteTime).TotalMinutes
            if ($age -gt 20) {
                Write-Slog ('no heartbeat for {0:N0} min - the worker looks hung, killing it' -f $age)
                & taskkill.exe /PID $p.Id /T /F | Out-Null
                break
            }
        }
    }
    $p.WaitForExit(60000) | Out-Null
    $code = $p.ExitCode
    if ($code -eq 9) { Write-Slog 'another worker is already running - this supervisor stops'; break }
    $ran = ((Get-Date) - $t0).TotalMinutes
    if ($ran -gt 5) { $delay = 60 } else { $delay = [Math]::Min($delay * 2, 900) }   # quick repeated crashes: back off
    Write-Slog ('worker ended (exit code {0}, ran {1:N0} min) - starting it again in {2} s' -f $code, $ran, $delay)
    Start-Sleep -Seconds $delay
}
