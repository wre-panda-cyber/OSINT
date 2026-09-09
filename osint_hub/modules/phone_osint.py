"""Phone OSINT module.

Uses the `phonenumbers` library (the same one PhoneInfoga relies on) to parse,
validate and locate a phone number, plus a curated set of public lookup links
(Truecaller, numinfo, country search engines).
"""

import phonenumbers
from phonenumbers import carrier, geocoder, timezone

from .. import core


def search(phone):
    phone = (phone or "").strip()
    if not phone:
        return {"ok": False, "error": "Numéro vide."}

    # Try parsing in several common default regions.
    parsed = None
    for region in (None, "FR", "US", "GB", "DE", "ES", "IT", "BE", "CA", "MA", "DZ", "TN"):
        try:
            parsed = phonenumbers.parse(phone, region)
            if phonenumbers.is_valid_number(parsed):
                break
        except phonenumbers.NumberParseException:
            parsed = None
    if parsed is None:
        return {"ok": False, "error": "Numéro introuvable / format non reconnu."}

    intl = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
    e164 = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    national = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.NATIONAL)

    result = {
        "e164": e164,
        "international": intl,
        "national": national,
        "country_code": parsed.country_code,
        "national_number": parsed.national_number,
        "valid": phonenumbers.is_valid_number(parsed),
        "possible": phonenumbers.is_possible_number(parsed),
        "region": geocoder.region_code_for_number(parsed),
        "country": geocoder.description_for_number(parsed, "fr") or geocoder.description_for_number(parsed, "en"),
        "carrier": carrier.name_for_number(parsed, "fr") or carrier.name_for_number(parsed, "en"),
        "line_type": "mobile" if phonenumbers.number_type(parsed) in (1, 2) else "fixed/other",
        "timezones": [str(tz) for tz in timezone.time_zones_for_number(parsed)],
    }

    # Public lookup links (manual follow-up)
    q = e164.replace("+", "")
    result["lookups"] = [
        {"engine": "Truecaller", "url": f"https://www.truecaller.com/search/{q}"},
        {"engine": "Sync.me", "url": f"https://sync.me/search/?number={q}"},
        {"engine": "Whocallsme", "url": f"https://whocallsme.com/Phone-Number.aspx/{q}"},
        {"engine": "Google", "url": f"https://www.google.com/search?q=%22{q}%22"},
        {"engine": "NumLookup (web)", "url": f"https://www.numlookup.com/{q}"},
        {"engine": "Epieos", "url": "https://epieos.com/"},
    ]

    result["summary"] = [
        f"{result['country']} ({result['region']})",
        f"Opérateur: {result['carrier'] or 'inconnu'}",
        f"Type: {result['line_type']}",
        f"Fuseaux: {', '.join(result['timezones']) or 'inconnu'}",
    ]
    return result
