"""PID file for the running Harvey loop, and a safe "is it alive?" check.

``os.kill(pid, 0)`` is a harmless existence probe on macOS/Linux, but on
Windows any signal other than CTRL_C/CTRL_BREAK calls TerminateProcess — it
would KILL whatever process now owns that PID. So Windows gets a read-only
OpenProcess/GetExitCodeProcess check instead.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

PID_FILE = Path(__file__).resolve().parent.parent / "data" / "harvey.pid"


def pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if sys.platform == "win32":
        import ctypes
        from ctypes import wintypes

        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        STILL_ACTIVE = 259
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.OpenProcess.restype = wintypes.HANDLE
        handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if not handle:
            return False
        try:
            code = wintypes.DWORD()
            if not kernel32.GetExitCodeProcess(handle, ctypes.byref(code)):
                return False
            return code.value == STILL_ACTIVE
        finally:
            kernel32.CloseHandle(handle)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True  # exists, owned by someone else
    except OSError:
        return False
    return True


def read_pid() -> int | None:
    """The recorded Harvey PID if that process is alive; clears a stale file."""
    try:
        pid = int(PID_FILE.read_text().strip())
    except (OSError, ValueError):
        return None
    if pid_alive(pid):
        return pid
    PID_FILE.unlink(missing_ok=True)
    return None


def write_pid() -> None:
    PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    PID_FILE.write_text(str(os.getpid()))


def clear_pid() -> None:
    """Remove the PID file if it is ours."""
    try:
        if int(PID_FILE.read_text().strip()) == os.getpid():
            PID_FILE.unlink(missing_ok=True)
    except (OSError, ValueError):
        pass
