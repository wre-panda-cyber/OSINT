"""Photo OSINT module.

Analyzes an uploaded image for EXIF metadata, extracts GPS coordinates when
present, performs reverse geocoding (Nominatim) and emits ready-to-use maps
plus astronomy/comparison hooks for the location.
"""

import io
from datetime import datetime

import exifread
from PIL import Image

from .. import core


def _to_deg(values):
    """Convert EXIF rational DMS triple to decimal degrees."""
    d = float(values.values[0].num) / float(values.values[0].den)
    m = float(values.values[1].num) / float(values.values[1].den)
    s = float(values.values[2].num) / float(values.values[2].den)
    return d + m / 60.0 + s / 3600.0


def _gps(tags):
    lat = lon = None
    try:
        lat_tag = tags.get("GPS GPSLatitude")
        lat_ref = tags.get("GPS GPSLatitudeRef")
        lon_tag = tags.get("GPS GPSLongitude")
        lon_ref = tags.get("GPS GPSLongitudeRef")
        if lat_tag and lon_tag:
            lat = _to_deg(lat_tag)
            lon = _to_deg(lon_tag)
            if lat_ref and str(lat_ref).strip() == "S":
                lat = -lat
            if lon_ref and str(lon_ref).strip() in ("W", "O"):
                lon = -lon
    except Exception:  # noqa: BLE001
        pass
    return lat, lon


def _reverse_geocode(lat, lon):
    try:
        from geopy.geocoders import Nominatim

        geo = Nominatim(user_agent="osint-hub")
        loc = geo.reverse(f"{lat}, {lon}", language="fr", timeout=8)
        if loc:
            return {"address": loc.address, "raw": dict(loc.raw)}
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc)}
    return {"address": None}


def _exif_summary(tags):
    keep = {
        "Image Make": "marque",
        "Image Model": "modèle",
        "EXIF DateTimeOriginal": "date_prise",
        "EXIF DateTimeDigitized": "date_numérisation",
        "Image Software": "logiciel",
        "Image Artist": "auteur",
        "EXIF ExifImageWidth": "largeur",
        "EXIF ExifImageLength": "hauteur",
        "EXIF FocalLength": "focale",
        "EXIF ISOSpeedRatings": "iso",
        "EXIF ExposureTime": "temps_exposition",
        "EXIF LensModel": "objectif",
        "GPS GPSLatitude": "gps_lat",
        "GPS GPSLongitude": "gps_lon",
        "GPS GPSAltitude": "altitude",
    }
    out = {}
    for tag, label in keep.items():
        if tag in tags:
            out[label] = str(tags[tag])
    return out


def analyze(fileobj, filename="photo"):
    raw = fileobj.read()
    fileobj.seek(0)

    tags = exifread.process_file(io.BytesIO(raw), details=False)
    info = {
        "filename": filename,
        "size_bytes": len(raw),
        "has_exif": bool(tags),
    }

    try:
        img = Image.open(io.BytesIO(raw))
        info["format"] = img.format
        info["width"], info["height"] = img.size
        info["mode"] = img.mode
    except Exception as exc:  # noqa: BLE001
        info["image_error"] = str(exc)

    info["exif"] = _exif_summary(tags)

    lat, lon = _gps(tags)
    info["gps"] = None
    if lat is not None and lon is not None:
        info["gps"] = {
            "latitude": round(lat, 6),
            "longitude": round(lon, 6),
        }
        info["gps"]["maps_google"] = f"https://www.google.com/maps?q={lat},{lon}"
        info["gps"]["maps_osm"] = f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}#map=16/{lat}/{lon}"
        info["gps"]["geo_hack"] = f"https://tools.wmflabs.org/geohack/geohack.php?params={lat}_{lon}"
        info["gps"]["reverse"] = _reverse_geocode(lat, lon)
        info["gps"]["astronomy_hook"] = True

    info["summary"] = []
    if info.get("exif", {}).get("marque"):
        info["summary"].append(f"{info['exif']['marque']} {info['exif'].get('modèle','')}")
    if info.get("exif", {}).get("date_prise"):
        info["summary"].append(f"Prise le {info['exif']['date_prise']}")
    if info.get("gps"):
        info["summary"].append(f"GPS: {lat:.4f}, {lon:.4f}")
        rev = info["gps"].get("reverse", {})
        if rev.get("address"):
            info["summary"].append(f"Adresse: {rev['address']}")
    elif info["has_exif"]:
        info["summary"].append("Aucune coordonnée GPS dans les EXIF")
    else:
        info["summary"].append("Aucune métadonnée EXIF (image probablement nettoyée)")
    return info
