"""External OSINT CLI tool runner.

Executes real open-source CLI tools via subprocess and parses their output:
- Sherlock   (username -> 400+ platforms)
- Maigret    (username -> 2500+ sites, dossier extraction)
- Holehe     (email -> registered-on-platform check)
- PhoneInfoga (phone -> advanced scan)

Each runner:
1. detects whether the binary is available on PATH
2. runs it in a subprocess with a hard timeout
3. parses stdout into structured JSON
4. never raises -> always returns {ok, available, tool, ...}

This lets the web hub actually *drive* the open-source tools, not just link
to them. When a tool is absent or errors out, the hub falls back gracefully
to its built-in passive module.
"""

import json
import os
import re
import shutil
import subprocess


ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def _strip_ansi(text):
    return ANSI_RE.sub("", text)


FOUND_RE = re.compile(r"^\[\+\]\s+(?P<name>[^:]+):\s*(?P<url>\S+)")


def _which(cmd):
    return shutil.which(cmd) is not None


def _run(args, timeout=120, cwd=None):
    """Run a subprocess capturing stdout; return (returncode, stdout, stderr)."""
    try:
        env = dict(os.environ, TERM="dumb", PYTHONUNBUFFERED="1")
        proc = subprocess.run(
            args, capture_output=True, text=True, timeout=timeout, env=env, cwd=cwd
        )
        return proc.returncode, proc.stdout or "", proc.stderr or ""
    except subprocess.TimeoutExpired as e:
        return 124, e.stdout or "", f"timeout after {timeout}s"
    except FileNotFoundError:
        return 127, "", f"{args[0]} not found"
    except Exception as exc:  # noqa: BLE001
        return 1, "", str(exc)


def _parse_sherlock(text):
    """Parse Sherlock `[+] Platform: url` lines."""
    hits = []
    for line in text.splitlines():
        m = FOUND_RE.match(line.strip())
        if m:
            hits.append({"platform": m.group("name").strip(), "url": m.group("url").strip()})
    return hits


def _parse_holehe(text):
    """Parse Holehe `[+] site` used-on lines."""
    used, not_used, rate_limited = [], [], []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("[+]"):
            used.append(line[3:].strip())
        elif line.startswith("[-]"):
            not_used.append(line[3:].strip())
        elif line.startswith("[x]"):
            rate_limited.append(line[3:].strip())
    return {"used_on": used, "not_used": not_used, "rate_limited": rate_limited}


def _parse_maigret(text):
    """Parse Maigret `[+] Site: url` hits."""
    hits = []
    for line in text.splitlines():
        m = FOUND_RE.match(line.strip())
        if m:
            hits.append({"platform": m.group("name").strip(), "url": m.group("url").strip()})
    return hits


def _parse_phoneinfoga(text):
    """Parse PhoneInfoga human output into sections."""
    sections = {}
    current = "general"
    sections[current] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("[!]") or line.startswith("[*]") or line.startswith("[+]") or line.startswith("[-]"):
            sections.setdefault(current, []).append(line)
            continue
        if re.match(r"^[A-Z][A-Za-z ]+:", line) or re.match(r"^[A-Z][A-Za-z ]+$", line) and len(line) < 40:
            current = line.rstrip(":").lower()
            sections.setdefault(current, [])
            continue
        sections[current].append(line)
    return sections


# --- public API --------------------------------------------------------------


def run_sherlock(username, timeout=120):
    if not username:
        return {"ok": False, "tool": "sherlock", "error": "username vide"}
    if not _which("sherlock"):
        return {"ok": False, "available": False, "tool": "sherlock",
                "error": "Sherlock non installé (pip install sherlock-project)"}
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        rc, out, err = _run(["sherlock", "--timeout", "8", "--print-found",
                             "--no-color", "--folderoutput", td, username], timeout, cwd=td)
    hits = _parse_sherlock(out)
    return {"ok": True, "available": True, "tool": "sherlock", "username": username,
            "returncode": rc, "accounts": hits, "count": len(hits),
            "raw_excerpt": out[-1500:] if out else err}


