import requests, webbrowser, time, os, json, socket, smtplib, email.utils, subprocess, sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from bs4 import BeautifulSoup

# ==============================
# ⚙️ CONFIGURATION GLOBALE
# ==============================

URL = ["https://www.croisierenet.com/liste-produits/r-2/m-0/p-0/c-5_2/b-0/px-0-92/du-0-3/liste.html",
       "https://www.croisierenet.com/liste-produits/r-2/m-0/p-0/c-5_2/b-0/px-0-220/du-4-6/liste.html",
       "https://www.croisierenet.com/liste-produits/r-2/m-0/p-0/c-5_2/b-0/px-0-360/du-7-9/liste.html",
       "https://www.croisierenet.com/liste-produits/r-2/m-0/p-0/c-5_2/b-0/px-0-540/du-9-13/liste.html",
       "https://www.croisierenet.com/liste-produits/r-2/m-0/p-0/c-5_2/b-0/px-0-800/du-14-24/liste.html",
       "https://www.croisierenet.com/liste-produits/r-7461/m-0/p-0/c-5_2/b-0/px-0-550/du-7-18/liste.html",
       "https://www.croisierenet.com/liste-produits/d-182/m-0/p-0/c-0/b-0/px-0-660/du-12-28/liste.html",
       "https://www.croisierenet.com/liste-produits/r-1365/m-0/p-0/c-5_2/b-0/px-0-580/du-8-16/liste.html",
       "https://www.croisierenet.com/liste-produits/r-1365/m-0/p-0/c-5_2/b-0/px-0-700/du-17-28/liste.html"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/129.0.0.0 Safari/537.36"
}

MAX_PRIX_PAR_NUIT = 40                  # Méditerranée MRS
MAX_PRIX_PAR_NUIT_NO_MRS = 38           # pas MRS
MAX_PRIX_PAR_NUIT_TRANSAT = 35          # FILTRE / Transatlantique Orient +8j
PAUSE = 3                               # pause de 3 seconds
AFFICHE_TOUT = False                    # Afficher toutes les Croisières sans filtre
TRANSATLANTIQUE = True                  # Inclure les Transatlantiques.

CHECK_INTERVAL = 60 * 60 * 4            # Vérification toutes les 4 heures.
START_HOUR, END_HOUR = 6, 21

FILE = "croisieres.json"
RESET_1E_MOIS = None                    # date du dernier reset FILE

ALERT_BEEP = False
ALERT_POPUP = False
ALERT_EMAIL = False

EMAIL_SENDER = "email_SENDER"
EMAIL_PASSWORD = "email_PASSWORD"
EMAIL_RECEIVER = "email_RECEIVER"
EMAIL_ALL = False                       # Envoie de mail a chaque verification.

# ==============================
# 🧩 FONCTIONS UTILES
# ==============================

def log(message: str):              # Affiche dans le terminal avec date et heure.
    now = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    print(f"{now} {message}")

def internet_ok(host="8.8.8.8", port=53, timeout=3):    # Teste la connexion Internet (Google DNS par défaut).
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except Exception:
        return False

def heure_autorisee():              # Retourne True si on est entre 6h et 22h inclus.
    heure = datetime.now().hour
    return START_HOUR <= heure <= END_HOUR

def openSoupHTML(soup):             # pour la conception de code ! Si 'True' affiche les pages HTML extraites.
    if False:   
        html_content = soup.prettify()  # formatage HTML
        with open("soup_scraping_cruis.html", "w", encoding="utf-8") as file:
            file.write(html_content)
        webbrowser.open("soup_scraping_cruis.html")

def up25cruis(soup):                # + de 25 Croisières trouve par page.
    nombreCroisieres = soup.find(id='nbCroisieres')
    if int(nombreCroisieres.string) > 25:
        log(f"🛑 Il y a {nombreCroisieres.string} Croisières trouve par page (Max 25)!")
        alert(True, False, False, f"⚠️ Croisières - Il y a {nombreCroisieres.string} Croisières trouve par page (Max 25)!")

def barreProgession(str):           # Barre de progression
    sys.stdout.write(str)
    sys.stdout.flush()

def afficheCrus(str):               # Affiche dans le terminal les Croisières
    for info in str:
        print(f"{info['id']} {info['categorie']}, {info['jours']}j, {info['portDepart']} -> {info['portArrivee']}, {info['date']}, {info['prix']}€ ({info['prixNuit']}€/nuit), {info['bateau']}, \n{info['lien']}\n")
        time.sleep(0.2)

def okMaxPrix(all_info, prixNuit):  # FILTRES
        ok = False

        if (all_info["categorie"] == "Iles Grecques" or all_info["categorie"] == "Iles Canaries" or all_info["categorie"] == "Méditerranée" or all_info["categorie"] == "Iles Baleares"):
            if MAX_PRIX_PAR_NUIT >= int(prixNuit) and (all_info["portDepart"] == "Marseille"):
                ok = True
            if MAX_PRIX_PAR_NUIT_NO_MRS >= int(prixNuit) and (all_info["portDepart"] != "Marseille"):
                ok = True

        if (all_info["categorie"] == "Transatlantique" or all_info["categorie"] == "Europe du Nord" or all_info["categorie"] == "Moyen-Orient - Dubaï"):
            if MAX_PRIX_PAR_NUIT_TRANSAT >= int(prixNuit) and (int(all_info["jours"]) > 8 and TRANSATLANTIQUE):
                ok = True
        return ok

