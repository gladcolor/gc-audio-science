@rem Daily operation: keep this window open (closing it stops the worker).
@rem supervise.ps1 starts tts_worker.py and starts it again by itself if it crashes or hangs.
@call "%~dp0env.cmd"
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0supervise.ps1"
pause
