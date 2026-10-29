"""Per-recipient send window: deliver during the recipient's working hours.

Global quiet hours are one window in one timezone. Once prospects span the UK,
Spain, the US and Asia, that window lands some sends at 3am. This module maps a
recipient to a timezone (from the company's discovered location, falling back
to the email's country TLD) so the sender can hold each email until it is
working hours *where the recipient is*.
"""

from __future__ import annotations

import re
from datetime import datetime, time

import pytz

# US state → timezone (the state's main zone; good enough for a send window).
_US_STATES = {
    "America/New_York": "CT DE DC FL GA ME MD MA MI NH NJ NY NC OH PA RI SC VT VA WV IN KY",
    "America/Chicago": "AL AR IL IA KS LA MN MS MO NE ND OK SD TN TX WI",
    "America/Denver": "CO MT NM UT WY ID",
    "America/Phoenix": "AZ",
    "America/Los_Angeles": "CA NV OR WA",
    "America/Anchorage": "AK",
    "Pacific/Honolulu": "HI",
}
US_STATE_TZ = {st: tz for tz, states in _US_STATES.items() for st in states.split()}

# Country / region names that appear in discovered locations.
COUNTRY_TZ = {
    "united kingdom": "Europe/London", "england": "Europe/London",
    "scotland": "Europe/London", "wales": "Europe/London",
    "northern ireland": "Europe/London", "uk": "Europe/London",
    "ireland": "Europe/Dublin",
    "spain": "Europe/Madrid", "españa": "Europe/Madrid",
    "indonesia": "Asia/Jakarta",
    "united states": "America/New_York", "usa": "America/New_York",
}

# Bare city names (a location is sometimes just "London").
CITY_TZ = {
    "london": "Europe/London", "manchester": "Europe/London",
    "birmingham": "Europe/London", "belfast": "Europe/London",
    "madrid": "Europe/Madrid", "barcelona": "Europe/Madrid",
    "valencia": "Europe/Madrid", "jaen": "Europe/Madrid", "jaén": "Europe/Madrid",
    "jakarta": "Asia/Jakarta",
}

# Email/domain TLD fallback when the location is empty or unrecognised.
TLD_TZ = {
    "uk": "Europe/London", "ie": "Europe/Dublin", "es": "Europe/Madrid",
    "id": "Asia/Jakarta",
}


# Phone fallback: OSM often gives only a suburb ("Santa Monica", "Stockport"),
# but the phone number's country code (and, in the US, area code) still says
# where the business is. Area codes cover the metros Harvey discovers in.
PHONE_CC_TZ = {"44": "Europe/London", "353": "Europe/Dublin",
               "34": "Europe/Madrid", "62": "Asia/Jakarta"}
_US_AREA = {
    "America/Los_Angeles": "213 310 323 424 562 626 657 661 714 747 818 909 949",
    "America/Chicago": "214 281 312 331 346 469 630 682 708 713 773 817 832 847 872 945 972",
    "America/New_York": "201 212 305 332 347 516 551 561 631 646 718 754 786 862 914 917 929 954 973",
}
US_AREA_TZ = {ac: tz for tz, codes in _US_AREA.items() for ac in codes.split()}


def _phone_timezone(phone: str) -> str | None:
    digits = re.sub(r"\D", "", phone or "")
    if not (phone or "").strip().startswith("+"):
        return None
    if digits.startswith("1") and len(digits) == 11:
        return US_AREA_TZ.get(digits[1:4])
    for cc in sorted(PHONE_CC_TZ, key=len, reverse=True):
        if digits.startswith(cc):
            return PHONE_CC_TZ[cc]
    return None


def recipient_timezone(
    location: str = "", email: str = "", phone: str = ""
) -> str | None:
    """Best-guess IANA timezone for a recipient, or None if unknown."""
    loc = (location or "").strip()
    if loc:
        # "Houston, TX" / "Wayne, NJ 07470"
        m = re.search(r",\s*([A-Z]{2})\b(?:\s+\d{5})?\s*$", loc)
        if m and m.group(1) in US_STATE_TZ:
            return US_STATE_TZ[m.group(1)]
        parts = [p.strip().lower() for p in loc.split(",") if p.strip()]
        for part in reversed(parts):
            if part in COUNTRY_TZ:
                return COUNTRY_TZ[part]
        for part in parts:
            if part in CITY_TZ:
                return CITY_TZ[part]
    tz = _phone_timezone(phone)
    if tz:
        return tz
    domain = (email or "").rsplit("@", 1)[-1].lower()
    tld = domain.rsplit(".", 1)[-1] if "." in domain else ""
    return TLD_TZ.get(tld)


def in_send_window(
    tz_name: str,
    start: str,
    end: str,
    weekdays_only: bool = True,
    now: datetime | None = None,
) -> bool:
    """True if it is currently within [start, end) in ``tz_name``."""
    tz = pytz.timezone(tz_name)
    local = (now or datetime.now(pytz.utc)).astimezone(tz)
    if weekdays_only and local.weekday() >= 5:
        return False
    t = local.time()
    s, e = time.fromisoformat(start), time.fromisoformat(end)
    if s <= e:
        return s <= t < e
    return t >= s or t < e
