@echo off
rem Runs Harvey's loop with output going to data\harvey-run.log instead of the
rem console. Harvey logs every HTTP request; if a console window isn't being
rem read, its buffer fills and Harvey freezes mid-write. A file never fills.
rem Watch it live with:  Get-Content data\harvey-run.log -Wait -Tail 30
echo Harvey is running. Log: %~dp0data\harvey-run.log  (Ctrl+C to stop)
call "%~dp0harvey.cmd" run >> "%~dp0data\harvey-run.log" 2>&1
