"""Shared helpers for input normalization and common formatting."""

import re

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")
URL_RE = re.compile(r"^(https?://)?[A-Za-z0-9.\-]+\.[A-Za-z]{2,}(/.*)?$")


def normalize_target(first_name="", last_name="", phone="", email="", website="", username=""):
    """Clean and consolidate the search criteria into a single target dict."""
    first_name = (first_name or "").strip()
    last_name = (last_name or "").strip()
    phone = (phone or "").strip()
    email = (email or "").strip()
    website = (website or "").strip()
    username = (username or "").strip()

    name_full = " ".join(part for part in (first_name, last_name) if part).strip()

    if website and not URL_RE.match(website):
        website = ""  # invalid -> ignore rather than crash

    if email and not EMAIL_RE.match(email):
        email = ""

    if not username and name_full:
        username = (first_name + last_name).lower()

    return {
        "first_name": first_name,
        "last_name": last_name,
        "name_full": name_full,
        "phone": phone,
        "email": email,
        "website": website,
        "username": username,
        "has_any": any([name_full, phone, email, website, username]),
    }


def safe_get(url, timeout=8, headers=None, **kwargs):
    """requests.get wrapper that never raises; returns (status, text|json, ok)."""
    import requests

    hdrs = {"User-Agent": "OSINT-Hub/1.0 (+research)"}
    if headers:
        hdrs.update(headers)
    try:
        resp = requests.get(url, timeout=timeout, headers=hdrs, **kwargs)
        return resp.status_code, resp.text, True
    except Exception as exc:  # noqa: BLE001
        return None, str(exc), False