def run_maigret(username, timeout=180):
    if not username:
        return {"ok": False, "tool": "maigret", "error": "username vide"}
    if not _which("maigret"):
        return {"ok": False, "available": False, "tool": "maigret",
                "error": "Maigret non installé (pip install maigret)"}
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        rc, out, err = _run(
            ["maigret", "--no-color", "--timeout", "8", "--max-connections", "30",
             "--no-progressbar", "--folderoutput", td, username],
            timeout, cwd=td,
        )
    hits = _parse_maigret(out)
    return {"ok": True, "available": True, "tool": "maigret", "username": username,
            "returncode": rc, "accounts": hits, "count": len(hits),
            "raw_excerpt": out[-2000:] if out else err}


def run_holehe(email, timeout=120):
    if not email:
        return {"ok": False, "tool": "holehe", "error": "email vide"}
    if not _which("holehe"):
        return {"ok": False, "available": False, "tool": "holehe",
                "error": "Holehe non installé (pip install holehe)"}
    rc, out, err = _run(["holehe", "--only-used", "--no-color", email], timeout)
    parsed = _parse_holehe(out)
    return {"ok": True, "available": True, "tool": "holehe", "email": email,
            "returncode": rc, "used_on": parsed["used_on"], "not_used": parsed["not_used"],
            "rate_limited": parsed["rate_limited"], "count": len(parsed["used_on"]),
            "raw_excerpt": out[-1500:] if out else err}


def run_phoneinfoga(number, timeout=90):
    if not number:
        return {"ok": False, "tool": "phoneinfoga", "error": "numéro vide"}
    if not _which("phoneinfoga"):
        return {"ok": False, "available": False, "tool": "phoneinfoga",
                "error": "PhoneInfoga non installé"}
    rc, out, err = _run(["phoneinfoga", "scan", "-n", number, "--no-ansi"], timeout, cwd=os.path.expanduser("~"))
    parsed = _parse_phoneinfoga(out)
    return {"ok": True, "available": True, "tool": "phoneinfoga", "number": number,
            "returncode": rc, "sections": parsed,
            "raw_excerpt": out[-2000:] if out else err}


def _parse_socialscan(text):
    """Parse socialscan tabular output: Platform<TAB>Status lines.

    socialscan emits a header, then lines like:
        repusseau\n--------\nGitLab\tAvailable, Taken/Reserved, Invalid, Error\n...
    Each platform row lists a status per query.
    """
    hits = []
    lines = [l for l in text.splitlines() if l.strip()]
    for line in lines:
        # rows are "Platform<TAB>Status" possibly repeated per query
        parts = line.split("\t")
        if len(parts) >= 2 and any(k in parts[-1] for k in ("Available", "Taken", "Reserved", "Invalid", "Error")):
            platform = parts[0].strip()
            status = parts[-1].strip()
            available = "Available" in status
            hits.append({"platform": platform, "status": status, "available": available})
    return hits


def run_socialscan(query, timeout=120):
    """socialscan checks email/username usage on ~8 platforms with deep verification.

    Unlike simple HTTP probes, socialscan uses platform APIs / proper checks,
    so it has very few false positives. Supports both usernames and emails.
    """
    if not query:
        return {"ok": False, "tool": "socialscan", "error": "requête vide"}
    if not _which("socialscan"):
        return {"ok": False, "available": False, "tool": "socialscan",
                "error": "socialscan non installé (pip install socialscan)"}
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        rc, out, err = _run(["socialscan", "--show-urls", "--available-only", query], timeout, cwd=td)
    parsed = _parse_socialscan(out)
    return {"ok": True, "available": True, "tool": "socialscan", "query": query,
            "returncode": rc, "results": parsed, "count": len(parsed),
            "raw_excerpt": out[-1500:] if out else err}


def _parse_dnstwist(text):
    """Parse dnstwist domain-permutation table output.

    Columns are space-separated: type domain IP [IPv6] NS:... MX:...
    """
    rows = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("*") or "Domain name permutation" in line:
            continue
        cols = line.split()
        if len(cols) >= 2:
            rows.append({
                "type": cols[0], "domain": cols[1],
                "ip": cols[2] if len(cols) > 2 and not cols[2].startswith("NS:") else "",
                "ns": next((c[3:] for c in cols if c.startswith("NS:")), ""),
                "mx": next((c[3:] for c in cols if c.startswith("MX:")), ""),
            })
    return rows


