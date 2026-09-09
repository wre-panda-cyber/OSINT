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


# registry of runnable tools for the UI
RUNNABLE = [
    {"id": "sherlock", "target": "username", "label": "Sherlock (400+ plateformes)"},
    {"id": "maigret", "target": "username", "label": "Maigret (2500+ sites, dossier)"},
    {"id": "holehe", "target": "email", "label": "Holehe (email enregistré ?)"},
    {"id": "phoneinfoga", "target": "phone", "label": "PhoneInfoga (scan avancé)"},
]


def availability():
    return {t["id"]: _which(t["id"]) for t in RUNNABLE}


def run(tool_id, value):
    dispatch = {
        "sherlock": run_sherlock,
        "maigret": run_maigret,
        "holehe": run_holehe,
        "phoneinfoga": run_phoneinfoga,
    }
    fn = dispatch.get(tool_id)
    if not fn:
        return {"ok": False, "error": f"outil inconnu: {tool_id}"}
    return fn(value)
