import requests, webbrowser, time
from bs4 import BeautifulSoup

# ==============================
# ⚙️ CONFIGURATION GLOBALE
# ==============================

URL = ["https://www.croisierenet.com/liste-produits/r-2/m-0/p-0/c-5_2/b-0/px-0-130/du-0-4/liste.html",
       "https://www.croisierenet.com/liste-produits/r-2/m-0/p-0/c-5_2/b-0/px-0-310/du-5-8/liste.html",
       "https://www.croisierenet.com/liste-produits/r-2/m-0/p-0/c-5_2/b-0/px-0-540/du-9-13/liste.html",
       "https://www.croisierenet.com/liste-produits/r-2/m-0/p-0/c-5_2/b-0/px-0-600/du-9-22/liste.html",
       "https://www.croisierenet.com/liste-produits/r-7461/m-0/p-0/c-5_2/b-0/px-0-550/du-7-18/liste.html",
       "https://www.croisierenet.com/liste-produits/d-182/m-0/p-0/c-0/b-0/px-0-600/du-12-28/liste.html",
       "https://www.croisierenet.com/liste-produits/r-1365/m-0/p-0/c-5_2/b-0/px-0-700/du-7-26/liste.html"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/129.0.0.0 Safari/537.36"
}

# MAX_PRIX_PAR_NUIT = 43
pause = 3     # pause de 3 seconds

# ==============================
# 🧩 FONCTIONS UTILES
# ==============================

def openSoupHTML(soup):
    if False:   # pour la conception de code !
        html_content = soup.prettify()  # formatage HTML
        with open("soup_scraping_cruis.html", "w", encoding="utf-8") as file:
            file.write(html_content)
        webbrowser.open("soup_scraping_cruis.html")

def up25cruis(soup):
    nombreCroisieres = soup.find(id='nbCroisieres')
    if int(nombreCroisieres.string) > 25:
        print(f"🛑 Il y a {nombreCroisieres.string} croisieres trouve par page (Max 25)!")

def getRequests(URL, HEADERS):
    all_articles = []

    for url in URL:
        print(f"📥 Récupération : {url}")

        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            response.raise_for_status()  # lève une erreur si code != 200
        except requests.exceptions.RequestException as e:
            print(f"❌ Erreur de requête : {e}")
            continue  # passe à l'URL suivante

        try:
            soup = BeautifulSoup(response.text, "html.parser")
            openSoupHTML(soup)
            up25cruis(soup)

            articles = soup.find_all("article")
            if not articles:
                print("⚠️ Aucun article trouvé sur cette page.")
            else:
                all_articles.extend(articles)
                print(f"→ {len(articles)} articles ajoutés.")

        except Exception as e:
            print(f"⚠️ Erreur de parsing sur {url} : {e}")
            continue  # ne stoppe pas le scraping global

        time.sleep(pause)

    print(f"\n✅ Total des articles collectés : {len(all_articles)}\n")
    return all_articles

def infoArticles(articles):
    all_cruis = []
    for article in articles:
        articleData = article.select_one("div.blocCroisiere")
        categorie = articleData.get("data-destination")
        bateau = articleData.get("data-bateau")
        portDepart = articleData.get("data-port")
        prix = articleData.get("data-price")
        # print(prix)

        date = article.select_one("span.datedp").get_text(strip=True)
        # print(date)

        jours_select = article.select_one("span.selectduree").get_text(strip=True)
        jours = jours_select.replace(" jours", "")
        jours_int = int(jours)
        # print(jours)

        prix_int = int(prix)
        prixNuit = str(round(prix_int / (jours_int - 1)))
        # print(prixNuit)

        link_tag = article.select_one("a.titreProductGA.lien")
        href = link_tag.get("href")
        data_hash = link_tag.get("data-hash")
        lien = f"{href}?param={data_hash}"
        # print(lien)

        all_info = {"categorie": categorie, "date": date, "jours": jours, "prix": prix, "prixNuit": prixNuit, "portDepart": portDepart, "bateau": bateau, "lien": lien}
        all_cruis.append(all_info)

    for info in all_cruis:
        print(f"Croisière de {info['jours']}j en {info['categorie']} le {info['date']} a {info['prix']}€ ({info['prixNuit']}€/nuit) avec le {info['bateau']} depart de {info['portDepart']}, {info['lien']}")
    return all_cruis

# ==============================
# 🚀 BOUCLE PRINCIPALE
# ==============================

def main():
    articles = getRequests(URL, HEADERS)
    cruis = infoArticles(articles)
    print("\n")
    # for cruise_str in cruis:
    #     print(cruise_str)

# ==============================
# ▶️ EXÉCUTION
# ==============================

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("🛑 Arrêt manuel du watcher.")
