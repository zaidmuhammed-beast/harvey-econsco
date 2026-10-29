"""Password login for the dashboard.

The dashboard can approve and send email and rewrite .env, so anything but a
loopback-only local run must be behind a login. Stdlib only:

- One shared password: DASHBOARD_PASSWORD in .env.
- Session = signed cookie (HMAC-SHA256 over an expiry), HttpOnly,
  SameSite=Strict, Secure when served over HTTPS. The signing key comes from
  DASHBOARD_SECRET, or is generated once into data/dashboard_secret.
- Brute force: 5 failures from one client address lock it out for 15 minutes.
- Cross-site POSTs are rejected (Origin must match Host) on top of SameSite.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
import time
from pathlib import Path

from harvey.paths import PROJECT_ROOT

COOKIE_NAME = "harvey_session"
SESSION_SECONDS = 7 * 24 * 3600
MAX_FAILURES = 5
LOCKOUT_SECONDS = 15 * 60
SECRET_FILE = PROJECT_ROOT / "data" / "dashboard_secret"

# Paths reachable without a session: the login form itself and static assets
# (CSS, fonts, JS — no data in them).
PUBLIC_PREFIXES = ("/login", "/static/", "/favicon")

_failures: dict[str, tuple[int, float]] = {}  # client -> (count, first_failure_at)


def configured_password() -> str:
    return os.environ.get("DASHBOARD_PASSWORD", "")


def auth_required(host: str) -> bool:
    """Login is on whenever a password is set. Without one, only a
    loopback-bound dashboard may run (and it runs open, as before)."""
    return bool(configured_password()) or host not in ("127.0.0.1", "localhost", "::1")


def _secret() -> bytes:
    env = os.environ.get("DASHBOARD_SECRET", "")
    if env:
        return env.encode()
    try:
        return bytes.fromhex(SECRET_FILE.read_text().strip())
    except (OSError, ValueError):
        pass
    key = secrets.token_bytes(32)
    SECRET_FILE.parent.mkdir(parents=True, exist_ok=True)
    SECRET_FILE.write_text(key.hex())
    try:
        SECRET_FILE.chmod(0o600)
    except OSError:
        pass
    return key


def _sign(payload: bytes) -> str:
    return hmac.new(_secret(), payload, hashlib.sha256).hexdigest()


def make_session() -> str:
    payload = f"{int(time.time()) + SESSION_SECONDS}:{secrets.token_hex(8)}".encode()
    return base64.urlsafe_b64encode(payload).decode() + "." + _sign(payload)


def valid_session(token: str | None) -> bool:
    if not token or "." not in token:
        return False
    b64, sig = token.rsplit(".", 1)
    try:
        payload = base64.urlsafe_b64decode(b64.encode())
    except (ValueError, TypeError):
        return False
    if not hmac.compare_digest(_sign(payload), sig):
        return False
    try:
        expires = int(payload.split(b":", 1)[0])
    except ValueError:
        return False
    return expires > time.time()


def password_ok(candidate: str) -> bool:
    expected = configured_password()
    if not expected:
        return False
    # Compare digests so timing doesn't leak the password length.
    return hmac.compare_digest(
        hashlib.sha256(candidate.encode()).digest(),
        hashlib.sha256(expected.encode()).digest(),
    )


def locked_out(client: str) -> int:
    """Seconds left on a lockout for this client, or 0."""
    count, first = _failures.get(client, (0, 0.0))
    if count < MAX_FAILURES:
        return 0
    left = int(first + LOCKOUT_SECONDS - time.time())
    if left <= 0:
        _failures.pop(client, None)
        return 0
    return left


def record_failure(client: str) -> None:
    count, first = _failures.get(client, (0, time.time()))
    if time.time() - first > LOCKOUT_SECONDS:
        count, first = 0, time.time()
    _failures[client] = (count + 1, first)


def clear_failures(client: str) -> None:
    _failures.pop(client, None)


def same_origin(origin: str | None, host: str | None) -> bool:
    """True when a POST's Origin (if the browser sent one) matches Host."""
    if not origin:
        return True
    if not host:
        return False
    return origin.split("://", 1)[-1].rstrip("/") == host


LOGIN_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Harvey — Sign in</title>
<link rel="stylesheet" href="/static/app.css">
<style>
  body {{ min-height: 100vh; display: grid; place-items: center; margin: 0; padding: 16px; box-sizing: border-box; }}
  .login {{ width: 100%; max-width: 360px; background: var(--panel); border: 1px solid var(--line, rgba(127,127,127,.25));
           border-radius: 12px; padding: 32px 28px; }}
  .login .brand {{ display: flex; gap: 12px; align-items: center; margin-bottom: 24px; }}
  .login label {{ display: block; font-size: 13px; margin-bottom: 6px; opacity: .8; }}
  .login input {{ width: 100%; box-sizing: border-box; padding: 10px 12px; font: inherit; border-radius: 8px;
                 border: 1px solid var(--line, rgba(127,127,127,.35)); background: var(--bg); color: inherit; }}
  .login button {{ width: 100%; margin-top: 16px; padding: 10px 12px; font: inherit; font-weight: 600; border: 0;
                  border-radius: 8px; cursor: pointer; background: var(--accent, #2b5cff); color: #fff; }}
  .login .error {{ margin-top: 14px; font-size: 13px; color: var(--danger, #c0392b); }}
</style>
</head>
<body>
<form class="login" method="post" action="/login">
  <div class="brand">
    <div class="mark">H</div>
    <div><h1 style="margin:0">Harvey</h1><div class="tagline">Sign in to the command deck</div></div>
  </div>
  <label for="password">Password</label>
  <input id="password" name="password" type="password" autocomplete="current-password" autofocus required>
  <button type="submit">Sign in</button>
  {error}
</form>
</body>
</html>"""


def login_page(error: str = "") -> str:
    from html import escape
    block = f'<div class="error" role="alert">{escape(error)}</div>' if error else ""
    return LOGIN_PAGE.format(error=block)
