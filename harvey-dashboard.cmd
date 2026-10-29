@echo off
rem Runs the dashboard with output going to data\harvey-dashboard.log, so a
rem console that isn't being read can never freeze it (see harvey-run.cmd).
echo Harvey dashboard: http://localhost:5555  (Ctrl+C to stop)
call "%~dp0harvey.cmd" dashboard >> "%~dp0data\harvey-dashboard.log" 2>&1
