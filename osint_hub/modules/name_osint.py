"""Name / username OSINT module.

Given a full name (or a username) this module:
- builds candidate usernames (initials, joined, dotted, hyphenated)
- builds candidate email permutations (à la Email Permutator+)
- checks profile presence across a curated list of social platforms
  (Sherlock-style probing by URL existence, no signup, no auth required)

It deliberately avoids heavy third-party deps so the interface stays
self-contained and runnable in a sandbox.
"""

import urllib.parse

from .. import core

# Curated platform probe list. Each probe maps a username placeholder to a
# public profile URL that, when it returns HTTP 200, strongly suggests an
# account exists. Inspired by Sherlock / Maigret probe sites.
PLATFORMS = [
    ("GitHub", "https://github.com/{u}"),
    ("GitLab", "https://gitlab.com/{u}"),
    ("Reddit", "https://www.reddit.com/user/{u}"),
    ("X / Twitter", "https://x.com/{u}"),
    ("Instagram", "https://www.instagram.com/{u}/"),
    ("TikTok", "https://www.tiktok.com/@{u}"),
    ("YouTube", "https://www.youtube.com/@{u}"),
    ("Twitch", "https://www.twitch.tv/{u}"),
    ("Medium", "https://medium.com/@{u}"),
    ("Dev.to", "https://dev.to/{u}"),
    ("HackerNews", "https://news.ycombinator.com/user?id={u}"),
    ("Keybase", "https://keybase.io/{u}"),
    ("Pinterest", "https://www.pinterest.com/{u}/"),
    ("Steam", "https://steamcommunity.com/id/{u}"),
    ("Flickr", "https://www.flickr.com/people/{u}"),
    ("Vimeo", "https://vimeo.com/{u}"),
    ("SoundCloud", "https://soundcloud.com/{u}"),
    ("Spotify (web)", "https://open.spotify.com/user/{u}"),
    ("LinkedIn (search)", "https://www.linkedin.com/in/{u}"),
    ("Facebook (search)", "https://www.facebook.com/{u}"),
    ("Telegram", "https://t.me/{u}"),
    ("Mastodon (web)", "https://mastodon.social/@{u}"),
    ("Threads", "https://www.threads.net/@{u}"),
    ("Snapchat", "https://www.snapchat.com/add/{u}"),
    ("About.me", "https://about.me/{u}"),
    ("Gravatar (profile)", "https://gravatar.com/{u}"),
]


def _candidates_from_name(name):
    f, _, l = name.partition(" ")
    f = f.lower().strip()
    l = l.lower().strip()
    if not f and not l:
        return []
    cands = set()
    if f and l:
        for sep in ("", ".", "_", "-"):
            cands.add(f"{f}{sep}{l}")
            cands.add(f"{f[0]}{sep}{l}")
            cands.add(f"{f}{sep}{l[0]}")
        cands.add(f"{l}{f}")
        cands.add(f"{f[0]}{l}")
    else:
        cands.add((f + l).lower())
    return sorted(c for c in cands if 2 <= len(c) <= 32)


def _email_permutations(name, domains):
    f, _, l = name.partition(" ")
    f = f.lower().strip()
    l = l.lower().strip()
    perms = set()
    if f and l:
        patterns = [
            "{f}{l}", "{f}.{l}", "{f}_{l}", "{f}-{l}",
            "{f}{l0}", "{f}.{l0}", "{l}{f}", "{l}.{f}",
            "{f0}{l}", "{f0}.{l}", "{f0}{l}", "{fl}", "{f}{l0}",
        ]
        for d in domains:
            for p in patterns:
                perms.add(p.format(f=f, l=l, f0=f[0], l0=l[0]) + "@" + d)
    return sorted(perms)


def _probe_platforms(username):
    """Return list of {platform, url, status} for the given username."""
    out = []
    for platform, tmpl in PLATFORMS:
        url = tmpl.format(u=urllib.parse.quote(username))
        status, _, ok = core.safe_get(url, timeout=6)
        # Many socials return 200 even for missing pages (SPA). Treat 404/410
        # as absent; everything else (200/301/302) as candidate presence.
        if status in (404, 410, 403, 451):
            presence = False
        elif ok and status and status < 500:
            presence = True
        else:
            presence = None
        out.append({"platform": platform, "url": url, "status": status, "present": presence})
    return out


def search(query):
    """Search by a name ("First Last") or by a raw username."""
    query = (query or "").strip()
    if not query:
        return {"ok": False, "error": "Requête vide."}

    parts = query.split()
    is_name = len(parts) >= 2 and all(p.isalpha() for p in parts)

    result = {"query": query, "is_name": is_name}

    if is_name:
        candidates = _candidates_from_name(query)
        result["candidate_usernames"] = candidates
        result["email_permutations"] = _email_permutations(
            query, ["gmail.com", "outlook.com", "hotmail.com", "yahoo.com", "proton.me", "icloud.com"]
        )
        primary = candidates[0] if candidates else query.lower()
    else:
        candidates = [query]
        primary = query

    result["primary_username"] = primary
    result["accounts"] = _probe_platforms(primary)
    result["probed_usernames"] = candidates

    found = [a for a in result["accounts"] if a["present"]]
    result["summary"] = {
        "accounts_found": len(found),
        "accounts_likely": len(found),
        "candidates": len(candidates),
    }
    return result
