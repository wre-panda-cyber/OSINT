"""Website / domain OSINT module.

Performs passive recon on a website or domain (no scanning, no auth):

- normalizes to a hostname
- resolves DNS A / AAAA / CNAME / NS / MX
- fetches HTTP response metadata (status, server, security headers,
  redirect target, final URL) like Wappalyzer-lite
- generates public lookup links (WHOIS, Shodan, crt.sh, VirusTotal, theHarvester)
"""

import re
import urllib.parse

from .. import core

_SCHEME_RE = re.compile(r"^[a-zA-Z]+://")


def _host_from(website):
    if not website:
        return ""
    w = website.strip()
    if not _SCHEME_RE.match(w):
        w = "http://" + w
    parsed = urllib.parse.urlparse(w)
    host = parsed.hostname or ""
    return host.lower().lstrip("www.")


def _dns_records(host, rtype):
    try:
        import dns.resolver

        answers = dns.resolver.resolve(host, rtype, lifetime=6)
        return [str(r).strip(".") if rtype == "NS" else str(r) for r in answers]
    except Exception as exc:  # noqa: BLE001
        return [f"error: {exc}"]


def _http_meta(url):
    status, text, ok = core.safe_get(url, timeout=8, allow_redirects=True)
    out = {"requested_url": url, "status": status, "ok": ok}
    if not ok:
        out["error"] = text
        return out
    # crude header scraping from the raw response text headers
    import requests

    try:
        resp = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"}, allow_redirects=True)
        out["final_url"] = resp.url
        out["server"] = resp.headers.get("Server", "")
        out["powered_by"] = resp.headers.get("X-Powered-By", "")
        out["content_type"] = resp.headers.get("Content-Type", "")
        out["security_headers"] = {
            "strict_transport_security": bool(resp.headers.get("Strict-Transport-Security")),
            "content_security_policy": bool(resp.headers.get("Content-Security-Policy")),
            "x_frame_options": resp.headers.get("X-Frame-Options", ""),
            "x_content_type_options": bool(resp.headers.get("X-Content-Type-Options")),
        }
        out["title"] = _extract_title(resp.text)
        out["technologies_hint"] = _technologies_hint(resp)
    except Exception as exc:  # noqa: BLE001
        out["error"] = str(exc)
    return out


def _extract_title(html):
    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
    return m.group(1).strip() if m else ""


def _technologies_hint(resp):
    hints = []
    server = (resp.headers.get("Server") or "").lower()
    if "nginx" in server:
        hints.append("Nginx")
    if "apache" in server:
        hints.append("Apache")
    if "cloudflare" in server:
        hints.append("Cloudflare")
    pb = (resp.headers.get("X-Powered-By") or "").lower()
    if "php" in pb:
        hints.append("PHP")
    if "express" in pb:
        hints.append("Node/Express")
    if "asp.net" in pb:
        hints.append("ASP.NET")
    ct = resp.headers.get("Content-Type", "").lower()
    if "text/html" in ct and "wp-content" in resp.text.lower():
        hints.append("WordPress")
    if "shopify" in resp.text.lower()[:20000]:
        hints.append("Shopify")
    return hints


def search(website):
    host = _host_from(website)
    if not host or "." not in host:
        return {"ok": False, "error": "Site invalide."}

    result = {"input": website, "host": host}
    result["dns"] = {
        "A": _dns_records(host, "A"),
        "AAAA": _dns_records(host, "AAAA"),
        "CNAME": _dns_records(host, "CNAME"),
        "NS": _dns_records(host, "NS"),
        "MX": _dns_records(host, "MX"),
    }
    result["http"] = _http_meta("https://" + host)
    if result["http"].get("ok") is False:
        result["http_insecure"] = _http_meta("http://" + host)

    result["lookups"] = [
        {"engine": "WHOIS", "url": f"https://who.is/whois/{host}"},
        {"engine": "crt.sh (certs)", "url": f"https://crt.sh/?q={host}"},
        {"engine": "Shodan", "url": f"https://www.shodan.io/search?query={host}"},
        {"engine": "VirusTotal", "url": f"https://www.virustotal.com/gui/domain/{host}"},
        {"engine": "urlscan.io", "url": f"https://urlscan.io/search/#{host}"},
        {"engine": "DNSdumpster", "url": f"https://dnsdumpster.com/?host={host}"},
        {"engine": "theHarvester", "url": f"https://github.com/laramies/theHarvester"},
        {"engine": "Wayback Machine", "url": f"https://web.archive.org/web/*/{host}"},
        {"engine": "SecurityHeaders", "url": f"https://securityheaders.com/?q={host}"},
        {"engine": "DNSChecker (propagation)", "url": f"https://dnschecker.org/#A/{host}"},
    ]

    found_dns = sum(1 for v in result["dns"].values() if v and "error" not in v[0])
    result["summary"] = [
        f"{found_dns} types d'enregistrements DNS résolus",
        f"Technos: {', '.join(result['http'].get('technologies_hint', [])) or 'non détecté'}",
        f"HTTP status: {result['http'].get('status')}",
    ]
    return result
