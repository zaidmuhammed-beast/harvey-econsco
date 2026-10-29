@echo off
rem Starts Harvey's loop and the dashboard in their own minimized windows.
rem Called at Windows login from the Startup folder; safe to run by hand too.
cd /d "%~dp0"
start "Harvey" /min "%~dp0harvey-run.cmd"
start "Harvey dashboard" /min "%~dp0harvey-dashboard.cmd"
