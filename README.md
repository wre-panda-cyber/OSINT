# OSINT Hub

Interface web **centralisée** d'investigation OSINT qui combine en un point unique les
outils open-source de recherche par **nom / prénom**, **téléphone**, **email**, **site web**,
**upload de photos** (EXIF / GPS), et le **calcul des positions et horaires des astres**.

## Fonctionnalités

- 🔎 **Barre de recherche unique** : on renseigne un ou plusieurs critères (nom + prénom,
  téléphone, email, site, username) et l'interface interroge simultanément tous les
  modules pertinents.
- 👤 **Identité / réseaux sociaux** : à partir d'un nom, génère les usernames
  candidats et les permutations d'emails, et sonde la présence d'un compte sur
  26 plateformes (GitHub, Reddit, X, Instagram, TikTok, YouTube, Telegram, LinkedIn,
  Mastodon, …) à la manière de Sherlock / Maigret.
- 📧 **Email** : validation syntaxique, résolution MX/A, Gravatar, fuite potentielles
  (k-anonymity HaveIBeenPwned), et liens vers Holehe, mosint, Hunter, Intelligence X.
- 📞 **Téléphone** : parsing/validation (phonenumbers), pays, opérateur, type de ligne,
  fuseaux, et liens Truecaller, Sync.me, Epieos, etc.
- 🌐 **Site web** : résolution DNS (A/AAAA/CNAME/NS/MX), headers HTTP, détection de
  technologies (Nginx, WordPress, PHP…), en-têtes de sécurité, et liens WHOIS,
  crt.sh, Shodan, VirusTotal, theHarvester, Wayback.
- 📷 **Upload de photos** : extraction EXIF (appareil, date, objectif…), coordonnées
  GPS, reverse-geocoding (Nominatim), carte OSM, liens Google Maps / GeoHack,
  et bouton « calculer les astres » pour le lieu retrouvé.
- 🌟 **Astronomie** : pour toute latitude/longitude et date, calcule :
  - lever / transit / coucher du Soleil, altitude courante, jour/nuit ;
  - altitude de la Lune, phase et illumination ;
  - position (altitude / azimut) des planètes visibles.
  Calcul maison basé sur les algorithmes NOAA / Meeus (aucune dépendance lourde).
- 🛠️ **Catalogue d'outils** : panneau listant 30 outils/services open-source par
  catégorie, chacun pointant vers son dépôt GitHub officiel.

## Démarrage rapide

```bash
pip install -r requirements.txt
python app.py
# -> http://127.0.0.1:5000
```

## API

| Endpoint | Méthode | Body | Description |
|---|---|---|---|
| `/api/search` | POST | `{first_name,last_name,phone,email,website,username}` | Recherche multi-modules |
| `/api/photo` | POST | `multipart/form-data` champ `photo` | Analyse EXIF/GPS |
| `/api/astronomy` | POST | `{lat,lon,date?}` | Positions & horaires des astres |
| `/api/tools` | GET | — | Catalogue des outils intégrés |

## Architecture

```
app.py                      # Serveur Flask + routes API
osint_hub/
  core.py                   # Normalisation des entrées, safe_get
  registry.py               # Catalogue des outils open-source
  modules/
    name_osint.py           # Nom / username / permutations email / sondes plateformes
    email_osint.py          # MX, Gravatar, HIBP, dorks
    phone_osint.py          # phonenumbers parsing + lookups
    web_osint.py            # DNS + HTTP meta + lookups
    photo_osint.py          # EXIF + GPS + reverse geocoding
    astronomy.py            # Soleil / Lune / planètes (calcul maison)
templates/index.html        # Interface web (single page)
```

## Outils open-source référencés

Identité : [Sherlock](https://github.com/sherlock-project/sherlock), [Maigret](https://github.com/soxoj/maigret),
[Social-Analyzer](https://github.com/qeeqbox/social-analyzer) ·
Email : [Holehe](https://github.com/megadose/holehe), [h8mail](https://github.com/khast3x/h8mail),
[mosint](https://github.com/AlpacaBote/mosint) ·
Téléphone : [PhoneInfoga](https://github.com/sundowndev/phoneinfoga) ·
Domaine : [theHarvester](https://github.com/laramies/theHarvester), [Amass](https://github.com/owasp-amass/amass),
[DNSTwist](https://github.com/elceef/dnstwist) ·
Photo : [ExifTool](https://github.com/exiftool/exiftool) ·
Astronomie : [PyEphem](https://github.com/brandon-rhodes/pyephem), [Astral](https://github.com/sff8/astral) ·
Frameworks : [SpiderFoot](https://github.com/smicallef/spiderfoot), [Recon-ng](https://github.com/lanmaster53/recon-ng).

## ⚖️ Usage légal & éthique

Cet outil agrège des sources publiques pour la **recherche défensive, la cybersécurité
et l'éducation**. Toute investigation ciblant des personnes physiques doit respecter le
RGPD et la législation locale (consentement, finalité légitime, proportionnalité).
Les auteurs déclinent toute responsabilité d'usage détourné.
