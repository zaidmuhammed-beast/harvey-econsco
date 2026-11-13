@echo off
rem Puts the real claude.exe on PATH (npm only ships .cmd wrappers, which
rem Harvey's subprocess calls can't launch on Windows), then runs Harvey.
set "PYTHONIOENCODING=utf-8"
rem Harvey's own claude calls must never start a self-update: interrupted
rem updates have left a broken claude.exe that froze Harvey.
set "DISABLE_AUTOUPDATER=1"
set "PATH=%APPDATA%\npm\node_modules\@anthropic-ai\claude-code\bin;%PATH%"
"%~dp0.venv\Scripts\harvey.exe" %*
