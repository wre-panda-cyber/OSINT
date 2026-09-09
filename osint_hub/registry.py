"""Catalogue of integrated OSINT tools.

Each entry documents an open-source tool that this hub either invokes directly
or exposes as a one-click launcher link. The registry powers the "Outils" panel
of the web interface so investigators see exactly what is at their disposal.
"""

TOOLS = [
    # People / name / username
    {"id": "sherlock", "name": "Sherlock", "category": "Identité / Username",
     "url": "https://github.com/sherlock-project/sherlock",
     "desc": "Recherche un username sur 400+ réseaux sociaux et plateformes."},
    {"id": "maigret", "name": "Maigret", "category": "Identité / Username",
     "url": "https://github.com/soxoj/maigret",
     "desc": "Évolution de Sherlock : 2500+ sites, extraction de dossier complet."},
    {"id": "socialscan", "name": "socialscan", "category": "Identité / Username",
     "url": "https://github.com/iojw/socialscan",
     "desc": "Vérification approfondie d'email/username sur plateformes (peu de faux positifs)."},
    {"id": "instaloader", "name": "Instaloader", "category": "Identité / Username",
     "url": "https://github.com/instaloader/instaloader",
     "desc": "Téléchargement de contenu et métadonnées Instagram public."},
    {"id": "social-analyzer", "name": "Social-Analyzer", "category": "Identité / Username",
     "url": "https://github.com/qeeqbox/social-analyzer",
     "desc": "Recherche et analyse de comptes sur 1000+ réseaux sociaux."},
    {"id": "namechk", "name": "Namechk (web)", "category": "Identité / Username",
     "url": "https://namechk.com/",
     "desc": "Vérification en ligne de la disponibilité d'un pseudo."},
    # Email
    {"id": "holehe", "name": "Holehe", "category": "Email",
     "url": "https://github.com/megadose/holehe",
     "desc": "Vérifie si un email est utilisé sur 120+ sites via la fonction mot de passe oublié."},
    {"id": "h8mail", "name": "h8mail", "category": "Email",
     "url": "https://github.com/khast3x/h8mail",
     "desc": "Chasse aux fuites de mot de passe par email (local & services premium)."},
    {"id": "mosint", "name": "mosint", "category": "Email",
     "url": "https://github.com/AlpacaBote/mosint",
     "desc": "OSINT automatisé sur les adresses email (plusieurs services)."},
    {"id": "haveibeenpwned", "name": "Have I Been Pwned (web)", "category": "Email",
     "url": "https://haveibeenpwned.com/",
     "desc": "Vérifie si un email apparaît dans des fuites de données connues."},
    {"id": "epieos", "name": "Epieos (web)", "category": "Email",
     "url": "https://epieos.com/",
     "desc": "Lookup inversé d'email / téléphone lié aux comptes Google."},
    # Phone
    {"id": "phoneinfoga", "name": "PhoneInfoga", "category": "Téléphone",
     "url": "https://github.com/sundowndev/phoneinfoga",
     "desc": "Scanners OSINT avancés sur numéro de téléphone (pays, opérateur, portage)."},
    {"id": "numverify", "name": "Numverify (API)", "category": "Téléphone",
     "url": "https://numverify.com/",
     "desc": "Validation et infos de numéro (ligne, localisation, opérateur)."},
    {"id": "truecaller", "name": "Truecaller (web)", "category": "Téléphone",
     "url": "https://www.truecaller.com/",
     "desc": "Annuaire inversé communautaire (à utiliser avec prudence OPSEC)."},
    # Website / domain
    {"id": "theharvester", "name": "theHarvester", "category": "Site web / Domaine",
     "url": "https://github.com/laramies/theHarvester",
     "desc": "Emails, sous-domaines, hôtes et employés depuis un domaine."},
    {"id": "amass", "name": "OWASP Amass", "category": "Site web / Domaine",
     "url": "https://github.com/owasp-amass/amass",
     "desc": "Énumération d'attaque de surface et cartographie de domaine."},
    {"id": "shodan", "name": "Shodan (web)", "category": "Site web / Domaine",
     "url": "https://www.shodan.io/",
     "desc": "Moteur de recherche des dispositifs connectés à Internet."},
    {"id": "dnstwist", "name": "DNSTwist", "category": "Site web / Domaine",
     "url": "https://github.com/elceef/dnstwist",
     "desc": "Détection de typosquatting et variants de domaines."},
    {"id": "wappalyzer", "name": "Wappalyzer (web)", "category": "Site web / Domaine",
     "url": "https://www.wappalyzer.com/",
     "desc": "Identification des technologies d'un site web."},
    # Photo / image
    {"id": "exiftool", "name": "ExifTool", "category": "Photo / Image",
     "url": "https://github.com/exiftool/exiftool",
     "desc": "Lecture exhaustive des métadonnées EXIF/GPS/IPTC d'une image."},
    {"id": "fawkes", "name": "fawkes", "category": "Photo / Image",
     "url": "https://github.com/Shawn-Shan/fawkes",
     "desc": "Protection contre la reconnaissance faciale (anti-reconnaissance)."},
    {"id": "pim-eyes", "name": "PimEyes (web)", "category": "Photo / Image",
     "url": "https://pimeyes.com/",
     "desc": "Recherche inversée de visages sur le web public."},
    {"id": "google-images", "name": "Google Images (web)", "category": "Photo / Image",
     "url": "https://images.google.com/",
     "desc": "Recherche inversée d'image par upload ou URL."},
    # Geolocation / astronomy
    {"id": "sunpy", "name": "SunPy", "category": "Astronomie / Géoloc",
     "url": "https://github.com/sunpy/sunpy",
     "desc": "Bibliothèque Python d'astronomie solaire."},
    {"id": "ephem", "name": "PyEphem", "category": "Astronomie / Géoloc",
     "url": "https://github.com/brandon-rhodes/pyephem",
     "desc": "Calcul de positions, lever/coucher des astres (soleil, lune, planètes)."},
    {"id": "astral", "name": "Astral", "category": "Astronomie / Géoloc",
     "url": "https://github.com/sff8/astral",
     "desc": "Calculs de lever/coucher du soleil, aube, crépuscule, phases de lune."},
    {"id": "google-earth", "name": "Google Earth (web)", "category": "Astronomie / Géoloc",
     "url": "https://earth.google.com/",
     "desc": "Visualisation satellite d'une coordonnée GPS."},
    {"id": "opencellid", "name": "OpenCelliD (web)", "category": "Astronomie / Géoloc",
     "url": "https://opencellid.org/",
     "desc": "Géoloc par antennes cellulaires (MCC/MNC/LAC/CellID)."},
    # Frameworks
    {"id": "spiderfoot", "name": "SpiderFoot", "category": "Framework",
     "url": "https://github.com/smicallef/spiderfoot",
     "desc": "Framework OSINT automatisé avec 200+ modules."},
    {"id": "recon-ng", "name": "Recon-ng", "category": "Framework",
     "url": "https://github.com/lanmaster53/recon-ng",
     "desc": "Framework de reconnaissance modulaire (style Metasploit)."},
    {"id": "maltego", "name": "Maltego CE (web)", "category": "Framework",
     "url": "https://www.maltego.com/",
     "desc": "Analyse de liens et visualisation graphique d'entités OSINT."},
    {"id": "osint-framework", "name": "OSINT Framework (web)", "category": "Framework",
     "url": "https://osintframework.com/",
     "desc": "Arbre de liens vers des centaines d'outils OSINT par catégorie."},
]


def list_tools():
    return TOOLS


def list_categories():
    seen = []
    for t in TOOLS:
        if t["category"] not in seen:
            seen.append(t["category"])
    return seen
