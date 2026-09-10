"""Company / dirigeant OSINT module (French company registry).

Uses the free, keyless official government API
(https://recherche-entreprises.api.gouv.fr) which fuses SIRENE / INSEE /
INPI / BODACC data. This is the same public data Pappers.fr exposes, and
requires NO API key.

Given a name (surname, full name) or a SIREN/SIRET, it returns:
- companies where the person is a dirigeant (officer)
- the company's legal form, address, activity, finances, establishments
- ready-to-use links to Pappers, Infogreffe, Societe.ninja, data.inpi, etc.
"""

import json
import urllib.parse

from .. import core

API_BASE = "https://recherche-entreprises.api.gouv.fr/search"


def _normalize_dirigeant(d):
    """Extract a concise dirigeant dict from the API record."""
    if d.get("type_dirigeant") == "personne morale":
        return {
            "type": "personne morale",
            "nom": d.get("denomination") or "",
            "siren": d.get("siren") or "",
            "qualite": d.get("qualite") or "",
        }
    return {
        "type": "personne physique",
        "nom": d.get("nom") or "",
        "prenoms": d.get("prenoms") or "",
        "annee_de_naissance": d.get("annee_de_naissance") or "",
        "date_de_naissance": d.get("date_de_naissance") or "",
        "qualite": d.get("qualite") or "",
        "nationalite": d.get("nationalite") or "",
    }


def _normalize_company(c):
    """Extract a concise company dict from the API record."""
    siege = c.get("siege") or {}
    finances = c.get("finances") or {}
    last_fin = finances[list(finances)[0]] if finances else {}
    dirigeants = [_normalize_dirigeant(d) for d in (c.get("dirigeants") or [])]
    return {
        "siren": c.get("siren") or "",
        "nom_complet": c.get("nom_complet") or "",
        "nom_raison_sociale": c.get("nom_raison_sociale") or "",
        "etat": "active" if c.get("etat_administratif") == "A" else "fermee",
        "date_creation": c.get("date_creation") or "",
        "categorie": c.get("categorie_entreprise") or "",
        "nature_juridique": c.get("nature_juridique") or "",
        "activite": c.get("activite_principale") or "",
        "siege_adresse": siege.get("adresse") or "",
        "siege_code_postal": siege.get("code_postal") or "",
        "siege_commune": siege.get("libelle_commune") or "",
        "siege_departement": siege.get("departement") or "",
        "siege_latitude": siege.get("latitude") or "",
        "siege_longitude": siege.get("longitude") or "",
        "nombre_etablissements": c.get("nombre_etablissements") or 0,
        "nombre_etablissements_ouverts": c.get("nombre_etablissements_ouverts") or 0,
        "chiffre_affaires": last_fin.get("ca") if last_fin else None,
        "resultat_net": last_fin.get("resultat_net") if last_fin else None,
        "annee_finances": (list(finances)[0] if finances else ""),
        "dirigeants": dirigeants,
        "pappers_url": f"https://www.pappers.fr/entreprise/{c.get('siren','')}",
        "infogreffe_url": f"https://www.infogreffe.fr/entreprise/{c.get('siren','')}",
        "societe_ninja_url": f"https://societe.ninja/index.php?s={c.get('siren','')}",
        "data_inpi_url": f"https://data.inpi.fr/entreprises/{c.get('siren','')}",
    }


def search(query):
    """Search French companies by name (company or dirigeant) or SIREN.

    query: a name (surname / full name) or a SIREN/SIRET number.
    """
    query = (query or "").strip()
    if not query:
        return {"ok": False, "error": "Requete vide."}

    # If it looks like a SIREN/SIRET (9-14 digits), search by that directly.
    digits = "".join(ch for ch in query if ch.isdigit())
    params = {"q": query, "per_page": 20, "page": 1}
    if len(digits) >= 9:
        params["siren"] = digits[:9]

    url = f"{API_BASE}?{urllib.parse.urlencode(params)}"
    status, text, ok = core.safe_get(url, timeout=15)
    result = {"query": query, "api_url": url, "http_status": status}

    if not ok:
        return {**result, "ok": False, "error": text or "echec API"}

    try:
        data = json.loads(text)
    except Exception as exc:
        return {**result, "ok": False, "error": f"JSON: {exc}"}

    companies = [_normalize_company(c) for c in (data.get("results") or [])]
    result["companies"] = companies
    result["total_results"] = data.get("total_results", 0)
    result["returned"] = len(companies)

    # For a person name search, highlight companies where the person is a
    # dirigeant whose surname matches the query.
    q_lower = query.lower()
    parts = q_lower.split()
    surname = parts[-1] if parts else q_lower
    as_dirigeant = []
    for comp in companies:
        for d in comp.get("dirigeants", []):
            dname = (d.get("nom", "") + " " + d.get("prenoms", "")).strip().lower()
            dname_clean = dname.replace("(", " ").replace(")", " ")
            if surname in dname_clean and d.get("type") == "personne physique":
                as_dirigeant.append({
                    "entreprise": comp["nom_complet"],
                    "siren": comp["siren"],
                    "pappers_url": comp["pappers_url"],
                    "dirigeant": d,
                })
    result["as_dirigeant"] = as_dirigeant

    result["summary"] = {
        "entreprises": len(companies),
        "total_bdd": data.get("total_results", 0),
        "en_tant_que_dirigeant": len(as_dirigeant),
    }
    result["ok"] = True
    return result
