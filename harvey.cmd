@echo off
rem Puts the real claude.exe on PATH (npm only ships .cmd wrappers, which
rem Harvey's subprocess calls can't launch on Windows), then runs Harvey.
set "PYTHONIOENCODING=utf-8"
set "PATH=%APPDATA%\npm\node_modules\@anthropic-ai\claude-code\bin;%PATH%"
"%~dp0.venv\Scripts\harvey.exe" %*
