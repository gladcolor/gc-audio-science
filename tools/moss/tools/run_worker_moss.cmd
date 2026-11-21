@rem MOSS-TTS read-aloud worker: keep this window open (closing it stops the worker).
@rem supervise_moss.ps1 starts tts_worker.py with tts_config_moss.json and restarts it if it crashes or hangs.
@call "%~dp0env.cmd"
set HF_HUB_OFFLINE=1
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0supervise_moss.ps1"
pause