def getRequests(URL, HEADERS):      # Extraction Web
    all_articles = []

    for url in URL:
        log(f"📥 Récupération : {url}")

        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            response.raise_for_status()  # lève une erreur si code != 200
        except requests.exceptions.RequestException as e:
            log(f"❌ Erreur de requête : {e}")
            alert(True, True, True, f"⚠️ Croisières - Erreur de requête : {e}")
            continue  # passe à l'URL suivante

        try:
            soup = BeautifulSoup(response.text, "html.parser")
            openSoupHTML(soup)
            up25cruis(soup)
            articles = soup.find_all("article")
            if not articles:
                log("⚠️ Aucun article trouvé sur cette page.")
            else:
                all_articles.extend(articles)
                log(f"→ {len(articles)} articles ajoutés.")

        except Exception as e:
            log(f"⚠️ Erreur de parsing sur {url} : {e}")
            alert(True, True, True, f"⚠️ Croisières - Erreur de parsing sur : {e}")
            continue  # ne stoppe pas le scraping global

        time.sleep(PAUSE)

    log(f"✅ Total des articles collectés : {len(all_articles)}")
    return all_articles

def getRequestsFiche(lien, HEADERS):      # Extraction du port d'arrivee sur la fiche
    try:
        response = requests.get(lien, headers=HEADERS, timeout=10)
        response.raise_for_status()  # lève une erreur si code != 200
    except requests.exceptions.RequestException as e:
        log(f"❌ Erreur de requête : {e}")
        alert(True, True, True, f"⚠️ Croisières - Erreur de requête sur la fiche : {e}")

    soup = BeautifulSoup(response.text, "html.parser")
    fiche = soup.find_all("div", class_="left w70P relative w100PPetit")[-1].get_text(strip=True)
    if fiche == "Jour•":
        fiche = soup.find_all("div", class_="left w70P relative w100PPetit")[-2].get_text(strip=True)
    portArrivee = fiche.split("•")[-1].strip()
    if fiche == "":
        portArrivee = "inconnu"

    time.sleep(1)
    return portArrivee

def infoArticles(articles):         # Extraction des donnees => []
    all_cruis = []
    barreProgession("\nProgression FILTRES : ")

    for article in articles:
        articleData = article.select_one("div.blocCroisiere")
        id = articleData.get("data-idproduct")
        categorie = articleData.get("data-destination")
        bateau = articleData.get("data-bateau")
        portDepart = articleData.get("data-port")
        prix = articleData.get("data-price")
        
        date = article.select_one("span.datedp").get_text(strip=True)

        jours_select = article.select_one("span.selectduree")
        jours = jours_select.get("data-duree")

        prixNuit = str(round(int(prix) / (int(jours) - 1)))

        link_tag = article.select_one("a.titreProductGA.lien")
        href = link_tag.get("href")
        data_hash = link_tag.get("data-hash")
        lien = f"{href}?param={data_hash}"


        all_info = {
             "id": id,
             "categorie": categorie,
             "date": date,
             "jours": jours,
             "prix": prix,
             "prixNuit": prixNuit,
             "portDepart": portDepart,
             "bateau": bateau,
             "lien": lien
             }
        
        if okMaxPrix(all_info, prixNuit) or AFFICHE_TOUT:
            portArrivee = getRequestsFiche(lien, HEADERS)
            all_info["portArrivee"] = portArrivee
            all_cruis.append(all_info)
        
            # Barre de progression en direct
            barreProgession('███ ')
    
    print("\n")
    log(f"✅ Total de Croisières filtrées : {len(all_cruis)}\n")

    return all_cruis

# ==============================
# ✅ FILE
# ==============================

def charger_anciens_resultats():                # Lecture FILE
    if os.path.exists(FILE):
        try:
            with open(FILE, "r", encoding="utf-8") as f:
                data = f.read().strip()
                if not data:
                    # fichier vide → on considère qu’il n’y a pas d’anciens résultats
                    log("⚠️ Fichier JSON vide, aucun ancien résultat chargé.")
                    return []
                return json.loads(data)
        except json.JSONDecodeError:
            log("⚠️ Fichier JSON corrompu, réinitialisation.")
            alert(True, False, True, "")
            return []
    return []

def sauvegarder_resultats(nouveaux):            # Ectiture FILE
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(nouveaux, f, ensure_ascii=False, indent=2)

