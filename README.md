<p align="center">
    <img width="50%" height="auto" src="https://github.com/Patrick2562/PYHABOT/blob/master/assets/logo.png">
</p>

# PYHABOT

Ez a fork extra feature-ök hozzáadása céljából készült.
Eredeti repo by Patrick2562: [PYHABOT](https://github.com/Patrick2562/PYHABOT)

A **PYHABOT** egy _web scraping_ alkalmazás Pythonban, amely a [Hardverapróra](https://hardverapro.hu) feltöltött hirdetéseket nézi át és küld értesítéseket egy új megjelenésekor, azokról amelyek megfelelnek az általunk megadott feltételeknek.
Rendelkezik több integrációval is, amelyek segítségével parancsokon keresztül hozzáadhatóak és törölhetőek a keresni kívánt termékek.

# Hogyan használd

Miután meghívtad a botot az általad használt platformon lévő szerverre/szobába, a lent listázott parancsokkal kezelheted.
Egy új hirdetésfigyelő hozzáadásához elsőnek fel kell menni a [Hardverapróra](https://hardverapro.hu) és rákeresni a termékre amit figyelni szeretnél. Érdemes a részletes keresést használni, beállítani a kategóriát, minimum és maximum árat.
Ha ez megvan akkor a kattints a KERESÉS gombra és a találatok oldalon másold ki az URL-t, ezután a botnak kell elküldeni a következő parancsot: `!add <Kimásolt URL>`
Ilyenkor felkerül a listára és láthatjuk a hirdetésfigyelő ID-jét (erre szükség lesz a többi parancs használatánál).
Alapértelmezetten az értesítéseket abba a szobába fogja küldeni, ahol a parancs be lett írva, de meg lehet változtatni, ehhez használd a `!notifyon <Hirdetésfigyelő ID> <Notification típus> [<args>]` parancsot.
Ha mindent megfelelően csináltál, akkor a bot innentől kezdve egy új hirdetés megjelenésekor értesítést küld.
Ha szeretnéd átvizsgáltatni vele az eddigi hirdetéseket (amelyek a figyelő hozzáadása előtt is léteztek), akkor használd a `!rescrape <Hirdetésfigyelő ID>` parancsot.

# Használat
## Windows

1. Python telepítése. Virtualenv létrehozása és aktiválása. `python -m venv venv`

3. Repository letöltése és kicsomagolása. [(letöltés)](https://github.com/maraid/PYHABOT/archive/refs/heads/master.zip)
4. Parancssor megnyitása és navigálás a letöltött repositoryba: `cd PYHABOT`
5. Szükséges modulok telepítése: `pip install -r requirements.txt`
6. **.env** fájl létrehozása _(**.env.example** másolata)_: `copy .env.example .env`
7. **.env** config fájl megnyitása és kitöltése
8. Indítás a `python run.py` paranccsal
9. Bot meghívása a szerverre/szobába, és jogot adni neki az üzenetek olvasásához/küldéséhez. (Discord esetében az indításkor megjelenő linken keresztül)
10. Hirdetésfigyelő hozzáadása: **Hogyan használd** szekcióban részletezve

## Docker

1. Feltételezzük, hogy a Docker telepítve van és minimális ismeretekkel rendelkezel.
2. Hozd létre a `docker-compose.yml` fájlt a következő tartalommal:

   **a) Környezeti változókkal:**
   ```yaml
   services:
     pyhabot:
       image: maraid/pyhabot:latest
       container_name: pyhabot
       environment:
         - INTEGRATION=telegram  # vagy discord
         - DISCORD_TOKEN="[token]"
         - TELEGRAM_TOKEN="[token]"  # nem kell mindkettő
       volumes:
         - ./path/to/data:/data
       restart: unless-stopped
    ```
    **b) Docker secrets használatával: (elég csak a használatban lévőt definiálni)**
    ```yaml
    secrets:
        DISCORD_TOKEN:
            file: ./secrets/DISCORD_TOKEN
        TELEGRAM_TOKEN:
            file: ./secrets/TELEGRAM_TOKEN

    services:
        pyhabot:
            image: maraid/pyhabot:latest
            container_name: pyhabot
            secrets: [DISCORD_TOKEN, TELEGRAM_TOKEN]
            environment:
                - INTEGRATION=telegram
                - DISCORD_TOKEN__FILE=/run/secrets/DISCORD_TOKEN
                - TELEGRAM_TOKEN__FILE=/run/secrets/TELEGRAM_TOKEN
            volumes:
                - ./path/to/data:/data
            restart: unless-stopped
    ```
3. Indítás a docker `compose up -d pyhabot` paranccsal
4. Bot meghívása a szerverre/szobába, és jogot adni neki az üzenetek olvasásához/küldéséhez. (Discord esetében az indításkor megjelenő linken keresztül)
5. Hirdetésfigyelő hozzáadása: Hogyan használd szekcióban részletezve

# Integrációk

| Azonosító | Leírás       |
| :----     | :-----       |
| discord   | Discord bot  |
| telegram  | Telegram bot |

# Parancsok

Minden parancs elé ki kell tenni a prefixet, ez alapértelmezetten: `!` _(Például: !add)_

| Parancs | Leírás |
| :---------- | :---------------------------------------------------------------------------------------------------------------------------------- |
| help | Listázza az elérhető parancsokat. |
| add <url> | Felvesz egy új hirdetésfigyelőt. |
| remove <watch_id> | Töröl egy létező hirdetésfigyelőt. |
| list | Listázza a felvett hirdetésfigyelőket. |
| info <watch_id> | Lekéri egy hirdetésfigyelő adatait. |
| seturl <watch_id> <url> | Módosítja egy hirdetésfigyelő URL-jét. |
| notifyon <watch_id> | Beállítja a jelenlegi chat-et az értesítések megjelenítésehez. |
| setwebhook <watch_id> <url> | Beállítja a webhookot egy hirdetésfigyelőhöz. |
| unsetwebhook <watch_id> | Kitörli a webhookot egy hirdetésfigyelőtől. |
| rescrape <watch_id> | Törli a mentett hirdetéseket és újra lekéri azokat. |
| listads <watch_id> | Lekéri az hirdetésfigyelőhöz tartozó hirdetéseket. |
| adinfo <ad_id> | Lekéri a hirdetés adatait. |
| setpricealert <ad_id> | Beállít árváltozás értesítőt egy hirdetéshez. |
| unsetpricealert <ad_id> | Törli az árváltozás értesítőt egy hirdetéshez. |
| settings | Lekéri a bot beállításait. |
| setprefix <prefix> | Módosítja a parancs prefixumot. |
| setinterval <interval> | Beállítja a frissítés gyakoriságát másodpercekben. |
