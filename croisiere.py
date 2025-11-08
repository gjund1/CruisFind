import requests, webbrowser
from bs4 import BeautifulSoup

# ==============================
# ⚙️ CONFIGURATION GLOBALE
# ==============================

URL = "https://www.croisierenet.com/liste-produits/r-2/m-202510_202511_202512_202601_202602_202603_202604_202605_202606_202607_202608/p-0/c-5_2/b-0/px-0-140/du-0-4/liste.html"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/129.0.0.0 Safari/537.36"
}

# MAX_PRIX_PAR_NUIT = 43

# ==============================
# 🧩 FONCTIONS UTILES
# ==============================

def openSoupHTML(soup):
    if False:
        html_content = soup.prettify()  # formatage HTML
        with open("soup_scraping_cruis.html", "w", encoding="utf-8") as file:
            file.write(html_content)
        webbrowser.open("soup_scraping_cruis.html")

def up25cruis(soup):
    nombreCroisieres = soup.find(id='nbCroisieres')
    print(f"{nombreCroisieres.string} Croisieres")
    print("-------------")
    if int(nombreCroisieres.string) > 25:
        print(f"🛑 Il y a {nombreCroisieres.string} croisieres trouve par page (Max 25)!")

def getRequests(URL, HEADERS):
    response = requests.get(URL, headers=HEADERS)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        openSoupHTML(soup)
        up25cruis(soup)
        articles = soup.find_all("article")
    else:
        print(f"Erreur {response.status_code} lors de la requête")
    return articles

def infoArticles(articles):
    all_cruis = []
    for article in articles:    
        date = article.select_one("span.datedp").get_text(strip=True)
        # print(date)

        jours_select = article.select_one("span.selectduree").get_text(strip=True)
        jours = jours_select.replace(" jours", "")
        jours_int = int(jours)
        # print(jours)

        prix_select = article.select_one("span.bestPrice").get_text(strip=True)
        prix = prix_select.replace("€", "")
        prix_int = int(prix)
        # print(prix_int)

        prixNuit = str(round(prix_int / (jours_int - 1)))
        # print(prixNuit)

        portDepart = article.select_one("span.selectportdep").get_text(strip=True)
        # print(portDepart)

        bateau = article.find("span", class_="").string
        # print(bateau)

        link_tag = article.select_one("a.titreProductGA.lien")
        href = link_tag.get("href")
        data_hash = link_tag.get("data-hash")
        lien = f"{href}?param={data_hash}"
        # print(lien)

        all_info = {"date": date, "jours": jours, "prix": prix, "prixNuit": prixNuit, "portDepart": portDepart, "bateau": bateau, "lien": lien}
        all_cruis.append(all_info)

    for info in all_cruis:
        print(f"Croisiere de {info['jours']}j le {info['date']} a {info['prix']}€ ({info['prixNuit']}€/nuit) avec le {info['bateau']} depart de {info['portDepart']}, {info['lien']}")

# ==============================
# 🚀 BOUCLE PRINCIPALE
# ==============================

def main():
    articles = getRequests(URL, HEADERS)
    infoArticles(articles)

# ==============================
# ▶️ EXÉCUTION
# ==============================

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("🛑 Arrêt manuel du watcher.")