def nouvelles_croisieres(anciennes, nouvelles): # Compare FILE
    # indexer les anciennes par ID pour accès rapide
    anciennes_dict = {c["id"]: c for c in anciennes}
    nouvelles_detectees = []

    for c in nouvelles:
        id_ = c["id"]
        prix = int(c["prix"])

        if id_ not in anciennes_dict:
            # 🚢 Nouvelle croisière
            nouvelles_detectees.append(c)
        else:
            ancien_prix = int(anciennes_dict[id_]["prix"])
            if prix < ancien_prix:
                # 💰 Même croisière mais prix en baisse
                c["ancien_prix"] = ancien_prix
                c["baisse"] = ancien_prix - prix
                nouvelles_detectees.append(c)

    return nouvelles_detectees

def reset_fichier():                            # Vide le fichier croisières.json le 1er de chaque mois."""
    global RESET_1E_MOIS
    aujourd_hui = datetime.now()
    mois_actuel = aujourd_hui.strftime("%Y-%m")

    if aujourd_hui.day == 1 and RESET_1E_MOIS != mois_actuel:
        if os.path.exists(FILE):
            with open(FILE, "w", encoding="utf-8") as f:
                f.write("")  # on vide le fichier
            log(f"🗓️ Nouveau mois ({aujourd_hui.strftime('%B %Y')}) → fichier {FILE} réinitialisé.")
            RESET_1E_MOIS = mois_actuel

# ==============================
# 📧 E-MAIL
# ==============================

def send_mail(corps, subject):          # Envoye de l'email
    # if not ALERT_EMAIL:
    #     return
    msg = MIMEMultipart()
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER
    msg["Subject"] = subject
    msg["Date"] = email.utils.formatdate(localtime=True)
    msg.attach(MIMEText(corps, "plain", "utf-8"))

    try:
        serveur = smtplib.SMTP("smtp.free.fr", 587)
        serveur.starttls()
        serveur.login(EMAIL_SENDER, EMAIL_PASSWORD)
        serveur.send_message(msg)
        serveur.quit()
        log("📧 Mail envoyé avec succès !")
    except Exception as e:
        log(f"❌ Erreur lors de l'envoi du mail : {e}")
        alert(True, False, True, "")

def mail(resultats):                    # Message de l'email
    # Construire le corps du mail
    if not resultats:
        corps = "Aucune croisière ne correspond aux critères."
    else:
        lignes = []
        for info in resultats:
            ligne = (
                f"• {info['categorie']} ({info['jours']} jours) – {info['prix']}€ "
                f"({info['prixNuit']}€/nuit) – {info['portDepart']}->{info['portArrivee']} – {info['bateau']} – {info['date']}\n"
                f"{info['lien']}\n"
            )
            # ➕ Ajout d'une ligne spéciale si baisse de prix
            if "baisse" in info:
                ligne += f"  🔻 Baisse de {info['baisse']}€ (ancien prix : {info['ancien_prix']}€)\n"

            lignes.append(ligne)
        corps = "\n".join(lignes)
        subject = f"🚢 Résumé des {len(resultats)} croisières trouvées le {datetime.now().strftime("%d %b %Y")}"     # datetime.now().strftime("%d %b %Y")
        send_mail(corps, subject)

def alert(beep, popup, mail, message):  # Alert BEEP POPUP et MAIL
    if ALERT_BEEP and beep:
        subprocess.run(["paplay", "/usr/share/sounds/freedesktop/stereo/complete.oga"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)

    if ALERT_POPUP and popup and not message == "":
        subprocess.run(["notify-send", message], check=False)

    if ALERT_EMAIL and mail and not message == "":
        send_mail("", message)

# ==============================
# 🚀 BOUCLE PRINCIPALE
# ==============================

def main():
    if not heure_autorisee():
        log(f"⏰ En dehors de la plage horaire ({START_HOUR}h-{END_HOUR}h). Attente...")
        return

    while not internet_ok():
        log("🌐 Nouvel essai dans 45 ninutes ...\n")
        alert(True, True, False, "⚠️ Croisières - Pas d'internet !")
        time.sleep(60*45)           # 60*45 => 45min

    articles = getRequests(URL, HEADERS)
    cruis = infoArticles(articles)
    afficheCrus(cruis)
    # print("")                                                 # ???

    reset_fichier()
    anciennes = charger_anciens_resultats()
    nouvelles = nouvelles_croisieres(anciennes, cruis)

    if nouvelles:
        log(f"📢 {len(nouvelles)} nouvelle(s) croisière(s) trouvée(s) ! Envoi du mail...")
        mail(nouvelles)
        sauvegarder_resultats(cruis)
    else:
        log("🔁 Aucune nouvelle croisière détectée.")
        if EMAIL_ALL:
            mail(anciennes)

# ==============================
# ▶️ EXÉCUTION
# ==============================

if __name__ == "__main__":
    try:
        while True:
            main()
            log(f"🕒 Attente {round(CHECK_INTERVAL/3600)}h avant la prochaine vérification...\n")
            time.sleep(CHECK_INTERVAL)
    except KeyboardInterrupt:
        log("🛑 Arrêt manuel du watcher.")