def run_dnstwist(domain, timeout=120):
    """dnstwist detects typosquatting / homograph variants of a domain."""
    if not domain:
        return {"ok": False, "tool": "dnstwist", "error": "domaine vide"}
    if not _which("dnstwist"):
        return {"ok": False, "available": False, "tool": "dnstwist",
                "error": "dnstwist non installé (pip install dnstwist)"}
    host = domain.replace("https://", "").replace("http://", "").split("/")[0].lstrip("www.")
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        rc, out, err = _run(["dnstwist", "-r", "-t", "5", host], timeout, cwd=td)
    parsed = _parse_dnstwist(out)
    return {"ok": True, "available": True, "tool": "dnstwist", "domain": host,
            "returncode": rc, "domains": parsed, "count": len(parsed),
            "raw_excerpt": out[-2000:] if out else err}


def _parse_h8mail(text):
    """Parse h8mail session recap: target | status table."""
    text = _strip_ansi(text)
    targets = []
    for line in text.splitlines():
        line = line.strip()
        if "|" in line and ("Compromised" in line or "Not Compromised" in line or "Found" in line):
            parts = [p.strip() for p in line.split("|") if p.strip()]
            if len(parts) >= 2:
                targets.append({"target": parts[0], "status": parts[1]})
    return targets


def run_h8mail(email, timeout=120):
    """h8mail hunts for password breaches associated with an email.

    Without local breach files or API keys it returns a Not Compromised status,
    but the runner exposes the tool so users with breach data can use it.
    """
    if not email:
        return {"ok": False, "tool": "h8mail", "error": "email vide"}
    if not _which("h8mail"):
        return {"ok": False, "available": False, "tool": "h8mail",
                "error": "h8mail non installé (pip install h8mail)"}
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        rc, out, err = _run(["h8mail", "-t", email], timeout, cwd=td)
    parsed = _parse_h8mail(out)
    return {"ok": True, "available": True, "tool": "h8mail", "email": email,
            "returncode": rc, "breaches": parsed, "count": len(parsed),
            "raw_excerpt": out[-2000:] if out else err}


def run_instaloader(username, timeout=60):
    """Instaloader can download public Instagram profile metadata (no login).

    Used here in dry/probe mode to check if a public Instagram profile exists.
    """
    if not username:
        return {"ok": False, "tool": "instaloader", "error": "username vide"}
    if not _which("instaloader"):
        return {"ok": False, "available": False, "tool": "instaloader",
                "error": "instaloader non installé (pip install instaloader)"}
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        rc, out, err = _run(["instaloader", "--no-pictures", "--no-videos",
                             "--no-captions", "--no-metadata-json", "--dirname-pattern", td,
                             username], timeout, cwd=td)
    # exit code 0 with a profile dir => exists; non-zero with specific message
    exists = rc == 0
    return {"ok": True, "available": True, "tool": "instaloader", "username": username,
            "returncode": rc, "instagram_exists": exists,
            "raw_excerpt": (out + err)[-1500:]}


# registry of runnable tools for the UI
RUNNABLE = [
    {"id": "sherlock", "target": "username", "label": "Sherlock (400+ plateformes)"},
    {"id": "maigret", "target": "username", "label": "Maigret (2500+ sites, dossier)"},
    {"id": "socialscan", "target": "username", "label": "socialscan (vérif. approfondie, peu de faux positifs)"},
    {"id": "instaloader", "target": "username", "label": "Instaloader (profil Instagram public)"},
    {"id": "holehe", "target": "email", "label": "Holehe (email enregistré ?)"},
    {"id": "h8mail", "target": "email", "label": "h8mail (fuites de mot de passe)"},
    {"id": "phoneinfoga", "target": "phone", "label": "PhoneInfoga (scan avancé)"},
    {"id": "dnstwist", "target": "website", "label": "DNSTwist (typosquatting de domaine)"},
]


def availability():
    return {t["id"]: _which(t["id"]) for t in RUNNABLE}


def run(tool_id, value):
    dispatch = {
        "sherlock": run_sherlock,
        "maigret": run_maigret,
        "socialscan": run_socialscan,
        "instaloader": run_instaloader,
        "holehe": run_holehe,
        "h8mail": run_h8mail,
        "phoneinfoga": run_phoneinfoga,
        "dnstwist": run_dnstwist,
    }
    fn = dispatch.get(tool_id)
    if not fn:
        return {"ok": False, "error": f"outil inconnu: {tool_id}"}
    return fn(value)
