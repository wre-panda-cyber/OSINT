"""Central OSINT investigation platform.

This web interface aggregates open-source OSINT capabilities behind a single
search bar: name / surname, phone, email, website and photo (EXIF/GPS).

Run locally:  python app.py   -> http://127.0.0.1:5000
"""

import io
import os
import time
from datetime import datetime, timezone

from flask import Flask, jsonify, render_template, request, send_from_directory

from osint_hub import core, report
from osint_hub.modules import (
    astronomy,
    email_osint,
    external_tools,
    name_osint,
    phone_osint,
    photo_osint,
    web_osint,
)
from osint_hub.registry import list_tools, list_categories

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024  # 25 MB photo upload cap
app.config["UPLOAD_FOLDER"] = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


@app.route("/")
def index():
    return render_template(
        "index.html",
        tools=list_tools(),
        categories=list_categories(),
    )


@app.route("/api/tools")
def api_tools():
    return jsonify({
        "tools": list_tools(),
        "categories": list_categories(),
        "runnable": external_tools.RUNNABLE,
        "availability": external_tools.availability(),
    })


@app.route("/api/external", methods=["POST"])
def api_external():
    """Run a real OSINT CLI tool (sherlock/maigret/holehe/phoneinfoga)."""
    data = request.get_json(silent=True) or {}
    tool_id = (data.get("tool") or "").strip()
    value = (data.get("value") or "").strip()
    if not tool_id or not value:
        return jsonify({"ok": False, "error": "Paramètres tool et value requis."}), 400
    started = time.time()
    result = external_tools.run(tool_id, value)
    result["elapsed_ms"] = int((time.time() - started) * 1000)
    return jsonify({"ok": result.get("ok", False), "results": result})


@app.route("/api/report", methods=["POST"])
def api_report():
    """Build and download a report (JSON or PDF) from the last investigation."""
    data = request.get_json(silent=True) or {}
    fmt = (data.get("format") or "json").lower()
    query = data.get("query") or {}
    results = data.get("results") or {}
    photo = data.get("photo")
    astro = data.get("astronomy")
    rep = report.build_report(query, results, photo=photo, astro=astro)
    if fmt == "pdf":
        try:
            pdf_bytes = report.to_pdf(rep)
        except Exception as exc:  # noqa: BLE001
            return jsonify({"ok": False, "error": f"PDF: {exc}"}), 500
        from flask import Response
        resp = Response(pdf_bytes, mimetype="application/pdf")
        resp.headers["Content-Disposition"] = 'attachment; filename="osint_report.pdf"'
        return resp
    # default JSON
    body = report.to_json(rep)
    from flask import Response
    resp = Response(body.encode("utf-8"), mimetype="application/json")
    resp.headers["Content-Disposition"] = 'attachment; filename="osint_report.json"'
    return resp


def _run_module(module, query, **extra):
    """Invoke a module search function with basic error isolation."""
    started = time.time()
    try:
        result = module.search(query, **extra) if extra else module.search(query)
        result = result or {}
        result.setdefault("module", module.__name__.split(".")[-1])
        result.setdefault("ok", True)
    except Exception as exc:  # noqa: BLE001 - module isolation
        result = {
            "module": module.__name__.split(".")[-1],
            "ok": False,
            "error": str(exc),
        }
    result["elapsed_ms"] = int((time.time() - started) * 1000)
    return result


@app.route("/api/search", methods=["POST"])
def api_search():
    data = request.get_json(silent=True) or {}
    target = core.normalize_target(
        first_name=data.get("first_name", ""),
        last_name=data.get("last_name", ""),
        phone=data.get("phone", ""),
        email=data.get("email", ""),
        website=data.get("website", ""),
        username=data.get("username", ""),
    )
    if not target["has_any"]:
        return jsonify({"ok": False, "error": "Aucun critère de recherche fourni."}), 400

    results = {"query": target, "started_at": datetime.now(timezone.utc).isoformat()}

    if target["name_full"]:
        results["name"] = _run_module(name_osint, target["name_full"])
    if target["email"]:
        results["email"] = _run_module(email_osint, target["email"])
    if target["phone"]:
        results["phone"] = _run_module(phone_osint, target["phone"])
    if target["website"]:
        results["website"] = _run_module(web_osint, target["website"])
    if target["username"]:
        # Reuse the name module's username engine directly when only a username is given.
        results.setdefault("name", _run_module(name_osint, target["username"]))

    results["finished_at"] = datetime.now(timezone.utc).isoformat()
    return jsonify({"ok": True, "results": results})


@app.route("/api/photo", methods=["POST"])
def api_photo():
    if "photo" not in request.files:
        return jsonify({"ok": False, "error": "Aucune photo reçue."}), 400
    file = request.files["photo"]
    if not file or not file.filename:
        return jsonify({"ok": False, "error": "Fichier vide."}), 400

    raw = file.read()
    if not raw:
        return jsonify({"ok": False, "error": "Fichier vide."}), 400

    started = time.time()
    try:
        result = photo_osint.analyze(io.BytesIO(raw), file.filename)
        result.setdefault("ok", True)
    except Exception as exc:  # noqa: BLE001
        result = {"ok": False, "error": str(exc)}
    result["elapsed_ms"] = int((time.time() - started) * 1000)
    return jsonify({"ok": True, "results": result})


@app.route("/api/astronomy", methods=["POST"])
def api_astronomy():
    data = request.get_json(silent=True) or {}
    lat = data.get("lat")
    lon = data.get("lon")
    date_str = data.get("date")
    try:
        lat = float(lat) if lat is not None else None
        lon = float(lon) if lon is not None else None
    except (TypeError, ValueError):
        return jsonify({"ok": False, "error": "Coordonnées invalides."}), 400
    if lat is None or lon is None:
        return jsonify({"ok": False, "error": "Latitude et longitude requises."}), 400
    started = time.time()
    try:
        result = astronomy.compute(lat, lon, date_str)
        result.setdefault("ok", True)
    except Exception as exc:  # noqa: BLE001
        result = {"ok": False, "error": str(exc)}
    result["elapsed_ms"] = int((time.time() - started) * 1000)
    return jsonify({"ok": True, "results": result})


@app.route("/uploads/<path:filename>")
def uploads(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
