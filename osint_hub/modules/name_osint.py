"""Name / username OSINT module.

Given a full name (or a surname alone, or a username) this module:
- builds candidate usernames (initials, joined, dotted, hyphenated) for both
  "First Last" and surname-only inputs
- builds candidate email permutations (a la Email Permutator+)
- checks profile presence across a curated list of social platforms
  (Sherlock-style probing by URL existence, no signup, no auth required)
- emits ready-to-use search-engine dork links (Google, Bing, DuckDuckGo,
  Yandex, annuaires) so the investigator always has actionable links even
  when automated probes are inconclusive

It deliberately avoids heavy third-party deps so the interface stays
self-contained and runnable in a sandbox.
"""

import re
import urllib.parse

from .. import core

# Curated platform probe list. Each probe maps a username placeholder to a
# public profile URL. We inspect both the HTTP status and a slice of the
# page body: a 200 with the username present in the body is a much stronger
# signal than a bare 200 (many SPAs return 200 for missing pages).
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

EMAIL_DOMAINS = ["gmail.com", "outlook.com", "hotmail.com", "yahoo.com",
                 "proton.me", "icloud.com", "live.com", "msn.com"]


def _candidates_from_name(name):
    """Generate username candidates from a full name OR a surname alone."""
    parts = [p for p in name.split() if p]
    if not parts:
        return []
    cands = set()
    if len(parts) >= 2:
        f = parts[0].lower().strip()
        l = parts[-1].lower().strip()
        for sep in ("", ".", "_", "-"):
            cands.add(f"{f}{sep}{l}")
            cands.add(f"{f[0]}{sep}{l}")
            cands.add(f"{f}{sep}{l[0]}")
        cands.add(f"{l}{f}")
        cands.add(f"{f[0]}{l}")
        cands.add(f"{f}{l[0]}")
        cands.add(l)
        cands.add(f)
        cands.add(f"{l}{f[0]}")
    else:
        single = parts[0].lower().strip()
        cands.add(single)
    return sorted(c for c in cands if 2 <= len(c) <= 32)


def _email_permutations(name, domains):
    parts = [p for p in name.split() if p]
    perms = set()
    if len(parts) >= 2:
        f = parts[0].lower().strip()
        l = parts[-1].lower().strip()
        patterns = [
            "{f}{l}", "{f}.{l}", "{f}_{l}", "{f}-{l}",
            "{f}{l0}", "{f}.{l0}", "{l}{f}", "{l}.{f}",
            "{f0}{l}", "{f0}.{l}", "{f0}{l}", "{fl}", "{f}{l0}",
        ]
        for d in domains:
            for p in patterns:
                perms.add(p.format(f=f, l=l, f0=f[0], l0=l[0]) + "@" + d)
    else:
        s = parts[0].lower().strip()
        for d in domains:
            perms.add(f"{s}@{d}")
            perms.add(f"{s}.{d.split('.')[0]}@{d}")
    return sorted(perms)


def _probe_platforms(username):
    """Return list of {platform, url, status, present} for the given username.

    Combines HTTP status with a body-content heuristic to reduce the false
    positives caused by single-page apps that return 200 for everything.
    """
    out = []
    uname_norm = username.lower()
    for platform, tmpl in PLATFORMS:
        url = tmpl.format(u=urllib.parse.quote(username))
        status, text, ok = core.safe_get(url, timeout=6)
        presence = None
        if status in (404, 410):
            presence = False
        elif status in (403, 451):
            presence = None
        elif ok and status and status < 500:
            body = (text or "").lower()
            if uname_norm in body and "not found" not in body[:500].lower() \
                    and "doesn't exist" not in body[:500].lower():
                presence = True
            else:
                presence = "candidate"
        out.append({"platform": platform, "url": url, "status": status, "present": presence})
    return out


def _search_dorks(query):
    """Build ready-to-use search-engine dork URLs for a name."""
    q = urllib.parse.quote(f'"{query}"')
    return [
        {"engine": "Google", "url": f"https://www.google.com/search?q={q}"},
        {"engine": "Bing", "url": f"https://www.bing.com/search?q={q}"},
        {"engine": "DuckDuckGo", "url": f"https://duckduckgo.com/?q={q}"},
        {"engine": "Yandex", "url": f"https://yandex.com/search/?text={q}"},
        {"engine": "Google Images", "url": f"https://www.google.com/search?q={q}&tbm=isch"},
        {"engine": "Google News", "url": f"https://www.google.com/search?q={q}&tbm=nws"},
        {"engine": "PagesJaunes", "url": f"https://www.pagesjaunes.fr/pagesblanches/recherche?quoi={q}"},
        {"engine": "118712", "url": f"https://www.118712.fr/s/{q}"},
        {"engine": "Skipeo", "url": f"https://www.skipeo.com/?q={q}"},
        {"engine": "Webmii", "url": f"https://webmii.com/people?n={q}"},
    ]


def search(query):
    """Search by a name ("First Last" or surname alone) or by a raw username."""
    query = (query or "").strip()
    if not query:
        return {"ok": False, "error": "Requete vide."}

    parts = query.split()
    is_name = len(parts) >= 1 and all(re.match(r"^[A-Za-zÀ-ÿ'\-]+$", p) for p in parts)

    result = {"query": query, "is_name": is_name}

    candidates = _candidates_from_name(query) if is_name else [query]
    result["candidate_usernames"] = candidates
    result["email_permutations"] = _email_permutations(
        query, EMAIL_DOMAINS
    ) if is_name else []

    all_accounts = []
    seen_urls = set()
    for cand in candidates:
        for a in _probe_platforms(cand):
            if a["url"] not in seen_urls:
                seen_urls.add(a["url"])
                all_accounts.append(a)

    confirmed = [a for a in all_accounts if a["present"] is True]
    candidates_hits = [a for a in all_accounts if a["present"] == "candidate"]
    result["accounts"] = all_accounts
    result["confirmed_accounts"] = confirmed
    result["candidate_accounts"] = candidates_hits
    result["probed_usernames"] = candidates

    result["search_dorks"] = _search_dorks(query) if is_name else []

    result["summary"] = {
        "accounts_found": len(confirmed),
        "accounts_candidate": len(candidates_hits),
        "candidates": len(candidates),
        "dorks": len(result["search_dorks"]),
    }
    return result
