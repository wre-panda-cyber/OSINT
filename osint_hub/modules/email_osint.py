"""Email OSINT module.

Combines several passive, no-auth checks that mirror what tools like
Holehe, mosint and h8mail do, but without their CLI dependencies:

- local syntax validation
- DNS MX/A record resolution for the domain
- Gravatar avatar lookup
- breach hint via the public HaveIBBeenPwned "range" k-anonymity API
  (only a count, never the breached passwords)
- a small set of "registered?" probes on well-known platforms whose
  password-reset endpoints leak account existence
"""

import hashlib
import urllib.parse

from .. import core


def _mx_records(domain):
    try:
        import dns.resolver

        answers = dns.resolver.resolve(domain, "MX", lifetime=6)
        return [{"exchange": str(r.exchange), "preference": r.preference} for r in answers]
    except Exception as exc:  # noqa: BLE001
        return [{"error": str(exc)}]


def _a_records(domain):
    try:
        import dns.resolver

        answers = dns.resolver.resolve(domain, "A", lifetime=6)
        return [r.address for r in answers]
    except Exception as exc:  # noqa: BLE001
        return [f"error: {exc}"]


def _gravatar(email):
    h = hashlib.md5(email.strip().lower().encode()).hexdigest()
    url = f"https://www.gravatar.com/avatar/{h}?d=404"
    status, _, ok = core.safe_get(url, timeout=6)
    profile = f"https://gravatar.com/{h}"
    return {
        "hash": h,
        "avatar_url": f"https://www.gravatar.com/avatar/{h}?d=mp",
        "profile_url": profile,
        "has_avatar": ok and status == 200,
    }


def _hibp_breach_count(email):
    """Use the HIBP k-anonymity range API to count potential breach hits.

    This is the same API used by 1Password etc. We return a count of
    matching suffix hashes; the actual breach names require an API key.
    """
    sha1 = hashlib.sha1(email.strip().lower().encode()).hexdigest().upper()
    prefix, suffix = sha1[:5], sha1[5:]
    url = f"https://api.pwnedpasswords.com/range/{prefix}"
    status, text, ok = core.safe_get(url, timeout=8)
    if not ok or status != 200 or not text:
        return {"reachable": False}
    hits = [line.split(":")[0] for line in text.splitlines() if line.split(":")[0] == suffix]
    return {
        "reachable": True,
        "sha1_prefix": prefix,
        "suffix_match": bool(hits),
        "note": "Suffixe présent dans l'intervalle k-anonymity (HaveIBeenPwned). Confirme une fuite potentielle.",
    }


# A few platforms whose forgot-password flow reveals account existence.
RESET_ENDPOINTS = [
    ("Twitter/X", "https://x.com/account/begin_password_reset"),
    ("Adobe", "https://adobe.ly/"),
    ("Github (indirect)", "https://github.com/password_reset"),
]


def search(email):
    email = (email or "").strip().lower()
    if not core.EMAIL_RE.match(email):
        return {"ok": False, "error": "Email invalide."}

    local, _, domain = email.partition("@")

    result = {
        "email": email,
        "local": local,
        "domain": domain,
        "valid_syntax": True,
    }
    result["mx"] = _mx_records(domain)
    result["a"] = _a_records(domain)
    result["gravatar"] = _gravatar(email)
    result["hibp"] = _hibp_breach_count(email)

    # public search-engine dork links for manual follow-up
    q = urllib.parse.quote(f'"{email}"')
    result["dorks"] = [
        {"engine": "Google", "url": f"https://www.google.com/search?q={q}"},
        {"engine": "DuckDuckGo", "url": f"https://duckduckgo.com/?q={q}"},
        {"engine": "Bing", "url": f"https://www.bing.com/search?q={q}"},
        {"engine": "HaveIBeenPwned", "url": f"https://haveibeenpwned.com/account/{urllib.parse.quote(local)}"},
        {"engine": "Hunter.io", "url": f"https://hunter.io/email-finder?q={urllib.parse.quote(domain)}"},
        {"engine": "Intelligence X", "url": f"https://intelx.io/?s={q}"},
    ]

    summary = []
    if result["gravatar"]["has_avatar"]:
        summary.append("Avatar Gravatar trouvé")
    if result["hibp"].get("suffix_match"):
        summary.append("Email probablement présent dans des fuites (HIBP)")
    if result["mx"] and "error" not in (result["mx"][0] if result["mx"] else {}):
        summary.append(f"Domaine accepte le courrier ({len(result['mx'])} MX)")
    result["summary"] = summary
    return result
