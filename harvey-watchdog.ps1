# Harvey watchdog: restarts Harvey's loop (and the dashboard) if they stop.
#
# Run every 10 minutes by the "Harvey Watchdog" scheduled task. Harvey writes
# to data\harvey-run.log at least every heartbeat (15 min), so a log that has
# been silent for $StaleMinutes means the loop has died or stalled (e.g. a
# timer that never fired after the PC slept). Either way: restart it.
#
# Actions are recorded in data\watchdog.log.

param([int]$StaleMinutes = 40)

$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$log = Join-Path $root 'data\harvey-run.log'
$wdLog = Join-Path $root 'data\watchdog.log'

function Note($msg) {
    try { Add-Content -Path $wdLog -Value ("{0:yyyy-MM-dd HH:mm:ss} {1}" -f (Get-Date), $msg) -Encoding utf8 } catch {}
}

function Get-HarveyProcs($mode) {
    Get-CimInstance Win32_Process -Filter "Name='harvey.exe'" |
        Where-Object { $_.CommandLine -match ('\.venv\\Scripts\\harvey\.exe"\s+' + $mode) }
}

function Stop-Tree($proc) {
    $ids = @($proc.ProcessId); $queue = @($proc.ProcessId)
    while ($queue.Count) {
        $n = $queue[0]; $queue = @($queue | Select-Object -Skip 1)
        Get-CimInstance Win32_Process -Filter "ParentProcessId=$n" | ForEach-Object { $ids += $_.ProcessId; $queue += $_.ProcessId }
    }
    $parent = Get-CimInstance Win32_Process -Filter "ProcessId=$($proc.ParentProcessId)"
    $ids | ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }
    if ($parent -and $parent.Name -eq 'cmd.exe') { Stop-Process -Id $parent.ProcessId -Force -ErrorAction SilentlyContinue }
}

function Start-Minimized($cmdFile) {
    Start-Process -FilePath (Join-Path $root $cmdFile) -WorkingDirectory $root -WindowStyle Minimized
}

# --- The loop ---
$runs = @(Get-HarveyProcs 'run')
$ageMin = if (Test-Path $log) { ((Get-Date) - (Get-Item $log).LastWriteTime).TotalMinutes } else { [double]::MaxValue }

if ($runs.Count -eq 0) {
    Note "Harvey loop not running. Starting it."
    Start-Minimized 'harvey-run.cmd'
} elseif ($ageMin -gt $StaleMinutes) {
    Note ("Harvey loop silent for {0:N0} min (limit {1}). Restarting it." -f $ageMin, $StaleMinutes)
    $runs | ForEach-Object { Stop-Tree $_ }
    Start-Sleep -Seconds 3
    Start-Minimized 'harvey-run.cmd'
} elseif ($runs.Count -gt 1) {
    # Two loops would email the same people twice: keep the newest.
    $extra = $runs | Sort-Object CreationDate | Select-Object -SkipLast 1
    Note "Found $($runs.Count) Harvey loops. Stopping the older $($extra.Count)."
    $extra | ForEach-Object { Stop-Tree $_ }
}

# --- The dashboard ---
if (@(Get-HarveyProcs 'dashboard').Count -eq 0) {
    Note "Dashboard not running. Starting it."
    Start-Minimized 'harvey-dashboard.cmd'
}
