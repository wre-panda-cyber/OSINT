# OSINT Hub

Interface web **centralisée** d'investigation OSINT qui combine en un point unique les
outils open-source de recherche par **nom / prénom**, **téléphone**, **email**, **site web**,
**entreprise / dirigeant**, **upload de photos** (EXIF / GPS), et le **calcul des positions
et horaires des astres**.

## Fonctionnalités

- 🔎 **Barre de recherche unique** : on renseigne un ou plusieurs critères (nom + prénom,
  téléphone, email, site, username) et l'interface interroge simultanément tous les
  modules pertinents, **y compris les outils CLI externes installés**.
- 👤 **Identité / réseaux sociaux** : à partir d'un nom, génère les usernames
  candidats et les permutations d'emails, et sonde la présence d'un compte sur
  26 plateformes (GitHub, Reddit, X, Instagram, TikTok, YouTube, Telegram, LinkedIn,
  Mastodon, …) avec une heuristique statut HTTP + contenu pour réduire les faux
  positifs. Fournit aussi 10 liens de recherche prêts à cliquer (Google, Bing,
  DuckDuckGo, Yandex, Google Images/News, PagesJaunes, 118712, Skipeo, Webmii).
- 🏢 **Entreprise / dirigeant** : pour tout nom ou SIREN/SIRET, interroge l'API
  officielle gouvernementale gratuite `recherche-entreprises.api.gouv.fr` (fusion
  SIRENE / INSEE / INPI / BODACC — équivalent Pappers, **sans clé API**). Retourne les
  entreprises correspondantes, leurs dirigeants (nom, prénoms, année de naissance,
  rôle), et met en avant les sociétés où la personne recherchée est dirigeant.
  Liens directs vers Pappers, Infogreffe, Societe.ninja, Data INPI.
- 📧 **Email** : validation syntaxique, résolution MX/A, Gravatar, fuites potentielles
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
- ⚡ **Exécution réelle des outils CLI** : la recherche centrale lance **automatiquement**
  les outils CLI installés (Sherlock, Maigret, socialscan, Instaloader pour un username ;
  Holehe, h8mail pour un email ; PhoneInfoga pour un téléphone ; DNSTwist pour un
  site) et affiche leurs résultats directement dans l'onglet Résultats. L'onglet
  « Outils CLI externes » permet aussi de les lancer individuellement. Détection
  automatique de la disponibilité (✅/❌) avec repli gracieux si l'outil n'est pas
  installé.
- 🛡️ **Sécurité HTTP** : en-têtes de sécurité appliqués à chaque réponse
  (X-Content-Type-Options, X-Frame-Options, Referrer-Policy, Content-Security-Policy,
  HSTS sur HTTPS).
- 📄 **Export de rapport** : boutons « Exporter rapport (JSON) » et « Exporter rapport
  (PDF) » générant un document complet de l'investigation (cible, modules, entreprise,
  photo, astres, outils CLI externes).
- 🗂️ **Catalogue d'outils** : panneau listant 37 outils/services open-source par
  catégorie, chacun pointant vers son dépôt GitHub ou site officiel.

## Démarrage rapide

```bash
pip install -r requirements.txt
python app.py
# -> http://127.0.0.1:5000
```

> Sur macOS, si le port 5000 est occupé (AirPlay Receiver), utilisez un autre port :
> `PORT=5005 python app.py`

### Activer les outils CLI externes (optionnel mais recommandé)

Les modules passifs (sondage HTTP, DNS, EXIF, astronomie, entreprise) fonctionnent
sans installation supplémentaire. Pour des résultats plus fiables et exhaustifs,
installez les outils CLI dans votre environnement :

```bash
pip install sherlock-project maigret holehe phoneinfoga socialscan dnstwist h8mail instaloader
```

Ils seront détectés automatiquement au démarrage et lancés pour chaque recherche
pertinente.

## API

| Endpoint | Méthode | Body | Description |
|---|---|---|---|
| `/api/search` | POST | `{first_name,last_name,phone,email,website,username}` | Recherche multi-modules + outils CLI auto |
| `/api/photo` | POST | `multipart/form-data` champ `photo` | Analyse EXIF/GPS |
| `/api/astronomy` | POST | `{lat,lon,date?}` | Positions & horaires des astres |
| `/api/external` | POST | `{tool,value}` | Exécute un outil CLI individuel |
| `/api/report` | POST | `{format:json\|pdf, query, results, photo?, astronomy?}` | Télécharge le rapport |
| `/api/tools` | GET | — | Catalogue + disponibilité des outils |

## Architecture

```
app.py                      # Serveur Flask + routes API + en-têtes de sécurité
osint_hub/
  core.py                   # Normalisation des entrées, safe_get
  registry.py               # Catalogue des outils open-source
  report.py                 # Génération de rapport JSON + PDF
  modules/
    name_osint.py           # Nom / username / permutations email / sondes plateformes / dorks
    company_osint.py        # Entreprise & dirigeants (API gouv recherche-entreprises, équivalent Pappers)
    email_osint.py          # MX, Gravatar, HIBP, dorks
    phone_osint.py          # phonenumbers parsing + lookups
    web_osint.py            # DNS + HTTP meta + lookups
    photo_osint.py          # EXIF + GPS + reverse geocoding
    astronomy.py            # Soleil / Lune / planètes (calcul maison)
    external_tools.py       # Exécution subprocess Sherlock/Maigret/socialscan/Holehe/h8mail/PhoneInfoga/DNSTwist/Instaloader
templates/index.html        # Interface web (single page)
```

## Outils open-source référencés

Identité : [Sherlock](https://github.com/sherlock-project/sherlock), [Maigret](https://github.com/soxoj/maigret),
[socialscan](https://github.com/iojw/socialscan), [Instaloader](https://github.com/instaloader/instaloader),
[Social-Analyzer](https://github.com/qeeqbox/social-analyzer) ·
Entreprise : [Pappers](https://www.pappers.fr/), [API recherche-entreprises (gouv.fr)](https://recherche-entreprises.api.gouv.fr/),
[Infogreffe](https://www.infogreffe.fr/), [Societe.ninja](https://societe.ninja/), [Data INPI](https://data.inpi.fr/) ·
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
