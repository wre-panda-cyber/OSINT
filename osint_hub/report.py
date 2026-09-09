"""Investigation report generator (JSON + PDF).

Builds a structured report from a set of module results and renders it as a
JSON file or a PDF (via fpdf2). Used by the export buttons in the web UI.
"""

import io
import json
from datetime import datetime, timezone


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def build_report(query, results, photo=None, astro=None):
    """Assemble a normalized report dict from module outputs."""
    return {
        "generated_at": _now(),
        "query": query,
        "modules": {
            k: v for k, v in {
                "name": results.get("name"),
                "email": results.get("email"),
                "phone": results.get("phone"),
                "website": results.get("website"),
                "external": results.get("external"),
            }.items() if v
        },
        "photo": photo,
        "astronomy": astro,
    }


def to_json(report):
    return json.dumps(report, ensure_ascii=False, indent=2)


def to_pdf(report):
    """Render the report to a PDF bytes buffer using fpdf2."""
    from fpdf import FPDF

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 10, "Rapport d'investigation OSINT", ln=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 6, f"Généré le {report.get('generated_at','')}", ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(2)

    q = report.get("query") or {}
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Cible", ln=True)
    pdf.set_font("Helvetica", "", 9)
    for label, key in (("Nom", "name_full"), ("Téléphone", "phone"),
                       ("Email", "email"), ("Site", "website"), ("Username", "username")):
        v = q.get(key)
        if v:
            pdf.cell(0, 6, f"  {label}: {v}", ln=True)
    pdf.ln(2)

    mods = report.get("modules") or {}
    for name, data in mods.items():
        _render_module(pdf, name, data)

    if report.get("photo"):
        _render_section(pdf, "Photo / EXIF / GPS", _flatten_photo(report["photo"]))

    if report.get("astronomy"):
        _render_section(pdf, "Astronomie", _flatten_astro(report["astronomy"]))

    out = io.BytesIO()
    pdf.output(out)
    return out.getvalue()


def _render_module(pdf, name, data):
    titles = {"name": "Identité / Réseaux", "email": "Email",
              "phone": "Téléphone", "website": "Site web", "external": "Outils externes"}
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(34, 211, 238)
    pdf.cell(0, 8, titles.get(name, name), ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 9)
    if name == "name":
        if data.get("primary_username"):
            pdf.cell(0, 6, f"  Username principal: {data['primary_username']}", ln=True)
        for a in (data.get("accounts") or []):
            mark = "+" if a.get("present") else ("-" if a.get("present") is False else "?")
            pdf.cell(0, 6, f"  [{mark}] {a.get('platform')}: {a.get('url')}", ln=True)
    elif name == "email":
        for k in ("email", "local", "domain"):
            if data.get(k):
                pdf.cell(0, 6, f"  {k}: {data[k]}", ln=True)
        if data.get("mx"):
            pdf.cell(0, 6, "  MX: " + ", ".join(str(x.get("exchange", x)) for x in data["mx"]), ln=True)
        if data.get("gravatar", {}).get("has_avatar"):
            pdf.cell(0, 6, "  Gravatar: avatar présent", ln=True)
        if data.get("hibp", {}).get("suffix_match"):
            pdf.cell(0, 6, "  HIBP: suffixe présent en fuite (potentiel)", ln=True)
    elif name == "phone":
        for k in ("e164", "country", "region", "carrier", "line_type"):
            if data.get(k):
                pdf.cell(0, 6, f"  {k}: {data[k]}", ln=True)
    elif name == "website":
        pdf.cell(0, 6, f"  Hôte: {data.get('host','')}", ln=True)
        h = data.get("http") or {}
        if h.get("title"):
            pdf.cell(0, 6, f"  Titre: {h['title']}", ln=True)
        if h.get("status"):
            pdf.cell(0, 6, f"  HTTP: {h.get('status')} Serveur: {h.get('server','')}", ln=True)
        if data.get("dns", {}).get("A"):
            pdf.cell(0, 6, "  A: " + ", ".join(data["dns"]["A"]), ln=True)
    elif name == "external":
        for tool, res in (data.items() if isinstance(data, dict) else []):
            _render_external(pdf, tool, res)
    pdf.ln(2)


def _render_external(pdf, tool, res):
    if not isinstance(res, dict):
        return
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(120, 120, 255)
    pdf.cell(0, 6, f"  >> {tool}", ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 9)
    if not res.get("available", True):
        pdf.cell(0, 6, f"     non disponible: {res.get('error','')}", ln=True)
        return
    if res.get("accounts"):
        pdf.cell(0, 6, f"     {len(res['accounts'])} comptes trouvés", ln=True)
        for a in res["accounts"][:50]:
            pdf.cell(0, 6, f"       {a.get('platform')}: {a.get('url')}", ln=True)
    if res.get("used_on"):
        pdf.cell(0, 6, f"     Email utilisé sur: {', '.join(res['used_on'])}", ln=True)
    if res.get("count") is not None:
        pdf.cell(0, 6, f"     Total: {res['count']}", ln=True)


def _render_section(pdf, title, lines):
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(34, 211, 238)
    pdf.cell(0, 8, title, ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 9)
    for ln in lines:
        pdf.cell(0, 6, f"  {ln}", ln=True)
    pdf.ln(2)


def _flatten_photo(p):
    out = []
    out.append(f"Fichier: {p.get('filename','')}")
    if p.get("format"):
        out.append(f"Format: {p['format']} {p.get('width','?')}x{p.get('height','?')}")
    exif = p.get("exif") or {}
    for k, v in exif.items():
        out.append(f"EXIF {k}: {v}")
    gps = p.get("gps")
    if gps:
        out.append(f"GPS: {gps.get('latitude')}, {gps.get('longitude')}")
        if gps.get("reverse", {}).get("address"):
            out.append(f"Adresse: {gps['reverse']['address']}")
    elif p.get("has_exif"):
        out.append("Aucun GPS dans les EXIF")
    else:
        out.append("Aucune métadonnée EXIF")
    return out


def _flatten_astro(a):
    out = [
        f"Lieu: {a.get('location',{}).get('lat')}, {a.get('location',{}).get('lon')}",
        f"Date UTC: {a.get('datetime_utc')}",
    ]
    sun = a.get("sun") or {}
    out.append(f"Soleil lever: {sun.get('rise')}  transit: {sun.get('transit')}  coucher: {sun.get('set')}")
    moon = a.get("moon") or {}
    mp = moon.get("phase") or {}
    out.append(f"Lune: {mp.get('name')} illumination {mp.get('illumination')} altitude {moon.get('altitude_deg')}°")
    for p in a.get("planets") or []:
        out.append(f"  {p.get('body')}: alt {p.get('altitude_deg')}° az {p.get('azimuth_deg')}° {'visible' if p.get('visible') else ''}")
    return out
